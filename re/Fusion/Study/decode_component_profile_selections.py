"""Observed component-context sketch profiles; context slot transforms unresolved.

Only the captured single-descriptor, single-profile-set variant is admitted.
Explicit descriptor sketch IDs and reciprocal owners establish membership; route
terminal UUIDs are retained as context evidence, never interpreted as sketch IDs.
"""

import struct
import uuid

from decode_component_body_proxies import FRAME, FRAME_LINK, ROUTE_LIST, ROUTE, SECONDARY
from decode_body_selections import CONTEXT, HELPER, PROXY, SUPPORT
from decode_parameters import read_string
from decode_profiles import PROFILE_DESCRIPTOR_GUID, PROFILE_LOOP_GUID, read_loops
from decode_sketch import numbers, reference


def resolve_component_sketch_profiles(data, records, selection_id, owner_id, features):
    def typed(identity, guid):
        matches = [r for r in records if r.is_primary and r.object_id == identity and r.class_guid == guid]
        if len(matches) != 1:
            raise ValueError('Component profile typed reference missing, ambiguous or wrong class')
        record = matches[0]
        return record, data[record.body:record.end]

    def text_uuid(payload, cursor):
        text, cursor = read_string(payload, cursor)
        if len(text) != 36:
            raise ValueError('Unsupported component profile UUID')
        uuid.UUID(text)
        return text, cursor

    def trailer(payload, cursor, source_id, support_owner):
        if (len(payload)-cursor != 71 or payload[cursor+18:cursor+22] != b'\1\1\0\0'
                or payload[cursor+30:cursor+34] != b'\1\1\0\0'
                or payload[cursor+45:cursor+48] != b'\1\0\0' or payload[cursor+59] != 0
                or reference(payload, cursor+60) != owner_id):
            raise ValueError('Unsupported component profile trailer/owner')
        helper_id, support_id = reference(payload, cursor+34), reference(payload, cursor+48)
        typed(helper_id, HELPER)
        _, support = typed(support_id, SUPPORT)
        if (len(support) != 58 or support[:12] != bytes.fromhex('000000000000010101000000')
                or reference(support, 12) != source_id or reference(support, 31) != support_owner):
            raise ValueError('Component profile support references are not reciprocal')
        return {'helper_record_object_id': helper_id, 'support_record_object_id': support_id,
                'uninterpreted_prefix_hex': payload[cursor:cursor+18].hex(),
                'uninterpreted_cached_scalar': numbers(payload, cursor+22, 1)[0]}

    _, proxy = typed(selection_id, PROXY)
    if len(proxy) != 125 or proxy[:6] != b'\0\0\1\0\0\0' or struct.unpack_from('<I', proxy, 39)[0] != 1:
        raise ValueError('Unsupported component profile proxy layout')
    descriptor_id = reference(proxy, 6)
    frame_ids = [reference(proxy, 17), reference(proxy, 28)]
    if frame_ids[0] == frame_ids[1]:
        raise ValueError('Duplicate component profile context slots')
    secondary_id = reference(proxy, 43)
    _, secondary = typed(secondary_id, SECONDARY)
    if secondary != bytes.fromhex('0000010100'):
        raise ValueError('Unsupported component profile secondary record')
    proxy_trailer = trailer(proxy, 54, descriptor_id, selection_id)
    _, descriptor = typed(descriptor_id, PROFILE_DESCRIPTOR_GUID)
    if descriptor[:2] != b'\0\0' or struct.unpack_from('<I', descriptor, 13)[0] != 1:
        raise ValueError('Unsupported component profile descriptor prefix')
    namespace, cursor = text_uuid(descriptor, 17)
    sketch_text, cursor = read_string(descriptor, cursor)
    if not sketch_text.isascii() or not sketch_text.isdecimal():
        raise ValueError('Component profile has no explicit decimal sketch identity')
    sketch_id = int(sketch_text)
    sketches = [f for f in features if f['kind'] == 'Sketch' and f['sketch_object_id'] == sketch_id]
    if len(sketches) != 1:
        raise ValueError('Component profile sketch unresolved or ambiguous')
    sketch = sketches[0]
    if descriptor[cursor:cursor+12] != struct.pack('<QI', 1, 1):
        raise ValueError('Unsupported component profile descriptor context list')
    context_id = reference(descriptor, cursor+12)
    descriptor_trailer = trailer(descriptor, cursor+23, sketch['object_id'], descriptor_id)
    _, context = typed(context_id, CONTEXT)
    if (len(context) != 171 or context[:2] != b'\0\0' or context[6:10] != b'\0'*4
            or struct.unpack_from('<I', context, 2)[0] not in (0, 1)):
        raise ValueError('Unsupported component profile descriptor context')
    context_namespace, position = text_uuid(context, 10)
    context_uuid, position = text_uuid(context, position)
    if context_namespace != namespace or context[position:] != struct.pack('<QB', 2, 0):
        raise ValueError('Component profile descriptor context namespace/suffix mismatch')
    frames = []
    for identity in frame_ids:
        _, frame = typed(identity, FRAME)
        if (len(frame) != 78 or frame[:20] != b'\0'*20 or frame[20:37] != struct.pack('<I', 3)+b'\0'*13
                or frame[48:50] != b'\1\0' or reference(frame, 50) != owner_id or frame[72:] != b'\0'*6):
            raise ValueError('Unsupported component profile frame/owner')
        frame_link_id, route_list_id = reference(frame, 37), reference(frame, 61)
        typed(frame_link_id, FRAME_LINK)
        _, listing = typed(route_list_id, ROUTE_LIST)
        if len(listing) != 18 or listing[:7] != bytes.fromhex('00000001000000'):
            raise ValueError('Unsupported component profile route wrapper')
        route_id = reference(listing, 7)
        _, route = typed(route_id, ROUTE)
        if route[:2] != b'\0\0':
            raise ValueError('Unsupported component profile route prefix')
        mode = struct.unpack_from('<I', route, 2)[0]
        occurrence_uuid, position = text_uuid(route, 6)
        if mode == 1:
            route_namespace, position = text_uuid(route, position)
            route_context, position = text_uuid(route, position)
            if (route_namespace != namespace or route_context != context_uuid
                    or route[position:position+8] != struct.pack('<Q', 2)):
                raise ValueError('Component profile route/descriptor context disagree')
            position += 8
        elif mode == 0:
            if occurrence_uuid != str(uuid.UUID(int=0)) or route[position:position+12] != struct.pack('<IQ', 0, 1):
                raise ValueError('Unsupported empty component profile route')
            position += 12
        else:
            raise ValueError('Unsupported component profile route mode')
        terminal_namespace, position = text_uuid(route, position)
        terminal_uuid, position = text_uuid(route, position)
        if terminal_namespace != namespace or route[position:] != struct.pack('<QI', 2, 0):
            raise ValueError('Component profile route namespace/suffix disagree')
        frames.append({'object_id': identity, 'frame_link_object_id': frame_link_id,
                       'route_wrapper_object_id': route_list_id, 'route_object_id': route_id,
                       'stored_route_mode': mode, 'stored_occurrence_uuid_text': occurrence_uuid,
                       'terminal_namespace_text': terminal_namespace, 'terminal_entity_uuid_text': terminal_uuid})
    if [f['stored_route_mode'] for f in frames] != [1, 0] or frames[0]['terminal_entity_uuid_text'] != frames[1]['terminal_entity_uuid_text']:
        raise ValueError('Unobserved component profile context slot combination or terminal mismatch')
    definition_id = reference(descriptor, 2)
    _, definition = typed(definition_id, PROFILE_LOOP_GUID)
    loops = read_loops(definition, descriptor_id, sketch)
    return [{'selection_record_object_id': selection_id, 'descriptor_object_id': descriptor_id,
             'loop_definition_object_id': definition_id, 'sketch_object_id': sketch_id,
             'sketch_name': sketch['name'], 'loops': loops,
             'component_context': {'context_record_object_id': context_id, 'namespace_text': namespace,
                                   'context_uuid_text': context_uuid, 'stored_context_index_field': struct.unpack_from('<I', context, 2)[0], 'slots': frames,
                                   'secondary_record_object_id': secondary_id,
                                   'proxy_trailer': proxy_trailer, 'descriptor_trailer': descriptor_trailer,
                                   'status': 'Explicit owned context slots and reciprocal source/profile supports; slot direction, terminal UUID identity and transforms unresolved'},
             'scope': 'Explicit sketch ID and typed curve-tag membership; context transforms and contour traversal unresolved'}]
