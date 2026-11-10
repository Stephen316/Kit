"""Observed two-section solid Loft with one explicit sketch-point endpoint.

Point references resolve by typed descriptor/leaf sketch ID and entity tag.
Cached endpoint coordinates cross-check placement; they never choose a point.
"""

import struct
import uuid

from decode_loft_modes import SECTION_GUID, decode_loft_modes
from decode_loft_operations import resolve_loft_profiles
from decode_parameters import read_string
from decode_selection import native_proxy_references
from decode_sketch import numbers, reference, same


PROXY = '2CA5A1CD-C99B-4C9B-91AF-57989148E841'
DESCRIPTOR = '5A1BF548-241F-46FD-9FB5-E4B05126EB9D'
POINT_LEAF = 'D95DBAC0-238B-4429-A0AD-4AE5BEE79ADF'
SUPPORT = '6CCF41D5-40BE-48ED-A834-18F3EAED6C57'
HELPER = '5FBE538E-139B-46D4-BCAF-CC796D1E1F78'
POINT_CONTEXT = '994C518A-A831-400A-B7C7-16DAC55F4F1C'


def resolve_loft_point_section(data, records, section_id, feature, features):
    owner_id = feature['object_id']

    def typed(identity, guid):
        matches = [r for r in records if r.is_primary and r.object_id == identity and r.class_guid == guid]
        if len(matches) != 1:
            raise ValueError('Loft point typed reference missing, ambiguous or wrong class')
        record = matches[0]
        return record, data[record.body:record.end]

    _, section = typed(section_id, SECTION_GUID)
    if len(section) == 36:
        if (section[:10] != b'\0'*10 or reference(section, 10) != owner_id
                or struct.unpack_from('<I', section, 32)[0] != 2):
            raise ValueError('Unsupported Loft profile section/owner')
        profiles = resolve_loft_profiles(data, records, reference(section, 21), owner_id, features)
        if len(profiles) != 1:
            raise ValueError('Only one profile in observed point Loft section supported')
        return {'profile': profiles[0]}
    if (len(section) != 60 or section[:6] != b'\0\0\1\0\0\0' or section[30:34] != b'\0'*4
            or reference(section, 34) != owner_id or struct.unpack_from('<I', section, 56)[0] != 4):
        raise ValueError('Unsupported Loft point section/owner')
    cached_position = numbers(section, 6, 3)
    selection_id = reference(section, 45)
    proxy, payload = typed(selection_id, PROXY)
    if len(payload) != 105 or reference(payload, 94) != owner_id:
        raise ValueError('Unsupported Loft point proxy layout/owner')
    descriptors, props = native_proxy_references(data, proxy)
    if props or len(descriptors) != 1:
        raise ValueError('Unsupported Loft point proxy descriptor list')
    descriptor_id = descriptors[0]
    _, descriptor = typed(descriptor_id, DESCRIPTOR)
    if (len(descriptor) != 263 or descriptor[:2] != b'\0\0'
            or struct.unpack_from('<I', descriptor, 13)[0] != 1
            or reference(descriptor, 252) != owner_id):
        raise ValueError('Unsupported Loft point descriptor layout/owner')
    namespace, cursor = read_string(descriptor, 17)
    entity_uuid, cursor = read_string(descriptor, cursor)
    for text in (namespace, entity_uuid):
        if len(text) != 36:
            raise ValueError('Unsupported Loft point UUID field')
        uuid.UUID(text)
    if descriptor[cursor:cursor+12] != struct.pack('<QI', 2, 1):
        raise ValueError('Unsupported Loft point descriptor context list')
    context_id = reference(descriptor, cursor+12)
    _, context = typed(context_id, POINT_CONTEXT)
    if len(context) not in (38, 166):
        raise ValueError('Unsupported Loft point context payload')
    leaf_id = reference(descriptor, 2)
    _, leaf = typed(leaf_id, POINT_LEAF)
    if len(leaf) != 18 or leaf[:2] != b'\0\0':
        raise ValueError('Unsupported Loft point leaf')
    sketch_id, tag = struct.unpack_from('<QQ', leaf, 2)
    sketches = [f for f in features if f['kind'] == 'Sketch' and f['sketch_object_id'] == sketch_id]
    if len(sketches) != 1:
        raise ValueError('Loft point sketch missing or ambiguous')
    sketch = sketches[0]
    points = [g for g in sketch.get('geometry', []) if g['kind'] == 'Point' and g['entity_tag'] == tag]
    if len(points) != 1:
        raise ValueError('Loft point entity tag missing or ambiguous')
    selected_point = points[0]

    def reciprocal_support(payload, cursor, source, support_owner, repeated):
        if (payload[cursor+18:cursor+22] != b'\1\1\0\0'
                or payload[cursor+30:cursor+34] != b'\1\1\0\0'
                or payload[cursor+45:cursor+48] != b'\1\0\0' or payload[cursor+59] != 0):
            raise ValueError('Unsupported Loft point selection trailer')
        numbers(payload, cursor+22, 1)
        helper_id, support_id = reference(payload, cursor+34), reference(payload, cursor+48)
        typed(helper_id, HELPER)
        _, support = typed(support_id, SUPPORT)
        count = 2 if repeated else 1
        if (len(support) != 39+19*count or support[:12] != b'\0'*6+b'\1\1'+struct.pack('<I', count)
                or reference(support, 12) != source or reference(support, 31) != support_owner
                or (repeated and reference(support, 50) != support_owner) or support[-8:] != b'\0'*8):
            raise ValueError('Loft point selection support references are not reciprocal')
        return support_id

    proxy_support = reciprocal_support(payload, 34, descriptor_id, selection_id, False)
    descriptor_support = reciprocal_support(descriptor, 192, sketch['object_id'], descriptor_id, True)
    component_position = selected_point.get('component_position_cm')
    if component_position is not None and not same(cached_position, component_position):
        raise ValueError('Loft point section cache disagrees with explicitly selected point placement')
    return {'point': {'selection_record_object_id': selection_id, 'descriptor_object_id': descriptor_id,
                      'terminal_object_id': leaf_id, 'sketch_object_id': sketch_id, 'sketch_name': sketch['name'],
                      'point_object_id': selected_point['object_id'], 'point_entity_tag': tag,
                      'position_cm': selected_point['position_cm'],
                      'component_position_cm': component_position, 'cached_section_position_cm': cached_position,
                      'proxy_support_record_object_id': proxy_support, 'descriptor_support_record_object_id': descriptor_support,
                      'context_record_object_id': context_id,
                      'context_payload_hex': context.hex(),
                      'context_status': 'Typed observed 38/166-byte point context retained; coordinate-frame payload semantics unresolved',
                      'association': 'Owned section/proxy/descriptor and reciprocal supports select typed sketch ID and point tag',
                      'scope': 'Explicit selected point membership; cached section position is independently cross-checked when sketch placement is available'}}


def decode_loft_points(data, records, body, feature, features):
    result = decode_loft_modes(data, records, body, feature, features,
                               allow_point_end_conditions=True, section_resolver=resolve_loft_point_section)
    if (result['operation'] != 'NewBody' or not result['is_solid'] or result['is_closed']
            or result['guide_count'] or result['section_count'] != 2):
        raise ValueError('Only observed open solid two-section NewBody point Loft without guides supported')
    point_sections = [s for s in result['sections'] if 'point' in s]
    if len(point_sections) != 1:
        raise ValueError('Observed point Loft requires exactly one point section')
    point_index = point_sections[0]['index']
    for section in result['sections']:
        expected = ('PointSharp', 'PointTangent') if 'point' in section else ('Free',)
        if section['end_condition']['type'] not in expected:
            raise ValueError('Loft endpoint condition disagrees with explicit point/profile section')
    if point_index == 0 and point_sections[0]['end_condition']['type'] != 'PointSharp':
        raise ValueError('PointTangent at start remains unverified')
    cursor = result['result_anchor_list_end_relative_offset']
    if body[cursor:cursor+8] != b'\0'*8 or struct.unpack_from('<I', body, cursor+8)[0] != 36:
        raise ValueError('Unobserved point Loft post-anchor input list')
    result.update(input_body_selection_record_object_ids=[], input_bodies=[],
                  point_section_count=1,
                  section_selection_status='Explicit ordered profile and sketch-point sections; point identified by native sketch ID/tag with reciprocal owners',
                  point_scope='Captured sharp point at start/end and tangent point at end with positive weight; other point-section combinations remain unsupported')
    return result
