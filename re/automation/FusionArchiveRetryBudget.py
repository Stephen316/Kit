ADMITTED = "fusion_archived_retry_admitted"
RETRY_ATTEMPT = 2


# opted-in recovery lowers the cap only for the exact admitted job snapshot
def attempts_exhausted(ledger, row, spec):
    attempts = row["attempts"]
    if attempts >= spec["max_attempts"]:
        return True
    if attempts < RETRY_ATTEMPT or not row["id"].startswith("fusion-phase:"):
        return False
    return (
        ledger.db.execute(
            "SELECT 1 FROM events WHERE job_id=? AND action=? "
            "AND json_extract(detail,'$.generation')=? "
            "AND json_extract(detail,'$.fingerprint')=? "
            "AND json_extract(detail,'$.definition_sha256')=? LIMIT 1",
            (
                row["id"],
                ADMITTED,
                row["generation"],
                row["fingerprint"],
                row["definition_hash"],
            ),
        ).fetchone()
        is not None
    )
