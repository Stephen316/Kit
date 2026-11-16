import json
from types import SimpleNamespace

from ApplicationProtocol import encoded, file_bytes, require, sha256
from FusionCommissionedExit import validate_exit
from FusionExitRecords import read_pinned
from FusionLifecycleRecords import optional
from FusionProbeArchiveCustody import first_attempt
from FusionQueueReceipt import seal
from FusionRequestEvidence import ARCHIVE_RECORD, match_request
from FusionRestartPairs import pair_for
from FusionTimeoutAudit import inspect_archive


# recovery custody requires the archived first claim and the commissioned peer in one generation
def retain_basis(owner, queue, queue_raw, database, config, timeout, archive):
    epoch = owner.exit_watch.epoch
    pair = pair_for(SimpleNamespace(db=database), queue["jobs"]["a"])
    attempt, accepted = first_attempt(database, owner.store, pair, timeout)
    if not exact_epoch(epoch, owner, queue, queue_raw, attempt):
        return {"recovery_basis_status": "commissioned_attempt_mismatch"}
    admission = epoch["admission_sha256"]
    exit_raw = optional(owner.root / f"initial-native-exit-{admission}.json")
    if exit_raw is None:
        return {"recovery_basis_status": "commissioned_exit_missing"}
    try:
        observed = validate_exit(owner.root, epoch, exit_raw)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError):
        return {"recovery_basis_status": "commissioned_exit_unverified"}
    if observed["disposition"] != "outside_owner_scheduled_quit":
        return {"recovery_basis_status": "commissioned_exit_quit_custody"}
    startup = read_pinned(
        owner.root / f"cold-start-admission-{admission}.json", admission
    )
    archive_sha = archive["archive_manifest_sha256"]
    manifest, request = archived_request(owner.root, config, timeout, archive_sha)
    startup_at = startup["startup_receipt"]["observed_at"]
    require(
        startup_at <= attempt["started"], "Fusion startup follows its admitted attempt"
    )
    if not startup_at <= observed["observed_at"] <= request["deadline"]:
        return {"recovery_basis_status": "commissioned_exit_outside_timeout_window"}
    require(
        attempt["started"]
        < request["deadline"]
        <= manifest["fence"]["at"]
        <= accepted["finished_at"],
        "Fusion archive request differs from its historical attempt timing",
    )
    return publish_basis(owner.root, epoch, timeout, archive_sha, exit_raw, attempt)


# a valid observation from another queue or job generation cannot explain this timeout
def exact_epoch(epoch, owner, queue, queue_raw, attempt):
    return (
        epoch["installation_sha256"] == sha256(owner.installation_bytes)
        and epoch["lifecycle_sha256"] == owner.lifecycle_sha
        and epoch["source_revision"] == queue["source_revision"]
        and epoch["queue_receipt_sha256"] == sha256(queue_raw)
        and epoch["job"] == attempt["job_id"]
        and epoch["generation"] == attempt["generation"]
        and epoch["fingerprint"] == attempt["fingerprint"]
        and attempt["number"] == 1
    )


# reread the ordinary archive and its exact request while endpoint and controller custody are held
def archived_request(root, config, timeout, archive_sha):
    observed = inspect_archive(root, config, timeout)
    require(
        observed
        == {
            "status": "archived",
            "archive_manifest_sha256": archive_sha,
            "fence_status": "absent",
        },
        "Fusion recovery requires the exact released hostless archive",
    )
    spool = root / "failed-spools" / timeout["queue_job_id"]
    manifest = read_pinned(spool / ARCHIVE_RECORD, archive_sha)
    request = match_request(file_bytes(spool / "probe.request"), config, timeout, "a")
    return manifest, request


# sealing the joined proof leaves native launch and the second controller attempt ineligible
def publish_basis(root, epoch, timeout, archive_sha, exit_raw, attempt):
    result = {
        "version": 1,
        "scope": "fusion_archived_recovery_basis",
        "epoch": epoch,
        "archive_manifest_sha256": archive_sha,
        "commissioned_exit_sha256": sha256(exit_raw),
        "first_attempt": attempt["number"],
        "first_receipt_sha256": timeout["receipt_sha256"],
        "first_result_sha256": timeout["result_sha256"],
        "request_sha256": timeout["request_sha256"],
        "plan_sha256": timeout["plan_sha256"],
    }
    raw = encoded(result)
    checksum = sha256(raw)
    seal(root / f"archived-recovery-basis-{archive_sha}.json", raw)
    return {
        "recovery_basis_status": "sealed_for_replacement_preflight",
        "recovery_basis_sha256": checksum,
    }
