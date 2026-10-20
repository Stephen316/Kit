"""Observed clamped degree-five exact_int_cur cache with native form code1.

The sampled cache is a trimmed segment of a periodic sketch curve. Form1 is
retained without assigning a universal periodicity or closure enum meaning.
"""

import math

from decode_bspline import knot_vector, read_token, scalar_lists


def decode_exact_curve_form_one(record):
    tokens = record["tokens"]
    if (record["name"] != "intcurve-curve" or read_token(tokens, 3, "boolean_token")
            or tokens[4]["kind"] != "subtype_start"
            or read_token(tokens, 5, "entity_name") != "exact_int_cur"
            or read_token(tokens, 6, "integer") != 23100
            or read_token(tokens, 7, "enum") != 0
            or read_token(tokens, 8, "entity_name") != "nurbs"
            or read_token(tokens, 9, "integer") != 5
            or read_token(tokens, 10, "enum") != 1):
        raise ValueError("Unsupported observed degree-five exact curve form1 layout")
    degree = 5
    knots, compact, count, cursor = knot_vector(tokens, 12, read_token(tokens, 11, "integer"), degree)
    flat = [read_token(tokens, cursor+i, "double") for i in range(4*count)]
    if any(not math.isfinite(value) for value in flat):
        raise ValueError("Nonfinite exact curve form1 control value")
    cursor += 4*count
    trailer_start = cursor
    read_token(tokens, cursor, "double")
    if ([read_token(tokens, cursor+i, "entity_name") for i in range(1, 5)]
            != ["null_surface", "null_surface", "nullbs", "nullbs"]):
        raise ValueError("Unsupported exact curve form1 support-surface definitions")
    if read_token(tokens, cursor+5, "boolean_token") or read_token(tokens, cursor+6, "boolean_token"):
        raise ValueError("Unsupported exact curve form1 trailer flags")
    lists, cursor = scalar_lists(tokens, cursor+7, 4)
    for kind in ("boolean_token", "double", "boolean_token", "double", "enum", "enum", "subtype_end"):
        read_token(tokens, cursor, kind)
        cursor += 1
    interval = []
    for _ in range(2):
        finite = read_token(tokens, cursor, "boolean_token")
        cursor += 1
        if not finite:
            raise ValueError("Unobserved unbounded exact curve form1 interval")
        interval.append(read_token(tokens, cursor, "double"))
        cursor += 1
    domain = [knots[degree], knots[-degree-1]]
    if cursor != len(tokens) or not all(math.isclose(a, b, abs_tol=1e-12) for a, b in zip(domain, interval)):
        raise ValueError("Unsupported exact curve form1 trailer/interval")
    weights = flat[3::4]
    if any(weight <= 0 for weight in weights):
        raise ValueError("Unsupported exact curve form1 nonpositive weight")
    return {"degree": degree, "knots": knots, "stored_compact_knots": compact,
            "raw_control_points": [flat[i:i+3] for i in range(0, len(flat), 4)],
            "weights": weights, "is_rational": True, "parameter_domain": domain,
            "stored_form_code": 1, "stored_parameter_interval": interval,
            "stored_trailer_scalar_lists": lists, "stored_cache_trailer": tokens[trailer_start:],
            "is_periodic": None,
            "periodicity_status": "Form code1 retained; periodicity enum meaning unresolved. The sampled clamped cache is a trim segment, not the full periodic sketch curve.",
            "representation": "Observed clamped degree-five rational exact_int_cur form1 cache",
            "coordinate_scope": "Raw ASM controls; body transforms and units/context are not applied"}
