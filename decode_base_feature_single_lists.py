"""Partial captured singleton-body BaseFeature definitions; no lifecycle replay."""
import struct
import uuid

from decode_base_feature_empty_lists import (BASE_FEATURE, CONTROLLER, BOOKKEEPING,
    OWNER_LINK, COLLECTION, COLLECTION_MEMBERS, HISTORY_CONTAINER)
from decode_body_properties import BODY
from decode_body_selections import decode_body_selections
from decode_parameters import read_string
from decode_sketch import reference
from decode_timeline import HISTORY_GUID, feature_state

SCOPE = ('Partial singleton stored-body/result-anchor BaseFeature definition with reciprocal controller, '
    'bookkeeping, collection and history membership. Table body and independently anchored result body '
    'remain distinct; no source mesh identity, PM/DM semantics, arbitrary direct edits or lifecycle replay.')


def decode_base_feature_single_list(data, records, feature, *, body_selections=None):
    groups = {}
    for record in records:
        if record.is_primary:
            groups.setdefault(record.object_id, []).append(record)

    def typed(identity, guid):
        rows = groups.get(identity, [])
        if len(rows) != 1 or rows[0].class_guid != guid:
            raise ValueError('Singleton BaseFeature typed identity missing, ambiguous or wrong class')
        record = rows[0]
        return record, data[record.body:record.end]

    def inherited(identity, guid):
        rows = [r for r in records if not r.is_primary and r.object_id == identity and r.class_guid == guid]
        if len(rows) != 1:
            raise ValueError('Singleton BaseFeature inherited ownership absent or ambiguous')
        record = rows[0]
        return record, data[record.body:record.end]

    identity = feature['object_id']
    record, body = typed(identity, BASE_FEATURE)
    if feature.get('class_guid') != BASE_FEATURE or feature.get('record_offset') != record.start:
        raise ValueError('Singleton BaseFeature feature metadata differs from primary record')
    if (len(body) != 289 or body[:5] != b'\1\1\0\0\0'
            or body[16:35] != bytes.fromhex('00000000010000000000000000010001000000')
            or body[46] != 0 or body[58:66] != struct.pack('<II', 0, 1)
            or body[77:85] != bytes(8)):
        raise ValueError('Unobserved singleton BaseFeature body/result table framing')
    table_body_id = reference(body, 5)
    if reference(body, 35) != table_body_id:
        raise ValueError('Singleton BaseFeature repeated body table disagrees')
    table_record, _ = typed(table_body_id, BODY)
    controller_id = reference(body, 47)
    controller_record, controller = typed(controller_id, CONTROLLER)
    if (len(controller) != 71 or controller[:14] != bytes(14)
            or reference(controller, 14) != identity or reference(controller, 60) != identity
            or controller[25:48] != bytes(20)+bytes.fromhex('010000') or controller[59] != 0):
        raise ValueError('Singleton BaseFeature controller framing/reciprocal owners disagree')
    bookkeeping_id = reference(controller, 48)
    bookkeeping_record, bookkeeping = typed(bookkeeping_id, BOOKKEEPING)
    if (len(bookkeeping) != 39 or bookkeeping[:12] != bytes(12)
            or reference(bookkeeping, 12) != controller_id or bookkeeping[31:] != bytes(8)):
        raise ValueError('Singleton BaseFeature controller/bookkeeping backlink disagrees')
    anchor_id = reference(body, 66)
    selections = decode_body_selections(data, records) if body_selections is None else body_selections
    anchors = [a for a in selections['body_anchors'] if a['object_id'] == anchor_id]
    if len(anchors) != 1 or anchors[0]['source_owner_object_id'] != identity:
        raise ValueError('Singleton BaseFeature result anchor missing, ambiguous or wrong owner')
    anchor = anchors[0]
    result_body_id = anchor['native_body_object_id']
    typed(result_body_id, BODY)
    if result_body_id == table_body_id:
        raise ValueError('Unobserved singleton BaseFeature coincident table/result bodies')
    namespace, cursor = read_string(body, 85)
    if (namespace != str(uuid.UUID(int=0)) or cursor != 161
            or body[161:168] != bytes.fromhex('00000001000000')
            or reference(body, 168) != controller_id):
        raise ValueError('Singleton BaseFeature nil UUID/repeated controller table disagrees')
    metadata = struct.unpack_from('<I', body, 179)[0]
    label, cursor = read_string(body, 183)
    index = struct.unpack_from('<Q', body, cursor)[0]
    name, cursor = read_string(body, cursor+8)
    if (metadata != 5 or label != 'Base Feature' or name != '' or cursor != 223
            or len(body)-cursor != 66 or index != feature.get('stored_index') or feature.get('name') is not None):
        raise ValueError('Singleton BaseFeature native metadata/empty-name/footer extent disagrees')
    owner_record, owner = inherited(identity, OWNER_LINK)
    controller_owner_record, controller_owner = inherited(controller_id, OWNER_LINK)
    if len(owner) != 11 or controller_owner != owner:
        raise ValueError('Singleton BaseFeature/controller collection owners disagree')
    collection_id = reference(owner, 0)
    collection_record, collection = typed(collection_id, COLLECTION)
    if collection != bytes(2):
        raise ValueError('Unobserved singleton BaseFeature owner collection payload')
    membership_record, membership = inherited(collection_id, COLLECTION_MEMBERS)
    count = struct.unpack_from('<I', membership, 0)[0]
    if not 1 <= count <= 10000 or len(membership) != 15+11*count:
        raise ValueError('Singleton BaseFeature collection counted extent unsupported')
    member_ids = [reference(membership, 4+11*i) for i in range(count)]
    if len(set(member_ids)) != count or member_ids.count(identity) != 1 or member_ids.count(controller_id) != 1:
        raise ValueError('Singleton BaseFeature/controller counted membership missing or repeated')
    if any(len(groups.get(member, [])) != 1 for member in member_ids):
        raise ValueError('Singleton BaseFeature collection member missing or ambiguous')
    container_id = reference(membership, 4+11*count)
    container_record, container = typed(container_id, HISTORY_CONTAINER)
    if len(container) < 66 or reference(container, len(container)-22) != collection_id:
        raise ValueError('Singleton BaseFeature collection/container backlink disagrees')
    history_id = reference(container, len(container)-55)
    history_record, history = typed(history_id, HISTORY_GUID)
    if history[:2] != bytes(2) or reference(history, 2) != container_id:
        raise ValueError('Singleton BaseFeature history/container ownership disagrees')
    history_count = struct.unpack_from('<I', history, 13)[0]
    if not 1 <= history_count <= 100000 or len(history) != 17+11*history_count:
        raise ValueError('Singleton BaseFeature history counted extent unsupported')
    history_ids = [reference(history, 17+11*i) for i in range(history_count)]
    if len(set(history_ids)) != history_count or history_ids.count(identity) != 1:
        raise ValueError('Singleton BaseFeature unique history membership disagrees')
    if any(len(groups.get(member, [])) != 1 for member in history_ids):
        raise ValueError('Singleton BaseFeature history member missing or ambiguous')
    def ref(value): return b'\1'+struct.pack('<Q', value)+bytes(2)
    def text(value): return struct.pack('<I', len(value))+value.encode('utf-16le')
    replay = (b'\1'+struct.pack('<I',1)+ref(table_body_id)+body[16:35]+ref(table_body_id)+b'\0'
        +ref(controller_id)+struct.pack('<II',0,1)+ref(anchor_id)+bytes(8)+text(namespace)
        +bytes.fromhex('00000001000000')+ref(controller_id)+struct.pack('<I',metadata)
        +text(label)+struct.pack('<Q',index)+text(name)+body[cursor:])
    if replay != body:
        raise ValueError('Singleton BaseFeature exact payload replay disagrees')
    return dict(feature_object_id=identity, name=None, stored_name=name, stored_index=index,
        definition_status='PartialObservedSingletonBodyAndResultAnchorLayout',
        stored_native_kind_label=label, stored_body_table_object_ids=[table_body_id],
        stored_body_record_offsets=[table_record.start], repeated_body_table_object_ids=[table_body_id],
        result_anchor_object_ids=[anchor_id], anchored_result_native_body_object_ids=[result_body_id],
        result_anchor=anchor, stored_table_metadata=metadata, table_metadata_semantics='Literal5 only; enum/flag meaning unassigned',
        source_mesh_object_id=None, PM_DM_body_pair_semantics=None, entire_contained_object_state=None,
        stored_shared_feature_state=feature_state(body),
        controller=dict(object_id=controller_id, class_guid=CONTROLLER, record_offset=controller_record.start,
            bookkeeping_object_id=bookkeeping_id, bookkeeping_record_offset=bookkeeping_record.start,
            payload_hex=controller.hex(), bookkeeping_payload_hex=bookkeeping.hex()),
        ownership=dict(collection_object_id=collection_id, collection_record_offset=collection_record.start,
            feature_owner_fragment_offset=owner_record.body, controller_owner_fragment_offset=controller_owner_record.body,
            membership_fragment_offset=membership_record.body, counted_member_object_ids=member_ids,
            native_history_container_object_id=container_id, native_history_container_record_offset=container_record.start),
        history=dict(object_id=history_id, record_offset=history_record.start,
            ordered_native_entry_object_ids=history_ids, native_entry_index=history_ids.index(identity)),
        stored_payload=dict(offset=record.body, end_offset=record.end, hex=body.hex(), exact_full_payload_replay=True),
        scope=SCOPE)


def decode_base_feature_single_lists(data, records, features, *, body_selections=None):
    result = dict(partial=[], unresolved=[], scope=SCOPE)
    by = {}
    for feature in features:
        by.setdefault(feature['object_id'], []).append(feature)
    for record in records:
        if not record.is_primary or record.class_guid != BASE_FEATURE:
            continue
        body = data[record.body:record.end]
        if body[:5] != b'\1\1\0\0\0':
            continue  # Existing absent/pair readers retain their own layouts/errors.
        try:
            if len(by.get(record.object_id, [])) != 1:
                raise ValueError('Singleton BaseFeature named metadata absent or ambiguous')
            result['partial'].append(decode_base_feature_single_list(data, records, by[record.object_id][0], body_selections=body_selections))
        except (ValueError, KeyError, IndexError, TypeError, struct.error, UnicodeError) as error:
            result['unresolved'].append(dict(feature_object_id=record.object_id, reason=str(error)))
    return result
