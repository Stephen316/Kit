import re


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
    return (
        all(timeout[key] == value for key, value in expected.items())
        and all(type(timeout[key]) is int for key in ("version", "generation", "attempt"))
        and isinstance(timeout["installation"], str) and isinstance(timeout["session"], str)
        and spec["options"] == {"source_revision": timeout["source_revision"]}
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
