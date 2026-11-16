import json
import math
import sqlite3
import time
from pathlib import Path

from Artifacts import Artifacts
from Records import digest, label, read_record, specification
from StoreRead import read_store


def capture_window(store, resource, start, end):
    database = store / "ledger.sqlite3"
    if database.is_symlink() or not database.is_file():
        raise ValueError("claim occupancy requires an initialized A03 store")
    if end > time.time():
        raise ValueError("claim occupancy window ends after the observation")
    try:
        with read_store(database, None, (4,)) as connection:
            row = connection.execute(
                "SELECT capacity,available FROM resources WHERE name=?",
                (resource,),
            ).fetchone()
            if row is None or row["capacity"] != 1:
                raise ValueError(
                    "claim occupancy requires a stored capacity-one resource"
                )
            attempts = connection.execute(
                "SELECT a.id,a.job_id,a.generation,a.number,a.fingerprint,a.started,a.ended,a.receipt,"
                "j.state AS current_state,j.snapshot AS current_snapshot,j.generation AS current_generation,"
                "j.attempts AS current_number,j.fingerprint AS current_fingerprint "
                "FROM attempts AS a LEFT JOIN jobs AS j ON j.active_attempt=a.id AND j.id=a.job_id "
                "WHERE a.started<? AND (a.ended IS NULL OR a.ended>?) ORDER BY a.started,a.id",
                (end, start),
            ).fetchall()
    except sqlite3.Error as error:
        raise OSError("could not read the A03 occupancy snapshot") from error
    return bool(row["available"]), attempts


def stored_record(objects, checksum):
    objects.verify(checksum)
    value = read_record(objects.path(checksum))
    if digest(value) != checksum:
        raise ValueError("stored claim evidence differs from its content identity")
    return value


def attempt_snapshot(objects, attempt):
    if attempt["ended"] is None:
        if (
            attempt["current_state"] != "running"
            or attempt["current_generation"] != attempt["generation"]
            or attempt["current_number"] != attempt["number"]
            or attempt["current_fingerprint"] != attempt["fingerprint"]
        ):
            raise ValueError("an open claim lacks its current controller snapshot")
        snapshot = json.loads(attempt["current_snapshot"])
    else:
        return closed_attempt_receipt(objects, attempt)["snapshot"]
    if digest(snapshot) != attempt["fingerprint"]:
        raise ValueError("claim occupancy snapshot fingerprint differs")
    return snapshot


def closed_attempt_receipt(objects, attempt):
    receipt = stored_record(objects, attempt["receipt"])
    expected = {
        "receipt_version": 1,
        "job_id": attempt["job_id"],
        "generation": attempt["generation"],
        "attempt": attempt["number"],
        "execution_id": attempt["id"],
        "fingerprint": attempt["fingerprint"],
    }
    if not all(receipt[key] == value for key, value in expected.items()):
        raise ValueError("a closed claim receipt does not match its historical attempt")
    if not attempt["started"] <= receipt["finished_at"] <= attempt["ended"]:
        raise ValueError("a closed claim receipt has an inconsistent completion time")
    if digest(receipt["snapshot"]) != attempt["fingerprint"]:
        raise ValueError("claim occupancy snapshot fingerprint differs")
    return receipt


def claim_intervals(objects, attempts, resource, start, end):
    definitions = {}
    intervals = []
    open_claims = 0
    for attempt in attempts:
        snapshot = attempt_snapshot(objects, attempt)
        definition = snapshot["definition_hash"]
        if definition not in definitions:
            spec = specification(stored_record(objects, definition))
            if digest(spec) != definition:
                raise ValueError(
                    "historical claim definition differs from its content identity"
                )
            definitions[definition] = spec
        spec = definitions[definition]
        if spec["id"] != attempt["job_id"]:
            raise ValueError("historical claim definition belongs to another job")
        if resource not in spec["resources"]:
            continue
        left, right = attempt["started"], attempt["ended"]
        if not math.isfinite(left) or (
            right is not None and (not math.isfinite(right) or right < left)
        ):
            raise ValueError("recorded claim times have an invalid interval")
        intervals.append((max(left, start), end if right is None else min(right, end)))
        open_claims += right is None
    return intervals, open_claims


def union_seconds(intervals, start):
    occupied, covered_until = 0.0, start
    for left, right in intervals:
        if right > covered_until:
            occupied += right - max(left, covered_until)
            covered_until = right
    return occupied


def claim_occupancy(config, resource, start, end):
    resource = label(resource)
    controller = config["controller"]
    if controller.get("adapter") != "a03" or config["resources"].get(resource) != 1:
        raise ValueError(
            "claim occupancy requires a configured capacity-one A03 resource"
        )
    if not (0 <= start < end and math.isfinite(end)):
        raise ValueError("claim occupancy requires increasing nonnegative Unix seconds")
    store = Path(controller["store"])
    available, attempts = capture_window(store, resource, start, end)
    objects = Artifacts(store, create=False)
    intervals, open_claims = claim_intervals(objects, attempts, resource, start, end)
    elapsed = end - start
    occupied = min(elapsed, union_seconds(intervals, start))
    return {
        "resource": resource,
        "scope": "a03_recorded_claim_occupancy",
        "from_unix_seconds": start,
        "until_unix_seconds": end,
        "window_seconds": elapsed,
        "occupied_seconds": occupied,
        "occupancy": occupied / elapsed,
        "recorded_closed_claims": len(intervals) - open_claims,
        "recorded_open_claims": open_claims,
        "resource_available_at_observation": available,
    }
