import argparse
from contextlib import nullcontext
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory

from ApplicationProtocol import (
    ACKNOWLEDGEMENT,
    BOOTSTRAP,
    FUSION_PROVIDER,
    PROTOCOL,
    committed_bytes,
    directory,
    encoded,
    file_bytes,
    identity,
    owner_lock,
    require,
    sha256,
    validate_configuration,
    write_new,
)
from AuditFusionPhases import (
    StoreSnapshot,
    phase_evidence,
    phase_row,
    validate_queue,
    verify_binding,
)
from FusionRestart import accepted_handoff
from StoreRead import read_store


def phase_acceptance(database, queue, config):
    with read_store(database, None, (4,)) as connection, TemporaryDirectory(
        prefix="kit-fusion-owner-restart-"
    ) as temporary:
        owner = StoreSnapshot(connection, database.parent)
        scratch = Path(temporary)
        row = phase_row(owner, queue, "a")
        require(
            phase_row(owner, queue, "b")["state"] != "completed",
            "Fusion phase B is already complete",
        )
        verify_binding(owner, queue, scratch)
        evidence = phase_evidence(owner, queue, "a", scratch / "phase-a")
        raw = file_bytes(scratch / "phase-a" / "dispatch.json")
    dispatch = json.loads(raw)
    handoff = accepted_handoff(config, dispatch["proof"], queue["plan_sha256"])
    require(
        evidence["process"]["start_unix_seconds"] == start_seconds(handoff["host"]),
        "accepted Fusion report and restart handoff differ on process creation time",
    )
    return row, evidence, handoff


def start_seconds(host):
    started = host["started"]
    if os.name == "nt":
        require(started.startswith("windows:"), "invalid Windows process creation time")
        return int(started.removeprefix("windows:")) // 10_000_000 - 11_644_473_600
    return int(
        datetime.strptime(started, "%a %b %d %H:%M:%S %Y")
        .replace(tzinfo=timezone.utc)
        .timestamp()
    )


def verify_retained(root, handoff):
    require(
        not os.path.lexists(root / ACKNOWLEDGEMENT),
        "Fusion phase A acknowledgement is still pending",
    )
    jobs = directory(root / "jobs")
    require(
        not os.path.lexists(jobs / handoff["job_id"]),
        "accepted Fusion phase A spool is still retained",
    )
    fence = file_bytes(root / "fence.json")
    require(
        fence == encoded(handoff),
        "retained Fusion restart fence differs from accepted phase A",
    )
    host = handoff["host"]
    require(
        identity(host["pid"]) == host,
        "the exact prior Fusion process is no longer live",
    )
    return sha256(fence)


def record_restart(installation, store, queue_path, *, check=False):
    installation_bytes, queue_bytes = file_bytes(installation), file_bytes(queue_path)
    config = validate_configuration(json.loads(installation_bytes))
    queue = validate_queue(json.loads(queue_bytes))
    require(
        config["application"] == "fusion"
        and config["installation"] == queue["installation"]
        and config["source_revision"] == queue["source_revision"],
        "owner installation differs from the queued Fusion plan",
    )
    protocol = sha256(committed_bytes(config, PROTOCOL))
    bootstrap = sha256(committed_bytes(config, BOOTSTRAP))
    root = directory(config["endpoint"])
    database = directory(store) / "ledger.sqlite3"
    file_info = database.lstat()
    require(
        database.is_file()
        and not database.is_symlink()
        and file_info.st_nlink == 1
        and not getattr(file_info, "st_file_attributes", 0) & 0x400,
        "expected an initialized A03 store",
    )
    row, evidence, handoff = phase_acceptance(database, queue, config)
    lock_path = root / "dispatch.lock"
    with nullcontext() if check else owner_lock(lock_path):
        fence = verify_retained(root, handoff)
        intent = {
            "version": 1,
            "provider": FUSION_PROVIDER,
            "installation": config["installation"],
            "installation_sha256": sha256(installation_bytes),
            "source_revision": config["source_revision"],
            "protocol_sha256": protocol,
            "bootstrap_sha256": bootstrap,
            "queue_receipt_sha256": sha256(queue_bytes),
            "store_path_sha256": sha256(os.fsencode(database.parent)),
            "controller_job": row["id"],
            "attempt": row["attempts"],
            "generation": row["generation"],
            "fingerprint": row["fingerprint"],
            "receipt_sha256": evidence["receipt_sha256"],
            "result_sha256": evidence["result_sha256"],
            "dispatch_sha256": evidence["artifacts"]["dispatch"]["sha256"],
            "fusion_version": evidence["fusion_version"],
            "restart_handoff": handoff,
            "fence_sha256": fence,
        }
        content = encoded(intent)
        path = root / f"restart-intent-{handoff['job_id']}.json"
        existing = check or os.path.lexists(path)
        if existing:
            require(
                file_bytes(path) == content,
                "durable Fusion restart intent differs from current evidence",
            )
        with read_store(database, None, (4,)) as connection:
            owner = StoreSnapshot(connection, database.parent)
            require(
                phase_row(owner, queue, "a") == row
                and phase_row(owner, queue, "b")["state"] != "completed",
                "controller phase A changed during restart verification",
            )
        require(
            file_bytes(installation) == installation_bytes
            and file_bytes(queue_path) == queue_bytes
            and verify_retained(root, handoff) == fence,
            "Fusion restart inputs changed during verification",
        )
        if not existing:
            write_new(path, content)
    return {
        "status": "intent_verified" if check else "intent_recorded",
        "intent": str(path),
        "intent_sha256": sha256(content),
        "native_lifecycle_performed": False,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Record or verify an acknowledged Fusion restart intent without changing processes"
    )
    parser.add_argument("--installation", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--queue-receipt", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = record_restart(
            args.installation, args.store, args.queue_receipt, check=args.check
        )
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        RecursionError,
        sqlite3.Error,
        subprocess.SubprocessError,
    ) as error:
        print(
            f"Fusion restart intent refused: {type(error).__name__}: {error}"[:2048],
            file=sys.stderr,
        )
        return 1
    print(encoded(result).decode(), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
