"""Plural cosmetic Thread source selections and separately qualified ASM BODY IDs."""
import struct

from decode_assembly import decode_assembly
from decode_body_properties import decode_body_properties,BODY,COLLECTION
from decode_body_selections import decode_body_selections
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_face_selections import resolve_native_faces
from decode_selection_context_recipes import decode_selection_context_recipes
from decode_mesh_contents import _require
from decode_parameters import read_string
from decode_sketch import reference

THREAD='584D9526-EF22-4F6F-9FE1-5FCF1F3CE575'
MAPPING='74CA4562-59F8-4C97-8AD1-F8297C21F9AA'
SCOPE=('Observed two separate owned Thread face proxies with singleton descriptors, bounded recipes, '
       'matching typed context namespaces and historical seed BODY anchors; reciprocal stored BODY collection '
       'and same-asset ASM stored-ID mapping qualified separately. No selected ASM face identity, API handle '
       'equivalence, source/result pairing, solved placement, lifecycle or regeneration inferred.')


def resolve_thread_multi_faces(data,records,body,feature,selection_cursor):
    """Pure opt-in plural Thread callback; exact two-source default remains strict."""
    return _resolve_thread_sources(data,records,body,feature,selection_cursor,expected_count=2,scope=SCOPE)


def _resolve_thread_sources(data,records,body,feature,selection_cursor,*,expected_count,scope):
    """Shared strict source frame, with independently observed singleton/plural counts."""
    _require(expected_count in (1,2),'Unobserved internal Thread source count')
    records=list(records);grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    def typed(identity,guid):
        rows=grouped.get(identity,[])
        _require(len(rows)==1 and rows[0].class_guid==guid,'Thread route typed reference missing/ambiguous/wrong class')
        r=rows[0];return r,data[r.body:r.end]
    identity=feature['object_id'];record,native=typed(identity,THREAD)
    _require(record.start==feature['record_offset'] and native==body,'Thread route feature/payload identity differs')
    count=struct.unpack_from('<I',body,selection_cursor)[0]
    _require(count==expected_count,('Only captured two-proxy Thread source layout supported' if expected_count==2 else 'Only captured singleton family Thread source layout supported'))
    ids=[reference(body,selection_cursor+4+11*i) for i in range(count)]
    _require(len(set(ids))==count,'Thread source proxy identities duplicate')
    end=selection_cursor+4+11*count
    selections=decode_body_selections(data,records)
    contexts=decode_selection_context_recipes(data,records,selections)
    rows=[];descriptor_ids=[];body_ids=[]
    for proxy_id in ids:
        proxy,payload=typed(proxy_id,'2CA5A1CD-C99B-4C9B-91AF-57989148E841')
        _require(len(payload)==105,'Unobserved plural Thread proxy extent')
        faces=resolve_native_faces(data,records,proxy_id,identity,selections)
        _require(not faces['attributes'] and len(faces['faces'])==1,'Thread proxy must own one unadorned face descriptor')
        face=faces['faces'][0];descriptor_id=face['descriptor_object_id']
        descriptor,descriptor_bytes=typed(descriptor_id,'5662F619-2281-4AD9-93DC-1FCFDA1062E7')
        matching=[c for c in contexts['contexts'] if c['descriptor_object_id']==descriptor_id and c['owner_object_id']==identity]
        _require(len(matching)==1 and len(descriptor_bytes)==276,'Thread face context/descriptor frame unresolved')
        context=matching[0]
        _require(context['native_body_object_id']==face['native_body_object_id']
                 and context['body_anchor_object_id']==face['body_anchor_object_id']
                 and context['descriptor_recipe']==face['recipe']
                 and context['optional_context_recipe_route'] is None
                 and face['recipe']['payload_kind']=='bounded_face_recipe_data'
                 and face['source_owner_object_id']!=identity,'Thread typed context/recipe/seed anchor disagrees')
        typed(face['source_owner_object_id'],'DD405BC2-D673-44F0-8833-5CB2A1C186C7')
        rows.append(dict(selection_record_object_id=proxy_id,face_selection=face,typed_context=context,
            stored_proxy_payload_hex=payload.hex(),stored_descriptor_payload_hex=descriptor_bytes.hex()))
        descriptor_ids.append(descriptor_id);body_ids.append(face['native_body_object_id'])
    _require(len(set(descriptor_ids))==count and len(set(body_ids))==count,'Thread distinct descriptors/historical bodies required')
    properties=decode_body_properties(data,records,decode_assembly(data,records,[]))
    props=[]
    for body_id in body_ids:
        matches=[p for p in properties['bodies'] if p['object_id']==body_id]
        _require(len(matches)==1,'Thread historical BODY reciprocal ownership unresolved');props.append(matches[0])
    collection_ids={p['collection_object_id'] for p in props}
    _require(len(collection_ids)==1,'Thread captured sources must share one typed BODY collection')
    collection_id=next(iter(collection_ids));collection_record,collection=typed(collection_id,COLLECTION)
    choices=[c for c in properties['collections'] if c['object_id']==collection_id]
    _require(len(choices)==1 and set(choices[0]['body_object_ids'])==set(body_ids)
             and len(choices[0]['body_object_ids'])==count,'Thread source/current collection membership differs')
    current=choices[0];typed(current['component_object_id'],'E03784ED-5E19-4E14-B9F2-3B07017018CD')
    middle=11+11*count
    _require(collection[middle]==1,'Thread BODY collection mapping marker differs')
    mapping_id=reference(collection,middle+12);mapping_record,payload=typed(mapping_id,MAPPING)
    _require(payload[:2]==bytes(2) and struct.unpack_from('<I',payload,2)[0]==count,'Thread history mapping prefix/count differs')
    entries=[struct.unpack_from('<QQ',payload,6+16*i) for i in range(count)]
    _require(len({h for h,_ in entries})==count and {i for _,i in entries}==set(body_ids),'Thread mapping handle/BODY identities duplicate or differ')
    after=6+16*count
    _require(reference(payload,after)==collection_id and payload[after+11]==0,'Thread history owner/filename separator differs')
    filename,cursor=read_string(payload,after+12)
    _require(cursor==len(payload) and filename.startswith('BREP.') and filename.endswith('.smbh')
             and '/' not in filename and '\\' not in filename,'Thread history filename extent/name differs')
    def ref(i):return b'\1'+struct.pack('<Q',i)+bytes(2)
    _require(struct.pack('<I',count)+b''.join(ref(i) for i in ids)==body[selection_cursor:end],'Thread full source list replay differs')
    _require(bytes(2)+struct.pack('<I',count)+b''.join(struct.pack('<QQ',*e) for e in entries)+ref(collection_id)+bytes(1)+struct.pack('<I',len(filename))+filename.encode('utf-16le')==payload,'Thread full native mapping replay differs')
    return dict(feature_object_id=identity,feature_record_offset=record.start,
        selection_start_offset=selection_cursor,selection_end_offset=end,selection_record_object_ids=ids,
        descriptor_object_ids=descriptor_ids,stored_selection_list_hex=body[selection_cursor:end].hex(),
        owned_face_source_routes=rows,historical_native_body_object_ids=body_ids,
        historical_source_body_properties=props,native_current_body_collection=current,
        native_current_body_object_ids=current['body_object_ids'],stored_history_filename=filename,
        native_history_mapping=dict(mapping_record_object_id=mapping_id,owner_object_id=collection_id,
            body_count=count,bindings=[dict(stored_handle=h,native_body_object_id=i) for h,i in entries]),
        layout=dict(collection_record_offset=collection_record.start,stored_collection_payload_hex=collection.hex(),
            mapping_record_offset=mapping_record.start,stored_mapping_payload_hex=payload.hex(),exact_selection_and_mapping_replay=True),
        scope=scope)


def qualify_thread_body_routes(data,records,member,members,evidence):
    """Revalidate plural source evidence, then join literal handles to ASM IDs."""
    return _qualify_thread_sources(data,records,member,members,evidence,resolver=resolve_thread_multi_faces,scope=SCOPE)


def _qualify_thread_sources(data,records,member,members,evidence,*,resolver,scope):
    """Shared late proof; caller-specific resolver reproduces all native evidence."""
    matches=[r for r in records if r.is_primary and r.object_id==evidence['feature_object_id'] and r.class_guid==THREAD]
    _require(len(matches)==1,'Thread late feature identity ambiguous');record=matches[0]
    fresh=resolver(data,records,data[record.body:record.end],
        dict(object_id=record.object_id,record_offset=record.start),evidence['selection_start_offset'])
    _require(fresh==evidence,'Thread late evidence differs from native revalidation')
    mapping={**evidence['native_history_mapping'],
        'history_blob_member':member.rsplit('/FusionDesignSegmentType1/',1)[0]+'/Breps.BlobParts/'+evidence['stored_history_filename']}
    _require(mapping['history_blob_member'] in members,'Thread same-asset history blob absent')
    identifiers=decode_body_asm_identifiers(data,records,member,members,{'decoded':[mapping]})
    _require(len(identifiers['decoded'])==1 and not identifiers['unresolved'],'Thread native handle/ASM stored BODY ID association unresolved')
    return dict(feature_object_id=record.object_id,native_selection_evidence=evidence,
        native_history_mapping=mapping,stored_asm_body_identifiers=identifiers,
        selected_asm_face_object_ids=None,native_API_face_assignment=None,source_to_result_pairing=None,scope=scope)
