from functools import partial
from types import SimpleNamespace

from ApplicationProtocol import require, sha256
from Artifacts import Artifacts
from FusionLifecycleRegistration import checked_policy
from FusionOwnerRestart import start_seconds
from FusionQueueReceipt import owned_bytes
from FusionRestartPairs import pair_for, same_values, verify_schema
from ResourceOccupancy import closed_attempt_receipt, stored_record

# automatic archival requires the owner and manual archive to share the reviewed source
ARCHIVE_POLICY = (
    "ApplicationWorkers/ApplicationProtocol.py",
    "ApplicationWorkers/ArchiveFusionProbe.py",
    "ApplicationWorkers/FusionArchivedReplacement.py",
    "ApplicationWorkers/FusionArchiveReplacementRecords.py",
    "ApplicationWorkers/FusionCommissionedExit.py",
    "ApplicationWorkers/FusionExitRecords.py",
    "ApplicationWorkers/FusionOwnerColdStart.py",
    "ApplicationWorkers/FusionOwnerRecovery.py",
    "ApplicationWorkers/FusionRecoveryBasis.py",
    "ApplicationWorkers/FusionReplacementPreflight.py",
    "ApplicationWorkers/FusionReplacementLaunch.py",
    "ApplicationWorkers/FusionProbeArchiveCustody.py",
    "ApplicationWorkers/FusionRequestEvidence.py",
    "ApplicationWorkers/FusionTimeoutAudit.py",
    "ApplicationWorkers/FusionApplicationWorker.py",
    "ApplicationWorkers/FusionStartupEvidence.py",
    "ApplicationWorkers/MacApplicationBundle.py",
    "ApplicationWorkers/MacArchiveLaunchGate.py",
    "ApplicationWorkers/MacBundleLaunch.py",
    "FusionColdStartAdmission.py",
    "LaunchGate.py",
    "Processes.py",
    "ResourceOccupancy.py",
    "Sessions.py",
)


# recheck source and exact registration under the archive locks before releasing the quarantine
def authorize_archive(owner, path, queue, raw, database, config, timeout):
    owner.check_configuration()
    require(
        config == owner.config and owned_bytes(path) == raw,
        "Fusion probe archive differs from the verified installation or queue",
    )
    ledger = SimpleNamespace(db=database)
    verify_schema(ledger)
    pair = pair_for(ledger, queue["jobs"]["a"])
    install = checked_policy(config, queue["resource"], extra=ARCHIVE_POLICY)
    require(
        pair is not None
        and same_values(
            pair,
            {
                "phase_b": queue["jobs"]["b"],
                "resource": queue["resource"],
                "installation": queue["installation"],
                "installation_sha256": install,
                "queue_sha256": sha256(raw),
                "plan_sha256": queue["plan_sha256"],
                "a_receipt": None,
            },
        ),
        "Fusion probe archive requires the exact registered owner pair",
    )
    return partial(
        verify_client_exit, exited_worker(database, owner.store, pair, timeout)
    )


# only the first historical attempt can explain this still parked application disposition
def first_attempt(database, store, pair, timeout):
    first, second = (
        database.execute(
            "SELECT id,definition_hash,generation,fingerprint,attempts,receipt,result FROM jobs WHERE id=?",
            (pair[f"phase_{phase}"],),
        ).fetchone()
        for phase in ("a", "b")
    )
    require(
        first is not None
        and second is not None
        and first["definition_hash"] == pair["a_definition"]
        and second["definition_hash"] == pair["b_definition"]
        and first["attempts"] == 1
        and second["attempts"] == 0
        and first["receipt"] == timeout["receipt_sha256"]
        and first["result"] == timeout["result_sha256"],
        "Fusion probe archive requires the original first attempt",
    )
    attempt = database.execute(
        "SELECT id,job_id,generation,number,fingerprint,started,ended,receipt FROM attempts "
        "WHERE job_id=? AND generation=? AND number=1 AND outcome='waiting_application' "
        "AND receipt=?",
        (first["id"], first["generation"], first["receipt"]),
    ).fetchone()
    require(
        attempt is not None and attempt["fingerprint"] == first["fingerprint"],
        "Fusion probe archive lacks the exact historical controller attempt",
    )
    objects = Artifacts(store, create=False)
    accepted = closed_attempt_receipt(objects, attempt)
    require(
        accepted["outcome"] == "waiting_application"
        and accepted["result_sha256"] == first["result"]
        and accepted["snapshot"]["definition_hash"] == first["definition_hash"],
        "Fusion historical hold differs from the settled job",
    )
    return attempt, accepted


# the archived transport must belong to the supervisor child that was reaped
def exited_worker(database, store, pair, timeout):
    attempt, accepted = first_attempt(database, store, pair, timeout)
    objects = Artifacts(store, create=False)
    worker = stored_record(objects, accepted["result_sha256"])["receipt"]
    require(
        type(worker.get("pid")) is int
        and worker["pid"] > 1
        and isinstance(worker.get("process_start"), str)
        and worker["process_start"].startswith("ps:")
        and type(worker.get("started_at")) in (int, float)
        and type(worker.get("ended_at")) in (int, float)
        and attempt["started"]
        <= worker["started_at"]
        <= worker["ended_at"]
        <= accepted["finished_at"],
        "Fusion probe archive lacks the supervisor worker exit",
    )
    return worker


# the hashed request client must be the settled supervisor worker rather than a native host
def verify_client_exit(worker, client, fenced_at):
    birth = start_seconds(client)
    require(
        worker["pid"] == client["pid"]
        and worker["started_at"] < birth + 1
        and max(birth, worker["started_at"]) <= fenced_at <= worker["ended_at"],
        "Fusion archive request client differs from its settled supervisor worker",
    )
