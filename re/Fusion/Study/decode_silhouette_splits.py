"""Observed SilhouetteSplit controls and explicit historical input provenance."""

import struct

from decode_body_selections import decode_body_selections
from decode_parameters import read_string
from decode_selection import known_construction_entities, resolve_native_selection
from decode_sketch import attributes, reference

FEATURE = 'D1C361B7-FA73-4D59-9406-066780667135'
DIRECTION = 'F2A7590D-6654-4674-B393-A2AEF4FEC48A'
OPERATIONS = {0: 'FacesOnly', 1: 'ShelledBody', 2: 'SolidBody'}


def decode_silhouette_splits(data, records, features, body_selections=None, *, direction_resolver=None):
    groups = {}
    for record in records:
        if record.is_primary:
            groups.setdefault(record.object_id, []).append(record)
    primary = {identity: values[0] for identity, values in groups.items() if len(values) == 1}
    bodies = body_selections if body_selections is not None else decode_body_selections(data, records)
    proxies = {p['selection_record_object_id']: p for p in bodies['selection_proxies']}
    descriptors = {d['object_id']: d for d in bodies['body_descriptors']}
    anchors = {a['object_id']: a for a in bodies['body_anchors']}
    known = known_construction_entities(data, records, features)

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Silhouette split typed reference missing, ambiguous or wrong class')
        return data[record.body:record.end]

    decoded, unresolved = [], []
    for feature in features:
        if feature['class_guid'] != FEATURE:
            continue
        owner = feature['object_id']
        try:
            body = typed(owner, FEATURE)
            if body[0] != 0 or body[1] not in (0, 1) or feature['parameters']:
                raise ValueError('Unobserved SilhouetteSplit prefix/parameters')
            props, cursor = attributes(body, 2) if body[1] else ({}, 2)
            if props or body[cursor:cursor+8] != bytes(8):
                raise ValueError('Unobserved SilhouetteSplit attributes/control prefix')
            direction_id = reference(body, cursor+8)
            operation = struct.unpack_from('<I', body, cursor+19)[0]
            if operation not in OPERATIONS or body[cursor+23:cursor+27] != bytes(4):
                raise ValueError('Unobserved SilhouetteSplit operation/control fields')
            count = struct.unpack_from('<I', body, cursor+27)[0]
            if count != (1 if operation in (1, 2) else 0):
                raise ValueError('Unobserved SilhouetteSplit additional body-anchor count')
            output_ids = [reference(body, cursor+31+11*i) for i in range(count)]
            cursor += 31+11*count
            if body[cursor:cursor+8] != bytes(4)+struct.pack('<I', 1):
                raise ValueError('Only captured single-target SilhouetteSplit supported')
            target_proxy_id = reference(body, cursor+8)
            namespace, end = read_string(body, cursor+19)
            if (namespace != '00000000-0000-0000-0000-000000000000'
                    or body[end:end+7] != bytes(3)+struct.pack('<I', 4)):
                raise ValueError('SilhouetteSplit metadata/reference table framing changed')
            refs = [reference(body, end+7+11*i) for i in range(4)]
            if refs[0] != direction_id or refs[2] != target_proxy_id:
                raise ValueError('SilhouetteSplit repeated input references disagree')
            direction = typed(direction_id, DIRECTION)
            if (len(direction) != 202 or direction[:6] != bytes.fromhex('000008000000')
                    or struct.unpack_from('<I', direction, 99)[0] != 1
                    or reference(direction, 191) != owner or reference(direction, 103) != refs[1]):
                raise ValueError('SilhouetteSplit direction count/owner correspondence changed')
            method = struct.unpack_from('<I', direction, 70)[0]
            if direction_resolver is None:
                descriptor = typed(refs[1], '5A1BF548-241F-46FD-9FB5-E4B05126EB9D')
                if (len(descriptor) != 263 or descriptor[:2] != bytes(2)
                        or struct.unpack_from('<I', descriptor, 13)[0] != 1 or reference(descriptor, 252) != owner):
                    raise ValueError('SilhouetteSplit direction descriptor count/owner changed')
                source = resolve_native_selection(data, records, direction_id, known)
                if (source is None or (method, source['entity']['kind']) not in
                        ((7, 'ConstructionAxis'), (14, 'ConstructionPlane'))):
                    raise ValueError('Only observed explicit construction direction sources supported')
                typed(source['terminal_object_id'], '90055C05-546C-4EE7-B3C9-3DD922AD0C9C')
            else:
                source = direction_resolver(data, records, features, direction_id, refs[1], owner, bodies, known)
            proxy = typed(target_proxy_id, '2CA5A1CD-C99B-4C9B-91AF-57989148E841')
            target = proxies.get(target_proxy_id)
            if (target is None or target['owner_object_id'] != owner
                    or target['descriptor_object_ids'] != [refs[3]] or reference(proxy, len(proxy)-11) != owner):
                raise ValueError('SilhouetteSplit owned target proxy/descriptors disagree')
            selected = descriptors[refs[3]]
            if selected['owner_object_id'] != owner or selected['context_record_object_ids']:
                raise ValueError('Only captured root-context SilhouetteSplit target supported')
            outputs = []
            for identity in output_ids:
                typed(identity, 'D26351F0-5940-4D23-AA20-2C35475A6D9E')
                anchor = anchors.get(identity)
                if anchor is None or anchor['source_owner_object_id'] != owner:
                    raise ValueError('SilhouetteSplit additional body anchor owner unresolved')
                outputs.append(anchor)
            decoded.append({'feature_object_id': owner, 'kind': 'SilhouetteSplit',
                            'operation': OPERATIONS[operation], 'operation_code': operation,
                            'view_direction': source, 'stored_direction_method_code': method,
                            'direction_control_object_id': direction_id,
                            'target': {'selection_record_object_id': target_proxy_id,
                                       'descriptor_object_id': refs[3],
                                       'native_body_object_id': selected['native_body_object_id'],
                                       'body_anchor_object_id': selected['body_anchor_object_id'],
                                       'source_owner_object_id': selected['source_owner_object_id']},
                            'stored_additional_body_anchors': outputs,
                            'additional_anchor_scope': 'Explicit owned additional body records; not the total result-body collection',
                            'geometry_status': 'Observed operation and historical input provenance; silhouette curves, result topology and regeneration unsupported'})
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
            unresolved.append({'feature_object_id': owner, 'kind': 'SilhouetteSplit', 'reason': str(error)})
    return {'decoded': decoded, 'unresolved': unresolved,
            'scope': 'Observed root-context SilhouetteSplit FacesOnly/ShelledBody/SolidBody and construction axis/plane directions; other source/layout variants and regeneration unsupported'}
