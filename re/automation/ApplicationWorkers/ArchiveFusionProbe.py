import argparse
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from AuditFusionPhases import StoreSnapshot, phase_row, read_queue, verify_binding
from ApplicationProtocol import (
    ACKNOWLEDGEMENT,
    check_spool,
    directory,
    exclusive_rename,
    file_bytes,
    identity,
    owner_lock,
    pin,
    record,
    require,
    sha256,
    sync_directory,
    write_record,
)
from FusionTimeoutAudit import match_request, parked_timeout
from QueueFusionPhases import queue_configuration
from Records import canonical
from StoreRead import read_store

ARCHIVE_RECORD = "ProbeArchive.json"
PROBE_FILES = {"cancel.json", "plan.json", "probe.request"}


def current_probe(connection, store, queue, kind, scratch):
    require(
        connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete",
        "Fusion archival requires the ordinary A03 read lock",
    )
    resource = connection.execute(
        "SELECT available,capacity FROM resources WHERE name=?",
        (queue["resource"],),
    ).fetchone()
    require(
        resource is not None and tuple(resource) == (0, 1),
        "Fusion installation resource must still be parked with capacity one",
    )
    owner = StoreSnapshot(connection, store)
    verify_binding(owner, queue, scratch)
    first, second = (phase_row(owner, queue, phase) for phase in ("a", "b"))
    held = connection.execute(
        "SELECT parked,active_attempt FROM jobs WHERE id=?",
        (first["id"],),
    ).fetchone()
    require(
        first["kind"] == second["kind"] == kind
        and first["state"] == "waiting_application"
        and second["state"] == "waiting_evidence"
        and held is not None
        and tuple(held) == (1, None)
        and first["result"] is not None
        and first["receipt"] is not None,
        "current Fusion pair does not have a settled Phase A application hold",
    )
    timeout = parked_timeout(owner, first, queue, "a", scratch / "phase-a")
    require(
        timeout is not None and timeout["operation"] == "probe",
        "Fusion Phase A is parked outside the unclaimed probe archive contract",
    )
    return timeout


def archive_record(spool, config, timeout, fence):
    check_spool(spool)
    found = {path.name for path in spool.iterdir()}
    require(
        found in (PROBE_FILES, PROBE_FILES | {ARCHIVE_RECORD}),
        "Fusion spool must contain only the untouched Phase A probe and its cancellation",
    )
    request = match_request(file_bytes(spool / "probe.request"), config, timeout, "a")
    cancel = record(spool / "cancel.json")
    require(
        request["body"] == {"plan_sha256": timeout["plan_sha256"]}
        and sha256(file_bytes(spool / "plan.json")) == timeout["plan_sha256"],
        "Fusion probe does not retain the exact queued plan",
    )
    require(
        set(fence) == {"installation", "job_id", "reason", "host", "at"}
        and fence["installation"] == config["installation"]
        and fence["job_id"] == timeout["queue_job_id"]
        and fence["reason"] == "quarantined"
        and fence["host"] is None
        and set(cancel) == {"reason", "at"}
        and cancel["reason"]
        == "requesting worker stopped before application completion"
        and type(cancel["at"]) in (int, float)
        and type(fence["at"]) in (int, float)
        and request["deadline"] <= cancel["at"] <= fence["at"] <= time.time(),
        "Fusion probe lacks its exact hostless quarantine and expired cancellation",
    )
    require(
        identity(request["client"]["pid"]) != request["client"],
        "the timed out Fusion request process is still present",
    )
    return {
        "archive_version": 1,
        "installation": config["installation"],
        "phase": "a",
        "timeout": timeout,
        "fence": fence,
        "files": {name: pin(spool / name, name) for name in sorted(PROBE_FILES)},
    }


def optional_record(path):
    try:
        return record(path)
    except FileNotFoundError:
        return None


def relocate(root, config, timeout):
    require(
        not os.path.lexists(root / ACKNOWLEDGEMENT)
        and not os.path.lexists(root / "grant.json"),
        "Fusion installation has a retained acknowledgement or application grant",
    )
    jobs = directory(root / "jobs")
    active = jobs / timeout["queue_job_id"]
    failed = root / "failed-spools"
    archived = failed / active.name
    if os.path.lexists(failed):
        directory(failed)
    already_moved = os.path.lexists(archived)
    require(
        list(jobs.iterdir()) == ([] if already_moved else [active]),
        "Fusion installation has another pending spool",
    )
    spool = directory(archived if already_moved else active)
    fence_path = root / "fence.json"
    fence = optional_record(fence_path)
    prior = optional_record(spool / ARCHIVE_RECORD)
    require(
        fence is not None or (already_moved and prior is not None),
        "Fusion installation has no matching quarantine to archive",
    )
    expected = archive_record(
        spool, config, timeout, fence if fence is not None else prior["fence"]
    )
    if prior is None:
        require(
            not already_moved, "retained Fusion archive is missing its identity record"
        )
        write_record(spool / ARCHIVE_RECORD, expected)
    else:
        require(
            prior == expected, "retained Fusion archive identity or file bytes changed"
        )
    if not already_moved:
        directory(failed, True)
        sync_directory(root)
        exclusive_rename(spool, archived)
    sync_directory(jobs)
    sync_directory(failed)
    require(
        record(archived / ARCHIVE_RECORD) == expected,
        "Fusion archive manifest changed during publication",
    )
    manifest_sha256 = pin(archived / ARCHIVE_RECORD, ARCHIVE_RECORD)["sha256"]
    status = "already_archived"
    if fence is not None:
        require(
            record(fence_path) == fence,
            "Fusion quarantine changed during archive publication",
        )
        fence_path.unlink()
        sync_directory(root)
        status = "archive_resumed" if already_moved else "archived"
    return {
        "status": status,
        "queue_job_id": timeout["queue_job_id"],
        "request_sha256": timeout["request_sha256"],
        "archive_manifest_sha256": manifest_sha256,
        "resource_rearmed": False,
    }


def archive_probe(config_path, queue, kind):
    store, config, _ = queue_configuration(config_path, kind, queue["resource"])
    require(
        config["installation"] == queue["installation"]
        and config["source_revision"] == queue["source_revision"],
        "installed Fusion owner configuration differs from the queued plan",
    )
    root = directory(config["endpoint"])
    database = directory(store) / "ledger.sqlite3"
    require(
        database.is_file() and not database.is_symlink(),
        "expected an initialized A03 store",
    )
    with (
        owner_lock(root / "dispatch.lock"),
        owner_lock(root / "host.lock"),
        read_store(database, None, (4,)) as connection,
        TemporaryDirectory(prefix="kit-fusion-probe-archive-") as temporary,
    ):
        timeout = current_probe(connection, store, queue, kind, Path(temporary))
        return relocate(root, config, timeout)


def main():
    parser = argparse.ArgumentParser(
        description="Archive one unclaimed timed out Phase A Fusion probe"
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--queue-receipt", type=Path, required=True)
    parser.add_argument("--kind", default="capture.fusion")
    args = parser.parse_args()
    try:
        require(
            sys.platform == "darwin",
            "Fusion probe archival requires the macOS installation owner",
        )
        result = archive_probe(args.config, read_queue(args.queue_receipt), args.kind)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        sqlite3.Error,
        subprocess.SubprocessError,
    ) as error:
        print(
            f"Fusion probe archive refused: {type(error).__name__}: {error}"[:2048],
            file=sys.stderr,
        )
        return 1
    print(canonical(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
