"""Typed ReplaceFace source/replacement roles and separate stored BODY/ASM proof."""
import struct

from decode_assembly import decode_assembly
from decode_body_properties import BODY,COLLECTION,decode_body_properties
from decode_body_bindings import decode_body_bindings
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_parameters import read_string
from decode_sketch import reference
from decode_mesh_contents import _require
from decode_owned_surface_selection import decode_owned_surface_selection

REPLACE='8BD31492-18F4-45C9-8512-D720CCFC2450'
FACE='5662F619-2281-4AD9-93DC-1FCFDA1062E7'
BODY_DESCRIPTOR='9716F783-676D-42E0-93F9-EBF273E7C035'
SCOPE=('Observed ReplaceFace distinct owned source-face and replacement face/body descriptors, historical '
       'Extrude/Patch BODY anchors, typed naming contexts and reciprocal stored BODY collection; initial '
       'same-asset ASM stored IDs qualified separately. Native target representation is retained; no '
       'persistent selected ASMface/API identity, source/result pairing, lifecycle or regeneration inferred.')


def resolve_replace_face_target(data,records,target_id,feature,known):
    """Pure opt-in target callback, reusing all canonical face/body selectors."""
    grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    def typed(identity,guid):
        rows=grouped.get(identity,[])
        _require(len(rows)==1 and rows[0].class_guid==guid,'ReplaceFace role typed reference missing/ambiguous/wrong class')
        record=rows[0];return record,data[record.body:record.end]
    fid=feature['object_id'];record,body=typed(fid,REPLACE)
    _require(record.start==feature['record_offset'] and body[:2]==bytes(2) and body[2] in (0,1)
             and struct.unpack_from('<I',body,3)[0]==1 and struct.unpack_from('<I',body,18)[0]==1
             and reference(body,7)==target_id,'ReplaceFace source/target header or feature identity differs')
    source_id=reference(body,22)
    _require(target_id!=source_id,'ReplaceFace source/target proxies alias')
    source=decode_owned_surface_selection(data,records,source_id,fid,face_recipe_kind='bounded_face_recipe_data')
    _require(source['kind']=='Face','ReplaceFace source must be an owned face')
    target=decode_owned_surface_selection(data,records,target_id,fid,face_recipe_kind='face_recipe_data')
    target_guid=FACE if target['kind']=='Face' else BODY_DESCRIPTOR
    target_identity=target['face'] if target['kind']=='Face' else target['descriptor']
    target_body_id=target_identity['native_body_object_id'];target_owner=target_identity['source_owner_object_id']
    typed(source['face']['source_owner_object_id'],'DD405BC2-D673-44F0-8833-5CB2A1C186C7')
    typed(target_owner,'BF77AE1A-E8F6-43AB-A325-A2C984AF1C6B')
    source_body_id=source['face']['native_body_object_id']
    _require(source_body_id!=target_body_id and len({source['face']['source_owner_object_id'],target_owner,fid})==3,
             'ReplaceFace source/target/feature historical roles alias')
    properties=decode_body_properties(data,records,decode_assembly(data,records,[]))
    props=[]
    for identity in (source_body_id,target_body_id):
        matches=[p for p in properties['bodies'] if p['object_id']==identity]
        _require(len(matches)==1,'ReplaceFace historical BODY reciprocal collection unresolved');props.append(matches[0])
    _require(props[0]['collection_object_id']==props[1]['collection_object_id'],'ReplaceFace historical roles have different collections')
    collection_id=props[0]['collection_object_id'];cr,collection=typed(collection_id,COLLECTION)
    cs=[c for c in properties['collections'] if c['object_id']==collection_id]
    _require(len(cs)==1 and len(cs[0]['body_object_ids'])==2 and set(cs[0]['body_object_ids'])=={source_body_id,target_body_id},'ReplaceFace current collection differs from distinct role BODY set')
    mapping_id=reference(collection,11+11*2+12);mr,mapping=typed(mapping_id,'74CA4562-59F8-4C97-8AD1-F8297C21F9AA')
    evidence=dict(feature_object_id=fid,feature_record_offset=record.start,source_selection_record_object_id=source_id,
        target_selection_record_object_id=target_id,target_descriptor_guid=target_guid,
        source_face_route=source,replacement_target_route=target,source_historical_native_body_object_id=source_body_id,
        replacement_historical_native_body_object_id=target_body_id,historical_body_properties=props,
        native_current_body_collection=cs[0],native_history_mapping_object_id=mapping_id,
        raw_role_prefix_hex=body[:33].hex(),stored_collection_payload_hex=collection.hex(),stored_mapping_payload_hex=mapping.hex(),scope=SCOPE)
    return target_guid,dict(kind={'Face':'BRepFace','Body':'BRepBody'}[target['kind']],native_body_object_id=target_body_id,
        native_evidence=evidence,representation_scope='Native face/body descriptor kind is explicit; requested and rolled API representations must be recorded independently',scope=SCOPE)


def qualify_replace_face_body_routes(data,records,member,members,evidence):
    """Revalidate role proof; map native BODY handles through the same stored asset."""
    matches=[r for r in records if r.is_primary and r.object_id==evidence['feature_object_id'] and r.class_guid==REPLACE]
    _require(len(matches)==1,'ReplaceFace late feature identity ambiguous');record=matches[0]
    _,target=resolve_replace_face_target(data,records,evidence['target_selection_record_object_id'],
        dict(object_id=record.object_id,record_offset=record.start),{})
    _require(target['native_evidence']==evidence,'ReplaceFace late role evidence differs from native revalidation')
    mr=[r for r in records if r.is_primary and r.object_id==evidence['native_history_mapping_object_id']]
    _require(len(mr)==1,'ReplaceFace stored mapping identity ambiguous');payload=data[mr[0].body:mr[0].end]
    count=struct.unpack_from('<I',payload,2)[0];filename,end=read_string(payload,6+16*count+12)
    _require(end==len(payload),'ReplaceFace history filename extent differs')
    blob=member.rsplit('/FusionDesignSegmentType1/',1)[0]+'/Breps.BlobParts/'+filename
    _require(blob in members,'ReplaceFace sameasset history blob absent')
    # The canonical mapping reader receives only actual blob member identities;
    # no ordered ASM root data is supplied, so it cannot generate ordinal candidates.
    bindings=decode_body_bindings(data,records,member,dict(streams=[dict(member=blob)]),dict(bodies=evidence['historical_body_properties']))
    rows=[m for m in bindings['decoded'] if m['mapping_record_object_id']==mr[0].object_id]
    _require(len(rows)==1 and rows[0]['owner_object_id']==evidence['native_current_body_collection']['object_id']
             and {b['native_body_object_id'] for b in rows[0]['bindings']}==set(evidence['native_current_body_collection']['body_object_ids']),
             'ReplaceFace canonical body mapping/current collection differs')
    mapping={k:rows[0][k] for k in ('mapping_record_object_id','owner_object_id','history_blob_member','body_count')}
    mapping['bindings']=[dict(stored_handle=b['stored_handle'],native_body_object_id=b['native_body_object_id']) for b in rows[0]['bindings']]
    identifiers=decode_body_asm_identifiers(data,records,member,members,dict(decoded=[mapping]))
    _require(len(identifiers['decoded'])==1 and not identifiers['unresolved'],'ReplaceFace sameasset native handle/ASM BODY identity unresolved')
    return dict(feature_object_id=record.object_id,native_role_evidence=evidence,native_history_mapping=mapping,
        stored_asm_body_identifiers=identifiers,selected_source_asm_face_id=None,selected_replacement_asm_face_id=None,
        native_API_body_assignment=None,source_to_result_pairing=None,scope=SCOPE)
