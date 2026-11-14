import math
import re
from collections import Counter

P03_BOUNDS_CASES = {
    "P03-solidworks-baseline-a.SLDPRT",
    "P03-solidworks-direction-negative.SLDPRT",
}
BODY_Z_BOUNDS = "neutral.body.bounding_box_z_mm"


def lengths_equal(expected, actual, tolerance):
    return (
        isinstance(actual, (int, float))
        and math.isclose(expected, actual, rel_tol=0, abs_tol=tolerance)
    )


def normalized_rhs(value):
    return re.sub(r"\s+", "", value)


def observation(name, expected, actual, match=None):
    if actual is None:
        status = "unobserved"
    elif match is None:
        status = "matched" if expected == actual else "different"
    else:
        status = "matched" if match else "different"
    return {"field": name, "expected": expected, "actual": actual, "status": status}


def segments_key(segments):
    return sorted(tuple(sorted(tuple(point) for point in edge)) for edge in segments)


def segment_equal(left, right, tolerance):
    return all(
        lengths_equal(a, b, tolerance)
        for left_point, right_point in zip(left, right, strict=True)
        for a, b in zip(left_point, right_point, strict=True)
    )


def segments_equal(expected, actual, tolerance):
    if actual is None or len(expected) != len(actual):
        return False
    remaining = list(actual)
    for left in expected:
        matches = [
            index for index, right in enumerate(remaining)
            if segment_equal(left, right, tolerance) or segment_equal(left, right[::-1], tolerance)
        ]
        if len(matches) != 1:
            return False
        remaining.pop(matches[0])
    return True


def compare_dimensions(measured, native, neutral, tolerance):
    native_dims = {item["name"]: item for item in native.get("dimensions", ())}
    neutral_params = {item["name"]: item for item in neutral.get("parameters", ())}
    comparisons = []
    for feature in measured["feature_tree"]:
        for dim in feature["dimensions"]:
            name = f"{dim['name']}@{feature['name']}"
            expected = dim["system_value"] * 1000
            extracted = native_dims.get(name, {}).get("value_mm")
            projected = neutral_params.get(name, {})
            value = projected.get("value") if projected.get("unit") == "mm" else None
            comparisons.extend((
                observation("native.dimension." + name, expected, extracted, lengths_equal(expected, extracted, tolerance)),
                observation("neutral.dimension." + name, expected, value, lengths_equal(expected, value, tolerance)),
            ))
    return comparisons


def compare_equations(measured, native, neutral):
    native_eqs = {item["lhs"]: item for item in native.get("equations", ())}
    neutral_params = {item["name"]: item for item in neutral.get("parameters", ())}
    comparisons = []
    for equation in measured["equations"]:
        lhs, rhs = equation.split("=", 1)
        name = lhs.strip().strip('"')
        expected = {"rhs": normalized_rhs(rhs), "references": re.findall(r'"([^"]+)"', rhs)}
        extracted = native_eqs.get(name)
        projected = neutral_params.get(name, {}).get("expression")
        for scope, row in (("native", extracted), ("neutral", projected)):
            actual = None if row is None else {
                "rhs": normalized_rhs(row["rhs"]), "references": list(row["references"]),
            }
            for kind in ("rhs", "references"):
                comparisons.append(observation(
                    f"{scope}.equation.{name}.{kind}", expected[kind], None if actual is None else actual[kind]
                ))
    return comparisons


def require_equation_bindings(findings):
    expected_fields = {
        "neutral.equation.cut_left_mm@CutSketch.references",
        "neutral.equation.cut_bottom_mm@CutSketch.references",
    }
    failures = []
    checked = 0
    for item in findings:
        if item["recipe_id"] != "P04":
            continue
        checked += 1
        references = {
            row["field"]: row for row in item["comparisons"] if row["field"] in expected_fields
        }
        for name in sorted(expected_fields):
            if references.get(name, {}).get("status") != "matched":
                failures.append(f"{item['asset']['path']}: {name}")
    if checked != 11:
        raise ValueError(f"P04 equation check requires 11 captures, found {checked}")
    if failures:
        raise ValueError("P04 equation binding regression:\n" + "\n".join(failures))
    print(f"Verified both P04 equation bindings in {checked} captures")


def compare_operations(measured, native, neutral, tolerance):
    native_ops = {item["name"]: item for item in native.get("operations", ())}
    neutral_ops = {item["name"]: item for item in neutral.get("features", ())}
    comparisons = []
    for step in measured["feature_tree"]:
        op = step["operation"]
        if not op:
            continue
        name = step["name"]
        extracted = native_ops.get(name, {})
        projected = neutral_ops.get(name, {})
        code = op["end_condition"]
        length = None if code == 1 else op["depth_m"] * 1000
        observed_length = projected.get("length_mm")
        comparisons.extend((
            observation(f"native.operation.{name}.reverse_code", int(op["reverse_direction"]), extracted.get("direction_code")),
            observation(f"native.operation.{name}.end_code", code, extracted.get("termination_code")),
            observation(f"neutral.operation.{name}.end", {0: "blind", 1: "through_all"}[code], projected.get("end_condition")),
            observation(f"neutral.operation.{name}.operation", "cut" if name.endswith("Cut") else "join", projected.get("operation")),
        ))
        if length is not None:
            native_length = extracted.get("length_mm")
            comparisons.append(observation(
                f"native.operation.{name}.depth_mm", length, native_length, lengths_equal(length, native_length, tolerance)
            ))
            comparisons.append(observation(f"neutral.operation.{name}.depth_mm", length, observed_length, lengths_equal(length, observed_length, tolerance)))
        if name == "BlindBoss":
            comparisons.extend((
                observation(f"neutral.operation.{name}.reversed", op["reverse_direction"], projected.get("reversed")),
                observation(f"neutral.operation.{name}.direction_multiplier",
                            -1 if op["reverse_direction"] else 1, projected.get("direction_multiplier")),
            ))
    return comparisons


def compare_sketches(measured, native, neutral, tolerance):
    native_sketches = {item["name"]: item for item in native.get("sketches", ())}
    neutral_sketches = {item["name"]: item for item in neutral.get("sketches", ())}
    comparisons = []
    for sketch in measured["sketches"]:
        name = sketch["name"]
        extracted = native_sketches.get(name, {})
        projected = neutral_sketches.get(name, {})
        expected = segments_key(
            (item["start_world_mm"], item["end_world_mm"])
            for item in sketch["entities"] if item["type"] == 0 and not item["construction"]
        )
        actual = segments_key(projected["world_segments_mm"]) if projected else None
        comparisons.append(observation(
            f"neutral.sketch.{name}.world_segments_mm", expected, actual, segments_equal(expected, actual, tolerance)
        ))
        for code, kind in ((4, "horizontal"), (5, "vertical")):
            constraints = [
                rel for rel in projected.get("relations", ())
                if rel["kind"] == kind and rel["reference_count"] > 0 and not rel["inferred"]
            ]
            count = Counter(rel["type"] for rel in sketch["relations"])
            comparisons.append(observation(
                f"neutral.sketch.{name}.bound_{kind}_constraints", count[code],
                len(constraints) if projected else None,
            ))
        if sketch["support_type"] == 2:
            comparisons.extend((
                observation(f"native.sketch.{name}.support_kind", "face", extracted.get("support_kind")),
                observation(
                    f"neutral.sketch.{name}.face_selection_present", True,
                    bool(projected.get("support_selection_id")) if projected else None,
                ),
                observation(
                    f"neutral.sketch.{name}.face_producer", "BlindBoss",
                    projected.get("support_face_producer"),
                ),
            ))
        else:
            comparisons.append(observation(f"neutral.sketch.{name}.support_name", sketch["support_name"], projected.get("support_name")))
    return comparisons


def compare_boss_bounds(measured, neutral, tolerance):
    depth_m = next(
        step["operation"]["depth_m"] for step in measured["feature_tree"]
        if step["name"] == "BlindBoss"
    )
    half_depth_mm = depth_m * 500
    center_z = measured["center_of_mass_mm"][2]
    expected = [center_z - half_depth_mm, center_z + half_depth_mm]
    bounds = neutral.get("body_bounding_box_mm")
    actual = [point[2] for point in bounds] if bounds is not None else None
    matched = actual is not None and all(
        lengths_equal(wanted, observed, tolerance)
        for wanted, observed in zip(expected, actual, strict=True)
    )
    return observation(BODY_Z_BOUNDS, expected, actual, matched)


def compare(measured, native, neutral, tolerance, capture_name):
    comparisons = [
        observation("neutral.solid_count", measured["body_count"], neutral.get("solid_count")),
        observation("neutral.source_display_unit", {3: "in", 5: "mm"}[measured["units_code"]], neutral.get("native_display_unit")),
        *compare_dimensions(measured, native, neutral, tolerance),
        *compare_equations(measured, native, neutral),
        *compare_operations(measured, native, neutral, tolerance),
        *compare_sketches(measured, native, neutral, tolerance),
    ]
    if capture_name in P03_BOUNDS_CASES:
        comparisons.append(compare_boss_bounds(measured, neutral, tolerance))
    return comparisons


def require_boss_directions(findings):
    cases = [entry for entry in findings if entry["recipe_id"] == "P03"]
    if len(cases) != 8:
        raise ValueError(f"P03 direction check requires 8 captures, found {len(cases)}")
    expected_fields = {
        "native.operation.BlindBoss.reverse_code",
        "neutral.operation.BlindBoss.reversed",
        "neutral.operation.BlindBoss.direction_multiplier",
    }
    for entry in cases:
        path = entry["asset"]["path"]
        required = (
            expected_fields | {BODY_Z_BOUNDS}
            if path.rsplit("/", 1)[-1] in P03_BOUNDS_CASES else expected_fields
        )
        matched = {row["field"] for row in entry["comparisons"] if row["status"] == "matched"}
        if missing := required - matched:
            raise ValueError(f"Blind boss direction mismatch in {path}: {', '.join(sorted(missing))}")
    print(f"Verified P03 boss directions in {len(cases)} captures and both XY baseline/reverse Z bounds")


def require_rectangle_edges(findings):
    cases = [entry for entry in findings if entry["recipe_id"] == "P01"]
    if len(cases) != 6:
        raise ValueError(f"P01 rectangle topology check requires 6 captures, found {len(cases)}")
    for entry in cases:
        path = entry["asset"]["path"]
        comparisons = [
            row for row in entry["comparisons"]
            if row["field"] == "neutral.sketch.RectangleSketch.world_segments_mm"
        ]
        if len(comparisons) != 1:
            raise ValueError(f"P01 has no unique rectangle edge comparison: {path}")
        comparison = comparisons[0]
        expected, actual = comparison["expected"], comparison["actual"]
        if len(expected) != 4 or actual is None or len(actual) != 4:
            raise ValueError(f"P01 does not project the four measured rectangle edges: {path}")
        if not path.endswith("-plane-yz.SLDPRT") and comparison["status"] != "matched":
            raise ValueError(f"P01 rectangle endpoints differ from the measurement: {path}")
    print(f"Verified four P01 edges in {len(cases)} captures and measured XY endpoints")
