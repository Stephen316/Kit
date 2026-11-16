import json
import os
import time
from types import SimpleNamespace

from ApplicationProtocol import encoded, identity, require, sha256
from FusionExitRecords import read_pinned
from FusionQueueReceipt import owned_bytes, seal
from FusionStartupEvidence import MAX_SECONDS
from FusionStartupProvision import StartupUnavailable, observe
from MacProcessExit import verify_peer


# later startup can only use the process from the exact sealed archive launch
def read_peer_receipt(path, request, request_raw, preflight):
    raw = owned_bytes(path)
    value = json.loads(raw)
    peer = value["peer"]
    require(
        value["version"] == 1
        and value["scope"] == "fusion_archived_replacement_process"
        and value["launch_request_sha256"] == sha256(request_raw)
        and value["replacement_preflight_sha256"]
        == request["replacement_preflight_sha256"]
        and value["host"]["pid"] == peer["pid"] != preflight["epoch"]["peer"]["pid"]
        and peer["uid"] == preflight["epoch"]["peer"]["uid"]
        and request["requested_at"]
        <= value["dispatched_at"]
        < request["dispatch_before"]
        and value["dispatched_at"] <= peer["started_unix_microseconds"] / 1_000_000,
        "Fusion archive replacement process differs from the sealed request",
    )
    return raw, value


# one vendor startup reply can prove the fresh archive process while the installation stays parked
def startup_proof(owner, preflight, bundle, launched, launch_raw, path, *, verify):
    executable = bundle["executable"]
    verify_peer(launched["peer"], executable)
    require(
        identity(launched["peer"]["pid"]) == launched["host"],
        "Fusion archive replacement host identity changed",
    )
    profile = read_pinned(owner.args.profile, preflight["profile_sha256"])
    existing = optional_receipt(path)
    if existing is not None:
        verify_bootstrap(existing, preflight, bundle, launched, launch_raw, profile)
        return startup_report(existing, launch_raw)
    unobserved = {
        "archive_replacement_status": "startup_unobserved",
        "archive_replacement_process_sha256": sha256(launch_raw),
    }
    remaining = int(
        launched["dispatched_at"] + owner.args.startup_seconds - time.time()
    )
    if remaining < 1:
        return unobserved
    args = SimpleNamespace(**vars(owner.args))
    args.pid = launched["peer"]["pid"]
    args.wait_seconds = min(MAX_SECONDS, remaining)
    replies = []
    try:
        observe(
            args,
            owner.config,
            owner.installation_bytes,
            owner.lifecycle_sha,
            executable,
            launch_binding=sha256(preflight["launch_challenge"].encode("ascii")),
            retain=replies.append,
        )
    except StartupUnavailable:
        return unobserved
    (reply,) = replies
    raw = encoded(
        {
            "version": 1,
            "scope": "fusion_archived_replacement_startup",
            "launch_receipt_sha256": sha256(launch_raw),
            "bootstrap_sha256": sha256(reply),
            "bootstrap": json.loads(reply),
        }
    )
    verify_bootstrap(raw, preflight, bundle, launched, launch_raw, profile)
    with verify():
        verify_peer(launched["peer"], executable)
        seal(path, raw)
    return startup_report(raw, launch_raw)


# the signed deployed startup challenge remains bound to this source and physical peer
def verify_bootstrap(raw, preflight, bundle, launched, launch_raw, profile):
    value = json.loads(raw)
    reply = value["bootstrap"]
    require(
        value["version"] == 1
        and value["scope"] == "fusion_archived_replacement_startup"
        and value["launch_receipt_sha256"] == sha256(launch_raw)
        and value["bootstrap_sha256"] == sha256(encoded(reply))
        and reply["scope"] == "fusion_bootstrap_startup_observation"
        and reply["startup_context"] == "vendor_application_startup"
        and reply["profile_sha256"] == preflight["profile_sha256"]
        and reply["source_revision"] == preflight["epoch"]["source_revision"]
        and reply["startup_provider_sha256"] == profile["startup_provider_sha256"]
        and reply["launch_binding_sha256"]
        == sha256(preflight["launch_challenge"].encode("ascii"))
        and reply["peer"]
        == {**launched["peer"], "executable": os.fspath(bundle["executable"])}
        and launched["dispatched_at"] <= reply["observed_at"] <= time.time(),
        "Fusion archive replacement bootstrap differs from the fresh process",
    )


# recovery verification surfaces only the durable evidence pins
def startup_report(raw, launch_raw):
    return {
        "archive_replacement_status": "startup_verified_control_pending",
        "archive_replacement_process_sha256": sha256(launch_raw),
        "archive_replacement_startup_sha256": sha256(raw),
    }


# an unobserved provider reply never becomes startup evidence
def optional_receipt(path):
    try:
        return owned_bytes(path)
    except FileNotFoundError:
        return None
