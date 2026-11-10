"""Raw selected-plane routes and independent station/cache verification."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_basics import named_features, attach_parameters
from decode_extrude import decode_extrude, optional_reference
from decode_extrusion_reconstruction import decode_extrusion_reconstruction
from decode_parameters import decode_stream
from decode_plane_extrusion_reconstruction import decode_plane_extrusion_reconstruction
from decode_sketch import attributes, numbers, reference
from validate_extrusion_reconstruction import independent_circle, altered_blob, near
from validate_mesh_remesh import load

ROOT=Path(__file__).resolve().parent
BASELINE=Path('/private/tmp/fusion-plane-extrusion-reconstruction-baseline.json')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def dot(a,b):return sum(x*y for x,y in zip(a,b))


def independent(data,records,features,members,owner):
    by={r.object_id:r for r in records if r.is_primary}
    source=owner['native_source_provenance'];group=source['source_groups'][0]
    limit,=source['plane_limit_provenance']['limits'];definition=limit['plane_definition']
    record=by[owner['feature_object_id']]
    feature=next(f for f in features if f['object_id']==record.object_id)
    original,reasons=decode_extrude(data[record.body:record.end],feature,allow_surface=True)
    assert original==source['settings']==group['extrude_controls']
    assert reasons==['Referenced start/end geometry selection not decoded']
    role=limit['operand_scope'];selection_id=limit['native_selection_record_object_id']
    selector=original['start'] if role=='start' else original['extent']['side_one']
    assert selector['selection_record_object_id']==selection_id
    proxy=by[selection_id];pb=data[proxy.body:proxy.end]
    descriptor_id=reference(pb,6);descriptor=by[descriptor_id];db=data[descriptor.body:descriptor.end]
    assert reference(pb,94)==record.object_id==reference(db,252)
    assert descriptor_id==limit['descriptor_object_id']
    leaf=by[reference(db,2)];leaf_bytes=data[leaf.body:leaf.end]
    assert leaf.class_guid=='90055C05-546C-4EE7-B3C9-3DD922AD0C9C' and len(leaf_bytes)==10
    plane_id=struct.unpack_from('<Q',leaf_bytes,2)[0]
    assert plane_id==definition['plane_object_id']
    plane=by[plane_id];plane_body=data[plane.body:plane.end];_,cursor=attributes(plane_body,2)
    stored_frame=numbers(plane_body,cursor+21,9)
    near(stored_frame,limit['stored_plane_geometry']['origin_cm']+limit['stored_plane_geometry']['x_axis']+limit['stored_plane_geometry']['y_axis'])
    support,=definition['support_inputs'];origin=support['entity']['native_entity']
    origin_record=by[origin['object_id']];origin_body=data[origin_record.body:origin_record.end]
    _,cursor=attributes(origin_body,2);origin_frame=numbers(origin_body,cursor+21,9)
    origin_position,x,y=origin_frame[:3],origin_frame[3:6],origin_frame[6:]
    normal=cross(x,y)
    near(origin_position,origin['origin_cm']);near(normal,origin['normal'])
    scalar,=definition['scalar_parameters'];binding=by[scalar['binding_object_id']]
    binding_body=data[binding.body:binding.end]
    assert struct.unpack_from('<Q',binding_body,6)[0]==definition['feature_object_id']
    value=struct.unpack_from('<d',binding_body,21)[0]
    assert value==scalar['value'] and definition['definition_kind']=='Offset' and definition['stored_backend_method_code']==2
    plane_origin=[p+value*n for p,n in zip(origin_position,normal)]
    near(plane_origin,stored_frame[:3]);near(normal,cross(stored_frame[3:6],stored_frame[6:]))
    near(plane_origin,limit['plane_native_geometry']['origin_cm'])
    # Typed context/direct leaves identify the same plane, independently of the
    # context's copied geometry. Coordinates never choose the selected entity.
    context=by[limit['context_object_id']];cb=data[context.body:context.end]
    near(numbers(cb,3,9),stored_frame)
    link=by[reference(cb,76)];lb=data[link.body:link.end]
    context_leaf=by[reference(lb,2)]
    assert data[context_leaf.body:context_leaf.end]==leaf_bytes
    profile=group['source_sketch']['placement']['sketch_to_component_matrix']
    axis=[profile[2],profile[6],profile[10]];profile_origin=[profile[3],profile[7],profile[11]]
    near(axis,[0.,0.,1.]);near(axis,original['extent']['stored_direction_vector']);near(axis,normal)
    intersection=dot(normal,[p-o for p,o in zip(plane_origin,profile_origin)])/dot(normal,axis)
    assert math.isfinite(intersection) and intersection>0
    def raw_binding(identity):
        record=by[identity];payload=data[record.body:record.end]
        assert struct.unpack_from('<Q',payload,6)[0]==owner['feature_object_id'] and reference(payload,len(payload)-11)==owner['feature_object_id']
        return struct.unpack_from('<d',payload,21)[0]
    references=original['extrusion_reference_fields']
    if role=='side_one':
        offset=raw_binding(references['offset']);low,high=0.,intersection+offset
        assert original['start']['kind']=='ProfilePlane' and original['extent']['side_one']['condition']=='ToEntity'
        assert original['extent']['side_one']['uninterpreted_flags']==1
    else:
        offset=raw_binding(references['start']);length=raw_binding(references['along'])
        low=intersection+offset;high=low+length
        assert original['start']['kind']=='FromEntity' and original['extent']['side_one']['condition']=='Distance'
        assert original['extent']['side_one']['uninterpreted_flags']==0
    assert offset>=0 and high>low
    model=owner['derived_geometry'];derivation=model['plane_limit_derivation']
    near([low,high],[s['axial_distance_cm'] for s in model['axial_stations']])
    near([intersection],[derivation['selected_plane_intersection_distance_cm']])
    assert derivation['native_start_kind']==original['start']['kind'] and derivation['native_end_kind']==original['extent']['side_one']['condition']
    assert derivation['mathematical_equivalent_controls_are_native_records'] is False
    # Reuse the earlier raw carrier/circle checker with independently constructed
    # reference stations. This private test object is not published native proof.
    equivalent=dict(operation=dict(kind='NewBody'),is_solid=True,stored_second_extent_enabled=0,
        start=dict(kind='ProfilePlane') if low==0 else dict(kind='Offset',offset_cm=low),
        extent=dict(mode='OneSided',side_one=dict(condition='Distance',uninterpreted_flags=0,taper_angle_radians=0.,distance_cm=high-low)))
    adapted=copy.deepcopy(owner);adapted['native_source_provenance']['settings']=equivalent
    geometry=independent_circle(data,records,members,adapted)
    assert source['settings']==original and group['extrude_controls']==original
    near([math.pi*(high-low)],[geometry['independent_volume_cm3']])
    return dict(native_selector_route=dict(proxy_object_id=selection_id,descriptor_object_id=descriptor_id,
        direct_leaf_object_id=leaf.object_id,selected_plane_object_id=plane_id,
        context_object_id=context.object_id,context_link_object_id=link.object_id,context_leaf_object_id=context_leaf.object_id),
        raw_origin_plane_frame=origin_frame,native_Offset_binding_object_id=binding.object_id,
        raw_Offset_scalar_cm=value,independently_derived_selected_plane_origin_cm=plane_origin,
        stored_selected_plane_frame=stored_frame,independent_plane_intersection_cm=intersection,
        independent_selected_offset_cm=offset,independent_axial_interval_cm=[low,high],
        original_native_start_kind=original['start']['kind'],original_native_end_kind=original['extent']['side_one']['condition'],
        complete_raw_cache_geometry=geometry,API_handle_identity=None,
        scope='Typed direct/context plane leaves and raw origin-plane/Offset binding, then independent axis intersection and full native analytic cache equations; no coordinate selection')


def fresh_features(data,records):
    features=named_features(data,records);parameters,_=decode_stream(data,records)
    attach_parameters(data,records,features,parameters)
    return features


def flags_offset(body):
    _,cursor=optional_reference(body,6);cursor+=2+42
    for _ in range(7):_,cursor=optional_reference(body,cursor)
    cursor+=4;_,cursor=optional_reference(body,cursor)
    return cursor


def validate(root,zstd):
    baseline=json.loads(BASELINE.read_text());samples=[];checks=[];guards=[];positives=[];saved=None
    truth=json.loads((root/'extents-f0f33a9a605f/ground_truth.json').read_text())
    counts=dict(decoded_owners=0,selected_native_planes=0,complete_circle_boundaries=0,analytic_carriers=0,
        Plane_caps=0,actual_API_bounds=0,empty_controls=0,prior_helper_full_summaries_exact=0)
    for archive,old in zip(baseline['files'],baseline['before']):
        data,records,features,member,members=load(root,archive,zstd);bindings=old['streams'][0]['body_blob_bindings']
        before=copy.deepcopy((features,bindings,members))
        result=decode_plane_extrusion_reconstruction(data,records,features,member,members,bindings)
        assert not result['unresolved'],(archive,result)
        assert (features,bindings,members)==before;checks.append(archive+' full caller purity')
        expected=1 if Path(archive).name in ('to_plane.f3d','to_plane_offset.f3d','from_plane.f3d') else 0
        assert len(result['decoded'])==expected;checks.append(archive+' bounded selected-limit candidate gate')
        proofs=[]
        for owner in result['decoded']:
            proof=independent(data,records,features,members,owner)
            api=next(s for s in truth['samples'] if s['file']==Path(archive).name)
            bounds=proof['complete_raw_cache_geometry']['independent_bounds_cm']
            near(bounds['minimum'],api['body_bounds_cm'][0]);near(bounds['maximum'],api['body_bounds_cm'][1])
            proof['actual_saved_API_bounds_cm']=api['body_bounds_cm'];proofs.append(proof)
            counts['decoded_owners']+=1;counts['selected_native_planes']+=1;counts['complete_circle_boundaries']+=2
            counts['analytic_carriers']+=1;counts['Plane_caps']+=2;counts['actual_API_bounds']+=1
            checks.extend([archive+' independent raw native plane selection',archive+' raw Offset definition derivation',
                archive+' original native control kinds unchanged',archive+' independent station interval',
                archive+' complete analytic cache carriers/boundaries',archive+' actual saved API bounds'])
            assert all(owner[k] is None for k in ('source_to_cache_entity_mapping','exact_API_handle_identity','qualified_historical_state','current_or_final_geometry_identity'))
            if saved is None:saved=(data,records,features,member,members,bindings,result)
        if not result['decoded']:counts['empty_controls']+=1
        # The existing helper remains responsible for its old diagnostic text.
        prior=decode_extrusion_reconstruction(data,records,features,member,members,bindings)
        original=old['streams'][0].get('extrusion_reconstruction')
        if original is None:assert not prior['decoded'] and not prior['unresolved']
        else:assert prior==original,(archive,'prior helper dictionary changed')
        counts['prior_helper_full_summaries_exact']+=1;checks.append(archive+' previous helper full summary exact')
        samples.append(dict(archive=archive,archive_sha256=sha(root/archive),expected_summary=result,
            independent_native_station_geometry=proofs,prior_extrusion_summary_exact=True,caller_inputs_unchanged=True))
    assert counts['decoded_owners']==3 and counts['empty_controls']==5
    data,records,features,member,members,bindings,result=saved;owner=result['decoded'][0]
    by={r.object_id:r for r in records if r.is_primary};limit=owner['native_source_provenance']['plane_limit_provenance']['limits'][0]
    def reject(name,changed_data,changed_members,expected):
        fresh=fresh_features(changed_data,records)
        found=decode_plane_extrusion_reconstruction(changed_data,records,fresh,member,changed_members,bindings)
        reasons=[r['reason'] for r in found['unresolved']]
        assert not found['decoded'] and any(expected in r for r in reasons),(name,found)
        guards.append(dict(name=name,reasons=reasons,intended_failure=expected))
    def native_mutant(name,operation,expected):
        changed=bytearray(data);operation(changed);changed=bytes(changed);ms=dict(members);ms[member]=changed
        reject(name,changed,ms,expected)
    context=by[limit['context_object_id']]
    native_mutant('Copied selector context plane moved',lambda changed:struct.pack_into('<d',changed,context.body+3+16,3.1),'explicit context frame differs')
    context_leaf=by[limit['context_identity_leaf_object_id']]
    origin_id=limit['plane_definition']['support_inputs'][0]['entity']['native_entity']['object_id']
    native_mutant('Context/direct plane identities disagree',lambda changed:struct.pack_into('<Q',changed,context_leaf.body+2,origin_id),'context/direct leaf plane identities differ')
    scalar=limit['plane_definition']['scalar_parameters'][0];binding=by[scalar['binding_object_id']]
    plane_feature=next(f for f in features if f['object_id']==limit['plane_definition']['feature_object_id'])
    parameter=next(p for p in plane_feature['parameters'] if p['binding_object_id']==binding.object_id)
    def changed_plane_scalar(changed):
        struct.pack_into('<d',changed,binding.body+21,4.)
        struct.pack_into('<d',changed,parameter['value_offset'],4.)
    native_mutant('Owned plane scalar/frame inconsistency',changed_plane_scalar,'Offset scalar/support/frame consistency differs')
    receiver=by[owner['feature_object_id']];payload=data[receiver.body:receiver.end]
    native_mutant('Unproved selected end flag',lambda changed:struct.pack_into('<I',changed,receiver.body+flags_offset(payload),0),'control combination outside observed family')
    selected_offset=owner['native_source_provenance']['settings']['extrusion_reference_fields']['offset']
    offset_binding=by[selected_offset];offset_parameter=next(p for p in next(f for f in features if f['object_id']==receiver.object_id)['parameters'] if p['binding_object_id']==selected_offset)
    def negative_offset(changed):
        struct.pack_into('<d',changed,offset_binding.body+21,-.1)
        struct.pack_into('<d',changed,offset_parameter['value_offset'],-.1)
    native_mutant('Negative selected-plane offset convention',negative_offset,'nonnegative selected-plane offset')
    _,cursor=optional_reference(payload,6)
    angle=1e-5
    native_mutant('Small native direction/frame rotation',lambda changed:struct.pack_into('<3d',changed,receiver.body+cursor+2+18,math.sin(angle),0.,math.cos(angle)),'outside parallel co-directed component frame')
    name=owner['history_blob_member'];blob=members[name];raw=inspect_asm(blob)['records']
    observation=owner['native_cache_geometry_corroboration'];cap=observation['native_boundary_circles'][0]
    plane=raw[cap['native_cap_Plane']['index']]
    mutant=altered_blob(blob,plane,4,[math.sin(angle),0.,math.cos(angle)])
    reference_length=math.hypot(*plane['tokens'][5]['value'])
    mutant=altered_blob(mutant,plane,5,[reference_length*math.cos(angle),0.,-reference_length*math.sin(angle)])
    ms=dict(members);ms[name]=mutant
    # dot(normal,+Z) differs only5e-11; componentwise coefficients must reject.
    assert abs(math.cos(angle)-1)<1e-8
    reject('Tiny coherent cap Plane rotation bypasses dot-only tolerance',data,ms,'cap Plane normal vector coefficients')
    side=raw[observation['native_lateral_carrier']['index']]
    ms=dict(members);ms[name]=altered_blob(blob,side,5,[1.01*v for v in side['tokens'][5]['value']])
    reject('Complete lateral radius coefficient mismatch',data,ms,'lateral radial-intercept coefficient')
    # Unrelated caller fields cannot create a new selected-plane candidate.
    control=next(s for s in samples if s['archive'].endswith('/distance_positive.f3d'))
    index=baseline['files'].index(control['archive']);d,r,f,m,ms=load(root,control['archive'],zstd)
    next(x for x in f if x['kind']=='Extrude')['tool_settings']={'start':{'kind':'FromEntity'}}
    assert decode_plane_extrusion_reconstruction(d,r,f,m,ms,baseline['before'][index]['streams'][0]['body_blob_bindings'])==control['expected_summary']
    positives.append(dict(name='Caller tool settings cannot invent a selected-limit candidate',passed=True))
    return dict(scope='Fixed8 native plane-limit/math/cache proof with actual-byte guards; no main/live calls',
        baseline_commit=baseline['baseline_commit'],baseline_sha256=sha(BASELINE),samples=samples,
        totals=counts,checks=checks,check_count=len(checks),guards=guards,guard_count=len(guards),positive_controls=positives,
        acquisition_main_calls=0,live_API_calls=0,
        source_sha256={n:sha(root/n) for n in ('decode_plane_extrusion_reconstruction.py','validate_plane_extrusion_reconstruction.py',
            'decode_extrusion_source_operands.py','decode_extrusion_plane_limits.py','decode_plane_extrusion_geometry.py',
            'decode_extrusion_reconstruction.py','decode_circular_extrusion_geometry.py','validate_extrusion_reconstruction.py')})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library',required=True);args=parser.parse_args()
    report=validate(ROOT,args.zstd_library)
    (ROOT/'plane-extrusion-reconstruction-decoding.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(totals=report['totals'],checks=report['check_count'],guards=report['guard_count'])))
