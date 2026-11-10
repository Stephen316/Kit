"""Partial singleton BaseMeshFeature definitions, independent of mesh lifecycle.

The feature's forward typed mesh list is qualified here. A reciprocal mesh owner,
current collection membership and mesh/asset contents require separate readers.
"""
import struct
import uuid

from decode_base_feature_empty_lists import (CONTROLLER, BOOKKEEPING, OWNER_LINK,
    COLLECTION, COLLECTION_MEMBERS, HISTORY_CONTAINER)
from decode_mesh_contents import MESH_FEATURE, MESH
from decode_parameters import read_string
from decode_sketch import reference
from decode_timeline import HISTORY_GUID, feature_state

SCOPE = ('Partial captured singleton263-byte empty-name BaseMeshFeature definition with typed forward '
         'mesh membership and reciprocal controller/bookkeeping/feature-collection/native-history links. '
         'Mesh owner backlink, current membership, assets, API BaseFeature ownership, lifecycle and geometry '
         'are not qualified; existing feature classification and diagnostics unchanged.')


def decode_base_mesh_feature_definition(data, records, feature):
    """Read one exact observed native definition; never decode a mesh asset."""
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)

    def typed(identity, guid=None):
        matches = grouped.get(identity, [])
        if len(matches) != 1 or (guid is not None and matches[0].class_guid != guid):
            raise ValueError('BaseMesh definition typed identity missing, ambiguous or wrong class')
        record = matches[0]
        return record, data[record.body:record.end]

    def inherited(identity, guid):
        matches = [r for r in records if not r.is_primary and r.object_id == identity and r.class_guid == guid]
        if len(matches) != 1:
            raise ValueError('BaseMesh definition inherited ownership missing or ambiguous')
        record = matches[0]
        return record, data[record.body:record.end]

    identity = feature['object_id']
    record, body = typed(identity, MESH_FEATURE)
    if feature.get('class_guid') != MESH_FEATURE or feature.get('record_offset') != record.start:
        raise ValueError('BaseMesh definition feature metadata differs from native primary record')
    if (len(body) != 263 or body[:6] != bytes(2)+struct.pack('<I',1)
            or body[17:22] != bytes(5) or body[33:49] != bytes(16)):
        raise ValueError('Unobserved BaseMesh singleton263-byte definition framing')
    mesh_id = reference(body,6)
    mesh_record, _ = typed(mesh_id,MESH)
    controller_id = reference(body,22)
    controller_record, controller = typed(controller_id,CONTROLLER)
    if (len(controller) != 71 or controller[:14] != bytes(14)
            or reference(controller,14) != identity or reference(controller,60) != identity
            or controller[25:48] != bytes(20)+bytes.fromhex('010000') or controller[59] != 0):
        raise ValueError('BaseMesh definition controller framing/feature backlinks disagree')
    bookkeeping_id = reference(controller,48)
    bookkeeping_record, bookkeeping = typed(bookkeeping_id,BOOKKEEPING)
    if (len(bookkeeping) != 39 or bookkeeping[:12] != bytes(12)
            or reference(bookkeeping,12) != controller_id or bookkeeping[31:] != bytes(8)):
        raise ValueError('BaseMesh definition controller bookkeeping backlink disagrees')
    namespace, cursor = read_string(body,49)
    if (namespace != str(uuid.UUID(int=0)) or cursor != 125
            or body[125:132] != bytes.fromhex('00000001000000')
            or reference(body,132) != controller_id or struct.unpack_from('<i',body,143)[0] != -1):
        raise ValueError('BaseMesh definition nil UUID/repeated controller/metadata framing disagrees')
    label, cursor = read_string(body,147)
    index = struct.unpack_from('<Q',body,cursor)[0]
    name, cursor = read_string(body,cursor+8)
    if (label != 'Base Mesh Feature' or index != feature.get('stored_index') or name != ''
            or feature.get('name') is not None or feature.get('native_kind_label') != label
            or feature.get('parameters') != [] or cursor != 197 or len(body)-cursor != 66):
        raise ValueError('BaseMesh definition empty-name/label/index/footer extent disagrees')
    state = feature_state(body)
    state_id, property_id, feature_book_id = (reference(body,cursor+i) for i in (7,39,53))
    _, state_body = typed(state_id,'B7F34D7B-DAC4-41A5-B67D-D672537C3BFA')
    _, property_body = typed(property_id,'5FBE538E-139B-46D4-BCAF-CC796D1E1F78')
    feature_book_record, feature_book = typed(feature_book_id,BOOKKEEPING)
    if (state_body != bytes.fromhex('0000000000000100000000000000')
            or property_body != bytes.fromhex('0001000000000000000000000000')
            or len(feature_book) != 77 or feature_book[:12] != bytes.fromhex('000000000000010102000000')
            or reference(feature_book,31) != identity or reference(feature_book,50) != identity
            or feature_book[69:] != bytes(8)):
        raise ValueError('BaseMesh definition footer/property/bookkeeping references disagree')
    related_id = reference(feature_book,12)
    related_record, _ = typed(related_id)
    owner_record, owner = inherited(identity,OWNER_LINK)
    controller_owner_record, controller_owner = inherited(controller_id,OWNER_LINK)
    if len(owner) != 11 or controller_owner != owner:
        raise ValueError('BaseMesh definition feature/controller inherited collections disagree')
    collection_id = reference(owner,0)
    collection_record, collection = typed(collection_id,COLLECTION)
    if collection != bytes(2):
        raise ValueError('Unobserved BaseMesh definition feature collection primary payload')
    membership_record, membership = inherited(collection_id,COLLECTION_MEMBERS)
    count = struct.unpack_from('<I',membership,0)[0]
    if not 1 <= count <= 10000 or len(membership) != 15+11*count:
        raise ValueError('BaseMesh definition collection counted extent unsupported')
    member_ids = [reference(membership,4+11*i) for i in range(count)]
    if len(set(member_ids)) != count or member_ids.count(identity) != 1 or member_ids.count(controller_id) != 1:
        raise ValueError('BaseMesh definition feature/controller collection membership absent or repeated')
    for member_id in member_ids:
        typed(member_id)
    container_id = reference(membership,4+11*count)
    container_record, container = typed(container_id,HISTORY_CONTAINER)
    if len(container) < 66 or reference(container,len(container)-22) != collection_id:
        raise ValueError('BaseMesh definition history-container collection backlink disagrees')
    history_id = reference(container,len(container)-55)
    history_record, history = typed(history_id,HISTORY_GUID)
    if history[:2] != bytes(2) or reference(history,2) != container_id:
        raise ValueError('BaseMesh definition history/container ownership disagrees')
    history_count = struct.unpack_from('<I',history,13)[0]
    if not 1 <= history_count <= 100000 or len(history) != 17+11*history_count:
        raise ValueError('BaseMesh definition history counted extent unsupported')
    history_ids = [reference(history,17+11*i) for i in range(history_count)]
    if len(set(history_ids)) != history_count or history_ids.count(identity) != 1:
        raise ValueError('BaseMesh definition unique native history membership disagrees')
    for history_member in history_ids:
        typed(history_member)
    def ref(value):return b'\1'+struct.pack('<Q',value)+bytes(2)
    def text(value):return struct.pack('<I',len(value))+value.encode('utf-16le')
    replay = (bytes(2)+struct.pack('<I',1)+ref(mesh_id)+bytes(5)+ref(controller_id)+bytes(16)
        +text(namespace)+bytes.fromhex('00000001000000')+ref(controller_id)+struct.pack('<i',-1)
        +text(label)+struct.pack('<Q',index)+text(name)+body[cursor:])
    if replay != body:
        raise ValueError('BaseMesh definition complete payload replay disagrees')
    return dict(feature_object_id=identity,name=None,stored_name=name,stored_index=index,
        definition_status='PartialObservedSingletonForwardMeshDefinition',stored_native_kind_label=label,
        stored_mesh_object_ids=[mesh_id],stored_mesh_records=[dict(object_id=mesh_id,class_guid=MESH,
            record_offset=mesh_record.start,body_offset=mesh_record.body,end_offset=mesh_record.end)],
        mesh_membership_scope='Explicit feature-owned counted forward typed mesh reference only; mesh owner backlink requires independent source framing',
        mesh_owner_backlink_qualified=False,current_mesh_membership=None,mesh_assets=None,API_BaseFeature_owner=None,
        stored_nil_uuid=namespace,stored_table_metadata=-1,table_metadata_semantics='Literal signed -1 retained; no enum/flag meaning assigned',
        stored_shared_feature_state=state,
        controller=dict(object_id=controller_id,class_guid=CONTROLLER,record_offset=controller_record.start,
            feature_backlink_offsets=[controller_record.body+14,controller_record.body+60],
            bookkeeping_object_id=bookkeeping_id,bookkeeping_record_offset=bookkeeping_record.start,
            bookkeeping_backlink_offset=bookkeeping_record.body+12,payload_hex=controller.hex(),
            bookkeeping_payload_hex=bookkeeping.hex(),opaque_bookkeeping_8byte_hex=bookkeeping[23:31].hex()),
        footer=dict(state_object_id=state_id,property_object_id=property_id,feature_bookkeeping_object_id=feature_book_id,
            feature_bookkeeping_record_offset=feature_book_record.start,feature_bookkeeping_payload_hex=feature_book.hex(),
            stored_related_object_id=related_id,stored_related_object_class_guid=related_record.class_guid,
            related_object_semantics=None,raw_footer_hex=body[cursor:].hex()),
        ownership=dict(collection_object_id=collection_id,collection_record_offset=collection_record.start,
            feature_owner_fragment_offset=owner_record.body,controller_owner_fragment_offset=controller_owner_record.body,
            membership_fragment_offset=membership_record.body,counted_member_object_ids=member_ids,
            membership_payload_hex=membership.hex(),native_history_container_object_id=container_id,
            container_collection_backlink_offset=container_record.end-22),
        history=dict(object_id=history_id,class_guid=HISTORY_GUID,record_offset=history_record.start,owner_object_id=container_id,
            container_history_reference_offset=container_record.end-55,ordered_native_entry_object_ids=history_ids,
            native_entry_index=history_ids.index(identity),payload_hex=history.hex()),
        stored_payload=dict(offset=record.body,end_offset=record.end,hex=body.hex(),exact_full_payload_replay=True),scope=SCOPE)


def decode_base_mesh_feature_definitions(data,records,features):
    """Return partial/unresolved/scope; no asset access or feature mutations."""
    result=dict(partial=[],unresolved=[],scope=SCOPE)
    named={}
    for feature in features:
        named.setdefault(feature['object_id'],[]).append(feature)
    for record in records:
        if not record.is_primary or record.class_guid != MESH_FEATURE:
            continue
        try:
            matches=named.get(record.object_id,[])
            if len(matches) != 1:
                raise ValueError('BaseMesh definition discovered feature identity missing or ambiguous')
            result['partial'].append(decode_base_mesh_feature_definition(data,records,matches[0]))
        except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error) as error:
            result['unresolved'].append(dict(feature_object_id=record.object_id,class_guid=MESH_FEATURE,reason=str(error)))
    return result
