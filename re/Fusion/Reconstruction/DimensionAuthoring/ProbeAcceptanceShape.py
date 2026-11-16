# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import math
import re
from collections import Counter

LENGTH_TOLERANCE_MM = 0.000001
CASES = {
    "origin": {
        "parameters": ("proof_width", "proof_height"),
        "original_mm": (17.75, 24.125),
        "edited_mm": (19.25, 26.75),
    },
    "owned": {
        "parameters": ("width_mm", "height_mm"),
        "original_mm": (40.0, 20.0),
        "edited_mm": (41.0, 23.0),
    },
}
CORNERS = ("anchor", "right", "diagonal", "upper")
EDGES = {
    frozenset(("anchor", "right")): "HorizontalConstraint",
    frozenset(("right", "diagonal")): "VerticalConstraint",
    frozenset(("diagonal", "upper")): "HorizontalConstraint",
    frozenset(("upper", "anchor")): "VerticalConstraint",
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def close_mm(actual, expected):
    return math.isclose(actual, expected, rel_tol=0.0, abs_tol=LENGTH_TOLERANCE_MM)


def point_matches(actual, expected):
    return len(actual) == len(expected) and all(
        close_mm(part, value) for part, value in zip(actual, expected, strict=True)
    )


def target_id(targets, name):
    target = targets[name]
    require(
        target["status"] == "resolved" and len(target["entity_ids"]) == 1,
        f"Native sketch operand is not unique: {name}",
    )
    return target["entity_ids"][0]


def perimeter(sketch, bindings, width, height):
    expected = dict(
        zip(
            CORNERS,
            ((0, 0, 0), (width, 0, 0), (width, height, 0), (0, height, 0)),
            strict=True,
        )
    )
    points = {row["id"]: row for row in bindings["points"]}
    origins = [row for row in points.values() if row["is_origin"]]
    require(
        len(origins) == 1 and point_matches(origins[0]["world_mm"], expected["anchor"]),
        "The distinct native sketch origin did not resolve at the anchor",
    )
    origin = origins[0]["id"]
    require(
        len(sketch["curves"]) == len(bindings["curves"]) == 4
        and all(
            row["type"] == "SketchLine"
            and not row["construction"]
            and not row["fixed"]
            and not row["reference"]
            for row in sketch["curves"]
        ),
        "The editable profile does not contain four ordinary lines",
    )
    corner_ids, edge_types, logical_edges = {}, {}, set()
    for row in bindings["curves"]:
        corners = []
        for name in ("startSketchPoint", "endSketchPoint"):
            point = target_id(row["points"], name)
            matches = [
                key
                for key, position in expected.items()
                if point_matches(points[point]["world_mm"], position)
            ]
            require(
                point != origin and len(matches) == 1,
                "Profile endpoint or origin ownership differs",
            )
            corner = matches[0]
            require(
                corner_ids.setdefault(corner, point) == point,
                f"Disconnected perimeter at {corner}",
            )
            corners.append(corner)
        edge = frozenset(corners)
        require(
            edge in EDGES and edge not in logical_edges,
            "Invalid or duplicate rectangle boundary",
        )
        logical_edges.add(edge)
        edge_types[row["id"]] = EDGES[edge]
    require(logical_edges == set(EDGES), "The perimeter is missing a rectangle edge")
    return origin, corner_ids, edge_types


def check_relations(bindings, origin, corners, edge_types):
    constraints = bindings["constraints"]
    kinds = [row["type"].split("::")[-1] for row in constraints]
    require(
        Counter(kinds)
        == {
            "HorizontalConstraint": 2,
            "VerticalConstraint": 2,
            "CoincidentConstraint": 1,
        }
        and not bindings["unresolved_constraint_indices"],
        "Native geometric relations or resolved operands differ",
    )
    constrained_edges = set()
    for kind, row in zip(kinds, constraints, strict=True):
        targets = row["targets"]
        if kind == "CoincidentConstraint":
            actual = {target_id(targets, name) for name in ("point", "entity")}
            require(
                actual == {origin, corners["anchor"]},
                "Coincidence does not join the perimeter anchor to the distinct origin",
            )
        else:
            edge = target_id(targets, "line")
            require(
                edge_types[edge] == kind and edge not in constrained_edges,
                "An axis constraint is duplicated or attached to the wrong perimeter edge",
            )
            constrained_edges.add(edge)
    require(
        constrained_edges == set(edge_types),
        "A perimeter line lacks its axis constraint",
    )


def check_dimensions(snapshot, bindings, kind, values, corners, orientations):
    dimensions = bindings["dimensions"]
    rows = snapshot["parameters"]
    parameters = {row["name"]: row for row in rows}
    names = CASES[kind]["parameters"]
    require(
        len(dimensions) == 2
        and not bindings["unresolved_dimension_indices"]
        and len(parameters) == len(rows)
        and set(names) <= set(parameters),
        "Native driving dimensions or their parameter names are missing or ambiguous",
    )
    seen = set()
    for dimension in dimensions:
        require(
            dimension["driving"]
            and dimension["type"].endswith("::SketchLinearDimension"),
            "One of the two native size dimensions is not driving",
        )
        orientation = dimension["orientation"]
        require(
            orientation in orientations and orientation not in seen,
            "Native size dimension orientation differs",
        )
        seen.add(orientation)
        axis, endpoint = orientations[orientation]
        expected = values[axis]
        driver = parameters[names[axis]]
        model = parameters[dimension["parameter"]]
        points = {
            target_id(dimension["targets"], name) for name in ("entityOne", "entityTwo")
        }
        require(
            points == {corners["anchor"], corners[endpoint]},
            "Size dimension is attached to the wrong endpoints",
        )
        require(
            model["kind"] == "ModelParameter"
            and close_mm(model["value_internal"] * 10.0, expected)
            and close_mm(driver["value_internal"] * 10.0, expected),
            "Measured native size or dimension parameter differs",
        )
        if kind == "owned":
            require(
                model == driver
                and re.fullmatch(r"[0-9]+(?:\.[0-9]+)?\s+mm", driver["expression"]),
                "Size parameter is not the sketch-owned direct driver",
            )
        else:
            require(
                model == driver or model["name"] in driver["dependents"],
                "The size dimension has no native dependency on its declared driver",
            )
    if kind == "owned":
        require(
            set(parameters) == set(names),
            "Sketch-owned candidate contains an additional parameter",
        )


def check_rectangle(snapshot, kind, values, orientations):
    require(
        snapshot["design_type"] == "parametric"
        and snapshot["body_count"] == 0
        and len(snapshot["feature_tree"]) == len(snapshot["sketches"]) == 1,
        "The candidate is not a single live sketch without solid bodies",
    )
    feature = snapshot["feature_tree"][0]
    require(
        feature["type"] == "Sketch"
        and feature["health"]["state"] == "healthy"
        and not feature["health"]["message"]
        and not feature["suppressed"]
        and not feature["rolled_back"],
        "The rectangle feature is unhealthy or inactive",
    )
    sketch = snapshot["sketches"][0]
    width, height = values
    areas = sketch["profile_areas_mm2"]
    require(
        sketch["fully_constrained"] is True
        and len(areas) == 1
        and math.isclose(
            areas[0],
            width * height,
            rel_tol=0.0,
            abs_tol=(width + height + LENGTH_TOLERANCE_MM) * LENGTH_TOLERANCE_MM,
        ),
        "The closed fully constrained native profile has the wrong area",
    )
    bindings = sketch["bindings"]
    origin, corners, edge_types = perimeter(sketch, bindings, width, height)
    check_relations(bindings, origin, corners, edge_types)
    check_dimensions(snapshot, bindings, kind, values, corners, orientations)
