# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
from graphlib import CycleError, TopologicalSorter

from PriorityBacklog import BACKLOG_TARGET, fill_backlog
from PriorityClaims import enabled
from PriorityPlan import schedule_plan
from Records import canonical, digest


# Queue metadata is independent of job definitions, fingerprints and active leases.
def initialize(ledger):
    if enabled(ledger):
        return
    for statement in (
        "CREATE TABLE a07_priority (job_id TEXT PRIMARY KEY, lane INTEGER NOT NULL, family TEXT NOT NULL, "
        "documents TEXT NOT NULL, evidence TEXT NOT NULL, installation TEXT, definition_hash TEXT NOT NULL)",
        "CREATE INDEX a07_installation ON a07_priority(installation,lane,job_id)",
        "CREATE TABLE a07_turns (pool TEXT NOT NULL, lane INTEGER NOT NULL, family TEXT NOT NULL, "
        "attempt INTEGER NOT NULL REFERENCES attempts(id), PRIMARY KEY(pool,lane,family))",
        "CREATE TABLE a07_grid_inventory (job_id TEXT PRIMARY KEY REFERENCES a07_priority(job_id), "
        "definition TEXT NOT NULL)",
    ):
        ledger.db.execute(statement)
    ledger.db.execute("INSERT INTO settings VALUES ('priority_schedule_version',1)")


# Existing controller jobs may adopt a priority without changing a live definition.
def validate_changes(ledger, jobs, metadata):
    for job_id, spec in jobs.items():
        installation = metadata[job_id][-1]
        if (
            installation is not None
            and not ledger.db.execute(
                "SELECT 1 FROM resources WHERE name=? AND capacity=1", (installation,)
            ).fetchone()
        ):
            raise ValueError("grid installation must be registered with capacity one")
        row = ledger.db.execute(
            "SELECT j.state,j.definition_hash,p.job_id AS scheduled FROM jobs j "
            "LEFT JOIN a07_priority p ON p.job_id=j.id AND p.definition_hash=j.definition_hash WHERE j.id=?",
            (job_id,),
        ).fetchone()
        if (
            row is not None
            and row["definition_hash"] != digest(spec)
            and (row["state"] == "running" or row["scheduled"] is None)
        ):
            raise ValueError(
                f"schedule would replace a running or standalone job: {job_id}"
            )


# Standard jobs required by submitted work cannot stay in the optional backlog.
def needed_specs(ledger, initial):
    specs = {spec["id"]: spec for spec in initial}
    pending = list(initial)
    while pending:
        spec = pending.pop()
        for parent in spec["depends_on"]:
            if parent in specs:
                continue
            row = ledger.db.execute(
                "SELECT definition FROM a07_grid_inventory WHERE job_id=?", (parent,)
            ).fetchone()
            if row is not None:
                needed = json.loads(row["definition"])
                specs[parent] = needed
                pending.append(needed)
    return list(specs.values())


# Standard-grid inventory cannot hide a cycle merely by delaying job admission.
def validate_inventory(ledger):
    inventory = ledger.db.execute(
        "SELECT job_id,definition FROM a07_grid_inventory"
    ).fetchall()
    if not inventory:
        return
    order = TopologicalSorter()
    for row in ledger.db.execute("SELECT job_id,dependency FROM dependencies"):
        order.add(row["job_id"], row["dependency"])
    for row in inventory:
        order.add(row["job_id"], *json.loads(row["definition"])["depends_on"])
    try:
        order.prepare()
    except CycleError as error:
        raise ValueError("dependency cycle through standard grid inventory") from error


# A schedule is admitted under the ledger transaction that guards ordinary submissions.
def schedule(ledger, record):
    jobs, metadata = schedule_plan(record)
    initialize(ledger)
    ledger.refresh()
    validate_changes(ledger, jobs, metadata)
    immediate = []
    for job_id, spec in jobs.items():
        lane, family, documents, evidence, installation = metadata[job_id]
        ledger.db.execute(
            "INSERT INTO a07_priority VALUES (?,?,?,?,?,?,?) ON CONFLICT(job_id) DO UPDATE SET "
            "lane=excluded.lane,family=excluded.family,documents=excluded.documents,"
            "evidence=excluded.evidence,installation=excluded.installation,definition_hash=excluded.definition_hash",
            (
                job_id,
                lane,
                family,
                canonical(documents),
                canonical(evidence),
                installation,
                digest(spec),
            ),
        )
        if (
            lane != 2
            or ledger.db.execute("SELECT 1 FROM jobs WHERE id=?", (job_id,)).fetchone()
        ):
            immediate.append(spec)
        else:
            ledger.db.execute(
                "INSERT INTO a07_grid_inventory VALUES (?,?) ON CONFLICT(job_id) DO UPDATE SET definition=excluded.definition",
                (job_id, canonical(spec)),
            )
    bounds = ledger.db.execute(
        "SELECT (SELECT COUNT(*) FROM a07_priority), "
        "(SELECT COALESCE(SUM(length(CAST(definition AS BLOB))),0) FROM a07_grid_inventory)"
    ).fetchone()
    if bounds[0] > 10_000 or bounds[1] > 16 * 1024 * 1024:
        raise ValueError("priority schedule inventory exceeds its store limit")
    admitted = needed_specs(ledger, immediate)
    if admitted:
        ledger.submit_many(admitted)
        ledger.db.executemany(
            "DELETE FROM a07_grid_inventory WHERE job_id=?",
            [(spec["id"],) for spec in admitted],
        )
    validate_inventory(ledger)
    balances = fill_backlog(ledger)
    deferred = ledger.db.execute("SELECT COUNT(*) FROM a07_grid_inventory").fetchone()[
        0
    ]
    ledger.event(
        None, "priority_schedule", {"planned": len(jobs), "deferred_standard": deferred}
    )
    return {
        "planned": len(jobs),
        "deferred_standard": deferred,
        "backlog_target": BACKLOG_TARGET,
        "queued_by_installation": balances,
    }
