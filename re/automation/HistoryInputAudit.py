import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

ROOTS = (
    "re/automation",
    "re/solidworks/WriterResearch",
    "re/Fusion/LocalOracle",
    "tests/Research",
)
SUFFIXES = frozenset(
    {
        ".py",
        ".json",
        ".toml",
        ".yaml",
        ".yml",
        ".cs",
        ".ps1",
        ".sh",
        ".cjs",
        ".mjs",
        ".md",
    }
)
HASH = re.compile(rb"(?<![0-9a-fA-F])[0-9a-f]{40}(?![0-9a-fA-F])")
CAPTURE = re.compile(
    r"re/automation/PairedCaptures/P[0-9]{2}/(?:fusion|solidworks)-[0-9a-f]{12}/[^/]+"
)
MAX_FILE = 4 * 1024 * 1024
MAX_SOURCE = 64 * 1024 * 1024
MAX_FILES = 4096
MAX_PINS = 8192
MAX_REFERENCES = 100000
MAX_METADATA = 16 * 1024 * 1024
MAX_READ = 256 * 1024 * 1024


class GitMetadata:
    def __init__(self, root):
        self.root = root.resolve()
        self.deadline = time.monotonic() + 180
        self.read_bytes = 0
        self.environment = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("GIT_")
        }
        self.environment.update(
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL=os.devnull,
            GIT_GRAFT_FILE=os.devnull,
            LC_ALL="C",
        )

    def run(self, *args, data=None, limit=MAX_METADATA, accepted=(0,)):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise ValueError("history audit exceeded its 180 second budget")
        with tempfile.TemporaryFile() as output:
            process = subprocess.run(
                [
                    "git",
                    "--no-replace-objects",
                    "--no-lazy-fetch",
                    "--no-optional-locks",
                    "-C",
                    str(self.root),
                    *args,
                ],
                input=data,
                stdout=output,
                stderr=subprocess.DEVNULL,
                env=self.environment,
                timeout=min(30, remaining),
                check=False,
            )
            if process.returncode not in accepted:
                raise ValueError(f"Git {args[0]} refused the requested metadata")
            size = output.tell()
            self.read_bytes += size
            if size > limit or self.read_bytes > MAX_READ:
                raise ValueError("Git metadata exceeded its byte limit")
            output.seek(0)
            return process.returncode, output.read()

    def commit(self, value):
        if (
            len(value) > 256
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", value) is None
        ):
            raise ValueError("expected a bounded Git ref or full commit ID")
        _, raw = self.run(
            "rev-parse", "--verify", "--end-of-options", value + "^{commit}", limit=128
        )
        result = raw.decode("ascii").strip()
        if re.fullmatch("[0-9a-f]{40}", result) is None:
            raise ValueError("history audit requires SHA-1 Git objects")
        return result

    def tree(self, revision):
        _, raw = self.run("ls-tree", "-rlz", "--full-tree", revision)
        entries = {}
        for row in raw.split(b"\0"):
            if not row:
                continue
            metadata, path = row.split(b"\t", 1)
            mode, kind, checksum, size = metadata.decode("ascii").split()
            if kind == "blob":
                entries[path.decode("utf-8")] = {
                    "mode": mode,
                    "git_blob": checksum,
                    "size_bytes": int(size),
                }
        return entries

    def types(self, checksums):
        result = {}
        for offset in range(0, len(checksums), 128):
            selected = checksums[offset : offset + 128]
            _, raw = self.run(
                "cat-file",
                "--batch-check=%(objectname) %(objecttype)",
                data=("\n".join(selected) + "\n").encode("ascii"),
                limit=16384,
            )
            rows = [line.split() for line in raw.decode("ascii").splitlines()]
            if len(rows) != len(selected):
                raise ValueError("Git object classification is incomplete")
            for checksum, row in zip(selected, rows, strict=True):
                if (
                    len(row) != 2
                    or row[0] != checksum
                    or row[1] not in {"commit", "tree", "blob", "tag", "missing"}
                ):
                    raise ValueError("Git returned inconsistent object metadata")
                result[checksum] = row[1]
        return result


def selections(values):
    result = sorted(set(values or ROOTS))
    if not 1 <= len(result) <= 32:
        raise ValueError("select 1 to 32 repository paths")
    for value in result:
        path = PurePosixPath(value)
        if (
            len(value) > 512
            or path.is_absolute()
            or value != path.as_posix()
            or any(part in {"", ".", ".."} for part in value.split("/"))
            or "\\" in value
            or any(ord(char) < 32 or ord(char) == 127 for char in value)
        ):
            raise ValueError("audit paths must be normalized relative repository paths")
    return result


def references(git, entries, paths):
    files, pins = [], defaultdict(list)
    selected = []
    for path, entry in sorted(entries.items()):
        if not any(path == prefix or path.startswith(prefix + "/") for prefix in paths):
            continue
        if (
            entry["mode"] not in {"100644", "100755"}
            or PurePosixPath(path).suffix.lower() not in SUFFIXES
        ):
            continue
        selected.append((path, entry))
    total_bytes = sum(entry["size_bytes"] for _, entry in selected)
    oversized = [
        {"path": path, "size_bytes": entry["size_bytes"]}
        for path, entry in selected
        if entry["size_bytes"] > MAX_FILE
    ]
    if oversized or total_bytes > MAX_SOURCE or len(selected) > MAX_FILES:
        details = json.dumps(
            {
                "selected_files": len(selected),
                "selected_bytes": total_bytes,
                "oversized_files": len(oversized),
                "oversized_examples": oversized[:8],
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        raise ValueError(
            "tracked source exceeds the audit file or byte limits: "
            + details
            + "; select reviewed files or directories with repeated --path; "
            "no source blobs were read and no partial inventory was produced"
        )
    total_references = 0
    for path, entry in selected:
        _, raw = git.run("cat-file", "blob", entry["git_blob"], limit=MAX_FILE)
        if len(raw) != entry["size_bytes"]:
            raise ValueError("tracked source differs from its Git tree metadata")
        raw.decode("utf-8")
        files.append({"path": path, **entry})
        for line_number, line in enumerate(raw.splitlines(), 1):
            for match in HASH.finditer(line):
                checksum = match[0].decode("ascii")
                pins[checksum].append(
                    {
                        "path": path,
                        "line": line_number,
                        "byte_column": match.start() + 1,
                    }
                )
                total_references += 1
                if len(pins) > MAX_PINS or total_references > MAX_REFERENCES:
                    raise ValueError(
                        "tracked source exceeds the audit pin or reference limits"
                    )
    if not files:
        raise ValueError("selection contains no supported tracked source files")
    return files, pins


def capture_comparison(entries, current):
    result = []
    for path, entry in sorted(entries.items()):
        if CAPTURE.fullmatch(path) is None:
            continue
        if PurePosixPath(path).suffix.lower() not in {
            ".sldprt",
            ".sldasm",
            ".f3d",
            ".f3z",
        } and PurePosixPath(path).name not in {
            "receipt.json",
            "measurements.json",
            "complete.txt",
        }:
            continue
        actual = current.get(path)
        state = (
            "missing"
            if actual is None
            else "unchanged" if actual == entry else "changed"
        )
        result.append(
            {
                "path": path,
                "git_blob": entry["git_blob"],
                "state": state,
                "head_git_blob": None if actual is None else actual["git_blob"],
            }
        )
    return result


def commit_details(git, checksum, main, current, shallow):
    entries = git.tree(checksum)
    status, _ = git.run("merge-base", "--is-ancestor", checksum, main, accepted=(0, 1))
    _, raw = git.run("rev-parse", "--verify", checksum + "^{tree}", limit=128)
    captures = capture_comparison(entries, current)
    return {
        "tree_sha": raw.decode("ascii").strip(),
        "main_reachability": (
            "ancestor"
            if status == 0
            else "unavailable_shallow" if shallow else "not_ancestor"
        ),
        "prohibited_paths": sorted(
            path
            for path in entries
            if PurePosixPath(path).suffix.lower() in {".dll", ".dmg"}
        ),
        "capture_comparison": captures,
        "capture_states": dict(
            sorted(Counter(item["state"] for item in captures).items())
        ),
    }


def audit(root, revision, main_ref, paths):
    git = GitMetadata(root)
    revision, main = git.commit(revision), git.commit(main_ref)
    _, raw = git.run("rev-parse", "--is-shallow-repository", limit=128)
    if raw.strip() not in {b"true", b"false"}:
        raise ValueError("Git did not establish the repository history scope")
    shallow = raw.strip() == b"true"
    current = git.tree(revision)
    _, revision_tree = git.run("rev-parse", "--verify", revision + "^{tree}", limit=128)
    _, main_tree = git.run("rev-parse", "--verify", main + "^{tree}", limit=128)
    files, pins = references(git, current, paths)
    types = git.types(sorted(pins))
    head_blobs = defaultdict(list)
    for path, entry in sorted(current.items()):
        head_blobs[entry["git_blob"]].append(path)
    objects = []
    for checksum, kind in sorted(types.items()):
        row = {"sha": checksum, "object_type": kind, "references": pins[checksum]}
        if kind == "commit":
            row.update(commit_details(git, checksum, main, current, shallow))
        elif kind == "blob":
            row["head_paths"] = head_blobs[checksum]
        objects.append(row)
    payload = {
        "report_version": 1,
        "scope": "literal_git_history_input_inventory",
        "revision": revision,
        "revision_tree": revision_tree.decode("ascii").strip(),
        "main_revision": main,
        "main_tree": main_tree.decode("ascii").strip(),
        "shallow_repository": shallow,
        "selected_paths": paths,
        "scanned_files": files,
        "objects": objects,
        "summary": {
            "source_files": len(files),
            "source_bytes": sum(item["size_bytes"] for item in files),
            "literal_references": sum(len(items) for items in pins.values()),
            "object_types": dict(sorted(Counter(types.values()).items())),
            "commits_with_prohibited_paths": sum(
                bool(item.get("prohibited_paths")) for item in objects
            ),
            "unsafe_commit_pins": [
                item["sha"] for item in objects if item.get("prohibited_paths")
            ],
        },
    }
    digest = hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    ).hexdigest()
    return {**payload, "report_sha256": digest}


def main():
    parser = argparse.ArgumentParser(
        description="Inventory literal Git pins without reading native or vendor payloads"
    )
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--main", default="refs/remotes/origin/main")
    parser.add_argument("--path", action="append")
    args = parser.parse_args()
    try:
        report = audit(args.root, args.revision, args.main, selections(args.path))
        print(
            json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        )
        return 0
    except (
        OSError,
        ValueError,
        TypeError,
        UnicodeError,
        subprocess.SubprocessError,
    ) as error:
        print(
            f"history input audit refused ({type(error).__name__}): {error}".encode(
                "ascii", "backslashreplace"
            ).decode("ascii"),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
