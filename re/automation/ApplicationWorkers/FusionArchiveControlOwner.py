import json
import os
import time

import ApplicationProtocol as protocol
from FusionArchiveControl import (
    ACTIVE,
    MAX_SECONDS,
    REQUEST_SCOPE,
    RESULT_SCOPE,
    evidence_binding,
    paths,
)
from FusionArchiveReplacementRecords import optional_receipt
from FusionStartupEvidence import MAILBOX, executable_peer
from MacApplicationPeer import process_peer


# a fresh owner can consume old durable evidence but never republish a sealed effect
def observe_control(owner, archive, launch_request, started, launched, verify):
    root = owner.root
    archive_sha = archive["archive_manifest_sha256"]
    queue_job = launch_request["queue_job_id"]
    files = paths(root, archive_sha)
    mailbox = protocol.directory(root / MAILBOX)
    active = mailbox / ACTIVE
    with verify():
        evidence, bootstrap, _, plan_raw = evidence_binding(
            vars(protocol), root, archive_sha, queue_job
        )
        protocol.require(
            evidence["startup"] == started["archive_replacement_startup_sha256"]
            and evidence["peer"] == started["archive_replacement_process_sha256"]
            and evidence["preflight"] == archive["replacement_preflight_sha256"]
            and evidence["recovery-basis"] == archive["recovery_basis_sha256"],
            "Fusion archive control lost verified replacement custody",
        )
        binding = {
            "version": 1,
            "scope": REQUEST_SCOPE,
            "archive_manifest_sha256": archive_sha,
            "queue_job_id": queue_job,
            "evidence": evidence,
            "plan_sha256": protocol.sha256(plan_raw),
            "profile_sha256": bootstrap["profile_sha256"],
            "peer": bootstrap["peer"],
            "launch_binding_sha256": bootstrap["launch_binding_sha256"],
        }
        request_raw = optional_receipt(files["request"])
        if request_raw is None:
            protocol.require(
                not any(os.path.lexists(files[role]) for role in ("attempt", "result"))
                and not os.path.lexists(active),
                "Fusion control effects lack the exact immutable request",
            )
            owner_peer = executable_peer(process_peer, os.getpid())
            now = time.time()
            seconds = min(owner.args.wait_seconds, MAX_SECONDS)
            request = {
                **binding,
                "client": owner_peer,
                "issued_at": now,
                "deadline": now + seconds,
                "deadline_ns": time.monotonic_ns() + seconds * 1_000_000_000,
            }
            request_raw = protocol.encoded(request)
            protocol.write_new(files["request"], request_raw)
            protocol.write_new(active, request_raw)
            created = True
        else:
            request = json.loads(request_raw)
            protocol.require(
                request
                == {
                    **binding,
                    "client": request["client"],
                    "issued_at": request["issued_at"],
                    "deadline": request["deadline"],
                    "deadline_ns": request["deadline_ns"],
                }
                and type(request["deadline_ns"]) is int
                and bootstrap["observed_at"] <= request["issued_at"] <= time.time()
                and 0 < request["deadline"] - request["issued_at"] <= MAX_SECONDS,
                "Fusion archive control request belongs to another startup or archive",
            )
            created = False
    try:
        return stored_control(
            owner, files, request, request_raw, launched, verify, created
        )
    finally:
        if optional_receipt(active) == request_raw:
            active.unlink()
            protocol.sync_directory(active.parent)


# waiting for native code must not retain the controller database read transaction
def stored_control(owner, files, request, request_raw, launched, verify, created):
    while True:
        reply_raw = optional_receipt(files["result"])
        if (
            reply_raw is not None
            or not created
            or time.monotonic_ns() >= request["deadline_ns"]
            or time.time() >= request["deadline"]
        ):
            break
        time.sleep(0.05)
    request_sha = protocol.sha256(request_raw)
    base = {"archive_replacement_control_request_sha256": request_sha}
    if reply_raw is None:
        return {**base, "archive_replacement_status": "control_unobserved"}
    with verify():
        evidence, _, _, _ = evidence_binding(
            vars(protocol),
            owner.root,
            request["archive_manifest_sha256"],
            request["queue_job_id"],
        )
        protocol.require(
            protocol.file_bytes(files["request"]) == request_raw
            and evidence == request["evidence"],
            "Fusion archive control custody changed before receipt verification",
        )
        reply = verify_control(owner, files, request, request_sha, launched, reply_raw)
    return {
        **base,
        "archive_replacement_control_sha256": protocol.sha256(reply_raw),
        "archive_replacement_status": (
            "control_verified_admission_pending"
            if reply["status"] == "healthy"
            else "control_refused"
        ),
    }


# only a bounded receipt from the current pinned provider can describe a healthy control
def verify_control(owner, files, request, request_sha, launched, reply_raw):
    reply = json.loads(reply_raw)
    peer = executable_peer(process_peer, launched["peer"]["pid"])
    provider_sha = protocol.sha256(
        protocol.committed_bytes(owner.config, protocol.MAC_ARCHIVE_CONTROL)
    )
    protocol.require(
        type(reply["version"]) is int
        and reply["version"] == 1
        and reply["scope"] == RESULT_SCOPE
        and reply["request_sha256"] == request_sha
        and reply["peer"] == request["peer"] == peer
        and reply["provider_sha256"] == provider_sha
        and request["issued_at"] <= reply["observed_at"] < request["deadline"]
        and reply["observed_at"] <= time.time(),
        "Fusion archive control result differs from its live request",
    )
    if reply["status"] == "refused":
        protocol.require(
            set(reply)
            == {
                "version",
                "scope",
                "request_sha256",
                "peer",
                "provider_sha256",
                "observed_at",
                "status",
            }
            and not os.path.lexists(files["attempt"]),
            "Fusion archive control refusal has uncertain actuation",
        )
        return reply
    attempt_raw = protocol.file_bytes(files["attempt"])
    attempt = json.loads(attempt_raw)
    proof = reply["proof"]
    protocol.require(
        set(reply)
        == {
            "version",
            "scope",
            "request_sha256",
            "attempt_sha256",
            "peer",
            "provider_sha256",
            "observed_at",
            "status",
            "proof",
        }
        and reply["status"] == "healthy"
        and reply["attempt_sha256"] == protocol.sha256(attempt_raw)
        and attempt
        == {
            "version": 1,
            "request_sha256": request_sha,
            "peer": peer,
            "reserved_at": attempt["reserved_at"],
        }
        and request["issued_at"]
        <= attempt["reserved_at"]
        <= proof["measured_at"]
        <= reply["observed_at"]
        and proof["host"] == launched["host"]
        and proof["claim"] == "unqualified_application_observation"
        and proof["control"] == "healthy"
        and proof["plan_sha256"] == request["plan_sha256"]
        and proof["documents_after"] == 0
        and proof["readings"]["healthy_control"]["compute_all_return"] is True,
        "Fusion archive control lacks its exact durable healthy measurement",
    )
    return reply
