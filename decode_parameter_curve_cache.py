"""Stored XYZ and UV caches in observed par_int_cur procedural records.

Raw wrapper/interval flags remain literal. The inline support namespace is not
mapped to ASM entity IDs. These caches do not reconstruct the exact procedural
curve or establish general edge/cache parameter correspondence.
"""

import math

from decode_bspline import knot_vector, scalar_lists
from decode_fillet_spline_caches import _expect, _prefix


def _support_bounds(tokens, cursor):
    flags, values = [], []
    for _ in range(4):
        finite = _expect(tokens, cursor, 'boolean_token')
        flags.append(finite)
        cursor += 1
        values.append(_expect(tokens, cursor, 'double') if finite else None)
        cursor += int(finite)
    return flags, values, cursor


def _grid(tokens, start, dimensions, allowed_degrees, rational_allowed):
    representation = _expect(tokens, start, 'entity_name')
    if representation not in (('nubs', 'nurbs') if rational_allowed else ('nubs',)):
        raise ValueError('Unsupported parameter-curve grid representation')
    degree = _expect(tokens, start+1, 'integer')
    if degree not in allowed_degrees:
        raise ValueError('Unsupported parameter-curve grid degree')
    _expect(tokens, start+2, 'enum', 0)
    knots, compact, count, cursor = knot_vector(tokens, start+4, _expect(tokens, start+3, 'integer'), degree)
    rational = representation == 'nurbs'
    stride = dimensions+int(rational)
    flat = [_expect(tokens, cursor+i, 'double') for i in range(stride*count)]
    cursor += stride*count
    weights = flat[dimensions::stride] if rational else []
    if any(not math.isfinite(w) or w <= 0 for w in weights):
        raise ValueError('Invalid parameter-curve rational weight')
    return {'degree': degree, 'knots': knots, 'stored_compact_knots': compact,
            'raw_control_points': [flat[i:i+dimensions] for i in range(0, len(flat), stride)],
            'weights': weights, 'is_rational': rational, 'stored_form_code': 0,
            'parameter_domain': [knots[degree], knots[-degree-1]]}, cursor


def decode_parameter_curve_cache(record):
    wrapper = _expect(record['tokens'], 3, 'boolean_token')
    tokens = _prefix(record, 'intcurve-curve', 'par_int_cur', wrapper)
    _expect(tokens, 7, 'enum', 0)
    cache, cursor = _grid(tokens, 8, 3, (3,), True)
    trailer_start = cursor
    scalar = _expect(tokens, cursor, 'double')
    cursor += 1
    support_start = cursor
    support_kind = _expect(tokens, cursor, 'entity_name')
    support = {'kind': support_kind}
    if support_kind == 'plane':
        for offset, kind in ((1, 'position_vector'), (2, 'direction_vector'), (3, 'direction_vector')):
            _expect(tokens, cursor+offset, kind)
        _expect(tokens, cursor+4, 'boolean_token', False)
        flags, bounds, cursor = _support_bounds(tokens, cursor+5)
        if any(flags):
            support.update(stored_interval_flags=flags, stored_parameter_intervals=bounds)
        support['definition_status'] = 'Explicit plane fields preserved; no procedural reconstruction or global identity mapping'
    elif support_kind == 'spline':
        flag = _expect(tokens, cursor+1, 'boolean_token')
        _expect(tokens, cursor+2, 'subtype_start')
        subtype = _expect(tokens, cursor+3, 'entity_name')
        support.update(stored_wrapper_flag=flag, procedural_subtype=subtype)
        if subtype == 'ref':
            _expect(tokens, cursor+1, 'boolean_token', False)
            ref = _expect(tokens, cursor+4, 'integer')
            if ref < 0:
                raise ValueError('Negative inline parameter-curve support reference')
            _expect(tokens, cursor+5, 'subtype_end')
            flags, bounds, cursor = _support_bounds(tokens, cursor+6)
            if any(flags):
                support.update(stored_interval_flags=flags, stored_parameter_intervals=bounds)
            support.update(stored_inline_surface_ref=ref,
                           definition_status='Inline reference namespace unresolved; not an ASM entity index')
        elif subtype == 'sweep_sur':
            try:
                from decode_sweep_surface_cache import decode_sweep_surface_inline
            except ImportError as error:
                raise ValueError('Inline sweep surface-cache decoder unavailable') from error
            surface, cursor = decode_sweep_surface_inline(tokens, cursor+1)
            support.update(stored_surface_cache=surface,
                           definition_status='Strictly decoded stored inline sweep approximation; exact procedural support remains unresolved')
        else:
            raise ValueError('Unsupported parameter-curve inline support subtype')
    else:
        raise ValueError('Unsupported parameter-curve support kind')
    support['stored_definition'] = tokens[support_start:cursor]
    _expect(tokens, cursor, 'entity_name', 'null_surface')
    uv, cursor = _grid(tokens, cursor+1, 2, (1, 3, 5), False)
    _expect(tokens, cursor, 'entity_name', 'nullbs')
    _expect(tokens, cursor+1, 'boolean_token', False)
    _expect(tokens, cursor+2, 'boolean_token', False)
    lists, cursor = scalar_lists(tokens, cursor+3, 4)
    trailer_flags = [_expect(tokens, cursor, 'boolean_token', True),
                     _expect(tokens, cursor+1, 'boolean_token', False)]
    _expect(tokens, cursor+2, 'subtype_end')
    cursor += 3
    interval, interval_flags = [], []
    for _ in range(2):
        finite = _expect(tokens, cursor, 'boolean_token')
        interval_flags.append(finite)
        cursor += 1
        interval.append(_expect(tokens, cursor, 'double') if finite else None)
        cursor += int(finite)
    if cursor != len(tokens):
        raise ValueError('Unsupported parameter-curve trailing fields')
    cache.update(procedural_subtype='par_int_cur', stored_wrapper_flag=wrapper,
                 uninterpreted_cache_scalar=scalar, stored_support_definition=support,
                 stored_embedded_uv_cache=uv, stored_trailer_scalar_lists=lists,
                 stored_trailer_flags=trailer_flags, stored_parameter_interval=interval,
                 stored_interval_flags=interval_flags, stored_cache_trailer=tokens[trailer_start:],
                 reference_scope='Inline support references retained in their own unresolved namespace; parent topology is resolved independently',
                 flag_scope='Literal wrapper and interval flags preserved; no curve reversal or edge/cache parameter remapping inferred',
                 representation='Stored cubic XYZ and degree-one/five UV approximation caches; exact parameter-defined curve is not reconstructed',
                 cache_status='No direct API XYZ/UV cache/evaluator getter comparison captured for this layout',
                 coordinate_scope='Raw ASM coordinates; body transforms and units/context not applied')
    if uv['degree'] == 3:
        cache['representation'] = 'Stored cubic XYZ and cubic UV approximation caches; exact parameter-defined curve is not reconstructed'
    return cache
