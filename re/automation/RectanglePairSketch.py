"""Bind public rectangular sketches to their saved and independently measured operands."""

import math
from collections import Counter

from FusionRectangleSketchEvidence import historical_world_curves
from PairedCaptureIntake import require
from PairedPerimeters import edge_gap, match_perimeters
from interchange.geometry.models.GeometryCurves import LineGeometry, PointGeometry


def unique(values, purpose):
    values = list(values)
    require(len(values) == 1, f"{purpose}: expected one value, found {len(values)}")
    return values[0]


def xyz(point):
    return point.x, point.y, point.z


def world(frame, point):
    return world_xy(frame, point.x, point.y)


def world_xy(frame, x, y):
    return tuple(
        origin + x * axis_x + y * axis_y
        for origin, axis_x, axis_y in zip(
            xyz(frame.origin), xyz(frame.x_axis), xyz(frame.y_axis), strict=True
        )
    )


def parameter_mm(parameter):
    value = parameter.value
    require(
        value.kind == "length"
        and type(value.value) in (float, int)
        and value.unit in ("mm", "cm")
        and math.isfinite(value.value),
        f"{parameter.id}: expected a finite millimetre or centimetre length",
    )
    return value.value * (10 if value.unit == "cm" else 1)


def same(first, second, tolerance, purpose):
    require(math.dist(first, second) <= tolerance, purpose)


def unique_index(values, key, purpose):
    mapping = {key(value): value for value in values}
    require(len(mapping) == len(values), f"{purpose}: duplicate identity")
    return mapping


def verify_cycle(perimeter, tolerance):
    edges = [edge for _, edge in perimeter]
    neighbours = []
    for index, edge in enumerate(edges):
        require(math.dist(*edge) > tolerance, "degenerate world perimeter edge")
        neighbours.append(
            [
                unique(
                    (
                        (other, end)
                        for other, line in enumerate(edges)
                        if other != index
                        for end, candidate in enumerate(line)
                        if math.dist(point, candidate) <= tolerance
                    ),
                    "perimeter vertex counterpart",
                )
                for point in edge
            ]
        )
    start, current = (0, 0), (0, 0)
    visited = set()
    for _ in range(4):
        index, incoming = current
        require(index not in visited, "premature perimeter closure")
        visited.add(index)
        current = neighbours[index][1 - incoming]
    require(current == start and len(visited) == 4, "four sides do not form one cycle")


def observed_geometry(observed, application, recipe):
    sketch = unique(observed["sketches"], "measured rectangular sketch")
    if application == "solidworks":
        measured = tuple(
            (tuple(row["id"]), (row["start_world_mm"], row["end_world_mm"]))
            for row in sketch["entities"]
            if row["type"] == 0 and not row["construction"]
        )
        matrix = sketch["model_to_sketch_transform"]
        axes = [
            tuple(matrix[index] for index in group)
            for group in ((0, 3, 6), (1, 4, 7), (2, 5, 8))
        ]
        require(matrix[12] == 1, "measured SOLIDWORKS frame has non-unit scale")
        origin = tuple(
            -1000 * sum(axis[row] * matrix[9 + index] for index, axis in enumerate(axes))
            for row in range(3)
        )
        return sketch, measured, origin, axes
    if recipe == "P01":
        curves = historical_world_curves(sketch)
        origin = sketch["origin_mm"]
    else:
        curves = sketch["curves"]
        origin = sketch["origin_world_mm"]
    measured = tuple(
        (index, (row["start_world_mm"], row["end_world_mm"]))
        for index, row in enumerate(curves)
        if row.get("type", "SketchLine") == "SketchLine"
        and not row.get("construction", False)
        and not row.get("reference", False)
    )
    axis_x, axis_y = sketch["x_direction"], sketch["y_direction"]
    normal = (
        axis_x[1] * axis_y[2] - axis_x[2] * axis_y[1],
        axis_x[2] * axis_y[0] - axis_x[0] * axis_y[2],
        axis_x[0] * axis_y[1] - axis_x[1] * axis_y[0],
    )
    return sketch, measured, origin, (axis_x, axis_y, normal)


def public_scope(document, observed, application, recipe, archive, tolerances):
    sketch = unique(document.sketches, "public rectangle")
    frame = unique(
        (
            value
            for value in document.support_planes
            if value.id == sketch.support_plane_id
        ),
        "public saved frame",
    )
    require(not sketch.suppressed, "public rectangle is suppressed")
    tolerance = tolerances["length_mm_absolute"]
    entities = unique_index(sketch.entities, lambda value: value.id, "sketch entity")
    line_entities = {
        identity: value
        for identity, value in entities.items()
        if isinstance(value.geometry, LineGeometry) and not value.construction
    }
    require(
        len(line_entities) == 4, "public sketch does not expose four authored lines"
    )
    loops = sketch.closed_profile_entity_ids
    if loops:
        (loop,) = loops
        require(
            len(loop) == 4 and set(loop) == line_entities.keys(),
            "public profile membership differs",
        )
    perimeter = tuple(
        (
            identity,
            (
                world(frame.transform, value.geometry.start),
                world(frame.transform, value.geometry.end),
            ),
        )
        for identity, value in line_entities.items()
    )
    verify_cycle(perimeter, tolerance)
    witness, measured, origin, axes = observed_geometry(observed, application, recipe)
    require(
        sketch.name == witness["name"] and len(measured) == 4,
        "historical sketch roster differs",
    )
    correspondence = match_perimeters(perimeter, measured, tolerance)
    require(
        correspondence["status"] == "equal",
        f"public to measured perimeter: {correspondence}",
    )
    if application == "fusion":
        require(
            frame.attributes.get("fusion.native_support_resolved") is True
            and frame.attributes.get("fusion.native_support_object_id")
            == archive["support"]["records"]["plane"]["object_id"]
            and frame.attributes.get("fusion.native_support_name")
            == archive["historical_measured_plane"]["plane"]
            and frame.provenance is not None,
            "public Fusion frame does not retain the saved datum route",
        )
        expected = {
            f"fusion-sketch-entity-{row['object_id']}": row["historical_curve_index"]
            for row in archive["geometry"]
            if row["kind"] == "Line"
        }
    else:
        require(
            sketch.attributes.get("support_plane_source") == "typed-archive-reference"
            and sketch.provenance is not None
            and any(
                item.record_kind == "sketch-support-reference"
                for item in sketch.provenance.spans
            )
            and frame.name == witness["support_name"],
            "public SOLIDWORKS frame lacks the saved datum reference",
        )
        expected = {
            key: (value.attributes["native_segment_id"],) * 2
            for key, value in line_entities.items()
        }
    require(
        dict(correspondence["matched_links"]) == expected,
        "public edge identity differs from native evidence",
    )
    same(xyz(frame.transform.origin), origin, tolerance, "public frame origin differs")
    angle = tolerances["angle_rad_absolute"]
    for value, measured_axis in zip(
        (frame.transform.x_axis, frame.transform.y_axis, frame.transform.z_axis),
        axes,
        strict=True,
    ):
        same(xyz(value), measured_axis, angle, "public frame axis differs")
    return sketch, frame.transform, entities, perimeter, witness, correspondence


def bound_point(entities, reference):
    geometry = entities[reference.entity_id].geometry
    if isinstance(geometry, PointGeometry):
        require(reference.point in ("", "start"), "unsupported point operand selector")
        return geometry.point
    require(
        isinstance(geometry, LineGeometry) and reference.point in ("start", "end"),
        "unsupported rectangle operand type",
    )
    return getattr(geometry, reference.point)


def match_axes(sketch, entities, witness, application, archive):
    axes = [
        item for item in sketch.constraints if item.kind in ("horizontal", "vertical")
    ]
    targets = {}
    for item in axes:
        (reference,) = item.references
        require(
            reference.point == ""
            and item.driving
            and not item.suppressed
            and item.provenance is not None,
            "axis rule lacks active typed line operand",
        )
        require(reference.entity_id not in targets, "repeated public axis target")
        if application == "solidworks":
            require(
                entities[reference.entity_id].attributes["native_segment_id"]
                == item.attributes["native_segment_id"],
                "SOLIDWORKS axis provenance and public line identify different segments",
            )
        targets[reference.entity_id] = item.kind
    require(len(axes) == len(targets) == 4, "four public axis relations required")
    if application == "fusion":
        expected = {
            f"fusion-sketch-entity-{item['entity_ids'][0]}": item["kind"].lower()
            for item in archive["constraints"]
            if item["kind"] in ("Horizontal", "Vertical")
        }
        require(
            targets == expected, "public Fusion axis targets differ from the archive"
        )
    else:
        measured = Counter(
            (row["type"], tuple(row["entities"][0]["id"]))
            for row in witness["relations"]
            if row["type"] in (4, 5)
        )
        require(
            measured
            == Counter(
                (
                    item.attributes["native_code"],
                    (item.attributes["native_segment_id"],) * 2,
                )
                for item in axes
            ),
            "public SOLIDWORKS axis targets differ from the reopen",
        )
    return targets


def match_origin(sketch, frame, entities, witness, application, archive, tolerance):
    rule = unique(
        (
            item
            for item in sketch.constraints
            if item.kind == "coincident" and not item.attributes.get("inferred")
        ),
        "authored origin coincidence",
    )
    require(
        rule.driving and not rule.suppressed and rule.provenance is not None,
        "origin coincidence lacks active typed provenance",
    )
    first, second = rule.references
    require(
        first.entity_id != second.entity_id,
        "origin relation repeats its public operand",
    )
    points = tuple(
        world(frame, bound_point(entities, operand)) for operand in rule.references
    )
    for point in points:
        same(
            point, xyz(frame.origin), tolerance, "origin operand lies off saved origin"
        )
    if application == "fusion":
        relation = unique(
            (item for item in archive["constraints"] if item["kind"] == "Coincident"),
            "saved Fusion origin relation",
        )
        expected = {f"fusion-sketch-entity-{key}" for key in relation["entity_ids"]}
        require(
            expected == {first.entity_id, second.entity_id},
            "wrong Fusion origin operands",
        )
    else:
        (relation,) = [item for item in witness["relations"] if item["type"] == 9]
        expected = tuple(tuple(operand["id"]) for operand in relation["entities"])
        require(
            rule.attributes["native_point_ids"] == expected,
            "wrong SOLIDWORKS origin operands",
        )
        unique(
            (
                entities[operand.entity_id]
                for operand in rule.references
                if entities[operand.entity_id].attributes.get(
                    "native_origin_feature_id"
                )
                is not None
            ),
            "owned SOLIDWORKS origin proxy",
        )
    return {
        "relation_id": rule.id,
        "operands": [first.entity_id, second.entity_id],
        "world_mm": points[0],
    }


def match_dimensions(
    document,
    sketch,
    frame,
    entities,
    perimeter,
    observed,
    witness,
    application,
    archive,
    tolerance,
):
    parameters = unique_index(
        document.parameters, lambda item: item.id, "public parameter"
    )
    rows = {}
    if application == "fusion":
        source = {item["parameter_name"]: item for item in archive["dimensions"]}
    else:
        feature = unique(
            (item for item in observed["feature_tree"] if item["name"] == sketch.name),
            "measured SOLIDWORKS parameter owner",
        )
        source = {item["name"]: item for item in feature["dimensions"]}
        measured_pairs = [item for item in witness["relations"] if item["type"] == 1]
        pairs = unique_index(
            measured_pairs,
            lambda item: tuple(tuple(operand["id"]) for operand in item["entities"]),
            "measured size operands",
        )
    for rule in sketch.constraints:
        if rule.parameter_id is None:
            continue
        parameter = parameters[rule.parameter_id]
        require(
            parameter.id in sketch.parameter_ids
            and parameter.name not in rows
            and rule.driving
            and not rule.suppressed
            and rule.provenance is not None,
            "public dimension is unowned, duplicated or lacks typed operands",
        )
        first, second = rule.references
        points = tuple(
            world(frame, bound_point(entities, operand)) for operand in rule.references
        )
        identity = unique(
            (key for key, edge in perimeter if edge_gap(points, edge) <= tolerance),
            "dimension endpoints identify their perimeter side",
        )
        measured = source[parameter.name]
        length = parameter_mm(parameter)
        if application == "fusion":
            require(
                measured["is_driving"]
                and measured["historical_dimension"]["driving"]
                and tuple(
                    f"fusion-sketch-entity-{key}" for key in measured["entity_ids"]
                )
                == (first.entity_id, second.entity_id)
                and identity
                == f"fusion-sketch-entity-{measured['ordered_operand_line_object_id']}",
                "public Fusion dimension differs from saved point handles or role",
            )
            expected_length = measured["value_mm"]
        else:
            require(
                measured["driven_state"] == 2 and rule.kind == "distance",
                "public SOLIDWORKS size differs from its saved driving distance",
            )
            ordered = pairs.pop(rule.attributes["native_point_ids"])
            for point, operand in zip(points, ordered["entities"], strict=True):
                x, y, z = operand["point_local_mm"]
                require(
                    z == 0, "measured dimension point lies outside the sketch plane"
                )
                same(
                    point,
                    world_xy(frame, x, y),
                    tolerance,
                    "public SOLIDWORKS ordered dimension position differs",
                )
            expected_length = measured["system_value"] * 1000
        require(
            abs(length - expected_length) <= tolerance
            and abs(math.dist(*points) - length) <= tolerance,
            "public dimension magnitude differs",
        )
        rows[parameter.name] = {
            "relation_id": rule.id,
            "parameter_id": parameter.id,
            "perimeter_id": identity,
            "operands_world_mm": points,
            "value_mm": length,
            "kind": rule.kind,
            "parameter_role": str(parameter.role),
            "parameter_unit": parameter.value.unit,
            "driving": rule.driving,
        }
    require(
        set(rows) == set(source) == {"width_mm", "height_mm"},
        "two owned public sizes required",
    )
    if application == "solidworks":
        require(not pairs, "public SOLIDWORKS size targets differ from reopen")
    return rows
