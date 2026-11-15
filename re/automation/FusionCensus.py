import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path, PurePosixPath

IDENTITY_FIELDS = ("corpus_revision", "manifest_sha256", "sdk_revision", "sdk_sources_sha256", "tool_sources", "python", "receipt_version")
LIMIT = 32 * 1024 * 1024


def read_json(path):
    with Path(path).open("rb") as source:
        content = source.read(LIMIT + 1)
    if len(content) > LIMIT:
        raise ValueError("census input exceeds 32 MiB")
    return json.loads(content)


def identity_of(summary):
    identity = {field: summary[field] for field in IDENTITY_FIELDS}
    for field in ("corpus_revision", "sdk_revision"):
        if not isinstance(identity[field], str) or not re.fullmatch(r"[0-9a-f]{40}", identity[field]):
            raise ValueError(f"invalid {field}")
    for field in ("manifest_sha256", "sdk_sources_sha256"):
        if not isinstance(identity[field], str) or not re.fullmatch(r"[0-9a-f]{64}", identity[field]):
            raise ValueError(f"invalid {field}")
    if identity["receipt_version"] != 1 or not isinstance(identity["python"], str) or len(identity["python"]) > 4096:
        raise ValueError("invalid reader runtime identity")
    tools = identity["tool_sources"]
    if not isinstance(tools, dict) or not 1 <= len(tools) <= 100 or any(not isinstance(name, str) or not 1 <= len(name) <= 4096 or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest) for name, digest in tools.items()):
        raise ValueError("invalid reader tool identity")
    return identity


def record_of(entry, source, summary_path, identity):
    record = {"path": source["path"], "sha256": source["sha256"], "git_blob": source["git_blob"], "outcome": entry["outcome"]}
    if entry["outcome"] == "decoded":
        directory = hashlib.sha256(source["path"].encode("utf-8")).hexdigest()
        if entry["directory"] != directory:
            raise ValueError("decoded asset directory differs from its path digest")
        receipt = read_json(summary_path.parent / directory / "receipt.json")
        if identity_of(receipt) != identity or receipt["source"] != source or receipt["reader_mode"] != entry["reader_mode"]:
            raise ValueError("receipt differs from its summary identity or pinned input")
        if receipt["options"] != {"mode": entry["reader_mode"], "allow_partial": True, "strict": entry["reader_mode"] == "strict", "include_brep": True, "include_tessellation": True}:
            raise ValueError("unexpected reader options")
        if receipt["portable_complete"] is not False or receipt["semantic_qualification"] != "unverified" or receipt["native_acceptance"] != "not_established":
            raise ValueError("research receipt claims qualification")
        record.update({"reader_mode": entry["reader_mode"], "strict_rejection": receipt["strict_rejection"]})
    else:
        if "directory" in entry:
            raise ValueError("failed asset has a document directory")
        record["reason"] = entry["reason"]
        if entry["outcome"] == "reader_error":
            record["error_type"] = entry["error_type"]
    return record


def validate_report(report):
    if not isinstance(report, dict) or report.get("census_version") != 1 or report.get("allow_partial") is not True:
        raise ValueError("unsupported Fusion census")
    identity_of(report["observation"])
    if report.get("portable_complete") is not False or report.get("semantic_qualification") != "unverified" or report.get("native_acceptance") != "not_established":
        raise ValueError("census must retain unqualified research status")
    records = report["assets"]
    if not isinstance(records, list) or not 1 <= len(records) <= 1000:
        raise ValueError("census must contain 1–1000 assets")
    paths = []
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("invalid census asset record")
        path = record["path"]
        if not isinstance(path, str) or not 1 <= len(path) <= 4096 or PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts:
            raise ValueError("invalid census asset path")
        for field, width in (("sha256", 64), ("git_blob", 40)):
            if not isinstance(record[field], str) or not re.fullmatch(rf"[0-9a-f]{{{width}}}", record[field]):
                raise ValueError("invalid census input digest")
        if record["outcome"] == "decoded":
            if set(record) != {"path", "sha256", "git_blob", "outcome", "reader_mode", "strict_rejection"} or record["reader_mode"] not in ("strict", "partial"):
                raise ValueError("invalid decoded outcome")
            reason = record["strict_rejection"]
            if (record["reader_mode"] == "strict" and reason is not None) or (record["reader_mode"] == "partial" and (not isinstance(reason, str) or not 1 <= len(reason) <= 1024)):
                raise ValueError("invalid strict rejection")
        elif record["outcome"] in ("rejected", "reader_error"):
            fields = {"path", "sha256", "git_blob", "outcome", "reason"}
            if record["outcome"] == "reader_error":
                fields.add("error_type")
                if not isinstance(record["error_type"], str) or not 1 <= len(record["error_type"]) <= 256:
                    raise ValueError("invalid reader error type")
            if set(record) != fields or not isinstance(record["reason"], str) or not 1 <= len(record["reason"]) <= 2048:
                raise ValueError("invalid rejected outcome")
        else:
            raise ValueError("unknown census outcome")
        paths.append(path)
    if paths != sorted(set(paths)):
        raise ValueError("census assets must be unique and sorted")
    return report


def collect(manifest_path, summary_paths):
    if not 1 <= len(summary_paths) <= 1000:
        raise ValueError("select 1–1000 summary shards")
    with manifest_path.open("rb") as source:
        manifest_bytes = source.read(LIMIT + 1)
    if len(manifest_bytes) > LIMIT:
        raise ValueError("manifest exceeds 32 MiB")
    manifest = json.loads(manifest_bytes)
    if manifest["manifest_version"] != 1:
        raise ValueError("unsupported corpus manifest")
    sources = [source for source in manifest["assets"] if source.get("kind") == "native" and source.get("format") in ("f3d", "f3z")]
    assets = {source["path"]: source for source in sources}
    if len(assets) != len(sources) or not 1 <= len(assets) <= 1000:
        raise ValueError("invalid Fusion manifest roster")
    identity, records, seen = None, [], set()
    for summary_path in summary_paths:
        summary = read_json(summary_path)
        current = identity_of(summary)
        if summary["allow_partial"] is not True or current["corpus_revision"] != manifest["source_revision"] or current["manifest_sha256"] != hashlib.sha256(manifest_bytes).hexdigest():
            raise ValueError("summary differs from corpus identity or reader mode")
        if identity is not None and current != identity:
            raise ValueError("summary shards use different source, tool or runtime identities")
        identity = current
        for entry in summary["assets"]:
            if entry["path"] not in assets or entry["path"] in seen:
                raise ValueError("unexpected or duplicate census input")
            seen.add(entry["path"])
            records.append(record_of(entry, assets[entry["path"]], summary_path, identity))
    if seen != set(assets):
        raise ValueError("census does not cover the complete Fusion manifest")
    return validate_report({"census_version": 1, "observation": identity, "allow_partial": True, "assets": sorted(records, key=lambda record: record["path"]), "semantic_qualification": "unverified", "portable_complete": False, "native_acceptance": "not_established"})


def compare(expected, actual):
    validate_report(expected)
    validate_report(actual)
    for field in ("corpus_revision", "manifest_sha256"):
        if expected["observation"][field] != actual["observation"][field]:
            raise ValueError(f"census {field} differs; review and pin a new corpus baseline")
    expected_assets = {entry["path"]: entry for entry in expected["assets"]}
    actual_assets = {entry["path"]: entry for entry in actual["assets"]}
    return [{"path": path, "expected": expected_assets.get(path), "actual": actual_assets.get(path)} for path in sorted(set(expected_assets) | set(actual_assets)) if expected_assets.get(path) != actual_assets.get(path)]


def main():
    parser = argparse.ArgumentParser(description="Collect or compare exact pinned Fusion reader outcomes without decoding inputs")
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("collect")
    capture.add_argument("--manifest", type=Path, required=True)
    capture.add_argument("--summary", type=Path, action="append", required=True)
    capture.add_argument("--output", type=Path, required=True)
    check = commands.add_parser("check")
    check.add_argument("--expected", type=Path, required=True)
    check.add_argument("--actual", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "collect":
            report = collect(args.manifest, args.summary)
            payload = (json.dumps(report, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
            with args.output.open("xb") as target:
                os.chmod(target.name, 0o600)
                target.write(payload)
            print(json.dumps({"output": str(args.output), "assets": len(report["assets"]), "portable_complete": False}, sort_keys=True))
            return 0
        expected, actual = read_json(args.expected), read_json(args.actual)
        changes = compare(expected, actual)
        print(json.dumps({"assets": len(actual["assets"]), "changes": changes, "baseline_revision": expected["observation"]["sdk_revision"], "observed_revision": actual["observation"]["sdk_revision"], "portable_complete": False}, sort_keys=True))
        return 3 if changes else 0
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as error:
        print(json.dumps({"error": str(error)[:2048], "portable_complete": False}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
