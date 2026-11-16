import json
import re

import ApplicationProtocol as protocol
from ApplicationProtocol import file_bytes, require, sha256
from FusionExitEvidence import verify_readiness
from FusionQuitAuthorization import evidence, paths


def pin(value):
    require(
        isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value),
        "expected an exact lowercase evidence SHA-256",
    )
    return value


def read_pinned(path, expected):
    raw = file_bytes(path)
    require(sha256(raw) == pin(expected), "record differs from its immutable digest")
    return json.loads(raw)


def exit_evidence(root, intent_sha256, exit_sha256):
    identifier = pin(intent_sha256)
    intent = read_pinned(root / f"quit-intent-{identifier}.json", identifier)
    receipt = read_pinned(root / f"quit-exit-{identifier}.json", exit_sha256)
    readiness = intent["readiness"]
    verify_readiness(readiness)
    require(
        intent["version"] == receipt["version"] == 1
        and intent["scope"] == "external_fusion_exit_watch"
        and receipt["scope"] == "external_fusion_exit_observation"
        and receipt["status"] == "exact_exit_observed"
        and receipt["observation"] == "darwin_process_exit_event"
        and receipt["quit_intent_sha256"] == identifier
        and receipt["restart_intent_sha256"] == readiness["intent_sha256"]
        and receipt["peer"] == readiness["peer"]
        and receipt["fence_sha256"] == intent["fence_sha256"]
        and readiness["observed_at"] <= intent["armed_at"] < readiness["expires_at"]
        and intent["armed_at"] <= receipt["observed_at"],
        "Fusion exit artifacts do not bind the exact accepted readiness and peer",
    )
    if intent.get("quit_mode") == "authorized_cocoa":
        action = receipt["quit_action"]
        files = paths(root, readiness["intent_sha256"])
        request = read_pinned(files["request"], action["request_sha256"])
        require(
            request["quit_intent_sha256"] == identifier
            and request["intent_sha256"] == readiness["intent_sha256"]
            and request["fence_sha256"] == receipt["fence_sha256"]
            and action == evidence(vars(protocol), files, action["request_sha256"])
            and "attempt_sha256" in action
            and action["state"] in ("reserved", "quit_call_returned"),
            "Fusion exit evidence differs from the reserved Cocoa quit action",
        )
    return readiness, receipt
