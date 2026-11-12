"""Bounded two-support int_int_cur XYZ/UV cache layouts.

Support/UV slot ordering and token spans are literal source facts. Inline refs,
edge parameter correspondence and exact procedural intersection stay unresolved.
"""

from decode_bspline import scalar_lists
from decode_fillet_spline_caches import _expect, _prefix
from decode_parameter_curve_cache import _grid


def optional_scalars(tokens, cursor, count):
    flags, values = [], []
    for _ in range(count):
        finite = _expect(tokens, cursor, 'boolean_token')
        flags.append(finite)
        cursor += 1
        values.append(_expect(tokens, cursor, 'double') if finite else None)
        cursor += int(finite)
    return flags, values, cursor


def _support(tokens, cursor, slot):
    start = cursor
    kind = _expect(tokens, cursor, 'entity_name')
    result = {'slot': slot, 'kind': kind, 'token_start': start}
    if kind == 'plane':
        for offset, token_kind in ((1, 'position_vector'), (2, 'direction_vector'), (3, 'direction_vector')):
            _expect(tokens, cursor+offset, token_kind)
        result['stored_surface_flag'] = _expect(tokens, cursor+4, 'boolean_token')
        flags, bounds, cursor = optional_scalars(tokens, cursor+5, 4)
        result.update(stored_interval_flags=flags, stored_parameter_intervals=bounds,
                      definition_status='Explicit plane fields retained; source topology identity not assigned')
    elif kind == 'spline':
        wrapper = _expect(tokens, cursor+1, 'boolean_token')
        _expect(tokens, cursor+2, 'subtype_start')
        subtype = _expect(tokens, cursor+3, 'entity_name')
        result.update(stored_wrapper_flag=wrapper, procedural_subtype=subtype,
                      subtype_token_start=cursor+2)
        if subtype == 'ref':
            ref = _expect(tokens, cursor+4, 'integer')
            if ref < 0:
                raise ValueError('Negative inline intersection support reference')
            _expect(tokens, cursor+5, 'subtype_end')
            flags, bounds, cursor = optional_scalars(tokens, cursor+6, 4)
            result.update(stored_inline_surface_ref=ref, stored_interval_flags=flags,
                          stored_parameter_intervals=bounds,
                          definition_status='Inline reference retained in unresolved subtype namespace; not a global ASM record ID')
        elif subtype == 'sweep_sur':
            from decode_sweep_surface_cache import decode_sweep_surface_inline
            surface, cursor = decode_sweep_surface_inline(tokens, cursor+1, allow_true_wrapper=(slot == 1))
            result.update(stored_surface_cache=surface,
                          definition_status='Stored inline sweep surface approximation decoded; exact procedural support unresolved')
        else:
            raise ValueError('Unsupported inline intersection support subtype')
    else:
        raise ValueError('Unsupported intersection support kind')
    result.update(token_end=cursor, stored_definition=tokens[start:cursor])
    return result, cursor


def decode_intersection_curve_variants(record):
    tokens = _prefix(record, 'intcurve-curve', 'int_int_cur', False)
    _expect(tokens, 7, 'enum', 0)
    cache, cursor = _grid(tokens, 8, 3, (3,), False)
    trailer_start = cursor
    scalar = _expect(tokens, cursor, 'double')
    cursor += 1
    supports = []
    for slot in range(2):
        support, cursor = _support(tokens, cursor, slot)
        supports.append(support)
    uv_caches, uv_spans = [], []
    for slot in range(2):
        start = cursor
        if _expect(tokens, cursor, 'entity_name') == 'nullbs':
            uv = None
            cursor += 1
        else:
            uv, cursor = _grid(tokens, cursor, 2, (3,), False)
        uv_caches.append(uv)
        uv_spans.append({'slot': slot, 'token_start': start, 'token_end': cursor})
    if all(uv is None for uv in uv_caches):
        raise ValueError('No observed intersection UV cache present')
    trailer_flags, trailer_values, cursor = optional_scalars(tokens, cursor, 2)
    lists, cursor = scalar_lists(tokens, cursor, 4)
    _expect(tokens, cursor, 'subtype_end')
    outer_flags, outer_bounds, cursor = optional_scalars(tokens, cursor+1, 2)
    if cursor != len(tokens):
        raise ValueError('Unsupported intersection-variant trailing fields')
    cache.update(procedural_subtype='int_int_cur', stored_wrapper_flag=False,
                 uninterpreted_cache_scalar=scalar, stored_supports=supports,
                 stored_embedded_uv_caches=uv_caches, stored_uv_slot_spans=uv_spans,
                 stored_trailer_optional_flags=trailer_flags, stored_trailer_optional_scalars=trailer_values,
                 stored_trailer_scalar_lists=lists, stored_interval_flags=outer_flags,
                 stored_parameter_interval=outer_bounds, stored_cache_trailer=tokens[trailer_start:],
                 reference_scope='Support/UV slots and raw token spans retained; subtype namespace resolution requires separate source-ordered evidence',
                 flag_scope='Literal flags preserved; no edge/cache reversal, UV-slot selection or parameter remapping inferred',
                 representation='Stored cubic intersection XYZ and ordered UV approximation caches; exact procedural intersection is not reconstructed',
                 cache_status='No independent API cache/evaluator getter match captured for these layouts',
                 coordinate_scope='Raw ASM coordinates; transforms and units/context not applied')
    return cache
