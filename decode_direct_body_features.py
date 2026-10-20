"""Observed BaseFeature body pairs and BoundaryFill-owned RemoveBody actions.

Native PM/DM attribute labels are retained literally. Feature ownership does not
establish current body visibility, regeneration, or arbitrary direct edits.
"""
import struct
import uuid

from decode_body_properties import BODY
from decode_body_selections import PROXY, DESCRIPTOR, decode_body_selections
from decode_boundary_fill import BOUNDARY_FILL_GUID, decode_boundary_fill
from decode_parameters import read_string
from decode_selection import native_proxy_references
from decode_sketch import ascii_string, reference

BASE_FEATURE = 'D7015B81-AB4D-4C89-BED7-AA4411E1964A'
REMOVE_BODY = '4A782808-FBDD-4351-A10A-F7AE5693D330'
BASE_CONTROLLER = '493A89BA-E146-498D-9033-2783FE727AF4'
SCOPE = 'Bounded native BaseFeature paired body attributes/result anchors, or BoundaryFill-owned RemoveBody body selections; no arbitrary direct-edit geometry or current final body lifecycle inference'


def decode_direct_body_features(data, records, body_selections=None):
    """Return decoded/unresolved/scope; successful items keyed by feature_object_id."""
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {i: items[0] for i, items in grouped.items() if len(items) == 1}
    selections = body_selections if body_selections is not None else decode_body_selections(data, records)

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Direct-body feature typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]

    def selected(identity, field, collection):
        items = [s for s in collection if s[field] == identity]
        if len(items) != 1:
            raise ValueError('Direct-body feature selection missing or ambiguous')
        return items[0]

    def passive(identity, expected_key, expected_reference):
        _, payload = typed(identity, BODY)
        if payload[:6] != b'\0\1\1\0\0\0':
            raise ValueError('Unobserved BaseFeature body attribute count/prefix')
        key, cursor = ascii_string(payload, 6)
        kind, cursor = ascii_string(payload, cursor)
        if key != expected_key or kind != 'PassiveRefMetaType' or reference(payload, cursor) != expected_reference:
            raise ValueError('BaseFeature passive body references are not reciprocal')
        return {'attribute_name': key, 'attribute_type': kind, 'referenced_body_object_id': expected_reference,
                'body_collection_object_id': reference(payload, len(payload)-11)}

    decoded, unresolved = [], []
    for record in records:
        if not record.is_primary or record.class_guid not in (BASE_FEATURE, REMOVE_BODY):
            continue
        try:
            if primary.get(record.object_id) is not record:
                raise ValueError('Direct-body feature identity ambiguous')
            payload = data[record.body:record.end]
            if record.class_guid == BASE_FEATURE:
                if (len(payload) < 250 or payload[:5] != b'\1\2\0\0\0'
                        or payload[16:20] != bytes(4) or payload[31:35] != bytes(4)
                        or payload[35:50] != bytes.fromhex('010000000000000000010001000000')
                        or payload[61] != 0 or payload[73:81] != struct.pack('<II', 0, 1)
                        or payload[92:100] != bytes(8)):
                    raise ValueError('Unobserved BaseFeature single-pair/list framing')
                first_id, second_id = reference(payload, 5), reference(payload, 20)
                if first_id == second_id or reference(payload, 50) != first_id:
                    raise ValueError('BaseFeature repeated first body/list disagrees')
                first = passive(first_id, 'BASEFEAT_PM_BODY_REF', second_id)
                second = passive(second_id, 'BASEFEAT_DM_BODY_REF', first_id)
                controller_id = reference(payload, 62)
                _, controller = typed(controller_id, BASE_CONTROLLER)
                if (len(controller) != 71 or reference(controller, 14) != record.object_id
                        or reference(controller, 60) != record.object_id):
                    raise ValueError('BaseFeature result controller owners disagree')
                anchor_id = reference(payload, 81)
                anchor = selected(anchor_id, 'object_id', selections['body_anchors'])
                if anchor['native_body_object_id'] != second_id or anchor['source_owner_object_id'] != record.object_id:
                    raise ValueError('BaseFeature explicit result anchor/body/owner disagree')
                namespace, cursor = read_string(payload, 100)
                if (namespace != str(uuid.UUID(int=0)) or cursor != 176
                        or payload[cursor:cursor+7] != bytes.fromhex('00000001000000')
                        or reference(payload, cursor+7) != controller_id):
                    raise ValueError('BaseFeature repeated controller table disagrees')
                label, cursor = read_string(payload, cursor+22)
                if label != 'Base Feature':
                    raise ValueError('BaseFeature stored metadata label disagrees')
                stored_index = struct.unpack_from('<Q', payload, cursor)[0]
                name, cursor = read_string(payload, cursor+8)
                decoded.append({'feature_object_id': record.object_id, 'kind': 'BaseFeature', 'name': name,
                                'stored_index': stored_index, 'body_pair': [
                                    {'native_body_object_id': first_id, 'passive_reference': first},
                                    {'native_body_object_id': second_id, 'passive_reference': second}],
                                'repeated_first_body_object_id': first_id,
                                'result_body_anchor_object_id': anchor_id,
                                'anchored_result_native_body_object_id': second_id,
                                'result_controller_object_id': controller_id,
                                'body_pair_status': 'Literal PM/DM passive-reference labels and reciprocal typed bodies; second body independently matches owned result anchor. General PM/DM lifecycle semantics unresolved.',
                                'remaining_metadata_hex': payload[cursor:].hex(), 'scope': SCOPE})
            else:
                if len(payload) != 266 or payload[:2] != bytes(2) :
                    raise ValueError('Unobserved RemoveBody framing')
                proxy_id = reference(payload, 2)
                namespace, cursor = read_string(payload, 13)
                uuid.UUID(namespace)
                if (len(namespace) != 36 or cursor != 89 or payload[89:96] != bytes.fromhex('00000002000000')
                        or reference(payload, 96) != proxy_id or payload[118:122] != b'\xff'*4):
                    raise ValueError('RemoveBody repeated body input table disagrees')
                descriptor_id = reference(payload, 107)
                proxy_record, proxy = typed(proxy_id, PROXY)
                ids, props = native_proxy_references(data, proxy_record)
                _, descriptor = typed(descriptor_id, DESCRIPTOR)
                if (ids != [descriptor_id] or props or reference(proxy, len(proxy)-11) != record.object_id
                        or reference(descriptor, len(descriptor)-11) != record.object_id):
                    raise ValueError('RemoveBody proxy/descriptor owner or membership disagrees')
                body_descriptor = selected(descriptor_id, 'object_id', selections['body_descriptors'])
                if body_descriptor['owner_object_id'] != record.object_id:
                    raise ValueError('RemoveBody selected descriptor owner disagrees')
                label, cursor = read_string(payload, 122)
                if label != 'RemoveBody':
                    raise ValueError('RemoveBody native metadata label disagrees')
                index = struct.unpack_from('<Q', payload, cursor)[0]
                name, cursor = read_string(payload, cursor+8)
                parent_id = reference(payload, 254)
                if payload[-1] != 0:
                    raise ValueError('Unobserved RemoveBody parent-link suffix')
                _, parent = typed(parent_id, BOUNDARY_FILL_GUID)
                parent_settings = decode_boundary_fill(data, records, parent,
                                  {'object_id': parent_id, 'class_guid': BOUNDARY_FILL_GUID})
                if (not parent_settings['is_remove_tools'] or record.object_id not in parent_settings['remove_body_feature_object_ids']):
                    raise ValueError('BoundaryFill removal list/action owner disagree')
                parent_tool_ids = []
                for tool in parent_settings['tools']:
                    if tool['kind'] != 'Body':
                        continue
                    candidate = selected(tool['descriptor_object_id'], 'object_id', selections['body_descriptors'])
                    if (candidate['native_body_object_id'] == body_descriptor['native_body_object_id']
                            and candidate['body_anchor_object_id'] == body_descriptor['body_anchor_object_id']):
                        parent_tool_ids.append(tool['selection_record_object_id'])
                if len(parent_tool_ids) != 1:
                    raise ValueError('RemoveBody input not a unique matching historical BoundaryFill tool')
                decoded.append({'feature_object_id': record.object_id, 'kind': 'RemoveBody', 'name': name,
                                'stored_index': index, 'selection_record_object_id': proxy_id,
                                'descriptor_object_id': descriptor_id,
                                'native_body_object_id': body_descriptor['native_body_object_id'],
                                'body_anchor_object_id': body_descriptor['body_anchor_object_id'],
                                'source_owner_object_id': body_descriptor['source_owner_object_id'],
                                'parent_boundary_fill_object_id': parent_id,
                                'matching_parent_tool_selection_record_object_id': parent_tool_ids[0],
                                'action_scope': 'Owned removal action for explicit historical BoundaryFill input tool; current final visibility/body lifetime not inferred',
                                'remaining_metadata_before_parent_hex': payload[cursor:254].hex(), 'scope': SCOPE})
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
            unresolved.append({'feature_object_id': record.object_id, 'class_guid': record.class_guid,
                               'record_offset': record.start, 'reason': str(error)})
    return {'decoded': decoded, 'unresolved': unresolved, 'scope': SCOPE}
