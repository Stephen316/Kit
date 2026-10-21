"""Observed inherited topology headers and bounded tolerant-record suffixes.

The stored positive scalars are retained without assigning solver tolerances.
Only the captured tcoedge/tedge/tvertex subclasses are admitted.
"""

import math

from decode_bspline import decode_bspline

KINDS = {'tcoedge-coedge': ('coedge', 11), 'tedge-edge': ('edge', 11),
         'tvertex-vertex': ('vertex', 6)}


def decode_tolerant_topology(record):
    """Return a derived base-header record plus literal additional fields."""
    kind = record['name']
    if kind not in KINDS:
        raise ValueError('Unsupported tolerant topology class')
    base_kind, base_count = KINDS[kind]
    ts = record['tokens']

    def expect(index, token_kind, expected=None):
        token = ts[index]
        if token['kind'] != token_kind or expected is not None and token['value'] != expected:
            raise ValueError('Unobserved tolerant topology field '+str(index))
        if token_kind == 'double' and not math.isfinite(token['value']):
            raise ValueError('Nonfinite tolerant topology scalar')
        return token['value']

    metadata = {'stored_record_kind': kind, 'base_topology_kind': base_kind,
        'is_derived_header': True, 'source_record_index': record['index'],
        'source_record_offset': record['offset'], 'base_token_count': base_count,
        'stored_additional_fields': ts[base_count:],
        'scope': 'Observed inherited topology header; extra scalar/cache fields retained without solver tolerance or exact geometry claims'}
    if kind == 'tedge-edge':
        if len(ts) != 14:
            raise ValueError('Unobserved tolerant edge suffix extent')
        scalar = expect(11, 'double')
        if scalar <= 0:
            raise ValueError('Unobserved nonpositive tolerant edge scalar')
        expect(12, 'integer', 23100); expect(13, 'integer', 0)
        metadata['stored_additional_scalar_11'] = scalar
    elif kind == 'tvertex-vertex':
        if len(ts) != 10:
            raise ValueError('Unobserved tolerant vertex suffix extent')
        expect(6, 'double', -1.)
        values = [expect(i, 'double') for i in (7, 8)]
        if min(values) <= 0:
            raise ValueError('Unobserved nonpositive tolerant vertex scalars')
        expect(9, 'integer', 0)
        metadata['stored_additional_scalars_7_8'] = values
    else:
        bounds = [expect(i, 'double') for i in (11, 12)]
        if bounds[0] > bounds[1]:
            raise ValueError('Reversed tolerant coedge stored bounds')
        expect(13, 'pointer', -1)
        count = expect(14, 'integer')
        metadata['stored_coedge_interval'] = bounds
        if count == 0:
            if len(ts) != 17:
                raise ValueError('Unobserved empty tolerant coedge cache extent')
            expect(15, 'entity_name', 'null_curve'); expect(16, 'integer', 0)
        elif count == 1:
            expect(15, 'entity_name', 'intcurve')
            expect(16, 'boolean_token', False); expect(17, 'subtype_start')
            subtype = expect(18, 'entity_name')
            if subtype not in ('par_int_cur', 'int_int_cur', 'exact_int_cur', 'ref'):
                raise ValueError('Unobserved tolerant coedge inline curve subtype')
            depth, cursor = 1, 18
            while cursor < len(ts) and depth:
                token_kind = ts[cursor]['kind']
                depth += int(token_kind == 'subtype_start')-int(token_kind == 'subtype_end')
                if depth > 128:
                    raise ValueError('Excessive tolerant coedge inline nesting')
                cursor += 1
            if depth:
                raise ValueError('Unclosed tolerant coedge inline curve')
            for _ in range(2):
                finite = expect(cursor, 'boolean_token')
                cursor += 1
                if finite:
                    expect(cursor, 'double')
                    cursor += 1
            expect(cursor, 'integer', 0)
            if cursor+1 != len(ts):
                raise ValueError('Unconsumed tolerant coedge suffix fields')
            inline = dict(record, name='intcurve-curve', tokens=ts[:3]+ts[16:cursor])
            metadata['stored_inline_curve_subtype'] = subtype
            try:
                metadata['inline_curve_cache'] = decode_bspline(inline)
            except (ValueError, KeyError, IndexError) as error:
                metadata['unresolved_inline_curve'] = str(error)
        else:
            raise ValueError('Unobserved tolerant coedge inline cache count')
    return dict(record, name=base_kind, tokens=ts[:base_count]), metadata
