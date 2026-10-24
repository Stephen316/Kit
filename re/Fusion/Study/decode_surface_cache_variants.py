"""Counted loft/centerline-loft grids and finite exact-surface trim variants.

The tensor-grid header is distinct from embedded one-dimensional curve headers.
Unknown procedural prefix/tail fields remain explicitly opaque and bounded.
"""

import math

from decode_bspline import knot_vector, scalar_lists
from decode_fillet_spline_caches import _expect, _finite

LOFT_FLAGS = {(2, 0, 0, 0), (2, 0, 0, 1), (2, 0, 0, 2), (2, 2, 0, 0)}


def decode_surface_cache_variants(record):
    ts = record['tokens']
    if record['name'] != 'spline-surface':
        raise ValueError('Surface-grid variant requires a spline-surface record')
    _expect(ts, 3, 'boolean_token', False); _expect(ts, 4, 'subtype_start')
    subtype = _expect(ts, 5, 'entity_name')
    if subtype not in ('exact_spl_sur', 'loft_spl_sur', 'cl_loft_spl_sur'):
        raise ValueError('Unsupported surface-grid wrapper subtype')
    _expect(ts, 6, 'integer', 23100)
    _finite(ts)
    depth, end, candidates = 0, None, []
    for i in range(4, len(ts)):
        token = ts[i]
        depth += int(token['kind'] == 'subtype_start')-int(token['kind'] == 'subtype_end')
        if not 0 <= depth <= 128:
            raise ValueError('Unobserved surface wrapper bracket nesting')
        if depth == 0:
            end = i
            break
        if depth == 1 and token['kind'] == 'entity_name' and token['value'] in ('nubs', 'nurbs'):
            h = i+3+int(token['value'] == 'nurbs')
            if (i+8 < len(ts) and [t['kind'] for t in ts[i+1:i+3]] == ['integer', 'integer']
                    and [t['kind'] for t in ts[h:h+4]] == ['enum']*4):
                candidates.append((i, h))
    if end is None or len(candidates) != 1:
        raise ValueError('Surface wrapper lacks one unambiguous root-level tensor-grid header')
    start, header = candidates[0]
    if subtype in ('exact_spl_sur', 'cl_loft_spl_sur'):
        _expect(ts, 7, 'enum', 0)
        if start != 8:
            raise ValueError('Unobserved direct surface-grid position')
    rational = ts[start]['value'] == 'nurbs'
    if rational:
        _expect(ts, start+3, 'entity_name', 'both')
    du, dv = _expect(ts, start+1, 'integer'), _expect(ts, start+2, 'integer')
    flags = tuple(_expect(ts, header+i, 'enum') for i in range(4))
    allowed = {(0, 0, 0, 0)} if subtype == 'exact_spl_sur' else LOFT_FLAGS
    if flags not in allowed:
        raise ValueError('Unobserved surface-grid variant axis flags')
    ku, compact_u, nu, cursor = knot_vector(ts, header+6, _expect(ts, header+4, 'integer'), du)
    kv, compact_v, nv, cursor = knot_vector(ts, cursor, _expect(ts, header+5, 'integer'), dv)
    if nu*nv > 100000:
        raise ValueError('Surface variant grid exceeds supported limit')
    stride = 4 if rational else 3
    flat = [_expect(ts, cursor+i, 'double') for i in range(stride*nu*nv)]
    cursor += stride*nu*nv
    trailer_start = cursor
    scalar = _expect(ts, cursor, 'double')
    lists, cursor = scalar_lists(ts, cursor+1, 6)
    _expect(ts, cursor, 'boolean_token', False)
    cursor += 1
    opaque_tail, inner_flags, inner_values = [], [], []
    if subtype == 'exact_spl_sur':
        for _ in range(4):
            finite = _expect(ts, cursor, 'boolean_token')
            inner_flags.append(finite)
            cursor += 1
            inner_values.append(_expect(ts, cursor, 'double') if finite else None)
            cursor += int(finite)
        _expect(ts, cursor, 'enum', 0)
        cursor += 1
    elif subtype == 'cl_loft_spl_sur':
        if cursor >= end:
            raise ValueError('Centerline loft lacks its bounded procedural tail')
        opaque_tail = ts[cursor:end]
        cursor = end
    if cursor != end:
        raise ValueError('Surface variant cache trailer does not reach its own wrapper end')
    _expect(ts, cursor, 'subtype_end')
    cursor += 1
    bounds, bound_flags = [], []
    for _ in range(4):
        finite = _expect(ts, cursor, 'boolean_token')
        bound_flags.append(finite)
        cursor += 1
        bounds.append(_expect(ts, cursor, 'double') if finite else None)
        cursor += int(finite)
    if cursor != len(ts):
        raise ValueError('Unconsumed surface variant outer interval fields')
    controls = [flat[i:i+3] for i in range(0, len(flat), stride)]
    weights = flat[3::4] if rational else []
    if any(not math.isfinite(w) or w <= 0 for w in weights):
        raise ValueError('Unsupported surface variant rational weight')
    return {'degree_u': du, 'degree_v': dv, 'control_count_u': nu, 'control_count_v': nv,
        'raw_control_points': [controls[v*nu+u] for u in range(nu) for v in range(nv)],
        'weights': [weights[v*nu+u] for u in range(nu) for v in range(nv)] if rational else [],
        'is_rational': rational, 'knots_u': ku, 'knots_v': kv,
        'stored_compact_knots_u': compact_u, 'stored_compact_knots_v': compact_v,
        'stored_control_grid_order': 'u-fast', 'normalized_control_grid_order': 'v-fast',
        'parameter_domain_u': [ku[du], ku[-du-1]], 'parameter_domain_v': [kv[dv], kv[-dv-1]],
        'stored_axis_flags': list(flags), 'stored_cache_trailer_scalar': scalar,
        'stored_trailer_scalar_lists': lists, 'stored_cache_trailer': ts[trailer_start:],
        'stored_parameter_interval_u': bounds[:2], 'stored_parameter_interval_v': bounds[2:],
        'stored_outer_interval_flags': bound_flags, 'stored_inner_optional_flags': inner_flags,
        'stored_inner_optional_values': inner_values, 'procedural_subtype': subtype,
        'stored_uninterpreted_prefix_fields': ts[7:start], 'stored_uninterpreted_post_cache_fields': opaque_tail,
        'procedural_definition_status': 'Counted tensor grid decoded; procedural prefix/centerline-tail fields retained without complete construction semantics',
        'representation': 'Stored clamped polynomial/rational surface grid; exact loft/trim reconstruction remains unresolved',
        'periodicity_status': 'Literal axis flags retained; cache evaluation is restricted to the stored clamped domain without inferred periodic extension',
        'coordinate_scope': 'Raw ASM control coordinates; body transforms and units/context not applied'}
