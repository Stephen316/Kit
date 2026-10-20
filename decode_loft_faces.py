"""Observed solid Loft from one BRep face/edge to a sketch profile.

BRep recipes and historical body ownership are explicit. Exact face/edge geometry
and alignment flags are not reconstructed from opaque recipe indices.
"""

import struct
import uuid

from decode_body_selections import decode_body_selections
from decode_brep_recipes import decode_recipe
from decode_face_selections import resolve_native_faces
from decode_loft_modes import SECTION_GUID, decode_loft_modes
from decode_loft_operations import resolve_loft_profiles
from decode_parameters import read_string
from decode_selection import native_proxy_references
from decode_sketch import reference


PROXY = '2CA5A1CD-C99B-4C9B-91AF-57989148E841'
TOPOLOGY = '5662F619-2281-4AD9-93DC-1FCFDA1062E7'


def resolve_loft_face_section(data, records, section_id, feature, features):
    owner = feature['object_id']
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: values[0] for identity, values in grouped.items() if len(values) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Loft face/edge typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]

    _, section = typed(section_id, SECTION_GUID)
    if len(section) != 36 or section[:10] != b'\0'*10 or reference(section, 10) != owner:
        raise ValueError('Unsupported Loft face/edge section layout/owner')
    selection_id = reference(section, 21)
    code = struct.unpack_from('<I', section, 32)[0]
    if code == 2:
        profiles = resolve_loft_profiles(data, records, selection_id, owner, features)
        if len(profiles) != 1:
            raise ValueError('Only observed one destination profile in face Loft supported')
        return {'profile': profiles[0]}
    if code == 3:
        selected = resolve_native_faces(data, records, selection_id, owner)
        if selected['attributes'] or len(selected['faces']) != 1:
            raise ValueError('Only observed one source face in Loft supported')
        face = selected['faces'][0]
        if face['recipe']['payload_kind'] != 'bounded_face_recipe_data':
            raise ValueError('Unobserved Loft source face recipe kind')
        return {'face': {'selection_record_object_id': selection_id, **face,
                         'stored_section_code': code,
                         'geometry_status': 'API source is a planar cylinder end face; exact native recipe-to-ASM face mapping unresolved'}}
    if code != 7:
        raise ValueError('Unsupported Loft topology section kind')
    proxy_record, proxy = typed(selection_id, PROXY)
    if reference(proxy, len(proxy)-11) != owner:
        raise ValueError('Loft edge section proxy owner disagrees')
    descriptors, props = native_proxy_references(data, proxy_record)
    if props or len(descriptors) != 1:
        raise ValueError('Only observed single owned edge descriptor in Loft section supported')
    identity = descriptors[0]
    _, descriptor = typed(identity, TOPOLOGY)
    if (len(descriptor) != 276 or descriptor[:4] != b'\0\0\0\1'
            or struct.unpack_from('<I', descriptor, 15)[0] != 1
            or reference(descriptor, len(descriptor)-11) != owner):
        raise ValueError('Unsupported Loft edge descriptor prefix/layout/owner')
    recipe_id = reference(descriptor, 4)
    recipe_record, _ = typed(recipe_id, '7ACC2A03-0261-4879-A14A-A93D661A5BDC')
    recipe = decode_recipe(data, recipe_record, primary)
    if recipe['payload_kind'] != 'edge_recipe_data':
        raise ValueError('Loft edge section recipe kind disagrees')
    namespace, cursor = read_string(descriptor, 19)
    entity_uuid, cursor = read_string(descriptor, cursor)
    if len(namespace) != 36 or len(entity_uuid) != 36:
        raise ValueError('Unsupported Loft edge namespace fields')
    uuid.UUID(namespace)
    uuid.UUID(entity_uuid)
    if descriptor[cursor:cursor+12] != struct.pack('<QI', 2, 1):
        raise ValueError('Unsupported Loft edge context count')
    context_id = reference(descriptor, cursor+12)
    typed(context_id, 'C46D3EEB-40E1-43FA-83DC-9CB204335417')
    cursor += 23
    if struct.unpack_from('<I', descriptor, cursor)[0] != 1 or len(descriptor)-(cursor+15) != 67:
        raise ValueError('Unsupported Loft edge body-anchor/trailer framing')
    anchor_id = reference(descriptor, cursor+4)
    anchors = [a for a in decode_body_selections(data, records)['body_anchors'] if a['object_id'] == anchor_id]
    if len(anchors) != 1:
        raise ValueError('Loft edge historical body anchor unresolved')
    anchor = anchors[0]
    return {'edge': {'selection_record_object_id': selection_id, 'descriptor_object_id': identity,
                     'stored_section_code': code, 'stored_descriptor_flag_at_3': descriptor[3],
                     'recipe': recipe, 'body_anchor_object_id': anchor_id,
                     'native_body_object_id': anchor['native_body_object_id'],
                     'source_owner_object_id': anchor['source_owner_object_id'],
                     'context_record_object_ids': [context_id],
                     'namespace_text': namespace, 'entity_guid_text': entity_uuid,
                     'representation_status': 'Captured documented one-edge Path input normalizes to actual API BRepEdge section',
                     'identity_scope': 'Owned edge recipe and typed historical body anchor; exact ASM edge/curve identity unresolved',
                     'context_scope': 'Explicit typed context retained; coordinate transform unresolved'}}


def decode_loft_faces(data, records, body, feature, features):
    result = decode_loft_modes(data, records, body, feature, features,
                               section_resolver=resolve_loft_face_section, allow_edge_end_conditions=True)
    if (result['operation'] != 'NewBody' or not result['is_solid'] or result['is_closed']
            or result['guide_count'] or result['section_count'] != 2):
        raise ValueError('Only observed two-section open solid NewBody face/edge Loft without guides supported')
    first, last = result['sections']
    if 'profile' not in last or last['end_condition']['type'] != 'Free':
        raise ValueError('Observed face/edge Loft requires final Free sketch profile')
    if 'face' in first:
        if first['end_condition']['type'] != 'Free':
            raise ValueError('Only observed Free BRepFace Loft start supported')
        source_kind = 'BRepFace'
    elif 'edge' in first:
        if first['end_condition']['type'] not in ('Tangent', 'Smooth'):
            raise ValueError('Only observed Tangent/Smooth BRepEdge Loft start supported')
        source_kind = 'BRepEdge'
    else:
        raise ValueError('Observed face/edge Loft requires first BRepFace or BRepEdge section')
    cursor = result['result_anchor_list_end_relative_offset']
    if body[cursor:cursor+8] != b'\0'*8 or struct.unpack_from('<I', body, cursor+8)[0] != 36:
        raise ValueError('Unobserved face/edge Loft post-anchor input list')
    anchors = decode_body_selections(data, records)['body_anchors']
    for identity in result['result_body_anchor_object_ids']:
        matches = [a for a in anchors if a['object_id'] == identity and a['source_owner_object_id'] == feature['object_id']]
        if len(matches) != 1:
            raise ValueError('Loft result anchor source owner disagrees')
    result.update(source_section_kind=source_kind,
                  input_body_selection_record_object_ids=[], input_bodies=[],
                  start_edge_alignment=None, end_edge_alignment=None,
                  edge_alignment_status='Actual captured API alignment enums are0; native alignment encoding is not independently identified',
                  section_selection_status='Explicit face/edge recipe and historical native body at start, explicit sketch profile membership at end; exact topology unresolved',
                  scope='Captured Free face start or positive-weight Tangent/Smooth edge start with Free profile end; no topology regeneration')
    return result
