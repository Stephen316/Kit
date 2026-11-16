import sys
from types import SimpleNamespace

from ApplicationAckIntent import installation_sha256
from Artifacts import Artifacts
from FusionRestartPairs import exact_first, installed
from Records import digest, read_record
from StoreRead import read_store

BACKOFF_SECONDS = (1, 3)


def can_retry(store, owner, installation, intent):
    if sys.platform != "darwin" or owner is None:
        return False
    config = read_record(installation)
    if (
        config["application"] != "fusion"
        or config.get("macos_automatic_quit") is not True
        or installation_sha256(installation) != intent["installation_sha256"]
    ):
        return False
    with read_store(store / "ledger.sqlite3", owner, (4,), timeout=2) as database:
        if not installed(SimpleNamespace(db=database)):
            return False
        row = database.execute(
            f"""
            SELECT b.result FROM fusion_restart_pairs pair JOIN jobs b ON b.id=pair.phase_b
            JOIN jobs a ON {exact_first('a', 'pair')}
            WHERE pair.phase_b=? AND pair.installation=? AND pair.a_receipt IS NOT NULL
              AND pair.restart_intent IS NOT NULL AND pair.final_evidence IS NULL
              AND b.state='completed' AND b.definition_hash=pair.b_definition
              AND b.generation=? AND b.fingerprint=? AND b.attempts=? AND b.kind=?
            """,
            (
                intent["job"],
                config["installation"],
                intent["generation"],
                intent["fingerprint"],
                intent["attempts"],
                intent["kind"],
            ),
        ).fetchone()
        if row is None:
            return False
        artifacts = Artifacts(store, create=False)
        artifacts.verify(row["result"])
        result = read_record(artifacts.path(row["result"]))
        return (
            result.get("application_acknowledgement_sha256") == digest(intent)
            and result["receipt"]["session"] == intent["session"]
        )
