"""Bounded readers for observed sketch NURBS records and continuations."""

import math
import struct
from decimal import Context, Decimal, DecimalException, localcontext
import sys

from decode_sketch import attributes, numbers, reference, same


# native array bounds prevent corrupted counts from escaping the stored geometry record
def numeric_array(body, cursor, dimensions=1):
    count, capacity, item_size = struct.unpack_from("<III", body, cursor)
    if not 0 <= count <= capacity <= 100000 or item_size != 8:
        raise ValueError("Unsupported NURBS array header")
    values = numbers(body, cursor + 12, count * dimensions)
    return values, cursor + 12 + count * dimensions * 8


# native shape invariants protect evaluation from inconsistent knot and control arrays
def nurbs_geometry(body, cursor):
    if body[cursor] != 1 or body[cursor + 1] not in (0, 1):
        raise ValueError("Unsupported NURBS flags")
    periodic = bool(body[cursor + 1])
    degree = struct.unpack_from("<I", body, cursor + 2)[0]
    tolerance = numbers(body, cursor + 6, 1)[0]
    if not 1 <= degree <= 9 or not 0 < tolerance < 1:
        raise ValueError("Unsupported NURBS degree/tolerance")
    knots, cursor = numeric_array(body, cursor + 14)
    weights, cursor = numeric_array(body, cursor)
    flat, cursor = numeric_array(body, cursor, 3)
    points = [flat[i : i + 3] for i in range(0, len(flat), 3)]
    if len(points) <= degree or len(knots) != len(points) + degree + 1:
        raise ValueError("Inconsistent NURBS control point/knot counts")
    if (
        any(a > b for a, b in zip(knots, knots[1:]))
        or knots[degree] >= knots[-degree - 1]
    ):
        raise ValueError("Invalid NURBS knot domain")
    if weights and (len(weights) != len(points) or any(w <= 0 for w in weights)):
        raise ValueError("Unsupported NURBS weights")
    return {
        "degree": degree,
        "knots": knots,
        "control_points_cm": points,
        "weights": weights,
        "is_rational": bool(weights),
        "is_periodic": periodic,
        "parameter_domain": [knots[degree], knots[-degree - 1]],
        "representation": "Stored sketch-local NURBS; no fitted-point approximation",
    }, cursor


# signal arithmetic range loss without treating valid rational geometry as malformed
class _NumericRange(ArithmeticError):
    pass


# a conservative precision floor protects ordinary tensor calculations across binary64 exponent extremes
_DECIMAL_PRECISION = 16384


# higher degrees need additional exponent headroom without narrowing the existing evaluator contract
def _decimal_context(order):
    return Context(
        prec=max(_DECIMAL_PRECISION, (order + 6) * 650 + 128), Emin=-999999, Emax=999999
    )


# reject malformed numeric operands before selecting float or decimal arithmetic
def _finite_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("NURBS operands must be finite numbers")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise ValueError("NURBS operands must be finite numbers")
    return value


# retain degree zero intermediate curves while validating complete evaluator dimensions
def _curve_operands(geometry, parameter):
    degree, knots = geometry["degree"], list(geometry["knots"])
    points = geometry["control_points_cm"]
    weights = list(geometry["weights"]) or [1.0] * len(points)
    if (
        type(degree) is not int
        or degree < 0
        or len(points) <= degree
        or len(knots) != len(points) + degree + 1
        or len(weights) != len(points)
    ):
        raise ValueError("Inconsistent NURBS evaluator counts or degree")
    dimension = len(points[0])
    if not dimension or any(len(point) != dimension for point in points):
        raise ValueError("Inconsistent NURBS evaluator point dimensions")
    for value in knots + weights + [value for point in points for value in point]:
        _finite_number(value)
    if any(weight <= 0 for weight in weights) or any(
        a > b for a, b in zip(knots, knots[1:])
    ):
        raise ValueError("Invalid NURBS evaluator weights or knots")
    start, end = geometry["parameter_domain"]
    _finite_number(start)
    _finite_number(end)
    _finite_number(parameter)
    if (
        not start < end
        or start < knots[degree]
        or end > knots[-degree - 1]
        or not start <= parameter <= end
    ):
        raise ValueError("Parameter outside the stored NURBS domain")
    return degree, knots, points, weights


# select a supported knot span without converting repeated knots into new geometry
def _span(degree, knots, count, parameter):
    if parameter == knots[count]:
        return count - 1
    for index in range(degree, count):
        if knots[index] <= parameter < knots[index + 1]:
            return index
    raise ValueError("Parameter has no supported NURBS knot span")


# detect subnormal or overflowing intermediate values before they lose projective information
def _float_intermediate(value):
    if not math.isfinite(value) or value and abs(value) < sys.float_info.min:
        raise _NumericRange()
    return value


# preserve ordinary products while detecting a nonzero value rounded to zero
def _float_product(a, b):
    value = _float_intermediate(a * b)
    if value == 0 and a != 0 and b != 0:
        raise _NumericRange()
    return value


# build homogeneous controls only when their floating products preserve finite information
def _float_homogeneous(points, weights):
    return [
        [_float_product(value, weight) for value in point]
        + [_float_intermediate(weight)]
        for point, weight in zip(points, weights)
    ]


# preserve the original de boor operation order for ordinary finite arithmetic
def _float_de_boor(points, degree, knots, parameter):
    span = _span(degree, knots, len(points), parameter)
    values = [list(points[index]) for index in range(span - degree, span + 1)]
    for level in range(1, degree + 1):
        for j in range(degree, level - 1, -1):
            index = span - degree + j
            denominator = _float_intermediate(
                knots[index + degree - level + 1] - knots[index]
            )
            numerator = _float_intermediate(parameter - knots[index])
            alpha = numerator / denominator if denominator else 0.0
            _float_intermediate(alpha)
            if denominator and (
                (alpha == 0 and numerator != 0)
                or (alpha == 1 and parameter != knots[index + degree - level + 1])
            ):
                raise _NumericRange()
            values[j] = [
                _float_intermediate(
                    _float_product(1 - alpha, a) + _float_product(alpha, b)
                )
                for a, b in zip(values[j - 1], values[j])
            ]
    return values[degree]


# convert binary64 operands exactly before performing extended range projective arithmetic
def _decimal(value):
    return Decimal.from_float(value) if isinstance(value, float) else Decimal(value)


# use the same complete knot recursion without binary64 underflow or overflow
def _decimal_de_boor(points, degree, knots, parameter):
    span = _span(degree, knots, len(points), parameter)
    values = [list(points[index]) for index in range(span - degree, span + 1)]
    for level in range(1, degree + 1):
        for j in range(degree, level - 1, -1):
            index = span - degree + j
            denominator = knots[index + degree - level + 1] - knots[index]
            alpha = (
                (parameter - knots[index]) / denominator if denominator else Decimal(0)
            )
            values[j] = [
                (1 - alpha) * a + alpha * b for a, b in zip(values[j - 1], values[j])
            ]
    return values[degree]


# return finite binary64 results or report an unrepresentable derived value explicitly
def _decimal_result(values):
    result = [float(value) for value in values]
    if not all(math.isfinite(value) for value in result):
        raise ValueError("Derived NURBS value exceeds the finite numeric range")
    return result


# recover rational values using extended exponent range without globally rescaling weights
def _decimal_nurbs(points, weights, degree, knots, parameter, derivative=False):
    try:
        with localcontext(_decimal_context(degree)):
            decimal_knots = [_decimal(value) for value in knots]
            decimal_parameter = _decimal(parameter)
            homogeneous = [
                [_decimal(value) * _decimal(weight) for value in point]
                + [_decimal(weight)]
                for point, weight in zip(points, weights)
            ]
            value = _decimal_de_boor(
                homogeneous, degree, decimal_knots, decimal_parameter
            )
            if not value[-1]:
                raise ValueError("NURBS homogeneous denominator is zero")
            if not derivative:
                return _decimal_result(
                    [coordinate / value[-1] for coordinate in value[:-1]]
                )
            controls = []
            for index in range(len(points) - 1):
                denominator = (
                    decimal_knots[index + degree + 1] - decimal_knots[index + 1]
                )
                if denominator <= 0:
                    raise ValueError(
                        "Unsupported repeated-knot derivative control interval"
                    )
                controls.append(
                    [
                        degree * (b - a) / denominator
                        for a, b in zip(homogeneous[index], homogeneous[index + 1])
                    ]
                )
            tangent = _decimal_de_boor(
                controls, degree - 1, decimal_knots[1:-1], decimal_parameter
            )
            denominator = value[-1] * value[-1]
            return _decimal_result(
                [
                    (d * value[-1] - coordinate * tangent[-1]) / denominator
                    for coordinate, d in zip(value[:-1], tangent[:-1])
                ]
            )
    except (DecimalException, OverflowError, ZeroDivisionError) as error:
        raise ValueError("NURBS projective arithmetic is not finite") from error


# evaluate source curves with the ordinary float path and an exact input range fallback
def evaluate_nurbs(geometry, parameter):
    """Evaluate the stored knot vector without losing a common rational scale."""
    degree, knots, points, weights = _curve_operands(geometry, parameter)
    try:
        homogeneous = _float_homogeneous(points, weights)
        value = _float_de_boor(homogeneous, degree, knots, parameter)
        if value[-1] == 0:
            raise _NumericRange()
        result = [coordinate / value[-1] for coordinate in value[:-1]]
        if not all(math.isfinite(coordinate) for coordinate in result):
            raise _NumericRange()
        return result
    except (_NumericRange, OverflowError, ZeroDivisionError):
        return _decimal_nurbs(points, weights, degree, knots, parameter)


# differentiate homogeneous curves before applying the rational quotient rule safely
def evaluate_nurbs_derivative(geometry, parameter):
    """Evaluate the exact rational first derivative with range-safe intermediates."""
    degree, knots, points, weights = _curve_operands(geometry, parameter)
    if degree == 0:
        raise ValueError("Degree-zero NURBS derivative is not qualified")
    try:
        homogeneous = _float_homogeneous(points, weights)
        value = _float_de_boor(homogeneous, degree, knots, parameter)
        controls = []
        for index in range(len(points) - 1):
            denominator = _float_intermediate(
                knots[index + degree + 1] - knots[index + 1]
            )
            if denominator <= 0:
                raise ValueError(
                    "Unsupported repeated-knot derivative control interval"
                )
            controls.append(
                [
                    _float_intermediate(
                        _float_product(degree, _float_intermediate(b - a)) / denominator
                    )
                    for a, b in zip(homogeneous[index], homogeneous[index + 1])
                ]
            )
        tangent = _float_de_boor(controls, degree - 1, knots[1:-1], parameter)
        denominator = _float_intermediate(value[-1] ** 2)
        if denominator == 0:
            raise _NumericRange()
        result = [
            _float_intermediate(
                (_float_product(d, value[-1]) - _float_product(coordinate, tangent[-1]))
                / denominator
            )
            for coordinate, d in zip(value[:-1], tangent[:-1])
        ]
        return result
    except (_NumericRange, OverflowError, ZeroDivisionError):
        return _decimal_nurbs(
            points, weights, degree, knots, parameter, derivative=True
        )


# explicit sketch ownership prevents curve endpoints from borrowing unrelated points
def point_in_sketch(entities, identity, owner):
    point = entities[identity]
    if point["kind"] != "Point" or point["sketch_object_id"] != owner:
        raise ValueError("NURBS point reference does not resolve in this sketch")
    return point["position_cm"]


# ordered point ownership preserves the distinction between fitted inputs and control geometry
def fitted_point_ids(data, records, chunk, object_id, start_id, end_id, periodic):
    collection_id = reference(chunk, 28)
    collections = []
    for container in records:
        if container.object_id != collection_id:
            continue
        slots = data[container.body : container.end]
        if len(slots) < 18 or slots[:2] != b"\0\0":
            continue
        count = struct.unpack_from("<I", slots, 2)[0]
        if (
            len(slots) != 18 + count * 11
            or reference(slots, len(slots) - 11) != object_id
        ):
            continue
        collections.append([reference(slots, 6 + i * 11) for i in range(count)])
    if len(collections) != 1:
        raise ValueError("Fitted spline point list is unresolved")
    return [start_id] + collections[0] + ([] if periodic else [end_id])


# reciprocal continuations preserve native endpoint and sketch identity before geometry is published
def decode_spline(data, records, record, props, continuations, sketches, entities):
    candidates = []
    for continuation in continuations:
        chunk = data[continuation.body : continuation.end]
        try:
            owner = reference(chunk, len(chunk) - 11)
            if owner not in sketches or len(chunk) < 198:
                continue
            shape, end = nurbs_geometry(chunk, 61)
            if len(chunk) - end != 123:
                continue
            start_id, end_id = reference(chunk, 50), reference(chunk, 39)
            start = point_in_sketch(entities, start_id, owner)
            finish = point_in_sketch(entities, end_id, owner)
            if not same(start, shape["control_points_cm"][0]) or not same(
                finish, shape["control_points_cm"][-1]
            ):
                raise ValueError("Spline endpoint references disagree with geometry")
            stored_degree = struct.unpack_from("<I", chunk, 23)[0]
            mode = chunk[27]
            if mode not in (0, 1) or stored_degree not in (0, 3, 5):
                continue
            if stored_degree and stored_degree != shape["degree"]:
                continue
            kind = (
                "ControlPointSpline"
                if stored_degree
                else "FixedSpline" if mode else "FittedSpline"
            )
            item = {
                "kind": kind,
                "object_id": record.object_id,
                "entity_tag": props["crv_primary_id"],
                "sketch_object_id": owner,
                "record_offset": record.start,
                "geometry_record_offset": continuation.start,
                "start_point_id": start_id,
                "end_point_id": end_id,
                "start_cm": start,
                "end_cm": finish,
                "nurbs": shape,
                "state_status": "Spline construction/fixed state not decoded",
            }
            if kind == "FittedSpline":
                fit_ids = fitted_point_ids(
                    data,
                    records,
                    chunk,
                    record.object_id,
                    start_id,
                    end_id,
                    shape["is_periodic"],
                )
                item.update(
                    fit_point_ids=fit_ids,
                    fit_points_cm=[
                        point_in_sketch(entities, i, owner) for i in fit_ids
                    ],
                )
            candidates.append(item)
        except (ValueError, KeyError, struct.error, IndexError):
            continue
    if len(candidates) != 1:
        raise ValueError("Split spline geometry is unresolved or ambiguous")
    return candidates[0]


# typed geometry records preserve unsupported sources without substituting approximated curves
def decode_splines(data, records, sketches, entities):
    """Preserve spline sources and the separate style continuations of conics."""
    decoded, skipped = {}, []
    for record in records:
        body = data[record.body : record.end]
        props = {}
        try:
            if body[:2] != b"\0\x01":
                continue
            props, cursor = attributes(body, 2)
            if (
                props.get("EntityGenesis") not in (2, 64)
                or "crv_primary_id" not in props
            ):
                continue
            if props.get("crv_secondary_id") != 0:
                continue
            same_id = [
                r
                for r in records
                if r.object_id == record.object_id and r.start != record.start
            ]
            if body[cursor:] == b"\xff" * 8:
                decoded[record.object_id] = decode_spline(
                    data, records, record, props, same_id, sketches, entities
                )
                continue
            styles = []
            for style in same_id:
                chunk = data[style.body : style.end]
                if len(chunk) == 53:
                    owner = reference(chunk, 42)
                    if owner in sketches:
                        styles.append((chunk, owner))
            if len(styles) != 1:
                continue
            style, owner = styles[0]
            rho = numbers(body, cursor, 1)[0]
            shape, end = nurbs_geometry(body, cursor + 19)
            if len(body) - end != 61 or shape["degree"] != 2 or not 0 < rho < 1:
                raise ValueError("Unsupported conic layout")
            apex_id, end_id, start_id = (
                reference(body, end + 26),
                reference(body, end + 37),
                reference(body, end + 49),
            )
            points = [
                point_in_sketch(entities, identity, owner)
                for identity in (start_id, apex_id, end_id)
            ]
            if not all(same(a, b) for a, b in zip(points, shape["control_points_cm"])):
                raise ValueError("Conic references disagree with NURBS control points")
            if not same(shape["weights"], [1, rho / (1 - rho), 1]):
                raise ValueError("Conic rho disagrees with NURBS weights")
            decoded[record.object_id] = {
                "kind": "Conic",
                "object_id": record.object_id,
                "entity_tag": props["crv_primary_id"],
                "sketch_object_id": owner,
                "record_offset": record.start,
                "rho": rho,
                "start_point_id": start_id,
                "end_point_id": end_id,
                "apex_point_id": apex_id,
                "start_cm": points[0],
                "end_cm": points[2],
                "apex_cm": points[1],
                "nurbs": shape,
                "state_status": "Conic construction/fixed state not decoded",
            }
        except (ValueError, KeyError, struct.error, IndexError) as error:
            if "crv_primary_id" in props:
                skipped.append({"object_id": record.object_id, "reason": str(error)})
    return decoded, skipped
