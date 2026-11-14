import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path, PurePosixPath

from Corpus import git, read_tree
from ReaderEvidence import reader_evidence

MANIFEST_LIMIT = 32 * 1024 * 1024
DOCUMENT_LIMIT = 64 * 1024 * 1024
RECEIPT_LIMIT = 32 * 1024 * 1024
RUN_LIMIT = 4 * 1024 * 1024 * 1024
ASSET_LIMIT = 1000
TOOL_FILES = ("FusionReader.py", "ReaderEvidence.py", "Corpus.py", "Evidence.py")


def load_manifest(manifest_path):
    with manifest_path.open("rb") as source:
        manifest_bytes = source.read(MANIFEST_LIMIT + 1)
    if len(manifest_bytes) > MANIFEST_LIMIT:
        raise ValueError("manifest exceeds 32 MiB")
    manifest = json.loads(manifest_bytes)
    if not isinstance(manifest, dict) or manifest.get("manifest_version") != 1:
        raise ValueError("unsupported corpus manifest")
    if not isinstance(manifest.get("assets"), list) or len(manifest["assets"]) > 10000 or any(not isinstance(asset, dict) for asset in manifest["assets"]):
        raise ValueError("manifest assets must contain at most 10000 records")
    return manifest, manifest_bytes


def pinned_content(root, manifest, entries, asset_path):
    if not 1 <= len(asset_path) <= 4096 or PurePosixPath(asset_path).is_absolute() or ".." in PurePosixPath(asset_path).parts:
        raise ValueError("asset must be a bounded repository-relative path")
    matches = [asset for asset in manifest["assets"] if asset.get("path") == asset_path]
    if len(matches) != 1:
        raise ValueError("asset must occur exactly once in the manifest")
    asset = matches[0]
    suffix = Path(asset_path).suffix.casefold()
    if asset.get("kind") != "native" or asset.get("format") not in ("f3d", "f3z") or suffix != "." + asset["format"]:
        raise ValueError("this reader accepts pinned F3D and F3Z files only")
    if not re.fullmatch(r"[0-9a-f]{40}", asset["git_blob"]) or entries.get(asset_path) != asset["git_blob"]:
        raise ValueError("asset blob does not match its pinned revision/path")
    size = int(git(root, "cat-file", "-s", asset["git_blob"]))
    if not 8 <= size <= 256 * 1024 * 1024 or size != asset["size_bytes"]:
        raise ValueError("asset size mismatch or input exceeds 256 MiB")
    content = git(root, "cat-file", "blob", asset["git_blob"])
    if len(content) != size or hashlib.sha256(content).hexdigest() != asset["sha256"] or content[:16].hex() != asset["prefix_hex"]:
        raise ValueError("asset bytes differ from the pinned digest/prefix")
    return asset, content


def source_digests(root):
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted((root / "src").rglob("*.py"))}


def read_document(content, allow_partial):
    from convert.adapters.base.ReadOptions import ReadOptions
    from convert.adapters.Fusion.Adapter import FusionReader

    reader = FusionReader()
    try:
        return reader.Read(content, ReadOptions(strict=True)), "strict", None
    except ValueError as error:
        if not allow_partial:
            raise
        strict_reason = str(error)[:1024]
    try:
        return reader.Read(content, ReadOptions(strict=False)), "partial", strict_reason
    except ValueError as error:
        raise ValueError(f"strict: {strict_reason}; partial: {error}") from error


def encode_document(document):
    from interchange.document.models.DocumentModel import CadDocument

    document.assert_valid()
    encoded = document.to_json(indent=None).encode("utf-8")
    if len(encoded) > DOCUMENT_LIMIT:
        raise ValueError("neutral artifact exceeds 64 MiB")
    rebuilt = CadDocument.from_json(encoded.decode("utf-8"))
    rebuilt.assert_valid()
    if rebuilt.to_json(indent=None).encode("utf-8") != encoded:
        raise ValueError("neutral serialization changed after typed reconstruction")
    return encoded


def write_private(path, payload):
    with path.open("xb") as target:
        os.chmod(target.name, 0o600)
        target.write(payload)
        target.flush()
        os.fsync(target.fileno())


def build_receipt(asset, identity, allow_partial, encoded, mode, strict_reason):
    options = {"mode": mode, "allow_partial": allow_partial, "strict": mode == "strict", "include_brep": True, "include_tessellation": True}
    asset_identity = {**identity, "source": asset, "options": options}
    fingerprint = hashlib.sha256(json.dumps(asset_identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    evidence = reader_evidence(json.loads(encoded))
    if mode == "partial":
        evidence["unresolved"].append({"path": "", "reason": "strict_reader_rejected_partial_reader_used", "strict_rejection": strict_reason})
        evidence["counts"]["unresolved"] = len(evidence["unresolved"])
    receipt = {
        **asset_identity, "fingerprint": fingerprint,
        "neutral_sha256": hashlib.sha256(encoded).hexdigest(),
        "serialization": "CadDocument JSON", "validation": "model_and_reconstruction_passed",
        "reader_mode": mode, "strict_rejection": strict_reason, **evidence,
    }
    receipt_bytes = (json.dumps(receipt, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    if len(receipt_bytes) > RECEIPT_LIMIT:
        raise ValueError("evidence receipt exceeds 32 MiB")
    return receipt, receipt_bytes


def decode_asset(asset, content, identity, allow_partial, staging):
    try:
        document, mode, strict_reason = read_document(content, allow_partial)
        encoded = encode_document(document)
        receipt, receipt_bytes = build_receipt(asset, identity, allow_partial, encoded, mode, strict_reason)
    except ValueError as error:
        return {"path": asset["path"], "outcome": "rejected", "reason": str(error)[:2048]}, 0
    except Exception as error:
        return {"path": asset["path"], "outcome": "reader_error", "error_type": type(error).__name__, "reason": str(error)[:2048]}, 0
    directory = hashlib.sha256(asset["path"].encode("utf-8")).hexdigest()
    (staging / directory).mkdir(mode=0o700)
    write_private(staging / directory / "document.json", encoded)
    write_private(staging / directory / "receipt.json", receipt_bytes)
    entry = {
        "path": asset["path"], "outcome": "decoded", "reader_mode": mode, "directory": directory,
        "fingerprint": receipt["fingerprint"], "neutral_sha256": receipt["neutral_sha256"], "counts": receipt["counts"],
    }
    return entry, len(encoded) + len(receipt_bytes)


def decode(root, manifest_path, asset_paths, allow_partial, output):
    if sys.version_info < (3, 14):
        raise ValueError("Fusion research reading requires Python 3.14 for ZIP Zstandard support")
    if output.exists() or output.is_symlink():
        raise ValueError("output already exists; select an unused directory")
    if not 1 <= len(asset_paths) <= ASSET_LIMIT or len(set(asset_paths)) != len(asset_paths):
        raise ValueError("select 1–1000 distinct assets")
    manifest, manifest_bytes = load_manifest(manifest_path)
    revision = manifest["source_revision"]
    entries = read_tree(root, revision)
    pinned = [pinned_content(root, manifest, entries, asset_path) for asset_path in asset_paths]
    source_files = source_digests(root)
    identity = {
        "corpus_revision": revision, "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "sdk_revision": git(root, "rev-parse", "HEAD").decode().strip(),
        "sdk_sources_sha256": hashlib.sha256(json.dumps(source_files, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "tool_sources": {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in TOOL_FILES},
        "python": sys.version, "receipt_version": 1,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".fusion-reader-", dir=output.parent))
    try:
        sys.path.insert(0, str(root / "src"))
        results = []
        written = 0
        for asset, content in pinned:
            entry, size = decode_asset(asset, content, identity, allow_partial, staging)
            written += size
            if written > RUN_LIMIT:
                raise ValueError("run output exceeds 4 GiB; select fewer assets")
            results.append(entry)
        if source_files != source_digests(root):
            raise ValueError("SDK source changed during decoding; retry against a stable checkout")
        outcomes = Counter(entry["outcome"] for entry in results)
        modes = Counter(entry["reader_mode"] for entry in results if entry["outcome"] == "decoded")
        summary = {
            **identity, "allow_partial": allow_partial, "assets": results,
            "counts": {"assets": len(results), **{name: outcomes.get(name, 0) for name in ("decoded", "rejected", "reader_error")}, "strict": modes.get("strict", 0), "partial": modes.get("partial", 0)},
            "semantic_qualification": "unverified", "portable_complete": False, "native_acceptance": "not_established",
        }
        write_private(staging / "summary.json", (json.dumps(summary, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8"))
        os.rename(staging, output)
        return {"output": str(output), "counts": summary["counts"], "portable_complete": False}
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def main():
    parser = argparse.ArgumentParser(description="Decode pinned Fusion files into research neutral JSON and explicit evidence")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("Corpus.json"))
    parser.add_argument("--asset", action="append", required=True)
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.root.resolve() != Path(__file__).resolve().parents[2]:
            raise ValueError("root must be this reader's SDK checkout")
        result = decode(args.root.resolve(), args.manifest, args.asset, args.allow_partial, args.output)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["counts"]["decoded"] == result["counts"]["assets"] else 3
    except (OSError, ValueError, KeyError, TypeError, RecursionError, subprocess.SubprocessError) as error:
        print(json.dumps({"error": str(error)[:2048], "portable_complete": False}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
