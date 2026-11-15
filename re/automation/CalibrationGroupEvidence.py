import json
import re

from Records import canonical, read_record
from Sessions import write_private
from StoreRead import read_store

GROUP_LIMIT_BYTES = 1048576
GROUP_MAX_MEMBERS = 20
LOG_LIMIT = 4 * 1048576


def grouped_claims(store, manifest, expected):
    specs = {spec["id"]: spec for spec in expected}
    with read_store(store / "ledger.sqlite3", None, (4,)) as db:
        cap = db.execute(
            "SELECT value FROM settings WHERE key='max_running'"
        ).fetchone()[0]
        if cap != GROUP_MAX_MEMBERS:
            raise ValueError("paired trial changed the logical controller limit")
        rows = db.execute(
            "SELECT detail FROM events WHERE action='group_claimed' ORDER BY id LIMIT ?",
            (len(expected) + 1,),
        ).fetchall()
    groups, seen = {}, set()
    for row in rows:
        event = json.loads(row["detail"])
        members = tuple(event["jobs"])
        if (
            event["group_protocol"] != 1
            or not 2 <= len(members) <= GROUP_MAX_MEMBERS
            or len(set(members)) != len(members)
            or seen.intersection(members)
            or not set(members) <= specs.keys()
        ):
            raise ValueError("group claim membership differs from the immutable jobs")
        footprint = sum(
            len(canonical(specs[job]).encode("utf-8"))
            + manifest["bindings"][specs[job]["inputs"]["source"]]["size_bytes"]
            for job in members
        )
        if footprint != event["input_bytes"] or footprint >= GROUP_LIMIT_BYTES:
            raise ValueError(
                "group claim footprint differs from the bounded definition and input bytes"
            )
        groups[members] = footprint
        seen.update(members)
    return groups


def observed_starts(directory, expected_count):
    with (directory / "stdout.log").open("rb") as source:
        content = source.read(LOG_LIMIT + 1)
    if len(content) > LOG_LIMIT:
        raise ValueError("paired supervisor log exceeds the calibration limit")
    starts = {}
    for raw in content.splitlines():
        event = json.loads(raw)
        if event.get("event") != "started":
            continue
        session = event["session"]
        if session in starts or len(starts) >= expected_count:
            raise ValueError(
                "paired supervisor reported duplicate or excess physical launches"
            )
        starts[session] = (event["pid"], event["group_size"], event["job"])
    return starts


def session_observations(directory, records, claims, windows):
    starts = observed_starts(directory, len(records))
    by_session = {}
    for row in records:
        by_session.setdefault(row["session"], []).append(row)
    if set(by_session) != starts.keys():
        raise ValueError("accepted receipts and launched physical sessions differ")
    groups, seen_groups, identities = [], set(), set()
    for session, rows in sorted(by_session.items()):
        rows.sort(key=lambda row: row["measurement"]["decode_started_ns"])
        member_ids = tuple(row["id"] for row in rows)
        pid, size, first_job = starts[session]
        identity = (pid, rows[0]["process_start"])
        if (
            not re.fullmatch(r"[a-f0-9]+-[a-f0-9]+", session)
            or type(pid) is not int
            or pid <= 1
            or not identity[1]
            or identity in identities
            or size != len(rows)
            or first_job != member_ids[0]
            or any(
                (row["pid"], row["process_start"], row["group_size"])
                != (*identity, size)
                for row in rows
            )
            or any(
                left["measurement"]["decode_ended_ns"]
                > right["measurement"]["decode_started_ns"]
                for left, right in zip(rows, rows[1:])
            )
        ):
            raise ValueError("paired physical session identity or member order differs")
        identities.add(identity)
        footprint = None
        if size > 1:
            if member_ids not in claims:
                raise ValueError("accepted group is missing its ordered A03 claim")
            seen_groups.add(member_ids)
            footprint = claims[member_ids]
        last = rows[-1]
        measurement = last["measurement"]
        peak = (
            measurement.get("worker_peak_working_set_bytes")
            if windows
            else last["peak_memory_bytes"]
        )
        groups.append(
            {
                "session": session,
                "pid": pid,
                "process_start": identity[1],
                "members": list(member_ids),
                "input_footprint_bytes": footprint,
                "process_cpu_seconds_observed": measurement["process_user_cpu_seconds"]
                + measurement["process_system_cpu_seconds"],
                "process_peak_rss_bytes": peak,
                "sampled_group_peak_memory_bytes": last[
                    "sampled_group_peak_memory_bytes"
                ],
            }
        )
    if seen_groups != claims.keys():
        raise ValueError("A03 claimed groups that lack matching accepted members")
    return groups


def observe(directory, manifest, expected, grouped, trial):
    result = {
        "mode": "grouped" if grouped else "singleton",
        "physical_sessions": 0,
        "multi_member_sessions": 0,
        "grouped_members": 0,
        "group_receipts_verified": False,
        "physical_process_cpu_seconds_observed": None,
        "cpu_measurements": 0,
        "cpu_measurements_complete": False,
        "rss_measurements_complete": False,
        "peak_worker_or_group_rss_bytes": None,
    }
    if not trial["execution_completed"]:
        return result
    cleanup = read_record(directory / "Cleanup.json")
    windows = trial["source_identity"]["host_topology"]["memory_source"].startswith(
        "windows:"
    )
    if (
        cleanup["supervisor_exit"] != 0
        or cleanup["forced_groups"]
        or cleanup["sessions_empty"] is not True
        or cleanup["claims_empty"] is not True
        or (windows and cleanup.get("job_members_empty") is not True)
    ):
        raise ValueError("paired trial lacks clean supervisor and worker cleanup")
    claims = grouped_claims(directory / "Controller", manifest, expected)
    sessions = session_observations(directory, trial["jobs"], claims, windows)
    sizes = [len(row["members"]) for row in sessions if len(row["members"]) > 1]
    if sizes and not grouped:
        raise ValueError("the singleton control unexpectedly grouped archives")
    complete = trial["complete"] and (bool(sizes) if grouped else True)
    reasons = trial["incomplete_reasons"] + (
        ["no_grouped_archive_session"] if grouped and not sizes else []
    )
    write_rows = {"group_evidence_version": 1, "sessions": sessions}
    write_private(directory / "PhysicalSessions.json", write_rows)
    peaks = [
        row[key]
        for row in sessions
        for key in ("process_peak_rss_bytes", "sampled_group_peak_memory_bytes")
        if type(row[key]) is int and row[key] > 0
    ]
    return {
        **result,
        "complete": complete,
        "incomplete_reasons": reasons,
        "physical_sessions": len(sessions),
        "multi_member_sessions": len(sizes),
        "grouped_members": sum(sizes),
        "group_receipts_verified": True,
        "physical_process_cpu_seconds_observed": sum(
            row["process_cpu_seconds_observed"] for row in sessions
        ),
        "cpu_measurements": len(sessions),
        "cpu_measurements_complete": trial["cpu_measurements_complete"],
        "rss_measurements_complete": trial["rss_measurements_complete"],
        "peak_worker_or_group_rss_bytes": max(peaks, default=None),
    }


def compare(trials):
    result = {
        "previous": "singleton",
        "current": "grouped",
        "comparable": False,
        "gain": None,
    }
    if len(trials) != 2:
        return result
    singleton, grouped = trials
    left, right = (trial["source_identity"] for trial in trials)
    comparable = (
        singleton["complete"]
        and grouped["complete"]
        and {key: value for key, value in left.items() if key != "registry_sha256"}
        == {key: value for key, value in right.items() if key != "registry_sha256"}
        and singleton["decoded_outputs_sha256"] == grouped["decoded_outputs_sha256"]
    )
    if comparable:
        result["comparable"] = True
        result["gain"] = (
            grouped["completed_jobs_per_minute"]
            / singleton["completed_jobs_per_minute"]
            - 1
        )
    return result
