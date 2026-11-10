"""Observed explicit non-rational UV spline caches inside ASM pcurve records."""

from decode_bspline import read_token, knot_vector, evaluate_curve


def _decode_observed_pcurve(record):
    tokens = record["tokens"]
    if read_token(tokens, 3, "integer") != 0:
        raise ValueError("Unsupported pcurve prefix flags")
    prefix_flag = read_token(tokens, 4, "boolean_token")
    if tokens[5]["kind"] != "subtype_start" or read_token(tokens, 6, "entity_name") != "exp_par_cur":
        raise ValueError("Unsupported parameter curve subtype")
    if read_token(tokens, 7, "entity_name") != "nubs":
        raise ValueError("Only observed non-rational pcurve caches supported")
    degree = read_token(tokens, 8, "integer")
    form = read_token(tokens, 9, "enum")
    if (degree, form) not in ((1, 0), (1, 2), (3, 0)):
        raise ValueError("Only observed degree-one/cubic UV curve forms supported")
    knots, compact, count, cursor = knot_vector(tokens, 11, read_token(tokens, 10, "integer"), degree)
    flat = [read_token(tokens, cursor+i, "double") for i in range(2*count)]
    cursor += 2*count
    if len(tokens) != cursor+14:
        raise ValueError("Unsupported explicit pcurve trailer length")
    scalar = read_token(tokens, cursor, "double")
    support_flag = read_token(tokens, cursor+2, "boolean_token")
    if (read_token(tokens, cursor+1, "entity_name") != "spline"
            or tokens[cursor+3]["kind"] != "subtype_start"
            or read_token(tokens, cursor+4, "entity_name") != "ref"
            or tokens[cursor+6]["kind"] != "subtype_end" or tokens[cursor+11]["kind"] != "subtype_end"):
        raise ValueError("Unsupported pcurve support-surface reference wrapper")
    if any(read_token(tokens, cursor+i, "boolean_token") for i in range(7, 11)):
        raise ValueError("Unimplemented pcurve support parameter bounds")
    support_ref = read_token(tokens, cursor+5, "integer")
    offset = [read_token(tokens, cursor+12+i, "double") for i in range(2)]
    raw = [flat[i:i+2] for i in range(0, len(flat), 2)]
    shifted = [[x+d for x,d in zip(p, offset)] for p in raw]
    result = {"degree": degree, "knots": knots, "stored_compact_knots": compact,
            "raw_control_points_uv": raw, "parameter_offset_uv": offset, "control_points_uv": shifted,
            "weights": [], "parameter_domain": [knots[degree], knots[-degree-1]],
            "stored_form_code": form, "uninterpreted_cache_scalar": scalar,
            "stored_inline_surface_ref": support_ref,
            "reference_scope": "Inline support reference namespace unresolved; parent face resolved separately through coedge/loop",
            "coordinate_system": "Parent surface UV parameter space; curve parameter units not inferred",
            "representation": "Stored explicit degree-one/cubic non-rational UV cache; exact coedge parameterization is not reconstructed",
            "cache_status": "Matches observed API spline geometry; sampled exact coedge evaluations may differ"}
    if prefix_flag or support_flag or count != degree+1:
        result.update(stored_prefix_flag_4=prefix_flag, stored_support_surface_flag=support_flag,
                      stored_control_count=count, stored_span_count=len(compact)-1,
                      flag_scope="Literal wrapper flags retained; no coedge direction, surface sense or parameter remapping inferred",
                      representation="Stored explicit clamped non-rational UV spline cache, including multiple spans; exact coedge parameterization unresolved",
                      cache_status="Stored control grid decoded; no direct API UV-cache getter comparison captured for this layout")
    return result


def decode_pcurve(record):
    try:
        return _decode_observed_pcurve(record)
    except (ValueError, IndexError):
        from decode_pcurve_variants import decode_pcurve_variants
        return decode_pcurve_variants(record)


def evaluate_pcurve(cache, parameter):
    return evaluate_curve({"degree": cache["degree"], "knots": cache["knots"], "weights": [],
                           "raw_control_points": [p+[0.] for p in cache["control_points_uv"]],
                           "parameter_domain": cache["parameter_domain"]}, parameter)[:2]
