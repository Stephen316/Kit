"""Observed FDM feature/thread-face attribute payloads, without owner semantics.

The numerical feature literal is not a typed native object reference. Position
triples and terminal flags remain literal cache fields, not thread limits or
internal/external/handedness flags. Callers must validate FACE ownership/chains.
"""

import math
import struct

DEFINITION = 'FDM_feature_attrib_def'


def decode_fdm_face_attribute(record):
    """Decode and replay only the exact observed14/18-token payload layouts."""
    tokens = record['tokens']
    if record['name'] != 'ATTRIB_CUSTOM-attrib' or len(tokens) not in (14, 18):
        raise ValueError('Unsupported FDM custom-attribute payload length/class')
    encoded = bytearray()
    def read(index, kind, expected=None):
        token = tokens[index]; value = token['value']
        if token['kind'] != kind:
            raise ValueError('Unexpected FDM payload token kind at field'+str(index))
        if expected is not None and value != expected:
            raise ValueError('Unsupported FDM payload field'+str(index))
        if kind == 'integer':
            if token.get('tag') != 4 or not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 0xffffffff:
                raise ValueError('FDM integer field lacks bounded typed uint32 literal')
            encoded.extend(b'\x04'+struct.pack('<q', value))
        elif kind == 'string':
            if token.get('tag') != 7 or not isinstance(value, str) or not 1 <= len(value) <= 64 or any(not 32 <= ord(c) <= 126 for c in value):
                raise ValueError('FDM string field lacks bounded printable ASCII')
            raw = value.encode('ascii'); encoded.extend(bytes((7, len(raw)))+raw)
        elif kind == 'position_vector':
            if token.get('tag') != 19 or len(value) != 3 or not all(math.isfinite(v) for v in value):
                raise ValueError('FDM position field is not a finite typed vector')
            encoded.extend(b'\x13'+struct.pack('<3d', *value))
        return value
    definition = read(5, 'string', DEFINITION)
    schema = [read(6, 'integer', 2), read(7, 'integer', 2)]
    payload_name = read(8, 'string')
    if payload_name not in ('feature_data', 'thread_face_data'):
        raise ValueError('Unsupported FDM payload name')
    layout = read(9, 'integer', 3)
    literal = read(10, 'integer')
    if literal == 0:
        raise ValueError('Unobserved zero FDM feature literal')
    flags = read(11, 'integer', 2097152)
    count = read(12, 'integer', 2 if payload_name == 'feature_data' else 6)
    kind = read(13, 'integer', 1902 if payload_name == 'feature_data' else 1901)
    positions, terminal = [], None
    if payload_name == 'thread_face_data':
        if len(tokens) != 18:
            raise ValueError('FDM thread-face payload has wrong field extent')
        positions = [read(i, 'position_vector') for i in (14, 15, 16)]
        terminal = read(17, 'integer')
        if terminal not in (0, 1):
            raise ValueError('Unobserved FDM terminal flag')
    elif len(tokens) != 14:
        raise ValueError('FDM feature payload has unconsumed fields')
    start, end = tokens[5]['offset'], record['end_offset']-1
    if end-start != len(encoded):
        raise ValueError('FDM typed replay length differs from stored payload extent')
    return {'definition_name': definition, 'stored_schema_fields': schema,
            'stored_payload_name': payload_name, 'stored_layout_code': layout,
            'stored_feature_literal': literal, 'stored_flags_literal': flags,
            'stored_count_field': count, 'stored_kind_literal': kind,
            'stored_position_vectors': positions, 'stored_terminal_flag': terminal,
            'payload_offset': start, 'payload_end_offset': end, 'payload_hex': bytes(encoded).hex(),
            'identity_scope': 'Literal feature field only; not a typed native feature object reference',
            'position_scope': 'Literal cache positions; thread limits and selected-face parameter roles unresolved',
            'ownership_scope': 'Payload only; caller must prove initial FACE owner and reciprocal attribute chain'}
