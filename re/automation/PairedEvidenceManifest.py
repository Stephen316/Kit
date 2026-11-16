import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
SPEC = "re/automation/PairSpecs.json"
MAX_MANIFEST = 1024 * 1024
MAX_RECORD = 32 * 1024 * 1024
PUBLIC = {
    "P01": "re/automation/PrincipalReadbackEvidence.py",
    "P02": "re/automation/CircleReadbackEvidence.py",
    "P03": "re/automation/PrincipalReadbackEvidence.py",
}


class Refused(ValueError):
    pass


def require(condition, reason):
    if not condition:
        raise Refused(reason)


def checksum(value, size=64):
    require(
        isinstance(value, str) and re.fullmatch(f"[0-9a-f]{{{size}}}", value),
        "expected a full lowercase digest",
    )
    return value


def exact(value, keys):
    require(
        isinstance(value, dict) and set(value) == set(keys), "unexpected record fields"
    )


def unique(pairs):
    value = dict(pairs)
    require(len(value) == len(pairs), "duplicate JSON key")
    return value


def plain(path, directory=False):
    info = path.lstat()
    require(
        (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))
        and not getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0),
        "evidence paths must be plain files and directories",
    )
    return info


def directory(path):
    path = path.absolute()
    for parent in (*reversed(path.parents), path):
        plain(parent, directory=True)
    return path


def read_sealed(path, expected, limit):
    checksum(expected)
    directory(path.absolute().parent)
    before = plain(path)
    require(0 < before.st_size <= limit, "sealed input exceeds its byte limit")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as source:
        opened = os.fstat(source.fileno())
        require(
            (opened.st_dev, opened.st_ino) == (before.st_dev, before.st_ino),
            "sealed input identity changed",
        )
        raw = source.read(limit + 1)
    after = plain(path)
    require(
        len(raw) == before.st_size <= limit
        and (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
        == (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        and hashlib.sha256(raw).hexdigest() == expected,
        "sealed input bytes changed",
    )
    return raw


def git(*args):
    result = subprocess.run(
        ["git", "--no-replace-objects", "-C", str(ROOT), *args],
        check=True,
        capture_output=True,
        timeout=30,
    )
    require(
        len(result.stdout) <= 16 * 1024 * 1024, "Git metadata exceeds its byte limit"
    )
    return result.stdout


def commit(revision):
    checksum(revision, 40)
    require(
        git("rev-parse", "--verify", revision + "^{commit}").decode("ascii").strip()
        == revision,
        "source revision is not an exact commit",
    )


def source_bytes(revision, relative):
    size = int(git("cat-file", "-s", f"{revision}:{relative}"))
    require(0 < size <= MAX_RECORD, "pinned source exceeds its byte limit")
    raw = git("show", f"{revision}:{relative}")
    require(len(raw) == size, "pinned source length changed")
    return raw


def checked_manifest(path, expected):
    manifest = json.loads(
        read_sealed(path, expected, MAX_MANIFEST), object_pairs_hook=unique
    )
    exact(
        manifest,
        {
            "version",
            "scope",
            "target_revision",
            "capture_revision",
            "frozen_rules_revision",
            "specifications_sha256",
            "recipes",
            "evidence",
        },
    )
    require(
        type(manifest["version"]) is int
        and manifest["version"] == 1
        and manifest["scope"] == "paired_supplemental_preflight",
        "unsupported manifest scope",
    )
    commit(manifest["target_revision"])
    commit(manifest["capture_revision"])
    commit(manifest["frozen_rules_revision"])
    require(
        git("rev-parse", "HEAD").decode("ascii").strip() == manifest["target_revision"],
        "checkout differs from target revision",
    )
    specs = source_bytes(manifest["target_revision"], SPEC)
    require(
        hashlib.sha256(specs).hexdigest()
        == checksum(manifest["specifications_sha256"]),
        "specification digest changed",
    )
    recipes = manifest["recipes"]
    require(
        isinstance(recipes, list)
        and 1 <= len(recipes) <= 4
        and all(
            isinstance(recipe, str) and recipe in ("P01", "P02", "P03", "P04")
            for recipe in recipes
        )
        and recipes == sorted(set(recipes)),
        "choose unique ordered P01 through P04 recipes",
    )
    evidence = manifest["evidence"]
    require(
        isinstance(evidence, list) and len(evidence) == 2 * len(recipes),
        "expected both applications for every recipe",
    )
    identities = set()
    for entry in evidence:
        checked_entry(entry, recipes)
        identity = entry["application"], entry["recipe"]
        require(identity not in identities, "duplicate application and recipe")
        identities.add(identity)
    require(
        identities
        == {
            (application, recipe)
            for application in ("solidworks", "fusion")
            for recipe in recipes
        },
        "application roster differs",
    )
    return manifest


def checked_entry(entry, recipes):
    require(isinstance(entry, dict), "expected an evidence object")
    require(
        entry.get("application") in ("solidworks", "fusion")
        and entry.get("recipe") in recipes,
        "unsupported application or recipe",
    )
    common = {"application", "recipe", "source_revision"}
    checksum(entry["source_revision"], 40)
    if entry["application"] == "fusion" or entry["recipe"] == "P04":
        exact(entry, common | {"handoff_revision"})
        checksum(entry["handoff_revision"], 40)
        return
    exact(
        entry,
        common
        | {
            "verifier_revision",
            "verifier_sha256",
            "input_directory",
            "input_sha256",
            "report_sha256",
        },
    )
    for key in ("verifier_sha256", "input_sha256", "report_sha256"):
        checksum(entry[key])
    checksum(entry["verifier_revision"], 40)
    relative = entry["input_directory"]
    require(
        isinstance(relative, str)
        and 1 <= len(relative) <= 255
        and "\\" not in relative,
        "invalid private evidence directory",
    )
    parts = PurePosixPath(relative)
    require(
        parts.parts
        and not parts.is_absolute()
        and all(part not in (".", "..") for part in parts.parts)
        and relative == parts.as_posix(),
        "private evidence directory must stay inside its root",
    )


def checked_source(entry):
    commit(entry["source_revision"])
    commit(entry["verifier_revision"])
    relative = PUBLIC[entry["recipe"]]
    raw = source_bytes(entry["verifier_revision"], relative)
    require(
        hashlib.sha256(raw).hexdigest() == entry["verifier_sha256"],
        "verifier source digest changed",
    )
    local = ROOT / relative
    read_sealed(local, entry["verifier_sha256"], MAX_RECORD)
    changes = git(
        "status", "--porcelain", "--untracked-files=no", "--", "src", "re/automation"
    )
    require(
        not changes, "tracked verifier dependencies differ from the target checkout"
    )
    return relative


def checked_private(root, relative):
    selected = root / relative
    if not selected.exists() and not selected.is_symlink():
        return None
    directory(selected)
    require(
        selected.resolve().is_relative_to(root),
        "private evidence directory escapes its root",
    )
    pending, count = [selected], 0
    while pending:
        parent = pending.pop()
        for path in parent.iterdir():
            count += 1
            require(count <= 64, "private evidence roster exceeds its file limit")
            info = path.lstat()
            if stat.S_ISDIR(info.st_mode):
                plain(path, directory=True)
                require(
                    path.parent == selected,
                    "private evidence directory is nested too deeply",
                )
                pending.append(path)
            else:
                require(
                    0 < plain(path).st_size <= MAX_RECORD,
                    "private evidence record exceeds its byte limit",
                )
    return selected


def replay(entry, selected):
    try:
        if entry["recipe"] == "P02":
            from CircleReadbackEvidence import verify

            value = verify(
                ROOT, selected, entry["input_sha256"], entry["source_revision"]
            )
            require(
                value["source_revision"] == entry["source_revision"],
                "circle source revision differs",
            )
            observations = {
                row["file"]: row["source_sha256"] for row in value["observations"]
            }
        else:
            from PrincipalReadbackEvidence import report

            value = report(selected, entry["input_sha256"])
            require(
                value["source_revision"] == entry["source_revision"]
                and value["qualification"] is False,
                "principal source or claim differs",
            )
            observations = {
                row["file"]: row["native"]["sha256"]
                for row in value["cases"]
                if row["capture"] == entry["recipe"]
            }
    except Refused:
        raise
    except (
        LookupError,
        ValueError,
        TypeError,
        OSError,
        subprocess.SubprocessError,
    ) as error:
        raise Refused(
            "public raw-chain verifier refused the private evidence"
        ) from error
    encoded = (
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    require(
        hashlib.sha256(encoded).hexdigest() == entry["report_sha256"],
        "normalized replay digest changed",
    )
    return observations


def bind_capture(revision, recipe, observations):
    prefix = f"re/automation/PairedCaptures/{recipe}/solidworks-"
    names = (
        git(
            "ls-tree",
            "-r",
            "--name-only",
            "-z",
            revision,
            "--",
            prefix.rsplit("/solidworks-", 1)[0],
        )
        .decode("utf-8")
        .split("\0")
    )
    receipts = [
        name
        for name in names
        if name.startswith(prefix) and name.endswith("/receipt.json")
    ]
    require(len(receipts) == 1, "target lacks one exact SOLIDWORKS capture receipt")
    receipt = json.loads(source_bytes(revision, receipts[0]), object_pairs_hook=unique)
    require(
        receipt["recipe_id"] == recipe and receipt["errors"] == 0,
        "target capture receipt differs",
    )
    expected = {item["file"]: item["sha256"] for item in receipt["native_files"]}
    require(
        len(expected) == len(receipt["native_files"]) and expected == observations,
        "replay archive roster differs from target capture",
    )
    folder = receipts[0].rsplit("/", 1)[0]
    for name, digest in expected.items():
        require(
            isinstance(name, str)
            and 1 <= len(name) <= 255
            and PurePosixPath(name).name == name
            and "\\" not in name,
            "target capture contains an invalid archive name",
        )
        require(
            hashlib.sha256(source_bytes(revision, f"{folder}/{name}")).hexdigest()
            == checksum(digest),
            "target archive bytes differ from the replay",
        )


def handoff(entry):
    available = False
    try:
        commit(entry["handoff_revision"])
        commit(entry["source_revision"])
        available = True
    except subprocess.CalledProcessError:
        pass
    return {
        "status": "waiting_source_handoff",
        "handoff_revision": entry["handoff_revision"],
        "source_revision": entry["source_revision"],
        "git_sources_available": available,
        "reason": "the existing owner must supply and integrate the actual verifier contract",
    }


def preflight(manifest, root, expected):
    root = directory(root)
    values = []
    for entry in manifest["evidence"]:
        identity = {"application": entry["application"], "recipe": entry["recipe"]}
        if entry["application"] == "fusion" or entry["recipe"] == "P04":
            values.append({**identity, **handoff(entry)})
            continue
        source = checked_source(entry)
        selected = checked_private(root, entry["input_directory"])
        if selected is None:
            values.append(
                {**identity, "status": "waiting_private_evidence", "verifier": source}
            )
            continue
        observations = replay(entry, selected)
        bind_capture(manifest["capture_revision"], entry["recipe"], observations)
        bind_capture(manifest["target_revision"], entry["recipe"], observations)
        values.append(
            {
                **identity,
                "status": "verified_same_format_observations",
                "verifier": source,
                "input_sha256": entry["input_sha256"],
                "report_sha256": entry["report_sha256"],
            }
        )
    return {
        "schema": 1,
        "scope": "paired_supplemental_preflight",
        "status": "blocked",
        "manifest_sha256": expected,
        "target_revision": manifest["target_revision"],
        "capture_revision": manifest["capture_revision"],
        "frozen_rules_revision": manifest["frozen_rules_revision"],
        "specifications_sha256": manifest["specifications_sha256"],
        "recipes": manifest["recipes"],
        "qualified_pairs": 0,
        "qualification": "not_evaluated",
        "evidence": values,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Preflight a sealed paired supplemental evidence roster without qualifying pairs"
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = checked_manifest(args.manifest, args.manifest_sha256)
        result = preflight(manifest, args.evidence_root, args.manifest_sha256)
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
        return 2
    except Refused as error:
        print(f"paired evidence preflight refused: {error}", file=sys.stderr)
        return 1
    except (
        LookupError,
        ValueError,
        TypeError,
        OSError,
        ImportError,
        RecursionError,
        subprocess.SubprocessError,
    ) as error:
        print(
            f"paired evidence preflight refused ({type(error).__name__})",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
