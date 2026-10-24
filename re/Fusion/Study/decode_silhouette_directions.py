"""Observed BRep edge/face and edge-defined axis SilhouetteSplit directions.

BRep geometry stays unresolved behind typed recipes and historical body anchors.
F2A preview/control vectors are preserved separately from actual source geometry.
"""
import math
import struct
import uuid

from decode_body_selections import decode_body_selections
from decode_brep_recipes import RECIPE_GUID, decode_recipe
from decode_parameters import read_string
from decode_selection import resolve_native_selection
from decode_silhouette_splits import DIRECTION, decode_silhouette_splits
from decode_sketch import attributes, numbers, reference, same

TOPOLOGY = '5662F619-2281-4AD9-93DC-1FCFDA1062E7'
AXIS_GEOMETRY = '19031004-3AB6-4D13-ABBF-C51EE214688D'
AXIS_FEATURE = '803DEC43-AEA6-42CC-B8D0-F593B5124BDD'
SCOPE = 'Captured FacesOnly BRepEdge/BRepFace or edge-defined custom-axis direction provenance; exact BRep source geometry, silhouette curves and topology/regeneration unresolved'


def resolve_silhouette_direction(data, records, features, direction_id, descriptor_id, owner_id, bodies, known):
    """Opt-in eight-argument shared-reader callback; no feature mutation."""
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {i: items[0] for i, items in grouped.items() if len(items) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Silhouette direction typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]

    def control(identity, expected_owner, expected_descriptor):
        _, payload = typed(identity, DIRECTION)
        if (len(payload) != 202 or payload[:6] != bytes.fromhex('000008000000')
                or struct.unpack_from('<I', payload, 99)[0] != 1
                or reference(payload, 103) != expected_descriptor
                or reference(payload, 191) != expected_owner):
            raise ValueError('Silhouette direction control descriptor/count/owner disagrees')
        support_id = reference(payload, 179)
        _, support = typed(support_id, '6CCF41D5-40BE-48ED-A834-18F3EAED6C57')
        if (len(support) != 58 or support[:12] != bytes.fromhex('000000000000010101000000')
                or reference(support, 12) != expected_descriptor or reference(support, 31) != identity):
            raise ValueError('Silhouette direction support references are not reciprocal')
        return payload, {'origin_cm': numbers(payload, 6, 3), 'vector': numbers(payload, 30, 3),
                         'remaining_control_bytes_hex': payload[54:99].hex(),
                         'status': 'Stored control/preview cache; not treated as source edge evaluator or face/axis geometry'}

    def topology(identity, owner, kind):
        _, payload = typed(identity, TOPOLOGY)
        if (len(payload) != 276 or payload[:4] != bytes(4)
                or struct.unpack_from('<I', payload, 15)[0] != 1
                or reference(payload, 265) != owner):
            raise ValueError('Unobserved Silhouette BRep source descriptor framing/owner')
        recipe_id = reference(payload, 4)
        record, _ = typed(recipe_id, RECIPE_GUID)
        recipe = decode_recipe(data, record, primary)
        if recipe['payload_kind'] != ('edge_recipe_data' if kind == 'BRepEdge' else 'face_recipe_data'):
            raise ValueError('Silhouette direction source recipe kind disagrees')
        namespace, cursor = read_string(payload, 19)
        entity, cursor = read_string(payload, cursor)
        uuid.UUID(namespace); uuid.UUID(entity)
        if (len(namespace) != 36 or len(entity) != 36 or cursor != 171
                or payload[cursor:cursor+12] != struct.pack('<QI', 2, 1)
                or struct.unpack_from('<I', payload, 194)[0] != 1):
            raise ValueError('Unobserved Silhouette BRep context/anchor framing')
        context_id, anchor_id = reference(payload, 183), reference(payload, 198)
        anchor_matches = [a for a in bodies['body_anchors'] if a['object_id'] == anchor_id]
        if len(anchor_matches) != 1:
            raise ValueError('Silhouette BRep historical source body anchor unresolved')
        anchor = anchor_matches[0]
        context_guid = '50AEE8B4-9456-4DD7-847D-6F6C909BBB9D' if kind == 'BRepEdge' else 'C46D3EEB-40E1-43FA-83DC-9CB204335417'
        _, context = typed(context_id, context_guid)
        if kind == 'BRepEdge':
            if len(context) != 55 or context[:2] != bytes(2) or context[-5:] != bytes.fromhex('0000000100'):
                raise ValueError('Unobserved Silhouette edge context cache framing')
        else:
            if len(context) != 171 or context[:2] != bytes(2) or context[6:10] != bytes(4):
                raise ValueError('Unobserved Silhouette face context framing')
            context_namespace, pos = read_string(context, 10)
            context_entity, pos = read_string(context, pos)
            if context_namespace != namespace or context_entity != entity or context[pos:] != struct.pack('<QB', 2, 0):
                raise ValueError('Silhouette face descriptor/context identity disagrees')
        support_id = reference(payload, 253)
        _, support = typed(support_id, '6CCF41D5-40BE-48ED-A834-18F3EAED6C57')
        if (len(support) != 58 or support[:12] != bytes.fromhex('000000000000010101000000')
                or reference(support, 12) != anchor['source_owner_object_id']
                or reference(support, 31) != identity):
            raise ValueError('Silhouette topology descriptor/source support is not reciprocal')
        return {'kind': kind, 'descriptor_object_id': identity, 'recipe': recipe,
                'body_anchor_object_id': anchor_id, 'native_body_object_id': anchor['native_body_object_id'],
                'source_owner_object_id': anchor['source_owner_object_id'],
                'body_name': anchor.get('body_properties', {}).get('name'),
                'namespace_text': namespace, 'entity_guid_text': entity,
                'context_evidence': {'object_id': context_id, 'class_guid': context_guid,
                                     'raw_hex': context.hex(), 'status': 'Stored context retained without geometry interpretation'},
                'source_geometry': None,
                'identity_status': 'Explicit typed topology recipe and historical body; exact source face/edge geometry and ASM identity unresolved'}

    payload, cache = control(direction_id, owner_id, descriptor_id)
    method = struct.unpack_from('<I', payload, 70)[0]
    if method in (8, 5):
        entity = topology(descriptor_id, owner_id, 'BRepEdge' if method == 8 else 'BRepFace')
        return {'entity': entity, 'selection_object_id': direction_id, 'descriptor_object_id': descriptor_id,
                'recipe_record_object_id': entity['recipe']['object_id'], 'stored_direction_method_code': method,
                'stored_control_cache': cache,
                'association': 'Owned direction control -> owned typed topology descriptor -> recipe and explicit historical body'}
    if method != 7:
        raise ValueError('Unobserved extended Silhouette source direction method')
    _, descriptor = typed(descriptor_id, '5A1BF548-241F-46FD-9FB5-E4B05126EB9D')
    if (len(descriptor) != 263 or descriptor[:2] != bytes(2)
            or struct.unpack_from('<I', descriptor, 13)[0] != 1 or reference(descriptor, 252) != owner_id):
        raise ValueError('Silhouette custom-axis source descriptor owner/count changed')
    leaf_id = reference(descriptor, 2)
    _, leaf = typed(leaf_id, '90055C05-546C-4EE7-B3C9-3DD922AD0C9C')
    if len(leaf) != 10 or leaf[:2] != bytes(2):
        raise ValueError('Unobserved Silhouette custom-axis identity leaf')
    axis_id = struct.unpack_from('<Q', leaf, 2)[0]
    _, axis = typed(axis_id, AXIS_GEOMETRY)
    props, cursor = attributes(axis, 2)
    if axis[:2] != b'\0\1' or props != {'EntityGenesis': 0} or cursor != 58:
        raise ValueError('Unobserved custom-axis native geometry attributes')
    origin, vector = numbers(axis, cursor, 3), numbers(axis, cursor+24, 3)
    length = math.sqrt(sum(v*v for v in vector))
    if not math.isfinite(length) or length <= 1e-12:
        raise ValueError('Invalid custom-axis stored line vector')
    _, end = read_string(axis, cursor+64)
    collection_id = reference(axis, end)
    index = struct.unpack_from('<Q', axis, end+11)[0]
    feature_id = reference(axis, end+20)
    if axis[end+19] != 0 or axis[end+31:end+33] != b'\0\1' or reference(axis, len(axis)-11) != collection_id:
        raise ValueError('Custom-axis geometry collection/owner fields disagree')
    name, name_end = read_string(axis, end+33)
    _, feature = typed(feature_id, AXIS_FEATURE)
    if (len(feature) != 236 or feature[:6] != bytes.fromhex('000004000000')
            or reference(feature, 6) != axis_id or feature[28] != 1
            or feature[105:112] != bytes.fromhex('00000002000000')
            or reference(feature, 112) != reference(feature, 17)):
        raise ValueError('Unobserved custom-axis feature/geometry correspondence')
    namespace, pos = read_string(feature, 29)
    label, label_end = read_string(feature, 138)
    if (namespace != str(uuid.UUID(int=0)) or pos != 105 or label != 'WorkAxis'
            or struct.unpack_from('<Q', feature, label_end)[0] != index):
        raise ValueError('Custom-axis feature metadata/index disagrees')
    inner_direction_id, inner_descriptor_id = reference(feature, 17), reference(feature, 123)
    inner, inner_cache = control(inner_direction_id, feature_id, inner_descriptor_id)
    if struct.unpack_from('<I', inner, 70)[0] != 8:
        raise ValueError('Only captured edge-defined custom-axis supported')
    edge = topology(inner_descriptor_id, feature_id, 'BRepEdge')
    if axis_id in known:
        existing = known[axis_id]
        if (existing['kind'] != 'ConstructionAxis' or existing.get('feature_object_id') != feature_id
                or not same(existing['origin_cm'], origin) or not same(existing['direction'], [v/length for v in vector])):
            raise ValueError('Known construction-axis geometry disagrees with reciprocal native source')
    axis_entity = {'kind': 'ConstructionAxis', 'object_id': axis_id, 'feature_object_id': feature_id,
                   'name': name, 'origin_cm': origin, 'stored_line_vector': vector,
                   'direction': [v/length for v in vector],
                   'direction_status': 'Normalized finite native axis line vector; agrees with actual axis getter in captured edge-defined holdout',
                   'definition_kind': 'ConstructionAxisEdgeDefinition', 'definition_edge': edge,
                   'native_geometry_suffix_hex': axis[name_end:].hex(),
                   'definition_control_cache': inner_cache}
    source = resolve_native_selection(data, records, direction_id, {axis_id: axis_entity})
    if source is None or source['descriptor_object_id'] != descriptor_id or source['terminal_object_id'] != leaf_id:
        raise ValueError('Custom-axis typed identity chain does not resolve uniquely')
    source.update(stored_direction_method_code=method, stored_control_cache=cache,
                  association='Explicit native-axis identity leaf; reciprocal named axis geometry/feature and owned edge-definition source')
    return source


def decode_silhouette_directions(data, records, features, body_selections=None):
    """Extended source summary only; root merges successes with original reader."""
    bodies = body_selections if body_selections is not None else decode_body_selections(data, records)
    result = decode_silhouette_splits(data, records, features, bodies,
                                    direction_resolver=resolve_silhouette_direction)
    decoded, unresolved = [], list(result['unresolved'])
    for item in result['decoded']:
        source = item['view_direction']['entity']
        source_body = source['definition_edge']['native_body_object_id'] if source['kind'] == 'ConstructionAxis' else source['native_body_object_id']
        if (item['operation_code'] != 0 or item['stored_additional_body_anchors']
                or source_body == item['target']['native_body_object_id']):
            unresolved.append({'feature_object_id': item['feature_object_id'], 'kind': 'SilhouetteSplit',
                               'reason': 'Only captured FacesOnly with independent support-source body supported'})
            continue
        decoded.append(item)
    return {'decoded': decoded, 'unresolved': unresolved, 'scope': SCOPE}
