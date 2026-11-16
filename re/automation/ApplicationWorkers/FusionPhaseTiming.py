# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import math
import time

from ApplicationProtocol import require
from ResourceOccupancy import union_seconds


# unusual recorded numbers must be rejected before comparing native and controller clocks
def is_timestamp(value):
    return type(value) in (int, float) and 0 <= value < math.inf


# missing historical phase clocks stay visible without estimating them from claim timestamps
def phase_timing(database, row, controller, dispatch, observed, plan):
    proof = dispatch["proof"]
    if proof.get("fixture_only") is True or observed.get("fixture_only") is True:
        return {"status": "fixture"}
    if "started_unix_seconds" not in observed:
        return {"status": "unmeasured"}
    start = observed["started_unix_seconds"]
    end = observed["ended_unix_seconds"]
    attempt = database.execute(
        "SELECT started,ended,receipt FROM attempts WHERE id=?",
        (controller["execution_id"],),
    ).fetchone()
    require(
        attempt is not None
        and attempt["receipt"] == row["receipt"]
        and all(
            is_timestamp(value)
            for value in (
                start,
                end,
                attempt["started"],
                attempt["ended"],
                dispatch["finished_at"],
                controller["finished_at"],
            )
        )
        and observed["process"]["start_unix_seconds"] <= start
        and attempt["started"]
        <= start
        < end
        <= dispatch["finished_at"]
        <= controller["finished_at"]
        <= attempt["ended"]
        and observed["pins"] == plan["pins"]
        and all(
            observed[control]["compute_all_return"] is True
            and observed[control]["native_input"] == plan["pins"]["control"]
            for control in ("healthy_control_before", "healthy_control_after")
        ),
        "Fusion phase timing differs from its process, accepted attempt or pinned controls",
    )
    return {"status": "measured", "start_unix_seconds": start, "end_unix_seconds": end}


# a fixed window bounds the observed fraction without asserting complete application telemetry
def busy_window(phases, start, end):
    counts = {"measured": 0, "unmeasured": 0, "fixture": 0, "uncompleted": 0}
    intervals = []
    for phase in phases.values():
        timing = phase.get("evidence", {}).get(
            "native_timing", {"status": "uncompleted"}
        )
        status = timing["status"]
        counts[status] += 1
        if status == "measured":
            left = max(start, timing["start_unix_seconds"])
            right = min(end, timing["end_unix_seconds"])
            if left < right:
                intervals.append((left, right))
    elapsed = end - start
    busy = min(elapsed, union_seconds(sorted(intervals), start))
    return {
        "scope": "accepted_fusion_phase_main_thread_intervals",
        "from_unix_seconds": start,
        "until_unix_seconds": end,
        "window_seconds": elapsed,
        "busy_seconds_lower_bound": busy,
        "busy_fraction_lower_bound": busy / elapsed,
        "intersecting_measured_phases": len(intervals),
        "phase_observations": counts,
    }


# reporting a future or reversed window would turn an unknown interval into idle time
def validate_window(window):
    if window is not None:
        start, end = window
        require(
            is_timestamp(start) and is_timestamp(end) and start < end <= time.time(),
            "Fusion busy time requires an increasing past Unix-time window",
        )
