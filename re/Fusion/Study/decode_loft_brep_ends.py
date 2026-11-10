"""Observed Loft Free-edge, face-end and weighted BRep-edge endpoint variants.

Uses the prior strict source reader where applicable. The newly captured
zero-flag topology descriptor has its own bounded reader; the flag's meaning,
exact topology identities and alignment encodings remain unresolved.
"""

import struct
import uuid

from decode_body_selections import decode_body_selections
from decode_brep_recipes import decode_recipe
from decode_loft_faces import PROXY, TOPOLOGY, resolve_loft_face_section
from decode_loft_modes import SECTION_GUID, decode_loft_modes
from decode_parameters import read_string
from decode_selection import native_proxy_references
from decode_sketch import reference


def resolve_loft_brep_end_section(data, records, section_id, feature, features):
    owner = feature['object_id']
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: items[0] for identity, items in grouped.items() if len(items) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Loft BRep endpoint typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]

    _, section = typed(section_id, SECTION_GUID)
    if (len(section) != 36 or section[:10] != b'\0'*10
            or reference(section, 10) != owner):
        raise ValueError('Unsupported Loft BRep endpoint section layout/owner')
    code = struct.unpack_from('<I', section, 32)[0]
    if code != 7:
        return resolve_loft_face_section(data, records, section_id, feature, features)
    selection_id = reference(section, 21)
    proxy_record, proxy = typed(selection_id, PROXY)
    if reference(proxy, len(proxy)-11) != owner:
        raise ValueError('Loft BRep endpoint proxy owner disagrees')
    identities, props = native_proxy_references(data, proxy_record)
    if props or len(identities) != 1:
        raise ValueError('Only observed one owned endpoint edge descriptor supported')
    identity = identities[0]
    _, descriptor = typed(identity, TOPOLOGY)
    if len(descriptor) < 4:
        raise ValueError('Truncated Loft endpoint edge descriptor')
    if descriptor[3] == 1:
        return resolve_loft_face_section(data, records, section_id, feature, features)
    if (len(descriptor) != 276 or descriptor[:4] != b'\0'*4
            or struct.unpack_from('<I', descriptor, 15)[0] != 1
            or reference(descriptor, len(descriptor)-11) != owner):
        raise ValueError('Unsupported zero-flag Loft edge descriptor layout/owner')
    recipe_id = reference(descriptor, 4)
    recipe_record, _ = typed(recipe_id, '7ACC2A03-0261-4879-A14A-A93D661A5BDC')
    recipe = decode_recipe(data, recipe_record, primary)
    if recipe['payload_kind'] != 'edge_recipe_data':
        raise ValueError('Loft endpoint edge recipe kind disagrees')
    namespace, cursor = read_string(descriptor, 19)
    entity_uuid, cursor = read_string(descriptor, cursor)
    if len(namespace) != 36 or len(entity_uuid) != 36:
        raise ValueError('Unsupported Loft endpoint edge namespace fields')
    uuid.UUID(namespace)
    uuid.UUID(entity_uuid)
    if descriptor[cursor:cursor+12] != struct.pack('<QI', 2, 1):
        raise ValueError('Unsupported Loft endpoint edge context count')
    context_id = reference(descriptor, cursor+12)
    typed(context_id, 'C46D3EEB-40E1-43FA-83DC-9CB204335417')
    cursor += 23
    if struct.unpack_from('<I', descriptor, cursor)[0] != 1 or len(descriptor)-(cursor+15) != 67:
        raise ValueError('Unsupported Loft endpoint edge anchor/trailer framing')
    anchor_id = reference(descriptor, cursor+4)
    anchors = [a for a in decode_body_selections(data, records)['body_anchors'] if a['object_id'] == anchor_id]
    if len(anchors) != 1:
        raise ValueError('Loft endpoint edge historical body anchor unresolved')
    anchor = anchors[0]
    return {'edge': {'selection_record_object_id': selection_id, 'descriptor_object_id': identity,
                     'stored_section_code': code, 'stored_descriptor_flag_at_3': 0,
                     'recipe': recipe, 'body_anchor_object_id': anchor_id,
                     'native_body_object_id': anchor['native_body_object_id'],
                     'source_owner_object_id': anchor['source_owner_object_id'],
                     'context_record_object_ids': [context_id],
                     'namespace_text': namespace, 'entity_guid_text': entity_uuid,
                     'representation_status': 'Captured documented one-edge Path input normalizes to actual API BRepEdge section',
                     'identity_scope': 'Owned edge recipe and typed historical body anchor; exact ASM edge/curve identity unresolved',
                     'context_scope': 'Explicit typed context retained; descriptor flag meaning and coordinate transform unresolved'}}


def decode_loft_brep_ends(data, records, body, feature, features):
    result = decode_loft_modes(data, records, body, feature, features,
                               section_resolver=resolve_loft_brep_end_section, allow_edge_end_conditions=True)
    if (result['operation'] != 'NewBody' or not result['is_solid'] or result['is_closed']
            or result['guide_count'] or result['section_count'] != 2):
        raise ValueError('Only observed two-section open solid NewBody BRep endpoints without guides supported')
    sections = result['sections']
    kinds = tuple('edge' if 'edge' in s else 'face' if 'face' in s else 'profile' for s in sections)
    conditions = tuple(s['end_condition']['type'] for s in sections)
    allowed = {
        (('edge', 'profile'), ('Free', 'Free')): 'FreeEdgeStart',
        (('profile', 'face'), ('Free', 'Free')): 'FreeFaceEnd',
        (('profile', 'edge'), ('Free', 'Tangent')): 'TangentEdgeEnd',
        (('profile', 'edge'), ('Free', 'Smooth')): 'SmoothEdgeEnd',
        (('edge', 'edge'), ('Tangent', 'Tangent')): 'TangentBothEdges',
    }
    configuration = allowed.get((kinds, conditions))
    if configuration is None:
        raise ValueError('Unobserved Loft BRep endpoint section/condition combination')
    for index, section in enumerate(sections):
        if 'edge' in section and section['edge']['stored_descriptor_flag_at_3'] != (1 if index == 0 else 0):
            raise ValueError('Unobserved Loft endpoint/descriptor flag combination; flag semantics unresolved')
    if kinds == ('edge', 'edge'):
        first, last = (s['edge'] for s in sections)
        if (first['native_body_object_id'] == last['native_body_object_id']
                or first['source_owner_object_id'] == last['source_owner_object_id']):
            raise ValueError('Only captured distinct historical source bodies for both-edge Loft supported')
    cursor = result['result_anchor_list_end_relative_offset']
    if body[cursor:cursor+8] != b'\0'*8 or struct.unpack_from('<I', body, cursor+8)[0] != 36:
        raise ValueError('Unobserved BRep endpoint Loft post-anchor input list')
    anchors = decode_body_selections(data, records)['body_anchors']
    for identity in result['result_body_anchor_object_ids']:
        if len([a for a in anchors if a['object_id'] == identity and a['source_owner_object_id'] == feature['object_id']]) != 1:
            raise ValueError('Loft BRep endpoint result-anchor source owner disagrees')
    result.update(brep_endpoint_configuration=configuration,
                  section_kinds=[{'edge': 'BRepEdge', 'face': 'BRepFace', 'profile': 'Profile'}[k] for k in kinds],
                  input_body_selection_record_object_ids=[], input_bodies=[],
                  start_edge_alignment=None, end_edge_alignment=None,
                  edge_alignment_status='Captured API alignments are0; native alignment encoding not independently identified',
                  section_selection_status='Ordered owned BRep recipes/historical source bodies or sketch-profile memberships; exact BRep topology unresolved',
                  scope='Captured Free edge start/face end, weighted edge end, or two tangent edges; open solid NewBody/two sections/no guides')
    return result
