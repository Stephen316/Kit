"""Observed alternate Sweep inputs: face, open curve/edge, two closed profiles.

BRep selections retain historical body anchors and topology recipes; exact ASM
face/edge identity and the feature's cached header vector meaning stay unresolved.
"""

import struct
import uuid

from decode_body_selections import decode_body_selections
from decode_brep_recipes import decode_recipe
from decode_face_selections import resolve_native_faces
from decode_parameters import read_string
from decode_profile_selections import resolve_sketch_profiles
from decode_selection import native_proxy_references, resolve_single_sketch_curve
from decode_sketch import reference
from decode_sweep_modes import decode_sweep_modes


PROXY = '2CA5A1CD-C99B-4C9B-91AF-57989148E841'
TOPOLOGY = '5662F619-2281-4AD9-93DC-1FCFDA1062E7'
CURVE = '5A1BF548-241F-46FD-9FB5-E4B05126EB9D'
PROFILE = '4BD53E5A-0B3E-45E5-AE8B-02044306485A'


def resolve_sweep_profiles(data, records, selection_id, owner_id, features):
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {i: items[0] for i, items in grouped.items() if len(items) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Alternate Sweep profile typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]

    record, proxy = typed(selection_id, PROXY)
    if reference(proxy, len(proxy)-11) != owner_id:
        raise ValueError('Alternate Sweep profile proxy owner disagrees')
    descriptor_ids, props = native_proxy_references(data, record)
    if props or len(descriptor_ids) != 1:
        raise ValueError('Only observed single-descriptor alternate Sweep profile proxy supported')
    identity = descriptor_ids[0]
    descriptor = primary.get(identity)
    if descriptor is None:
        raise ValueError('Alternate Sweep profile descriptor unresolved')
    if descriptor.class_guid == PROFILE:
        profiles = resolve_sketch_profiles(data, records, selection_id, owner_id, features)
        if len(profiles) != 2 or any(p.get('source_profile_set_count') != 2 for p in profiles):
            raise ValueError('Only observed two-set closed Sweep profile collection supported here')
        return [{'kind': 'SketchProfile', **p} for p in profiles]
    if descriptor.class_guid == CURVE:
        source = resolve_single_sketch_curve(data, records, selection_id, owner_id, features, ('Line',))
        sketch = next(f for f in features if f['kind'] == 'Sketch' and f['sketch_object_id'] == source['sketch_object_id'])
        source['sketch_name'] = sketch['name']
        return [{'kind': 'SketchCurvePath', 'selection_record_object_id': selection_id,
                 'segments': [source], 'count': 1, 'is_closed': False,
                 'scope': 'Explicit one-Line sketch ID/tag; API returns a Path for this open profile'}]
    if descriptor.class_guid != TOPOLOGY:
        raise ValueError('Unsupported alternate Sweep profile descriptor class')
    _, payload = typed(identity, TOPOLOGY)
    if (payload[:4] != b'\0'*4 or struct.unpack_from('<I', payload, 15)[0] != 1
            or reference(payload, len(payload)-11) != owner_id):
        raise ValueError('Unsupported alternate Sweep topology profile prefix/owner')
    recipe_id = reference(payload, 4)
    recipe_record, _ = typed(recipe_id, '7ACC2A03-0261-4879-A14A-A93D661A5BDC')
    recipe = decode_recipe(data, recipe_record, primary)
    if recipe['payload_kind'] == 'bounded_face_recipe_data':
        selected = resolve_native_faces(data, records, selection_id, owner_id)
        if selected['attributes'] or len(selected['faces']) != 1:
            raise ValueError('Only observed single BRepFace Sweep profile supported')
        return [{'kind': 'BRepFace', 'selection_record_object_id': selection_id, **selected['faces'][0],
                 'geometry_status': 'Captured API selection is planar; exact native recipe-to-ASM face and plane reconstruction unresolved'}]
    if recipe['payload_kind'] != 'edge_recipe_data':
        raise ValueError('Unsupported alternate Sweep topology profile recipe kind')
    namespace, cursor = read_string(payload, 19)
    entity_uuid, cursor = read_string(payload, cursor)
    if len(namespace) != 36 or len(entity_uuid) != 36:
        raise ValueError('Unsupported alternate Sweep edge UUID lengths')
    uuid.UUID(namespace)
    uuid.UUID(entity_uuid)
    if payload[cursor:cursor+12] != struct.pack('<QI', 2, 1):
        raise ValueError('Unobserved alternate Sweep edge context list')
    context_id = reference(payload, cursor+12)
    typed(context_id, 'C46D3EEB-40E1-43FA-83DC-9CB204335417')
    cursor += 23
    if struct.unpack_from('<I', payload, cursor)[0] != 1 or len(payload)-(cursor+15) != 67:
        raise ValueError('Unobserved alternate Sweep edge anchor/trailer')
    anchor_id = reference(payload, cursor+4)
    anchors = [a for a in decode_body_selections(data, records)['body_anchors'] if a['object_id'] == anchor_id]
    if len(anchors) != 1:
        raise ValueError('Alternate Sweep edge historical body anchor unresolved')
    anchor = anchors[0]
    return [{'kind': 'BRepEdgePath', 'selection_record_object_id': selection_id,
             'descriptor_object_id': identity, 'body_anchor_object_id': anchor_id,
             'native_body_object_id': anchor['native_body_object_id'], 'source_owner_object_id': anchor['source_owner_object_id'],
             'recipe': recipe, 'context_record_object_ids': [context_id],
             'namespace_text': namespace, 'entity_guid_text': entity_uuid,
             'count': 1,
             'identity_scope': 'Explicit owned edge recipe and historical native body; exact ASM edge and geometric curve unresolved',
             'context_scope': 'Typed context identity retained; no occurrence transform inferred'}]


def decode_sweep_profiles(data, records, body, feature, features):
    result = decode_sweep_modes(data, records, body, feature, features,
                                profile_resolver=resolve_sweep_profiles, allow_two_sided=True,
                                allowed_header_vectors=((0., 0., 1.), (0., -1., 0.)),
                                allowed_new_body_anchor_counts=(1, 2))
    profiles = result['profiles']
    kinds = [p['kind'] for p in profiles]
    if kinds not in (['BRepFace'], ['SketchCurvePath'], ['BRepEdgePath'], ['SketchProfile', 'SketchProfile']):
        raise ValueError('Unobserved alternate Sweep profile combination')
    expected_solid = kinds in (['BRepFace'], ['SketchProfile', 'SketchProfile'])
    expected_vector = [0., -1., 0.] if kinds == ['BRepEdgePath'] else [0., 0., 1.]
    if (result['stored_mode_code'] != 2 or result['is_solid'] != expected_solid
            or result['stored_header_vector'] != expected_vector
            or len(result['result_body_anchors']) != len(profiles)):
        raise ValueError('Unobserved alternate Sweep control/profile/result combination')
    expected_values = {'AgainstDistance': 0., 'AgainstRailDistance': 1., 'AlongDistance': 1.,
                       'AlongRailDistance': 1., 'TaperAngle': 0., 'TwistAngle': 0.}
    if kinds == ['BRepEdgePath']:
        expected_values.update(AgainstDistance=result['stored_parameter_values']['AgainstDistance'], AlongDistance=0.)
        if not 0 < expected_values['AgainstDistance'] <= 1:
            raise ValueError('Unobserved BRep-edge profile active fraction')
    if (result['stored_parameter_values'] != expected_values or result['path']['count'] != 1
            or result['path']['segments'][0]['kind'] != 'Line'):
        raise ValueError('Only observed straight default-angle alternate Sweep profile parameter branches supported')
    cursor = result['result_anchor_list_end_relative_offset']
    if body[cursor:cursor+8] != b'\0'*8 or struct.unpack_from('<I', body, cursor+8)[0] != 36:
        raise ValueError('Unobserved alternate Sweep post-anchor input-body list')
    if kinds == ['BRepEdgePath']:
        result.update(path_fraction=result['stored_parameter_values']['AgainstDistance'],
                      active_distance_parameter_role='AgainstDistance',
                      distance_branch_status='Observed BRep-edge open profile, raw header(0,-1,0), mode2, Along0: AgainstDistance matches API distanceOne for full/partial and reversed source-line captures; other profile frames unverified')
    result.update(profile_input_kind={
        ('BRepFace',): 'BRepFace', ('SketchCurvePath',): 'SketchOpenProfile',
        ('BRepEdgePath',): 'BRepEdgeOpenProfile', ('SketchProfile', 'SketchProfile'): 'SketchProfileCollection'}[tuple(kinds)],
        profile_api_type='adsk::fusion::BRepFace' if kinds == ['BRepFace'] else 'adsk::core::ObjectCollection' if len(profiles) == 2 else 'adsk::fusion::Path',
        input_body_selection_record_object_ids=[], input_bodies=[],
        header_vector_status='Observed raw header vector retained; coordinate-frame meaning not assigned',
        input_selection_status='Explicit alternate profile membership/recipes and straight sketch path; BRep exact topology and profile traversal unresolved')
    return result
