import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

from Corpus import git, read_tree
from ReaderEvidence import reader_evidence


def decode(root, manifest_path, asset_path, configuration, output):
    if output.exists() or output.is_symlink():
        raise ValueError("output already exists; select an unused directory")
    if not 1 <= len(asset_path) <= 4096 or PurePosixPath(asset_path).is_absolute() or ".." in PurePosixPath(asset_path).parts:
        raise ValueError("asset must be a bounded repository-relative path")
    with manifest_path.open("rb") as source:
        manifest_bytes = source.read(32 * 1024 * 1024 + 1)
    if len(manifest_bytes) > 32 * 1024 * 1024:
        raise ValueError("manifest exceeds 32 MiB")
    manifest = json.loads(manifest_bytes)
    if not isinstance(manifest, dict) or manifest.get("manifest_version") != 1:
        raise ValueError("unsupported corpus manifest")
    if not isinstance(manifest.get("assets"), list) or len(manifest["assets"]) > 10000 or any(not isinstance(asset, dict) for asset in manifest["assets"]):
        raise ValueError("manifest assets must contain at most 10000 records")
    revision = manifest["source_revision"]
    entries = read_tree(root, revision)
    matches = [asset for asset in manifest["assets"] if asset["path"] == asset_path]
    if len(matches) != 1:
        raise ValueError("asset must occur exactly once in the manifest")
    asset = matches[0]
    if asset.get("kind") != "native" or asset.get("format") != "sldprt" or Path(asset_path).suffix.casefold() != ".sldprt":
        raise ValueError("this reader accepts pinned SLDPRT parts only")
    if not re.fullmatch(r"[0-9a-f]{40}", asset["git_blob"]) or entries.get(asset_path) != asset["git_blob"]:
        raise ValueError("asset blob does not match its pinned revision/path")
    size = int(git(root, "cat-file", "-s", asset["git_blob"]))
    if not 8 <= size <= 256 * 1024 * 1024 or size != asset["size_bytes"]:
        raise ValueError("asset size mismatch or input exceeds 256 MiB")
    content = git(root, "cat-file", "blob", asset["git_blob"])
    if len(content) != size or hashlib.sha256(content).hexdigest() != asset["sha256"] or content[:16].hex() != asset["prefix_hex"]:
        raise ValueError("asset bytes differ from the pinned digest/prefix")
    sdk_paths = sorted((root / "src").rglob("*.py"))
    source_files = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sdk_paths}
    tool_files = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ("SolidworksReader.py", "ReaderEvidence.py", "Corpus.py", "Evidence.py")}
    source_digest = hashlib.sha256(json.dumps(source_files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    options = {"configuration": configuration, "strict": True, "include_brep": True, "include_tessellation": True}
    identity = {
        "corpus_revision": revision, "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "source": asset, "sdk_revision": git(root, "rev-parse", "HEAD").decode().strip(),
        "sdk_sources_sha256": source_digest, "tool_sources": tool_files,
        "python": sys.version, "options": options, "receipt_version": 1,
    }
    fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".reader-", dir=output.parent))
    try:
        sys.path.insert(0, str(root / "src"))
        from convert.adapters.solidworks.core.Adapter import ReadSldprt
        from convert.adapters.solidworks.container.Container import SldprtArchive
        from convert.adapters.solidworks.container.Format import KitDocStream
        from interchange.document.models.DocumentModel import CadDocument

        archive = SldprtArchive.from_bytes(content, asset_path)
        if archive.get(KitDocStream) is not None:
            raise ValueError("embedded Kit documents are not independent native reader evidence")
        document = ReadSldprt(content, Config=configuration)
        document.assert_valid()
        encoded = document.to_json(indent=None).encode("utf-8")
        if len(encoded) > 64 * 1024 * 1024:
            raise ValueError("neutral artifact exceeds 64 MiB")
        rebuilt = CadDocument.from_json(encoded.decode("utf-8"))
        rebuilt.assert_valid()
        if rebuilt.to_json(indent=None).encode("utf-8") != encoded:
            raise ValueError("neutral serialization changed after typed reconstruction")
        if source_files != {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sdk_paths}:
            raise ValueError("SDK source changed during decoding; retry against a stable checkout")
        wire = json.loads(encoded)
        receipt = {
            **identity, "fingerprint": fingerprint,
            "neutral_sha256": hashlib.sha256(encoded).hexdigest(),
            "serialization": "CadDocument JSON", "validation": "model_and_reconstruction_passed",
            "streams": sorted(archive.streams), **reader_evidence(wire),
        }
        receipt_bytes = (json.dumps(receipt, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
        if len(receipt_bytes) > 32 * 1024 * 1024:
            raise ValueError("evidence receipt exceeds 32 MiB")
        for name, payload in (("document.json", encoded), ("receipt.json", receipt_bytes)):
            with (staging / name).open("xb") as target:
                os.chmod(target.name, 0o600)
                target.write(payload)
                target.flush()
                os.fsync(target.fileno())
        output.mkdir(mode=0o700)
        try:
            for name in ("document.json", "receipt.json"):
                os.replace(staging / name, output / name)
        except BaseException:
            shutil.rmtree(output)
            raise
        return {"output": str(output), "fingerprint": fingerprint, "neutral_sha256": receipt["neutral_sha256"], "counts": receipt["counts"], "portable_complete": False}
    finally:
        shutil.rmtree(staging)


def main():
    parser = argparse.ArgumentParser(description="Decode one pinned SOLIDWORKS part into research neutral JSON and explicit evidence")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("Corpus.json"))
    parser.add_argument("--asset", required=True)
    parser.add_argument("--configuration")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.root.resolve() != Path(__file__).resolve().parents[2]:
            raise ValueError("root must be this reader's SDK checkout")
        if args.configuration is not None and not 1 <= len(args.configuration) <= 256:
            raise ValueError("configuration must contain 1–256 characters")
        result = decode(args.root.resolve(), args.manifest, args.asset, args.configuration, args.output)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RecursionError, subprocess.SubprocessError) as error:
        print(json.dumps({"error": str(error)[:2048], "portable_complete": False}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
