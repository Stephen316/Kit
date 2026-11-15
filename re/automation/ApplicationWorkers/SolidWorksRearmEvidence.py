"""Verify archived Windows SOLIDWORKS timeout rearm evidence after listener exit."""

import argparse
import json
import math
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sys

from ApplicationProtocol import (
    MAX_BYTES,
    directory,
    encoded,
    file_bytes,
    request_link,
    require,
    sha256,
)
from SolidWorksReadbackWorker import BUILD, OPERATION, PRINCIPAL, PROVIDER, phase_request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from Artifacts import Artifacts
from Records import canonical, digest, specification

SPOOL_RECORDS = (
    "native-timeout-request.json",
    "phase.done",
    "native-recovery.json",
    "readback/native-launch.json",
    "readback/native-owner.json",
)
JSON_LIMIT = 1024 * 1024


def matches(left, right, *keys):
    return all(left[key] == right[key] for key in keys)


def checksum(value):
    require(
        isinstance(value, str) and re.fullmatch("[0-9a-f]{64}", value), "invalid SHA-256 pin"
    )
    return value


def checked_bytes(path, pin, limit=JSON_LIMIT):
    data = file_bytes(path, limit)
    require(sha256(data) == checksum(pin), "retained evidence differs from its SHA-256 pin")
    return data


def document(content):
    value = json.loads(content)
    require(isinstance(value, dict), "evidence must contain a JSON object")
    return value


def artifact(store, pin):
    return document(checked_bytes(store.path(pin), pin))


def windows_identity(value):
    return (
        isinstance(value, dict)
        and set(value) == {"pid", "started"}
        and type(value["pid"]) is int
        and value["pid"] > 0
        and isinstance(value["started"], str)
        and re.fullmatch("windows:[0-9]+", value["started"])
    )


def attempt(store, receipt_pin):
    receipt = artifact(store, receipt_pin)
    envelope = artifact(store, receipt["result_sha256"])
    snapshot = receipt["snapshot"]
    spec = specification(artifact(store, snapshot["definition_hash"]))
    result, runner = envelope["result"], envelope["receipt"]
    records = result["records"]
    timeout = records["queue_timeout"]
    scope = spec["options"].get("readback_operation", OPERATION)
    options = {"source_revision": timeout["source_revision"]}
    if scope == PRINCIPAL:
        options["readback_operation"] = scope
    require(
        receipt["receipt_version"]
        == envelope["session_version"]
        == runner["receipt_version"]
        == timeout["version"]
        == 1
        and receipt["outcome"] == result["outcome"] == "waiting_application"
        and records["application"] == "solidworks"
        and records["claim"] == "unqualified_dispatch"
        and records["native_qualified"] is False
        and digest(spec) == snapshot["definition_hash"]
        and digest(snapshot) == receipt["fingerprint"]
        and matches(timeout, receipt, "job_id", "generation", "fingerprint", "attempt")
        and matches(timeout, runner, "job_id", "kind", "session", "attempt")
        and timeout["job_id"] == spec["id"]
        and timeout["kind"] == spec["kind"]
        and timeout["installation"] == records["installation"]
        and spec["inputs"] == {}
        and timeout["resources"] == spec["resources"]
        and len(spec["resources"]) == 1
        and scope in (OPERATION, PRINCIPAL)
        and spec["options"] == options
        and re.fullmatch("[0-9a-f]{40}", timeout["source_revision"])
        and re.fullmatch("[0-9a-f]{32}", timeout["queue_job_id"])
        and re.fullmatch("[0-9a-f]{48}", timeout["nonce"])
        and windows_identity(timeout["client"])
        and windows_identity({"pid": runner["pid"], "started": runner["process_start"]})
        and runner["orphan"] is False
        and runner["stop_reason"] is None
        and runner["exit_status"] == 0
        and runner["signal"] is None
        and "output_artifacts" not in envelope
        and "artifacts" not in result,
        "A03 receipt, result and exact Windows timeout do not agree",
    )
    checksum(timeout["request_sha256"])
    return receipt, envelope, timeout, spec


def spool_evidence(read, timeout, scope):
    request_raw, done_raw, recovery_raw, launch_raw, ticket_raw = map(read, SPOOL_RECORDS)
    request, terminal, recovery, launch, ticket = map(
        document, (request_raw, done_raw, recovery_raw, launch_raw, ticket_raw)
    )
    require(
        request["version"] == 1
        and request["operation"] == "phase"
        and request["body"] == phase_request(timeout, scope)
        and request_raw == encoded(request)
        and all(timeout[key] == value for key, value in request_link(request).items())
        and matches(timeout, request, "installation", "source_revision")
        and type(request["deadline"]) in (int, float)
        and math.isfinite(request["deadline"])
        and request["deadline"] > 0
        and terminal["version"] == 1
        and terminal["status"] == "expired"
        and terminal["provider"] == PROVIDER
        and terminal["files"] == {}
        and terminal["proof"] is None
        and terminal["finished_at"] >= request["deadline"]
        and matches(
            timeout, terminal, "installation", "source_revision", "request_sha256", "nonce"
        )
        and recovery["version"] == 2
        and recovery["trigger"] == "collector_timeout"
        and recovery["status"] in ("already_exited", "terminated_owned_process")
        and matches(
            timeout,
            recovery,
            "queue_job_id",
            "request_sha256",
            "nonce",
            "client",
            "installation",
            "source_revision",
        )
        and windows_identity(recovery["listener"])
        and recovery["listener"] == terminal["host"]
        and launch["version"] == 1
        and matches(recovery, launch, "request_sha256", "source_revision", "pid", "created")
        and windows_identity({"pid": launch["pid"], "started": launch["created"]})
        and type(launch["session"]) is int
        and launch["session"] >= 0
        and PureWindowsPath(launch["image"]).is_absolute()
        and PureWindowsPath(launch["image"]).name.lower() == "sldworks.exe"
        and ticket == {**launch, "build": BUILD, "initial_documents": 0}
        and sha256(encoded(ticket)) == recovery["owner_ticket_sha256"],
        "terminal request, owned process ticket and listener disposition do not agree",
    )
    return recovery, launch


def archived_spool(store, manifest):
    files = manifest["files"]
    require(
        0 < len(files) <= 256 and set(SPOOL_RECORDS) <= files.keys(),
        "incomplete archive roster",
    )
    total = 0
    for name, item in files.items():
        path = PurePosixPath(name)
        require(
            not path.is_absolute()
            and path.parts
            and ".." not in path.parts
            and path.as_posix() == name
            and "\\" not in name
            and set(item) == {"sha256", "size_bytes"}
            and type(item["size_bytes"]) is int
            and item["size_bytes"] >= 0,
            "invalid archived file entry",
        )
        total += item["size_bytes"]
        require(total <= MAX_BYTES, "archived spool exceeds the byte limit")
        pin = checksum(item["sha256"])
        require(
            store.verify(pin) == item["size_bytes"], "archived file differs from its size pin"
        )

    def read(name):
        pin = files[name]["sha256"]
        return checked_bytes(store.path(pin), pin)

    return read


def retained_history(
    root, pins, first, second, manifest, manifest_pin, timeout, recovery, launch, scope
):
    require(
        set(pins)
        == {"schema", "events_sha256", "supervisor_sha256", "fence_sha256", "second_files"}
        and pins["schema"] == 1
        and set(pins["second_files"]) == set(SPOOL_RECORDS),
        "retained history requires exact pins for events, supervisor, fence and second spool",
    )
    endpoint = directory(root / "endpoint")
    spool = directory(endpoint / "jobs" / timeout["queue_job_id"])
    second_recovery, second_launch = spool_evidence(
        lambda name: checked_bytes(spool / name, pins["second_files"][name]), timeout, scope
    )
    fence = document(checked_bytes(endpoint / "fence.json", pins["fence_sha256"]))
    require(
        fence["reason"] == "quarantined"
        and fence["job_id"] == timeout["queue_job_id"]
        and fence["installation"] == timeout["installation"]
        and fence["host"] in (None, second_recovery["listener"]),
        "retained quarantine does not identify the second request",
    )
    events = document(checked_bytes(root / "ControllerEvents.json", pins["events_sha256"]))[
        "events"
    ]
    log = (
        checked_bytes(root / "supervisor.stdout", pins["supervisor_sha256"])
        .decode("utf-8-sig")
        .splitlines()
    )
    job = first["job_id"]
    claims = sorted(
        (event for event in events if event["job_id"] == job and event["action"] == "claimed"),
        key=lambda event: event["id"],
    )
    (rearm,) = [
        event
        for event in events
        if event["job_id"] == job and event["action"] == "application_timeout_rearmed"
    ]
    (marker,) = [
        row
        for row in map(document, (line for line in log if line.startswith("{")))
        if row.get("event") == "application_rearm" and row.get("job") == job
    ]
    rearm_detail = document(rearm["detail"])
    recovered = marker.get("recovered")
    holds = [
        (event["id"], document(event["detail"]))
        for event in events
        if event["job_id"] == job and event["action"] == "application_timeout_hold"
    ]
    require(len(holds) == 2, "retained history must contain the two exact held attempts")
    hold_receipts = {detail["receipt"]: (event_id, detail) for event_id, detail in holds}
    first_hold, first_detail = hold_receipts[first["receipt_sha256"]]
    second_hold, second_detail = hold_receipts[second["receipt_sha256"]]
    for detail, receipt in ((first_detail, first), (second_detail, second)):
        require(
            matches(detail, receipt, "attempt", "generation", "fingerprint", "execution_id")
            and detail["result"] == receipt["result_sha256"]
            and detail["resource"] == manifest["resource"],
            "retained hold differs from its accepted A03 receipt",
        )
    require(
        len(claims) == 2
        and [json.loads(row["detail"])["attempt"] for row in claims] == [1, 2]
        and claims[0]["id"] < first_hold < rearm["id"] < claims[1]["id"] < second_hold
        and first_detail["epoch"] == manifest["epoch"] < second_detail["epoch"]
        and rearm_detail["archive"] == marker["archive"] == manifest_pin
        and matches(rearm_detail, manifest, "receipt", "result", "epoch", "resource")
        and marker["attempt"] == 1
        and marker["session"] == manifest["claim"]["session"]
        and marker["status"] == "rearmed"
        and (
            type(recovered) is bool
            or ("recovered" not in marker and "version" not in manifest["claim"])
        ),
        "retained history does not bind the rearm between the two accepted requests",
    )
    rotations = [
        event
        for event in events
        if event["action"] == "supervisor_owner_rotated"
        and first_hold < event["id"] < rearm["id"]
    ]
    require(
        bool(rotations) == bool(recovered),
        "owner history does not corroborate the restart marker",
    )
    return {
        "status": "verified",
        "replacement_supervisor_replayed": recovered,
        "same_listener": recovery["listener"] == second_recovery["listener"],
        "distinct_native_processes": (launch["pid"], launch["created"])
        != (second_launch["pid"], second_launch["created"]),
        "same_native_desktop_session": launch["session"] == second_launch["session"],
        "second_quarantine_retained": True,
        "second_native_exit": second_recovery["status"],
        "second_owner_ticket_sha256": second_recovery["owner_ticket_sha256"],
    }


def verify(store_path, manifest_pin, first_pin, second_pin, history=None):
    store = Artifacts(directory(store_path), create=False)
    manifest = artifact(store, manifest_pin)
    require(
        manifest["version"] == 1 and manifest["receipt"] == first_pin,
        "archive belongs to a different first attempt receipt",
    )
    first, envelope, timeout, spec = attempt(store, first_pin)
    second, _, retry, retry_spec = attempt(store, second_pin)
    claim = manifest["claim"]
    require(
        first["attempt"] == 1
        and second["attempt"] == spec["max_attempts"] == 2
        and first["execution_id"] != second["execution_id"]
        and first["snapshot"] == second["snapshot"]
        and spec == retry_spec
        and matches(first, second, "job_id", "generation", "fingerprint")
        and matches(timeout, retry, "installation", "source_revision", "resources")
        and all(
            timeout[key] != retry[key]
            for key in ("queue_job_id", "request_sha256", "nonce", "client")
        )
        and manifest["result"] == first["result_sha256"]
        and manifest["resource"] == spec["resources"][0]
        and matches(manifest, timeout, "request_sha256", "queue_job_id")
        and matches(
            claim, timeout, "job_id", "generation", "fingerprint", "attempt", "session"
        ),
        "archive and receipts do not identify one exhausted Windows rearm sequence",
    )
    if claim.get("version") == 1:
        require(
            matches(claim, timeout, "kind")
            and claim["queue_timeout_sha256"] == digest(timeout)
            and envelope["application_rearm_intent_sha256"] == digest(claim),
            "immutable result does not bind the archived rearm intent",
        )
    else:
        require(
            "version" not in claim and "application_rearm_intent_sha256" not in envelope,
            "unsupported archived rearm intent",
        )
    scope = spec["options"].get("readback_operation", OPERATION)
    recovery, launch = spool_evidence(archived_spool(store, manifest), timeout, scope)
    archived_fence = manifest["fence"]
    require(
        archived_fence is None
        or (
            archived_fence["reason"] == "quarantined"
            and archived_fence["job_id"] == timeout["queue_job_id"]
            and archived_fence["installation"] == timeout["installation"]
            and archived_fence["host"] in (None, recovery["listener"])
        ),
        "archived quarantine differs from the first request",
    )
    extra = {"status": "not_supplied"}
    if history is not None:
        root, pins = history
        extra = retained_history(
            root,
            pins,
            {**first, "receipt_sha256": first_pin},
            {**second, "receipt_sha256": second_pin},
            manifest,
            manifest_pin,
            retry,
            recovery,
            launch,
            scope,
        )
    return {
        "schema": 1,
        "claim": "archived_solidworks_timeout_rearm",
        "native_qualified": False,
        "source_revision": timeout["source_revision"],
        "readback_scope": scope,
        "manifest_sha256": manifest_pin,
        "first_receipt_sha256": first_pin,
        "second_receipt_sha256": second_pin,
        "first_result_sha256": first["result_sha256"],
        "second_result_sha256": second["result_sha256"],
        "definition_sha256": first["snapshot"]["definition_hash"],
        "fingerprint": first["fingerprint"],
        "archived_files": len(manifest["files"]),
        "intent_version": claim.get("version"),
        "first_native_exit": recovery["status"],
        "first_owner_ticket_sha256": recovery["owner_ticket_sha256"],
        "distinct_queue_requests": True,
        "max_attempts": spec["max_attempts"],
        "retained_history": extra,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True)
    for role in ("manifest", "first-receipt", "second-receipt"):
        parser.add_argument(f"--{role}-sha256", required=True)
    parser.add_argument("--history-root", type=Path)
    parser.add_argument("--history-pins", type=Path)
    parser.add_argument("--history-pins-sha256")
    args = parser.parse_args()
    try:
        optional = (args.history_root, args.history_pins, args.history_pins_sha256)
        require(
            all(optional) or not any(optional),
            "supply all three optional history arguments together",
        )
        history = None
        if all(optional):
            history = (
                directory(args.history_root),
                document(checked_bytes(args.history_pins, args.history_pins_sha256)),
            )
        result = verify(
            args.store,
            args.manifest_sha256,
            args.first_receipt_sha256,
            args.second_receipt_sha256,
            history,
        )
        if history is not None:
            result["retained_history"]["pins_sha256"] = args.history_pins_sha256
        sys.stdout.buffer.write((canonical(result) + "\n").encode("utf-8"))
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as error:
        parser.exit(1, f"offline SOLIDWORKS rearm evidence refused: {error}\n")


if __name__ == "__main__":
    main()
