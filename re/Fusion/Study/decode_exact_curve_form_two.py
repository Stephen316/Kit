"""Observed closed-loft cubic exact_int_cur form2 cache.

The clamped control grid is independently evaluable inside its stored domain.
Form2 is retained without inferring universal periodicity, reversal or an
extension beyond that domain. The exact procedural closed curve is unresolved.
"""

from decode_bspline import knot_vector, scalar_lists
from decode_fillet_spline_caches import _expect, _prefix


def decode_exact_curve_form_two(record):
    tokens = _prefix(record, 'intcurve-curve', 'exact_int_cur', False)
    _expect(tokens, 7, 'enum', 0)
    _expect(tokens, 8, 'entity_name', 'nubs')
    degree = _expect(tokens, 9, 'integer', 3)
    _expect(tokens, 10, 'enum', 2)
    knots, compact, count, cursor = knot_vector(tokens, 12, _expect(tokens, 11, 'integer'), degree)
    flat = [_expect(tokens, cursor+i, 'double') for i in range(3*count)]
    cursor += 3*count
    trailer_start = cursor
    scalar = _expect(tokens, cursor, 'double')
    if [_expect(tokens, cursor+i, 'entity_name') for i in range(1, 5)] != ['null_surface', 'null_surface', 'nullbs', 'nullbs']:
        raise ValueError('Unsupported exact curve form2 support definitions')
    _expect(tokens, cursor+5, 'boolean_token', False)
    _expect(tokens, cursor+6, 'boolean_token', False)
    lists, cursor = scalar_lists(tokens, cursor+7, 4)
    flags, values = [], []
    for _ in range(2):
        flags.append(_expect(tokens, cursor, 'boolean_token', True))
        values.append(_expect(tokens, cursor+1, 'double'))
        cursor += 2
    enums = [_expect(tokens, cursor+i, 'enum', 0) for i in (0, 1)]
    _expect(tokens, cursor+2, 'subtype_end')
    _expect(tokens, cursor+3, 'boolean_token', False)
    _expect(tokens, cursor+4, 'boolean_token', False)
    if cursor+5 != len(tokens):
        raise ValueError('Unsupported exact curve form2 trailer length')
    return {'degree': degree, 'knots': knots, 'stored_compact_knots': compact,
            'raw_control_points': [flat[i:i+3] for i in range(0, len(flat), 3)],
            'weights': [], 'is_rational': False, 'stored_form_code': 2,
            'parameter_domain': [knots[degree], knots[-degree-1]],
            'stored_parameter_interval': [None, None], 'stored_interval_flags': [False, False],
            'uninterpreted_cache_scalar': scalar, 'stored_trailer_scalar_lists': lists,
            'stored_trailer_optional_flags': flags, 'stored_trailer_optional_values': values,
            'stored_trailer_enums': enums, 'stored_cache_trailer': tokens[trailer_start:],
            'is_periodic': None,
            'periodicity_status': 'Form code2 retained; the sampled stored cache closes, but universal periodicity/extension semantics remain unresolved',
            'flag_scope': 'Literal form, interval and trailer fields preserved; no sign mapping or curve reversal inferred',
            'representation': 'Observed clamped cubic non-rational exact_int_cur form2 cache; exact procedural closed-loft curve is not reconstructed',
            'coordinate_scope': 'Raw ASM coordinates; body transforms and units/context not applied'}
