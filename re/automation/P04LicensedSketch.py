"""Match saved P04 sketch dimensions and equations to licensed SOLIDWORKS observations."""

import argparse
import math
import re
import sys
from pathlib import Path

from P04LicensedSupport import licensed_cases
from CutHistoryGraph import unique
from CutHistorySketch import bound_parameters
from PairedCaptureIntake import require
from Records import canonical
from interchange.enums.EnumValues import ParameterRole, ValueKind
from interchange.features.DistanceParam import GetDistParam

ASSIGNMENT = re.compile(r'"([^"]+)"\s*=\s*\(\s*"([^"]+)"\s*-\s*"([^"]+)"\s*\)\s*/\s*2')
PHASES = ("before_rebuild", "after_rebuild")


def paired_dimensions(history, role, native, tolerance):
    observed = unique(
        (sketch for sketch in native["sketches"] if sketch["feature"]["name"] == role.sketch.name),
        "licensed sketch owner",
    )
    measured = {item["name"]: item for item in observed["dimensions"]}
    require(len(measured) == len(observed["dimensions"]), "duplicate measured dimension name")
    matched = {}
    for identity, constraint in bound_parameters(history, role).items():
        parameter = history.parameters[identity]
        expected = measured.pop(parameter.name)
        qualified = f"{parameter.name}@{role.sketch.name}"
        driven_state = expected["driven_state"]
        require(
            "@".join(expected["full_name"].split("@")[:2]) == qualified
            and expected["owner"] == observed["feature"]
            and expected["same_owner"] is True and expected["dangling"] is False
            and driven_state in (1, 2) and constraint.driving == (driven_state == 2)
            and parameter.role == (ParameterRole.KDriving if constraint.driving else ParameterRole.KDerived),
            f"{qualified}: saved and measured parameter roles or owners differ",
        )
        length = GetDistParam(role.owner, identity, history.parameters, ValueKind.KLength)
        measured_length = 1000 * expected["system_value"]
        require(
            math.isfinite(measured_length) and abs(length - measured_length) <= tolerance,
            f"{qualified}: saved and measured values differ",
        )
        matched[qualified] = {
            "parameter_id": identity,
            "constraint_id": constraint.id,
            "sketch_native_id": observed["feature"]["id"],
            "role": parameter.role.value,
            "saved_mm": length,
            "measured_mm": measured_length,
        }
    require(not measured and matched, "a licensed dimension is missing from the saved sketch")
    return matched


def paired_equations(history, native, dimensions, tolerance):
    rows = {}
    for value in native["equations"]:
        assignment = ASSIGNMENT.fullmatch(value.strip())
        require(assignment is not None, "unexpected licensed centering expression")
        target, left, right = assignment.groups()
        require(target not in rows, f"duplicate licensed equation for {target}")
        owner = dimensions[target]
        left_value, right_value = dimensions[left], dimensions[right]
        expression = history.parameters[owner["parameter_id"]].expression
        expected = f'("{left}" - "{right}") / 2'
        require(
            expression is not None and expression.language == "solidworks"
            and expression.source == expected
            and expression.parameter_ids == (left_value["parameter_id"], right_value["parameter_id"]),
            f"{target}: ordered saved dependencies differ from the licensed expression",
        )
        measured_result = (left_value["measured_mm"] - right_value["measured_mm"]) / 2
        require(
            abs(owner["measured_mm"] - measured_result) <= tolerance,
            f"{target}: equation does not reproduce its measured value",
        )
        rows[target] = {"source": value, "parameter_ids": expression.parameter_ids}
    require(
        set(rows) == {name for name, row in dimensions.items() if row["role"] == "derived"},
        "saved expression-owned dimensions differ from the measured equation roster",
    )
    return rows


def report(directory, receipt_digest):
    provenance, tolerances, cases = licensed_cases(directory, receipt_digest)
    tolerance = tolerances["length_mm_absolute"]
    rows = []
    for asset, history, native in cases:
        bindings = {}
        for phase in PHASES:
            observed = native[phase]
            dimensions = {
                **paired_dimensions(history, history.base, observed, tolerance),
                **paired_dimensions(history, history.cut, observed, tolerance),
            }
            equations = paired_equations(history, observed, dimensions, tolerance)
            bindings[phase] = {"dimensions": dimensions, "equations": equations}
        rows.append({"variant": asset["variant"], "sha256": asset["sha256"], "native": bindings})
    return {
        "scope": "solidworks_a04c_saved_sketch_bindings_vs_licensed_measurement",
        **provenance,
        "length_tolerance_mm": tolerance,
        "cases": rows,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("readback_directory", type=Path)
    parser.add_argument("--receipt-sha256", required=True)
    args = parser.parse_args()
    sys.stdout.buffer.write((canonical(report(args.readback_directory, args.receipt_sha256)) + "\n").encode())
