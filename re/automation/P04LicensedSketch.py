"""Match saved P04 sketch dimensions and equations to licensed SOLIDWORKS observations."""

import argparse
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

from P04LicensedSupport import licensed_cases
from CutHistoryGraph import unique, xyz
from CutHistorySketch import bound_parameters
from PairedCaptureIntake import require
from Records import canonical
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Features.DistanceParam import GetDistParam
from interchange.geometry.Models.GeometryCurves import LineGeometry, PointGeometry

ASSIGNMENT = re.compile(r'"([^"]+)"\s*=\s*\(\s*"([^"]+)"\s*-\s*"([^"]+)"\s*\)\s*/\s*2')
PHASES = ("before_rebuild", "after_rebuild")


def paired_operands(role, constraint, measured, native, tolerance):
    attachments = measured["attachments"]
    require(
        measured["attachment_status"] == "observed_slots"
        and measured["attachment_count"] == len(attachments) == len(constraint.references) == 2,
        "expected two observed dimension attachments",
    )
    return paired_definition(role, constraint, attachments, native, tolerance)


def paired_definition(role, constraint, attachments, native, tolerance):
    entities = {item.id: item for item in role.sketch.entities}
    operands = []
    sources = constraint.attributes["native_point_ids"]
    for reference, point_id, attachment in zip(constraint.references, sources, attachments, strict=True):
        entity = entities[reference.entity_id]
        geometry = entity.geometry
        require(
            attachment["kind"] == "sketch_point" and attachment["native_sketch_available"] is True,
            "licensed dimension operand is missing its sketch point owner",
        )
        if isinstance(geometry, LineGeometry) and reference.point in ("start", "end"):
            point = getattr(geometry, reference.point)
            local = (point.x, point.y, 0.0)
            require(
                attachment["same_sketch"] is True
                and attachment["native_sketch_owner"] == role.sketch.name
                and tuple(attachment["id"]) == tuple(point_id)
                and math.dist(local, [1000 * value for value in attachment["local_m"]]) <= tolerance,
                "licensed point ID or placement differs from the saved ordered perimeter operand",
            )
        else:
            origin = native["origin_feature"]
            measured_origin = unique(native["origin_points"], "licensed Origin point")
            require(
                isinstance(geometry, PointGeometry) and reference.point == ""
                and native["origin_returns_sketch"] is True
                and attachment["same_sketch"] is False
                and attachment["native_sketch_owner"] == origin["name"]
                and attachment["id"] == measured_origin["id"]
                and attachment["local_m"] == measured_origin["local_m"] == [0, 0, 0]
                and entity.attributes["native_origin_feature_id"] == origin["id"]
                and entity.attributes["native_point_id"] == tuple(point_id),
                "saved Origin proxy does not resolve to the licensed external operand",
            )
            frame = role.plane.transform
            position = xyz(frame.origin)
            expected_local = tuple(
                -math.fsum(a * b for a, b in zip(position, xyz(axis), strict=True))
                for axis in (frame.x_axis, frame.y_axis)
            )
            local = (geometry.point.x, geometry.point.y, 0.0)
            require(
                math.dist(local[:2], expected_local) <= tolerance,
                "saved Origin proxy differs from the measured Origin projected into the sketch",
            )
        operands.append({
            "entity_id": entity.id, "point": reference.point,
            "saved_point_id": point_id, "measured_point_id": attachment["id"],
            "measured_sketch": attachment["native_sketch_owner"],
            "saved_local_mm": local,
        })
    return operands


def paired_relation(role, constraint, relation, native, tolerance):
    current = relation["entities"]
    definition = relation["definition_entities"]
    require(
        relation["entity_types"] == [2, 2] and len(current) == len(definition) == 2,
        "licensed point relation lacks two ordered operands",
    )
    operands = paired_definition(role, constraint, definition, native, tolerance)
    for measured, authored, operand in zip(current, definition, operands, strict=True):
        require(
            measured["kind"] == "sketch_point"
            and measured["same_sketch"] is True
            and measured["native_sketch_available"] is True
            and measured["native_sketch_owner"] == role.sketch.name
            and math.dist(
                [1000 * value for value in measured["local_m"]], operand["saved_local_mm"]
            ) <= tolerance
            and (not authored["same_sketch"] or measured == authored),
            "licensed current point differs from the saved local relation operand",
        )
        operand["current_point_id"] = measured["id"]
    return operands


def consume_relation(measured, code, point_ids):
    pending = measured[(code, point_ids)]
    require(pending, f"missing licensed relation {code} with ordered IDs {point_ids}")
    return pending.pop()


def paired_relations(role, sketch, native, tolerance):
    measured = defaultdict(list)
    for relation in sketch["relations"]:
        key = relation["type"], tuple(tuple(entity["id"]) for entity in relation["entities"])
        measured[key].append(relation)
    entities = {item.id: item for item in role.sketch.entities}
    matched = []
    for constraint in role.sketch.constraints:
        code = constraint.attributes["native_code"]
        if code in (4, 5):
            segment_id = constraint.attributes["native_segment_id"]
            (reference,) = constraint.references
            entity = entities[reference.entity_id]
            require(
                isinstance(entity.geometry, LineGeometry) and not entity.construction
                and reference.point == "" and entity.attributes["native_segment_id"] == segment_id,
                "saved axis relation must target the native perimeter member",
            )
            relation = consume_relation(measured, code, ((segment_id, segment_id),))
            require(
                relation["entity_types"] == [3]
                and relation["entities"] == relation["definition_entities"] == [
                    {"kind": "sketch_segment", "id": [segment_id, segment_id], "type": 0, "same_sketch": True}
                ],
                "licensed current and definition axis operands differ from the saved member",
            )
            operands = [{"entity_id": entity.id, "segment_id": segment_id}]
        else:
            point_ids = constraint.attributes["native_point_ids"]
            relation = consume_relation(measured, code, point_ids)
            operands = paired_relation(role, constraint, relation, native, tolerance)
        matched.append({"constraint_id": constraint.id, "native_code": code, "ordered_operands": operands})
    require(not any(measured.values()), "a licensed relation is missing from the saved sketch")
    return matched


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
            "ordered_operands": paired_operands(role, constraint, expected, native, tolerance),
        }
    require(not measured and matched, "a licensed dimension is missing from the saved sketch")
    return matched, paired_relations(role, observed, native, tolerance)


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
            base_dimensions, base_relations = paired_dimensions(history, history.base, observed, tolerance)
            cut_dimensions, cut_relations = paired_dimensions(history, history.cut, observed, tolerance)
            dimensions = {**base_dimensions, **cut_dimensions}
            equations = paired_equations(history, observed, dimensions, tolerance)
            bindings[phase] = {
                "dimensions": dimensions,
                "equations": equations,
                "relations": {history.base.sketch.name: base_relations, history.cut.sketch.name: cut_relations},
            }
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
