import json
import re

from AcknowledgeApplication import stored_bytes
from ApplicationProtocol import (
    directory,
    encoded,
    file_bytes,
    record,
    require,
    sha256,
)
from FusionRequestEvidence import ARCHIVE_RECORD, match_request, probe_archive_record
from Records import digest


def parked_timeout(owner, row, queue, phase, scratch):
    scratch.mkdir(mode=0o700)
    result = json.loads(stored_bytes(owner, row["result"], scratch / "result.json"))
    require(isinstance(result, dict), "parked Fusion result must be a record")
    declared = result.get("result")
    records = declared.get("records") if isinstance(declared, dict) else None
    timeout = records.get("queue_timeout") if isinstance(records, dict) else None
    if timeout is None:
        return None
    receipt = json.loads(stored_bytes(owner, row["receipt"], scratch / "receipt.json"))
    expected = {
        "receipt_version": 1,
        "job_id": row["id"],
        "generation": row["generation"],
        "attempt": row["attempts"],
        "fingerprint": row["fingerprint"],
        "outcome": "waiting_application",
        "result_sha256": row["result"],
    }
    snapshot = receipt["snapshot"]
    require(
        all(receipt[key] == value for key, value in expected.items())
        and digest(snapshot) == row["fingerprint"]
        and snapshot["definition_hash"] == row["definition_hash"]
        and snapshot["inputs"]["plan"]
        == {"binding": queue["plan_binding"], "sha256": queue["plan_sha256"]},
        "parked Fusion receipt does not bind the current job, result and plan",
    )
    worker = result["receipt"]
    require(
        result["session_version"] == 1
        and declared["outcome"] == "waiting_application"
        and worker["receipt_version"] == 1
        and worker["job_id"] == row["id"]
        and worker["attempt"] == row["attempts"]
        and worker["orphan"] is False
        and worker["stop_reason"] is None
        and worker["exit_status"] == 0
        and worker["signal"] is None
        and "output_artifacts" not in result
        and "artifacts" not in declared,
        "parked Fusion result does not bind a settled application worker",
    )
    require(
        records["application"] == "fusion"
        and records["claim"] == "unqualified_dispatch"
        and records["native_qualified"] is False
        and records["phase"] == phase
        and records["installation"] == queue["installation"]
        and records.get("scope") == queue.get("scope")
        and isinstance(timeout, dict)
        and set(timeout)
        == {
            "version",
            "queue_job_id",
            "request_sha256",
            "source_revision",
            "operation",
            "plan_sha256",
        }
        and type(timeout["version"]) is int
        and timeout["version"] == 1
        and re.fullmatch("[a-f0-9]{32}", timeout["queue_job_id"])
        and re.fullmatch("[a-f0-9]{64}", timeout["request_sha256"])
        and timeout["operation"] in ("probe", "phase")
        and timeout["source_revision"] == queue["source_revision"]
        and timeout["plan_sha256"] == queue["plan_sha256"],
        "parked Fusion request identity differs from the pinned installation, phase or plan",
    )
    return {"receipt_sha256": row["receipt"], "result_sha256": row["result"], **timeout}


def inspect_response(response, timeout, config):
    require(
        type(response["version"]) is int
        and response["version"] == 1
        and response["provider"] == "autodesk.fusion.addin"
        and response["installation"] == config["installation"]
        and response["source_revision"] == config["source_revision"]
        and response["request_sha256"] == timeout["request_sha256"]
        and response["status"] in ("completed", "expired", "waiting_application")
        and isinstance(response["files"], dict)
        and (
            response["status"] == "completed"
            or (response["files"] == {} and response["proof"] is None)
        ),
        "retained Fusion response does not match the parked request",
    )
    return {
        "response_status": response["status"],
        "retained_output_count": len(response["files"]),
    }


def inspect_spool(config, timeout, phase):
    queue_job_id = timeout["queue_job_id"]
    operation = timeout["operation"]
    try:
        root = directory(config["endpoint"])
    except FileNotFoundError:
        return {"status": "spool_unavailable"}
    try:
        spool = directory(root / "jobs" / queue_job_id)
    except FileNotFoundError:
        if phase == "a" and operation == "probe":
            return inspect_archive(root, config, timeout)
        return {"status": "spool_unavailable"}
    observations = []
    for suffix in ("request", "running", "done"):
        try:
            raw = file_bytes(spool / f"{operation}.{suffix}")
        except FileNotFoundError:
            continue
        if suffix == "done":
            extra = inspect_response(json.loads(raw), timeout, config)
        else:
            match_request(raw, config, timeout, phase)
            extra = {}
        observations.append({"status": suffix, **extra})
    if len(observations) != 1:
        return {"status": "spool_transition_or_no_record"}
    return {**observations[0], "fence_status": fence_status(root, config, timeout)}


def inspect_archive(root, config, timeout):
    try:
        spool = directory(root / "failed-spools" / timeout["queue_job_id"])
    except FileNotFoundError:
        return {"status": "spool_unavailable"}
    except OSError as error:
        raise ValueError("archived Fusion probe evidence is unavailable") from error
    try:
        raw = file_bytes(spool / ARCHIVE_RECORD)
        manifest = json.loads(raw)
        require(
            isinstance(manifest, dict), "archived Fusion probe manifest is not a record"
        )
        expected, _ = probe_archive_record(spool, config, timeout, manifest["fence"])
        require(
            raw == encoded(expected),
            "archived Fusion probe manifest or pinned bytes changed",
        )
        observed_fence = fence_status(root, config, timeout)
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as error:
        raise ValueError(
            "archived Fusion probe evidence does not match its retained manifest"
        ) from error
    return {
        "status": "archived",
        "archive_manifest_sha256": sha256(raw),
        "fence_status": observed_fence,
    }


def fence_status(root, config, timeout):
    try:
        fence = record(root / "fence.json")
    except FileNotFoundError:
        return "absent"
    matched = (
        fence.get("job_id") == timeout["queue_job_id"]
        and fence.get("installation") == config["installation"]
    )
    if not matched:
        return "other_request"
    require(
        fence["reason"] in ("quarantined", "acceptance_required", "restart_required"),
        "retained Fusion fence has an unknown disposition",
    )
    return fence["reason"]
