"""Observed inherited COMPONENT prefix and raw display-color float32 channels.

The controlled componentColor getter/setter capture establishes channel order.
This reader does not derive RGB8, alpha, color space or material appearance.
"""
import math
import struct

from decode_assembly import COMPONENT_GUID
from decode_sketch import reference

PRIMARY_COMPONENT = 'E03784ED-5E19-4E14-B9F2-3B07017018CD'
PREFIX_REFERENCE_CLASSES = (
    '0C5DAB90-715E-49EA-A56E-E30F2328F43E', '47C245A2-2DBE-4B1F-9C56-762F373BB0C8',
    'AC202226-A700-462A-BC41-13631C9E95D5', '596C8B98-D176-4E40-B294-6404BAD566BC',
    'CD57BC48-50EC-47DC-975A-FB6DEA72F4DA', '0DBF95ED-82D2-4CC4-936D-642370679CBB',
    'FCB17D75-8538-4E8E-BDBE-CB4FE2120DB7', '77EF6384-409E-498D-8167-BCA537533B35',
    'B0556F58-EE09-46A7-B18F-E296F48E5B13', '30DCFC57-8E13-405B-9295-5CF74AC1FB39',
    '5275CBA4-3D7D-40DC-A651-1DFF3FC8AFBF', '372234A0-2A6C-4122-8047-E74DBA04F326',
    'A8635B5F-1E2C-45FD-8BA9-0173B0FEB75E')
ADJACENT_BYTES = bytes.fromhex('0000803f01010000')
SCOPE = 'Observed inherited COMPONENT base-prefix grammar and reciprocal typed reference runs qualify raw red/green/blue float32 display-color fields; no general RGB8 quantization, alpha, color space or appearance inference'


def decode_component_display_colors(data, records):
    """Return decoded/unresolved/scope; caller supplies indexed metadata records."""
    grouped = {}
    components = {}
    for r in records:
        if r.is_primary: grouped.setdefault(r.object_id, []).append(r)
        if r.class_guid == COMPONENT_GUID: components.setdefault(r.object_id, []).append(r)
    primary = {identity: rows[0] for identity, rows in grouped.items() if len(rows) == 1}
    decoded, unresolved = [], []
    for identity, rows in components.items():
        try:
            if len(rows) != 1: raise ValueError('Ambiguous inherited COMPONENT base record')
            record = rows[0]; owner = primary.get(identity)
            if (record.is_primary or owner is None or owner.class_guid != PRIMARY_COMPONENT
                    or record.payload_start is None or record.body != record.payload_start+4
                    or not 0 <= record.payload_start <= record.body < record.end <= len(data)
                    or data[record.payload_start:record.body] != bytes(4)):
                raise ValueError('Unsupported indexed COMPONENT inheritance/leading prefix')
            body = data[record.body:record.end]; cursor = 0; encoded = bytearray(bytes(4)); links = []
            def references(count):
                nonlocal cursor
                for _ in range(count):
                    slot = len(links); start = cursor; target = reference(body, cursor)
                    referenced = primary.get(target)
                    if referenced is None or referenced.class_guid != PREFIX_REFERENCE_CLASSES[slot]:
                        raise ValueError('COMPONENT prefix typed reference class/identity disagrees')
                    payload = data[referenced.body:referenced.end]
                    if reference(payload, len(payload)-11) != identity:
                        raise ValueError('COMPONENT prefix referenced record owner is not reciprocal')
                    encoded.extend(b'\1'+struct.pack('<Q', target)+bytes(2)); cursor += 11
                    links.append({'slot': slot, 'object_id': target, 'class_guid': referenced.class_guid,
                                  'reference_offset_from_component_body': start,
                                  'reciprocal_owner_reference_offset': referenced.end-11})
            def null():
                nonlocal cursor
                if body[cursor:cursor+1] != b'\0': raise ValueError('Unsupported COMPONENT prefix reference separator')
                encoded.extend(b'\0'); cursor += 1
            references(2)
            scalars = list(struct.unpack_from('<4d', body, cursor))
            if scalars != [-1., -1., -1., -1.]: raise ValueError('Unsupported COMPONENT prefix scalar quartet')
            encoded.extend(struct.pack('<4d', *scalars)); cursor += 32
            references(7); null(); references(4); null()
            literal = struct.unpack_from('<I', body, cursor)[0]
            encoded.extend(struct.pack('<I', literal)); cursor += 4
            color_start = cursor; values = list(struct.unpack_from('<3f', body, cursor))
            if not all(math.isfinite(value) and 0 <= value <= 1 for value in values):
                raise ValueError('COMPONENT color float32 channels outside observed finite unit interval')
            color_bytes = struct.pack('<3f', *values); encoded.extend(color_bytes); cursor += 12
            adjacent = body[cursor:cursor+8]
            if adjacent != ADJACENT_BYTES: raise ValueError('Unsupported COMPONENT color-adjacent literal framing')
            encoded.extend(adjacent); cursor += 8
            if bytes(encoded) != data[record.payload_start:record.body+cursor]:
                raise ValueError('COMPONENT framed prefix exact replay disagrees')
            decoded.append({'component_object_id': identity, 'primary_class_guid': owner.class_guid,
                'component_base_class_guid': record.class_guid, 'component_base_record_offset': record.start,
                'component_base_body_offset': record.body, 'inherited_component_record': True,
                'prefix_references': links, 'stored_prefix_scalar_float64': scalars,
                'stored_pre_color_uint32_literal': literal,
                'color_offset_from_component_body': color_start, 'color_offset': record.body+color_start,
                'stored_component_color_rgb_float32': dict(zip(('red', 'green', 'blue'), values)),
                'stored_rgb_float32_bytes_hex': color_bytes.hex(),
                'stored_color_adjacent_bytes_hex': adjacent.hex(),
                'framed_prefix_offset': record.payload_start, 'framed_prefix_end_offset': record.body+cursor,
                'framed_prefix_hex': bytes(encoded).hex(),
                'unparsed_component_tail_offset': record.body+cursor,
                'color_scope': 'Observed componentColor red/green/blue storage channels; raw float32 only, no derived RGB8/alpha/color-space/material appearance',
                'display_scope': 'Component-color assignment only; whether Display Component Colors is enabled is not decoded',
                'prefix_scope': 'Bounded observed typed-reference runs and reciprocal owners; scalar quartet, uint32 literal and following8 bytes retained without further meaning'})
        except (ValueError, KeyError, IndexError, TypeError, struct.error) as error:
            unresolved.append({'component_object_id': identity, 'reason': str(error)})
    return {'decoded': decoded, 'unresolved': unresolved, 'scope': SCOPE}
