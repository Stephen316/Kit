"""Bounded absent-pair/zero-result-anchor BaseFeature definition provenance.

This is a partial native definition, not proof that a feature contains no other
objects. It does not classify features, assign meshes or alter existing errors.
"""
import struct
import uuid

from decode_parameters import read_string
from decode_sketch import reference
from decode_timeline import HISTORY_GUID, feature_state

BASE_FEATURE = 'D7015B81-AB4D-4C89-BED7-AA4411E1964A'
CONTROLLER = '493A89BA-E146-498D-9033-2783FE727AF4'
BOOKKEEPING = '6CCF41D5-40BE-48ED-A834-18F3EAED6C57'
OWNER_LINK = 'CB844AB6-240D-4fc9-9C9F-3679DC896D6F'
COLLECTION = '3A6D1E62-99F8-4E32-BAAA-DBA0A2CFB27C'
COLLECTION_MEMBERS = '834C9DEF-4C39-4587-A08D-A5BD1267B7B4'
HISTORY_CONTAINER = 'C3423E04-7E85-4B44-8E31-A5FA9C100052'
PREFIX = bytes.fromhex('0001000000000000000001000000000000')
SCOPE = ('Partial BaseFeature definition with captured absent body-pair branch, zero result-anchor list, '
         'reciprocal controller/bookkeeping and typed collection/history membership. Entire contained-object '
         'state, mesh ownership, direct edits and current/final lifecycle remain unqualified; feature kind and errors unchanged.')


def decode_base_feature_empty_list(data, records, feature):
    groups = {}
    for record in records:
        if record.is_primary:
            groups.setdefault(record.object_id, []).append(record)

    def typed(identity, guid):
        rows = groups.get(identity, [])
        if len(rows) != 1 or rows[0].class_guid != guid:
            raise ValueError('Empty-list BaseFeature typed identity missing, ambiguous or wrong class')
        record = rows[0]
        return record, data[record.body:record.end]

    def inherited(identity, guid):
        rows = [r for r in records if not r.is_primary and r.object_id == identity and r.class_guid == guid]
        if len(rows) != 1:
            raise ValueError('Empty-list BaseFeature inherited owner/membership identity missing or ambiguous')
        record = rows[0]
        return record, data[record.body:record.end]

    identity = feature['object_id']
    record, body = typed(identity, BASE_FEATURE)
    if feature.get('class_guid') != BASE_FEATURE or feature.get('record_offset') != record.start:
        raise ValueError('Empty-list BaseFeature feature metadata differs from primary native record')
    if (len(body) < 240 or body[:17] != PREFIX or body[28:44] != bytes(16)):
        raise ValueError('Unobserved BaseFeature absent-pair/zero-result-anchor prefix')
    controller_id = reference(body, 17)
    namespace, cursor = read_string(body, 44)
    if (namespace != str(uuid.UUID(int=0)) or cursor != 120
            or body[120:127] != bytes.fromhex('00000001000000')
            or reference(body, 127) != controller_id):
        raise ValueError('Empty-list BaseFeature nil UUID/repeated controller table disagrees')
    metadata = struct.unpack_from('<I', body, 138)[0]
    label, cursor = read_string(body, 142)
    index = struct.unpack_from('<Q', body, cursor)[0]
    name, cursor = read_string(body, cursor+8)
    if (metadata != 2 or label != 'Base Feature' or len(body)-cursor != 66
            or index != feature.get('stored_index') or name != feature.get('name')):
        raise ValueError('Empty-list BaseFeature metadata/label/index/name/footer extent disagrees')
    state = feature_state(body)
    controller_record, controller = typed(controller_id, CONTROLLER)
    if (len(controller) != 71 or controller[:14] != bytes(14)
            or reference(controller, 14) != identity
            or controller[25:48] != bytes(20)+bytes.fromhex('010000') or controller[59] != 0
            or reference(controller, 60) != identity):
        raise ValueError('Empty-list BaseFeature controller framing/reciprocal owners disagree')
    bookkeeping_id = reference(controller, 48)
    bookkeeping_record, bookkeeping = typed(bookkeeping_id, BOOKKEEPING)
    if (len(bookkeeping) != 39 or bookkeeping[:12] != bytes(12)
            or reference(bookkeeping, 12) != controller_id or bookkeeping[31:] != bytes(8)):
        raise ValueError('Empty-list BaseFeature controller/bookkeeping typed backlink disagrees')
    owner_record, owner = inherited(identity, OWNER_LINK)
    controller_owner_record, controller_owner = inherited(controller_id, OWNER_LINK)
    if len(owner) != 11 or controller_owner != owner:
        raise ValueError('Empty-list BaseFeature and controller collection owners disagree')
    collection_id = reference(owner, 0)
    collection_record, collection = typed(collection_id, COLLECTION)
    if collection != bytes(2):
        raise ValueError('Unobserved BaseFeature owner collection primary payload')
    membership_record, membership = inherited(collection_id, COLLECTION_MEMBERS)
    count = struct.unpack_from('<I', membership, 0)[0]
    if not 1 <= count <= 10000 or len(membership) != 15+11*count:
        raise ValueError('Empty-list BaseFeature collection counted membership extent unsupported')
    members = [reference(membership, 4+11*i) for i in range(count)]
    if len(set(members)) != count or members.count(identity) != 1 or members.count(controller_id) != 1:
        raise ValueError('Empty-list BaseFeature/controller collection membership missing or repeated')
    if any(len(groups.get(member, [])) != 1 for member in members):
        raise ValueError('Empty-list BaseFeature collection contains missing or ambiguous native member')
    container_id = reference(membership, 4+11*count)
    container_record, container = typed(container_id, HISTORY_CONTAINER)
    if len(container) < 66 or reference(container, len(container)-22) != collection_id:
        raise ValueError('Empty-list BaseFeature collection/history-container backlink disagrees')
    history_id = reference(container, len(container)-55)
    history_record, history = typed(history_id, HISTORY_GUID)
    if history[:2] != bytes(2) or reference(history, 2) != container_id:
        raise ValueError('Empty-list BaseFeature history/container typed ownership disagrees')
    history_count = struct.unpack_from('<I', history, 13)[0]
    if not 1 <= history_count <= 100000 or len(history) != 17+11*history_count:
        raise ValueError('Empty-list BaseFeature history counted extent unsupported')
    history_ids = [reference(history, 17+11*i) for i in range(history_count)]
    if len(set(history_ids)) != history_count or history_ids.count(identity) != 1:
        raise ValueError('Empty-list BaseFeature history membership missing or repeated')
    if any(len(groups.get(member, [])) != 1 for member in history_ids):
        raise ValueError('Empty-list BaseFeature history contains missing or ambiguous native member')
    # Exact payload replay: preserve every stored byte, including raw footer
    # and unassigned metadata; this is not a native authoring API.
    def ref(value):
        return b'\1'+struct.pack('<Q', value)+bytes(2)
    def text(value):
        return struct.pack('<I', len(value))+value.encode('utf-16le')
    replay = (PREFIX+ref(controller_id)+bytes(16)+text(namespace)+bytes.fromhex('00000001000000')
        +ref(controller_id)+struct.pack('<I', metadata)+text(label)+struct.pack('<Q', index)+text(name)+body[cursor:])
    if replay != body:
        raise ValueError('Empty-list BaseFeature exact full payload replay disagrees')
    return {'feature_object_id': identity, 'name': name, 'stored_index': index,
        'definition_status': 'PartialObservedAbsentPairAndZeroResultAnchorLayout',
        'stored_native_kind_label': label,
        'definition': {'stored_initial_branch_byte': body[0], 'initial_branch_prefix_hex': body[:17].hex(),
            'body_pair_table_scope': 'Observed absent pair branch, contrasted with explicitly typed PM/DM body-pair records; not a count of all contained objects',
            'stored_reserved_uint32_at_28': struct.unpack_from('<I', body, 28)[0],
            'stored_result_anchor_count': struct.unpack_from('<I', body, 32)[0],
            'stored_result_anchor_object_ids': [], 'stored_nil_uuid': namespace,
            'stored_repeated_controller_count': 1, 'stored_repeated_controller_object_ids': [controller_id],
            'stored_table_metadata': metadata, 'table_metadata_semantics': 'Literal2 only; no enum or flag meaning assigned',
            'stored_shared_feature_state': state, 'remaining_footer_hex': body[cursor:].hex(),
            'entire_contained_object_state': None, 'mesh_owner_object_ids': None,
            'scope': 'Only observed native pair/result-anchor fields are qualified; arbitrary contained-object state and mesh ownership are unqualified'},
        'controller': {'object_id': controller_id, 'class_guid': CONTROLLER,
            'record_offset': controller_record.start, 'feature_owner_reference_offsets': [controller_record.body+14, controller_record.body+60],
            'bookkeeping_object_id': bookkeeping_id, 'bookkeeping_record_offset': bookkeeping_record.start,
            'bookkeeping_backlink_offset': bookkeeping_record.body+12,
            'opaque_bookkeeping_8byte_hex': bookkeeping[23:31].hex(),
            'payload_hex': controller.hex(), 'bookkeeping_payload_hex': bookkeeping.hex(),
            'association': 'Feature direct/repeated controller references; controller twice references feature; typed bookkeeping reciprocally references controller'},
        'ownership': {'collection_object_id': collection_id, 'collection_class_guid': COLLECTION,
            'collection_record_offset': collection_record.start,
            'feature_owner_fragment_offset': owner_record.body, 'controller_owner_fragment_offset': controller_owner_record.body,
            'membership_fragment_offset': membership_record.body, 'counted_member_object_ids': members,
            'membership_payload_hex': membership.hex(),
            'native_history_container_object_id': container_id, 'native_history_container_class_guid': HISTORY_CONTAINER,
            'container_collection_backlink_offset': container_record.end-22,
            'association': 'Feature and controller inherited owners agree; unique counted membership includes both; collection footer and typed history-container backlink reciprocate',
            'scope': 'Native ownership container only; no occurrence transform, component geometry or mesh assignment inferred'},
        'history': {'object_id': history_id, 'class_guid': HISTORY_GUID, 'record_offset': history_record.start,
            'owner_object_id': container_id, 'container_history_reference_offset': container_record.end-55,
            'ordered_native_entry_object_ids': history_ids, 'native_entry_index': history_ids.index(identity),
            'payload_hex': history.hex(),
            'scope': 'Explicit native sequence position, not a separately captured API timeline index or general edit/lifecycle state'},
        'stored_payload': {'offset': record.body, 'end_offset': record.end, 'hex': body.hex(),
            'exact_full_payload_replay': True}, 'scope': SCOPE}


def decode_base_feature_empty_lists(data, records, features):
    result = {'partial': [], 'unresolved': [], 'scope': SCOPE}
    named = {}
    for feature in features:
        named.setdefault(feature['object_id'], []).append(feature)
    for record in records:
        if not record.is_primary or record.class_guid != BASE_FEATURE:
            continue
        body = data[record.body:record.end]
        if body[:1] == b'\1':
            continue  # Existing paired-body decoder owns that distinct layout.
        try:
            rows = named.get(record.object_id, [])
            if len(rows) != 1:
                raise ValueError('Empty-list BaseFeature named metadata absent or ambiguous')
            result['partial'].append(decode_base_feature_empty_list(data, records, rows[0]))
        except (ValueError, KeyError, IndexError, TypeError, struct.error, UnicodeError) as error:
            result['unresolved'].append({'feature_object_id': record.object_id, 'reason': str(error)})
    return result
