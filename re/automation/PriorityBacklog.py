# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json

from PriorityClaims import enabled

# A finite standard-grid inventory supplies this many queued jobs when evidence is ready.
BACKLOG_TARGET = 10


# Pool and admission checks retain the ordinary controller's installation and evidence rules.
def fill_backlog(ledger, selected_installations=()):
    if not enabled(ledger):
        return {}
    inventory = ledger.db.execute("""
        SELECT p.job_id,p.installation,i.definition
        FROM a07_grid_inventory i
        JOIN a07_priority p ON p.job_id=i.job_id
        JOIN resources r ON r.name=p.installation AND r.available=1 AND r.capacity=1
        WHERE NOT EXISTS (SELECT 1 FROM jobs j WHERE j.id=i.job_id)
        ORDER BY p.installation, (
            SELECT COUNT(*) FROM dependencies d JOIN jobs child ON child.id=d.job_id
            WHERE d.dependency=p.job_id AND child.state IN (
                'queued','waiting_evidence','waiting_ci','waiting_application'
            )
        ) DESC, json_array_length(p.documents) DESC, json_array_length(p.evidence) DESC,
        p.family,p.job_id
        """)
    balances = {
        row["installation"]: row["pending"]
        for row in ledger.db.execute(
            "SELECT p.installation,SUM(CASE WHEN j.state='queued' THEN 1 ELSE 0 END) AS pending "
            "FROM a07_priority p LEFT JOIN jobs j ON j.id=p.job_id AND j.definition_hash=p.definition_hash "
            "WHERE p.installation IS NOT NULL GROUP BY p.installation"
        )
    }
    for installation in selected_installations:
        if installation is not None:
            balances[installation] -= 1
    quotas = dict(
        ledger.db.execute(
            "SELECT key,value FROM settings WHERE key IN ('job_count','definition_bytes')"
        )
    )
    remaining_jobs = 10_000 - quotas["job_count"]
    remaining_bytes = 16 * 1024 * 1024 - quotas["definition_bytes"]
    selected = []
    for item in inventory:
        if remaining_jobs == 0:
            break
        installation = item["installation"]
        size = len(item["definition"].encode("utf-8"))
        if balances.get(installation, 0) >= BACKLOG_TARGET or size > remaining_bytes:
            continue
        spec = json.loads(item["definition"])
        if (
            any(
                not ledger.db.execute(
                    "SELECT 1 FROM resources WHERE name=? AND available=1", (resource,)
                ).fetchone()
                for resource in spec["resources"]
            )
            or ledger.snapshot(spec, verify_artifacts=False) is None
        ):
            continue
        selected.append(spec)
        remaining_jobs -= 1
        remaining_bytes -= size
        balances[installation] = balances.get(installation, 0) + 1
    if selected:
        ledger.submit_many(selected)
        ledger.db.executemany(
            "DELETE FROM a07_grid_inventory WHERE job_id=?",
            [(spec["id"],) for spec in selected],
        )
    return balances
