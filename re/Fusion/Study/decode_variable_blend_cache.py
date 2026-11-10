"""Observed rational cached grids in srf_srf_v_bl_spl_sur fillet wrappers.

The embedded supports, spine and width descriptions are preserved; procedural
blend reconstruction, native flag meanings and exact approximation error remain
unresolved. Only two observed planar-support wrapper variants are accepted.
"""

import math

from decode_bspline import decode_bspline, knot_vector, scalar_lists
from decode_fillet_spline_caches import _expect, _prefix


def decode_variable_blend_cache(record):
    tokens = _prefix(record, 'spline-surface', 'srf_srf_v_bl_spl_sur', False)
    for start in (7, 23):
        _expect(tokens, start, 'string', 'blend_support_surface')
        _expect(tokens, start+1, 'entity_name', 'plane')
        for offset, kind in ((2, 'position_vector'), (3, 'direction_vector'), (4, 'direction_vector')):
            _expect(tokens, start+offset, kind)
        for offset in range(5, 10):
            _expect(tokens, start+offset, 'boolean_token', False)
        _expect(tokens, start+10, 'entity_name', 'null_curve')
        _expect(tokens, start+11, 'entity_name', 'nullbs')
        _expect(tokens, start+12, 'position_vector')
        _expect(tokens, start+13, 'entity_name', 'nullbs')
        _expect(tokens, start+14, 'integer', 0)
        _expect(tokens, start+15, 'entity_name', 'nullbs')
    spine_kind = _expect(tokens, 39, 'entity_name')
    spine_cache = None
    if spine_kind == 'straight':
        _expect(tokens, 40, 'position_vector')
        _expect(tokens, 41, 'direction_vector')
        for i in (42, 44):
            _expect(tokens, i, 'boolean_token', True)
            _expect(tokens, i+1, 'double')
        cursor, mode = 46, 1
    elif spine_kind == 'intcurve':
        _expect(tokens, 40, 'boolean_token', False)
        _expect(tokens, 41, 'subtype_start')
        _expect(tokens, 42, 'entity_name', 'exact_int_cur')
        _expect(tokens, 43, 'integer', 23100)
        _expect(tokens, 44, 'enum', 0)
        _expect(tokens, 45, 'entity_name', 'nubs')
        _expect(tokens, 46, 'integer', 5)
        _expect(tokens, 47, 'enum', 0)
        depth, cursor = 1, 42
        while cursor < len(tokens) and depth:
            if tokens[cursor]['kind'] == 'subtype_start':
                depth += 1
            elif tokens[cursor]['kind'] == 'subtype_end':
                depth -= 1
            cursor += 1
        if depth:
            raise ValueError('Unbounded embedded blend spine subtype')
        _expect(tokens, cursor, 'boolean_token', False)
        _expect(tokens, cursor+1, 'boolean_token', False)
        cursor += 2
        # The complete embedded curve wrapper is validated by the established
        # exact cache reader, not located by searching for a grid marker.
        spine_cache = decode_bspline({'name': 'intcurve-curve',
                                      'tokens': tokens[:3]+tokens[40:cursor]})
        mode = 0
    else:
        raise ValueError('Unsupported variable-blend spine kind')
    _expect(tokens, cursor, 'double')
    _expect(tokens, cursor+1, 'double')
    _expect(tokens, cursor+2, 'enum', mode)
    cursor += 3
    for _ in range(2 if mode else 1):
        _expect(tokens, cursor, 'entity_name', 'edge_offset' if mode else 'fixed_width')
        _expect(tokens, cursor+1, 'enum', 0)
        _expect(tokens, cursor+2, 'boolean_token', True)
        for offset in (3, 4, 5):
            _expect(tokens, cursor+offset, 'double')
        cursor += 6
    _expect(tokens, cursor, 'enum', 0)
    for offset in (1, 3):
        _expect(tokens, cursor+offset, 'boolean_token', True)
        _expect(tokens, cursor+offset+1, 'double')
    _expect(tokens, cursor+5, 'boolean_token', False)
    _expect(tokens, cursor+6, 'boolean_token', False)
    _expect(tokens, cursor+7, 'integer', 1)
    _expect(tokens, cursor+8, 'double')
    _expect(tokens, cursor+9, 'double')
    _expect(tokens, cursor+10, 'integer', 1)
    _expect(tokens, cursor+11, 'enum', 0)
    start = cursor+12
    _expect(tokens, start, 'entity_name', 'nurbs')
    du = _expect(tokens, start+1, 'integer', 3)
    dv = _expect(tokens, start+2, 'integer', 3)
    _expect(tokens, start+3, 'entity_name', 'both')
    flags = [_expect(tokens, start+i, 'enum', 0) for i in range(4, 8)]
    ku, compact_u, nu, cursor = knot_vector(tokens, start+10, _expect(tokens, start+8, 'integer'), du)
    kv, compact_v, nv, cursor = knot_vector(tokens, cursor, _expect(tokens, start+9, 'integer'), dv)
    if nu*nv > 100000:
        raise ValueError('Variable-blend grid exceeds supported limit')
    flat = [_expect(tokens, cursor+i, 'double') for i in range(4*nu*nv)]
    cursor += 4*nu*nv
    trailer_start = cursor
    scalar = _expect(tokens, cursor, 'double')
    lists, cursor = scalar_lists(tokens, cursor+1, 6)
    _expect(tokens, cursor, 'boolean_token', False)
    for offset in (1, 2, 3):
        _expect(tokens, cursor+offset, 'integer', 0)
    _expect(tokens, cursor+4, 'entity_name', 'null_curve')
    for offset, value in ((5, True), (6, False), (7, False), (8, False)):
        _expect(tokens, cursor+offset, 'boolean_token', value)
    for offset in (9, 10):
        _expect(tokens, cursor+offset, 'entity_name', 'nullbs')
    _expect(tokens, cursor+11, 'subtype_end')
    cursor += 12
    bounds = []
    for _ in range(4):
        _expect(tokens, cursor, 'boolean_token', True)
        bounds.append(_expect(tokens, cursor+1, 'double'))
        cursor += 2
    if cursor != len(tokens):
        raise ValueError('Unsupported variable-blend trailing fields')
    for interval, domain in ((bounds[:2], [ku[du], ku[-du-1]]),
                             (bounds[2:], [kv[dv], kv[-dv-1]])):
        if not interval[0] < interval[1] or interval[0] < domain[0]-1e-12 or interval[1] > domain[1]+1e-12:
            raise ValueError('Variable-blend trim interval outside cache domain')
    weights = flat[3::4]
    if any(not math.isfinite(w) or w <= 0 for w in weights):
        raise ValueError('Invalid variable-blend rational weight')
    controls = [flat[i:i+3] for i in range(0, len(flat), 4)]
    result = {'degree_u': du, 'degree_v': dv, 'control_count_u': nu, 'control_count_v': nv,
              'raw_control_points': [controls[v*nu+u] for u in range(nu) for v in range(nv)],
              'weights': [weights[v*nu+u] for u in range(nu) for v in range(nv)],
              'is_rational': True, 'knots_u': ku, 'knots_v': kv,
              'stored_compact_knots_u': compact_u, 'stored_compact_knots_v': compact_v,
              'stored_control_grid_order': 'u-fast', 'normalized_control_grid_order': 'v-fast',
              'parameter_domain_u': [ku[du], ku[-du-1]], 'parameter_domain_v': [kv[dv], kv[-dv-1]],
              'stored_parameter_interval_u': bounds[:2], 'stored_parameter_interval_v': bounds[2:],
              'stored_axis_flags': flags, 'stored_wrapper_flag': False,
              'stored_spine_kind': spine_kind, 'stored_blend_mode_code': mode,
              'stored_procedural_definition': tokens[5:start], 'stored_grid_start_token': start,
              'stored_cache_trailer_scalar': scalar, 'stored_trailer_scalar_lists': lists,
              'stored_cache_trailer': tokens[trailer_start:],
              'procedural_subtype': 'srf_srf_v_bl_spl_sur',
              'representation': 'Stored rational bicubic variable-blend approximation; exact procedural blend is not reconstructed',
              'cache_status': 'No direct API surface-cache/evaluator getter comparison captured; approximation error is unbounded',
              'periodicity_status': 'Native axis flags retained; general periodicity/form semantics unresolved',
              'flag_scope': 'Native wrapper flags preserved; no coordinate reversal, surface sense or parameter remapping inferred',
              'coordinate_scope': 'Raw ASM coordinates; body transforms and units/context not applied'}
    if spine_cache is not None:
        result['stored_embedded_spine_cache'] = spine_cache
    return result
