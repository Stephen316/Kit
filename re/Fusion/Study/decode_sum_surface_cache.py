"""Observed line/ellipse sum-surface wrapper with a rational 2x3 cache."""

import math

from decode_bspline import knot_vector, scalar_lists
from decode_fillet_spline_caches import _expect, _finite


def decode_sum_surface_cache(record):
    ts = record['tokens']
    if record['name'] != 'spline-surface':
        raise ValueError('Sum surface requires a spline-surface record')
    _finite(ts)
    for i, kind, value in ((3, 'boolean_token', False), (4, 'subtype_start', None),
                           (5, 'entity_name', 'sum_spl_sur'), (6, 'integer', 23100),
                           (7, 'entity_name', 'straight'), (12, 'entity_name', 'ellipse'),
                           (20, 'enum', 0), (21, 'entity_name', 'nurbs'),
                           (22, 'integer', 1), (23, 'integer', 2), (24, 'entity_name', 'v')):
        _expect(ts, i, kind, value)
    line = {'raw_origin': _expect(ts, 8, 'position_vector'),
            'raw_direction': _expect(ts, 9, 'direction_vector')}
    ellipse = {'raw_center': _expect(ts, 13, 'position_vector'),
               'raw_normal': _expect(ts, 14, 'direction_vector'),
               'raw_major_axis': _expect(ts, 15, 'direction_vector'),
               'stored_ratio': _expect(ts, 16, 'double')}
    if (sum(v*v for v in line['raw_direction']) <= 0 or ellipse['stored_ratio'] <= 0
            or not math.isclose(sum(v*v for v in ellipse['raw_normal']), 1., abs_tol=1e-9)
            or sum(v*v for v in ellipse['raw_major_axis']) <= 0
            or abs(sum(a*b for a, b in zip(ellipse['raw_normal'], ellipse['raw_major_axis']))) > 1e-9):
        raise ValueError('Unsupported degenerate/nonorthogonal sum support frame')
    for i in (10, 11, 17, 18):
        _expect(ts, i, 'boolean_token', False)
    stored_position = _expect(ts, 19, 'position_vector')
    flags = [_expect(ts, i, 'enum', 0) for i in range(25, 29)]
    ku, compact_u, nu, cursor = knot_vector(ts, 31, _expect(ts, 29, 'integer', 2), 1)
    kv, compact_v, nv, cursor = knot_vector(ts, cursor, _expect(ts, 30, 'integer', 2), 2)
    if (nu, nv) != (2, 3):
        raise ValueError('Unobserved sum-surface cache dimensions')
    flat = [_expect(ts, cursor+i, 'double') for i in range(4*nu*nv)]
    cursor += len(flat)
    trailer_start = cursor
    scalar = _expect(ts, cursor, 'double')
    lists, cursor = scalar_lists(ts, cursor+1, 6)
    _expect(ts, cursor, 'boolean_token', False)
    _expect(ts, cursor+1, 'subtype_end')
    for i in range(cursor+2, cursor+6):
        _expect(ts, i, 'boolean_token', False)
    if cursor+6 != len(ts):
        raise ValueError('Unconsumed sum-surface cache trailer')
    weights, controls = flat[3::4], [flat[i:i+3] for i in range(0, len(flat), 4)]
    if any(w <= 0 for w in weights):
        raise ValueError('Nonpositive sum-surface rational weight')
    # The literal v-only rational flag is corroborated by equal weights along U.
    if any(weights[2*v] != weights[2*v+1] for v in range(nv)):
        raise ValueError('Sum-surface v-only weights disagree along U')
    return {'degree_u': 1, 'degree_v': 2, 'control_count_u': nu, 'control_count_v': nv,
            'raw_control_points': [controls[v*nu+u] for u in range(nu) for v in range(nv)],
            'weights': [weights[v*nu+u] for u in range(nu) for v in range(nv)], 'is_rational': True,
            'knots_u': ku, 'knots_v': kv, 'stored_compact_knots_u': compact_u, 'stored_compact_knots_v': compact_v,
            'stored_control_grid_order': 'u-fast', 'normalized_control_grid_order': 'v-fast',
            'parameter_domain_u': [ku[1], ku[-2]], 'parameter_domain_v': [kv[2], kv[-3]],
            'stored_axis_flags': flags, 'stored_rational_axis': 'v', 'procedural_subtype': 'sum_spl_sur',
            'stored_line_support': line, 'stored_ellipse_support': ellipse, 'stored_position_field': stored_position,
            'stored_support_fields': ts[7:21], 'stored_cache_trailer_scalar': scalar,
            'stored_trailer_scalar_lists': lists, 'stored_cache_trailer': ts[trailer_start:],
            'stored_parameter_interval_u': [None, None], 'stored_parameter_interval_v': [None, None],
            'representation': 'Observed rational line/ellipse sum-surface cache; native procedural composition remains partial',
            'parameterization_scope': 'Evaluate only the stored tensor domain; ellipse angular parameter and rational V parameter are not equated',
            'coordinate_scope': 'Raw ASM coordinates; body transforms and units/context not applied'}
