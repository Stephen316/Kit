"""Explicit quadratic/linear NUBS tensor grids in observed cyl_spl_sur.

The embedded exact curve and extrusion vector are source fields, separate from
this independently stored finite tensor grid. No artificial V domain or exact
procedural/extrusion parameterization is synthesized.
"""

from decode_bspline import decode_bspline, knot_vector, scalar_lists
from decode_fillet_spline_caches import _expect, _prefix
from decode_intersection_curve_variants import optional_scalars


def decode_cylindrical_spline_cache(record):
    wrapper = _expect(record['tokens'], 3, 'boolean_token')
    tokens = _prefix(record, 'spline-surface', 'cyl_spl_sur', wrapper)
    _expect(tokens, 7, 'entity_name', 'intcurve')
    _expect(tokens, 8, 'boolean_token', False)
    _expect(tokens, 9, 'subtype_start')
    _expect(tokens, 10, 'entity_name', 'exact_int_cur')
    _expect(tokens, 11, 'integer', 23100)
    _expect(tokens, 12, 'enum', 0)
    _expect(tokens, 13, 'entity_name', 'nubs')
    _expect(tokens, 14, 'integer', 2)
    _expect(tokens, 15, 'enum', 0)
    depth, cursor = 1, 10
    while cursor < len(tokens) and depth:
        if tokens[cursor]['kind'] == 'subtype_start':
            depth += 1
        elif tokens[cursor]['kind'] == 'subtype_end':
            depth -= 1
        cursor += 1
    if depth:
        raise ValueError('Unbounded cylindrical spline embedded curve')
    _, _, end_curve = optional_scalars(tokens, cursor, 2)
    curve = decode_bspline({'name': 'intcurve-curve', 'tokens': tokens[:3]+tokens[8:end_curve]})
    direction = _expect(tokens, end_curve, 'direction_vector')
    origin = _expect(tokens, end_curve+1, 'position_vector')
    _expect(tokens, end_curve+2, 'enum', 0)
    start = end_curve+3
    _expect(tokens, start, 'entity_name', 'nubs')
    du = _expect(tokens, start+1, 'integer', 2)
    dv = _expect(tokens, start+2, 'integer', 1)
    flags = [_expect(tokens, start+i, 'enum', 0) for i in range(3, 7)]
    ku, compact_u, nu, cursor = knot_vector(tokens, start+9, _expect(tokens, start+7, 'integer'), du)
    kv, compact_v, nv, cursor = knot_vector(tokens, cursor, _expect(tokens, start+8, 'integer'), dv)
    if nu*nv > 100000:
        raise ValueError('Cylindrical spline cache grid exceeds supported limit')
    flat = [_expect(tokens, cursor+i, 'double') for i in range(3*nu*nv)]
    cursor += 3*nu*nv
    trailer_start = cursor
    scalar = _expect(tokens, cursor, 'double')
    lists, cursor = scalar_lists(tokens, cursor+1, 6)
    _expect(tokens, cursor, 'boolean_token', False)
    _expect(tokens, cursor+1, 'subtype_end')
    interval_flags, intervals, cursor = optional_scalars(tokens, cursor+2, 4)
    if cursor != len(tokens):
        raise ValueError('Unsupported cylindrical spline trailing fields')
    controls = [flat[i:i+3] for i in range(0, len(flat), 3)]
    return {'degree_u': du, 'degree_v': dv, 'control_count_u': nu, 'control_count_v': nv,
            'raw_control_points': [controls[v*nu+u] for u in range(nu) for v in range(nv)],
            'weights': [], 'is_rational': False, 'knots_u': ku, 'knots_v': kv,
            'stored_compact_knots_u': compact_u, 'stored_compact_knots_v': compact_v,
            'stored_control_grid_order': 'u-fast', 'normalized_control_grid_order': 'v-fast',
            'parameter_domain_u': [ku[du], ku[-du-1]], 'parameter_domain_v': [kv[dv], kv[-dv-1]],
            'stored_parameter_interval_u': intervals[:2], 'stored_parameter_interval_v': intervals[2:],
            'stored_interval_flags': interval_flags, 'stored_axis_flags': flags, 'stored_wrapper_flag': wrapper,
            'stored_embedded_curve_cache': curve,
            'stored_embedded_curve_token_span': {'token_start': 7, 'subtype_token_start': 9, 'token_end': end_curve},
            'stored_extrusion_direction': direction, 'stored_extrusion_origin': origin,
            'stored_procedural_definition': tokens[5:start], 'stored_grid_start_token': start,
            'stored_cache_trailer_scalar': scalar, 'stored_trailer_scalar_lists': lists,
            'stored_cache_trailer': tokens[trailer_start:], 'procedural_subtype': 'cyl_spl_sur',
            'representation': 'Explicit stored quadratic/linear non-rational tensor grid; exact cylindrical-spline procedural surface is not reconstructed',
            'cache_status': 'Finite U/V domains come from explicit stored knots; no independent API surface-evaluator comparison captured',
            'periodicity_status': 'Axis flags retained literally; general form/periodicity meanings unresolved',
            'flag_scope': 'Wrapper and bound flags preserved; no coordinate reversal, surface sense or parameter remapping inferred',
            'coordinate_scope': 'Raw ASM coordinates; component transforms and units/context not applied'}
