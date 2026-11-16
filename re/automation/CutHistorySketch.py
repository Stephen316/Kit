"""Compare selected world perimeters and distinguish the two P04 positioning graphs."""

import math

from CutHistoryGraph import GraphGap, check, index, length_mm, ref, unique, world
from interchange.Enums.EnumValues import ParameterRole
from interchange.geometry.Models.GeometryCurves import LineGeometry, PointGeometry
from PairedPerimeters import match_perimeters


def measured_edges(sketch, application):
    if application == "fusion":
        curves = [
            row
            for row in sketch["curves"]
            if row["type"] == "SketchLine"
            and not row["construction"]
            and not row["reference"]
        ]
    else:
        curves = [
            row
            for row in sketch["entities"]
            if row["type"] == 0 and not row["construction"]
        ]
    return tuple(
        (ordinal, (row["start_world_mm"], row["end_world_mm"]))
        for ordinal, row in enumerate(curves)
    )


def measure_profile(role, observation, application, tolerance):
    matches = []
    for sketch in observation["sketches"]:
        geometry = match_perimeters(
            role.perimeter, measured_edges(sketch, application), tolerance
        )
        if geometry["status"] == "ambiguous":
            raise GraphGap(
                "historical perimeter edge correspondence is ambiguous", "ambiguous"
            )
        if geometry["status"] == "equal":
            matches.append((sketch, geometry))
    return unique(matches, "historical measured profile with the same world perimeter")


def bound_parameters(history, role):
    parameters = {}
    entities = index(role.sketch.entities, "constraint operand")
    for relation in role.sketch.constraints:
        if relation.parameter_id is None or relation.suppressed:
            continue
        parameter = ref(
            history.parameters, relation.parameter_id, "dimension parameter"
        )
        check(
            parameter.id in role.sketch.parameter_ids
            and parameter.id in role.owner.parameter_ids
            and parameter.owner_id == role.owner.id
            and relation.references
            and all(operand.entity_id in entities for operand in relation.references),
            "dimension lacks exact sketch ownership or operand links",
        )
        check(
            parameter.id not in parameters, "duplicate parameter bindings", "ambiguous"
        )
        parameters[parameter.id] = relation
    return parameters


def size_axis(role, relation, length, tolerance):
    entities = index(role.sketch.entities, "dimension operand")
    points = []
    for operand in relation.references:
        geometry = ref(entities, operand.entity_id, "dimension operand").geometry
        if isinstance(geometry, PointGeometry):
            points.append(world(role.plane.transform, geometry.point))
        elif isinstance(geometry, LineGeometry) and operand.point in ("start", "end"):
            points.append(world(role.plane.transform, getattr(geometry, operand.point)))
        else:
            raise GraphGap("size dimension lacks a selected profile endpoint")
    corners = tuple(point for _, edge in role.perimeter for point in edge)
    check(
        len(points) == 2
        and all(
            any(math.dist(point, corner) <= tolerance for corner in corners)
            for point in points
        ),
        "size dimension endpoints are outside the selected profile",
    )
    spans = tuple(abs(a - b) for a, b in zip(*points, strict=True))
    axis = unique(
        (index for index, value in enumerate(spans) if value > tolerance),
        "world size axis",
    )
    check(
        abs(spans[axis] - length) <= tolerance,
        "size parameter differs from selected endpoints",
    )
    return axis


def fusion_center(history, measured, tolerance):
    sketch = history.cut.sketch
    entities = index(sketch.entities, "Fusion Cut sketch entity")
    midpoint = unique(
        (
            item
            for item in sketch.constraints
            if item.kind == "midpoint" and item.driving and not item.suppressed
        ),
        "Fusion Cut midpoint relation",
    )
    operands = tuple(
        ref(entities, item.entity_id, "midpoint operand")
        for item in midpoint.references
    )
    diagonal = unique(
        (
            item
            for item in operands
            if item.construction and isinstance(item.geometry, LineGeometry)
        ),
        "midpoint construction diagonal",
    )
    center = unique(
        (item for item in operands if item.id != diagonal.id), "midpoint center point"
    )
    anchor = unique(
        (
            item
            for item in entities.values()
            if item.attributes.get("fusion.projection_mode") == "origin_project"
        ),
        "projected origin",
    )
    projection = tuple(
        item
        for item in entities.values()
        if item.attributes.get("fusion.projection_mode") == "automatic_face_boundary"
    )
    measured_curves = measured["curves"]
    member = history.support.attributes.get("fusion.history_body_member")
    selected = {identity for identity, _ in history.cut.perimeter}
    check(
        isinstance(center.geometry, PointGeometry)
        and isinstance(anchor.geometry, PointGeometry)
        and diagonal.id not in selected
        and len(projection) == 4
        and member is not None
        and all(
            item.id not in selected
            and isinstance(item.geometry, LineGeometry)
            and item.attributes.get("fusion.projection_source_member") == member
            for item in projection
        )
        and len(
            {
                item.attributes.get("fusion.projection_source_edge_ordinal")
                for item in projection
            }
        )
        == 4
        and sum(
            item["reference"] and not item["construction"] for item in measured_curves
        )
        == 4
        and sum(
            item["construction"] and not item["reference"] for item in measured_curves
        )
        == 1
        and sum(
            item["type"] == "MidPointConstraint" for item in measured["constraints"]
        )
        == 1,
        "Fusion midpoint and reference-curve inventory lacks independent corroboration",
    )
    base = bound_parameters(history, history.base)
    historical_expressions = {
        item["expression"] for item in measured["dimensions"] if item["driving"]
    }
    expressions = []
    for identity, relation in bound_parameters(history, history.cut).items():
        parameter = history.parameters[identity]
        if parameter.expression is None or not parameter.expression.parameter_ids:
            continue
        dependency = unique(
            parameter.expression.parameter_ids, "Fusion center expression dependency"
        )
        value = length_mm(parameter.value)
        check(
            relation.kind in ("distance_x", "distance_y")
            and relation.driving
            and {item.entity_id for item in relation.references}
            == {anchor.id, center.id}
            and dependency in base
            and base[dependency].driving
            and parameter.expression.source in historical_expressions
            and abs(value - length_mm(history.parameters[dependency].value) / 2)
            <= tolerance,
            "Fusion center expression lacks its midpoint, base-size dependency or measured value",
        )
        base_size = length_mm(history.parameters[dependency].value)
        expressions.append(
            {
                "relation": relation.id,
                "parameter": identity,
                "driving": relation.driving,
                "base_dependency": dependency,
                "value_mm": value,
                "base_size_mm": base_size,
                "world_size_axis": size_axis(
                    history.base, base[dependency], base_size, tolerance
                ),
                "source": parameter.expression.source,
            }
        )
    check(
        len(expressions) == len({item["base_dependency"] for item in expressions}) == 2,
        "Fusion center dimensions do not bind two distinct base sizes",
    )
    return {
        "midpoint": midpoint.id,
        "diagonal": diagonal.id,
        "projected_origin": anchor.id,
        "projected_edges": tuple(item.id for item in projection),
        "dimensions": expressions,
    }


def solidworks_offsets(history, measured, observation, tolerance):
    base = bound_parameters(history, history.base)
    cut = bound_parameters(history, history.cut)
    perimeter = {key for key, _ in history.cut.perimeter}
    independent_rhs = {item.partition(" = ")[2] for item in observation["equations"]}
    check(
        all(not item["construction"] for item in measured["entities"])
        and not any(
            item.construction and isinstance(item.geometry, LineGeometry)
            for item in history.cut.sketch.entities
        ),
        "SOLIDWORKS offset history has unclassified construction curves",
    )
    expressions = []
    for identity, relation in cut.items():
        parameter = history.parameters[identity]
        if parameter.expression is None:
            continue
        dependencies = parameter.expression.parameter_ids
        base_key = unique(
            (key for key in dependencies if key in base), "offset base size"
        )
        cut_key = unique((key for key in dependencies if key in cut), "offset cut size")
        cut_size = history.parameters[cut_key]
        value = length_mm(parameter.value)
        base_size = length_mm(history.parameters[base_key].value)
        size = length_mm(cut_size.value)
        check(
            len(dependencies) == 2
            and cut_size.expression is None
            and relation.kind in ("distance_x", "distance_y")
            and parameter.role == ParameterRole.KDerived
            and not relation.driving
            and base[base_key].driving
            and cut[cut_key].driving
            and any(
                item.entity_id in perimeter and item.point in ("start", "end")
                for item in relation.references
            )
            and parameter.expression.source in independent_rhs
            and abs(value - (base_size - size) / 2) <= tolerance,
            "SOLIDWORKS offset lacks measured equation, selected endpoint or typed size dependencies",
        )
        axis = size_axis(history.base, base[base_key], base_size, tolerance)
        check(
            size_axis(history.cut, cut[cut_key], size, tolerance) == axis,
            "SOLIDWORKS offset dependencies use different world axes",
        )
        expressions.append(
            {
                "relation": relation.id,
                "parameter": identity,
                "driving": relation.driving,
                "base_dependency": base_key,
                "cut_dependency": cut_key,
                "value_mm": value,
                "base_size_mm": base_size,
                "cut_size_mm": size,
                "world_size_axis": axis,
                "source": parameter.expression.source,
            }
        )
    check(
        len(expressions)
        == len({item["base_dependency"] for item in expressions})
        == len({item["cut_dependency"] for item in expressions})
        == 2,
        "SOLIDWORKS offsets do not bind two distinct base and cut size pairs",
    )
    return expressions


def compare_positioning(
    fusion, solidworks, fusion_sketch, sw_sketch, sw_observation, tolerance
):
    centers = fusion_center(fusion, fusion_sketch, tolerance)
    offsets = solidworks_offsets(solidworks, sw_sketch, sw_observation, tolerance)
    matched_offsets = set()
    for center in centers["dimensions"]:
        offset = unique(
            (
                item
                for item in offsets
                if item["world_size_axis"] == center["world_size_axis"]
            ),
            "offset with the same independently bound world size axis",
        )
        check(
            offset["parameter"] not in matched_offsets,
            "offset axis matched twice",
            "ambiguous",
        )
        matched_offsets.add(offset["parameter"])
        check(
            abs(offset["base_size_mm"] - center["base_size_mm"]) <= tolerance
            and abs(offset["value_mm"] + offset["cut_size_mm"] / 2 - center["value_mm"])
            <= tolerance,
            "midpoint and offset positions disagree within the selected perimeters",
            "different",
        )
    return {
        "status": "meaningfully_different",
        "fusion": centers,
        "solidworks": offsets,
    }
