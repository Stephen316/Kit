"""Observed straight-sketch Pipe Boolean controls and owned historical target.

Common dimensions, fractions and path parsing remain in decode_pipe. API Join
infers its target; the native owned body-selection list does not imply the user
explicitly supplied API participantBodies for that operation.
"""
import struct

from decode_body_selections import decode_body_selections
from decode_body_properties import decode_body_properties
from decode_pipe import decode_pipe
from decode_selection import native_proxy_references
from decode_sketch import reference

PIPE='73615646-8752-4EE6-AD02-0B90804B7CD7'
OPERATIONS={1:'Join',2:'Cut',3:'Intersect'}
SCOPE='Observed solid circular full-distance straight-sketch Pipe Join/Cut/Intersect common controls and one explicitly owned historical native target body; no Boolean regeneration, current-final body lifecycle or persistent topology inferred'


def resolve_pipe_operation_layout(body):
    if len(body)<111 or body[:2]!=bytes(2):raise ValueError('Pipe Boolean layout requires captured empty-attributes header')
    cursor=2
    code=struct.unpack_from('<I',body,cursor+1)[0]
    if code not in OPERATIONS:raise ValueError('Pipe Boolean operation code outside observed Join/Cut/Intersect')
    return cursor-6,OPERATIONS[code]


def decode_pipe_operation(data,records,feature,features,body_selections=None):
    groups={}
    for record in records:
        if record.is_primary:groups.setdefault(record.object_id,[]).append(record)
    def typed(identity,guid):
        rows=groups.get(identity,[])
        if len(rows)!=1 or rows[0].class_guid!=guid:raise ValueError('Pipe Boolean typed record missing/ambiguous/wrong class')
        record=rows[0];return record,data[record.body:record.end]
    if feature.get('kind')!='Pipe' or feature.get('class_guid')!=PIPE:raise ValueError('Pipe Boolean requires native Pipe feature')
    record,body=typed(feature['object_id'],PIPE)
    delta,operation=resolve_pipe_operation_layout(body)
    settings=decode_pipe(data,records,body,feature,features,layout_resolver=resolve_pipe_operation_layout)
    if (settings['is_hollow'] or settings['section_type']!='Circular' or settings['path'].get('kind')!='Line'
            or settings['path']['is_closed'] or settings['distance_one_fraction']!=1.):
        raise ValueError('Pipe Boolean outside observed solid circular full-distance single-Line family')
    # The body list follows common section controls, with offsets derived from
    # the validated native attribute prefix rather than patched source bytes.
    start=84+delta
    if body[start:start+16]!=bytes(16) or struct.unpack_from('<I',body,start+16)[0]!=1:
        raise ValueError('Pipe Boolean target body-list reserved/count fields unsupported')
    proxy_id=reference(body,start+20);proxy_record,proxy=typed(proxy_id,'2CA5A1CD-C99B-4C9B-91AF-57989148E841')
    descriptors,props=native_proxy_references(data,proxy_record)
    if len(proxy)!=105 or props or len(descriptors)!=1 or reference(proxy,94)!=feature['object_id']:
        raise ValueError('Pipe Boolean target proxy count/attributes/owner disagrees')
    descriptor_id=descriptors[0];_,native_descriptor=typed(descriptor_id,'9716F783-676D-42E0-93F9-EBF273E7C035')
    if reference(native_descriptor,len(native_descriptor)-11)!=feature['object_id']:
        raise ValueError('Pipe Boolean target descriptor owner differs from feature')
    selections=body_selections if body_selections is not None else decode_body_selections(data,records)
    selected=[d for d in selections['body_descriptors'] if d['object_id']==descriptor_id]
    if len(selected)!=1 or selected[0]['owner_object_id']!=feature['object_id'] or selected[0]['context_record_object_ids']:
        raise ValueError('Pipe Boolean target descriptor not decoded in captured root context')
    selected=selected[0]
    # Custom-name anchors are independently decoded; no assembly/component
    # ownership is supplied or claimed merely to retrieve the stored name.
    properties=decode_body_properties(data,records,{'components':[]})
    names=[p for p in properties['bodies'] if p['object_id']==selected['native_body_object_id']]
    name=names[0].get('name') if len(names)==1 else None
    target={'proxy_object_id':proxy_id,'descriptor_object_id':descriptor_id,
        'body_anchor_object_id':selected['body_anchor_object_id'],'native_body_object_id':selected['native_body_object_id'],
        'source_owner_object_id':selected['source_owner_object_id'],'stored_name':name,
        'name_scope':'Independent typed body-name anchor only; no assembly ownership inferred',
        'association':'Feature counted target list→owned proxy→owned typed body descriptor→typed body anchor→explicit native BODY',
        'identity_scope':'Historical native body identity; current/final result lifecycle and selected topology are separate'}
    return {'feature_object_id':feature['object_id'],'tool_settings':settings,'stored_operation_code':struct.unpack_from('<I',body,3)[0],
        'target_body':target,'API_participant_applicability':operation in ('Cut','Intersect'),
        'participant_scope':'Explicit API participantBodies applies to Cut/Intersect; Join native target list does not establish an explicit API participant request',
        'layout':{'empty_attributes_header_hex':body[:2].hex(),'common_offset_delta':delta,'target_list_start_offset':start,
            'target_list_hex':body[start:start+31].hex(),'offset_scope':'Relative to native feature body; exact original bytes retained'},'scope':SCOPE}


def decode_pipe_operations(data,records,features):
    decoded,unresolved=[],[]
    for feature in features:
        if feature.get('kind')!='Pipe' or feature.get('class_guid')!=PIPE:continue
        rows=[r for r in records if r.is_primary and r.object_id==feature['object_id']]
        if len(rows)!=1:continue
        body=data[rows[0].body:rows[0].end]
        if body[:2]!=bytes(2):continue
        if len(body)>=7 and struct.unpack_from('<I',body,3)[0]==4:continue
        try:decoded.append(decode_pipe_operation(data,records,feature,features))
        except (ValueError,KeyError,IndexError,TypeError,struct.error) as error:
            unresolved.append({'feature_object_id':feature['object_id'],'reason':str(error)})
    return {'decoded':decoded,'unresolved':unresolved,'scope':SCOPE}
