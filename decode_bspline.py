"""Observed non-rational ASM spline caches; procedural definitions stay opaque."""


def read_token(tokens, index, kind):
    item = tokens[index]
    if item["kind"] != kind:
        raise ValueError("Unexpected spline-cache token at field "+str(index))
    return item["value"]


def knot_vector(tokens, cursor, unique_count, degree):
    if not 2 <= unique_count <= 100000 or not 1 <= degree <= 9:
        raise ValueError("Unsupported compact knot count/degree")
    pairs = []
    for _ in range(unique_count):
        value = read_token(tokens, cursor, "double")
        multiple = read_token(tokens, cursor+1, "integer")
        if not 1 <= multiple <= degree:
            raise ValueError("Unsupported compact knot multiplicity")
        if pairs and value <= pairs[-1][0]:
            raise ValueError("Compact knot values are not strictly increasing")
        pairs.append((value, multiple))
        cursor += 2
    if pairs[0][1] != degree or pairs[-1][1] != degree:
        raise ValueError("Only observed clamped-end compact knot layouts supported")
    expanded = [v for v,m in pairs for _ in range(m)]
    # The observed ASM compact representation omits one copy at each end.
    full = [expanded[0]]+expanded+[expanded[-1]]
    controls = len(full)-degree-1
    if controls <= degree or controls > 100000:
        raise ValueError("Unsupported spline control count")
    return full, pairs, controls, cursor


def decode_bspline(record):
    tokens, name = record["tokens"], record["name"]
    if read_token(tokens, 3, "boolean_token") or tokens[4]["kind"] != "subtype_start":
        raise ValueError("Unsupported spline wrapper")
    procedural = read_token(tokens, 5, "entity_name")
    version = read_token(tokens, 6, "integer")
    if version != 23100:
        raise ValueError("Unsupported observed spline payload version")
    if name == "intcurve-curve" and procedural == "exact_int_cur":
        if read_token(tokens, 8, "entity_name") != "nubs" or read_token(tokens, 7, "enum") != 0:
            raise ValueError("Only observed non-rational exact curve caches supported")
        degree = read_token(tokens, 9, "integer")
        form = read_token(tokens, 10, "enum")
        if form != 0:
            raise ValueError("Unsupported spline curve form")
        knots, compact, count, cursor = knot_vector(tokens, 12, read_token(tokens, 11, "integer"), degree)
        flat = [read_token(tokens, cursor+i, "double") for i in range(3*count)]
        cursor += 3*count
        if len(tokens) != cursor+20 or tokens[-3]["kind"] != "subtype_end":
            raise ValueError("Unsupported exact curve cache trailer")
        if [read_token(tokens, cursor+i, "entity_name") for i in range(1,5)] != ["null_surface", "null_surface", "nullbs", "nullbs"]:
            raise ValueError("Exact curve has unimplemented support-surface definitions")
        return {"degree": degree, "knots": knots, "stored_compact_knots": compact,
                "raw_control_points": [flat[i:i+3] for i in range(0, len(flat), 3)], "weights": [],
                "parameter_domain": [knots[degree], knots[-degree-1]], "stored_form_code": form,
                "stored_cache_trailer": tokens[cursor:],
                "representation": "Observed non-rational exact_int_cur NUBS cache; support/trailer semantics remain partial"}
    if name != "spline-surface" or procedural != "loft_spl_sur":
        raise ValueError("Unsupported procedural spline subtype")
    starts = [i for i,t in enumerate(tokens) if t["kind"] == "entity_name" and t["value"] == "nubs"]
    if len(starts) != 1:
        raise ValueError("Spline surface cache marker missing or ambiguous")
    start = starts[0]
    du, dv = read_token(tokens, start+1, "integer"), read_token(tokens, start+2, "integer")
    flags = [read_token(tokens, start+i, "enum") for i in range(3, 7)]
    if flags != [2, 0, 0, 0]:
        raise ValueError("Only observed loft surface cache flags supported")
    unique_u, unique_v = read_token(tokens, start+7, "integer"), read_token(tokens, start+8, "integer")
    ku, compact_u, nu, cursor = knot_vector(tokens, start+9, unique_u, du)
    kv, compact_v, nv, cursor = knot_vector(tokens, cursor, unique_v, dv)
    if nu*nv > 100000:
        raise ValueError("Surface control grid exceeds supported limit")
    flat = [read_token(tokens, cursor+i, "double") for i in range(3*nu*nv)]
    cursor += 3*nu*nv
    if len(tokens) != cursor+13 or tokens[cursor+8]["kind"] != "subtype_end":
        raise ValueError("Unsupported loft surface cache trailer")
    controls = [flat[i:i+3] for i in range(0, len(flat), 3)]
    normalized = [controls[v*nu+u] for u in range(nu) for v in range(nv)]
    return {"degree_u": du, "degree_v": dv, "control_count_u": nu, "control_count_v": nv,
            "raw_control_points": normalized, "weights": [], "knots_u": ku, "knots_v": kv,
            "stored_compact_knots_u": compact_u, "stored_compact_knots_v": compact_v,
            "stored_control_grid_order": "u-fast", "normalized_control_grid_order": "v-fast",
            "parameter_domain_u": [ku[du], ku[-du-1]], "parameter_domain_v": [kv[dv], kv[-dv-1]],
            "stored_axis_flags": flags, "periodicity_status": "Native axis flags preserved; general form semantics unverified",
            "stored_cache_trailer_scalar": read_token(tokens, cursor, "double"),
            "stored_cache_trailer": tokens[cursor:], "procedural_subtype": procedural,
            "representation": "Stored non-rational loft NUBS approximation; original procedural loft is not reconstructed",
            "coordinate_scope": "Raw ASM control coordinates; body transforms and units/context not applied"}


def evaluate_curve(cache, parameter):
    from decode_nurbs import evaluate_nurbs

    return evaluate_nurbs({"degree": cache["degree"], "knots": cache["knots"],
                           "control_points_cm": cache["raw_control_points"], "weights": cache["weights"],
                           "parameter_domain": cache["parameter_domain"]}, parameter)


def evaluate_surface(cache, u, v):
    """Evaluate the recovered non-rational grid; returns raw coordinate values."""
    intermediate = []
    nu, nv = cache["control_count_u"], cache["control_count_v"]
    for row in range(nv):
        curve = {"degree": cache["degree_u"], "knots": cache["knots_u"], "weights": [],
                 "raw_control_points": [cache["raw_control_points"][col*nv+row] for col in range(nu)],
                 "parameter_domain": cache["parameter_domain_u"]}
        intermediate.append(evaluate_curve(curve, u))
    return evaluate_curve({"degree": cache["degree_v"], "knots": cache["knots_v"], "weights": [],
                           "raw_control_points": intermediate, "parameter_domain": cache["parameter_domain_v"]}, v)
