import argparse
import hashlib
import json
import os
import secrets
from pathlib import Path

from InferenceInputs import checksum
from Records import canonical, digest, label, specification
from SemanticComparison import (
    DOCUMENT_BYTES,
    compare_documents,
    document_input,
    tolerance_input,
)
from Sessions import read_bounded, write_private

KIND = "semantic.compare"
UNITS = {"mm", "cm", "m", "in", "ft"}
STATUSES = [
    "equal_observed_graph",
    "different",
    "ambiguous",
    "unresolved",
    "incomplete",
]


def input_path(session, descriptor):
    if not isinstance(descriptor, dict) or set(descriptor) != {
        "binding",
        "sha256",
        "path",
    }:
        raise ValueError("semantic input must use the version 1 session descriptor")
    expected = checksum(descriptor["sha256"])
    relative = f"inputs/{expected}"
    path = session / relative
    if descriptor["path"] != relative or path.resolve() != path:
        raise ValueError("semantic input escaped its content-addressed session path")
    return path


def write_report(work, report):
    if not work.is_dir() or work.resolve() != work:
        raise ValueError("semantic output requires the session work directory")
    staged = work / f".semantic-report.{secrets.token_hex(8)}"
    target = work / "semantic-report.json"
    hasher = hashlib.sha256()
    size = 0
    descriptor = os.open(staged, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as output:
            encoder = json.JSONEncoder(
                sort_keys=True, separators=(",", ":"), allow_nan=False
            )
            for chunk in encoder.iterencode(report):
                content = chunk.encode("utf-8")
                if size + len(content) > DOCUMENT_BYTES:
                    raise ValueError("semantic comparison artifact exceeds 32 MiB")
                output.write(content)
                hasher.update(content)
                size += len(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(staged, target)
    finally:
        staged.unlink(missing_ok=True)
    return {"path": target.name, "sha256": hasher.hexdigest(), "size_bytes": size}


def run(session):
    session = session.resolve()
    packet = read_bounded(session / "job.json")
    if (
        not isinstance(packet, dict)
        or type(packet.get("session_version")) is not int
        or packet["session_version"] != 1
        or packet.get("work") != "work"
        or packet.get("result") != "result.json"
    ):
        raise ValueError("unsupported semantic comparison session contract")
    job, inputs = packet["job"], packet["inputs"]
    if canonical(specification(job)) != canonical(job) or job["kind"] != KIND:
        raise ValueError("semantic session must contain its normalized registered job")
    options = job["options"]
    if (
        set(options)
        != {"scope", "first_geometry_unit", "second_geometry_unit", "max_candidates"}
        or not isinstance(inputs, dict)
        or set(inputs) != {"first", "second", "tolerances"}
        or set(job["inputs"]) != set(inputs)
        or type(options["max_candidates"]) is not int
        or not 1 <= options["max_candidates"] <= 100000
        or options["first_geometry_unit"] not in UNITS
        or options["second_geometry_unit"] not in UNITS
    ):
        raise ValueError(
            "semantic job requires three pinned inputs and explicit units and budget"
        )
    scope = label(options["scope"])
    paths = {
        role: input_path(session, descriptor) for role, descriptor in inputs.items()
    }
    if any(
        descriptor["binding"] != job["inputs"][role]
        for role, descriptor in inputs.items()
    ):
        raise ValueError("semantic input bindings differ from the scheduled job")
    snapshot = {
        "definition_hash": digest(job),
        "dependencies": packet["dependencies"],
        "inputs": {
            role: {"binding": descriptor["binding"], "sha256": descriptor["sha256"]}
            for role, descriptor in inputs.items()
        },
    }
    fingerprint = checksum(packet["fingerprint"])
    if digest(snapshot) != fingerprint:
        raise ValueError(
            "semantic session inputs differ from the controller fingerprint"
        )
    pins = {role: descriptor["sha256"] for role, descriptor in inputs.items()}
    first = document_input(paths["first"], pins["first"])
    second = document_input(paths["second"], pins["second"])
    tolerances = tolerance_input(paths["tolerances"], pins["tolerances"])
    report = compare_documents(
        first,
        second,
        tolerances,
        options["first_geometry_unit"],
        options["second_geometry_unit"],
        options["max_candidates"],
    )
    report["input_sha256"] = {
        "left": pins["first"],
        "right": pins["second"],
        "tolerances": pins["tolerances"],
    }
    report["execution"] = {
        "kind": KIND,
        "scope": scope,
        "definition_sha256": snapshot["definition_hash"],
        "fingerprint": fingerprint,
        "rule_version": job["rule_version"],
        "tool_version": job["tool_version"],
    }
    artifact = write_report(session / "work", report)
    write_private(
        session / "result.json",
        {
            "outcome": "completed",
            "reason": "recorded portable semantic observations without native qualification",
            "records": {
                "comparison_version": 1,
                "kind": KIND,
                "scope": scope,
                "observation_scope": "portable_semantic_graph_observation",
                "status": report["status"],
                "semantic_qualification": "unverified",
                "native_acceptance": "not_established",
                "independent_source_inventory": "not_supplied",
                "input_sha256": report["input_sha256"],
                "fingerprint": fingerprint,
                "definition_sha256": snapshot["definition_hash"],
                "report_sha256": artifact["sha256"],
                "report_size_bytes": artifact["size_bytes"],
            },
            "artifacts": {"semantic-report": artifact},
        },
    )


def result_schema():
    checksum_schema = {"type": "string", "minLength": 64, "maxLength": 64}
    properties = {
        "comparison_version": {"type": "integer", "const": 1},
        "kind": {"type": "string", "const": KIND},
        "scope": {"type": "string", "minLength": 1, "maxLength": 128},
        "observation_scope": {
            "type": "string",
            "const": "portable_semantic_graph_observation",
        },
        "status": {"type": "string", "enum": STATUSES},
        "semantic_qualification": {"type": "string", "const": "unverified"},
        "native_acceptance": {"type": "string", "const": "not_established"},
        "independent_source_inventory": {"type": "string", "const": "not_supplied"},
        "input_sha256": {
            "type": "object",
            "required": ["left", "right", "tolerances"],
            "additionalProperties": False,
            "properties": {
                role: checksum_schema for role in ("left", "right", "tolerances")
            },
        },
        "fingerprint": checksum_schema,
        "definition_sha256": checksum_schema,
        "report_sha256": checksum_schema,
        "report_size_bytes": {
            "type": "integer",
            "minimum": 1,
            "maximum": DOCUMENT_BYTES,
        },
    }
    return {
        "type": "object",
        "required": list(properties),
        "additionalProperties": False,
        "properties": properties,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Run a pinned portable semantic observation through a controller session"
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
        parser.exit(1, f"semantic comparison session refused: {error}\n")


if __name__ == "__main__":
    main()
