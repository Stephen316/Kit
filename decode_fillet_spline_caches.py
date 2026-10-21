"""Bounded stored NUBS caches inside observed procedural fillet definitions.

These are cached approximations. Neither procedural blend reconstruction nor
inline support-reference identity is inferred from the cache/control layout.
"""

import math

from decode_bspline import knot_vector, read_token, scalar_lists


def _expect(tokens, index, kind, value=None):
    actual = read_token(tokens, index, kind)
    if value is not None and actual != value:
        raise ValueError('Unsupported procedural cache field '+str(index))
    return actual


def _finite(tokens):
    for token in tokens:
        value = token.get('value')
        if token['kind'] == 'double' and not math.isfinite(value):
            raise ValueError('Nonfinite procedural spline cache scalar')
        if token['kind'] in ('position_vector', 'direction_vector'):
            if len(value) != 3 or any(not math.isfinite(v) for v in value):
                raise ValueError('Invalid procedural spline cache vector')


def _prefix(record, name, subtype, wrapper):
    tokens = record['tokens']
    if record['name'] != name:
        raise ValueError('Unexpected procedural cache record kind')
    _finite(tokens)
    _expect(tokens, 3, 'boolean_token', wrapper)
    _expect(tokens, 4, 'subtype_start')
    _expect(tokens, 5, 'entity_name', subtype)
    _expect(tokens, 6, 'integer', 23100)
    return tokens


def _curve_grid(tokens, start, dimensions):
    _expect(tokens, start, 'entity_name', 'nubs')
    degree = _expect(tokens, start+1, 'integer', 3)
    _expect(tokens, start+2, 'enum', 0)
    knots, compact, count, cursor = knot_vector(tokens, start+4,
                                               _expect(tokens, start+3, 'integer'), degree)
    flat = [_expect(tokens, cursor+i, 'double') for i in range(dimensions*count)]
    cursor += dimensions*count
    return {'degree': degree, 'knots': knots, 'stored_compact_knots': compact,
            'raw_control_points': [flat[i:i+dimensions] for i in range(0, len(flat), dimensions)],
            'weights': [], 'is_rational': False, 'stored_form_code': 0,
            'parameter_domain': [knots[degree], knots[-degree-1]]}, cursor


def decode_intersection_curve_cache(record):
    """Observed cubic XYZ + UV NUBS caches with spline-ref / plane supports."""
    tokens = _prefix(record, 'intcurve-curve', 'int_int_cur', False)
    _expect(tokens, 7, 'enum', 0)
    cache, cursor = _curve_grid(tokens, 8, 3)
    trailer_start = cursor
    scalar = _expect(tokens, cursor, 'double')
    _expect(tokens, cursor+1, 'entity_name', 'spline')
    support_flag = _expect(tokens, cursor+2, 'boolean_token')
    _expect(tokens, cursor+3, 'subtype_start')
    _expect(tokens, cursor+4, 'entity_name', 'ref')
    support_ref = _expect(tokens, cursor+5, 'integer')
    if support_ref < 0:
        raise ValueError('Negative inline procedural support reference')
    _expect(tokens, cursor+6, 'subtype_end')
    for i in range(7, 11):
        _expect(tokens, cursor+i, 'boolean_token', False)
    _expect(tokens, cursor+11, 'entity_name', 'plane')
    for i, kind in ((12, 'position_vector'), (13, 'direction_vector'), (14, 'direction_vector')):
        _expect(tokens, cursor+i, kind)
    for i in range(15, 20):
        _expect(tokens, cursor+i, 'boolean_token', False)
    uv, cursor = _curve_grid(tokens, cursor+20, 2)
    _expect(tokens, cursor, 'entity_name', 'nullbs')
    _expect(tokens, cursor+1, 'boolean_token', False)
    _expect(tokens, cursor+2, 'boolean_token', False)
    lists, cursor = scalar_lists(tokens, cursor+3, 4)
    _expect(tokens, cursor, 'subtype_end')
    _expect(tokens, cursor+1, 'boolean_token', False)
    _expect(tokens, cursor+2, 'boolean_token', False)
    if cursor+3 != len(tokens):
        raise ValueError('Unsupported intersection cache trailer length')
    # Preserve the two cache parameter domains independently. No invariant
    # correspondence between their parameterizations or surface references.
    cache.update(procedural_subtype='int_int_cur', stored_wrapper_flag=False,
                 uninterpreted_cache_scalar=scalar, stored_inline_surface_ref=support_ref,
                 stored_support_surface_flag=support_flag, stored_parameter_interval=[None, None],
                 stored_embedded_uv_cache=uv, stored_trailer_scalar_lists=lists,
                 stored_cache_trailer=tokens[trailer_start:],
                 reference_scope='Inline surface-reference namespace unresolved; no persistent surface/body identity assigned',
                 flag_scope='Literal support flag retained; no curve reversal or parameter remapping inferred',
                 representation='Stored cubic non-rational intersection-curve approximation; procedural intersection is not reconstructed',
                 cache_status='Stored XYZ and UV grids decoded; no direct API cache/evaluator comparison captured',
                 coordinate_scope='Raw ASM coordinates; body transforms and units/context not applied')
    return cache


def decode_g2_blend_surface_cache(record):
    """Observed planar-support g2_blend_spl_sur wrapper with an explicit grid."""
    tokens = _prefix(record, 'spline-surface', 'g2_blend_spl_sur', True)
    for i in (7, 8):
        _expect(tokens, i, 'double')
    for start in (9, 25):
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
    _expect(tokens, 41, 'entity_name', 'straight')
    _expect(tokens, 42, 'position_vector')
    _expect(tokens, 43, 'direction_vector')
    for i in (44, 46, 51, 53):
        _expect(tokens, i, 'boolean_token', True)
        _expect(tokens, i+1, 'double')
    for i in (48, 49, 58, 59):
        _expect(tokens, i, 'double')
    _expect(tokens, 50, 'enum', -1)
    for i in (55, 56):
        _expect(tokens, i, 'boolean_token', False)
    for i in (57, 60):
        _expect(tokens, i, 'integer', 1)
    _expect(tokens, 61, 'enum', 0)
    _expect(tokens, 62, 'entity_name', 'nubs')
    du = _expect(tokens, 63, 'integer', 4)
    dv = _expect(tokens, 64, 'integer', 3)
    flags = [_expect(tokens, i, 'enum', 0) for i in range(65, 69)]
    ku, compact_u, nu, cursor = knot_vector(tokens, 71, _expect(tokens, 69, 'integer'), du)
    kv, compact_v, nv, cursor = knot_vector(tokens, cursor, _expect(tokens, 70, 'integer'), dv)
    if nu*nv > 100000:
        raise ValueError('Procedural surface control grid exceeds supported limit')
    flat = [_expect(tokens, cursor+i, 'double') for i in range(3*nu*nv)]
    cursor += 3*nu*nv
    trailer_start = cursor
    scalar = _expect(tokens, cursor, 'double')
    lists, cursor = scalar_lists(tokens, cursor+1, 6)
    _expect(tokens, cursor, 'boolean_token', False)
    for i in range(1, 4):
        _expect(tokens, cursor+i, 'integer', 0)
    _expect(tokens, cursor+4, 'subtype_end')
    cursor += 5
    intervals = []
    for _ in range(4):
        _expect(tokens, cursor, 'boolean_token', True)
        intervals.append(_expect(tokens, cursor+1, 'double'))
        cursor += 2
    if cursor != len(tokens):
        raise ValueError('Unsupported G2 blend cache trailer length')
    controls = [flat[i:i+3] for i in range(0, len(flat), 3)]
    return {'degree_u': du, 'degree_v': dv, 'control_count_u': nu, 'control_count_v': nv,
            'raw_control_points': [controls[v*nu+u] for u in range(nu) for v in range(nv)],
            'weights': [], 'is_rational': False, 'knots_u': ku, 'knots_v': kv,
            'stored_compact_knots_u': compact_u, 'stored_compact_knots_v': compact_v,
            'stored_control_grid_order': 'u-fast', 'normalized_control_grid_order': 'v-fast',
            'parameter_domain_u': [ku[du], ku[-du-1]], 'parameter_domain_v': [kv[dv], kv[-dv-1]],
            'stored_parameter_interval_u': intervals[:2], 'stored_parameter_interval_v': intervals[2:],
            'stored_axis_flags': flags, 'stored_wrapper_flag': True,
            'stored_procedural_definition': tokens[5:62],
            'stored_cache_trailer_scalar': scalar, 'stored_trailer_scalar_lists': lists,
            'stored_cache_trailer': tokens[trailer_start:], 'procedural_subtype': 'g2_blend_spl_sur',
            'periodicity_status': 'Native flags preserved; general form semantics unverified',
            'flag_scope': 'Wrapper flag retained without applying coordinate reversal or surface sense',
            'representation': 'Stored non-rational G2 blend NUBS approximation; exact procedural blend is not reconstructed',
            'cache_status': 'No direct API surface-cache/evaluator getter comparison captured; approximation error is unbounded',
            'coordinate_scope': 'Raw ASM control coordinates; body transforms and units/context not applied'}
