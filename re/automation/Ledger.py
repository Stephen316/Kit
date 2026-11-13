import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from collections import deque
from pathlib import Path

from Artifacts import Artifacts
from Records import bounded, canonical, digest, label, reason_text, specification


class Ledger:
    def __init__(self, root, create=False, max_running=4):
        root = Path(root).resolve()
        database = root / "ledger.sqlite3"
        if database.is_symlink():
            raise ValueError("database cannot be a symbolic link")
        if not create and not database.is_file():
            raise ValueError("store is not initialized")
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.objects = Artifacts(root)
        self.db = sqlite3.connect(database, timeout=30, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        try:
            version = self.db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise ValueError("unsupported research store version")
            self.db.execute("PRAGMA foreign_keys=ON")
            self.db.execute("PRAGMA journal_mode=DELETE")
            self.db.execute("PRAGMA synchronous=FULL")
            self.db.execute("BEGIN IMMEDIATE")
            version = self.db.execute("PRAGMA user_version").fetchone()[0]
            if version == 0:
                if not create or self.db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchone():
                    raise ValueError("unrecognized research database")
                for statement in Path(__file__).with_name("Schema.sql").read_text().split(";"):
                    if statement.strip():
                        self.db.execute(statement)
                self.db.execute("INSERT INTO settings VALUES (?,?)", ("max_running", bounded(max_running, 1, 64)))
                self.db.execute("PRAGMA user_version=1")
            self.db.execute("COMMIT")
            os.chmod(database, 0o600)
        except BaseException:
            self.db.close()
            raise

    def __enter__(self):
        self.db.execute("BEGIN IMMEDIATE")
        self.checked = set()
        self.refreshed = False
        return self

    def __exit__(self, kind, value, traceback):
        try:
            self.db.execute("ROLLBACK" if kind else "COMMIT")
        finally:
            self.db.close()

    def event(self, job_id, action, detail):
        self.db.execute("INSERT INTO events(at,job_id,action,detail) VALUES (?,?,?,?)", (time.time(), job_id, action, canonical(detail)))

    def verify_object(self, sha256):
        if sha256 not in self.checked:
            self.objects.verify(sha256)
            self.checked.add(sha256)

    def bind(self, name, path):
        name = label(name)
        sha256 = self.objects.put_file(path)
        self.db.execute("INSERT INTO bindings VALUES (?,?) ON CONFLICT(name) DO UPDATE SET sha256=excluded.sha256", (name, sha256))
        self.refreshed = False
        self.event(None, "binding", {"name": name, "sha256": sha256})
        self.refresh()
        return {"name": name, "sha256": sha256}

    def resource(self, name, available):
        name = label(name)
        previous = self.db.execute("SELECT available FROM resources WHERE name=?", (name,)).fetchone()
        self.db.execute("INSERT INTO resources VALUES (?,?) ON CONFLICT(name) DO UPDATE SET available=excluded.available", (name, int(available)))
        if available and (previous is None or not previous[0]):
            for row in self.db.execute("SELECT id,definition FROM jobs WHERE state='waiting_application' AND parked=1").fetchall():
                if name in json.loads(row["definition"])["resources"]:
                    self.db.execute("UPDATE jobs SET parked=0 WHERE id=?", (row["id"],))
        self.refreshed = False
        self.event(None, "resource", {"name": name, "available": bool(available)})
        self.refresh()
        return {"name": name, "available": bool(available)}

    def store_spec(self, spec):
        encoded = canonical(spec)
        previous = self.db.execute("SELECT definition_hash FROM jobs WHERE id=?", (spec["id"],)).fetchone()
        if previous is not None and previous[0] == digest(spec):
            return
        self.objects.put_record(spec)
        self.db.execute(
            "INSERT INTO jobs(id,definition,definition_hash,state,fingerprint,created) VALUES (?,?,?,'queued','',?) "
            "ON CONFLICT(id) DO UPDATE SET definition=excluded.definition,definition_hash=excluded.definition_hash",
            (spec["id"], encoded, digest(spec), time.time()),
        )
        self.db.execute("DELETE FROM dependencies WHERE job_id=?", (spec["id"],))
        self.db.executemany("INSERT INTO dependencies VALUES (?,?)", [(spec["id"], item) for item in spec["depends_on"]])
        self.event(spec["id"], "submitted", {"definition_hash": digest(spec)})
        self.refreshed = False

    def submit_many(self, values):
        if not isinstance(values, list) or not 1 <= len(values) <= 10000:
            raise ValueError("batch must contain 1–10000 job records")
        specs = [specification(value) for value in values]
        if len({spec["id"] for spec in specs}) != len(specs):
            raise ValueError("batch contains duplicate job identifiers")
        for spec in specs:
            self.store_spec(spec)
        count, size = self.db.execute("SELECT COUNT(*),COALESCE(SUM(length(CAST(definition AS BLOB))),0) FROM jobs").fetchone()
        if count > 10000 or size > 16 * 1024 * 1024:
            raise ValueError("store job metadata limit exceeded")
        self.refresh()
        return {"submitted": len(specs)}

    def submit(self, value):
        self.submit_many([value])
        return self.status(value["id"])

    def snapshot(self, spec):
        self.verify_object(digest(spec))
        inputs = {}
        for role, name in spec["inputs"].items():
            row = self.db.execute("SELECT sha256 FROM bindings WHERE name=?", (name,)).fetchone()
            if row is None:
                return None
            self.verify_object(row[0])
            inputs[role] = {"binding": name, "sha256": row[0]}
        dependencies = {}
        for name in spec["depends_on"]:
            row = self.db.execute("SELECT state,receipt,result FROM jobs WHERE id=?", (name,)).fetchone()
            if row is None or row["state"] != "completed":
                return None
            self.verify_object(row["receipt"])
            self.verify_object(row["result"])
            dependencies[name] = {"receipt": row["receipt"], "result": row["result"]}
        return {"definition_hash": digest(spec), "inputs": inputs, "dependencies": dependencies}

    def revoke(self, row, reason):
        receipt = None
        if row["active_attempt"] is not None:
            previous = self.db.execute("SELECT ended,receipt FROM attempts WHERE id=?", (row["active_attempt"],)).fetchone()
            receipt = previous["receipt"]
            if previous["ended"] is None:
                if reason in ("invalidated", "resource_unavailable"):
                    prior_hash = json.loads(row["snapshot"])["definition_hash"]
                    self.verify_object(prior_hash)
                    prior_spec = json.loads(self.objects.path(prior_hash).read_text(encoding="utf-8"))
                    for resource in prior_spec["resources"]:
                        self.db.execute("UPDATE resources SET available=0 WHERE name=?", (resource,))
                        self.event(None, "resource_recovery_required", {"name": resource})
                receipt = self.objects.put_record({
                    "receipt_version": 1, "job_id": row["id"], "generation": row["generation"],
                    "attempt": row["attempts"], "execution_id": row["active_attempt"],
                    "fingerprint": row["fingerprint"], "snapshot": json.loads(row["snapshot"]),
                    "worker": row["worker"], "outcome": reason, "result_sha256": None,
                    "finished_at": time.time(),
                })
                self.db.execute("UPDATE attempts SET ended=?,outcome=?,receipt=? WHERE id=?", (time.time(), reason, receipt, row["active_attempt"]))
        self.db.execute("UPDATE jobs SET worker=NULL,token_hash=NULL,lease_until=NULL,deadline=NULL,active_attempt=NULL WHERE id=?", (row["id"],))
        return receipt

    def refresh(self):
        if self.refreshed:
            return
        pending = {row["id"]: row for row in self.db.execute("SELECT * FROM jobs ORDER BY id").fetchall()}
        specs = {name: json.loads(row["definition"]) for name, row in pending.items()}
        children = {name: [] for name in pending}
        indegree = {name: 0 for name in pending}
        for name, spec in specs.items():
            for parent in spec["depends_on"]:
                if parent in pending:
                    children[parent].append(name)
                    indegree[name] += 1
        ready = deque(name for name in pending if indegree[name] == 0)
        visited = 0
        while ready:
            name = ready.popleft()
            row = pending[name]
            spec = specs[name]
            snapshot = self.snapshot(spec)
            fingerprint = digest(snapshot) if snapshot is not None else None
            if fingerprint is not None and row["fingerprint"] == fingerprint:
                self.verify_object(fingerprint)
            if row["fingerprint"] != fingerprint:
                self.revoke(row, "invalidated")
                if snapshot is not None:
                    self.objects.put_record(snapshot)
                self.db.execute(
                    "UPDATE jobs SET generation=generation+1,fingerprint=?,snapshot=?,attempts=0,parked=0,next_run=0,"
                    "receipt=NULL,result=NULL,state='queued',reason=? WHERE id=?",
                    (fingerprint, canonical(snapshot) if snapshot is not None else None, "prerequisites changed", name),
                )
                self.event(name, "invalidated", {"fingerprint": fingerprint})
                row = self.db.execute("SELECT * FROM jobs WHERE id=?", (name,)).fetchone()
            if row["state"] == "running" and min(row["lease_until"], row["deadline"]) <= time.time():
                self.expire(row, spec)
                row = self.db.execute("SELECT * FROM jobs WHERE id=?", (name,)).fetchone()
            unavailable = any(not self.db.execute("SELECT 1 FROM resources WHERE name=? AND available=1", (resource,)).fetchone() for resource in spec["resources"])
            if row["state"] == "running" and unavailable:
                receipt = self.revoke(row, "resource_unavailable")
                self.db.execute("UPDATE jobs SET state='waiting_application',parked=0,receipt=?,result=NULL,reason=? WHERE id=?", (receipt, "resource unavailable", name))
                row = self.db.execute("SELECT * FROM jobs WHERE id=?", (name,)).fetchone()
            if row["state"] == "completed":
                self.verify_object(row["receipt"])
                self.verify_object(row["result"])
            elif row["state"] != "running" and not row["parked"] and row["state"] not in ("failed", "rejected"):
                state = "waiting_evidence" if snapshot is None else "waiting_application" if unavailable else "queued"
                self.db.execute("UPDATE jobs SET state=? WHERE id=?", (state, name))
            visited += 1
            for child in children[name]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    ready.append(child)
        if visited != len(pending):
            raise ValueError("job dependency cycle")
        for row in self.db.execute("SELECT id FROM jobs WHERE parked=0 AND fingerprint IS NOT NULL AND state IN ('queued','waiting_application')").fetchall():
            unavailable = any(not self.db.execute("SELECT 1 FROM resources WHERE name=? AND available=1", (resource,)).fetchone() for resource in specs[row["id"]]["resources"])
            self.db.execute("UPDATE jobs SET state=? WHERE id=?", ("waiting_application" if unavailable else "queued", row["id"]))
        self.refreshed = True

    def expire(self, row, spec):
        receipt = self.revoke(row, "expired")
        for resource in spec["resources"]:
            self.db.execute("UPDATE resources SET available=0 WHERE name=?", (resource,))
            self.event(None, "resource_recovery_required", {"name": resource})
        state = "failed" if row["attempts"] >= spec["max_attempts"] else "queued"
        delay = min(300, spec["retry_base_seconds"] * 2 ** (row["attempts"] - 1))
        self.db.execute("UPDATE jobs SET state=?,next_run=?,receipt=?,result=NULL,reason=? WHERE id=?", (state, time.time() + delay, receipt, "lease or execution timeout expired", row["id"]))
        self.event(row["id"], "expired", {"attempt": row["attempts"], "state": state})

    def claim(self, worker):
        worker = label(worker)
        self.refresh()
        maximum = self.db.execute("SELECT value FROM settings WHERE key='max_running'").fetchone()[0]
        running = self.db.execute("SELECT * FROM jobs WHERE state='running'").fetchall()
        if len(running) >= maximum:
            return {"job": None, "reason": "concurrency limit"}
        busy = {resource for row in running for resource in json.loads(row["definition"])["resources"]}
        for row in self.db.execute("SELECT * FROM jobs WHERE state='queued' AND next_run<=? ORDER BY created,id", (time.time(),)).fetchall():
            spec = json.loads(row["definition"])
            if any(not self.db.execute("SELECT 1 FROM resources WHERE name=? AND available=1", (resource,)).fetchone() for resource in spec["resources"]):
                continue
            if busy.intersection(spec["resources"]):
                continue
            if row["attempts"] >= spec["max_attempts"]:
                self.db.execute("UPDATE jobs SET state='failed',reason=? WHERE id=?", ("attempt budget exhausted", row["id"]))
                continue
            now = time.time()
            token = secrets.token_hex(32)
            deadline = now + spec["timeout_seconds"]
            lease_until = min(deadline, now + spec["lease_seconds"])
            attempt = self.db.execute(
                "INSERT INTO attempts(job_id,generation,number,fingerprint,worker,started) VALUES (?,?,?,?,?,?)",
                (row["id"], row["generation"], row["attempts"] + 1, row["fingerprint"], worker, now),
            ).lastrowid
            self.db.execute(
                "UPDATE jobs SET state='running',attempts=attempts+1,worker=?,token_hash=?,lease_until=?,deadline=?,active_attempt=?,reason=NULL,receipt=NULL,result=NULL WHERE id=?",
                (worker, hashlib.sha256(token.encode()).hexdigest(), lease_until, deadline, attempt, row["id"]),
            )
            self.refreshed = False
            self.event(row["id"], "claimed", {"attempt": row["attempts"] + 1, "worker": worker})
            return {"job": spec, "generation": row["generation"], "attempt": row["attempts"] + 1, "fingerprint": row["fingerprint"], "snapshot": json.loads(row["snapshot"]), "lease_token": token, "lease_until": lease_until, "deadline": deadline}
        return {"job": None, "reason": "no runnable jobs"}

    def leased(self, job_id, token):
        self.refresh()
        label(job_id)
        if not isinstance(token, str) or len(token) != 64:
            raise ValueError("invalid lease token")
        row = self.db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None or row["state"] != "running" or not hmac.compare_digest(row["token_hash"], hashlib.sha256(token.encode()).hexdigest()):
            raise ValueError("stale or invalid lease")
        return row

    def heartbeat(self, job_id, token):
        row = self.leased(job_id, token)
        spec = json.loads(row["definition"])
        lease_until = min(time.time() + spec["lease_seconds"], row["deadline"])
        self.db.execute("UPDATE jobs SET lease_until=? WHERE id=?", (lease_until, job_id))
        return {"job_id": job_id, "lease_until": lease_until, "deadline": row["deadline"]}

    def finish(self, job_id, token, outcome, result, reason):
        row = self.leased(job_id, token)
        spec = json.loads(row["definition"])
        allowed = {"completed", "retry", "rejected", "waiting_evidence", "waiting_ci", "waiting_application"}
        if outcome not in allowed:
            raise ValueError("unsupported outcome")
        reason = reason_text(reason)
        result_hash = self.objects.put_record(result)
        receipt = self.objects.put_record({
            "receipt_version": 1, "job_id": job_id, "generation": row["generation"],
            "attempt": row["attempts"], "execution_id": row["active_attempt"],
            "fingerprint": row["fingerprint"], "snapshot": json.loads(row["snapshot"]),
            "rule_version": spec["rule_version"], "tool_version": spec["tool_version"],
            "worker": row["worker"], "outcome": outcome, "result_sha256": result_hash,
            "reason": reason, "finished_at": time.time(),
        })
        state = outcome
        if outcome == "retry":
            state = "failed" if row["attempts"] >= spec["max_attempts"] else "queued"
        if outcome == "waiting_application":
            for resource in spec["resources"]:
                self.db.execute("UPDATE resources SET available=0 WHERE name=?", (resource,))
                self.event(None, "resource_recovery_required", {"name": resource})
        delay = min(300, spec["retry_base_seconds"] * 2 ** (row["attempts"] - 1)) if outcome == "retry" else 0
        self.db.execute("UPDATE attempts SET ended=?,outcome=?,receipt=? WHERE id=?", (time.time(), outcome, receipt, row["active_attempt"]))
        self.revoke(row, outcome)
        self.db.execute(
            "UPDATE jobs SET state=?,receipt=?,result=?,reason=?,parked=?,next_run=? WHERE id=?",
            (state, receipt, result_hash, reason, int(state.startswith("waiting_") or state == "rejected"), time.time() + delay, job_id),
        )
        self.refreshed = False
        self.event(job_id, "finished", {"outcome": outcome, "state": state, "receipt": receipt})
        self.refresh()
        return self.status(job_id)

    def status(self, job_id=None, after=None):
        if job_id is not None:
            label(job_id)
        if after is not None:
            label(after)
        self.refresh()
        rows = self.db.execute(
            "SELECT id,state,generation,fingerprint,attempts,receipt,result,reason,lease_until,deadline FROM jobs "
            "WHERE (? IS NULL OR id=?) AND (? IS NULL OR id>?) ORDER BY id LIMIT 101",
            (job_id, job_id, after, after),
        ).fetchall()
        return {"jobs": [dict(row) for row in rows[:100]], "next_after": rows[99]["id"] if len(rows) > 100 else None}

    def events(self):
        return {"events": [dict(row) for row in self.db.execute("SELECT * FROM events ORDER BY id DESC LIMIT 100").fetchall()]}
