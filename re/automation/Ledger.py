import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from pathlib import Path

from ApplicationHolds import invalidate_application_hold, retry_delay, save_application_hold
from Artifacts import Artifacts
from OutputIntake import OutputIntake
from OutputManifest import InvalidOutput, output_manifest
from PriorityBacklog import fill_backlog
from PriorityClaims import record_turn, runnable_jobs
from Records import StaleLease, bounded, canonical, digest, label, read_record, reason_text, specification


def named_inputs(spec):
    return {binding for binding in spec["inputs"].values() if isinstance(binding, str)}


def pending_ci_inputs(snapshot):
    return {
        name: item["pending_ci_fingerprint"]
        for name, item in snapshot["dependencies"].items()
        if "pending_ci_fingerprint" in item
    }


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
            if version not in (0, 1, 2, 3, 4):
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
            if version in (0, 1):
                for statement in Path(__file__).with_name("QueueSchema.sql").read_text().split(";"):
                    if statement.strip():
                        self.db.execute(statement)
                for row in self.db.execute("SELECT id,definition FROM jobs").fetchall():
                    spec = specification(json.loads(row["definition"]))
                    self.db.executemany("INSERT INTO job_inputs VALUES (?,?)", [(row["id"], name) for name in named_inputs(spec)])
                    self.db.executemany("INSERT INTO job_resources VALUES (?,?)", [(row["id"], name) for name in spec["resources"]])
                self.db.execute("INSERT INTO dirty SELECT id FROM jobs")
            if version in (0, 1, 2):
                count, size = self.db.execute("SELECT COUNT(*),COALESCE(SUM(length(CAST(definition AS BLOB))),0) FROM jobs").fetchone()
                self.db.executemany("INSERT INTO settings VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", [("job_count", count), ("definition_bytes", size)])
                self.db.execute("PRAGMA user_version=3")
            if version in (0, 1, 2, 3):
                self.upgrade_pools()
            self.db.execute("COMMIT")
            os.chmod(database, 0o600)
        except BaseException:
            self.db.close()
            raise

    def upgrade_pools(self):
        if "capacity" not in {row["name"] for row in self.db.execute("PRAGMA table_info(resources)")}:
            self.db.execute("ALTER TABLE resources ADD COLUMN capacity INTEGER NOT NULL DEFAULT 1 CHECK (capacity BETWEEN 1 AND 64)")
        if "kind" not in {row["name"] for row in self.db.execute("PRAGMA table_info(jobs)")}:
            self.db.execute("ALTER TABLE jobs ADD COLUMN kind TEXT")
        self.db.executemany("UPDATE jobs SET kind=? WHERE id=?", [(json.loads(row["definition"])["kind"], row["id"]) for row in self.db.execute("SELECT id,definition FROM jobs").fetchall()])
        self.db.execute("CREATE TABLE IF NOT EXISTS pool_kinds (kind TEXT PRIMARY KEY, pool TEXT NOT NULL)")
        self.db.execute("CREATE INDEX IF NOT EXISTS pool_members ON pool_kinds(pool,kind)")
        self.db.execute("CREATE INDEX IF NOT EXISTS jobs_pool_claim ON jobs(state,kind,created,id)")
        self.db.execute("PRAGMA user_version=4")

    def __enter__(self):
        self.db.execute("BEGIN IMMEDIATE")
        self.checked = {}
        self.checked_results = set()
        self.bytes_hashed = 0
        self.reconciled = 0
        self.cycle_searches = 0
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
            self.checked[sha256] = self.objects.verify(sha256)
            self.bytes_hashed += self.checked[sha256]
        return self.checked[sha256]

    def verify_result(self, sha256):
        self.verify_object(sha256)
        if sha256 in self.checked_results:
            return
        result = read_record(self.objects.path(sha256))
        if "output_artifacts_version" in result:
            if result["output_artifacts_version"] != 1:
                raise ValueError("unsupported accepted output artifact version")
            for item in output_manifest(result.get("output_artifacts"), paths=False).values():
                if self.verify_object(item["sha256"]) != item["size_bytes"]:
                    raise ValueError("accepted output size mismatch")
        self.checked_results.add(sha256)

    def enqueue_children(self, job_id):
        self.db.execute("INSERT OR IGNORE INTO dirty SELECT job_id FROM dependencies WHERE dependency=?", (job_id,))

    def change_resource(self, name, available, unpark_waiters=True):
        invalidate_application_hold(self, name)
        previous = self.db.execute("SELECT available FROM resources WHERE name=?", (name,)).fetchone()
        if previous is not None and previous[0] == int(available):
            return
        self.db.execute("INSERT INTO resources(name,available) VALUES (?,?) ON CONFLICT(name) DO UPDATE SET available=excluded.available", (name, int(available)))
        if available and unpark_waiters:
            self.db.execute("UPDATE jobs SET parked=0 WHERE state='waiting_application' AND parked=1 AND id IN (SELECT job_id FROM job_resources WHERE resource=?)", (name,))
        self.db.execute("INSERT OR IGNORE INTO dirty SELECT job_id FROM job_resources WHERE resource=?", (name,))
        self.event(None, "resource", {"name": name, "available": bool(available)})

    def bind(self, name, path):
        name = label(name)
        sha256 = self.objects.put_file(path)
        self.set_binding(name, sha256)
        self.refresh()
        return {"name": name, "sha256": sha256}

    def set_binding(self, name, sha256):
        name = label(name)
        previous = self.db.execute("SELECT sha256 FROM bindings WHERE name=?", (name,)).fetchone()
        self.db.execute("INSERT INTO bindings VALUES (?,?) ON CONFLICT(name) DO UPDATE SET sha256=excluded.sha256", (name, sha256))
        if previous is None or previous[0] != sha256:
            self.db.execute("INSERT OR IGNORE INTO dirty SELECT job_id FROM job_inputs WHERE binding=?", (name,))
        self.event(None, "binding", {"name": name, "sha256": sha256})

    def resource(self, name, available=None, capacity=None):
        name = label(name)
        if available is None and capacity is None:
            raise ValueError("resource change needs availability or capacity")
        if capacity is not None:
            capacity = bounded(capacity, 1, 64)
            previous = self.db.execute("SELECT capacity FROM resources WHERE name=?", (name,)).fetchone()
            if previous is None:
                self.db.execute("INSERT INTO resources(name,available,capacity) VALUES (?,0,?)", (name, capacity))
            elif previous[0] != capacity:
                self.db.execute("UPDATE resources SET capacity=? WHERE name=?", (capacity, name))
            if previous is None or previous[0] != capacity:
                invalidate_application_hold(self, name)
                self.event(None, "resource_capacity", {"name": name, "capacity": capacity})
        if available is not None:
            self.change_resource(name, available)
        self.refresh()
        row = self.db.execute("SELECT available,capacity FROM resources WHERE name=?", (name,)).fetchone()
        return {"name": name, "available": bool(row["available"]), "capacity": row["capacity"]}

    def pool(self, name, kinds):
        name = label(name)
        if not isinstance(kinds, list) or not 1 <= len(kinds) <= 64:
            raise ValueError("a pool needs 1–64 job kinds")
        kinds = sorted({label(kind) for kind in kinds})
        for kind in kinds:
            owner = self.db.execute("SELECT pool FROM pool_kinds WHERE kind=?", (kind,)).fetchone()
            if owner is not None and owner[0] != name:
                raise ValueError("job kind already belongs to another pool")
        self.db.execute("DELETE FROM pool_kinds WHERE pool=?", (name,))
        self.db.executemany("INSERT INTO pool_kinds VALUES (?,?)", [(kind, name) for kind in kinds])
        if self.db.execute("SELECT COUNT(*) FROM pool_kinds").fetchone()[0] > 1024:
            raise ValueError("store pool metadata limit exceeded")
        self.event(None, "pool", {"name": name, "kinds": kinds})
        return {"pool": name, "kinds": kinds}

    def store_spec(self, spec):
        encoded = canonical(spec)
        previous = self.db.execute("SELECT definition_hash,length(CAST(definition AS BLOB)) AS size FROM jobs WHERE id=?", (spec["id"],)).fetchone()
        if previous is not None and previous[0] == digest(spec):
            return
        self.objects.put_record(spec)
        self.db.execute(
            "INSERT INTO jobs(id,kind,definition,definition_hash,state,fingerprint,created) VALUES (?,?,?,?,'queued','',?) "
            "ON CONFLICT(id) DO UPDATE SET kind=excluded.kind,definition=excluded.definition,definition_hash=excluded.definition_hash",
            (spec["id"], spec["kind"], encoded, digest(spec), time.time()),
        )
        old_parents = {row[0] for row in self.db.execute("SELECT dependency FROM dependencies WHERE job_id=?", (spec["id"],))}
        self.db.execute("DELETE FROM dependencies WHERE job_id=?", (spec["id"],))
        self.db.executemany("INSERT INTO dependencies VALUES (?,?)", [(spec["id"], item) for item in spec["depends_on"]])
        self.event(spec["id"], "submitted", {"definition_hash": digest(spec)})
        self.db.execute("DELETE FROM job_inputs WHERE job_id=?", (spec["id"],))
        self.db.executemany("INSERT INTO job_inputs VALUES (?,?)", [(spec["id"], name) for name in named_inputs(spec)])
        self.db.execute("DELETE FROM job_resources WHERE job_id=?", (spec["id"],))
        self.db.executemany("INSERT INTO job_resources VALUES (?,?)", [(spec["id"], name) for name in spec["resources"]])
        self.db.execute("INSERT OR IGNORE INTO dirty VALUES (?)", (spec["id"],))
        self.db.executemany("UPDATE settings SET value=value+? WHERE key=?", [(int(previous is None), "job_count"), (len(encoded.encode("utf-8")) - (previous["size"] if previous is not None else 0), "definition_bytes")])
        added = set(spec["depends_on"]) - old_parents
        if added and self.db.execute("SELECT 1 FROM dependencies WHERE dependency=? LIMIT 1", (spec["id"],)).fetchone():
            return spec["id"], added
        return None

    def submit_many(self, values):
        if not isinstance(values, list) or not 1 <= len(values) <= 10000:
            raise ValueError("batch must contain 1–10000 job records")
        specs = [specification(value) for value in values]
        if len({spec["id"] for spec in specs}) != len(specs):
            raise ValueError("batch contains duplicate job identifiers")
        checks = [check for spec in specs if (check := self.store_spec(spec)) is not None]
        count = self.db.execute("SELECT value FROM settings WHERE key='job_count'").fetchone()[0]
        size = self.db.execute("SELECT value FROM settings WHERE key='definition_bytes'").fetchone()[0]
        if count > 10000 or size > 16 * 1024 * 1024:
            raise ValueError("store job metadata limit exceeded")
        for job_id, parents in checks:
            self.check_edges(job_id, parents)
        self.refresh()
        return {"submitted": len(specs)}

    def submit(self, value):
        self.submit_many([value])
        return self.status(value["id"])

    def snapshot(self, spec, verify_artifacts=True):
        if verify_artifacts:
            self.verify_object(digest(spec))
        inputs = {}
        for role, name in spec["inputs"].items():
            if not isinstance(name, str):
                continue
            row = self.db.execute("SELECT sha256 FROM bindings WHERE name=?", (name,)).fetchone()
            if row is None:
                return None
            if verify_artifacts:
                self.verify_object(row[0])
            inputs[role] = {"binding": name, "sha256": row[0]}
        selectors = [value for value in spec["inputs"].values() if isinstance(value, dict)]
        candidate_inputs = {value["dependency"] for value in selectors if value.get("candidate_fingerprint")}
        ordinary_inputs = {value["dependency"] for value in selectors if not value.get("candidate_fingerprint")}
        candidate_fingerprints, dependencies = {}, {}
        for name in spec["depends_on"]:
            row = self.db.execute(
                "SELECT state,receipt,result,parked,fingerprint,snapshot FROM jobs WHERE id=?", (name,)
            ).fetchone()
            if row is None:
                return None
            pending = (
                row["state"] == "waiting_ci"
                and row["parked"] == 1
                and name in candidate_inputs
                and name not in ordinary_inputs
            )
            if not pending and row["state"] != "completed":
                return None
            if pending_ci_inputs(json.loads(row["snapshot"])):
                return None
            if verify_artifacts:
                self.verify_object(row["receipt"])
                self.verify_result(row["result"])
            dependencies[name] = {"receipt": row["receipt"], "result": row["result"]}
            if name in candidate_inputs:
                if verify_artifacts:
                    self.verify_object(row["fingerprint"])
                candidate_fingerprints[name] = row["fingerprint"]
            if pending:
                dependencies[name]["pending_ci_fingerprint"] = row["fingerprint"]
        manifests = {}
        for role, selector in spec["inputs"].items():
            if isinstance(selector, str):
                continue
            if selector.get("candidate_fingerprint"):
                sha256 = candidate_fingerprints[selector["dependency"]]
            else:
                sha256 = self.dependency_input(selector, dependencies, manifests)
            if sha256 is None:
                return None
            inputs[role] = {"binding": selector, "sha256": sha256}
        return {"definition_hash": digest(spec), "inputs": inputs, "dependencies": dependencies}

    def dependency_input(self, selector, dependencies, manifests):
        result_hash = dependencies[selector["dependency"]]["result"]
        if "artifact" not in selector:
            return result_hash
        if result_hash not in manifests:
            result = read_record(self.objects.path(result_hash))
            if digest(result) != result_hash:
                raise ValueError("dependency result integrity mismatch")
            manifests[result_hash] = (
                output_manifest(result["output_artifacts"], paths=False) if result.get("output_artifacts_version") == 1 else {}
            )
        artifact = manifests[result_hash].get(selector["artifact"])
        return artifact["sha256"] if artifact is not None else None

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
                        self.change_resource(resource, False)
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

    def check_edges(self, job_id, parents):
        for parent in parents:
            if self.db.execute("SELECT 1 FROM jobs WHERE id=?", (parent,)).fetchone() is None:
                continue
            self.cycle_searches += 1
            if self.db.execute(
                "WITH RECURSIVE ancestors(id) AS (SELECT ? UNION SELECT d.dependency FROM dependencies d JOIN ancestors a ON d.job_id=a.id) "
                "SELECT 1 FROM ancestors WHERE id=? LIMIT 1", (parent, job_id)
            ).fetchone():
                raise ValueError("job dependency cycle")

    def reconcile_job(self, row):
        self.reconciled += 1
        name = row["id"]
        spec = json.loads(row["definition"])
        before = (row["receipt"], row["result"]) if row["state"] in {"completed", "waiting_ci"} else None
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
            self.verify_result(row["result"])
        elif row["state"] != "running" and not row["parked"] and row["state"] not in ("failed", "rejected"):
            state = "waiting_evidence" if snapshot is None else "waiting_application" if unavailable else "queued"
            self.db.execute("UPDATE jobs SET state=? WHERE id=?", (state, name))
        after = self.db.execute("SELECT state,receipt,result FROM jobs WHERE id=?", (name,)).fetchone()
        after = (after["receipt"], after["result"]) if after["state"] in {"completed", "waiting_ci"} else None
        if before != after:
            self.enqueue_children(name)

    def refresh(self):
        self.db.execute("INSERT OR IGNORE INTO dirty SELECT id FROM jobs WHERE state='running' AND (lease_until<=? OR deadline<=?)", (time.time(), time.time()))
        while True:
            dirty = self.db.execute("SELECT job_id FROM dirty ORDER BY job_id LIMIT 1").fetchone()
            if dirty is None:
                return
            self.db.execute("DELETE FROM dirty WHERE job_id=?", (dirty[0],))
            self.reconcile_job(self.db.execute("SELECT * FROM jobs WHERE id=?", (dirty[0],)).fetchone())

    def verify_job(self, row, verify_artifacts=True):
        snapshot = self.snapshot(json.loads(row["definition"]), verify_artifacts)
        if (digest(snapshot) if snapshot is not None else None) != row["fingerprint"]:
            raise ValueError("job prerequisites require reconciliation")
        if verify_artifacts and row["fingerprint"] is not None:
            self.verify_object(row["fingerprint"])
        if verify_artifacts and row["state"] == "completed":
            self.verify_object(row["receipt"])
            self.verify_result(row["result"])

    def expire(self, row, spec):
        receipt = self.revoke(row, "expired")
        for resource in spec["resources"]:
            self.change_resource(resource, False)
            self.event(None, "resource_recovery_required", {"name": resource})
        state = "failed" if row["attempts"] >= spec["max_attempts"] else "queued"
        delay = retry_delay(spec, row["attempts"])
        self.db.execute("UPDATE jobs SET state=?,next_run=?,receipt=?,result=NULL,reason=? WHERE id=?", (state, time.time() + delay, receipt, "lease or execution timeout expired", row["id"]))
        self.event(row["id"], "expired", {"attempt": row["attempts"], "state": state})

    def claim(self, worker, pool=None):
        worker = label(worker)
        if pool is not None and not self.db.execute("SELECT 1 FROM pool_kinds WHERE pool=? LIMIT 1", (label(pool),)).fetchone():
            raise ValueError("pool has no registered job kinds")
        self.refresh()
        maximum = self.db.execute("SELECT value FROM settings WHERE key='max_running'").fetchone()[0]
        running = self.db.execute("SELECT COUNT(*) FROM jobs WHERE state='running'").fetchone()[0]
        if running >= maximum:
            return {"job": None, "reason": "concurrency limit"}
        fill_backlog(self)
        while True:
            row = runnable_jobs(self, pool).fetchone()
            if row is None:
                return {"job": None, "reason": "no runnable jobs"}
            self.verify_job(row)
            spec = json.loads(row["definition"])
            if row["attempts"] >= spec["max_attempts"]:
                self.db.execute("UPDATE jobs SET state='failed',reason=? WHERE id=?", ("attempt budget exhausted", row["id"]))
                continue
            if row["schedule_installation"] is not None:
                fill_backlog(self, (row["schedule_installation"],))
            return self.issue_claim(row, spec, worker, pool)

    def issue_claim(self, row, spec, worker, pool):
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
        record_turn(self, row, pool, attempt)
        self.event(row["id"], "claimed", {"attempt": row["attempts"] + 1, "worker": worker})
        return {"job": spec, "generation": row["generation"], "attempt": row["attempts"] + 1, "fingerprint": row["fingerprint"], "snapshot": json.loads(row["snapshot"]), "lease_token": token, "lease_until": lease_until, "deadline": deadline}

    def leased(self, job_id, token, verify_artifacts=True):
        if verify_artifacts:
            self.refresh()
        label(job_id)
        if not isinstance(token, str) or len(token) != 64:
            raise ValueError("invalid lease token")
        row = self.db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None or row["state"] != "running" or row["token_hash"] is None or not hmac.compare_digest(row["token_hash"], hashlib.sha256(token.encode()).hexdigest()):
            raise StaleLease("lease was replaced, revoked or finished")
        if min(row["lease_until"], row["deadline"]) <= time.time():
            raise StaleLease("lease or execution deadline expired")
        snapshot = self.snapshot(json.loads(row["definition"]), False)
        if (digest(snapshot) if snapshot is not None else None) != row["fingerprint"]:
            raise StaleLease("inputs changed during the attempt")
        self.verify_job(row, verify_artifacts)
        if min(row["lease_until"], row["deadline"]) <= time.time():
            raise StaleLease("lease or execution deadline expired")
        return row

    def heartbeat(self, job_id, token):
        row = self.leased(job_id, token, verify_artifacts=False)
        spec = json.loads(row["definition"])
        lease_until = min(time.time() + spec["lease_seconds"], row["deadline"])
        self.db.execute("UPDATE jobs SET lease_until=? WHERE id=?", (lease_until, job_id))
        return {"job_id": job_id, "lease_until": lease_until, "deadline": row["deadline"], "reconciled_jobs": self.reconciled, "cycle_searches": self.cycle_searches, "artifact_bytes_hashed": self.bytes_hashed}

    def finish(self, job_id, token, outcome, result_path, reason, output_root=None, result_record=None, owner_pin=None):
        row = self.leased(job_id, token)
        spec = json.loads(row["definition"])
        allowed = {"completed", "retry", "rejected", "waiting_evidence", "waiting_ci", "waiting_application"}
        if outcome not in allowed:
            raise ValueError("unsupported outcome")
        reason = reason_text(reason)
        result = read_record(result_path) if result_record is None else result_record
        if output_root is None and ("output_artifacts_version" in result or "output_artifacts" in result or isinstance(result.get("result"), dict) and "artifacts" in result["result"]):
            raise InvalidOutput("declared or accepted output metadata requires explicit output intake")
        if output_root is not None:
            output_root = Path(os.path.abspath(output_root))
            if output_root != Path(os.path.abspath(result_path)).parent / "work":
                raise InvalidOutput("output root must be the finish record's private work directory")
            declared = result.get("result")
            if outcome != "completed" or not isinstance(declared, dict) or declared.get("outcome") != "completed" or "artifacts" not in declared:
                raise InvalidOutput("output intake requires a completed runner result with artifacts")
            if "output_artifacts_version" in result or "output_artifacts" in result:
                raise InvalidOutput("runner cannot supply accepted output metadata")
            try:
                output_manifest(declared["artifacts"])
            except ValueError as error:
                raise InvalidOutput(str(error)) from error
            with OutputIntake(self.objects, output_root, declared["artifacts"]) as intake:
                self.leased(job_id, token, verify_artifacts=False)
                manifest = intake.publish()
            declared["artifacts"] = manifest
            result["output_artifacts_version"] = 1
            result["output_artifacts"] = manifest
        if min(row["lease_until"], row["deadline"]) <= time.time():
            raise StaleLease("lease or execution deadline expired")
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
                self.change_resource(resource, False)
                self.event(None, "resource_recovery_required", {"name": resource})
        delay = retry_delay(spec, row["attempts"]) if outcome == "retry" else 0
        self.leased(job_id, token, verify_artifacts=False)
        self.db.execute("UPDATE attempts SET ended=?,outcome=?,receipt=? WHERE id=?", (time.time(), outcome, receipt, row["active_attempt"]))
        self.revoke(row, outcome)
        self.db.execute(
            "UPDATE jobs SET state=?,receipt=?,result=?,reason=?,parked=?,next_run=? WHERE id=?",
            (state, receipt, result_hash, reason, int(state.startswith("waiting_") or state == "rejected"), time.time() + delay, job_id),
        )
        self.enqueue_children(job_id)
        detail = {"outcome": outcome, "state": state, "receipt": receipt}
        pending = pending_ci_inputs(json.loads(row["snapshot"]))
        if pending:
            detail["waiting_ci_inputs"] = pending
        self.event(job_id, "finished", detail)
        if outcome == "waiting_application":
            save_application_hold(self, row, spec, result, owner_pin, receipt, result_hash)
        self.refresh()
        return self.status(job_id)

    def status(self, job_id=None, after=None):
        if job_id is not None:
            label(job_id)
        if after is not None:
            label(after)
        self.refresh()
        if job_id is not None:
            rows = self.db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchall()
        else:
            rows = self.db.execute("SELECT * FROM jobs WHERE id>? ORDER BY id LIMIT 101", (after or "",)).fetchall()
        for row in rows[:100]:
            self.verify_job(row)
        fields = ("id", "kind", "state", "generation", "fingerprint", "attempts", "receipt", "result", "reason", "lease_until", "deadline")
        jobs = []
        for row in rows[:100]:
            job = {key: row[key] for key in fields}
            pending = pending_ci_inputs(json.loads(row["snapshot"])) if row["snapshot"] else {}
            if pending:
                job["waiting_ci_inputs"] = pending
            jobs.append(job)
        return {"jobs": jobs, "next_after": rows[99]["id"] if len(rows) > 100 else None, "reconciled_jobs": self.reconciled, "cycle_searches": self.cycle_searches}

    def events(self):
        return {"events": [dict(row) for row in self.db.execute("SELECT * FROM events ORDER BY id DESC LIMIT 100").fetchall()]}
