"""Bounded literal generic_tag_attrib_def counted naming payloads.

Owner links, attribute chains, entity kinds, coverage and semantic identity are
intentionally the caller's responsibility. Signed32 components and their exact
unsigned32 bit interpretations are preserved without promoting them to IDs.
"""

import struct

DEFINITION = 'generic_tag_attrib_def'


def decode_counted_asm_name(record):
    """Return existing generic-tag payload dictionary fields, with typed replay.

    Proven term counts1/2/3/4/5/6/8 and component counts0/1/2/3 only. Offsets refer to the
    supplied serialized record; callers must compare payload_hex with the actual
    blob bytes and independently qualify owner/coverage before any association.
    """
    tokens = record['tokens']
    if record['name'] != 'ATTRIB_CUSTOM-attrib' or len(tokens) < 11:
        raise ValueError('Counted ASM name requires the observed custom attribute payload')
    encoded = bytearray()
    cursor = 5
    def integer(low, high):
        nonlocal cursor
        token = tokens[cursor]; cursor += 1
        value = token['value']
        if (token['kind'] != 'integer' or token.get('tag') != 4 or not isinstance(value, int)
                or isinstance(value, bool) or not low <= value <= high):
            raise ValueError('Counted ASM naming integer token kind/range mismatch')
        encoded.extend(b'\x04'+struct.pack('<q', value))
        return value
    def text():
        nonlocal cursor
        token = tokens[cursor]; cursor += 1
        value = token['value']
        if (token['kind'] != 'string' or token.get('tag') != 7 or not isinstance(value, str)
                or not 1 <= len(value) <= 128 or any(not 32 <= ord(c) <= 126 for c in value)):
            raise ValueError('Counted ASM naming string is not bounded printable ASCII')
        raw = value.encode('ascii')
        encoded.extend(bytes((7, len(raw)))+raw)
        return value
    definition = text()
    schema = [integer(-1, 3) for _ in range(3)]
    namespace = text()
    if definition != DEFINITION or schema != [3, 3, -1] or namespace != DEFINITION+' ':
        raise ValueError('Unobserved counted ASM naming definition/schema/namespace')
    count = integer(1, 8)
    if count not in (1, 2, 3, 4, 5, 6, 8):
        raise ValueError('Unobserved counted ASM naming term count')
    terms = []
    for _ in range(count):
        size = integer(1, 128)
        name = text()
        if len(name.encode('ascii')) != size:
            raise ValueError('Counted ASM naming explicit byte length disagrees')
        index = integer(0, 0xffffffff)
        component_count = integer(0, 3)
        components = [integer(-0x80000000, 0x7fffffff) for _ in range(component_count)]
        terminator = integer(0, 0)
        terms.append({'name': name, 'stored_index': index,
                      'stored_reference_component_count': component_count,
                      'stored_reference_components_int32': components,
                      'stored_reference_components_uint32': [value & 0xffffffff for value in components],
                      'stored_reference_terminator_uint32': terminator})
    if cursor != len(tokens):
        raise ValueError('Unconsumed counted ASM naming payload fields')
    start, end = tokens[5]['offset'], record['end_offset']-1
    if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end-start != len(encoded):
        raise ValueError('Counted ASM naming replay length differs from source payload bounds')
    return {'definition_name': definition, 'stored_definition_schema_fields': schema,
            'stored_namespace_text': namespace, 'stored_term_count': count, 'terms': terms,
            'payload_offset': start, 'payload_end_offset': end, 'payload_hex': bytes(encoded).hex()}
