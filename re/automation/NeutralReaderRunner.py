import argparse
import hashlib
import json
import os
import secrets
import stat
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from convert.api.ApiOpen import OpenDocument
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KitDocStream
from interchange.document.Models.DocumentModel import CadDocument
from interchange.serialization.EncodeData import ToData
from interchange.serialization.JsonCodec import DumpJson, LoadJson

from InferenceInputs import checksum
from ReaderEvidence import reader_evidence
from Records import canonical, digest, label, specification
from SemanticComparison import pinned_bytes
from Sessions import read_bounded, write_private

KIND = "reader.neutral"
FORMATS = {"fusion.f3d", "solidworks.sldprt"}
INPUT_BYTES = 256 * 1024 * 1024
OUTPUT_BYTES = 32 * 1024 * 1024


def source_identity():
    root = Path(__file__).resolve().parents[2]
    sdk_paths = sorted((root / "src").rglob("*.py"))
    if not sdk_paths or len(sdk_paths) > 100000:
        raise ValueError("reader SDK source inventory is unavailable or oversized")
    tool_paths = [
        Path(__file__).with_name(name)
        for name in (
            "NeutralReaderRunner.py",
            "ReaderEvidence.py",
            "SemanticComparison.py",
            "SemanticGraph.py",
            "SemanticMatching.py",
            "InferenceInputs.py",
            "Records.py",
            "Sessions.py",
        )
    ]
    hashes = {}
    total = 0
    for path in (*sdk_paths, *tool_paths):
        before = path.lstat()
        if (
            not stat.S_ISREG(before.st_mode)
            or getattr(before, "st_file_attributes", 0) & 0x400
        ):
            raise ValueError("reader implementation source must be a regular file")
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0),
        )
        hasher = hashlib.sha256()
        with os.fdopen(descriptor, "rb") as source:
            opened = os.fstat(source.fileno())
            if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
                raise ValueError("reader implementation source changed while opening")
            while chunk := source.read(65536):
                total += len(chunk)
                if total > 512 * 1024 * 1024:
                    raise ValueError(
                        "reader implementation source inventory exceeds 512 MiB"
                    )
                hasher.update(chunk)
            after = os.fstat(source.fileno())
            if (opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns) != (
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            ):
                raise ValueError("reader implementation source changed during hashing")
        hashes[str(path.relative_to(root))] = hasher.hexdigest()
    sdk_hashes = {
        str(path.relative_to(root)): hashes[str(path.relative_to(root))]
        for path in sdk_paths
    }
    return {
        "sdk_sources_sha256": hashlib.sha256(
            json.dumps(sdk_hashes, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "sdk_source_files": len(sdk_paths),
        "tool_sources_sha256": {
            path.name: hashes[str(path.relative_to(root))] for path in tool_paths
        },
    }


def session_input(session):
    packet = read_bounded(session / "job.json")
    if (
        not isinstance(packet, dict)
        or type(packet.get("session_version")) is not int
        or packet["session_version"] != 1
        or packet.get("work") != "work"
        or packet.get("result") != "result.json"
    ):
        raise ValueError("unsupported native reader session contract")
    job, inputs = packet["job"], packet["inputs"]
    if canonical(specification(job)) != canonical(job) or job["kind"] != KIND:
        raise ValueError("reader session must contain its normalized registered job")
    options = job["options"]
    if (
        set(options) != {"scope", "source_format", "strict", "configuration"}
        or options["source_format"] not in FORMATS
        or type(options["strict"]) is not bool
        or not isinstance(inputs, dict)
        or set(inputs) != {"source"}
        or set(job["inputs"]) != {"source"}
    ):
        raise ValueError(
            "reader job requires its exact pinned source and explicit read options"
        )
    label(options["scope"])
    configuration = options["configuration"]
    if configuration is not None and (
        not isinstance(configuration, str)
        or not 1 <= len(configuration) <= 256
        or any(ord(character) < 32 for character in configuration)
    ):
        raise ValueError("reader configuration must be null or bounded printable text")
    descriptor = inputs["source"]
    if not isinstance(descriptor, dict) or set(descriptor) != {
        "binding",
        "sha256",
        "path",
    }:
        raise ValueError("reader source must use the version 1 session descriptor")
    pin = checksum(descriptor["sha256"])
    path = session / f"inputs/{pin}"
    if (
        descriptor["path"] != f"inputs/{pin}"
        or path.resolve() != path
        or descriptor["binding"] != job["inputs"]["source"]
    ):
        raise ValueError("reader source differs from its scheduled content address")
    snapshot = {
        "definition_hash": digest(job),
        "dependencies": packet["dependencies"],
        "inputs": {"source": {"binding": descriptor["binding"], "sha256": pin}},
    }
    fingerprint = checksum(packet["fingerprint"])
    if digest(snapshot) != fingerprint:
        raise ValueError(
            "reader session differs from the controller snapshot fingerprint"
        )
    return job, pin, path, snapshot["definition_hash"], fingerprint


def write_json(work, name, value):
    if not work.is_dir() or work.resolve() != work:
        raise ValueError("reader output requires the private session work directory")
    staged = work / f".{name}.{secrets.token_hex(8)}"
    hasher = hashlib.sha256()
    size = 0
    descriptor = os.open(staged, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as output:
            encoder = json.JSONEncoder(
                sort_keys=True, ensure_ascii=False, allow_nan=False
            )
            for chunk in encoder.iterencode(value):
                content = chunk.encode("utf-8")
                if size + len(content) > OUTPUT_BYTES:
                    raise ValueError("native reader JSON artifact exceeds 32 MiB")
                output.write(content)
                hasher.update(content)
                size += len(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(staged, work / name)
    finally:
        staged.unlink(missing_ok=True)
    return {"path": name, "sha256": hasher.hexdigest(), "size_bytes": size}


def run(session):
    session = session.resolve()
    job, pin, path, definition, fingerprint = session_input(session)
    options = job["options"]
    implementation = source_identity()
    content = pinned_bytes(path, pin, INPUT_BYTES)
    if options["source_format"] == "solidworks.sldprt":
        archive = SldprtArchive.from_bytes(content)
        if archive.get(KitDocStream) is not None:
            raise ValueError(
                "embedded Kit documents are not independent native reader evidence"
            )
    document = OpenDocument(
        content,
        SourceFormat=options["source_format"],
        Configuration=options["configuration"],
        IncludeBrep=True,
        IncludeTess=True,
        StrictMode=options["strict"],
    )
    if not isinstance(document, CadDocument) or document.source.sha256 != pin:
        raise ValueError("native reader document source differs from its raw input pin")
    document.assert_valid()
    wire = ToData(document)
    neutral = write_json(session / "work", "neutral-document.json", wire)
    encoded = pinned_bytes(
        session / "work" / neutral["path"], neutral["sha256"], OUTPUT_BYTES
    )
    rebuilt = LoadJson(encoded.decode("utf-8"))
    if not isinstance(rebuilt, CadDocument):
        raise ValueError(
            "native reader serialization did not reconstruct a CadDocument"
        )
    rebuilt.assert_valid()
    if (
        rebuilt != document
        or DumpJson(rebuilt, IndentSize=None).encode("utf-8") != encoded
    ):
        raise ValueError("native reader document changed during codec reconstruction")
    execution = {
        "kind": KIND,
        "scope": options["scope"],
        "source_format": options["source_format"],
        "source_sha256": pin,
        "definition_sha256": definition,
        "fingerprint": fingerprint,
        "rule_version": job["rule_version"],
        "tool_version": job["tool_version"],
        "implementation": implementation,
        "read_options": {
            "strict": options["strict"],
            "configuration": options["configuration"],
            "include_brep": True,
            "include_tessellation": True,
        },
    }
    evidence = {
        "reader_version": 1,
        **execution,
        "neutral_sha256": neutral["sha256"],
        "validation": "model_and_reconstruction_passed",
        **reader_evidence(wire),
    }
    evidence_artifact = write_json(session / "work", "reader-evidence.json", evidence)
    if source_identity() != implementation:
        raise ValueError(
            "reader implementation changed during decoding; use a stable checkout"
        )
    write_private(
        session / "result.json",
        {
            "outcome": "completed",
            "reason": "recorded native reader observations without portable or native qualification",
            "records": {
                "reader_version": 1,
                **execution,
                "neutral_sha256": neutral["sha256"],
                "neutral_size_bytes": neutral["size_bytes"],
                "evidence_sha256": evidence_artifact["sha256"],
                "evidence_size_bytes": evidence_artifact["size_bytes"],
                "semantic_qualification": "unverified",
                "native_acceptance": "not_established",
                "portable_complete": False,
            },
            "artifacts": {
                "neutral-document": neutral,
                "reader-evidence": evidence_artifact,
            },
        },
    )


def result_schema():
    seal = {"type": "string", "minLength": 64, "maxLength": 64}
    size = {"type": "integer", "minimum": 1, "maximum": OUTPUT_BYTES}
    version = {"type": "string", "minLength": 1, "maxLength": 128}
    properties = {
        "reader_version": {"type": "integer", "const": 1},
        "kind": {"type": "string", "const": KIND},
        "scope": version,
        "source_format": {"type": "string", "enum": sorted(FORMATS)},
        "source_sha256": seal,
        "definition_sha256": seal,
        "fingerprint": seal,
        "rule_version": version,
        "tool_version": version,
        "implementation": {
            "type": "object",
            "required": [
                "sdk_sources_sha256",
                "sdk_source_files",
                "tool_sources_sha256",
            ],
            "additionalProperties": False,
            "properties": {
                "sdk_sources_sha256": seal,
                "sdk_source_files": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100000,
                },
                "tool_sources_sha256": {"type": "object", "additionalProperties": seal},
            },
        },
        "read_options": {
            "type": "object",
            "required": [
                "strict",
                "configuration",
                "include_brep",
                "include_tessellation",
            ],
            "additionalProperties": False,
            "properties": {
                "strict": {"type": "boolean"},
                "configuration": {
                    "type": ["string", "null"],
                    "minLength": 1,
                    "maxLength": 256,
                },
                "include_brep": {"type": "boolean", "const": True},
                "include_tessellation": {"type": "boolean", "const": True},
            },
        },
        "neutral_sha256": seal,
        "neutral_size_bytes": size,
        "evidence_sha256": seal,
        "evidence_size_bytes": size,
        "semantic_qualification": {"type": "string", "const": "unverified"},
        "native_acceptance": {"type": "string", "const": "not_established"},
        "portable_complete": {"type": "boolean", "const": False},
    }
    return {
        "type": "object",
        "required": list(properties),
        "additionalProperties": False,
        "properties": properties,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Observe one pinned native CAD input through a controller session"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--schema", action="store_true")
    mode.add_argument("session", nargs="?", type=Path)
    arguments = parser.parse_args()
    try:
        if arguments.schema:
            print(canonical(result_schema()))
        else:
            run(arguments.session)
    except (
        LookupError,
        OSError,
        TypeError,
        ValueError,
        ArithmeticError,
        RecursionError,
    ) as error:
        parser.exit(1, f"native reader session refused: {error}\n")


if __name__ == "__main__":
    main()
