"""Observed MeshReduce controls, typed input mesh and separately stored assets.

Requested Face Count/Proportion/MaximumDeviation values are controls, not proof
that an algorithm achieved a target or satisfied a geometric deviation bound. Native mesh ownership and current asset selection are taken
from the common strict mesh reader; invariant packed prefix bytes are not links.
"""
import math
import lzma
import struct
import uuid

from decode_mesh_geometry_variants import decode_mesh_asset,decode_mesh_contents_variants,native_layout
from decode_mesh_contents import decode_mesh_contents,MESH,MESH_FEATURE
from decode_timeline import feature_state
from decode_mesh_selections import decode_mesh_selection
from decode_parameters import decode_stream,read_string
from decode_sketch import reference

REDUCE='BE693D4C-741E-4794-A93E-5BFED71E9E13'
FLOAT_BINDING='D91D429C-1BB5-4640-B49F-69AF14F463E9'
INTEGER_BINDING='A085449A-5144-4B2B-B455-7F7035A40559'
PARAMETER='7A6A3D31-BE74-4E19-9115-20642944C2E4'
DEVIATION_SCOPE='Observed MaximumDeviation target0 with literal Adaptive0/Uniform1 method controls, positive finite owned Tolerance parameter, typed current/additional asset routes; executed algorithm, deviation attainment, additional asset lifecycle and regeneration unresolved'
SCOPE='Observed Adaptive/Uniform FaceCount6 and Adaptive Proportion real50 unitless native controls, owned input mesh selection and typed current/additional asset references; counts/coordinates are stored caches, no physical reduction, historical state or mesh regeneration claim'


def _triangles(geometry):
    points=geometry['stored_node_coordinates_float32'];indices=geometry['triangle_node_indices']
    return sorted(tuple(sorted(tuple(points[indices[start+i]]) for i in range(3))) for start in range(0,len(indices),3))


def decode_mesh_reduce(data,records,features,member,members,mesh_contents=None):
    """Return decoded/unresolved/scope; success rows feature_object_id/name/settings."""
    records=list(records);candidates=[r for r in records if r.is_primary and r.class_guid==REDUCE]
    result=dict(decoded=[],unresolved=[],scope=SCOPE)
    if not candidates:return result
    grouped={}
    for record in records:
        if record.is_primary:grouped.setdefault(record.object_id,[]).append(record)
    def typed(identity,guid):
        rows=grouped.get(identity,[])
        if len(rows)!=1 or rows[0].class_guid!=guid:raise ValueError('MeshReduce typed reference missing/ambiguous/wrong class')
        record=rows[0];return record,data[record.body:record.end]
    named={f['object_id']:f for f in features}
    parameters,_=decode_stream(data,records)
    meshes=mesh_contents if mesh_contents is not None else decode_mesh_contents_variants(data,records,member,members)
    for record in candidates:
        try:
            typed(record.object_id,REDUCE);feature=named.get(record.object_id);owner=record.object_id
            if feature is None or feature['class_guid']!=REDUCE or feature['record_offset']!=record.start:
                raise ValueError('MeshReduce feature metadata absent/stale')
            body=data[record.body:record.end]
            if (body[:2]!=bytes(2) or body[17]!=0 or body[66:70]!=bytes(4) or body[81]!=0):
                raise ValueError('Unobserved MeshReduce native feature prefix/separators')
            method,target=struct.unpack_from('<I',body,13)[0],struct.unpack_from('<I',body,29)[0]
            if (method,target) not in((0,2),(1,2),(0,1),(0,0),(1,0)):
                raise ValueError('Unobserved MeshReduce method/target combination')
            deviation=target==0
            if deviation:
                result['scope']=DEVIATION_SCOPE
                result.setdefault('partial',[])
            binding_ids={'Tolerance':reference(body,2),'Proportion':reference(body,18),'Face Count':reference(body,33)}
            if len(set(binding_ids.values()))!=3:raise ValueError('MeshReduce scalar roles share a binding')
            scalar_rows={}
            for role,binding_id in binding_ids.items():
                integer=role=='Face Count';binding,_=typed(binding_id,INTEGER_BINDING if integer else FLOAT_BINDING)
                payload=data[binding.body:binding.end]
                if (len(payload)!=(82 if integer else 85) or payload[:6]!=bytes.fromhex('010100000001')
                        or reference(payload,5)!=owner or reference(payload,len(payload)-11)!=owner
                        or reference(payload,45 if integer else 48)!=owner):
                    raise ValueError('MeshReduce scalar binding owner/framing mismatch: '+role)
                parameter_id=reference(payload,26 if integer else 29);parameter_record,_=typed(parameter_id,PARAMETER)
                raw=struct.unpack_from('<I',payload,22)[0] if integer else struct.unpack_from('<d',payload,21)[0]
                if integer and payload[21]!=1:raise ValueError('MeshReduce Face Count tagged integer marker mismatch')
                matches=[p for p in parameters if p['role']==role and p.get('declared_binding_object_id')==binding_id
                    and parameter_record.body<=p['role_offset']<parameter_record.end]
                attached=[p for p in feature['parameters'] if p.get('binding_object_id')==binding_id and p['role']==role]
                if (len(matches)!=1 or len(attached)!=1 or matches[0]['raw_float64']!=raw
                        or attached[0]['raw_float64']!=raw or attached[0].get('parameter_object_id')!=parameter_id
                        or not math.isfinite(raw)):
                    raise ValueError('MeshReduce role/parameter/binding numeric copies disagree: '+role)
                scalar_rows[role]=dict(binding_object_id=binding_id,parameter_object_id=parameter_id,
                    stored_value=raw,display_units=matches[0]['display_units'],parameter_name=matches[0]['parameter_name'],
                    value_representation='tagged_uint32' if integer else 'float64',
                    is_active=role==('Face Count' if target==2 else 'Tolerance' if deviation else 'Proportion'))
            values={role:row['stored_value'] for role,row in scalar_rows.items()}
            if deviation:
                if (values['Tolerance']<=0 or scalar_rows['Tolerance']['display_units']!='mm'
                        or values['Proportion']!=0 or values['Face Count']!=0
                        or scalar_rows['Proportion']['display_units']!='' or scalar_rows['Face Count']['display_units']!=''):
                    raise ValueError('Unsupported MaximumDeviation positive Tolerance/inactive scalar values or units')
            elif (values['Tolerance']!=0 or (target==2 and (values['Face Count']!=6 or values['Proportion']!=0))
                    or (target==1 and (values['Proportion']!=50.0 or values['Face Count']!=0))
                    or scalar_rows['Proportion']['display_units']!='' or scalar_rows['Face Count']['display_units']!=''):
                raise ValueError('Uncaptured MeshReduce active/inactive scalar values or units')
            current_asset_id,additional_asset_id=reference(body,44),reference(body,55)
            if current_asset_id==additional_asset_id:raise ValueError('MeshReduce two stored asset references unexpectedly alias')
            selection_id=reference(body,70);selection=decode_mesh_selection(data,records,selection_id,owner)
            matching=[m for m in meshes['decoded'] if m['mesh_object_id']==selection['mesh_object_id']]
            if deviation and not matching:
                metadata=decode_mesh_contents(data,records,member,members,native_layout_decoder=native_layout,metadata_only=True)
                matching=[m for m in metadata['decoded'] if m['mesh_object_id']==selection['mesh_object_id']]
            if len(matching)!=1:raise ValueError('MeshReduce selected native mesh lacks one qualified current asset/owner route')
            mesh=matching[0]
            if current_asset_id!=mesh['asset_object_id']:
                raise ValueError('MeshReduce first stored asset differs from selected native mesh current asset')
            geometry_errors=[]
            try:
                current_asset=decode_mesh_asset(data,records,current_asset_id,member,members)
            except (ValueError,IndexError,struct.error,lzma.LZMAError) as error:
                if not deviation:raise
                current_asset=decode_mesh_asset(data,records,current_asset_id,member,members,metadata_only=True)
                geometry_errors.append(dict(asset_object_id=current_asset_id,reason=str(error),
                    scope='Strict current geometry failed; typed header/asset and active controls remain partial evidence'))
            if deviation and mesh['geometry'] is None and not geometry_errors:
                geometry_errors.append(dict(asset_object_id=current_asset_id,reason='Current native mesh geometry not independently qualified',
                    scope='Metadata-only current route does not qualify geometry by itself'))
            additional_asset=decode_mesh_asset(data,records,additional_asset_id,member,members)
            if current_asset['asset_member']!=mesh['asset_member']:
                raise ValueError('MeshReduce current asset same-asset filename route disagrees')
            nil,cursor=read_string(body,82)
            if nil!=str(uuid.UUID(int=0)) or body[cursor:cursor+3]!=bytes(3):
                raise ValueError('MeshReduce nil UUID/repeated dependency separator mismatch')
            count=struct.unpack_from('<I',body,cursor+3)[0];cursor+=7
            if count!=5:raise ValueError('MeshReduce repeated dependency count mismatch')
            repeated=[reference(body,cursor+11*i) for i in range(count)];cursor+=11*count
            if repeated!=[selection_id,selection['descriptor_object_id'],binding_ids['Proportion'],binding_ids['Tolerance'],binding_ids['Face Count']]:
                raise ValueError('MeshReduce repeated descriptor/binding references disagree')
            if body[cursor:cursor+4]!=b'\xff'*4:raise ValueError('MeshReduce feature label marker mismatch')
            label,end=read_string(body,cursor+4);index=struct.unpack_from('<Q',body,end)[0];name,tail=read_string(body,end+8)
            if label!='MeshReduce' or index!=feature['stored_index'] or name!=feature.get('name') or len(body)-tail!=66:
                raise ValueError('MeshReduce counted label/index/name/footer framing mismatch')
            if deviation:
                if (mesh['native_feature_class_guid']!=MESH_FEATURE or mesh['feature_object_id']==owner
                        or mesh['collection_mesh_object_ids']!=[selection['mesh_object_id']]
                        or {r.object_id for r in records if r.is_primary and r.class_guid==MESH}!={selection['mesh_object_id']}
                        or (additional_asset['geometry']['node_count'],additional_asset['geometry']['triangle_count'])!=(6,8)
                        or (current_asset['geometry'] is not None and (current_asset['geometry']['node_count'],current_asset['geometry']['triangle_count'])!=(6,8))):
                    raise ValueError('MaximumDeviation outside captured singleton native owner/cache family')
            geometry=mesh['geometry'];current_count=geometry['triangle_count'] if geometry is not None else None
            settings=dict(method={0:'Adaptive',1:'Uniform'}[method],target_type={0:'MaximumDeviation',1:'Proportion',2:'FaceCount'}[target],
                stored_method_code=method,stored_target_code=target,scalar_bindings=scalar_rows,
                requested_face_count=values['Face Count'] if target==2 else None,
                requested_proportion_stored_value=values['Proportion'] if target==1 else None,
                proportion_units=scalar_rows['Proportion']['display_units'],
                proportion_scope='Captured real50.0 produces native/API ModelParameter50.0 unitempty; no0.5 normalization inferred and string50 % failure retained only as negative capture evidence',
                input_selection=selection,native_mesh_object_id=selection['mesh_object_id'],mesh_name=mesh['name'],
                component_object_id=mesh['component_object_id'],mesh_collection_object_id=mesh['mesh_collection_object_id'],
                current_mesh_native_feature_owner_object_id=mesh['feature_object_id'],
                current_mesh_native_owner_class_guid=mesh['native_feature_class_guid'],
                mesh_reduce_owns_current_mesh=None,
                owner_scope='Selection proves mesh input; current mesh owner remains the independently decoded native BaseMeshFeature. MeshReduce is not promoted to current mesh owner or API baseOrFormFeature',
                stored_current_asset_field_relative_offset=44,current_mesh_asset=current_asset,
                stored_additional_asset_field_relative_offset=55,additional_stored_asset=additional_asset,
                additional_asset_temporal_role=None,
                asset_scope='First typed stored asset is corroborated by selected native mesh current asset. Second typed asset is explicit but source/prior/result lifecycle role is unqualified; no identity inferred from coordinates or storage order',
                current_cache_node_count=geometry['node_count'] if geometry is not None else None,current_cache_triangle_count=current_count,
                face_count_target_attained_in_current_cache=(current_count==values['Face Count']) if target==2 else None,
                target_scope='Stored controls and current triangle counts compared arithmetically only. Successful feature/native control does not imply target attainment or execution of a reconstructed reduction algorithm',
                stored_two_asset_triangle_coordinate_multisets_equal=_triangles(current_asset['geometry'])==_triangles(additional_asset['geometry']) if current_asset['geometry'] is not None else None,
                geometry_scope='Exact stored coordinate/index arrays remain separate per explicitly referenced asset; multiset comparison is cache arithmetic only, no persistent face identity, source-state qualification or regeneration',
                repeated_dependency_object_ids=repeated)
            row=dict(feature_object_id=owner,kind='MeshReduce',name=name,settings=settings)
            if deviation:
                state=feature_state(body)
                state_id=reference(body,tail+7)
                _,state_body=typed(state_id,'B7F34D7B-DAC4-41A5-B67D-D672537C3BFA')
                if state_body!=bytes.fromhex('0000000000000100000000000000'):
                    raise ValueError('Unobserved MaximumDeviation shared state payload')
                def ref(identity):return b'\1'+struct.pack('<Q',identity)+bytes(2)
                def text(value):return struct.pack('<I',len(value))+value.encode('utf-16le')
                replay=(bytes(2)+ref(binding_ids['Tolerance'])+struct.pack('<I',method)+bytes(1)
                    +ref(binding_ids['Proportion'])+struct.pack('<I',target)+ref(binding_ids['Face Count'])
                    +ref(current_asset_id)+ref(additional_asset_id)+bytes(4)+ref(selection_id)+bytes(1)+text(nil)
                    +bytes(3)+struct.pack('<I',5)+b''.join(ref(i) for i in repeated)+b'\xff'*4
                    +text(label)+struct.pack('<Q',index)+text(name)+body[tail:])
                if replay!=body:raise ValueError('MaximumDeviation complete feature payload replay differs')
                settings.update(maximum_deviation_cm=values['Tolerance'],maximum_deviation_attained=None,
                    effective_algorithm=None,
                    method_scope='Literal native/API Adaptive0 or Uniform1 selection. SDK says MaximumDeviation uses Adaptive internally, but no executed algorithm is recovered; captured Uniform getter remains1 and is not normalized.',
                    maximum_deviation_scope='Positive finite owned float64 Tolerance internal centimetres corroborated at0.05/0.1; display unit mm does not rescale native value. No measured maximum deviation or target-attainment guarantee.',
                    proportion_scope='Inactive stored Proportion0 and Face Count0 in captured MaximumDeviation target; their mode-specific getters/setters were not invoked',
                    target_scope='Stored requested maximum deviation only; healthy feature, current counts or equal caches do not prove geometric deviation bounds or a reconstructed reduction algorithm',
                    geometry_unresolved=geometry_errors,
                    control_decoding_status='Qualified MaximumDeviation controls; current geometry unresolved' if geometry_errors else 'Qualified MaximumDeviation controls and independently decoded current cache',
                    layout=dict(feature_body_offset=record.body,feature_body_end_offset=record.end,feature_body_hex=body.hex(),
                        method_body_relative_offset=13,target_body_relative_offset=29,maximum_deviation_binding_reference_offset=2,
                        shared_footer_hex=body[tail:].hex(),shared_feature_state=state,stored_state_object_id=state_id,
                        stored_state_payload_hex=state_body.hex(),exact_full_payload_replay=True))
                if geometry_errors:
                    row['partial_reason']='Qualified MaximumDeviation controls and native metadata; current stored geometry unresolved'
                    result['partial'].append(row)
                    result['unresolved'].append(dict(feature_object_id=owner,class_guid=REDUCE,reason=row['partial_reason'],geometry_unresolved=geometry_errors))
                    continue
            result['decoded'].append(row)
        except (ValueError,KeyError,IndexError,UnicodeError,struct.error,TypeError) as error:
            result['unresolved'].append(dict(feature_object_id=record.object_id,class_guid=REDUCE,reason=str(error)))
    return result
