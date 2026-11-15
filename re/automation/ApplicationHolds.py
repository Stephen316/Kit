import re
import json
import time

from Records import digest, label, read_record


def holds_installed(ledger):
    return ledger.db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='application_holds'"
    ).fetchone() is not None


def invalidate_application_hold(ledger, resource):
    if not holds_installed(ledger):
        return
    ledger.db.execute(
        "UPDATE application_holds SET epoch=epoch+1, job_id=NULL, owner=NULL, receipt=NULL, result=NULL"
        " WHERE resource=?", (resource,),
    )


def matched_timeout(row, spec, result, owner):
    if (owner is None or len(spec["resources"]) != 1 or spec["inputs"] or row["active_attempt"] is None
            or type(result.get("session_version")) is not int or result["session_version"] != 1):
        return False
    declared = result.get("result")
    if not isinstance(declared, dict) or declared.get("outcome") != "waiting_application":
        return False
    records = declared.get("records")
    receipt = result.get("receipt")
    if (not isinstance(records, dict) or records.get("application") != "solidworks"
            or records.get("claim") != "unqualified_dispatch" or records.get("native_qualified") is not False
            or not isinstance(receipt, dict) or receipt.get("job_id") != row["id"]
            or receipt.get("attempt") != row["attempts"] or receipt.get("orphan") is not False
            or receipt.get("stop_reason") is not None or receipt.get("exit_status") != 0
            or receipt.get("signal") is not None or receipt.get("receipt_version") != 1):
        return False
    timeout = records.get("queue_timeout")
    if not isinstance(timeout, dict) or set(timeout) != {
        "version", "queue_job_id", "request_sha256", "nonce", "client", "installation", "source_revision",
        "job_id", "kind", "resources", "session", "generation", "fingerprint", "attempt",
    }:
        return False
    expected = {"version": 1, "job_id": row["id"], "kind": spec["kind"], "resources": spec["resources"],
                "installation": records.get("installation"), "session": receipt.get("session"),
                "generation": row["generation"], "fingerprint": row["fingerprint"], "attempt": row["attempts"]}
    client = timeout["client"]
    pinned = {"source_revision": timeout["source_revision"]}
    return (
        all(timeout[key] == value for key, value in expected.items())
        and all(type(timeout[key]) is int for key in ("version", "generation", "attempt"))
        and isinstance(timeout["installation"], str) and isinstance(timeout["session"], str)
        and spec["options"] in (pinned, {**pinned, "readback_operation": "p01-p03-readback"})
        and all(isinstance(timeout[key], str) and re.fullmatch(pattern, timeout[key])
                for key, pattern in (("queue_job_id", "[0-9a-f]{32}"), ("nonce", "[0-9a-f]{48}"),
                                     ("request_sha256", "[0-9a-f]{64}"), ("source_revision", "[0-9a-f]{40}")))
        and isinstance(client, dict) and set(client) == {"pid", "started"} and type(client["pid"]) is int
        and client["pid"] > 0 and isinstance(client["started"], str) and re.fullmatch("windows:[0-9]+", client["started"])
    )


def save_application_hold(ledger, row, spec, result, owner, receipt_hash, result_hash):
    if not matched_timeout(row, spec, result, owner):
        return
    resource = spec["resources"][0]
    capacity = ledger.db.execute("SELECT capacity FROM resources WHERE name=?", (resource,)).fetchone()
    if capacity is None or capacity["capacity"] != 1:
        return
    ledger.db.execute(
        "CREATE TABLE IF NOT EXISTS application_holds ("
        "resource TEXT PRIMARY KEY REFERENCES resources(name), epoch INTEGER NOT NULL,"
        "job_id TEXT, owner TEXT, receipt TEXT, result TEXT)"
    )
    ledger.db.execute(
        "INSERT INTO application_holds VALUES (?,1,?,?,?,?) ON CONFLICT(resource) DO UPDATE SET "
        "epoch=application_holds.epoch+1, job_id=excluded.job_id, owner=excluded.owner,"
        "receipt=excluded.receipt, result=excluded.result",
        (resource, row["id"], owner, receipt_hash, result_hash),
    )
    epoch = ledger.db.execute("SELECT epoch FROM application_holds WHERE resource=?", (resource,)).fetchone()["epoch"]
    ledger.event(row["id"], "application_timeout_hold", {
        "resource": resource, "epoch": epoch, "generation": row["generation"], "fingerprint": row["fingerprint"],
        "attempt": row["attempts"], "execution_id": row["active_attempt"], "receipt": receipt_hash, "result": result_hash,
    })


def retry_delay(spec, attempt):
    return min(300, spec["retry_base_seconds"] * 2 ** (attempt - 1))


def rearm_history(ledger, claim):
    ledger.db.execute(
        "CREATE TABLE IF NOT EXISTS application_rearms ("
        "job_id TEXT NOT NULL, generation INTEGER NOT NULL, attempt INTEGER NOT NULL,"
        "claim_hash TEXT NOT NULL, archive TEXT NOT NULL, PRIMARY KEY(job_id,generation,attempt))"
    )
    return ledger.db.execute(
        "SELECT claim_hash,archive FROM application_rearms WHERE job_id=? AND generation=? AND attempt=?",
        (claim["job_id"], claim["generation"], claim["attempt"]),
    ).fetchone()


def parked_timeout(ledger, claim):
    if not holds_installed(ledger):
        raise ValueError("controller has no application timeout hold")
    job_id = label(claim["job_id"])
    holds = ledger.db.execute("SELECT * FROM application_holds WHERE job_id=?", (job_id,)).fetchall()
    row = ledger.db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if (len(holds) != 1 or row is None or row["state"] != "waiting_application" or row["parked"] != 1
            or row["active_attempt"] is not None or row["generation"] != claim["generation"]
            or row["fingerprint"] != claim["fingerprint"] or row["attempts"] != claim["attempt"]):
        raise ValueError("controller no longer has the exact parked application attempt")
    hold = holds[0]
    owner = claim["original_owner_sha256"]
    if hold["owner"] != owner or hold["receipt"] != row["receipt"] or hold["result"] != row["result"]:
        raise ValueError("application timeout hold no longer belongs to this owner and result")
    ledger.verify_job(row)
    spec = json.loads(row["definition"])
    resource = hold["resource"]
    if spec["resources"] != [resource] or row["attempts"] >= spec["max_attempts"]:
        raise ValueError("application job has no retry budget or its resource differs from the hold")
    available = ledger.db.execute("SELECT available,capacity FROM resources WHERE name=?", (resource,)).fetchone()
    if available is None or available["available"] != 0 or available["capacity"] != 1:
        raise ValueError("application resource is no longer held")
    for key in ("receipt", "result"):
        ledger.verify_object(row[key])
    receipt = read_record(ledger.objects.path(row["receipt"]))
    result = read_record(ledger.objects.path(row["result"]))
    execution = ledger.db.execute("SELECT * FROM attempts WHERE id=?", (receipt["execution_id"],)).fetchone()
    if (receipt["job_id"] != job_id or receipt["outcome"] != "waiting_application"
            or receipt["result_sha256"] != row["result"] or receipt["generation"] != claim["generation"]
            or receipt["fingerprint"] != claim["fingerprint"] or receipt["attempt"] != claim["attempt"]
            or execution is None or execution["ended"] is None or execution["receipt"] != row["receipt"]
            or execution["job_id"] != job_id or execution["generation"] != claim["generation"]
            or execution["fingerprint"] != claim["fingerprint"] or execution["number"] != claim["attempt"]):
        raise ValueError("immutable receipt and attempt do not match the parked application")
    held_attempt = {**dict(row), "active_attempt": receipt["execution_id"]}
    if (not matched_timeout(held_attempt, spec, result, owner) or result["receipt"]["session"] != claim["session"]
            or result.get("application_rearm_intent_sha256") != digest(claim) or spec["kind"] != claim["kind"]):
        raise ValueError("controller result no longer binds the exact supervisor timeout")
    timeout = result["result"]["records"]["queue_timeout"]
    if digest(timeout) != claim["queue_timeout_sha256"]:
        raise ValueError("controller result no longer binds the exact queue timeout")
    return hold, receipt, spec, timeout


def commit_rearm(ledger, claim, hold, receipt, spec, archive):
    ledger.change_resource(hold["resource"], True, unpark_waiters=False)
    due = max(time.time(), receipt["finished_at"] + retry_delay(spec, claim["attempt"]))
    ledger.db.execute("UPDATE jobs SET parked=0,next_run=? WHERE id=?", (due, claim["job_id"]))
    ledger.db.execute(
        "INSERT INTO application_rearms VALUES (?,?,?,?,?)",
        (claim["job_id"], claim["generation"], claim["attempt"], digest(claim), archive),
    )
    ledger.event(claim["job_id"], "application_timeout_rearmed", {
        "receipt": hold["receipt"], "result": hold["result"], "epoch": hold["epoch"],
        "resource": hold["resource"], "archive": archive, "attempt": claim["attempt"], "next_run": due,
    })
    ledger.refresh()
