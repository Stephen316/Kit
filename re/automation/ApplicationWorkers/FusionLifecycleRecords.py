import json
import os

from ApplicationProtocol import file_bytes, require, sha256
from FusionExitRecords import exit_evidence, pin, read_pinned
from FusionQuitAuthorization import custody_path, paths
from FusionReplacementLaunch import replacement_paths


def optional(path):
    try:
        return file_bytes(path)
    except FileNotFoundError:
        return None


def active_intent(queue_path, queue_raw, restart_sha, intent, lifecycle_sha):
    return {
        "version": 1,
        "queue": queue_path.name,
        "queue_receipt_sha256": sha256(queue_raw),
        "restart_intent_sha256": restart_sha,
        "handoff_id": intent["restart_handoff"]["job_id"],
        "installation_sha256": intent["installation_sha256"],
        "lifecycle_sha256": lifecycle_sha,
        **{
            key: intent[key]
            for key in (
                "receipt_sha256",
                "result_sha256",
                "attempt",
                "generation",
                "fingerprint",
                "fence_sha256",
                "installation",
                "source_revision",
            )
        },
    }


def eligible_exit(root, active):
    restart_sha = active["restart_intent_sha256"]
    files = paths(root, restart_sha)
    link_raw = optional(custody_path(root, "replacement", active["handoff_id"]))
    raw = optional(files["request"])
    if raw is None:
        require(
            link_raw is None
            and not any(os.path.lexists(files[kind]) for kind in ("attempt", "action")),
            "Fusion quit request is missing while its action custody exists",
        )
        return None, None
    request = json.loads(raw)
    require(
        request["scope"] == "macos_fusion_quit_request"
        and request["version"] == 1
        and request["intent_sha256"] == restart_sha
        and request["handoff_id"] == active["handoff_id"]
        and request["fence_sha256"] == active["fence_sha256"]
        and request["installation"] == active["installation"]
        and request["source_revision"] == active["source_revision"],
        "quit request belongs to another Fusion restart",
    )
    arm = pin(request["quit_intent_sha256"])
    if link_raw is not None:
        link = json.loads(link_raw)
        launch_path, _ = replacement_paths(root, arm)
        launch_request = read_pinned(launch_path, link["launch_request_sha256"])
        require(
            link["version"] == 1
            and link["quit_intent_sha256"] == arm
            and launch_request["scope"] == "owner_fusion_replacement_request"
            and launch_request["version"] == 1
            and launch_request["handoff_id"] == active["handoff_id"]
            and launch_request["restart_intent_sha256"] == restart_sha
            and launch_request["quit_intent_sha256"] == arm
            and launch_request["fence_sha256"] == active["fence_sha256"]
            and launch_request["installation_sha256"] == active["installation_sha256"],
            "replacement link belongs to another Fusion restart",
        )
    observed = optional(root / f"quit-exit-{arm}.json")
    if observed is None:
        require(link_raw is None, "authorized Fusion replacement has no observed exit")
        return arm, None
    exit_sha = sha256(observed)
    readiness, receipt = exit_evidence(root, arm, exit_sha)
    require(
        readiness["intent_sha256"] == restart_sha
        and readiness["installation_sha256"] == active["installation_sha256"]
        and readiness["lifecycle_sha256"] == active["lifecycle_sha256"]
        and receipt["quit_action"]["request_sha256"] == sha256(raw),
        "Fusion exit differs from the active lifecycle",
    )
    if link_raw is not None:
        require(
            launch_request["quit_exit_sha256"] == exit_sha,
            "Fusion replacement links a different exit receipt",
        )
    return arm, exit_sha


def pin_handoff(value):
    require(
        isinstance(value, str)
        and len(value) == 32
        and all(part in "0123456789abcdef" for part in value),
        "invalid Fusion handoff",
    )
    return value
