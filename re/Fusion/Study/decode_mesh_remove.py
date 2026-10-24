"""Observed MeshRemove singleton selections and retained native source proofs.

The API's multi-input add can return multiple native feature records in a different
order. Each feature is decoded from its own typed selection, never array order.
"""
import lzma
import struct
import uuid

from decode_mesh_contents import MESH, _require
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_mesh_selections import decode_mesh_selection
from decode_retained_mesh_sources import decode_retained_mesh_source
from decode_parameters import read_string
from decode_sketch import reference
from decode_timeline import feature_state

REMOVE = '57A2E341-A23A-469D-B41D-59B57A9AD8B8'
SCOPE = ('Observed MeshRemove definitions with one owned MeshBody selection each, typed retained native '
         'source/BaseMesh/asset routes and explicit current counted collection nonmembership. Multi-input '
         'API call grouping/order, general deletion/visibility flags, temporal lifecycle and regeneration unresolved.')


def decode_mesh_remove(data, records, features, member, members, mesh_contents=None):
    """Return decoded/unresolved/scope, rows feature_object_id/kind/name/settings."""
    result = dict(decoded=[],unresolved=[],scope=SCOPE)
    candidates = [r for r in records if r.is_primary and r.class_guid == REMOVE]
    if not candidates:
        return result
    grouped, named = {}, {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    for feature in features:
        named.setdefault(feature['object_id'], []).append(feature)
    def typed(identity, guid):
        rows = grouped.get(identity, [])
        _require(len(rows)==1 and rows[0].class_guid==guid, 'MeshRemove typed identity missing, ambiguous or wrong class')
        record=rows[0]
        return record,data[record.body:record.end]
    meshes = mesh_contents if mesh_contents is not None else decode_mesh_contents_variants(data,records,member,members)
    native_mesh_ids = {r.object_id for r in records if r.is_primary and r.class_guid == MESH}
    for record in candidates:
        try:
            typed(record.object_id, REMOVE)
            rows=named.get(record.object_id,[])
            _require(len(rows)==1 and rows[0].get('class_guid')==REMOVE and rows[0].get('record_offset')==record.start
                and rows[0].get('native_kind_label')=='MeshRemove', 'MeshRemove discovered feature metadata differs')
            feature=rows[0]
            body=data[record.body:record.end]
            _require(body[:2]==bytes(2), 'MeshRemove singleton-selection prefix differs')
            selection=decode_mesh_selection(data,records,reference(body,2),record.object_id)
            nil,cursor=read_string(body,13)
            _require(nil==str(uuid.UUID(int=0)) and cursor==89 and body[89:92]==bytes(3)
                and struct.unpack_from('<I',body,92)[0]==2, 'MeshRemove nil UUID/dependency table framing differs')
            repeated=[reference(body,96+11*i) for i in range(2)]
            _require(repeated==[selection['proxy_object_id'],selection['descriptor_object_id']]
                and body[118:122]==b'\xff'*4, 'MeshRemove repeated source dependencies or label marker differ')
            label,cursor=read_string(body,122)
            index=struct.unpack_from('<Q',body,cursor)[0]
            name,tail=read_string(body,cursor+8)
            _require(label=='MeshRemove' and index==feature.get('stored_index') and name==feature.get('name')
                and len(body)-tail==66, 'MeshRemove label/index/name/shared footer extent differs')
            state=feature_state(body)
            state_id=reference(body,tail+7)
            _,state_body=typed(state_id,'B7F34D7B-DAC4-41A5-B67D-D672537C3BFA')
            _require(state_body==bytes.fromhex('0000000000000100000000000000'), 'Unobserved MeshRemove stored state payload')
            source=decode_retained_mesh_source(data,records,selection['mesh_object_id'],selection,member,members)
            current_ids=source['retained_owner_collection_member_ids']
            _require(source['retained_membership_status']=='NotInCountedMembers' and len(native_mesh_ids) in (1,2)
                and len(current_ids) in (0,1) and len(candidates) in (1,2)
                and source['geometry']['node_count']==source['geometry']['triangle_count']==4,
                'MeshRemove outside captured retained tetra/small root family')
            current=[r for r in meshes['decoded'] if r['mesh_object_id'] in current_ids]
            _require(len({r['mesh_object_id'] for r in current})==len(current), 'MeshRemove remaining cache identity ambiguous')
            for row in current:
                _require(row['mesh_collection_object_id']==source['retained_mesh_collection_object_id']
                    and row['component_object_id']==source['component_object_id']
                    and row['collection_mesh_object_ids']==current_ids, 'MeshRemove remaining current mesh owner/membership differs')
            def ref(identity):return b'\1'+struct.pack('<Q',identity)+bytes(2)
            def text(value):return struct.pack('<I',len(value))+value.encode('utf-16le')
            replay=(bytes(2)+ref(selection['proxy_object_id'])+text(nil)+bytes(3)
                +struct.pack('<I',2)+b''.join(ref(i) for i in repeated)+b'\xff'*4+text(label)
                +struct.pack('<Q',index)+text(name)+body[tail:])
            _require(replay==body, 'MeshRemove complete feature payload replay differs')
            settings=dict(operation='Remove',input_selection=selection,retained_source=source,
                selected_mesh_object_id=selection['mesh_object_id'],selected_mesh_is_in_current_counted_members=False,
                current_mesh_collection_object_id=source['retained_mesh_collection_object_id'],
                component_object_id=source['component_object_id'],current_counted_mesh_object_ids=current_ids,
                current_counted_mesh_count=len(current_ids),current_counted_meshes=current,
                remaining_geometry_unresolved=[r for r in meshes['unresolved'] if r['mesh_object_id'] in current_ids],
                native_feature_record_input_count=1,
                API_add_call_group=None,API_returned_array_index=None,
                grouping_scope='Each native feature has its own owned singleton selection. Saved API multi-input add returns two features in reversed request order; no native call-group or returned-array index association inferred.',
                is_deleted=None,is_hidden=None,
                lifecycle_scope='Selected source is explicitly absent from current counted collection but retained with reciprocal BaseMesh and asset links. No general deletion, hidden/visibility flag, API BaseFeature ownership or historical replay inferred.',
                repeated_dependency_object_ids=repeated,
                layout=dict(feature_body_offset=record.body,feature_body_end_offset=record.end,feature_body_hex=body.hex(),
                    source_reference_body_relative_offset=2,repeated_dependency_body_relative_offset=96,
                    stored_state_object_id=state_id,stored_state_payload_hex=state_body.hex(),
                    shared_footer_hex=body[tail:].hex(),shared_feature_state=state,exact_full_payload_replay=True))
            result['decoded'].append(dict(feature_object_id=record.object_id,kind='MeshRemove',name=name,settings=settings))
        except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error,lzma.LZMAError) as error:
            result['unresolved'].append(dict(feature_object_id=record.object_id,class_guid=REMOVE,reason=str(error)))
    return result
