"""Observed Combine controls and explicit target/tool selection roles."""
import struct

from decode_sketch import attributes, reference

COMBINE = '2A94257F-2020-4B19-9A68-103A2672F1B7'
PROXY = '2CA5A1CD-C99B-4C9B-91AF-57989148E841'
DESCRIPTOR = '9716F783-676D-42E0-93F9-EBF273E7C035'
ANCHOR = 'D26351F0-5940-4D23-AA20-2C35475A6D9E'
FRAME = '2E3AC990-483D-4A55-8662-C064B976A957'


def decode_combine(data, records, body, feature):
    if (feature['class_guid'] != COMBINE or len(body) < 12
            or body[0] != 0 or body[1] not in (0, 1)):
        raise ValueError('Unsupported Combine class/prefix')
    props, cursor = attributes(body, 2) if body[1] else ({}, 2)
    operation = struct.unpack_from('<I', body, cursor)[0]
    if (props or operation not in (0, 1, 2) or body[cursor+4:cursor+8] != b'\0'*4
            or body[cursor+8] not in (0, 1) or body[cursor+9] not in (0, 1)):
        raise ValueError('Unsupported Combine controls')
    keep, component = bool(body[cursor+8]), bool(body[cursor+9])
    primary = {}
    for record in records:
        if record.is_primary:
            primary.setdefault(record.object_id, []).append(record)

    def typed(identity, guid):
        matches = primary.get(identity, [])
        if len(matches) != 1 or matches[0].class_guid != guid:
            raise ValueError('Combine reference missing, ambiguous or wrong class: '+guid)
        record = matches[0]
        return data[record.body:record.end]

    def counted(offset, guid):
        count = struct.unpack_from('<I', body, offset)[0]
        if count > 1024 or offset+4+11*count > len(body):
            raise ValueError('Unsupported Combine reference count')
        identities = [reference(body, offset+4+11*i) for i in range(count)]
        if len(set(identities)) != count:
            raise ValueError('Duplicate Combine references')
        for identity in identities:
            typed(identity, guid)
        return identities, offset+4+11*count

    frames, after_frames = counted(cursor+10, FRAME)
    if len(frames) != 1:
        raise ValueError('Only one observed Combine frame supported')
    frame = typed(frames[0], FRAME)
    if (len(frame) != 58 or frame[:20] != b'\0'*20 or struct.unpack_from('<I', frame, 20)[0] != 3
            or reference(frame, 40) != feature['object_id'] or frame[51:] != b'\0'*7):
        raise ValueError('Unsupported Combine frame/owner')
    stored_handle = struct.unpack_from('<Q', body, after_frames)[0]
    tools, cursor = counted(after_frames+8, PROXY)
    if not tools:
        raise ValueError('Combine tool list is empty')
    auxiliary = []
    for _ in range(3):
        identities, cursor = counted(cursor, ANCHOR)
        auxiliary.append(identities)
    targets, cursor = counted(cursor, PROXY)
    if len(targets) != 1 or targets[0] in tools:
        raise ValueError('Unsupported Combine target list')
    selected = []
    for identity in tools+targets:
        proxy = typed(identity, PROXY)
        if len(proxy) < 6 or proxy[0] != 0 or proxy[1] not in (0, 1):
            raise ValueError('Unsupported Combine body proxy prefix')
        start = attributes(proxy, 2)[1] if proxy[1] else 2
        if struct.unpack_from('<I', proxy, start)[0] != 1:
            raise ValueError('Only single-body Combine proxies observed')
        descriptor_id = reference(proxy, start+4)
        descriptor = typed(descriptor_id, DESCRIPTOR)
        if (reference(proxy, len(proxy)-11) != feature['object_id']
                or reference(descriptor, len(descriptor)-11) != feature['object_id']):
            raise ValueError('Combine proxy/descriptor owners disagree')
        selected.append({'selection_record_object_id': identity, 'descriptor_object_id': descriptor_id,
                         'role': 'TargetBody' if identity == targets[0] else 'ToolBody'})
    return {'operation': {0: 'Join', 1: 'Cut', 2: 'Intersect'}[operation],
            'stored_operation_code': operation, 'keep_tool_bodies': keep, 'is_new_component': component,
            'target_body_selection_object_id': targets[0], 'tool_body_selection_object_ids': tools,
            'input_selections': selected, 'frame_record_object_id': frames[0],
            'uninterpreted_stored_handle': stored_handle,
            'handle_scope': 'Opaque stored value; not treated as a native object ID or ASM entity index',
            'auxiliary_body_anchor_lists': auxiliary,
            'auxiliary_scope': 'Typed anchor lists retained without assigning deleted/result/current-body lifecycle semantics',
            'input_definition_end_offset': cursor,
            'geometry_status': 'Observed controls and selection roles; Boolean reconstruction and general topology remain unresolved'}


def attach_combine_bodies(features, body_selections):
    """Join explicit role references to independently decoded body identities."""
    proxies = {item['selection_record_object_id']: item for item in body_selections['selection_proxies']}
    descriptors = {item['object_id']: item for item in body_selections['body_descriptors']}
    for feature in features:
        if feature['kind'] != 'Combine' or 'input_selections' not in feature.get('tool_settings', {}):
            continue
        for selected in feature['tool_settings']['input_selections']:
            proxy = proxies.get(selected['selection_record_object_id'])
            descriptor = descriptors.get(selected['descriptor_object_id'])
            if (proxy is None or descriptor is None or proxy['owner_object_id'] != feature['object_id']
                    or selected['descriptor_object_id'] not in proxy['descriptor_object_ids']
                    or proxy['native_body_object_ids'] != [descriptor['native_body_object_id']]):
                selected['body_identity_status'] = 'Independent body selection/descriptor association unresolved'
                continue
            selected.update(native_body_object_id=descriptor['native_body_object_id'],
                            body_properties=descriptor['body_properties'],
                            body_identity_status='Explicit owned proxy/descriptor and typed native body anchor agree')
