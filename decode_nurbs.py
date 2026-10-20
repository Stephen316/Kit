"""Bounded readers for observed sketch NURBS records and continuations."""

import math
import struct

from decode_sketch import attributes, numbers, reference, same


def numeric_array(body, cursor, dimensions=1):
    count, capacity, item_size = struct.unpack_from("<III", body, cursor)
    if not 0 <= count <= capacity <= 100000 or item_size != 8:
        raise ValueError("Unsupported NURBS array header")
    values = numbers(body, cursor+12, count*dimensions)
    return values, cursor+12+count*dimensions*8


def nurbs_geometry(body, cursor):
    if body[cursor] != 1 or body[cursor+1] not in (0, 1):
        raise ValueError("Unsupported NURBS flags")
    periodic = bool(body[cursor+1])
    degree = struct.unpack_from("<I", body, cursor+2)[0]
    tolerance = numbers(body, cursor+6, 1)[0]
    if not 1 <= degree <= 9 or not 0 < tolerance < 1:
        raise ValueError("Unsupported NURBS degree/tolerance")
    knots, cursor = numeric_array(body, cursor+14)
    weights, cursor = numeric_array(body, cursor)
    flat, cursor = numeric_array(body, cursor, 3)
    points = [flat[i:i+3] for i in range(0, len(flat), 3)]
    if len(points) <= degree or len(knots) != len(points)+degree+1:
        raise ValueError("Inconsistent NURBS control point/knot counts")
    if any(a > b for a, b in zip(knots, knots[1:])) or knots[degree] >= knots[-degree-1]:
        raise ValueError("Invalid NURBS knot domain")
    if weights and (len(weights) != len(points) or any(w <= 0 for w in weights)):
        raise ValueError("Unsupported NURBS weights")
    return {"degree": degree, "knots": knots, "control_points_cm": points,
            "weights": weights, "is_rational": bool(weights), "is_periodic": periodic,
            "parameter_domain": [knots[degree], knots[-degree-1]],
            "representation": "Stored sketch-local NURBS; no fitted-point approximation"}, cursor


def evaluate_nurbs(geometry, parameter):
    """Evaluate the full stored knot vector using homogeneous de Boor recursion."""
    degree, knots = geometry["degree"], geometry["knots"]
    points = geometry["control_points_cm"]
    weights = geometry["weights"] or [1.] * len(points)
    start, end = geometry["parameter_domain"]
    if not math.isfinite(parameter) or not start <= parameter <= end:
        raise ValueError("Parameter outside the stored NURBS domain")
    span = len(points)-1 if parameter == end else next(
        i for i in range(degree, len(points)) if knots[i] <= parameter < knots[i+1])
    values = [[v*weights[i] for v in points[i]]+[weights[i]]
              for i in range(span-degree, span+1)]
    for level in range(1, degree+1):
        for j in range(degree, level-1, -1):
            index = span-degree+j
            denominator = knots[index+degree-level+1]-knots[index]
            alpha = (parameter-knots[index])/denominator if denominator else 0.
            values[j] = [(1-alpha)*a+alpha*b for a, b in zip(values[j-1], values[j])]
    return [v/values[degree][-1] for v in values[degree][:-1]]


def point_in_sketch(entities, identity, owner):
    point = entities[identity]
    if point["kind"] != "Point" or point["sketch_object_id"] != owner:
        raise ValueError("NURBS point reference does not resolve in this sketch")
    return point["position_cm"]


def fitted_point_ids(data, records, chunk, object_id, start_id, end_id, periodic):
    collection_id = reference(chunk, 28)
    collections = []
    for container in records:
        if container.object_id != collection_id:
            continue
        slots = data[container.body:container.end]
        if len(slots) < 18 or slots[:2] != b"\0\0":
            continue
        count = struct.unpack_from("<I", slots, 2)[0]
        if len(slots) != 18+count*11 or reference(slots, len(slots)-11) != object_id:
            continue
        collections.append([reference(slots, 6+i*11) for i in range(count)])
    if len(collections) != 1:
        raise ValueError("Fitted spline point list is unresolved")
    return [start_id]+collections[0]+([] if periodic else [end_id])


def decode_spline(data, records, record, props, continuations, sketches, entities):
    candidates = []
    for continuation in continuations:
        chunk = data[continuation.body:continuation.end]
        try:
            owner = reference(chunk, len(chunk)-11)
            if owner not in sketches or len(chunk) < 198:
                continue
            shape, end = nurbs_geometry(chunk, 61)
            if len(chunk)-end != 123:
                continue
            start_id, end_id = reference(chunk, 50), reference(chunk, 39)
            start = point_in_sketch(entities, start_id, owner)
            finish = point_in_sketch(entities, end_id, owner)
            if not same(start, shape["control_points_cm"][0]) or not same(finish, shape["control_points_cm"][-1]):
                raise ValueError("Spline endpoint references disagree with geometry")
            stored_degree = struct.unpack_from("<I", chunk, 23)[0]
            mode = chunk[27]
            if mode not in (0, 1) or stored_degree not in (0, 3, 5):
                continue
            if stored_degree and stored_degree != shape["degree"]:
                continue
            kind = "ControlPointSpline" if stored_degree else "FixedSpline" if mode else "FittedSpline"
            item = {"kind": kind, "object_id": record.object_id, "entity_tag": props["crv_primary_id"],
                    "sketch_object_id": owner, "record_offset": record.start,
                    "geometry_record_offset": continuation.start,
                    "start_point_id": start_id, "end_point_id": end_id,
                    "start_cm": start, "end_cm": finish, "nurbs": shape,
                    "state_status": "Spline construction/fixed state not decoded"}
            if kind == "FittedSpline":
                fit_ids = fitted_point_ids(data, records, chunk, record.object_id, start_id, end_id, shape["is_periodic"])
                item.update(fit_point_ids=fit_ids,
                            fit_points_cm=[point_in_sketch(entities, i, owner) for i in fit_ids])
            candidates.append(item)
        except (ValueError, KeyError, struct.error, IndexError):
            continue
    if len(candidates) != 1:
        raise ValueError("Split spline geometry is unresolved or ambiguous")
    return candidates[0]


def decode_splines(data, records, sketches, entities):
    decoded, skipped = {}, []
    for record in records:
        body = data[record.body:record.end]
        props = {}
        try:
            if body[:2] != b"\0\x01":
                continue
            props, cursor = attributes(body, 2)
            if props.get("EntityGenesis") not in (2, 64) or "crv_primary_id" not in props:
                continue
            if props.get("crv_secondary_id") != 0:
                continue
            same_id = [r for r in records if r.object_id == record.object_id and r.start != record.start]
            if body[cursor:] == b"\xff"*8:
                decoded[record.object_id] = decode_spline(data, records, record, props, same_id, sketches, entities)
                continue
            # Conics use a separate style/owner continuation and rational quadratic geometry.
            styles = []
            for style in same_id:
                chunk = data[style.body:style.end]
                if len(chunk) == 53:
                    owner = reference(chunk, 42)
                    if owner in sketches:
                        styles.append((chunk, owner))
            if len(styles) != 1:
                continue
            style, owner = styles[0]
            rho = numbers(body, cursor, 1)[0]
            shape, end = nurbs_geometry(body, cursor+19)
            if len(body)-end != 61 or shape["degree"] != 2 or not 0 < rho < 1:
                raise ValueError("Unsupported conic layout")
            apex_id, end_id, start_id = reference(body, end+26), reference(body, end+37), reference(body, end+49)
            points = [point_in_sketch(entities, identity, owner) for identity in (start_id, apex_id, end_id)]
            if not all(same(a, b) for a, b in zip(points, shape["control_points_cm"])):
                raise ValueError("Conic references disagree with NURBS control points")
            if not same(shape["weights"], [1, rho/(1-rho), 1]):
                raise ValueError("Conic rho disagrees with NURBS weights")
            decoded[record.object_id] = {
                "kind": "Conic", "object_id": record.object_id, "entity_tag": props["crv_primary_id"],
                "sketch_object_id": owner, "record_offset": record.start, "rho": rho,
                "start_point_id": start_id, "end_point_id": end_id, "apex_point_id": apex_id,
                "start_cm": points[0], "end_cm": points[2], "apex_cm": points[1], "nurbs": shape,
                "state_status": "Conic construction/fixed state not decoded",
            }
        except (ValueError, KeyError, struct.error, IndexError) as error:
            if "crv_primary_id" in props:
                skipped.append({"object_id": record.object_id, "reason": str(error)})
    return decoded, skipped
