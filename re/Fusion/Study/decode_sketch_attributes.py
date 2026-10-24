"""Literal observed ASM sketch-attribute payloads, without sketch identities.

COEDGE/EDGE/VERTEX ownership and reciprocal attribute chains belong to callers.
The six decimal text fields are retained as strings, never native object IDs.
"""

import struct

DEFINITION = 'sketch_attrib_def'


def decode_sketch_attribute(record):
    """Replay the bounded ten-token schema[1,1,3], six-decimal-field payload."""
    tokens = record['tokens']
    if record['name'] != 'ATTRIB_CUSTOM-attrib' or len(tokens) != 10:
        raise ValueError('Unsupported sketch attribute class/field extent')
    encoded = bytearray()
    cursor = tokens[5]['offset']

    def read(index, kind, tag):
        nonlocal cursor
        token = tokens[index]; value = token['value']
        if token['kind'] != kind or token.get('tag') != tag or token['offset'] != cursor:
            raise ValueError('Sketch attribute payload kind/tag/contiguity mismatch')
        if kind == 'string':
            if not isinstance(value, str) or not 1 <= len(value) <= 128 or any(not 32 <= ord(c) <= 126 for c in value):
                raise ValueError('Sketch attribute requires bounded printable ASCII')
            raw = value.encode('ascii'); chunk = bytes((7, len(raw)))+raw
        else:
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError('Sketch schema requires typed integer literals')
            chunk = bytes((4,))+struct.pack('<q', value)
        encoded.extend(chunk); cursor += len(chunk)
        return value

    definition = read(5, 'string', 7)
    if definition != DEFINITION:
        raise ValueError('Unsupported sketch attribute definition')
    schema = [read(i, 'integer', 4) for i in (6, 7, 8)]
    if schema != [1, 1, 3]:
        raise ValueError('Unsupported sketch attribute schema')
    text = read(9, 'string', 7)
    fields = text.split(' ')
    if len(fields) != 6 or any(not f or any(c not in '0123456789' for c in f) for f in fields):
        raise ValueError('Unsupported sketch attribute six-decimal text layout')
    if cursor != record['end_offset']-1:
        raise ValueError('Sketch attribute replay does not consume exact payload extent')
    return {'definition_name': definition, 'stored_schema_fields': schema,
            'uninterpreted_text': text, 'stored_decimal_text_fields': fields,
            'payload_offset': tokens[5]['offset'], 'payload_end_offset': cursor,
            'payload_hex': bytes(encoded).hex(),
            'identity_scope': 'Six literal decimal text fields; native sketch/entity identities and flag semantics unresolved',
            'ownership_scope': 'Payload only; caller must validate initial typed owner and reciprocal attribute chain'}
