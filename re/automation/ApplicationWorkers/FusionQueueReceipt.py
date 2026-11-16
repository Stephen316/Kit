from contextlib import nullcontext
import ntpath
import os
from pathlib import PureWindowsPath
import stat

from ApplicationProtocol import (
    directory,
    file_bytes,
    require,
    windows_function,
    write_new,
)
from Artifacts import Artifacts
from Records import canonical, digest, specification
from StoreRead import read_store


# windows leaf components must reject colon aliases before pathname device checks
def is_windows_record_name(name):
    if name.endswith((".", " ")) or any(
        character in '"*/:<>?\\|' or ord(character) < 32 for character in name
    ):
        return False
    is_reserved = getattr(ntpath, "isreserved", None)
    if is_reserved is not None:
        return not is_reserved(name)
    return not PureWindowsPath(name).is_reserved()


# a receipt and its intent share the same directly checked owner directory
def receipt_paths(path):
    require(
        os.name in {"posix", "nt"}, "persisted Fusion receipts require owner custody"
    )
    require(path.is_absolute() and path.name, "Fusion receipt path must be absolute")
    if os.name == "nt":
        require(
            all(is_windows_record_name(part) for part in path.parts[1:]),
            "Fusion receipt requires ordinary Windows path components",
        )
        hold_directory = windows_function("windows_records", "hold_directory")
        with hold_directory(path.parent):
            target = path
    else:
        target = directory(path.parent) / path.name
    return target, target.with_name(f".{target.name}.intent.json")


def receipt_bytes(value):
    return (canonical(value) + "\n").encode("utf-8")


# the platform record guard reads immutable bytes under the applicable owner boundary
def owned_bytes(path):
    if os.name == "nt":
        return file_bytes(path)
    info = path.lstat()
    require(
        stat.S_ISREG(info.st_mode)
        and info.st_uid == os.getuid()
        and not stat.S_IMODE(info.st_mode) & 0o077,
        "Fusion receipt or intent must be a private regular owner file",
    )
    raw = file_bytes(path)
    after = path.lstat()
    require(
        (info.st_dev, info.st_ino, info.st_uid, info.st_mode)
        == (after.st_dev, after.st_ino, after.st_uid, after.st_mode),
        "Fusion receipt or intent owner custody changed",
    )
    return raw


def matches(path, expected):
    try:
        raw = owned_bytes(path)
    except FileNotFoundError:
        return False
    require(raw == expected, "existing Fusion receipt or intent differs")
    return True


# windows holds the checked ancestor chain across inspection and exclusive publication
def seal(path, expected):
    custody = nullcontext()
    if os.name == "nt":
        hold_directory = windows_function("windows_records", "hold_directory")
        custody = hold_directory(path.parent)
    with custody:
        if matches(path, expected):
            return
        try:
            write_new(path, expected)
        except FileExistsError:
            require(
                matches(path, expected), "existing Fusion receipt or intent disappeared"
            )


def submission_intent(store, kind, run, receipt, jobs):
    return {
        "version": 1,
        "store": os.fspath(store.resolve(strict=True)),
        "kind": kind,
        "run": run,
        "receipt": receipt,
        "definitions": {job["id"]: digest(specification(job)) for job in jobs},
    }


def exact_jobs(database, jobs):
    found = []
    for job in jobs:
        spec = specification(job)
        checksum = digest(spec)
        row = database.execute(
            "SELECT definition,definition_hash FROM jobs WHERE id=?", (spec["id"],)
        ).fetchone()
        if row is None:
            continue
        require(
            row["definition_hash"] == checksum and row["definition"] == canonical(spec),
            "existing generated phase job has a different definition",
        )
        found.append(checksum)
    return found


def verify_committed(store, receipt, jobs):
    store = store.resolve(strict=True)
    artifacts = Artifacts(store, create=False)
    with read_store(store / "ledger.sqlite3", None, (4,)) as database:
        row = database.execute(
            "SELECT sha256 FROM bindings WHERE name=?", (receipt["plan_binding"],)
        ).fetchone()
        require(
            row is not None and row["sha256"] == receipt["plan_sha256"],
            "committed Fusion plan binding differs or is absent",
        )
        definitions = exact_jobs(database, jobs)
        require(len(definitions) == 2, "the exact submitted Fusion pair is incomplete")
        for checksum in (row["sha256"], *definitions):
            artifacts.verify(checksum)
