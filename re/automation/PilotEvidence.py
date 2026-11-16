import argparse
import hashlib
import json
import math
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

from PilotActivity import operating_report
from PilotCiJobs import ci_summary, job_identity
from Records import canonical, label

MAX_BYTES = 1024 * 1024
WINDOW = {
    "from_unix_seconds",
    "until_unix_seconds",
    "after_event_id",
    "through_event_id",
    "selected_events_sha256",
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def checksum(value):
    return isinstance(value, str) and re.fullmatch("[0-9a-f]{64}", value) is not None


def unique_object(pairs):
    value = dict(pairs)
    require(len(value) == len(pairs), "private evidence contains duplicate JSON keys")
    return value


def pinned_record(path, expected):
    require(checksum(expected), "expected an exact evidence SHA-256")
    require(
        path.is_file() and not path.is_symlink(), "expected a regular evidence file"
    )
    with path.open("rb") as source:
        raw = source.read(MAX_BYTES + 1)
    require(len(raw) <= MAX_BYTES, "private evidence exceeds 1 MiB")
    require(
        hashlib.sha256(raw).hexdigest() == expected, "private evidence SHA-256 changed"
    )
    value = json.loads(raw, object_pairs_hook=unique_object)
    require(isinstance(value, dict), "expected a private evidence JSON object")
    return value


def fields(value, expected, reason):
    require(isinstance(value, dict) and set(value) == expected, reason)


def epoch(value):
    require(
        type(value) in (int, float) and math.isfinite(value) and value >= 0,
        "expected a finite nonnegative Unix time",
    )
    return value


def intervention_summary(records, start, end):
    count = 0
    for item in records:
        fields(
            item,
            {"id", "at", "operator", "reason", "evidence_sha256"},
            "invalid intervention attestation",
        )
        label(item["operator"])
        require(
            isinstance(item["reason"], str)
            and 0 < len(item["reason"]) <= 512
            and item["reason"].strip()
            and checksum(item["evidence_sha256"]),
            "intervention requires a reason and evidence SHA-256",
        )
        count += start <= epoch(item["at"]) < end
    return {"status": "attested", "interventions": count}


def union_seconds(intervals):
    total, previous_end = 0, 0
    for left, right in sorted(intervals):
        total += max(0, right - max(left, previous_end))
        previous_end = max(right, previous_end)
    return total


def duration_summary(records, start, end):
    actors = defaultdict(list)
    open_count = 0
    for item in records:
        fields(
            item,
            {"id", "agent", "attempt", "from", "until", "evidence_sha256"},
            "invalid measured agent interval",
        )
        actor = label(item["agent"])
        label(item["attempt"])
        require(
            checksum(item["evidence_sha256"]),
            "agent interval lacks its evidence SHA-256",
        )
        left = epoch(item["from"])
        if item["until"] is None:
            open_count += left < end
            continue
        right = epoch(item["until"])
        require(left < right, "agent interval must increase")
        clipped = max(left, start), min(right, end)
        if clipped[0] < clipped[1]:
            actors[actor].append(clipped)
    if not actors and not open_count:
        return {"status": "unmeasured", "closed_intervals": 0, "open_intervals": 0}
    return {
        "status": "partial" if open_count else "measured",
        "closed_intervals": sum(len(items) for items in actors.values()),
        "open_intervals": open_count,
        "agent_seconds": sum(union_seconds(items) for items in actors.values()),
        "active_wall_seconds": union_seconds(
            interval for items in actors.values() for interval in items
        ),
    }


def acceptance_status(item):
    fields(item, {"status", "receipt_sha256"}, "invalid independent acceptance pin")
    require(
        item["status"] in ("accepted", "not_accepted")
        and checksum(item["receipt_sha256"]),
        "expected an explicit independent acceptance result and receipt SHA-256",
    )
    return item["status"], item["receipt_sha256"]


def acceptance_summary(records, start, end):
    cases, gains = {}, set()
    for item in records:
        fields(
            item,
            {
                "id",
                "at",
                "document_sha256",
                "family",
                "format_version",
                "direction",
                "baseline",
                "candidate",
                "verifier",
            },
            "invalid independent acceptance attestation",
        )
        document = item["document_sha256"]
        require(
            checksum(document), "acceptance must bind a fixed corpus document SHA-256"
        )
        label(item["verifier"])
        case = (
            document,
            label(item["family"]),
            label(item["format_version"]),
            label(item["direction"]),
        )
        baseline, baseline_hash = acceptance_status(item["baseline"])
        candidate, candidate_hash = acceptance_status(item["candidate"])
        require(
            baseline_hash != candidate_hash,
            "acceptance needs distinct baseline and candidate receipts",
        )
        if not start <= epoch(item["at"]) < end:
            continue
        pair = (baseline, baseline_hash, candidate, candidate_hash)
        require(
            cases.setdefault(case, pair) == pair,
            "conflicting independent acceptance attestations",
        )
        if baseline == "not_accepted" and candidate == "accepted":
            gains.add(case)
    return {
        "status": "independently_attested",
        "matched_cases": len(cases),
        "attested_case_gains": len(gains),
        "attested_document_gains": len({case[0] for case in gains}),
    }


SOURCES = {
    "interventions": (
        "Interventions.json",
        "operator_attestation",
        intervention_summary,
    ),
    "agent_activity": (
        "AgentIntervals.json",
        "measured_agent_intervals",
        duration_summary,
    ),
    "acceptance": (
        "Acceptances.json",
        "independent_acceptance_attestation",
        acceptance_summary,
    ),
    "ci_activity": ("CiActivity.json", "github_actions_job_observations", ci_summary),
}


def source_report(root, name, expected, start, end):
    if expected is None:
        return {"status": "unmeasured"}
    filename, authority, summarize = SOURCES[name]
    value = pinned_record(root / filename, expected)
    fields(
        value, {"version", "authority", "records"}, "invalid private evidence source"
    )
    require(
        type(value["version"]) is int
        and value["version"] == 1
        and value["authority"] == authority
        and isinstance(value["records"], list),
        "private evidence source has the wrong version or authority",
    )
    unique = {}
    for item in value["records"]:
        require(isinstance(item, dict), "private evidence records must be JSON objects")
        identifier = job_identity(item) if name == "ci_activity" else label(item["id"])
        require(
            canonical(unique.setdefault(identifier, item)) == canonical(item),
            "conflicting private evidence with the same record ID",
        )
    return {
        "authority": authority,
        "source_sha256": expected,
        **summarize(unique.values(), start, end),
    }


def report(store, path, manifest_hash):
    manifest = pinned_record(path, manifest_hash)
    fields(
        manifest, {"version", "window", "sources"}, "invalid pilot evidence manifest"
    )
    require(
        type(manifest["version"]) is int and manifest["version"] == 1,
        "invalid manifest version",
    )
    window = manifest["window"]
    fields(window, WINDOW, "pilot evidence requires a fixed controller event window")
    start, end = epoch(window["from_unix_seconds"]), epoch(window["until_unix_seconds"])
    require(
        all(type(window[key]) is int for key in ("after_event_id", "through_event_id")),
        "expected both fixed controller event IDs",
    )
    require(
        checksum(window["selected_events_sha256"]),
        "expected an exact controller event SHA-256",
    )
    activity = operating_report(
        store, start, end, window["after_event_id"], window["through_event_id"]
    )
    require(
        all(window[key] == activity[key] for key in WINDOW),
        "controller event evidence differs from the frozen manifest",
    )
    pins = manifest["sources"]
    require(
        isinstance(pins, dict)
        and set(pins) <= set(SOURCES)
        and all(checksum(pin) for pin in pins.values()),
        "expected the exact private source roster and evidence SHA-256s",
    )
    private = {
        name: source_report(path.parent, name, pins.get(name), start, end)
        for name in SOURCES
        if name != "ci_activity" or name in pins
    }
    return {
        "report_version": 1,
        "scope": "pre_pilot_operational_evidence",
        "manifest_sha256": manifest_hash,
        "controller_activity": activity,
        **private,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Read pinned private A15 pre-pilot evidence"
    )
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args()
    try:
        print(canonical(report(args.store, args.manifest, args.manifest_sha256)))
        return 0
    except (
        ValueError,
        OSError,
        KeyError,
        TypeError,
        OverflowError,
        RecursionError,
        sqlite3.Error,
    ) as error:
        print(f"pre-pilot evidence refused ({type(error).__name__})", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
