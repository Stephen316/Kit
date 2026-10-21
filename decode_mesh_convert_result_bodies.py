"""Typed Convert/BaseFeature result anchors through native/ASM BODY mapping.

Result and source collections stay distinct. No pairing to mesh inputs is
inferred from anchor order, body order, coordinates or API names.
"""
import struct

from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_body_selections import decode_body_selections
from decode_mesh_contents import MESH,_require
from decode_parameters import read_string
from decode_sketch import reference

BODY='D3937028-C20C-4E65-B010-94AD418A5C20'
COLLECTION='CD57BC48-50EC-47DC-975A-FB6DEA72F4DA'
MAPPING='74CA4562-59F8-4C97-8AD1-F8297C21F9AA'
FEATURES={'62B85DC3-27B5-47BA-9F13-B2527B72EE49','D7015B81-AB4D-4C89-BED7-AA4411E1964A'}


def decode_mesh_convert_result_bodies(data,records,member,members,feature_id,result_anchor_ids,component_object_id=None):
    """Return result-route proof for independently qualified feature/anchor operands."""
    records=list(records);grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    def typed(identity,guid):
        rows=grouped.get(identity,[])
        _require(len(rows)==1 and rows[0].class_guid==guid,'Convert result typed reference missing/ambiguous/wrong class')
        record=rows[0];return record,data[record.body:record.end]
    _require(len(grouped.get(feature_id,[]))==1 and grouped[feature_id][0].class_guid in FEATURES,
             'Convert result feature owner unsupported')
    _require(len(result_anchor_ids) in (1,2) and len(set(result_anchor_ids))==len(result_anchor_ids),
             'Convert result anchor list outside observed singleton/two-body family')
    selections=decode_body_selections(data,records)
    owned=[a for a in selections['body_anchors'] if a['source_owner_object_id']==feature_id]
    _require({a['object_id'] for a in owned}==set(result_anchor_ids),
             'Convert result anchor list differs from uniquely owned typed anchors')
    anchors=[next(a for a in owned if a['object_id']==identity) for identity in result_anchor_ids]
    body_ids=[a['native_body_object_id'] for a in anchors]
    _require(len(set(body_ids))==len(body_ids),'Convert result anchors share native BODY')
    collections=[]
    for identity in body_ids:
        _,body=typed(identity,BODY);collections.append(reference(body,len(body)-11))
    _require(len(set(collections))==1,'Convert result BODY collection owners differ')
    collection_id=collections[0];collection_record,collection=typed(collection_id,COLLECTION)
    stored_component_id=reference(collection,len(collection)-11)
    if component_object_id is None:component_object_id=stored_component_id
    _require(component_object_id==stored_component_id,'Convert result explicit component disagrees with collection backlink')
    typed(component_object_id,'E03784ED-5E19-4E14-B9F2-3B07017018CD')
    _require(collection[:3]==bytes(3),'Convert result collection prefix differs')
    body_count,member_count=struct.unpack_from('<II',collection,3)
    _require((body_count,member_count) in ((1,1),(1,2),(2,2)) and body_count==len(body_ids),
             'Convert result collection body/member counts outside observed family')
    member_ids=[reference(collection,11+11*i) for i in range(member_count)]
    _require(len(set(member_ids))==member_count,'Convert result collection members duplicate')
    typed_members=[]
    for identity in member_ids:
        rows=grouped.get(identity,[])
        _require(len(rows)==1 and rows[0].class_guid in (BODY,MESH),
                 'Convert result mixed collection member wrong type')
        typed_members.append(dict(object_id=identity,class_guid=rows[0].class_guid))
    _require({m['object_id'] for m in typed_members if m['class_guid']==BODY}==set(body_ids),
             'Convert result collection BODY members differ from explicit owned anchors')
    cursor=11+11*member_count
    _require(collection[cursor]==1,'Convert result property marker differs')
    property_id=reference(collection,cursor+1);mapping_id=reference(collection,cursor+12)
    _require(collection[cursor+23]==1,'Convert result bookkeeping marker differs')
    bookkeeping_id=reference(collection,cursor+24)
    _require(collection[cursor+35]==0 and struct.unpack_from('<I',collection,cursor+36)[0]==body_count,
             'Convert result repeated BODY count differs')
    repeated=[reference(collection,cursor+40+11*i) for i in range(body_count)]
    component_offset=cursor+40+11*body_count
    _require(len(collection)==component_offset+11 and reference(collection,component_offset)==component_object_id
             and len(set(repeated))==body_count and set(repeated)==set(body_ids),
             'Convert result repeated BODY/component backlinks disagree')
    _,properties=typed(property_id,'E55D0457-898F-4A8E-B1A5-C85BDBA8794F')
    _require(reference(properties,14)==collection_id,'Convert result property table owner differs')
    _,bookkeeping=typed(bookkeeping_id,'372234A0-2A6C-4122-8047-E74DBA04F326')
    _require(len(bookkeeping)==23 and bookkeeping[:12]==bytes(12)
             and reference(bookkeeping,12)==component_object_id,'Convert result collection bookkeeping/component differs')
    mapping_record,payload=typed(mapping_id,MAPPING)
    _require(payload[:2]==bytes(2) and struct.unpack_from('<I',payload,2)[0]==body_count,
             'Convert result native history mapping prefix/count differs')
    entries=[struct.unpack_from('<QQ',payload,6+16*i) for i in range(body_count)]
    _require(len({h for h,_ in entries})==body_count and {identity for _,identity in entries}==set(body_ids),
             'Convert result history handles/native BODY identities duplicate or absent')
    end_pairs=6+16*body_count
    _require(reference(payload,end_pairs)==collection_id and payload[end_pairs+11]==0,
             'Convert result history mapping collection/filename separator differs')
    filename,end=read_string(payload,end_pairs+12)
    _require(end==len(payload) and filename.startswith('BREP.') and filename.endswith('.smbh')
             and '/' not in filename and '\\' not in filename,'Convert result history filename extent/name differs')
    path=member.split('/FusionDesignSegmentType1/')[0]+'/Breps.BlobParts/'+filename
    _require(path in members,'Convert result same-asset history blob missing')
    def ref(identity):return b'\1'+struct.pack('<Q',identity)+bytes(2)
    mapping_replay=bytes(2)+struct.pack('<I',body_count)+b''.join(struct.pack('<QQ',*entry) for entry in entries)+ref(collection_id)+bytes(1)+struct.pack('<I',len(filename))+filename.encode('utf-16le')
    _require(mapping_replay==payload,'Convert result full native history mapping replay differs')
    collection_replay=(bytes(3)+struct.pack('<II',body_count,member_count)+b''.join(ref(i) for i in member_ids)
        +b'\1'+ref(property_id)+ref(mapping_id)+b'\1'+ref(bookkeeping_id)+bytes(1)
        +struct.pack('<I',body_count)+b''.join(ref(i) for i in repeated)+ref(component_object_id))
    _require(collection_replay==collection,'Convert result full collection payload replay differs')
    mapping=dict(mapping_record_object_id=mapping_id,owner_object_id=collection_id,
        history_blob_member=path,body_count=body_count,
        bindings=[dict(stored_handle=handle,native_body_object_id=identity) for handle,identity in entries])
    identifiers=decode_body_asm_identifiers(data,records,member,members,{'decoded':[mapping]})
    _require(len(identifiers['decoded'])==1 and not identifiers['unresolved'],
             'Convert result stored ASM BODY identifier association unresolved')
    return dict(result_body_anchors=anchors,result_native_body_object_ids=body_ids,
        result_body_collection_object_id=collection_id,result_body_component_object_id=component_object_id,
        native_history_mapping=mapping,stored_asm_body_identifiers=identifiers,
        result_collection_provenance=dict(native_entity_members=typed_members,repeated_native_body_object_ids=repeated,
            property_record_object_id=property_id,bookkeeping_record_object_id=bookkeeping_id,
            collection_record_offset=collection_record.start,stored_collection_payload_hex=collection.hex(),
            mapping_record_offset=mapping_record.start,stored_mapping_payload_hex=payload.hex(),
            exact_collection_and_mapping_replay=True,
            scope='Literal mixed entity collection and owned BODY subset; mesh entries do not establish source/result pairing or current mesh membership'),
        result_identity_scope='Owned anchors and reciprocal native BODY/collection mapping qualify same-blob ASM stored IDs. Stored handles are not record ordinals; no per-input/result pairing, lifecycle, current visibility or regeneration inferred')
