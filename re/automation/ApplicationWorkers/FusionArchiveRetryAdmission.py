import json
import time
from pathlib import Path
from tempfile import TemporaryDirectory

import ApplicationProtocol as protocol
from FusionArchiveControl import MAX_SECONDS, evidence_binding, paths
from FusionArchiveControlOwner import verify_control
from FusionArchiveReplacementRecords import read_peer_receipt
from FusionArchiveRetryBudget import ADMITTED, RETRY_ATTEMPT
from FusionColdStartAdmission import blocked, prior, verify_cold_schema
from FusionExitRecords import read_pinned
from FusionQueueReceipt import owned_bytes
from Ledger import Ledger
from RetryFusionProbe import make_retry_runnable, retry_timing


# the dispatch lock spans observation and one transaction on the already parked controller
def admit_retry(owner, queue, archive, result, parked):
    with (
        Ledger(owner.store) as ledger,
        TemporaryDirectory(prefix="kit-fusion-retry-admission-") as temporary,
    ):
        ledger.refresh()
        current, timeout = parked(ledger.db, Path(temporary))
        protocol.require(
            current == archive, "Fusion archive changed before retry admission"
        )
        record, due = exact_retry(ledger, owner, queue, archive, timeout)
        files, receipt, launched = checked_control(owner, archive, result, timeout)
        if not current_window(receipt, due):
            return {"archive_replacement_status": "control_admission_expired"}
        evidence = retain_control(ledger, owner, files, result, archive)
        require_live_host(owner, launched, receipt["peer"])
        if not current_window(receipt, due):
            return {"archive_replacement_status": "control_admission_expired"}
        event = {
            **record,
            **evidence,
            "archive_manifest_sha256": archive["archive_manifest_sha256"],
            "recovery_basis_sha256": archive["recovery_basis_sha256"],
            "replacement_preflight_sha256": archive["replacement_preflight_sha256"],
            "resource": queue["resource"],
            "source_revision": queue["source_revision"],
            "first_receipt_sha256": timeout["receipt_sha256"],
            "first_result_sha256": timeout["result_sha256"],
            "next_attempt": RETRY_ATTEMPT,
            "next_run": due,
        }
        ledger.event(queue["jobs"]["a"], ADMITTED, event)
        make_retry_runnable(ledger, queue, due)
        require_live_host(owner, launched, receipt["peer"])
        protocol.require(
            current_window(receipt, due),
            "Fusion archived control expired while preparing the retry transaction",
        )
    return {
        "archive_replacement_status": "retry_admitted",
        "archive_replacement_admission_attempt": RETRY_ATTEMPT,
    }


# the existing cold-start claim guard stays intact and limits eligibility to this exact Phase A
def exact_retry(ledger, owner, queue, archive, timeout):
    verify_cold_schema(ledger)
    row, due = retry_timing(ledger.db, ledger.objects, queue, timeout)
    reservation = prior(ledger, queue["resource"])
    archive_sha = archive["archive_manifest_sha256"]
    basis = read_pinned(
        owner.root / f"archived-recovery-basis-{archive_sha}.json",
        archive["recovery_basis_sha256"],
    )
    epoch = basis["epoch"]
    protocol.require(
        reservation is not None
        and reservation["startup_receipt"] == epoch["admission_sha256"]
        and reservation["phase_a"] == epoch["job"] == row["id"]
        and reservation["definition"] == row["definition_hash"]
        and reservation["generation"] == epoch["generation"] == row["generation"]
        and reservation["fingerprint"] == epoch["fingerprint"] == row["fingerprint"]
        and row["attempts"] == basis["first_attempt"] == RETRY_ATTEMPT - 1
        and row["active_attempt"] is None
        and row["parked"] == 1
        and not blocked(ledger, queue["resource"]),
        "Fusion retry lost the exact reserved first attempt or exclusive resource",
    )
    prior_event = ledger.db.execute(
        "SELECT 1 FROM events WHERE job_id=? AND action=? LIMIT 1",
        (row["id"], ADMITTED),
    ).fetchone()
    protocol.require(
        prior_event is None, "Fusion archive already authorized its only retry"
    )
    ledger.verify_job(row)
    return {
        "definition_sha256": row["definition_hash"],
        "generation": row["generation"],
        "fingerprint": row["fingerprint"],
        "commissioned_admission_sha256": epoch["admission_sha256"],
    }, due


# transaction verification binds raw cryptographic evidence to the still-live replacement
def checked_control(owner, archive, result, timeout):
    root = owner.root
    archive_sha = archive["archive_manifest_sha256"]
    files = paths(root, archive_sha)
    launch_path = root / f"archived-replacement-launch-{archive_sha}.json"
    launch_raw = owned_bytes(launch_path)
    launch = json.loads(launch_raw)
    preflight = read_pinned(
        root / f"archived-replacement-preflight-{archive_sha}.json",
        archive["replacement_preflight_sha256"],
    )
    peer_path = root / f"archived-replacement-peer-{archive_sha}.json"
    peer_raw, launched = read_peer_receipt(peer_path, launch, launch_raw, preflight)
    request_raw = owned_bytes(files["request"])
    request = json.loads(request_raw)
    reply_raw = owned_bytes(files["result"])
    evidence, bootstrap, _, plan_raw = evidence_binding(
        vars(protocol),
        root,
        archive_sha,
        timeout["queue_job_id"],
    )
    request_sha = protocol.sha256(request_raw)
    protocol.require(
        request_sha == result["archive_replacement_control_request_sha256"]
        and protocol.sha256(reply_raw) == result["archive_replacement_control_sha256"]
        and request["archive_manifest_sha256"] == archive_sha
        and request["queue_job_id"] == timeout["queue_job_id"]
        and request["plan_sha256"]
        == timeout["plan_sha256"]
        == protocol.sha256(plan_raw)
        and request["evidence"] == evidence
        and evidence["preflight"] == archive["replacement_preflight_sha256"]
        and evidence["recovery-basis"] == archive["recovery_basis_sha256"]
        and evidence["startup"] == result["archive_replacement_startup_sha256"]
        and evidence["peer"]
        == protocol.sha256(peer_raw)
        == result["archive_replacement_process_sha256"]
        and request["peer"] == bootstrap["peer"]
        and request["profile_sha256"] == bootstrap["profile_sha256"]
        and request["launch_binding_sha256"] == bootstrap["launch_binding_sha256"],
        "Fusion retry lost its verified control or startup evidence",
    )
    reply = verify_control(owner, files, request, request_sha, launched, reply_raw)
    protocol.require(
        reply["status"] == "healthy", "Fusion retry needs a healthy control"
    )
    return files, reply, launched


# filesystem objects are stored by verified digest before the database refers to them
def retain_control(ledger, owner, files, result, archive):
    archive_sha = archive["archive_manifest_sha256"]
    sources = {
        "control_request_sha256": (
            files["request"],
            result["archive_replacement_control_request_sha256"],
        ),
        "control_sha256": (
            files["result"],
            result["archive_replacement_control_sha256"],
        ),
        "process_sha256": (
            owner.root / f"archived-replacement-peer-{archive_sha}.json",
            result["archive_replacement_process_sha256"],
        ),
        "startup_sha256": (
            owner.root / f"archived-replacement-startup-{archive_sha}.json",
            result["archive_replacement_startup_sha256"],
        ),
    }
    retained = {}
    for role, (path, expected) in sources.items():
        copied = ledger.objects.put_file(path)
        protocol.require(
            copied == expected, "Fusion archive evidence changed while retaining it"
        )
        retained[role] = copied
    result_path = ledger.objects.path(retained["control_sha256"])
    attempt = json.loads(protocol.file_bytes(result_path))["attempt_sha256"]
    protocol.require(
        ledger.objects.put_file(files["attempt"]) == attempt,
        "Fusion archive control reservation changed while retaining it",
    )
    return {**retained, "control_attempt_sha256": attempt}


# wall and monotonic bounds must both permit the first runnable instant
def current_window(reply, due):
    age_ns = time.monotonic_ns() - reply["observed_ns"]
    return (
        0 <= time.time() - reply["observed_at"] < MAX_SECONDS
        and 0 <= age_ns < MAX_SECONDS * 1_000_000_000
        and due < reply["observed_at"] + MAX_SECONDS
        and age_ns / 1_000_000_000 + max(0, due - time.time()) < MAX_SECONDS
    )


# startup host ownership must survive until the final controller write
def require_live_host(owner, launched, bound_peer):
    from MacApplicationPeer import process_peer
    from FusionStartupEvidence import executable_peer

    observed = executable_peer(process_peer, launched["peer"]["pid"])
    protocol.require(
        observed == bound_peer
        and observed == {**launched["peer"], "executable": bound_peer["executable"]}
        and protocol.identity(observed["pid"]) == launched["host"],
        "Fusion archive replacement process changed before admission",
    )
    try:
        with protocol.owner_lock(owner.root / "host.lock"):
            raise ValueError("Fusion archive replacement lost its host lock")
    except BlockingIOError:
        return
