"""Modifying Thin Extrude target/owned-new-body lists and native ASM routes."""
import struct

from decode_assembly import decode_assembly
from decode_body_properties import decode_body_properties,BODY,COLLECTION
from decode_body_selections import decode_body_selections
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_mesh_contents import _require
from decode_parameters import read_string
from decode_sketch import reference

EXTRUDE='DD405BC2-D673-44F0-8833-5CB2A1C186C7'
MAPPING='74CA4562-59F8-4C97-8AD1-F8297C21F9AA'
SCOPE=('Observed modifying Thin Extrude owned target proxy/descriptor to historical seed anchor/native BODY, '
       'separate optional new owned BODY anchor, reciprocal native current collection and same-blob ASM stored '
       'BODY identifier mapping. Target/seed/new-result identities stay distinct; no source/result ordinal '
       'pairing, participant API applicability, current visibility, lifecycle or regeneration inferred.')


def resolve_thin_extrude_body_routes(data,records,body,feature,cursor):
    """Pure body-list callback; early controls/profile proof belongs to caller."""
    records=list(records);grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    def typed(identity,guid):
        rows=grouped.get(identity,[])
        _require(len(rows)==1 and rows[0].class_guid==guid,'Thin body route typed reference missing/ambiguous/wrong class')
        record=rows[0];return record,data[record.body:record.end]
    feature_id=feature['object_id'];record,native=typed(feature_id,EXTRUDE)
    _require(record.start==feature['record_offset'] and native==body,'Thin body route feature/payload identity differs')
    start=cursor
    _require(body[cursor:cursor+4]==bytes(4),'Thin body route new-anchor separator differs');cursor+=4
    count=struct.unpack_from('<I',body,cursor)[0];cursor+=4
    _require(count in (0,1),'Unobserved modifying Thin new-anchor count')
    new_ids=[reference(body,cursor+11*i) for i in range(count)];cursor+=11*count
    _require(body[cursor:cursor+4]==bytes(4),'Thin body route target-list separator differs');cursor+=4
    _require(struct.unpack_from('<I',body,cursor)[0]==1,'Only captured singleton Thin target selection supported');cursor+=4
    target_proxy_id=reference(body,cursor);cursor+=11
    selections=decode_body_selections(data,records)
    targets=[p for p in selections['selection_proxies'] if p['selection_record_object_id']==target_proxy_id
             and p['owner_object_id']==feature_id]
    _require(len(targets)==1 and len(targets[0]['descriptor_object_ids'])==1
             and len(targets[0]['native_body_object_ids'])==1,'Thin owned target proxy/descriptor ambiguous')
    target=targets[0];descriptor_id=target['descriptor_object_ids'][0]
    descriptors=[d for d in selections['body_descriptors'] if d['object_id']==descriptor_id and d['owner_object_id']==feature_id]
    _require(len(descriptors)==1,'Thin owned target descriptor unresolved')
    descriptor=descriptors[0];target_id=descriptor['native_body_object_id']
    _require(target['native_body_object_ids']==[target_id] and descriptor['source_owner_object_id']!=feature_id,
             'Thin target seed owner not distinct from modifying feature')
    owned=[a for a in selections['body_anchors'] if a['source_owner_object_id']==feature_id]
    _require({a['object_id'] for a in owned}==set(new_ids) and len(owned)==count,
             'Thin new-anchor list disagrees with owned typed anchors')
    new_anchors=[next(a for a in owned if a['object_id']==identity) for identity in new_ids]
    new_body_ids=[a['native_body_object_id'] for a in new_anchors]
    _require(len(set(new_body_ids+[target_id]))==count+1,'Thin new bodies alias target or each other')
    _,target_body=typed(target_id,BODY);collection_id=reference(target_body,len(target_body)-11)
    collection_record,collection=typed(collection_id,COLLECTION)
    assembly=decode_assembly(data,records,[])
    properties=decode_body_properties(data,records,assembly)
    choices=[c for c in properties['collections'] if c['object_id']==collection_id]
    _require(len(choices)==1,'Thin target reciprocal typed BODY collection unresolved')
    current=choices[0];body_ids=current['body_object_ids']
    _require(len(body_ids)==count+1 and set(body_ids)==set([target_id]+new_body_ids),
             'Thin current BODY collection differs from target plus separately owned new-body anchors')
    component_id=current['component_object_id']
    typed(component_id,'E03784ED-5E19-4E14-B9F2-3B07017018CD')
    middle=11+11*len(body_ids)
    _require(collection[middle]==1,'Thin BODY collection middle marker differs')
    mapping_id=reference(collection,middle+12)
    mapping_record,payload=typed(mapping_id,MAPPING)
    _require(payload[:2]==bytes(2) and struct.unpack_from('<I',payload,2)[0]==len(body_ids),
             'Thin BODY/history mapping prefix/count differs')
    entries=[struct.unpack_from('<QQ',payload,6+16*i) for i in range(len(body_ids))]
    _require(len({h for h,_ in entries})==len(body_ids) and {i for _,i in entries}==set(body_ids),
             'Thin native history handles/BODY IDs duplicate or differ from current collection')
    end_pairs=6+16*len(body_ids)
    _require(reference(payload,end_pairs)==collection_id and payload[end_pairs+11]==0,
             'Thin history mapping owner/filename separator differs')
    filename,end=read_string(payload,end_pairs+12)
    _require(end==len(payload) and filename.startswith('BREP.') and filename.endswith('.smbh')
             and '/' not in filename and '\\' not in filename,'Thin history filename extent/name differs')
    def ref(identity):return b'\1'+struct.pack('<Q',identity)+bytes(2)
    _require(bytes(4)+struct.pack('<I',count)+b''.join(ref(i) for i in new_ids)+bytes(4)+struct.pack('<I',1)+ref(target_proxy_id)==body[start:cursor],
             'Thin full body-list frame replay disagrees')
    _require(bytes(2)+struct.pack('<I',len(body_ids))+b''.join(struct.pack('<QQ',*entry) for entry in entries)+ref(collection_id)+bytes(1)+struct.pack('<I',len(filename))+filename.encode('utf-16le')==payload,
             'Thin full history mapping replay disagrees')
    return dict(feature_object_id=feature_id,feature_record_offset=record.start,
        body_list_start_offset=start,body_list_end_offset=cursor,stored_body_list_hex=body[start:cursor].hex(),
        new_result_anchor_object_ids=new_ids,new_result_body_anchors=new_anchors,new_result_native_body_object_ids=new_body_ids,
        target_body_selection_object_ids=[target_proxy_id],target_body_selection_proxy=target,
        target_body_descriptor=descriptor,target_native_body_object_ids=[target_id],
        target_seed_anchor_object_ids=[descriptor['body_anchor_object_id']],target_seed_owner_object_ids=[descriptor['source_owner_object_id']],
        native_current_body_collection=current,native_current_body_object_ids=body_ids,
        stored_history_filename=filename,native_history_mapping=dict(mapping_record_object_id=mapping_id,
            owner_object_id=collection_id,body_count=len(body_ids),
            bindings=[dict(stored_handle=h,native_body_object_id=i) for h,i in entries]),
        layout=dict(collection_record_offset=collection_record.start,stored_collection_payload_hex=collection.hex(),
            mapping_record_offset=mapping_record.start,stored_mapping_payload_hex=payload.hex(),
            exact_body_list_and_mapping_replay=True),
        native_identity_scope='Owned target selection references a distinct seed feature BODY anchor. Optional newly owned anchors and literal reciprocal current collection retained separately; no historical input replaced by result identity.',
        scope=SCOPE)


def qualify_thin_extrude_body_routes(data,records,member,members,body_list_evidence):
    """Qualify same-asset ASM IDs late, preserving independent early controls."""
    evidence=body_list_evidence;identity=evidence['feature_object_id']
    choices=[r for r in records if r.is_primary and r.object_id==identity and r.class_guid==EXTRUDE]
    _require(len(choices)==1,'Thin late route feature identity ambiguous')
    record=choices[0]
    fresh=resolve_thin_extrude_body_routes(data,records,data[record.body:record.end],
        dict(object_id=identity,record_offset=record.start),evidence['body_list_start_offset'])
    _require(fresh==evidence,'Thin late route evidence disagrees with independent native revalidation')
    mapping={**evidence['native_history_mapping'],
        'history_blob_member':member.split('/FusionDesignSegmentType1/')[0]+'/Breps.BlobParts/'+evidence['stored_history_filename']}
    _require(mapping['history_blob_member'] in members,'Thin explicit same-asset history blob absent')
    identifiers=decode_body_asm_identifiers(data,records,member,members,{'decoded':[mapping]})
    _require(len(identifiers['decoded'])==1 and not identifiers['unresolved'],
             'Thin same-blob native handle/ASM BODY identifier association unresolved')
    return dict(feature_object_id=identity,native_body_list_evidence=evidence,
        native_history_mapping=mapping,stored_asm_body_identifiers=identifiers,
        source_to_result_pairing=None,
        scope=SCOPE)
