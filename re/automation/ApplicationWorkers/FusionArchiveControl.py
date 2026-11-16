import json
import os
import re
import time

ACTIVE = "archive-control-active.json"
MAX_SECONDS = 30
REQUEST_SCOPE = "owner_fusion_archived_control_request"
RESULT_SCOPE = "fusion_archived_replacement_control"
ENDPOINT_RECORDS = ("recovery-basis", "preflight", "launch", "peer", "startup")


# only a verified archive digest may select immutable request and evidence paths
def paths(root, archive_sha):
    if not isinstance(archive_sha, str) or not re.fullmatch(
        "[0-9a-f]{64}", archive_sha
    ):
        raise ValueError("invalid Fusion archive control identity")
    return {
        role: root / f"archived-control-{role}-{archive_sha}.json"
        for role in ("request", "attempt", "result")
    }


# archived native input is selected by the retained queue job, never a supplied path
def archived_spool(protocol, root, queue_job):
    protocol["require"](
        isinstance(queue_job, str) and re.fullmatch("[0-9a-f]{32}", queue_job),
        "invalid archived Fusion spool identity",
    )
    return protocol["directory"](root / "failed-spools" / queue_job)


# owner and embedded host verify the same complete chain before accepting a measurement
def evidence_binding(protocol, root, archive_sha, queue_job):
    spool = archived_spool(protocol, root, queue_job)
    read = protocol["file_bytes"]
    digest = protocol["sha256"]
    manifest = read(spool / "ProbeArchive.json")
    protocol["require"](
        digest(manifest) == archive_sha,
        "Fusion archived control manifest changed",
    )
    records = {}
    for role in ENDPOINT_RECORDS:
        stem = "archived" if role == "recovery-basis" else "archived-replacement"
        records[role] = read(root / f"{stem}-{role}-{archive_sha}.json")
    basis, preflight, launch, peer, startup = (
        json.loads(records[role]) for role in ENDPOINT_RECORDS
    )
    archive = json.loads(manifest)
    timeout = archive["timeout"]
    plan_raw = read(spool / "plan.json")
    protocol["require"](
        archive["phase"] == "a"
        and timeout["queue_job_id"] == launch["queue_job_id"] == queue_job
        and basis["archive_manifest_sha256"]
        == preflight["archive_manifest_sha256"]
        == launch["archive_manifest_sha256"]
        == archive_sha
        and digest(records["recovery-basis"])
        == preflight["recovery_basis_sha256"]
        == launch["recovery_basis_sha256"]
        and digest(records["preflight"])
        == launch["replacement_preflight_sha256"]
        == peer["replacement_preflight_sha256"]
        and digest(records["launch"]) == peer["launch_request_sha256"]
        and digest(records["peer"]) == startup["launch_receipt_sha256"]
        and digest(plan_raw) == basis["plan_sha256"] == timeout["plan_sha256"]
        and digest(read(spool / "probe.request"))
        == basis["request_sha256"]
        == timeout["request_sha256"]
        and not os.path.lexists(root / "fusion-lifecycle-active.json"),
        "Fusion archived control differs from the retained recovery chain",
    )
    return (
        {role: digest(raw) for role, raw in records.items()},
        startup["bootstrap"],
        spool,
        plan_raw,
    )


# host receipt only covers work performed while the exact owner still holds dispatch custody
def require_dispatch(protocol, root):
    try:
        with protocol["owner_lock"](root / "dispatch.lock"):
            pass
    except BlockingIOError:
        return
    raise ValueError("Fusion archived control lost the dispatch owner")


# startup and control use different mailboxes so ordinary startup cannot issue a measurement
def matches(startup, request):
    return (
        set(request)
        == {
            "version",
            "scope",
            "archive_manifest_sha256",
            "queue_job_id",
            "evidence",
            "plan_sha256",
            "profile_sha256",
            "peer",
            "client",
            "launch_binding_sha256",
            "issued_at",
            "deadline",
            "deadline_ns",
        }
        and type(request["version"]) is int
        and request["version"] == 1
        and request["scope"] == REQUEST_SCOPE
        and request["peer"] == startup.peer
        and request["client"] != startup.peer
        and request["profile_sha256"] == startup.profile_sha256
        and startup.launch_binding is not None
        and request["launch_binding_sha256"] == startup.launch_binding
        and type(request["issued_at"]) in (int, float)
        and type(request["deadline"]) in (int, float)
        and type(request["deadline_ns"]) is int
        and time.monotonic_ns() < request["deadline_ns"]
        and request["issued_at"]
        <= time.time()
        < request["deadline"]
        <= request["issued_at"] + MAX_SECONDS
    )


# fresh event delivery does not authorize replay after the native reservation is durable
def pending(startup):
    protocol = startup.protocol
    request = protocol["record"](startup.root / ACTIVE)
    if matches(startup, request):
        archive_sha = request["archive_manifest_sha256"]
        files = paths(startup.host.root, archive_sha)
        if not any(os.path.lexists(files[role]) for role in ("attempt", "result")):
            return f"archive:{archive_sha}"
    return None


# every irreversible boundary binds the same live client, vendor startup and idle installation
def check_custody(startup, request, raw, files):
    protocol = startup.protocol
    root = startup.host.root
    client = request["client"]
    require_dispatch(protocol, root)
    startup.check_deployment()
    protocol["require"](
        matches(startup, request)
        and client == startup.exact_peer(client["pid"])
        and protocol["file_bytes"](startup.root / ACTIVE) == raw
        and protocol["file_bytes"](files["request"]) == raw
        and not any(protocol["directory"](root / "jobs").iterdir())
        and not any(
            os.path.lexists(root / name)
            for name in (
                protocol["ACKNOWLEDGEMENT"],
                "grant.json",
                "fence.json",
            )
        ),
        "Fusion archived control requires the exact idle main-thread peer and live owner",
    )


# archive recovery cannot interrupt or close documents outside the new control
def idle(app):
    return (
        app.isStartupComplete is True
        and app.hasActiveJobs is False
        and app.documents.count == 0
        and app.activeDocument is None
    )


# the proof is strictly bound to the same bootstrap and saved control input
def serve(startup, archive_sha, app):
    protocol = startup.protocol
    require = protocol["require"]
    digest = protocol["sha256"]
    root = startup.host.root
    files = paths(root, archive_sha)
    raw = protocol["file_bytes"](files["request"])
    request = json.loads(raw)
    require(
        request["archive_manifest_sha256"] == archive_sha,
        "wrong Fusion archive control",
    )
    check_custody(startup, request, raw, files)
    evidence, bootstrap, spool, plan_raw = evidence_binding(
        protocol, root, archive_sha, request["queue_job_id"]
    )
    require(
        request["evidence"] == evidence
        and request["plan_sha256"] == digest(plan_raw)
        and bootstrap["peer"] == startup.peer
        and bootstrap["profile_sha256"] == startup.profile_sha256
        and bootstrap["launch_binding_sha256"] == startup.launch_binding
        and bootstrap["fusion_version"] == app.version
        and bootstrap["observed_at"] <= request["issued_at"],
        "Fusion archived control does not name its authenticated startup peer",
    )
    response = {
        "version": 1,
        "scope": RESULT_SCOPE,
        "request_sha256": digest(raw),
        "peer": startup.peer,
        "provider_sha256": _source_pin["sha256"],
    }
    if not idle(app):
        check_custody(startup, request, raw, files)
        refused = {
            **response,
            "status": "refused",
            "observed_at": time.time(),
            "observed_ns": time.monotonic_ns(),
        }
        require(matches(startup, request), "Fusion archive control expired")
        protocol["write_new"](files["result"], protocol["encoded"](refused))
        return
    counterpart = protocol["load_pinned"](startup.host.config, protocol["COUNTERPART"])
    counterpart["protocol"] = protocol
    plan, tool = counterpart["pinned_plan"](startup.host, spool, request)
    reservation = {
        "version": 1,
        "request_sha256": digest(raw),
        "peer": startup.peer,
        "reserved_at": time.time(),
    }
    reservation_raw = protocol["encoded"](reservation)
    current = evidence_binding(protocol, root, archive_sha, request["queue_job_id"])[0]
    check_custody(startup, request, raw, files)
    require(
        current == evidence and idle(app), "Fusion archive control lost its idle peer"
    )
    protocol["write_new"](files["attempt"], reservation_raw)
    check_custody(startup, request, raw, files)
    require(idle(app), "Fusion archive control lost its reserved idle peer")
    proof = counterpart["measure_control_proof"](
        startup.host, request["plan_sha256"], app, plan, tool
    )
    check_custody(startup, request, raw, files)
    require(
        idle(app)
        and evidence_binding(protocol, root, archive_sha, request["queue_job_id"])[0]
        == evidence,
        "Fusion archive recovery evidence changed during control",
    )
    reply = {
        **response,
        "attempt_sha256": digest(reservation_raw),
        "proof": proof,
        "status": "healthy",
        "observed_at": time.time(),
        "observed_ns": time.monotonic_ns(),
    }
    require(matches(startup, request), "Fusion archive control deadline elapsed")
    protocol["write_new"](files["result"], protocol["encoded"](reply))
