"""SplitBody sheet tool, historical source and separately owned new BODY routes."""
import struct

from decode_assembly import decode_assembly
from decode_body_properties import COLLECTION,decode_body_properties
from decode_body_selections import decode_body_selections
from decode_body_bindings import decode_body_bindings
from decode_body_asm_identifiers import decode_body_asm_identifiers
from decode_owned_surface_selection import decode_owned_surface_selection
from decode_parameters import read_string
from decode_sketch import reference
from decode_mesh_contents import _require

SPLIT='65CA3206-E33A-471E-8E40-2C72B57C6181'
SCOPE=('Observed owned SplitBody sheet face/body tool and historical source BODY selectors; explicit '
       'per-target newly owned BODY anchor and reciprocal stored collection retain source, tool and new '
       'BODY identities separately. Same-asset initial ASM stored-ID mapping qualified late. No API body '
       'or selected-face identity, source/result ordinal pairing, lifecycle, solver or regeneration inferred.')


def resolve_split_body_sheet_tool(data,records,tool_id,feature,known):
    """Pure common Split tool callback; native roles are independent of API shape."""
    grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    def typed(identity,guid):
        rows=grouped.get(identity,[])
        _require(len(rows)==1 and rows[0].class_guid==guid,'Split sheet typed reference missing/ambiguous/wrong class')
        record=rows[0];return record,data[record.body:record.end]
    fid=feature['object_id'];record,body=typed(fid,SPLIT)
    _require(record.start==feature['record_offset'] and body[:6]==bytes.fromhex('000100000000') and body[6] in (0,1)
             and struct.unpack_from('<I',body,7)[0]==1 and body[20]==0
             and struct.unpack_from('<I',body,30)[0]==1 and reference(body,34)==tool_id
             and body[45:49]==bytes(4) and struct.unpack_from('<I',body,49)[0]==1,
             'Split sheet common tool/per-target prefix differs')
    flag=struct.unpack_from('<Q',body,22)[0];definition_id=reference(body,11)
    definition_record,definition=typed(definition_id,'2E3AC990-483D-4A55-8662-C064B976A957')
    _require(len(definition)==58 and definition[:40]==bytes.fromhex('00000000000000000000000000000000000000000300000000000000000000000000000000000100')
             and reference(definition,40)==fid and definition[51:]==bytes(7),
             'Split sheet definition framing/owner backlink differs')
    new_anchor_id=reference(body,53)
    _require(body[64:72]==bytes.fromhex('0000000001000000'),'Split sheet source selection prefix differs')
    source_id=reference(body,72)
    _require(tool_id!=source_id,'Split sheet tool/source proxies alias')
    tool=decode_owned_surface_selection(data,records,tool_id,fid,
        expected_attributes={'DcFeatureOperationIdFlag':flag},face_recipe_kind='face_recipe_data')
    source=decode_owned_surface_selection(data,records,source_id,fid,body_context_counts=(0,))
    _require(source['kind']=='Body','Split sheet source must be the captured body descriptor')
    source_body_id=source['descriptor']['native_body_object_id'];source_owner=source['descriptor']['source_owner_object_id']
    tool_identity=tool['face'] if tool['kind']=='Face' else tool['descriptor'];tool_body_id=tool_identity['native_body_object_id'];tool_owner=tool_identity['source_owner_object_id']
    typed(source_owner,'DD405BC2-D673-44F0-8833-5CB2A1C186C7');typed(tool_owner,'BF77AE1A-E8F6-43AB-A325-A2C984AF1C6B')
    _require(len({fid,source_owner,tool_owner})==3 and source_body_id!=tool_body_id,'Split sheet historical role owners/bodies alias')
    selections=decode_body_selections(data,records)
    owned=[a for a in selections['body_anchors'] if a['source_owner_object_id']==fid]
    _require(len(owned)==1 and owned[0]['object_id']==new_anchor_id,'Split sheet per-target list differs from uniquely owned new anchor')
    new_body_id=owned[0]['native_body_object_id']
    _require(new_body_id not in (source_body_id,tool_body_id),'Split newly owned BODY aliases historical role')
    properties=decode_body_properties(data,records,decode_assembly(data,records,[]));props=[]
    for identity in (source_body_id,tool_body_id,new_body_id):
        matches=[p for p in properties['bodies'] if p['object_id']==identity]
        _require(len(matches)==1,'Split role/current BODY reciprocal ownership unresolved');props.append(matches[0])
    _require(len({p['collection_object_id'] for p in props})==1,'Split stored role/current collections differ')
    collection_id=props[0]['collection_object_id'];cr,collection=typed(collection_id,COLLECTION)
    cs=[c for c in properties['collections'] if c['object_id']==collection_id]
    _require(len(cs)==1 and len(cs[0]['body_object_ids'])==3 and set(cs[0]['body_object_ids'])=={source_body_id,tool_body_id,new_body_id},
             'Split current3 BODY collection differs from source/tool/new-owned identities')
    mapping_id=reference(collection,11+11*3+12);_,mapping=typed(mapping_id,'74CA4562-59F8-4C97-8AD1-F8297C21F9AA')
    evidence=dict(feature_object_id=fid,feature_record_offset=record.start,
        tool_selection_record_object_id=tool_id,source_selection_record_object_id=source_id,
        tool_route=tool,source_body_route=source,source_historical_native_body_object_id=source_body_id,
        tool_historical_native_body_object_id=tool_body_id,per_target_record_object_ids=[new_anchor_id],
        newly_owned_result_anchors=owned,newly_owned_native_body_object_ids=[new_body_id],
        historical_and_current_body_properties=props,native_current_body_collection=cs[0],
        native_history_mapping_object_id=mapping_id,stored_role_prefix_hex=body[:83].hex(),
        definition_record_object_id=definition_id,stored_definition_payload_hex=definition.hex(),
        stored_collection_payload_hex=collection.hex(),stored_mapping_payload_hex=mapping.hex(),scope=SCOPE)
    return dict(entity=dict(kind='BRepFace' if tool['kind']=='Face' else 'BRepBody',native_body_object_id=tool_body_id),
        native_evidence=evidence,representation_scope='Stored face/body descriptor kind retained independently of requested and rolled API representation',scope=SCOPE)


def qualify_split_body_sheet_routes(data,records,member,members,evidence):
    """Late stored native BODY handle proof; no source/result ordering assignment."""
    matches=[r for r in records if r.is_primary and r.object_id==evidence['feature_object_id'] and r.class_guid==SPLIT]
    _require(len(matches)==1,'Split sheet late feature identity ambiguous');record=matches[0]
    tool=resolve_split_body_sheet_tool(data,records,evidence['tool_selection_record_object_id'],
        dict(object_id=record.object_id,record_offset=record.start),{})
    _require(tool['native_evidence']==evidence,'Split sheet late evidence differs from independent native revalidation')
    mr=[r for r in records if r.is_primary and r.object_id==evidence['native_history_mapping_object_id']]
    _require(len(mr)==1,'Split sheet native mapping identity ambiguous');payload=data[mr[0].body:mr[0].end]
    count=struct.unpack_from('<I',payload,2)[0];filename,end=read_string(payload,6+16*count+12)
    _require(end==len(payload),'Split sheet mapping filename extent differs')
    blob=member.rsplit('/FusionDesignSegmentType1/',1)[0]+'/Breps.BlobParts/'+filename
    _require(blob in members,'Split sheet sameasset history blob absent')
    mappings=decode_body_bindings(data,records,member,dict(streams=[dict(member=blob)]),dict(bodies=evidence['historical_and_current_body_properties']))
    rows=[m for m in mappings['decoded'] if m['mapping_record_object_id']==mr[0].object_id]
    _require(len(rows)==1 and rows[0]['owner_object_id']==evidence['native_current_body_collection']['object_id']
             and {b['native_body_object_id'] for b in rows[0]['bindings']}==set(evidence['native_current_body_collection']['body_object_ids']),
             'Split sheet canonical mapping/current BODY collection differs')
    mapping={k:rows[0][k] for k in ('mapping_record_object_id','owner_object_id','history_blob_member','body_count')}
    mapping['bindings']=[dict(stored_handle=b['stored_handle'],native_body_object_id=b['native_body_object_id']) for b in rows[0]['bindings']]
    identifiers=decode_body_asm_identifiers(data,records,member,members,dict(decoded=[mapping]))
    _require(len(identifiers['decoded'])==1 and not identifiers['unresolved'],'Split sheet explicit native handles/ASM BODY IDs unresolved')
    return dict(feature_object_id=record.object_id,native_role_evidence=evidence,native_history_mapping=mapping,
        stored_asm_body_identifiers=identifiers,selected_tool_asm_face_id=None,native_API_body_assignment=None,
        source_to_result_pairing=None,scope=SCOPE)
