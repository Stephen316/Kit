"""Observed rational XYZ/linear UV caches inside spring_int_cur wrappers.

The explicit grids are stored approximations. Procedural spring construction,
inline support identity and global approximation error remain unresolved.
"""

import math

from decode_bspline import knot_vector, scalar_lists
from decode_fillet_spline_caches import _expect, _finite


def decode_spring_curve_cache(record):
    """Return the observed cubic NURBS cache and separately framed UV cache.

    Raw cache parameters are retained. This reader does not silently negate edge
    parameters or reinterpret the wrapper Boolean/terminal enum as general sense.
    """
    ts = record['tokens']
    if record['name'] != 'intcurve-curve':
        raise ValueError('Spring cache requires an intcurve record')
    _finite(ts)
    for i, kind, expected in ((0, 'pointer', -1), (1, 'integer', -1), (2, 'pointer', -1),
                              (4, 'subtype_start', None), (5, 'entity_name', 'spring_int_cur'),
                              (6, 'integer', 23100), (7, 'enum', 0), (8, 'entity_name', 'nurbs'),
                              (9, 'integer', 3), (10, 'enum', 0)):
        _expect(ts, i, kind, expected)
    wrapper = _expect(ts, 3, 'boolean_token')
    if not isinstance(wrapper, bool):
        raise ValueError('Spring wrapper flag is not Boolean')
    degree = 3
    knots, compact, count, cursor = knot_vector(ts, 12, _expect(ts, 11, 'integer'), degree)
    flat = [_expect(ts, cursor+i, 'double') for i in range(4*count)]
    cursor += 4*count
    weights = flat[3::4]
    if any(not math.isfinite(w) or w <= 0 for w in weights):
        raise ValueError('Spring NURBS weights must be finite and positive')
    trailer_start = cursor
    scalar = _expect(ts, cursor, 'double')
    _expect(ts, cursor+1, 'entity_name', 'spline')
    _expect(ts, cursor+2, 'boolean_token', False)
    _expect(ts, cursor+3, 'subtype_start')
    _expect(ts, cursor+4, 'entity_name', 'ref')
    support_ref = _expect(ts, cursor+5, 'integer', 0)
    _expect(ts, cursor+6, 'subtype_end')
    for i in range(7, 11):
        _expect(ts, cursor+i, 'boolean_token', False)
    _expect(ts, cursor+11, 'entity_name', 'plane')
    vectors = [_expect(ts, cursor+i, kind) for i, kind in
               ((12, 'position_vector'), (13, 'direction_vector'), (14, 'direction_vector'))]
    for v in vectors[1:]:
        if not math.isclose(sum(x*x for x in v), 1., abs_tol=1e-9):
            raise ValueError('Spring support plane axis/normal is not unit length')
    if not math.isclose(sum(a*b for a, b in zip(vectors[1], vectors[2])), 0., abs_tol=1e-9):
        raise ValueError('Spring support plane axis is not perpendicular to its normal')
    for i in range(15, 20):
        _expect(ts, cursor+i, 'boolean_token', False)
    uv_start = cursor+20
    _expect(ts, uv_start, 'entity_name', 'nubs')
    _expect(ts, uv_start+1, 'integer', 1)
    _expect(ts, uv_start+2, 'enum', 0)
    unique_uv = _expect(ts, uv_start+3, 'integer', 2)
    uv_knots, uv_compact, uv_count, cursor = knot_vector(ts, uv_start+4, unique_uv, 1)
    if uv_count != 2:
        raise ValueError('Only observed two-control spring UV caches supported')
    uv_flat = [_expect(ts, cursor+i, 'double') for i in range(2*uv_count)]
    cursor += 2*uv_count
    _expect(ts, cursor, 'entity_name', 'nullbs')
    _expect(ts, cursor+1, 'boolean_token', False)
    _expect(ts, cursor+2, 'boolean_token', False)
    lists, cursor = scalar_lists(ts, cursor+3, 4)
    if lists != [[], [], [], []]:
        raise ValueError('Unobserved populated spring trailer lists')
    terminal_enum = _expect(ts, cursor, 'enum')
    if (wrapper, terminal_enum) not in ((True, 0), (False, 2)):
        raise ValueError('Unobserved spring wrapper/terminal-enum combination')
    _expect(ts, cursor+1, 'subtype_end')
    _expect(ts, cursor+2, 'boolean_token', False)
    _expect(ts, cursor+3, 'boolean_token', False)
    if cursor+4 != len(ts):
        raise ValueError('Unconsumed spring cache trailer')
    uv = {'degree': 1, 'knots': uv_knots, 'stored_compact_knots': uv_compact,
          'raw_control_points': [uv_flat[i:i+2] for i in range(0, len(uv_flat), 2)],
          'weights': [], 'is_rational': False, 'stored_form_code': 0,
          'parameter_domain': [uv_knots[1], uv_knots[-2]],
          'scope': 'Independent stored UV grid; inline support identity/parameter correspondence not inferred'}
    return {'degree': degree, 'knots': knots, 'stored_compact_knots': compact,
        'raw_control_points': [flat[i:i+3] for i in range(0, len(flat), 4)], 'weights': weights,
        'is_rational': True, 'parameter_domain': [knots[degree], knots[-degree-1]],
        'stored_form_code': 0, 'procedural_subtype': 'spring_int_cur',
        'stored_wrapper_flag': wrapper, 'stored_terminal_enum': terminal_enum,
        'uninterpreted_cache_scalar': scalar, 'stored_inline_surface_ref': support_ref,
        'stored_support_surface_flag': False,
        'stored_explicit_plane_support': {'raw_origin': vectors[0], 'raw_normal': vectors[1],
                                          'raw_reference_axis': vectors[2]},
        'stored_embedded_uv_cache': uv, 'stored_trailer_scalar_lists': lists,
        'stored_outer_trailer_flags': [False, False], 'stored_cache_trailer': ts[trailer_start:],
        'flag_scope': 'Captured wrapper/enum pairs retained; no automatic edge-parameter negation, orientation or geometric reversal',
        'reference_scope': 'Inline ref0 is opaque; parent-surface correspondence requires independent coedge/loop/face links',
        'representation': 'Stored cubic rational spring-curve approximation with a separate linear UV cache; procedural spring definition is not reconstructed',
        'cache_status': 'Only stored grids/typed endpoint evidence; no direct API curve evaluator or global approximation error bound',
        'coordinate_scope': 'Raw ASM cache coordinates; body transforms and units/context not applied'}
