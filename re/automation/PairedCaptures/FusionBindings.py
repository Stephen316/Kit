CONSTRAINT_TARGETS = {
    "HorizontalConstraint": ("line",),
    "VerticalConstraint": ("line",),
    "CoincidentConstraint": ("point", "entity"),
    "MidPointConstraint": ("point", "midPointCurve"),
}
DIMENSION_TARGETS = {
    "SketchLinearDimension": ("entityOne", "entityTwo"),
    "SketchDiameterDimension": ("entity",),
}
CURVE_POINTS = {
    "SketchLine": ("startSketchPoint", "endSketchPoint"),
    "SketchArc": ("startSketchPoint", "endSketchPoint", "centerSketchPoint"),
    "SketchCircle": ("centerSketchPoint",),
}


def entity_reference(entity, entities):
    if entity is None:
        return {"status": "null", "entity_ids": []}
    matches = [identity for identity, candidate in entities if candidate == entity]
    return {
        "status": "resolved" if len(matches) == 1 else "unmapped" if not matches else "ambiguous",
        "type": entity.objectType,
        "entity_ids": matches,
    }


def read_targets(item, properties, entities):
    targets = {}
    for name in properties:
        try:
            targets[name] = entity_reference(getattr(item, name), entities)
        except Exception as error:
            targets[name] = {"status": "api_error", "error_type": type(error).__name__, "entity_ids": []}
    return targets


def bound_record(item, index, table, entities):
    kind = item.objectType.split("::")[-1]
    properties = table.get(kind)
    targets = read_targets(item, properties or (), entities)
    return {
        "index": index,
        "type": item.objectType,
        "binding_status": "unsupported_type" if properties is None else (
            "resolved" if all(target["status"] == "resolved" for target in targets.values()) else "unresolved"
        ),
        "targets": targets,
    }


def capture_sketch_bindings(sketch, point_mm):
    points = [(f"point:{index}", sketch.sketchPoints.item(index)) for index in range(sketch.sketchPoints.count)]
    if not any(candidate == sketch.originPoint for _, candidate in points):
        points.append(("point:origin", sketch.originPoint))
    curves = [(f"curve:{index}", sketch.sketchCurves.item(index)) for index in range(sketch.sketchCurves.count)]
    entities = points + curves
    dimensions = []
    for index in range(sketch.sketchDimensions.count):
        item = sketch.sketchDimensions.item(index)
        row = bound_record(item, index, DIMENSION_TARGETS, entities)
        parameter = item.parameter
        row.update({
            "driving": item.isDriving,
            "parameter": parameter.name if parameter is not None else None,
            "expression": parameter.expression if parameter is not None else None,
            "orientation": int(item.orientation) if row["type"].endswith("::SketchLinearDimension") else None,
        })
        dimensions.append(row)
    constraints = [
        bound_record(sketch.geometricConstraints.item(index), index, CONSTRAINT_TARGETS, entities)
        for index in range(sketch.geometricConstraints.count)
    ]
    return {
        "schema": 1,
        "identity_scope": "this sketch observation only; compare native objects, never entity-token strings",
        "points": [{
            "id": identity, "type": point.objectType, "world_mm": point_mm(point.worldGeometry),
            "is_origin": point == sketch.originPoint,
        } for identity, point in points],
        "curves": [{
            "id": identity, "type": curve.objectType,
            "points": read_targets(curve, CURVE_POINTS.get(curve.objectType.split("::")[-1], ()), entities),
            "point_binding_status": "supported_type" if curve.objectType.split("::")[-1] in CURVE_POINTS else "unsupported_type",
        } for identity, curve in curves],
        "constraints": constraints,
        "dimensions": dimensions,
        "unresolved_constraint_indices": [row["index"] for row in constraints if row["binding_status"] != "resolved"],
        "unresolved_dimension_indices": [row["index"] for row in dimensions if row["binding_status"] != "resolved"],
    }
