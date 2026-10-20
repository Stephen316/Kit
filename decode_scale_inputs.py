"""Observed Scale Sketch inputs and separately framed BRepVertex references."""

import struct
import uuid

from decode_body_tools import decode_body_tool
from decode_brep_recipes import RECIPE_GUID, decode_recipe
from decode_parameters import read_string
from decode_sketch import numbers, reference, same

SCALE = 'D45FD6C4-161B-4240-BFAC-83A7C2C97A0C'
DESCRIPTOR = '5A1BF548-241F-46FD-9FB5-E4B05126EB9D'
LEAF = '90055C05-546C-4EE7-B3C9-3DD922AD0C9C'


def primary_records(records):
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    return {identity: items[0] for identity, items in grouped.items() if len(items) == 1}


def decode_scale_sketch(data, records, body, feature, known, features):
    """A bounded scalar-reader opt-in, followed by explicit native Sketch identity."""
    if feature['class_guid'] != SCALE or body[32:37] != bytes.fromhex('0101000000'):
        raise ValueError('Only observed uniform single-Sketch Scale layout supported')
    result = decode_body_tool(data, records, body, feature, known,
                             allowed_uniform_scale_prefixes=(bytes.fromhex('0101000000'),))
    primary = primary_records(records)

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Scale Sketch typed reference missing, ambiguous or wrong class')
        return data[record.body:record.end]

    descriptor_id = reference(body, 37)
    descriptor = typed(descriptor_id, DESCRIPTOR)
    if (len(descriptor) != 252 or descriptor[:2] != bytes(2)
            or struct.unpack_from('<I', descriptor, 13)[0] != 1
            or reference(descriptor, 241) != feature['object_id']):
        raise ValueError('Unsupported Scale Sketch descriptor count/owner')
    namespace, cursor = read_string(descriptor, 17)
    entity_uuid, cursor = read_string(descriptor, cursor)
    for text in (namespace, entity_uuid):
        if len(text) != 36:
            raise ValueError('Unsupported Scale Sketch UUID length')
        uuid.UUID(text)
    if cursor != 169 or descriptor[cursor:cursor+12] != struct.pack('<QI', 2, 0):
        raise ValueError('Only observed root-context Scale Sketch descriptor supported')
    leaf_id = reference(descriptor, 2)
    leaf = typed(leaf_id, LEAF)
    if len(leaf) != 10 or leaf[:2] != bytes(2):
        raise ValueError('Unsupported Scale Sketch identity leaf')
    sketch_id = struct.unpack_from('<Q', leaf, 2)[0]
    matches = [s for s in features if s['kind'] == 'Sketch' and s['sketch_object_id'] == sketch_id]
    if len(matches) != 1:
        raise ValueError('Explicit Scale Sketch ID unresolved or ambiguous')
    sketch = matches[0]
    typed(sketch_id, '44A64366-4BD3-4B24-881A-F94C206E8F2D')
    result.update(input_kind='Sketch', input_count=1, input_body_count=0, input_face_count=0,
                  input_selections=[{'kind': 'Sketch', 'descriptor_object_id': descriptor_id,
                                     'terminal_object_id': leaf_id, 'sketch_object_id': sketch_id,
                                     'sketch_feature_object_id': sketch['object_id'], 'sketch_name': sketch['name'],
                                     'namespace_text': namespace, 'entity_guid_text': entity_uuid,
                                     'association': 'Owned typed descriptor and native Sketch-ID leaf; no geometry-based matching'}],
                  input_selection_status='Observed single root-context Sketch input; scale-history replay unsupported')
    return result


def decode_scale_vertex_points(data, records, features, body_selections):
    """Explicit selected vertex recipe, with geometry cache kept separately."""
    primary = primary_records(records)
    anchors = {a['object_id']: a for a in body_selections['body_anchors']}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Scale vertex typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]

    decoded, unresolved = [], []
    for feature in features:
        if feature['kind'] != 'Scale' or 'tool_settings' not in feature or feature['tool_settings'].get('point') is not None:
            continue
        try:
            owner = feature['object_id']
            record, body = typed(owner, SCALE)
            backend_id = reference(body, 10)
            _, backend = typed(backend_id, '69EE2FA7-BCC7-449E-9CA9-976CEFDFED44')
            if len(backend) != 178 or struct.unpack_from('<I', backend, 47)[0] != 1:
                continue  # The independent SketchPoint reader owns method10.
            if (backend[:23] != bytes(23) or struct.unpack_from('<I', backend, 75)[0] != 1
                    or reference(backend, 167) != owner):
                raise ValueError('Unsupported Scale vertex backend count/owner')
            descriptor_id = reference(backend, 79)
            _, descriptor = typed(descriptor_id, '5662F619-2281-4AD9-93DC-1FCFDA1062E7')
            if (len(descriptor) != 276 or descriptor[:4] != bytes(4)
                    or struct.unpack_from('<I', descriptor, 15)[0] != 1 or reference(descriptor, 265) != owner):
                raise ValueError('Unsupported Scale vertex descriptor count/owner')
            namespace, cursor = read_string(descriptor, 19)
            entity_uuid, cursor = read_string(descriptor, cursor)
            for text in (namespace, entity_uuid):
                uuid.UUID(text)
            if (cursor != 171 or descriptor[cursor:cursor+12] != struct.pack('<QI', 2, 1)
                    or struct.unpack_from('<I', descriptor, 194)[0] != 1):
                raise ValueError('Unsupported Scale vertex context/anchor list')
            context_id = reference(descriptor, 183)
            _, context = typed(context_id, '994C518A-A831-400A-B7C7-16DAC55F4F1C')
            if len(context) != 28 or context[:2] != bytes(2) or context[-2:] != b'\1\0':
                raise ValueError('Unobserved Scale vertex context layout')
            context_position = numbers(context, 2, 3)
            if not same(context_position, numbers(backend, 23, 3)):
                raise ValueError('Scale vertex backend and typed context coordinate caches disagree')
            anchor_id = reference(descriptor, 198)
            if anchor_id not in anchors:
                raise ValueError('Scale vertex historical body anchor unresolved')
            anchor = anchors[anchor_id]
            recipe_record, _ = typed(reference(descriptor, 4), RECIPE_GUID)
            recipe = decode_recipe(data, recipe_record, primary)
            if recipe['payload_kind'] != 'vertex_recipe_data':
                raise ValueError('Scale point requires explicit vertex recipe')
            point = {'entity': {'kind': 'BRepVertexRecipe', 'native_body_object_id': anchor['native_body_object_id'],
                                'recipe': recipe}, 'selection_object_id': backend_id,
                     'descriptor_object_id': descriptor_id, 'context_object_id': context_id,
                     'context_raw_hex': context.hex(), 'context_cached_position_cm': context_position,
                     'context_status': 'Observed typed coordinate cache agrees with backend; persistent vertex identity unresolved',
                     'body_anchor_object_id': anchor_id, 'source_owner_object_id': anchor['source_owner_object_id'],
                     'cached_position_cm': numbers(backend, 23, 3),
                     'association': 'Owned backend/descriptor selects vertex recipe and historical body; persistent ASM vertex identity unresolved',
                     'coordinate_scope': 'Saved backend cache in parent component; source-vertex evaluation and occurrence transforms unsupported'}
            decoded.append({'feature_object_id': owner, 'point': point,
                            'point_selection_status': 'Observed explicit vertex recipe; coordinate cache and persistent topology kept distinct'})
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
            unresolved.append({'feature_object_id': feature['object_id'], 'reason': str(error)})
    return {'decoded': decoded, 'unresolved': unresolved,
            'scope': 'Observed Scale vertex-source recipe and cached coordinates; exact topology and evaluation unsupported'}
