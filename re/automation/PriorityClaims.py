# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import time


# Version checks keep old controller stores on their original claim path.
def enabled(ledger):
    row = ledger.db.execute(
        "SELECT value FROM settings WHERE key='priority_schedule_version'"
    ).fetchone()
    if row is None:
        return False
    if row[0] != 1:
        raise ValueError("unsupported priority schedule extension")
    return True


# Both claim paths must use the same job ranking and resource admission.
def runnable_jobs(ledger, pool, *, grouped=False):
    where = """
        WHERE j.state='queued' AND j.next_run<=:now
        AND (:pool IS NULL OR j.kind IN (SELECT kind FROM pool_kinds WHERE pool=:pool))
        AND NOT EXISTS (
            SELECT 1 FROM job_resources r LEFT JOIN resources a ON a.name=r.resource
            WHERE r.job_id=j.id AND (COALESCE(a.available,0)=0 OR (
                SELECT COUNT(*) FROM job_resources held JOIN jobs owner ON owner.id=held.job_id
                WHERE held.resource=r.resource AND owner.state='running'
            )>=a.capacity)
        )
    """
    params = {"now": time.time(), "pool": pool, "scope": pool or ""}
    limit = "" if grouped else " LIMIT 1"
    if not enabled(ledger):
        return ledger.db.execute(
            "SELECT j.*, NULL AS schedule_lane, NULL AS schedule_family, NULL AS schedule_installation FROM jobs j "
            + where
            + "ORDER BY j.created,j.id"
            + limit,
            params,
        )
    return ledger.db.execute(
        """
        SELECT j.*, COALESCE(p.lane,1) AS schedule_lane,
               COALESCE(p.family,'') AS schedule_family, p.installation AS schedule_installation
        FROM jobs j
        LEFT JOIN a07_priority p ON p.job_id=j.id AND p.definition_hash=j.definition_hash
        LEFT JOIN a07_turns turn ON turn.pool=:scope
            AND turn.lane=COALESCE(p.lane,1) AND turn.family=COALESCE(p.family,'')
        """
        + where
        + """
        AND (p.installation IS NULL OR EXISTS (
            SELECT 1 FROM resources i WHERE i.name=p.installation AND i.capacity=1
        ))
        AND (p.lane IS NULL OR p.lane<>2 OR NOT EXISTS (
            SELECT 1 FROM a07_priority request JOIN jobs grid ON grid.id=request.job_id
            WHERE request.installation=p.installation AND request.lane=0
              AND request.definition_hash=grid.definition_hash
              AND grid.state='queued'
              AND grid.next_run<=:now
              AND NOT EXISTS (
                  SELECT 1 FROM job_resources required
                  LEFT JOIN resources available ON available.name=required.resource
                  WHERE required.job_id=grid.id AND (COALESCE(available.available,0)=0 OR (
                      SELECT COUNT(*) FROM job_resources held
                      JOIN jobs owner ON owner.id=held.job_id
                      WHERE held.resource=required.resource AND owner.state='running'
                  )>=available.capacity)
              )
        ))
        ORDER BY schedule_lane,COALESCE(turn.attempt,0),
            CASE WHEN p.job_id IS NOT NULL THEN (
                SELECT COUNT(*) FROM dependencies d JOIN jobs child ON child.id=d.job_id
                WHERE d.dependency=j.id AND child.state IN ('queued','waiting_evidence','waiting_ci','waiting_application')
            ) ELSE 0 END DESC,
            COALESCE(json_array_length(p.documents),0) DESC,
            COALESCE(json_array_length(p.evidence),0) DESC,
            j.created,j.id
        """
        + limit,
        params,
    )


# Advancing a family only on committed claims keeps rolls and restarts deterministic.
def record_turn(ledger, row, pool, attempt):
    if row["schedule_lane"] is None:
        return
    ledger.db.execute(
        "INSERT INTO a07_turns(pool,lane,family,attempt) VALUES (?,?,?,?) "
        "ON CONFLICT(pool,lane,family) DO UPDATE SET attempt=excluded.attempt",
        (pool or "", row["schedule_lane"], row["schedule_family"], attempt),
    )
