import json
import os
import shutil
import tempfile
from pathlib import Path

from PriorityBacklog import fill_backlog
from PriorityClaims import runnable_jobs
from Records import StaleLease, bounded, canonical, digest, label, read_record


def read_group(path):
    path = Path(path)
    record = read_record(path / "group.json")
    if set(record) != {"group_claims_version", "members"} or type(record["group_claims_version"]) is not int or record["group_claims_version"] != 1:
        raise ValueError("group claims must use protocol 1")
    names = record["members"]
    if not isinstance(names, list) or not 1 <= len(names) <= 20 or names != [f"{index:02d}.json" for index in range(len(names))]:
        raise ValueError("group members must be 1–20 ordered opaque names")
    return [read_record(path / name) for name in names]


def group_extension(ledger):
    version = ledger.db.execute("SELECT value FROM settings WHERE key=?", ("group_claims_version",)).fetchone()
    if version is not None and version[0] != 1:
        raise ValueError("unsupported optional group claims extension")
    ledger.db.execute("INSERT OR IGNORE INTO settings VALUES (?,?)", ("group_claims_version", 1))
    ledger.db.execute("CREATE TABLE IF NOT EXISTS group_solo (job_id TEXT PRIMARY KEY REFERENCES jobs(id), generation INTEGER NOT NULL, fingerprint TEXT NOT NULL)")


def mark_solo(ledger, claim):
    group_extension(ledger)
    row = ledger.db.execute("SELECT generation,fingerprint FROM jobs WHERE id=?", (claim["job"]["id"],)).fetchone()
    if row is not None and row["generation"] == claim["generation"] and row["fingerprint"] == claim["fingerprint"]:
        ledger.db.execute("INSERT INTO group_solo VALUES (?,?,?) ON CONFLICT(job_id) DO UPDATE SET generation=excluded.generation,fingerprint=excluded.fingerprint", (claim["job"]["id"], claim["generation"], claim["fingerprint"]))


def renew_group(ledger, claims):
    results = []
    for claim in claims:
        try:
            renewed = ledger.heartbeat(claim["job"]["id"], claim["lease_token"])
        except StaleLease:
            results.append({"stale": True})
        else:
            results.append({"stale": False, "lease_until": renewed["lease_until"], "deadline": renewed["deadline"]})
    return {"members": results, "stale": any(item["stale"] for item in results)}


def claim_group(ledger, worker, pool, entries):
    worker, pool = label(worker), label(pool)
    if not isinstance(entries, dict) or not entries or len(entries) > 256:
        raise ValueError("group registry must contain 1–256 kinds")
    limits = {label(kind): bounded(limit, 1, 268435456) for kind, limit in entries.items()}
    if not ledger.db.execute("SELECT 1 FROM pool_kinds WHERE pool=? LIMIT 1", (pool,)).fetchone():
        raise ValueError("pool has no registered job kinds")
    group_extension(ledger)
    ledger.refresh()
    maximum = ledger.db.execute("SELECT value FROM settings WHERE key='max_running'").fetchone()[0]
    running = ledger.db.execute("SELECT COUNT(*) FROM jobs WHERE state='running'").fetchone()[0]
    if maximum - running < 2:
        return []
    fill_backlog(ledger)
    rows = runnable_jobs(ledger, pool, grouped=True).fetchall()
    selected, reserved, identity, total = [], {}, None, 0
    for row in rows:
        spec = json.loads(row["definition"])
        if row["attempts"] >= spec["max_attempts"]:
            continue
        key = (spec["kind"], spec["tool_version"], spec["rule_version"],
               row["schedule_lane"], row["schedule_family"])
        solo = ledger.db.execute("SELECT 1 FROM group_solo WHERE job_id=? AND generation=? AND fingerprint=?", (row["id"], row["generation"], row["fingerprint"])).fetchone()
        if identity is None:
            if spec["kind"] not in limits or solo or not spec["inputs"]:
                return []
            identity = key
        if key != identity or solo or not spec["inputs"]:
            continue
        ledger.verify_job(row)
        snapshot = json.loads(row["snapshot"])
        objects = {digest(spec), *(item["sha256"] for item in snapshot["inputs"].values())}
        for dependency in snapshot["dependencies"].values():
            objects.update(dependency.values())
            result = read_record(ledger.objects.path(dependency["result"]))
            objects.update(item["sha256"] for item in result.get("output_artifacts", {}).values())
        footprint = sum(ledger.verify_object(value) for value in objects)
        if footprint >= limits[spec["kind"]]:
            if not selected:
                return []
            continue
        if total + footprint >= limits[spec["kind"]]:
            continue
        resources = ledger.db.execute(
            "SELECT r.resource,a.capacity,(SELECT COUNT(*) FROM job_resources held JOIN jobs owner ON owner.id=held.job_id WHERE held.resource=r.resource AND owner.state='running') AS held "
            "FROM job_resources r JOIN resources a ON a.name=r.resource WHERE r.job_id=?", (row["id"],)
        ).fetchall()
        if any(item["held"] + reserved.get(item["resource"], 0) >= item["capacity"] for item in resources):
            continue
        for item in resources:
            reserved[item["resource"]] = reserved.get(item["resource"], 0) + 1
        selected.append((row, spec))
        total += footprint
        if len(selected) >= min(20, maximum - running):
            break
    if len(selected) < 2:
        return []
    installations = [row["schedule_installation"] for row, spec in selected if row["schedule_installation"] is not None]
    if installations:
        fill_backlog(ledger, installations)
    claims = [ledger.issue_claim(row, spec, worker, pool) for row, spec in selected]
    ledger.event(None, "group_claimed", {"jobs": [claim["job"]["id"] for claim in claims], "input_bytes": total, "group_protocol": 1})
    return claims


def write_group(path, claims):
    path = Path(path)
    staged = Path(tempfile.mkdtemp(prefix=".group-stage-", dir=path.parent))
    try:
        names = [f"{index:02d}.json" for index in range(len(claims))]
        for name, claim in [("group.json", {"group_claims_version": 1, "members": names}), *zip(names, claims)]:
            descriptor = os.open(staged / name, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                output.write(canonical(claim) + "\n")
                output.flush()
                os.fsync(output.fileno())
        os.rename(staged, path)
    finally:
        shutil.rmtree(staged, ignore_errors=True)
