import json
import os
import re
import threading
import time
from contextlib import contextmanager


def paths(root, restart_digest):
    if not re.fullmatch("[0-9a-f]{64}", restart_digest):
        raise ValueError("invalid accepted Fusion restart identity")
    return {
        kind: root / f"quit-{kind}-{restart_digest}.json"
        for kind in ("request", "attempt", "action")
    }


def exact_peer(read_peer, pid):
    peer = read_peer(pid)
    return {**peer, "executable": os.fspath(peer["executable"])}


def custody_path(root, kind, handoff_id):
    if not re.fullmatch("[0-9a-f]{32}", handoff_id):
        raise ValueError("invalid Fusion restart handoff")
    return root / f"quit-{kind}-{handoff_id}.json"


def hold_record(request):
    return {
        "version": 1,
        "restart_intent_sha256": request["intent_sha256"],
        "fence_sha256": request["fence_sha256"],
    }


def evidence(protocol, files, request_digest):
    result = {"request_sha256": request_digest, "state": "request_pending"}
    for kind, field, statuses in (
        ("action", "action_sha256", ("quit_call_returned", "refused")),
        ("attempt", "attempt_sha256", ("reserved",)),
    ):
        try:
            raw = protocol["file_bytes"](files[kind])
        except FileNotFoundError:
            continue
        value = json.loads(raw)
        protocol["require"](
            set(value) == {"version", "request_sha256", "status"}
            and type(value["version"]) is int
            and value["version"] == 1
            and value["request_sha256"] == request_digest
            and value["status"] in statuses,
            "Fusion quit action record differs from its request",
        )
        result[field] = protocol["sha256"](raw)
        if result["state"] == "request_pending":
            result["state"] = value["status"]
    protocol["require"](
        result["state"] != "quit_call_returned" or "attempt_sha256" in result,
        "Fusion quit return requires a durable attempt",
    )
    return result


@contextmanager
def authorize(
    protocol,
    config,
    root,
    readiness,
    executable,
    quit_intent_sha256,
    watch_deadline_ns,
    read_peer,
    bridge_sha256,
    action_source_sha256,
):
    files = paths(root, readiness["intent_sha256"])
    protocol["require"](
        re.fullmatch("[0-9a-f]{64}", quit_intent_sha256),
        "invalid armed Fusion quit intent",
    )
    armed_bytes = protocol["file_bytes"](
        root / f"quit-intent-{quit_intent_sha256}.json"
    )
    armed = json.loads(armed_bytes)
    with protocol["owner_lock"](root / f"quit-lease-{quit_intent_sha256}.lock"):
        watcher = exact_peer(read_peer, os.getpid())
        target = {**readiness["peer"], "executable": os.fspath(executable)}
        remaining_ns = int((readiness["expires_at"] - time.time()) * 1_000_000_000)
        now_ns = time.monotonic_ns()
        deadline_ns = min(watch_deadline_ns, now_ns + remaining_ns)
        protocol["require"](
            now_ns < deadline_ns
            and protocol["sha256"](armed_bytes) == quit_intent_sha256
            and armed["quit_mode"] == "authorized_cocoa"
            and armed["readiness"] == readiness
            and armed["watcher"]["pid"] == watcher["pid"]
            and exact_peer(read_peer, target["pid"]) == target,
            "Fusion quit authorization lost its live watcher or target",
        )
        handoff = protocol["record"](root / "fence.json")
        request = {
            "version": 1,
            "scope": "macos_fusion_quit_request",
            "installation": handoff["installation"],
            "source_revision": config["source_revision"],
            "handoff_id": handoff["job_id"],
            "intent_sha256": readiness["intent_sha256"],
            "quit_intent_sha256": quit_intent_sha256,
            "fence_sha256": armed["fence_sha256"],
            "watcher": watcher,
            "target": target,
            "deadline_ns": deadline_ns,
            "bridge_sha256": bridge_sha256,
            "action_source_sha256": action_source_sha256,
        }
        raw = protocol["encoded"](request)
        hold_path = custody_path(root, "hold", request["handoff_id"])
        hold_bytes = protocol["encoded"](hold_record(request))
        if os.path.lexists(hold_path):
            protocol["require"](
                protocol["file_bytes"](hold_path) == hold_bytes,
                "existing automatic quit fence custody differs",
            )
        else:
            protocol["write_new"](hold_path, hold_bytes)
        protocol["write_new"](files["request"], raw)
        yield lambda: evidence(protocol, files, protocol["sha256"](raw))


def pending(protocol, host):
    try:
        fence = protocol["record"](host.root / "fence.json")
        if fence.get("reason") != "restart_required" or fence.get("host") != host.host:
            return None
        handoff_id = fence["job_id"]
        if not re.fullmatch("[0-9a-f]{32}", handoff_id):
            return None
        intent = protocol["file_bytes"](host.root / f"restart-intent-{handoff_id}.json")
        files = paths(host.root, protocol["sha256"](intent))
        if files["request"].is_file() and not any(
            os.path.lexists(files[kind]) for kind in ("attempt", "action")
        ):
            return files["request"]
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None


def verify_lease(protocol, host, request, armed, read_peer):
    require = protocol["require"]
    lease = host.root / f"quit-lease-{request['quit_intent_sha256']}.lock"
    require(os.path.lexists(lease), "Fusion quit watcher lease is absent")
    try:
        with protocol["owner_lock"](lease):
            raise ValueError("Fusion quit watcher released its lease")
    except BlockingIOError:
        pass
    remaining = request["deadline_ns"] - time.monotonic_ns()
    require(
        0 < remaining <= 20_000_000_000
        and time.time() < armed["readiness"]["expires_at"]
        and exact_peer(read_peer, request["watcher"]["pid"]) == request["watcher"]
        and exact_peer(read_peer, os.getpid()) == request["target"]
        and request["target"]["pid"] == host.host["pid"],
        "Fusion quit lease expired or its exact watcher or target differs",
    )


def verify_armed(protocol, host, request, source_pin, grant_pin, bridge_pin):
    require = protocol["require"]
    identifier = request["quit_intent_sha256"]
    require(
        re.fullmatch("[0-9a-f]{64}", identifier)
        and set(request)
        == {
            "version",
            "scope",
            "installation",
            "source_revision",
            "handoff_id",
            "intent_sha256",
            "quit_intent_sha256",
            "fence_sha256",
            "watcher",
            "target",
            "deadline_ns",
            "bridge_sha256",
            "action_source_sha256",
        }
        and type(request["version"]) is int
        and request["version"] == 1
        and request["scope"] == "macos_fusion_quit_request"
        and request["action_source_sha256"] == source_pin["sha256"]
        and request["bridge_sha256"] == bridge_pin["sha256"]
        and type(request["deadline_ns"]) is int,
        "Fusion quit request differs from its pinned action or deadline",
    )
    raw = protocol["file_bytes"](host.root / f"quit-intent-{identifier}.json")
    record = json.loads(raw)
    ready = record["readiness"]
    grant, consumption = ready["grant"], ready["consumption"]
    require(
        protocol["sha256"](raw) == identifier
        and record["version"] == 1
        and record["scope"] == "external_fusion_exit_watch"
        and record["quit_mode"] == "authorized_cocoa"
        and record["fence_sha256"] == request["fence_sha256"]
        and record["watcher"]["pid"] == request["watcher"]["pid"]
        and ready["intent_sha256"] == request["intent_sha256"]
        and ready["installation_sha256"] == host.installation_sha256
        and ready["status"] == "restart_readiness_observed"
        and ready["documents"] == 0
        and ready["peer"]
        == {
            key: value
            for key, value in request["target"].items()
            if key != "executable"
        }
        and grant["status"] == "granted"
        and consumption["status"] == "consumed"
        and grant["host"] == consumption["host"] == host.host
        and grant["provider"] == consumption["provider"] == host.provider
        and grant["source_sha256"]
        == consumption["source_sha256"]
        == ready["provider_source_sha256"]
        == grant_pin["sha256"]
        and protocol["sha256"](protocol["encoded"](grant)) == ready["grant_sha256"]
        and protocol["sha256"](protocol["encoded"](consumption))
        == ready["consumption_sha256"]
        and consumption["grant_sha256"] == ready["grant_sha256"]
        and grant["expires_at"] == ready["expires_at"]
        and grant["observed_at"]
        <= consumption["observed_at"]
        == ready["observed_at"]
        <= record["armed_at"]
        < ready["expires_at"]
        <= grant["observed_at"] + 20,
        "Fusion quit action requires an armed watch with exact consumed readiness",
    )
    return record


def serve(protocol, grant, capability, host, path, app, main_thread):
    require = protocol["require"]
    require(
        threading.get_ident() == main_thread
        and protocol["macos_automatic_quit"](host.config)
        and path == pending(protocol, host),
        "Fusion quit action requires the pinned macOS main-thread callback",
    )
    raw = protocol["file_bytes"](path)
    restart_digest = path.name.removeprefix("quit-request-").removesuffix(".json")
    files = paths(host.root, restart_digest)
    response = {"version": 1, "request_sha256": protocol["sha256"](raw)}
    bridge = capability["bridge"]
    read_peer = capability["peer"]["process_peer"]
    try:
        request = json.loads(raw)
        require(
            request["intent_sha256"] == restart_digest,
            "Fusion quit request differs from the retained restart intent",
        )
        armed = verify_armed(
            protocol,
            host,
            request,
            capability["_source_pin"],
            grant["_source_pin"],
            bridge["_source_pin"],
        )

        def recheck():
            intent = grant["retained_intent"](protocol, host, request)
            armed_path = host.root / f"quit-intent-{request['quit_intent_sha256']}.json"
            require(
                protocol["file_bytes"](capability["installation"])
                == capability["installation_bytes"]
                and protocol["file_bytes"](path) == raw
                and protocol["sha256"](protocol["file_bytes"](armed_path))
                == request["quit_intent_sha256"]
                and protocol["record"](
                    custody_path(host.root, "hold", request["handoff_id"])
                )
                == hold_record(request)
                and protocol["sha256"](protocol["file_bytes"](host.root / "fence.json"))
                == request["fence_sha256"],
                "Fusion quit action lost its retained owner files",
            )
            verify_lease(protocol, host, request, armed, read_peer)
            require(
                app.version == intent["fusion_version"]
                and app.isStartupComplete is True
                and app.hasActiveJobs is False
                and app.documents.count == 0
                and app.activeDocument is None,
                "Fusion quit action requires the expected idle build and no open documents",
            )

        recheck()
        protocol["write_new"](
            files["attempt"], protocol["encoded"]({**response, "status": "reserved"})
        )
        recheck()
        bridge["request_quit"]()
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
        bridge["QuitUnavailable"],
    ):
        status = "refused"
    else:
        status = "quit_call_returned"
    protocol["write_new"](
        files["action"], protocol["encoded"]({**response, "status": status})
    )
