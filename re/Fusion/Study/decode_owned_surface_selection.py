"""Observed singleton owned face/body selectors with optional typed contexts."""
import struct

from decode_body_selections import BODY,CONTEXT,decode_body_selections
from decode_brep_recipes import decode_recipe
from decode_face_selections import resolve_native_faces
from decode_selection_context_recipes import decode_selection_context_recipes
from decode_selection import native_proxy_references
from decode_parameters import read_string
from decode_sketch import reference
from decode_mesh_contents import _require

FACE='5662F619-2281-4AD9-93DC-1FCFDA1062E7'
BODY_DESCRIPTOR='9716F783-676D-42E0-93F9-EBF273E7C035'


def decode_owned_surface_selection(data,records,proxy_id,owner_id,*,expected_attributes=None,
                                   face_recipe_kind=None,body_context_counts=(1,)):
    """Reuse strict selectors; exact descriptor and context routes retain raw identities."""
    expected_attributes={} if expected_attributes is None else expected_attributes
    grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    def typed(identity,guid):
        rows=grouped.get(identity,[])
        _require(len(rows)==1 and rows[0].class_guid==guid,'ReplaceFace role typed reference missing/ambiguous/wrong class')
        record=rows[0];return record,data[record.body:record.end]
    primary={identity:rows[0] for identity,rows in grouped.items() if len(rows)==1}
    _,proxy=typed(proxy_id,'2CA5A1CD-C99B-4C9B-91AF-57989148E841')
    descriptor_ids,attributes=native_proxy_references(data,primary[proxy_id])
    _require(attributes==expected_attributes and len(descriptor_ids)==1 and reference(proxy,len(proxy)-11)==owner_id,'ReplaceFace target owned singleton proxy differs')
    descriptor_id=descriptor_ids[0]
    _require(descriptor_id in primary and primary[descriptor_id].class_guid in (FACE,BODY_DESCRIPTOR),'ReplaceFace target descriptor kind unsupported')
    selections=decode_body_selections(data,records)
    if primary[descriptor_id].class_guid==FACE:
        resolved=resolve_native_faces(data,records,proxy_id,owner_id,selections)
        _require(resolved['attributes']==expected_attributes and len(resolved['faces'])==1,'ReplaceFace captured singleton face route differs')
        face=resolved['faces'][0];contexts=decode_selection_context_recipes(data,records,selections)
        matches=[c for c in contexts['contexts'] if c['descriptor_object_id']==face['descriptor_object_id'] and c['owner_object_id']==owner_id]
        _require(len(matches)==1 and matches[0]['descriptor_recipe']==face['recipe'] and face['recipe']['payload_kind']==face_recipe_kind
                 and matches[0]['native_body_object_id']==face['native_body_object_id'],'ReplaceFace face recipe/context route unresolved')
        return dict(kind='Face',selection=resolved,face=face,typed_context=matches[0])
    candidates=[s for s in selections['selection_proxies'] if s['selection_record_object_id']==proxy_id and s['owner_object_id']==owner_id]
    ds=[d for d in selections['body_descriptors'] if d['object_id']==descriptor_id and d['owner_object_id']==owner_id]
    _require(len(candidates)==len(ds)==1 and candidates[0]['descriptor_object_ids']==descriptor_ids,'ReplaceFace owned body target unresolved')
    descriptor=ds[0];body_id=descriptor['native_body_object_id']
    recipe=decode_recipe(data,primary[descriptor['recipe_record_object_id']],primary)
    context_ids=descriptor['context_record_object_ids']
    _require(recipe['payload_kind']=='body_recipe_data' and len(context_ids) in body_context_counts,'ReplaceFace body target recipe/context count differs')
    typed_context=None
    if context_ids:
        _require(len(context_ids)==1,'Unobserved owned BODY context count')
        context_id=context_ids[0];_,context=typed(context_id,CONTEXT)
        _require(len(context)==181 and context[:2]==bytes(2) and context[6:10]==bytes(4),'ReplaceFace body naming context frame differs')
        namespace,cursor=read_string(context,10);entity,cursor=read_string(context,cursor)
        _require(cursor==162 and namespace==descriptor['namespace_text'] and entity==descriptor['entity_uuid_text']
                 and context[162:170]==struct.pack('<Q',2),'ReplaceFace body descriptor/context namespace differs')
        link_id=reference(context,170);_,link=typed(link_id,'CB4F4CC2-9D6F-48BA-9B1F-20C1992C9C9C')
        _require(len(link)==14 and link[:2]==bytes(2) and link[-1]==0,'ReplaceFace body naming link frame differs')
        leaf_id=reference(link,2);_,leaf=typed(leaf_id,'90055C05-546C-4EE7-B3C9-3DD922AD0C9C')
        _require(len(leaf)==10 and leaf[:2]==bytes(2),'ReplaceFace body context identity leaf differs')
        leaf_body_id=struct.unpack_from('<Q',leaf,2)[0];typed(leaf_body_id,BODY)
        _require(leaf_body_id==body_id,'ReplaceFace context identity leaf and anchored BODY disagree')
        typed_context=dict(context_object_id=context_id,stored_index_field=struct.unpack_from('<I',context,2)[0],
            namespace_text=namespace,entity_guid_text=entity,stored_context_payload_hex=context.hex(),
            body_identity_link_object_id=link_id,body_identity_leaf_object_id=leaf_id,
            leaf_native_body_object_id=leaf_body_id,stored_leaf_payload_hex=leaf.hex())
    return dict(kind='Body',selection=candidates[0],descriptor=descriptor,recipe=recipe,typed_context=typed_context)
