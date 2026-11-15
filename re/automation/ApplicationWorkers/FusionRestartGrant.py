import json
import os
import re
import threading
import time

MAILBOX = "restart-readiness"
OPERATIONS = ("issue", "consume")
GRANT_SECONDS = 20
REQUEST_SECONDS = 60


def pending_request(protocol, host):
    mailbox = host.root / MAILBOX
    if not os.path.lexists(mailbox):
        return None
    try:
        fence = protocol["record"](host.root / "fence.json")
        if fence.get("reason") != "restart_required" or fence.get("host") != host.host:
            return None
        attempts = sorted(protocol["directory"](mailbox).glob("attempt-*"))
    except (OSError, ValueError):
        return None
    for attempt in attempts:
        try:
            protocol["directory"](attempt)
        except (OSError, ValueError):
            continue
        for operation in OPERATIONS:
            path = attempt / f"{operation}.request"
            if path.exists() and not os.path.lexists(path.with_suffix(".claimed")):
                return path
    return None


def retained_intent(protocol, host, request):
    require = protocol["require"]
    root = host.root
    require(
        os.path.lexists(root / "dispatch.lock"),
        "Fusion restart dispatch lock is absent",
    )
    try:
        with protocol["owner_lock"](root / "dispatch.lock"):
            raise ValueError(
                "Fusion restart readiness owner released its dispatch lock"
            )
    except BlockingIOError:
        pass
    require(
        host.provider == protocol["FUSION_PROVIDER"]
        and request["installation"] == host.config["installation"]
        and request["source_revision"] == host.config["source_revision"]
        and re.fullmatch("[0-9a-f]{32}", request["handoff_id"])
        and not os.path.lexists(root / protocol["ACKNOWLEDGEMENT"])
        and not any(protocol["directory"](root / "jobs").iterdir()),
        "Fusion restart grant requires the acknowledged empty installation queue",
    )
    raw = protocol["file_bytes"](root / f"restart-intent-{request['handoff_id']}.json")
    intent = json.loads(raw)
    fence = protocol["file_bytes"](root / "fence.json")
    handoff = intent["restart_handoff"]
    require(
        protocol["sha256"](raw) == request["intent_sha256"]
        and intent["version"] == 1
        and intent["provider"] == host.provider
        and intent["installation"] == request["installation"]
        and intent["source_revision"] == request["source_revision"]
        and intent["installation_sha256"] == host.installation_sha256
        and protocol["fusion_startup_loaded"](host.config, host.loaded_sources)
        and intent["bootstrap_sha256"] == host.loaded_sources["bootstrap"]["sha256"]
        and intent["protocol_sha256"] == host.loaded_sources["protocol"]["sha256"]
        and protocol["sha256"](fence) == intent["fence_sha256"]
        and fence == protocol["encoded"](handoff)
        and handoff["reason"] == "restart_required"
        and handoff["job_id"] == request["handoff_id"]
        and handoff["host"] == host.host,
        "Fusion restart grant differs from the pinned provider, intent or retained fence",
    )
    return intent


def verify_request(protocol, request, operation, now):
    required = {
        "version",
        "operation",
        "installation",
        "source_revision",
        "handoff_id",
        "intent_sha256",
        "challenge",
        "client",
        "deadline",
    }
    if operation == "consume":
        required.add("grant_sha256")
    protocol["require"](
        set(request) == required
        and type(request["version"]) is int
        and request["version"] == 1
        and request["operation"] == operation
        and re.fullmatch("[0-9a-f]{48}", request["challenge"])
        and type(request["deadline"]) in (int, float)
        and now < request["deadline"] <= now + REQUEST_SECONDS
        and request["client"] == protocol["identity"](request["client"]["pid"]),
        "Fusion restart readiness request expired or its owner changed",
    )


def active_grant(protocol, directory, request, response, now):
    path = directory / "issue.response"
    raw = protocol["file_bytes"](path)
    grant = json.loads(raw)
    first = protocol["record"](directory / "issue.claimed")
    protocol["require"](
        protocol["sha256"](raw) == request["grant_sha256"]
        and grant["status"] == "granted"
        and grant["request_sha256"] == protocol["sha256"](protocol["encoded"](first))
        and all(
            first[key] == request[key]
            for key in (
                "challenge",
                "client",
                "installation",
                "source_revision",
                "handoff_id",
                "intent_sha256",
            )
        )
        and all(
            grant[key] == response[key] for key in ("provider", "host", "source_sha256")
        )
        and grant["documents"] == 0
        and grant["observed_at"]
        <= now
        < grant["expires_at"]
        <= grant["observed_at"] + GRANT_SECONDS
        and request["deadline"] <= grant["expires_at"],
        "Fusion restart readiness grant is stale, changed or already consumed",
    )
    return path


def serve(protocol, source_pin, host, path, app, main_thread):
    require = protocol["require"]
    operation = path.stem
    require(
        threading.get_ident() == main_thread
        and path.parent.parent == host.root / MAILBOX
        and re.fullmatch("attempt-[A-Za-z0-9_-]{1,64}", path.parent.name)
        and protocol["directory"](path.parent) == path.parent
        and operation in OPERATIONS
        and path.suffix == ".request",
        "Fusion restart readiness requires its private main-thread callback",
    )
    claimed = path.with_suffix(".claimed")
    target = path.with_suffix(".response")
    try:
        protocol["exclusive_rename"](path, claimed)
    except FileNotFoundError:
        return
    raw = protocol["file_bytes"](claimed)
    response = {
        "version": 1,
        "request_sha256": protocol["sha256"](raw),
        "provider": host.provider,
        "host": host.host,
        "source_sha256": source_pin["sha256"],
    }
    try:
        request = json.loads(raw)
        verify_request(protocol, request, operation, time.time())
        intent = retained_intent(protocol, host, request)
        require(
            app.version == intent["fusion_version"]
            and app.documents.count == 0
            and app.activeDocument is None,
            "Fusion restart requires the expected build and no open documents",
        )
        observed = time.time()
        require(observed < request["deadline"], "Fusion restart request expired")
        if operation == "consume":
            grant = active_grant(protocol, path.parent, request, response, observed)
            protocol["exclusive_rename"](grant, path.parent / "issue.consumed")
            response.update(status="consumed", grant_sha256=request["grant_sha256"])
        else:
            response.update(
                status="granted",
                expires_at=min(request["deadline"], observed + GRANT_SECONDS),
            )
        response.update(observed_at=observed, documents=0)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        response.update(status="refused")
    protocol["write_new"](target, protocol["encoded"](response))
