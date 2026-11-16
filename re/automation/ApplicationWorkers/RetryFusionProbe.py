import argparse
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from ArchiveFusionProbe import current_probe
from AuditFusionPhases import read_queue
from ApplicationHolds import retry_delay
from ApplicationProtocol import ACKNOWLEDGEMENT, directory, owner_lock, require
from Artifacts import Artifacts
from FusionArchiveControl import paths as control_paths
from FusionTimeoutAudit import inspect_archive
from Ledger import Ledger
from QueueFusionPhases import queue_configuration
from Records import canonical, read_record, specification
from StoreRead import read_store

ACTION = "application_archived_fusion_probe_retry"


def prior_retry(connection, queue, kind, archive_sha256):
    row = connection.execute(
        "SELECT detail FROM events WHERE job_id=? AND action=? AND "
        "json_extract(detail, '$.archive_manifest_sha256')=? LIMIT 1",
        (queue["jobs"]["a"], ACTION, archive_sha256),
    ).fetchone()
    if row is None:
        return None
    event = json.loads(row["detail"])
    require(
        event["installation"] == queue["installation"]
        and event["resource"] == queue["resource"]
        and event["plan_sha256"] == queue["plan_sha256"]
        and event["source_revision"] == queue["source_revision"]
        and event["kind"] == kind,
        "the recorded Fusion retry belongs to another queue receipt",
    )
    return {
        "status": "retry_already_requested",
        "archive_manifest_sha256": archive_sha256,
    }


def require_exclusive_resource(connection, queue):
    other = connection.execute(
        "SELECT 1 FROM job_resources AS r JOIN jobs AS j ON j.id=r.job_id "
        "WHERE r.resource=? AND j.id NOT IN (?,?) "
        "AND j.state NOT IN ('completed','failed','rejected') LIMIT 1",
        (queue["resource"], queue["jobs"]["a"], queue["jobs"]["b"]),
    ).fetchone()
    require(other is None, "Fusion resource has unrelated unfinished jobs")


def retry_timing(connection, objects, queue, timeout):
    row = connection.execute(
        "SELECT * FROM jobs WHERE id=?", (queue["jobs"]["a"],)
    ).fetchone()
    spec = specification(json.loads(row["definition"]))
    require(
        row["attempts"] < spec["max_attempts"], "Fusion Phase A has no retry budget"
    )
    receipt = read_record(objects.path(timeout["receipt_sha256"]))
    due = max(time.time(), receipt["finished_at"] + retry_delay(spec, row["attempts"]))
    return row, due


# both owner and manual admission retain the retry deadline and exact target row
def make_retry_runnable(ledger, queue, due):
    job_id = queue["jobs"]["a"]
    ledger.change_resource(queue["resource"], True, unpark_waiters=False)
    ledger.db.execute("UPDATE jobs SET parked=0,next_run=? WHERE id=?", (due, job_id))
    ledger.refresh()
    first, second = (
        ledger.db.execute(
            "SELECT state FROM jobs WHERE id=?", (queue["jobs"][phase],)
        ).fetchone()["state"]
        for phase in ("a", "b")
    )
    require(
        first == "queued" and second == "waiting_evidence",
        "Fusion retry did not leave Phase B behind its accepted evidence gate",
    )


def queue_retry(ledger, queue, timeout, archive_sha256):
    job_id = queue["jobs"]["a"]
    row, due = retry_timing(ledger.db, ledger.objects, queue, timeout)
    make_retry_runnable(ledger, queue, due)
    ledger.event(
        job_id,
        ACTION,
        {
            "installation": queue["installation"],
            "resource": queue["resource"],
            "plan_sha256": queue["plan_sha256"],
            "source_revision": queue["source_revision"],
            "previous_receipt_sha256": timeout["receipt_sha256"],
            "previous_result_sha256": timeout["result_sha256"],
            "archive_manifest_sha256": archive_sha256,
            "kind": row["kind"],
            "generation": row["generation"],
            "attempt": row["attempts"],
            "next_run": due,
        },
    )
    return {"status": "retry_queued", "archive_manifest_sha256": archive_sha256}


def retry_configuration(config_path, queue, kind):
    store, config, _ = queue_configuration(config_path, kind, queue["resource"])
    require(
        config["installation"] == queue["installation"]
        and config["source_revision"] == queue["source_revision"],
        "installed Fusion owner configuration differs from the queued plan",
    )
    return store, config, directory(config["endpoint"])


def require_idle(root):
    require(
        not any(directory(root / "jobs").iterdir())
        and all(
            not os.path.lexists(root / name)
            for name in (ACKNOWLEDGEMENT, "grant.json", "fence.json")
        ),
        "Fusion installation has active or fenced application work",
    )


def require_archive(
    connection, store, root, config, queue, kind, archive_sha256, scratch
):
    timeout = current_probe(connection, store, queue, kind, scratch)
    observed = inspect_archive(root, config, timeout)
    require(
        observed
        == {
            "status": "archived",
            "archive_manifest_sha256": archive_sha256,
            "fence_status": "absent",
        },
        "Fusion retry must name its exact current archive manifest after quarantine release",
    )
    require(
        not any(os.path.lexists(path) for path in control_paths(root, archive_sha256).values()),
        "Fusion retry is reserved for the archived control owner",
    )
    require_exclusive_resource(connection, queue)
    return timeout


def retry_probe(config_path, queue, kind, archive_sha256):
    store, config, root = retry_configuration(config_path, queue, kind)
    with (
        owner_lock(root / "dispatch.lock"),
        Ledger(directory(store)) as ledger,
        TemporaryDirectory(prefix="kit-fusion-probe-retry-") as temporary,
    ):
        previous = prior_retry(ledger.db, queue, kind, archive_sha256)
        if previous is not None:
            return previous
        require_idle(root)
        ledger.refresh()
        timeout = require_archive(
            ledger.db, store, root, config, queue, kind, archive_sha256, Path(temporary)
        )
        return queue_retry(ledger, queue, timeout, archive_sha256)


def observe_retry(config_path, queue_path, kind, archive_sha256):
    readiness = {"physical_host_readiness": "unverified"}
    stage = "queue_configuration"
    try:
        require(
            re.fullmatch("[0-9a-f]{64}", archive_sha256),
            "expected the exact archive manifest SHA-256",
        )
        queue = read_queue(queue_path)
        store, config, root = retry_configuration(config_path, queue, kind)
        stage = "controller_snapshot"
        database = directory(store) / "ledger.sqlite3"
        require(
            database.is_file() and not database.is_symlink(),
            "expected an initialized A03 store",
        )
        with (
            read_store(database, None, (4,)) as connection,
            TemporaryDirectory(prefix="kit-fusion-retry-observe-") as temporary,
        ):
            previous = prior_retry(connection, queue, kind, archive_sha256)
            if previous is not None:
                return {
                    **readiness,
                    "retry_admissibility": "already_requested",
                    "archive_manifest_sha256": archive_sha256,
                }, 0
            stage = "endpoint"
            require_idle(root)
            stage = "archive_and_resource"
            timeout = require_archive(
                connection,
                store,
                root,
                config,
                queue,
                kind,
                archive_sha256,
                Path(temporary),
            )
            stage = "retry_budget"
            retry_timing(connection, Artifacts(store, create=False), queue, timeout)
        return {
            **readiness,
            "retry_admissibility": "eligible_at_snapshot",
            "archive_manifest_sha256": archive_sha256,
        }, 0
    except (OSError, ValueError, KeyError, TypeError, RecursionError, sqlite3.Error):
        return {
            **readiness,
            "retry_admissibility": "blocked_or_unverified",
            "stage": stage,
        }, 1


def main():
    parser = argparse.ArgumentParser(
        description="Permit retry of an archived Phase A Fusion probe"
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--queue-receipt", type=Path, required=True)
    parser.add_argument("--archive-manifest-sha256", required=True)
    parser.add_argument("--kind", default="capture.fusion")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        result, status = observe_retry(
            args.config, args.queue_receipt, args.kind, args.archive_manifest_sha256
        )
        print(canonical(result))
        return status
    try:
        require(
            sys.platform == "darwin",
            "Fusion probe retry requires the macOS installation owner",
        )
        require(
            re.fullmatch("[0-9a-f]{64}", args.archive_manifest_sha256),
            "expected the exact archive manifest SHA-256",
        )
        result = retry_probe(
            args.config,
            read_queue(args.queue_receipt),
            args.kind,
            args.archive_manifest_sha256,
        )
    except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
        print(
            f"Fusion probe retry refused: {type(error).__name__}: {error}"[:2048],
            file=sys.stderr,
        )
        return 1
    print(canonical(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
