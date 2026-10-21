"""Observed SurfaceTrim tool-source identity, separate from selected-cell recipes."""
import struct

from decode_assembly import decode_assembly
from decode_body_properties import decode_body_properties
from decode_owned_surface_selection import decode_owned_surface_selection,FACE,BODY_DESCRIPTOR
from decode_selection import native_proxy_references
from decode_sketch import reference
from decode_mesh_contents import _require

TRIM='FF1741AE-E78B-4A5F-8418-751899E12F66'
SCOPE=('Observed singleton SurfaceTrim source-tool identity through typed owned selectors. Historical '
       'source provenance and component ownership remain separate from target cells and resulting geometry; '
       'selected-cell meaning, selected ASMface/API identity, lifecycle and regeneration unresolved.')


def resolve_surface_trim_source(data,records,tool_id,owner_id,features):
    """Pure source callback; common Trim header/target/cell codec stays independent."""
    grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    def typed(identity,guid):
        rows=grouped.get(identity,[])
        _require(len(rows)==1 and rows[0].class_guid==guid,'SurfaceTrim source typed identity missing/ambiguous/wrong class')
        record=rows[0];return record,data[record.body:record.end]
    feature,body=typed(owner_id,TRIM)
    _require(body[:2]==bytes(2) and len(body)>=55 and reference(body,17)==tool_id,
             'SurfaceTrim source operand differs from native feature field')
    proxy,payload=typed(tool_id,'2CA5A1CD-C99B-4C9B-91AF-57989148E841')
    ids,props=native_proxy_references(data,proxy)
    _require(not props and len(ids)==1 and reference(payload,len(payload)-11)==owner_id,'SurfaceTrim source owned singleton proxy differs')
    _require(ids[0] in grouped and len(grouped[ids[0]])==1,'SurfaceTrim source descriptor ambiguous')
    descriptor=grouped[ids[0]][0]
    _require(descriptor.class_guid in (FACE,BODY_DESCRIPTOR),'Unobserved SurfaceTrim source descriptor class')
    route=decode_owned_surface_selection(data,records,tool_id,owner_id,face_recipe_kind='face_recipe_data')
    identity=route['face'] if route['kind']=='Face' else route['descriptor'];native_body_id=identity['native_body_object_id']
    source_kind='BRepFace' if route['kind']=='Face' else 'BRepBody'
    typed(identity['source_owner_object_id'],'BF77AE1A-E8F6-43AB-A325-A2C984AF1C6B')
    properties=decode_body_properties(data,records,decode_assembly(data,records,[]))
    matches=[p for p in properties['bodies'] if p['object_id']==native_body_id]
    _require(len(matches)==1,'SurfaceTrim source BODY reciprocal ownership unresolved')
    evidence=dict(feature_object_id=owner_id,tool_selection_record_object_id=tool_id,tool_descriptor_object_ids=ids,
        source_kind=source_kind,source_route=route,historical_native_body_object_id=native_body_id,
        source_body_properties=matches[0],native_component_object_id=matches[0]['component_object_id'],
        native_feature_record_offset=feature.start,stored_tool_operand_hex=body[17:28].hex(),
        selected_asm_face_id=None,native_API_source_assignment=None,
        cell_selection_status='Source identity only; native Trim cell recipe and kept/removed region meaning unresolved',scope=SCOPE)
    return dict(selection_record_object_id=tool_id,entity=dict(kind=source_kind,native_body_object_id=native_body_id),
        native_source_evidence=evidence,scope=SCOPE)
