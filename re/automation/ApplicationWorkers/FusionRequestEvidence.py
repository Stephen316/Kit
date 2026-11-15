import json
import time

from ApplicationProtocol import (
    check_spool,
    file_bytes,
    pin,
    record,
    require,
    sha256,
    validate_request,
)

ARCHIVE_RECORD = "ProbeArchive.json"
PROBE_FILES = {"cancel.json", "plan.json", "probe.request"}


def match_request(raw, config, timeout, phase):
    queued = json.loads(raw)
    operation = timeout["operation"]
    validate_request(queued, config, timeout["queue_job_id"], operation)
    require(
        sha256(raw) == timeout["request_sha256"]
        and queued["body"]["plan_sha256"] == timeout["plan_sha256"]
        and (operation == "probe" or queued["body"]["phase"] == phase),
        "retained Fusion request bytes do not match the parked request",
    )
    return queued


def probe_archive_record(spool, config, timeout, fence):
    found = {path.name for path in spool.iterdir()}
    require(
        found in (PROBE_FILES, PROBE_FILES | {ARCHIVE_RECORD}),
        "Fusion spool must contain only the untouched Phase A probe and its cancellation",
    )
    check_spool(spool)
    request = match_request(file_bytes(spool / "probe.request"), config, timeout, "a")
    cancel = record(spool / "cancel.json")
    require(
        request["body"] == {"plan_sha256": timeout["plan_sha256"]}
        and sha256(file_bytes(spool / "plan.json")) == timeout["plan_sha256"],
        "Fusion probe does not retain the exact queued plan",
    )
    require(
        set(fence) == {"installation", "job_id", "reason", "host", "at"}
        and fence["installation"] == config["installation"]
        and fence["job_id"] == timeout["queue_job_id"]
        and fence["reason"] == "quarantined"
        and fence["host"] is None
        and set(cancel) == {"reason", "at"}
        and cancel["reason"]
        == "requesting worker stopped before application completion"
        and type(cancel["at"]) in (int, float)
        and type(fence["at"]) in (int, float)
        and request["deadline"] <= cancel["at"] <= fence["at"] <= time.time(),
        "Fusion probe lacks its exact hostless quarantine and expired cancellation",
    )
    manifest = {
        "archive_version": 1,
        "installation": config["installation"],
        "phase": "a",
        "timeout": timeout,
        "fence": fence,
        "files": {name: pin(spool / name, name) for name in sorted(PROBE_FILES)},
    }
    return manifest, request["client"]
