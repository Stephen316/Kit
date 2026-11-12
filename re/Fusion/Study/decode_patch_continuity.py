"""Observed BRep Patch continuity controls and owned boundary/result provenance.

The common surface-tool parser owns prefix/operation/count validation. Only the
contrasted per-edge continuity0/1/2 has API meaning here. Weight/group/flip-like
fields retain their stored bytes without extending single-value coincidences.
"""
import math
import struct
import uuid

from decode_body_selections import decode_body_selections
from decode_surface_tools import decode_surface_tool
from decode_brep_recipes import decode_recipe
from decode_parameters import read_string
from decode_sketch import reference

PATCH='BF77AE1A-E8F6-43AB-A325-A2C984AF1C6B'
CONTROL='7A1DDA31-F6C4-42F6-8282-8654B2085F40'
CONTINUITIES={0:'Connected',1:'Tangent',2:'Curvature'}
SCOPE='Captured singleton BRep edge-recipe Patch NewBody continuity0/1/2 with explicit historical body and result anchors; rawscalar/group/flip semantics, exact ASM edge, surface continuity solving and regeneration unresolved'


def decode_patch_boundary(data,records,body,feature,definitions,selection,*,features):
    grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    def typed(identity,guid):
        rows=grouped.get(identity,[])
        if len(rows)!=1 or rows[0].class_guid!=guid:raise ValueError('BRep Patch typed reference missing/ambiguous/wrong class')
        record=rows[0];return record,data[record.body:record.end]
    if body[11]!=0:raise ValueError('Uncaptured BRep Patch raw group/header field')
    if len(definitions)!=1:raise ValueError('Only captured singleton BRep Patch boundary definition supported')
    identity=definitions[0];record,control=typed(identity,CONTROL)
    if (len(control)!=56 or control[:3]!=bytes(3) or struct.unpack_from('<I',control,7)[0]!=2
            or control[30:33]!=b'\1\0\0' or control[44]!=0 or reference(control,45)!=feature['object_id']):
        raise ValueError('Unobserved BRep Patch control framing/owner')
    code=struct.unpack_from('<I',control,3)[0]
    scalar=struct.unpack_from('<d',control,11)[0]
    if code not in CONTINUITIES or not math.isfinite(scalar) or scalar!=.5:
        raise ValueError('BRep Patch continuity/scalar outside captured contrasts')
    cache_id=reference(control,33);_,cache=typed(cache_id,'6CCF41D5-40BE-48ED-A834-18F3EAED6C57')
    if len(cache)!=39 or cache[:12]!=bytes(12) or reference(cache,12)!=identity or cache[31:]!=bytes(8):
        raise ValueError('BRep Patch control bookkeeping backlink disagrees')
    proxy_id=reference(control,19);selected,props=selection(proxy_id)
    if props or selected['stored_descriptor_count']!=1:raise ValueError('BRep Patch boundary proxy attributes/count unsupported')
    descriptor_id=selected['descriptor_object_ids'][0]
    _,descriptor=typed(descriptor_id,'5662F619-2281-4AD9-93DC-1FCFDA1062E7')
    if (len(descriptor)!=276 or descriptor[:4]!=bytes(4) or struct.unpack_from('<I',descriptor,15)[0]!=1
            or reference(descriptor,265)!=feature['object_id']):
        raise ValueError('BRep Patch edge descriptor count/owner framing unsupported')
    recipe_record,_=typed(reference(descriptor,4),'7ACC2A03-0261-4879-A14A-A93D661A5BDC')
    primary={identity:rows[0] for identity,rows in grouped.items() if len(rows)==1}
    recipe=decode_recipe(data,recipe_record,primary)
    if recipe['payload_kind']!='edge_recipe_data':raise ValueError('BRep Patch boundary requires explicit edge recipe')
    namespace,cursor=read_string(descriptor,19);entity_uuid,cursor=read_string(descriptor,cursor)
    if len(namespace)!=36 or len(entity_uuid)!=36:raise ValueError('BRep Patch source UUID lengths unsupported')
    uuid.UUID(namespace);uuid.UUID(entity_uuid)
    if cursor!=171 or descriptor[cursor:cursor+12]!=struct.pack('<QI',2,1):
        raise ValueError('BRep Patch source context list framing unsupported')
    context_id=reference(descriptor,cursor+12)
    _,context=typed(context_id,'B0B3FA59-C374-444F-B424-24AA5DE41645')
    if len(context)!=103:raise ValueError('BRep Patch source cache extent outside captured framing')
    if struct.unpack_from('<I',descriptor,cursor+23)[0]!=1:
        raise ValueError('BRep Patch source historical body anchor count unsupported')
    source_anchor_id=reference(descriptor,cursor+27)
    typed(source_anchor_id,'D26351F0-5940-4D23-AA20-2C35475A6D9E')
    source_anchors=[a for a in decode_body_selections(data,records)['body_anchors'] if a['object_id']==source_anchor_id]
    if len(source_anchors)!=1:raise ValueError('BRep Patch historical source body anchor unresolved')
    source_anchor=source_anchors[0]
    if source_anchor['source_owner_object_id']==feature['object_id']:
        raise ValueError('BRep Patch source self-references its own result feature')
    typed(source_anchor['source_owner_object_id'],PATCH)
    source={'kind':'BRepEdgeRecipe','selection_record_object_id':proxy_id,'descriptor_object_id':descriptor_id,
        'recipe':recipe,'body_anchor_object_id':source_anchor_id,'native_body_object_id':source_anchor['native_body_object_id'],
        'source_owner_object_id':source_anchor['source_owner_object_id'],'namespace_text':namespace,'entity_guid_text':entity_uuid,
        'context_record_object_id':context_id,'context_class_guid':'B0B3FA59-C374-444F-B424-24AA5DE41645',
        'context_payload_hex':context.hex(),'context_scope':'Referenced typed103-byte cache retained literally; geometry, native closure and parameter/traversal meanings not inferred',
        'identity_scope':'Explicit owned edge recipe and typed historical native BODY; exact selected ASM edge and persistent topology unresolved'}
    # These reserved/output fields are exact native framing, not a manufactured
    # sketch-profile payload or a result selected by matching its geometry.
    if body[36:60]!=bytes(24) or body[71:75]!=bytes(4) or struct.unpack_from('<I',body,75)[0]!=1:
        raise ValueError('Unobserved BRep Patch output/separator framing')
    bookkeeping_id=reference(body,60);_,bookkeeping=typed(bookkeeping_id,'E17B013D-E8F7-45B2-9DFA-D31CD2ECFB2D')
    if (len(bookkeeping)!=81 or bookkeeping[:2]!=bytes(2)
            or reference(bookkeeping,2)!=feature['object_id'] or reference(bookkeeping,70)!=feature['object_id']):
        raise ValueError('BRep Patch feature bookkeeping owner copies disagree')
    result_anchor_id=reference(body,79)
    _,anchor_payload=typed(result_anchor_id,'D26351F0-5940-4D23-AA20-2C35475A6D9E')
    anchors=[a for a in decode_body_selections(data,records)['body_anchors'] if a['object_id']==result_anchor_id]
    if (len(anchors)!=1 or anchors[0]['source_owner_object_id']!=feature['object_id']
            or len(anchor_payload)!=102 or reference(anchor_payload,91)!=feature['object_id']):
        raise ValueError('BRep Patch result anchor is not owned by feature')
    return {'boundary_input_kind':'BRepEdgeRecipe','boundary_selection':selected,'boundary_curve_count':1,
        'boundary_sources':[source],
        'boundary_controls':[{'definition_record_object_id':identity,'stored_continuity_code':code,'continuity':CONTINUITIES[code],
            'boundary_selection_record_object_id':proxy_id,'stored_scalar_at_11':scalar,
            'scalar_scope':'Storedfloat64.5 agrees actual API weight in these captures only; other weights unverified and not admitted',
            'stored_prefix_hex':control[:3].hex(),'stored_field_at_7':struct.unpack_from('<I',control,7)[0],
            'stored_flags_30_to_32_hex':control[30:33].hex(),'stored_flag_at_44':control[44],
            'flags_scope':'Uncontrasted raw fields retained without assigning flip/direction semantics',
            'control_bookkeeping_object_id':cache_id,'stored_bookkeeping_timestamp_hex':cache[23:31].hex(),
            'control_payload_hex':control.hex()}],
        'feature_bookkeeping_object_id':bookkeeping_id,'stored_group_field_at_11':body[11],
        'group_status':'Captured setContinuity returns isGroupEdgesFalse; this raw header field has no contrasted True BRep mapping',
        'continuity_status':'Actual BRep getter continuity0/1/2 matches typed per-edge definition field; exact surface continuity construction remains unresolved',
        'result_body_anchors':[{'body_anchor_object_id':result_anchor_id,'native_body_object_id':anchors[0]['native_body_object_id'],
            'source_owner_object_id':anchors[0]['source_owner_object_id'],'identity_scope':'Explicit feature-owned native BODY anchor, no current/final visibility claim'}],
        'geometry_status':'Owned edge recipe/historical body and result provenance only; exact boundary curve/ASM edge and patch surface regeneration unresolved'}


def decode_patch_continuity(data,records,features):
    decoded,unresolved=[],[]
    for feature in features:
        if feature.get('kind')!='SurfacePatch' or feature.get('class_guid')!=PATCH:continue
        matches=[r for r in records if r.is_primary and r.object_id==feature['object_id']]
        if len(matches)!=1:continue
        body=data[matches[0].body:matches[0].end]
        if len(body)<21 or struct.unpack_from('<I',body,17)[0]!=1:continue
        try:
            def resolver(data,records,body,feature,definitions,selection):
                return decode_patch_boundary(data,records,body,feature,definitions,selection,features=features)
            settings=decode_surface_tool(data,records,body,feature,patch_boundary_resolver=resolver)
            decoded.append({'feature_object_id':feature['object_id'],'settings':settings})
        except (ValueError,KeyError,IndexError,TypeError,struct.error,UnicodeError) as error:
            unresolved.append({'feature_object_id':feature['object_id'],'reason':str(error)})
    return {'decoded':decoded,'unresolved':unresolved,'scope':SCOPE}
