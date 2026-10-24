"""Captured fixed/moving parting-line Draft controls and typed source roles.

Common numeric bindings and owned face/edge recipe framing are reused from
strict Draft readers. The parting/fixed-edge lists establish serialized roles,
not persistent ASM topology or regenerated drafted geometry.
"""
import math
import struct
import uuid

from decode_draft import parse_draft_controls, make_draft_selection_readers
from decode_parameters import read_string
from decode_recipe_components import decode_counted_recipe
from decode_selection import native_origin_entities
from decode_sketch import reference

DRAFT='F4163A07-9E71-4C46-BD92-ACE5B5B40BED'
FACE_CONTEXT='C46D3EEB-40E1-43FA-83DC-9CB204335417'
EDGE_CONTEXT='50AEE8B4-9456-4DD7-847D-6F6C909BBB9D'
SCOPE='Observed fixed symmetric3/7degree and moving single-angle parting-line Draft, two face inputs/one edge parting line, moving two fixed edges, native XY pull; stored selections/controls only, exact persistent topology and draft regeneration unresolved'


def decode_parting_line_drafts(data,records,features,known=None):
    """Return decoded/unresolved/scope; success rows hold feature ID/name/settings."""
    records=list(records)
    result=dict(decoded=[],unresolved=[],scope=SCOPE)
    grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    named={f['object_id']:f for f in features}
    entities=native_origin_entities(data,records) if known is None else known
    for record in records:
        if not record.is_primary or record.class_guid!=DRAFT:continue
        body=data[record.body:record.end]
        if len(body)>=10 and struct.unpack_from('<II',body,2)==(3,1):continue
        try:
            feature=named.get(record.object_id);owner=record.object_id
            if (len(grouped.get(owner,[]))!=1 or feature is None or feature['class_guid']!=DRAFT
                    or feature['record_offset']!=record.start):
                raise ValueError('Parting Draft feature identity missing/ambiguous/stale')
            settings=parse_draft_controls(body,feature,allowed_header_fields=((3,2),(3,3)))
            moving=settings['stored_header_fields']==[3,3]
            if (settings['is_direction_flipped'] or settings['is_tangent_chain']
                    or settings['stored_angle_mode_code']!=(1 if moving else 3)
                    or not math.isfinite(settings['angle_one_radians']) or not 0<settings['angle_one_radians']<math.pi/2
                    or settings['stored_angle_one_radians']!=settings['stored_angle_two_radians']):
                raise ValueError('Unobserved parting Draft flags/angle mode/angle pair')
            readers=make_draft_selection_readers(data,records,feature,entities,
                allowed_recipe_kinds=('face_recipe_data','bounded_face_recipe_data','edge_recipe_data'),
                allowed_context_classes=(FACE_CONTEXT,EDGE_CONTEXT),recipe_decoder=decode_counted_recipe)
            typed,selection,counted=readers['typed'],readers['selection'],readers['counted']
            if moving:
                if body[54]!=0:raise ValueError('Unobserved moving Draft raw byte54')
                fixed_id,pull_id,parting_id=reference(body,55),reference(body,66),reference(body,77)
                input_ids,cursor=counted(body,88)
            else:
                if body[54:56]!=bytes(2):raise ValueError('Unobserved fixed-parting Draft separator bytes')
                fixed_id=None;pull_id,parting_id=reference(body,56),reference(body,67)
                input_ids,cursor=counted(body,78)
            if len(input_ids)!=1:raise ValueError('Parting Draft input selection group count must be one')
            if len(set([pull_id,parting_id,*input_ids]+([fixed_id] if moving else [])))!=(4 if moving else 3):
                raise ValueError('Parting Draft source roles alias the same proxy')
            inputs=selection(input_ids[0]);parting=selection(parting_id)
            fixed=selection(fixed_id) if moving else None;pull=selection(pull_id,True)
            if (inputs['descriptor_count']!=2 or parting['descriptor_count']!=1
                    or (moving and fixed['descriptor_count']!=2)):
                raise ValueError('Unobserved parting Draft face/line/fixed-edge counts')
            native=pull['native_selection']
            if (pull['descriptor_count']!=1 or native is None or native['entity']['kind']!='ConstructionPlane'
                    or native['entity']['name']!='XY' or native['entity']['origin_cm']!=[0.,0.,0.]
                    or native['entity']['normal']!=[0.,0.,1.]):
                raise ValueError('Only captured explicit native XY parting Draft pull geometry supported')
            pull['geometry_status']='Explicit reference to independently decoded native construction-plane geometry'
            descriptors=[]
            for role,item,kind,context in [('InputFaces',inputs,'Face',FACE_CONTEXT),('PartingLine',parting,'Edge',EDGE_CONTEXT)]+(
                    [('FixedEdges',fixed,'Edge',EDGE_CONTEXT)] if moving else []):
                for descriptor in item['descriptors']:
                    if descriptor['kind']!=kind or len(descriptor['context_record_object_ids'])!=1:
                        raise ValueError('Parting Draft descriptor recipe kind/context count disagrees with input role')
                    typed(descriptor['context_record_object_ids'][0],context)
                    _,raw=typed(descriptor['object_id'],'5662F619-2281-4AD9-93DC-1FCFDA1062E7')
                    if len(raw)!=276:raise ValueError('Unobserved parting Draft descriptor extent')
                    descriptors.append(descriptor)
            if len({d['object_id'] for d in descriptors})!=len(descriptors):
                raise ValueError('Parting Draft explicit face/edge descriptor roles overlap')
            if (len({d['body_anchor_object_id'] for d in descriptors})!=1
                    or len({d['native_body_object_id'] for d in descriptors})!=1):
                raise ValueError('Parting Draft source roles do not share one explicit historical native body anchor')
            nil,cursor=read_string(body,cursor)
            if nil!=str(uuid.UUID(int=0)) or body[cursor:cursor+3]!=bytes(3):
                raise ValueError('Parting Draft nil UUID/repeated dependency separator mismatch')
            repeated,cursor=counted(body,cursor+3)
            expected=[input_ids[0],*[d['object_id'] for d in inputs['descriptors']],parting_id,
                *[d['object_id'] for d in parting['descriptors']]]
            if moving:expected.extend([fixed_id,*[d['object_id'] for d in fixed['descriptors']]])
            expected.extend([pull_id,*[d['object_id'] for d in pull['descriptors']],
                settings['angle_binding_object_ids']['Angle1'],settings['angle_binding_object_ids']['Angle2']])
            if repeated!=expected:raise ValueError('Parting Draft repeated role/dependency references disagree')
            pre_label=struct.unpack_from('<I',body,cursor)[0];label,end=read_string(body,cursor+4)
            stored_index=struct.unpack_from('<Q',body,end)[0];name,tail=read_string(body,end+8)
            if (pre_label!=(10 if moving else 18) or label!='Draft' or stored_index!=feature['stored_index']
                    or name!=feature.get('name') or len(body)-tail!=66):
                raise ValueError('Parting Draft feature label/index/name/footer framing mismatch')
            settings.update(draft_type='PartingLine',parting_line_type='Moving' if moving else 'Fixed',
                draft_type_api_value=1,parting_line_type_api_value=1 if moving else 0,
                header_scope='Exact captured (3,2) fixed-parting versus (3,3) moving-parting layouts; first field/general versions not interpreted',
                angle_activity_scope='Angle1 controls captured single-angle definition; equal stored Angle2 retained independently',
                pull_geometry=pull,input_selections=[inputs],input_descriptor_count=2,
                parting_line_selection=parting,moving_fixed_edge_selection=fixed,
                moving_direction=None,moving_direction_status=('Only actual BothAngles getter2 was captured; no independently contrasted native direction discriminator mapped' if moving else 'Inactive for Fixed parting-line type'),
                is_chained=None,is_chained_status='Requested False in captures; native chaining field not identified and no independent public getter exists',
                stored_layout_byte54=body[54],stored_pre_label_word=pre_label,
                historical_body_anchor_object_id=descriptors[0]['body_anchor_object_id'],
                historical_native_body_object_id=descriptors[0]['native_body_object_id'],
                historical_source_owner_object_id=descriptors[0]['source_owner_object_id'],
                repeated_dependency_object_ids=repeated,
                geometry_status='Typed face/parting-edge/fixed-edge selection roles and historical body association decoded; geometry caches and persistent topology are not regenerated or matched by coordinates',
                unsupported_scope='General parting directions/chaining, unobserved modes, exact persistent selected face/edge identities and draft geometry reconstruction remain unresolved')
            result['decoded'].append(dict(feature_object_id=owner,kind='Draft',name=feature.get('name'),settings=settings))
        except (ValueError,KeyError,IndexError,struct.error,UnicodeError,TypeError) as error:
            result['unresolved'].append(dict(feature_object_id=record.object_id,class_guid=DRAFT,reason=str(error)))
    return result
