import json
import math
import time

from ApplicationProtocol import file_bytes, require, sha256
from AuditFusionPhases import StoreSnapshot, phase_row, validate_queue
from FusionQueueReceipt import owned_bytes
from Records import specification
from StoreRead import read_store

ACTIONABLE = ("queued", "running")


def pairs(inbox, config, store):
    for pending in sorted(inbox.glob(".*.intent.json")):
        target = pending.name.removeprefix(".").removesuffix(".intent.json")
        if not target or target.startswith(".") or not target.endswith(".json"):
            continue
        saved = json.loads(owned_bytes(pending))
        queue = validate_queue(saved["receipt"])
        if (
            saved["store"] == str(store)
            and queue["installation"] == config["installation"]
            and queue["source_revision"] == config["source_revision"]
            and queue["supervised_acknowledgement"] is True
        ):
            yield inbox / target, queue


def select_pair(store, inbox, config, fence):
    with read_store(store / "ledger.sqlite3", None, (4,)) as database:
        owner = StoreSnapshot(database, store)
        selected = None
        for path, queue in pairs(inbox, config, store):
            if queue["plan_sha256"] != fence["plan_sha256"]:
                continue
            rows = owner.ReadStatus(queue["jobs"]["a"])["jobs"]
            if not rows or rows[0]["state"] != "completed":
                continue
            checksum = rows[0]["result"]
            raw = file_bytes(owner.objects.path(checksum))
            require(
                sha256(raw) == checksum, "accepted Phase A result integrity mismatch"
            )
            accepted = json.loads(raw)
            if accepted["result"]["records"].get("restart_handoff") != fence:
                continue
            phase_row(owner, queue, "a")
            current = phase_row(owner, queue, "b")
            if selected is None:
                selected = path, queue, current["state"]
            else:
                require(
                    queue == selected[1],
                    "retained Fusion fence matches more than one queued pair",
                )
    return selected


def phase_state(store, queue, active, grace, maximum, *, verify_complete=False):
    with read_store(store / "ledger.sqlite3", None, (4,)) as database:
        owner = StoreSnapshot(database, store)
        first = phase_row(owner, queue, "a")
        require(
            first["state"] == "completed"
            and first["receipt"] == active["receipt_sha256"]
            and first["result"] == active["result_sha256"]
            and first["attempts"] == active["attempt"]
            and first["generation"] == active["generation"]
            and first["fingerprint"] == active["fingerprint"],
            "Fusion lifecycle lost its exact accepted Phase A",
        )
        second = phase_row(owner, queue, "b")
        if verify_complete and second["state"] == "completed":
            for row in (first, second):
                for key in ("receipt", "result"):
                    owner.objects.verify(row[key])
        if second["state"] != "running":
            return second, 0
        resource = database.execute(
            "SELECT available,capacity FROM resources WHERE name=?",
            (queue["resource"],),
        ).fetchone()
        require(
            resource is not None and resource["capacity"] == 1,
            "Fusion lifecycle requires the counted installation resource",
        )
        other = database.execute(
            "SELECT 1 FROM jobs JOIN job_resources ON jobs.id=job_resources.job_id "
            "WHERE job_resources.resource=? AND jobs.state='running' AND jobs.id<>? LIMIT 1",
            (queue["resource"], second["id"]),
        ).fetchone()
        if not resource["available"] or other is not None:
            return second, 0
        spec = specification(json.loads(second["definition"]))
        reserve = min(grace + 2, spec["timeout_seconds"] / 2) + 1
        claim = database.execute(
            "SELECT jobs.deadline,jobs.lease_until,attempts.started FROM jobs "
            "JOIN attempts ON jobs.active_attempt=attempts.id WHERE jobs.id=?",
            (second["id"],),
        ).fetchone()
        now = time.time()
        if claim is None or claim["lease_until"] <= now:
            return second, 0
        remaining = (
            min(
                claim["deadline"] - reserve,
                claim["started"] + 300,
                claim["lease_until"],
            )
            - now
        )
        return second, max(0, min(maximum, math.floor(remaining)))
