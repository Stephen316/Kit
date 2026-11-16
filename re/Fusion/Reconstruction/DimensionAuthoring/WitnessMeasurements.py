# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import math

from ProbeAcceptance import require
from ProbeAcceptanceShape import CASES, check_rectangle, close_mm

CONTROL_VOLUME_MM3 = 30000.0


def check_readback(reading, pin):
    diagnostic = reading["import"]
    require(
        reading["native_input"] == pin
        and reading["compute_all_return"] is True
        and diagnostic["return"] == "document"
        and diagnostic["exception"] is None
        and diagnostic["last_error_on_failure"] is None
        and diagnostic["aggregate_loader_warnings"] is None,
        "Native import or recompute does not bind the expected input",
    )
    for key in ("before_recompute", "after_recompute"):
        timeline = reading[key]["feature_tree"]
        require(
            timeline
            and all(
                row["health"]["state"] == "healthy"
                and row["suppressed"] is False
                and row["rolled_back"] is False
                for row in timeline
            ),
            "Native readback contains an unhealthy or inactive feature",
        )


def check_controls(report, pin):
    for label in ("healthy_control_before", "healthy_control_after"):
        control = report[label]
        check_readback(control, pin)
        snapshot = control["after_recompute"]
        require(
            type(snapshot["body_count"]) is int
            and snapshot["body_count"] == 1
            and math.isclose(
                snapshot["volume_mm3"], CONTROL_VOLUME_MM3, rel_tol=1e-9, abs_tol=1e-6
            ),
            "Native control did not retain its measured solid",
        )


def original_orientations(snapshot, size):
    # The width and height of both controls differ, so the measured sizes identify the axes.
    parameters = {row["name"]: row for row in snapshot["parameters"]}
    dimensions = snapshot["sketches"][0]["bindings"]["dimensions"]
    endpoints = ("right", "upper")
    orientations = {}
    for dimension in dimensions:
        orientation = dimension["orientation"]
        value_mm = parameters[dimension["parameter"]]["value_internal"] * 10.0
        matches = [
            axis for axis, expected in enumerate(size) if close_mm(value_mm, expected)
        ]
        require(
            type(orientation) is int
            and orientation not in orientations
            and len(matches) == 1,
            "Original measurements do not distinguish the two size orientations",
        )
        axis = matches[0]
        orientations[orientation] = (axis, endpoints[axis])
    require(
        set(orientations.values()) == {(0, "right"), (1, "upper")},
        "Original measurements do not bind both size axes",
    )
    return orientations


def check_snapshot(snapshot, kind, sizes, orientations):
    check_rectangle(snapshot, kind, sizes, orientations)
    require(
        snapshot["sketches"][0]["support"] == "ConstructionPlane",
        "Native sketch no longer reports a construction-plane support",
    )
    parameters = snapshot["parameters"]
    expressions = {row["name"]: row["expression"] for row in parameters}
    require(
        len(expressions) == len(parameters)
        and all(isinstance(value, str) and value for value in expressions.values()),
        "Native parameter expressions are missing or ambiguous",
    )
    return expressions


def check_original(report, pin, kind, sizes, orientations):
    reading = report["readback"]
    check_readback(reading, pin)
    before = check_snapshot(reading["before_recompute"], kind, sizes, orientations)
    after = check_snapshot(reading["after_recompute"], kind, sizes, orientations)
    require(before == after, "Native recompute changed the original expressions")
    return after


def check_edits(first, second, original, orientations):
    kind = first["candidate_kind"]
    case = CASES[kind]
    names = case["parameters"]
    require(
        first["initial"] == original
        and second["reopened_expressions"] == original
        and set(first["edits"]) == set(names),
        "The independent edit or restoration roster differs",
    )
    areas = {}
    for axis, name in enumerate(names):
        row = first["edits"][name]
        requested = case["edited_mm"][axis]
        edited_sizes = list(case["original_mm"])
        edited_sizes[axis] = requested
        require(
            row["original_expression"] == original[name]
            and type(row["requested_mm"]) in (float, int)
            and row["requested_mm"] == requested
            and row["edit_compute_all_return"] is True
            and row["restore_compute_all_return"] is True,
            "Native edit or restoration did not record a successful rebuild",
        )
        edited = check_snapshot(row["edited"], kind, edited_sizes, orientations)
        restored = check_snapshot(
            row["restored"], kind, case["original_mm"], orientations
        )
        require(
            set(edited) == set(original)
            and edited[name] != original[name]
            and all(
                edited[key] == value for key, value in original.items() if key != name
            )
            and restored == original,
            "The edit changed another driver or failed to restore the original expressions",
        )
        areas[name] = row["edited"]["sketches"][0]["profile_areas_mm2"][0]
    return areas


def verify_measurements(plan, first, second, restored):
    kind = plan["candidate_kind"]
    size = CASES[kind]["original_mm"]
    orientations = original_orientations(first["readback"]["before_recompute"], size)
    check_controls(first, plan["pins"]["control"])
    check_controls(second, plan["pins"]["control"])
    original = check_original(
        first, plan["candidate"]["input"], kind, size, orientations
    )
    reopened = check_original(second, restored, kind, size, orientations)
    require(
        reopened == original,
        "Fresh-process reopen did not retain the restored expressions",
    )
    return {
        "healthy_control_count": 4,
        "initial_area_mm2": first["readback"]["after_recompute"]["sketches"][0][
            "profile_areas_mm2"
        ][0],
        "edited_areas_mm2": check_edits(first, second, original, orientations),
        "reopened_area_mm2": second["readback"]["after_recompute"]["sketches"][0][
            "profile_areas_mm2"
        ][0],
    }
