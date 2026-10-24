"""Observed ASM spline control grids; procedural definitions stay opaque."""

import math


# typed tokens prevent cache fields from silently changing their native meanings
def read_token(tokens, index, kind):
    item = tokens[index]
    if item["kind"] != kind:
        raise ValueError("Unexpected spline-cache token at field " + str(index))
    return item["value"]


# observed compact multiplicities preserve the full native parameter domain
def knot_vector(tokens, cursor, unique_count, degree):
    """Expand compact knots, including one omitted copy at each end."""
    if not 2 <= unique_count <= 100000 or not 1 <= degree <= 9:
        raise ValueError("Unsupported compact knot count/degree")
    pairs = []
    for _ in range(unique_count):
        value = read_token(tokens, cursor, "double")
        multiple = read_token(tokens, cursor + 1, "integer")
        if not 1 <= multiple <= degree:
            raise ValueError("Unsupported compact knot multiplicity")
        if pairs and value <= pairs[-1][0]:
            raise ValueError("Compact knot values are not strictly increasing")
        pairs.append((value, multiple))
        cursor += 2
    if pairs[0][1] != degree or pairs[-1][1] != degree:
        raise ValueError("Only observed clamped-end compact knot layouts supported")
    expanded = [v for v, m in pairs for _ in range(m)]
    full = [expanded[0]] + expanded + [expanded[-1]]
    controls = len(full) - degree - 1
    if controls <= degree or controls > 100000:
        raise ValueError("Unsupported spline control count")
    return full, pairs, controls, cursor


# bounded trailer lists preserve literal fields whose semantics remain unresolved
def scalar_lists(tokens, cursor, count):
    """Read observed length-prefixed lists without assigning them field meanings."""
    result = []
    for _ in range(count):
        size = read_token(tokens, cursor, "integer")
        if not 0 <= size <= 100000:
            raise ValueError("Unsupported spline trailer list size")
        result.append(
            [read_token(tokens, cursor + 1 + i, "double") for i in range(size)]
        )
        cursor += 1 + size
    return result, cursor


# strict native wrappers prevent procedural records from masquerading as control grids
def _decode_observed_bspline(record):
    tokens, name = record["tokens"], record["name"]
    if (
        len(tokens) > 6
        and tokens[4]["kind"] == "subtype_start"
        and tokens[5]["kind"] == "entity_name"
    ):
        if name == "spline-surface" and tokens[5]["value"] == "g2_blend_spl_sur":
            from decode_fillet_spline_caches import decode_g2_blend_surface_cache

            return decode_g2_blend_surface_cache(record)
        if name == "intcurve-curve" and tokens[5]["value"] == "int_int_cur":
            from decode_fillet_spline_caches import decode_intersection_curve_cache

            try:
                return decode_intersection_curve_cache(record)
            except (ValueError, IndexError):
                from decode_intersection_curve_variants import (
                    decode_intersection_curve_variants,
                )

                return decode_intersection_curve_variants(record)
        if name == "spline-surface" and tokens[5]["value"] == "srf_srf_v_bl_spl_sur":
            from decode_variable_blend_cache import decode_variable_blend_cache

            try:
                return decode_variable_blend_cache(record)
            except (ValueError, IndexError):
                from decode_rule_blend_cache import decode_rule_blend_cache

                try:
                    return decode_rule_blend_cache(record)
                except (ValueError, IndexError) as prior_error:
                    if (
                        str(prior_error)
                        != "Rule blend fallback requires captured unbounded spine"
                    ):
                        raise
                    from decode_interp_blend_cache import decode_interp_blend_cache

                    try:
                        return decode_interp_blend_cache(record)
                    except (ValueError, IndexError):
                        raise prior_error from None
        if name == "intcurve-curve" and tokens[5]["value"] == "spring_int_cur":
            from decode_spring_curve_cache import decode_spring_curve_cache

            try:
                return decode_spring_curve_cache(record)
            except (ValueError, IndexError):
                from decode_rule_blend_cache import decode_rule_blend_cache

                return decode_rule_blend_cache(record)
        if name == "spline-surface" and tokens[5]["value"] == "sweep_sur":
            from decode_sweep_surface_cache import decode_sweep_surface_cache

            return decode_sweep_surface_cache(record)
        if name == "spline-surface" and tokens[5]["value"] == "cyl_spl_sur":
            from decode_cylindrical_spline_cache import decode_cylindrical_spline_cache

            return decode_cylindrical_spline_cache(record)
        if name == "spline-surface" and tokens[5]["value"] == "sum_spl_sur":
            from decode_sum_surface_cache import decode_sum_surface_cache

            return decode_sum_surface_cache(record)
        if name == "intcurve-curve" and tokens[5]["value"] == "par_int_cur":
            from decode_parameter_curve_cache import decode_parameter_curve_cache

            try:
                return decode_parameter_curve_cache(record)
            except (ValueError, IndexError) as prior_error:
                if str(prior_error) != "Unsupported procedural cache field 10":
                    raise
                from decode_closed_parameter_curve_cache import (
                    decode_closed_parameter_curve_cache,
                )

                try:
                    return decode_closed_parameter_curve_cache(record)
                except (ValueError, IndexError):
                    raise prior_error from None
    if read_token(tokens, 3, "boolean_token") or tokens[4]["kind"] != "subtype_start":
        raise ValueError("Unsupported spline wrapper")
    procedural = read_token(tokens, 5, "entity_name")
    version = read_token(tokens, 6, "integer")
    if version != 23100:
        raise ValueError("Unsupported observed spline payload version")
    if name == "intcurve-curve" and procedural == "exact_int_cur":
        representation = read_token(tokens, 8, "entity_name")
        if (
            representation not in ("nubs", "nurbs")
            or read_token(tokens, 7, "enum") != 0
        ):
            raise ValueError("Unsupported exact curve representation")
        rational = representation == "nurbs"
        degree = read_token(tokens, 9, "integer")
        form = read_token(tokens, 10, "enum")
        if form == 1:
            from decode_exact_curve_form_one import decode_exact_curve_form_one

            return decode_exact_curve_form_one(record)
        if form == 2:
            from decode_exact_curve_form_two import decode_exact_curve_form_two

            return decode_exact_curve_form_two(record)
        if form != 0:
            raise ValueError("Unsupported spline curve form")
        knots, compact, count, cursor = knot_vector(
            tokens, 12, read_token(tokens, 11, "integer"), degree
        )
        stride = 4 if rational else 3
        flat = [read_token(tokens, cursor + i, "double") for i in range(stride * count)]
        cursor += stride * count
        trailer_start = cursor
        read_token(tokens, cursor, "double")
        if [read_token(tokens, cursor + i, "entity_name") for i in range(1, 5)] != [
            "null_surface",
            "null_surface",
            "nullbs",
            "nullbs",
        ]:
            raise ValueError(
                "Exact curve has unimplemented support-surface definitions"
            )
        if read_token(tokens, cursor + 5, "boolean_token") or read_token(
            tokens, cursor + 6, "boolean_token"
        ):
            raise ValueError("Unsupported exact curve trailer flags")
        cursor += 7
        lists, cursor = scalar_lists(tokens, cursor, 4)
        for expected_kind in (
            "boolean_token",
            "double",
            "boolean_token",
            "double",
            "enum",
            "enum",
            "subtype_end",
        ):
            read_token(tokens, cursor, expected_kind)
            cursor += 1
        interval = []
        for _ in range(2):
            finite = read_token(tokens, cursor, "boolean_token")
            cursor += 1
            interval.append(read_token(tokens, cursor, "double") if finite else None)
            cursor += int(finite)
        if cursor != len(tokens):
            raise ValueError("Unsupported exact curve cache trailer")
        weights = flat[3::4] if rational else []
        if any(not math.isfinite(w) or w <= 0 for w in weights):
            raise ValueError("Unsupported exact curve rational weights")
        return {
            "degree": degree,
            "knots": knots,
            "stored_compact_knots": compact,
            "raw_control_points": [
                flat[i : i + 3] for i in range(0, len(flat), stride)
            ],
            "weights": weights,
            "is_rational": rational,
            "parameter_domain": [knots[degree], knots[-degree - 1]],
            "stored_form_code": form,
            "stored_parameter_interval": interval,
            "stored_trailer_scalar_lists": lists,
            "stored_cache_trailer": tokens[trailer_start:],
            "representation": "Observed clamped exact_int_cur polynomial/rational curve; trailer scalar-list semantics remain partial",
        }
    if name == "spline-surface" and procedural == "exact_spl_sur":
        if read_token(tokens, 7, "enum") != 0:
            raise ValueError("Unsupported exact surface wrapper")
        start = 8
    elif name == "spline-surface" and procedural == "loft_spl_sur":
        starts = [
            i
            for i, t in enumerate(tokens)
            if t["kind"] == "entity_name" and t["value"] == "nubs"
        ]
        if len(starts) != 1:
            raise ValueError("Spline surface cache marker missing or ambiguous")
        start = starts[0]
    else:
        raise ValueError("Unsupported procedural spline subtype")
    rational = read_token(tokens, start, "entity_name") == "nurbs"
    if tokens[start]["value"] not in ("nubs", "nurbs"):
        raise ValueError("Unsupported spline surface grid representation")
    du, dv = read_token(tokens, start + 1, "integer"), read_token(
        tokens, start + 2, "integer"
    )
    header = start + 3
    if rational:
        if (
            procedural != "exact_spl_sur"
            or read_token(tokens, header, "entity_name") != "both"
        ):
            raise ValueError("Unsupported rational surface axis layout")
        header += 1
    flags = [read_token(tokens, header + i, "enum") for i in range(4)]
    expected_flags = [0, 0, 0, 0] if procedural == "exact_spl_sur" else [2, 0, 0, 0]
    if flags != expected_flags:
        raise ValueError("Unsupported observed surface axis flags")
    unique_u, unique_v = read_token(tokens, header + 4, "integer"), read_token(
        tokens, header + 5, "integer"
    )
    ku, compact_u, nu, cursor = knot_vector(tokens, header + 6, unique_u, du)
    kv, compact_v, nv, cursor = knot_vector(tokens, cursor, unique_v, dv)
    if nu * nv > 100000:
        raise ValueError("Surface control grid exceeds supported limit")
    stride = 4 if rational else 3
    flat = [read_token(tokens, cursor + i, "double") for i in range(stride * nu * nv)]
    cursor += stride * nu * nv
    lists = []
    if procedural == "exact_spl_sur":
        lists, suffix = scalar_lists(tokens, cursor + 1, 6)
        expected = (
            ["boolean_token"]
            + ["boolean_token", "double"] * 4
            + ["enum", "subtype_end"]
            + ["boolean_token"] * 4
        )
        if [t["kind"] for t in tokens[suffix:]] != expected:
            raise ValueError("Unsupported exact surface trailer")
    elif len(tokens) != cursor + 13 or tokens[cursor + 8]["kind"] != "subtype_end":
        raise ValueError("Unsupported loft surface cache trailer")
    controls = [flat[i : i + 3] for i in range(0, len(flat), stride)]
    normalized = [controls[v * nu + u] for u in range(nu) for v in range(nv)]
    weights = flat[3::4] if rational else []
    if any(not math.isfinite(w) or w <= 0 for w in weights):
        raise ValueError("Unsupported nonpositive/nonfinite rational weights")
    normalized_weights = (
        [weights[v * nu + u] for u in range(nu) for v in range(nv)] if rational else []
    )
    return {
        "degree_u": du,
        "degree_v": dv,
        "control_count_u": nu,
        "control_count_v": nv,
        "raw_control_points": normalized,
        "weights": normalized_weights,
        "is_rational": rational,
        "knots_u": ku,
        "knots_v": kv,
        "stored_compact_knots_u": compact_u,
        "stored_compact_knots_v": compact_v,
        "stored_control_grid_order": "u-fast",
        "normalized_control_grid_order": "v-fast",
        "parameter_domain_u": [ku[du], ku[-du - 1]],
        "parameter_domain_v": [kv[dv], kv[-dv - 1]],
        "stored_axis_flags": flags,
        "periodicity_status": "Native axis flags preserved; general form semantics unverified",
        "stored_cache_trailer_scalar": read_token(tokens, cursor, "double"),
        "stored_trailer_scalar_lists": lists,
        "stored_cache_trailer": tokens[cursor:],
        "procedural_subtype": procedural,
        "representation": (
            "Stored exact spline grid; observed clamped open polynomial/rational surface layout"
            if procedural == "exact_spl_sur"
            else "Stored non-rational loft NUBS approximation; original procedural loft is not reconstructed"
        ),
        "coordinate_scope": "Raw ASM control coordinates; body transforms and units/context not applied",
    }


# qualified variants extend cache coverage without relaxing the ordinary native grammar
def decode_bspline(record):
    try:
        return _decode_observed_bspline(record)
    except (ValueError, IndexError):
        ts = record["tokens"]
        if (
            record["name"] == "spline-surface"
            and len(ts) > 6
            and ts[5].get("value")
            in ("exact_spl_sur", "loft_spl_sur", "cl_loft_spl_sur")
        ):
            from decode_surface_cache_variants import decode_surface_cache_variants

            return decode_surface_cache_variants(record)
        raise


# shared projective evaluation preserves the original curve coordinates and rational weights
def evaluate_curve(cache, parameter):
    from decode_nurbs import evaluate_nurbs

    return evaluate_nurbs(
        {
            "degree": cache["degree"],
            "knots": cache["knots"],
            "control_points_cm": cache["raw_control_points"],
            "weights": cache["weights"],
            "parameter_domain": cache["parameter_domain"],
        },
        parameter,
    )


# validate tensor dimensions and both knot domains before homogeneous arithmetic
def _surface_operands(cache, u, v):
    from decode_nurbs import _curve_operands, _finite_number

    nu, nv = cache["control_count_u"], cache["control_count_v"]
    if (
        type(nu) is not int
        or type(nv) is not int
        or nu <= 0
        or nv <= 0
        or nu * nv != len(cache["raw_control_points"])
    ):
        raise ValueError("Inconsistent NURBS surface control counts")
    points = cache["raw_control_points"]
    weights = list(cache["weights"]) or [1.0] * len(points)
    if len(weights) != len(points) or any(len(point) != 3 for point in points):
        raise ValueError("Inconsistent NURBS surface control dimensions")
    for value in weights + [value for point in points for value in point]:
        _finite_number(value)
    if any(weight <= 0 for weight in weights):
        raise ValueError("NURBS surface weights must be positive")
    for axis, count, parameter in (("u", nu, u), ("v", nv, v)):
        _curve_operands(
            dict(
                degree=cache["degree_" + axis],
                knots=cache["knots_" + axis],
                control_points_cm=[[0.0]] * count,
                weights=[],
                parameter_domain=cache["parameter_domain_" + axis],
            ),
            parameter,
        )
    return nu, nv, points, weights


# preserve projective tensor values when finite source weights exceed floating intermediate range
def _decimal_surface(cache, u, v, nu, nv, points, weights):
    from decimal import DecimalException, localcontext
    from decode_nurbs import (
        _decimal_context,
        _decimal,
        _decimal_de_boor,
        _decimal_result,
    )

    try:
        with localcontext(_decimal_context(cache["degree_u"] + cache["degree_v"])):
            homogeneous = [
                [_decimal(value) * _decimal(weight) for value in point]
                + [_decimal(weight)]
                for point, weight in zip(points, weights)
            ]
            knots_u = [_decimal(value) for value in cache["knots_u"]]
            knots_v = [_decimal(value) for value in cache["knots_v"]]
            intermediate = [
                _decimal_de_boor(
                    [homogeneous[column * nv + row] for column in range(nu)],
                    cache["degree_u"],
                    knots_u,
                    _decimal(u),
                )
                for row in range(nv)
            ]
            result = _decimal_de_boor(
                intermediate, cache["degree_v"], knots_v, _decimal(v)
            )
            if result[-1] == 0:
                raise ValueError("NURBS surface homogeneous denominator is zero")
            return _decimal_result([value / result[-1] for value in result[:-1]])
    except (DecimalException, OverflowError, ZeroDivisionError) as error:
        raise ValueError("NURBS surface projective arithmetic is not finite") from error


# retain the ordinary tensor path and retry unsafe homogeneous products without global scaling
def evaluate_surface(cache, u, v):
    """Evaluate the complete rational tensor grid with finite projective arithmetic."""
    from decode_nurbs import _NumericRange, _float_de_boor, _float_homogeneous

    nu, nv, points, weights = _surface_operands(cache, u, v)
    try:
        homogeneous = _float_homogeneous(points, weights)
        intermediate = [
            _float_de_boor(
                [homogeneous[column * nv + row] for column in range(nu)],
                cache["degree_u"],
                cache["knots_u"],
                u,
            )
            for row in range(nv)
        ]
        result = _float_de_boor(intermediate, cache["degree_v"], cache["knots_v"], v)
        if result[3] == 0:
            raise _NumericRange()
        value = [coordinate / result[3] for coordinate in result[:3]]
        if not all(math.isfinite(coordinate) for coordinate in value):
            raise _NumericRange()
        return value
    except (_NumericRange, OverflowError, ZeroDivisionError):
        return _decimal_surface(cache, u, v, nu, nv, points, weights)
