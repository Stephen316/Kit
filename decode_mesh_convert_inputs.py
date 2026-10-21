"""Observed two-input Faceted parametric Convert definition and typed routes.

The two source selections and two result anchors are independent ordered lists.
Neither list order nor geometry is a source-to-result identity pairing.
"""
import lzma
import struct
import uuid

from decode_body_selections import decode_body_selections
from decode_mesh_contents import MESH,_require
from decode_mesh_convert import CONVERT,SOURCE_LIST,STATE,CONTROLLER
from decode_mesh_selections import decode_mesh_selection
from decode_retained_mesh_sources import decode_retained_mesh_source
from decode_parameters import read_string
from decode_sketch import reference
from decode_timeline import feature_state

SCOPE=('Observed two-input Faceted parametric MeshConvert counted selections/results/state-controller graph, '
       'typed retained mesh sources and native result BODY/history/ASM identifier routes. Source-to-result '
       'pairing, unvaried method/operation enum bytes, additional inputs, lifecycle and regeneration unresolved.')


def decode_mesh_convert_inputs(data,records,features,member,members):
    """Return decoded/unresolved/scope; rows feature_object_id/kind/name/settings."""
    result=dict(decoded=[],unresolved=[],scope=SCOPE)
    candidates=[]
    for record in records:
        if record.is_primary and record.class_guid==CONVERT:
            body=data[record.body:record.end]
            if len(body)>=14 and struct.unpack_from('<I',body,10)[0]!=1:
                candidates.append(record)
    if not candidates:return result
    grouped,named={},{}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    for feature in features:named.setdefault(feature['object_id'],[]).append(feature)
    def typed(identity,guid):
        rows=grouped.get(identity,[])
        _require(len(rows)==1 and rows[0].class_guid==guid,'Multi-input Convert typed reference missing, ambiguous or wrong class')
        record=rows[0]
        return record,data[record.body:record.end]
    anchors=decode_body_selections(data,records)['body_anchors']
    for record in candidates:
        try:
            typed(record.object_id,CONVERT)
            rows=named.get(record.object_id,[])
            _require(len(rows)==1 and rows[0].get('class_guid')==CONVERT and rows[0].get('record_offset')==record.start
                and rows[0].get('native_kind_label')=='Convert Mesh','Multi-input Convert discovery metadata differs')
            feature=rows[0];owner=record.object_id
            body=data[record.body:record.end]
            _require(body[:10]==bytes.fromhex('00010000000003000000') and struct.unpack_from('<I',body,10)[0]==2,
                'Only observed two-source Faceted parametric Convert header supported')
            source_list_ids=[reference(body,14+11*i) for i in range(2)]
            _require(len(set(source_list_ids))==2,'Multi-input Convert source lists repeat')
            selections=[];source_list_payloads=[]
            for identity in source_list_ids:
                _,payload=typed(identity,SOURCE_LIST)
                _require(len(payload)==20 and payload[:3]==bytes(3) and payload[14:]==bytes.fromhex('010100000000'),
                    'Multi-input Convert source-list framing differs')
                selections.append(decode_mesh_selection(data,records,reference(payload,3),owner))
                source_list_payloads.append(payload.hex())
            _require(len({s['proxy_object_id'] for s in selections})==len({s['mesh_object_id'] for s in selections})==2,
                'Multi-input Convert owned source selections alias')
            _require(body[36:46]==b'\xff'*4+bytes(6) and struct.unpack_from('<I',body,46)[0]==2,
                'Multi-input Convert source/result counted-table framing differs')
            anchor_ids=[reference(body,50+11*i) for i in range(2)]
            _require(len(set(anchor_ids))==2 and body[72:80]==bytes(8),'Multi-input Convert result anchor list/separator differs')
            result_anchors=[]
            for identity in anchor_ids:
                matches=[a for a in anchors if a['object_id']==identity and a['source_owner_object_id']==owner]
                _require(len(matches)==1,'Multi-input Convert result anchor is not uniquely typed/owned')
                result_anchors.append(matches[0])
            _require(len({a['native_body_object_id'] for a in result_anchors})==len({a['native_uuid_text'] for a in result_anchors})==2,
                'Multi-input Convert result BODY identities/UUIDs alias')
            nil,cursor=read_string(body,80)
            _require(nil==str(uuid.UUID(int=0)) and cursor==156 and body[156:159]==bytes(3)
                and struct.unpack_from('<I',body,159)[0]==4,'Multi-input Convert nil/dependency framing differs')
            repeated=[reference(body,163+11*i) for i in range(4)]
            expected=[identity for s in selections for identity in (s['proxy_object_id'],s['descriptor_object_id'])]
            _require(repeated==expected and struct.unpack_from('<I',body,207)[0]==4,
                'Multi-input Convert repeated owned selection table/literal marker differs')
            label,cursor=read_string(body,211)
            index=struct.unpack_from('<Q',body,cursor)[0]
            name,tail=read_string(body,cursor+8)
            _require(label=='Convert Mesh' and index==feature.get('stored_index') and name==feature.get('name')
                and len(body)-tail==66,'Multi-input Convert label/index/name/footer framing differs')
            shared_state=feature_state(body)
            state_id=reference(body,tail+7)
            _,state=typed(state_id,STATE)
            _require(len(state)==52 and state[:6]==bytes(2)+struct.pack('<I',2),
                'Multi-input Convert counted state framing differs')
            controller_ids=[reference(state,6+19*i) for i in range(2)]
            literal_words=[struct.unpack_from('<Q',state,17+19*i)[0] for i in range(2)]
            _require(len(set(controller_ids))==2 and literal_words==[1,2]
                and struct.unpack_from('<Q',state,44)[0]==3,'Multi-input Convert state literal table/trailer differs')
            controllers=[]
            def ref(identity):return b'\1'+struct.pack('<Q',identity)+bytes(2)
            def text(value):return struct.pack('<I',len(value))+value.encode('utf-16le')
            for controller_id in controller_ids:
                _,payload=typed(controller_id,CONTROLLER)
                _require(payload[:3]==bytes(3),'Multi-input Convert controller prefix differs')
                controller_uuid,c=read_string(payload,3)
                matches=[a for a in result_anchors if a['native_uuid_text']==controller_uuid]
                _require(len(matches)==1 and c==79 and len(payload)==134,
                    'Multi-input Convert controller UUID does not uniquely match an owned result anchor')
                leading,one,label_count=struct.unpack_from('<III',payload,79)
                _require(leading in (1,2) and one==1 and label_count==4 and payload[91:95]==b'1234',
                    'Multi-input Convert controller literal labels/leading words differ')
                table_count=struct.unpack_from('<I',payload,95)[0]
                _require(table_count==5 and list(struct.unpack_from('<5I',payload,99))==list(range(5))
                    and payload[127:]==bytes.fromhex('00010000000000'),
                    'Multi-input Convert controller literal table/trailer differs')
                opaque=struct.unpack_from('<Q',payload,119)[0]
                replay=(bytes(3)+text(controller_uuid)+struct.pack('<III',leading,one,4)+b'1234'
                    +struct.pack('<I',5)+struct.pack('<5I',*range(5))+struct.pack('<Q',opaque)+bytes.fromhex('00010000000000'))
                _require(replay==payload,'Multi-input Convert controller payload replay differs')
                controllers.append(dict(controller_object_id=controller_id,native_uuid_text=controller_uuid,
                    matched_result_anchor_object_id=matches[0]['object_id'],matched_native_body_object_id=matches[0]['native_body_object_id'],
                    stored_leading_uint32=leading,stored_second_uint32=one,controller_literal_labels='1234',
                    controller_stored_table=list(range(5)),controller_uninterpreted_uint64=opaque,
                    stored_controller_payload_hex=payload.hex(),exact_payload_replay=True))
            _require(len({c['matched_result_anchor_object_id'] for c in controllers})==2,
                'Multi-input Convert controller/result UUID correspondence not bijective')
            state_replay=bytes(2)+struct.pack('<I',2)+b''.join(ref(i)+struct.pack('<Q',v) for i,v in zip(controller_ids,literal_words))+struct.pack('<Q',3)
            _require(state_replay==state,'Multi-input Convert state payload replay differs')
            sources=[decode_retained_mesh_source(data,records,s['mesh_object_id'],s,member,members) for s in selections]
            _require(len({s['component_object_id'] for s in sources})==len({s['retained_mesh_collection_object_id'] for s in sources})==1
                and all(s['retained_owner_collection_member_ids']==[] and s['retained_membership_status']=='NotInCountedMembers'
                    and (s['geometry']['node_count'],s['geometry']['triangle_count'])==(4,4) for s in sources)
                and {r.object_id for r in records if r.is_primary and r.class_guid==MESH}=={s['mesh_object_id'] for s in sources},
                'Multi-input Convert outside captured two retained tetra sources/current empty collection family')
            from decode_mesh_convert_result_bodies import decode_mesh_convert_result_bodies
            routes=decode_mesh_convert_result_bodies(data,records,member,members,owner,anchor_ids,sources[0]['component_object_id'])
            _require(routes['result_body_anchors']==result_anchors
                and routes['result_native_body_object_ids']==[a['native_body_object_id'] for a in result_anchors],
                'Multi-input Convert independent result route disagrees with owned anchor list')
            replay=(bytes.fromhex('00010000000003000000')+struct.pack('<I',2)+b''.join(ref(i) for i in source_list_ids)
                +b'\xff'*4+bytes(6)+struct.pack('<I',2)+b''.join(ref(i) for i in anchor_ids)+bytes(8)+text(nil)
                +bytes(3)+struct.pack('<I',4)+b''.join(ref(i) for i in repeated)+struct.pack('<I',4)
                +text(label)+struct.pack('<Q',index)+text(name)+body[tail:])
            _require(replay==body,'Multi-input Convert full feature payload replay differs')
            settings=dict(mesh_convert_method='Faceted',mesh_convert_operation='ObservedParametricFeature',
                method_decode_scope='Only captured Faceted native prefix admitted; method enum alternatives are not inferred from invariant header words',
                operation_decode_scope='Explicit parametric Convert class/owned sources/results/controller/history graph; raw header codes are not assigned API operation enum semantics',
                stored_uninterpreted_header_uint32=list(struct.unpack_from('<II',body,2)),
                source_list_object_ids=source_list_ids,source_mesh_selections=selections,qualified_source_meshes=sources,
                result_anchor_object_ids=anchor_ids,**routes,
                source_to_result_pairing=None,
                pairing_scope='Independent native source selection list and result anchor list. No ordinal, name, coordinate, proximity or shape match pairs a source mesh with a resulting BODY.',
                state_object_id=state_id,history_controllers=controllers,
                state_literal_uint64_words=literal_words,state_literal_trailer_uint64=3,
                state_controller_scope='Owned typed state refs plus unique exact UUID equality to owned result anchors. Literal counters/label tables remain uninterpreted and are not face IDs or replay instructions.',
                repeated_dependency_object_ids=repeated,inactive_controls_scope='Organic resolution/accuracy/numberOfFaces/preprocess not decoded as active controls',
                geometry_scope='Explicit result BODY/history/ASM identifier association and retained source assets are separately qualified; no conversion regeneration or persistent source/result lifecycle inferred',
                layout=dict(feature_body_offset=record.body,feature_body_end_offset=record.end,feature_body_hex=body.hex(),
                    source_count_body_relative_offset=10,result_count_body_relative_offset=46,
                    stored_source_list_payloads_hex=source_list_payloads,stored_state_payload_hex=state.hex(),
                    shared_footer_hex=body[tail:].hex(),shared_feature_state=shared_state,
                    exact_full_payload_replay=True,exact_state_payload_replay=True))
            result['decoded'].append(dict(feature_object_id=owner,kind='MeshConvert',name=name,class_guid=CONVERT,settings=settings))
        except (ValueError,KeyError,IndexError,TypeError,UnicodeError,struct.error,lzma.LZMAError) as error:
            result['unresolved'].append(dict(feature_object_id=record.object_id,class_guid=CONVERT,reason=str(error)))
    return result
