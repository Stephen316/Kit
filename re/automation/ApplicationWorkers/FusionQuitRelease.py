import json
import os
import re


def bind_replacement(protocol, root, request, request_sha256, executable):
    handoff_id = request["handoff_id"]
    hold_path = root / f"quit-hold-{handoff_id}.json"
    if not os.path.lexists(hold_path):
        return
    hold = protocol["record"](hold_path)
    protocol["require"](
        hold
        == {
            "version": 1,
            "restart_intent_sha256": request["restart_intent_sha256"],
            "fence_sha256": request["fence_sha256"],
        },
        "Fusion automatic quit hold differs from the verified replacement request",
    )
    link = {
        "version": 1,
        "quit_intent_sha256": request["quit_intent_sha256"],
        "launch_request_sha256": request_sha256,
        "executable": os.fspath(executable),
    }
    protocol["write_new"](
        root / f"quit-replacement-{handoff_id}.json", protocol["encoded"](link)
    )


def permits_replacement(protocol, host, fence, read_peer):
    try:
        return matches_replacement(protocol, host, fence, read_peer)
    except (OSError, ValueError, KeyError, AttributeError, TypeError, RecursionError):
        return False


def matches_replacement(protocol, host, fence, read_peer):
    root = host.root
    handoff_id = fence["job_id"]
    if not re.fullmatch("[0-9a-f]{32}", handoff_id):
        return False
    hold = protocol["record"](root / f"quit-hold-{handoff_id}.json")
    link = protocol["record"](root / f"quit-replacement-{handoff_id}.json")
    identifier = link["quit_intent_sha256"]
    if not re.fullmatch("[0-9a-f]{64}", identifier):
        return False
    request_bytes = protocol["file_bytes"](
        root / f"replacement-launch-{identifier}.json"
    )
    request = json.loads(request_bytes)
    launch = protocol["record"](root / f"replacement-peer-{identifier}.json")
    exit_bytes = protocol["file_bytes"](root / f"quit-exit-{identifier}.json")
    exit_record = json.loads(exit_bytes)
    quit_intent = protocol["file_bytes"](root / f"quit-intent-{identifier}.json")
    restart = protocol["file_bytes"](root / f"restart-intent-{handoff_id}.json")
    peer = read_peer(host.host["pid"])
    digest = protocol["sha256"]
    return (
        hold["version"]
        == link["version"]
        == request["version"]
        == launch["version"]
        == exit_record["version"]
        == 1
        and hold["restart_intent_sha256"]
        == digest(restart)
        == request["restart_intent_sha256"]
        == exit_record["restart_intent_sha256"]
        and hold["fence_sha256"]
        == digest(protocol["encoded"](fence))
        == request["fence_sha256"]
        == exit_record["fence_sha256"]
        and request["handoff_id"] == handoff_id
        and request["installation_sha256"] == host.installation_sha256
        and digest(request_bytes)
        == link["launch_request_sha256"]
        == launch["launch_request_sha256"]
        and identifier
        == digest(quit_intent)
        == request["quit_intent_sha256"]
        == launch["quit_intent_sha256"]
        == exit_record["quit_intent_sha256"]
        and digest(exit_bytes)
        == request["quit_exit_sha256"]
        == launch["quit_exit_sha256"]
        and exit_record["scope"] == "external_fusion_exit_observation"
        and exit_record["status"] == "exact_exit_observed"
        and exit_record["observation"] == "darwin_process_exit_event"
        and exit_record["peer"]["pid"] == fence["host"]["pid"] != peer["pid"]
        and request["scope"] == "owner_fusion_replacement_request"
        and launch["scope"] == "owner_fusion_replacement_observation"
        and launch["status"] == "replacement_process_observed"
        and launch["host"] == host.host
        and launch["peer"]
        == {key: value for key, value in peer.items() if key != "executable"}
        and os.fspath(peer["executable"]) == link["executable"]
        and request["requested_at"]
        <= launch["dispatched_at"]
        <= peer["started_unix_microseconds"] / 1_000_000
    )
