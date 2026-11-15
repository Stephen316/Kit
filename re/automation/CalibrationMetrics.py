import hashlib
import math

from Artifacts import Artifacts
from Records import canonical, read_record

PLATEAU_SECONDS = 1.0


def overlap(intervals, requested):
    events = {}
    for started, ended in intervals:
        if type(started) is not int or type(ended) is not int or ended <= started:
            raise ValueError("decoder interval is invalid")
        events[started] = events.get(started, 0) + 1
        events[ended] = events.get(ended, 0) - 1
    active, peak, longest = 0, 0, 0
    previous, plateau = None, None
    for instant, delta in sorted(events.items()):
        if previous is not None and active >= requested:
            plateau = previous if plateau is None else plateau
            longest = max(longest, instant - plateau)
        else:
            plateau = None
        active += delta
        peak = max(peak, active)
        previous = instant
    return peak, longest / 1e9


def jobs(adapter, store, expected):
    rows, after = [], None
    while True:
        page = adapter.ReadStatus(after=after)
        rows.extend(page["jobs"])
        after = page["next_after"]
        if after is None:
            break
    if {row["id"] for row in rows} != {job["id"] for job in expected}:
        raise ValueError(
            "private calibration store differs from the explicit job manifest"
        )
    objects = Artifacts(store)
    records = []
    for row in rows:
        payload = {}
        if row["result"] is not None:
            objects.verify(row["result"])
            payload = read_record(objects.path(row["result"]))
        receipt = payload.get("receipt") or {}
        declared = payload.get("result") or {}
        measurement = declared.get("records")
        records.append(
            {
                "id": row["id"],
                "state": row["state"],
                "attempts": row["attempts"],
                "result_sha256": row["result"],
                "receipt_sha256": row["receipt"],
                "peak_memory_bytes": receipt.get("peak_memory_bytes"),
                "sampled_group_peak_memory_bytes": receipt.get(
                    "sampled_group_peak_memory_bytes"
                ),
                "pid": receipt.get("pid"),
                "process_start": receipt.get("process_start"),
                "exit_status": receipt.get("exit_status"),
                "signal": receipt.get("signal"),
                "stop_reason": receipt.get("stop_reason"),
                "measurement": measurement,
            }
        )
    return records


def summarize(requested, manifest, expected, records, wall, reason, limited, identity):
    intervals, decoded, memory, cpu = [], {}, [], 0.0
    cpu_count, rss_count = 0, 0
    for entry in records:
        if type(entry["peak_memory_bytes"]) is int and entry["peak_memory_bytes"] > 0:
            rss_count += 1
        for key in ("peak_memory_bytes", "sampled_group_peak_memory_bytes"):
            value = entry[key]
            if type(value) is int and value >= 0:
                memory.append(value)
        measurement = entry["measurement"]
        if measurement is None:
            continue
        job = next(value for value in expected if value["id"] == entry["id"])
        source = manifest["bindings"][job["inputs"]["source"]]["sha256"]
        if (
            measurement["job_id"] != entry["id"]
            or measurement["kind"] != manifest["kind"]
            or measurement["input_sha256"] != source
        ):
            raise ValueError(
                "worker measurement does not match its immutable input job"
            )
        intervals.append(
            (measurement["decode_started_ns"], measurement["decode_ended_ns"])
        )
        for key in (
            "decode_wall_seconds",
            "decode_cpu_seconds",
            "process_user_cpu_seconds",
            "process_system_cpu_seconds",
        ):
            value = measurement[key]
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError("worker CPU or wall-time measurement is invalid")
        if (
            measurement["decode_cpu_seconds"]
            > manifest["runner"]["threads"] * measurement["decode_wall_seconds"] * 1.05
            + 0.02
        ):
            limited = [*limited, "declared_thread_budget_exceeded"]
        cpu += (
            measurement["process_user_cpu_seconds"]
            + measurement["process_system_cpu_seconds"]
        )
        cpu_count += 1
        if (
            entry["state"] == "completed"
            and entry["attempts"] == 1
            and entry["exit_status"] == 0
            and entry["stop_reason"] is None
            and measurement["neutral_sha256"] is not None
        ):
            decoded[entry["id"]] = measurement["neutral_sha256"]
    peak, plateau = overlap(intervals, requested)
    successful = len(decoded) == len(expected)
    metrics_complete = cpu_count == len(expected) and rss_count == len(expected)
    complete = (
        successful
        and metrics_complete
        and reason is None
        and not limited
        and peak == requested
        and plateau >= PLATEAU_SECONDS
    )
    problems = list(limited)
    if reason is not None:
        problems.append(reason)
    if not successful:
        problems.append("not_all_jobs_completed_once")
    if not metrics_complete:
        problems.append("physical_resource_measurements_incomplete")
    if peak != requested or plateau < PLATEAU_SECONDS:
        problems.append("requested_decode_overlap_not_sustained")
    return {
        "trial_version": 1,
        "requested_concurrency": requested,
        "observed_peak_decode_concurrency": peak,
        "longest_requested_overlap_seconds": plateau,
        "declared_plateau_threshold_seconds": PLATEAU_SECONDS,
        "complete": complete,
        "execution_completed": successful,
        "incomplete_reasons": sorted(set(problems)),
        "completed_jobs": len(decoded),
        "expected_jobs": len(expected),
        "wall_seconds": wall,
        "completed_jobs_per_minute": len(decoded) * 60 / wall if wall > 0 else None,
        "physical_process_cpu_seconds_observed": cpu,
        "cpu_measurements": cpu_count,
        "cpu_measurements_complete": cpu_count == len(expected),
        "peak_worker_or_group_rss_bytes": max(memory, default=None),
        "rss_measurements_complete": rss_count == len(expected),
        "decoded_outputs_sha256": (
            hashlib.sha256(canonical(decoded).encode()).hexdigest()
            if successful
            else None
        ),
        "source_identity": identity,
        "jobs": records,
    }


def recommendation(trials):
    comparisons = []
    for previous, current in zip(trials, trials[1:]):
        comparable = (
            previous["complete"]
            and current["complete"]
            and previous["source_identity"] == current["source_identity"]
            and previous["decoded_outputs_sha256"] == current["decoded_outputs_sha256"]
        )
        if not comparable:
            comparisons.append(
                {
                    "previous": previous["requested_concurrency"],
                    "current": current["requested_concurrency"],
                    "comparable": False,
                    "gain": None,
                }
            )
            continue
        gain = (
            current["completed_jobs_per_minute"] / previous["completed_jobs_per_minute"]
            - 1
        )
        comparisons.append(
            {
                "previous": previous["requested_concurrency"],
                "current": current["requested_concurrency"],
                "comparable": True,
                "gain": gain,
            }
        )
        if gain < 0.10:
            return previous["requested_concurrency"], comparisons
    return None, comparisons
