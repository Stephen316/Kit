"""Independent raw-native/control algebra for saved Extrude reconstructions."""
import argparse
import copy
import hashlib
import itertools
import json
import math
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_extrusion_reconstruction import decode_extrusion_reconstruction
from decode_sketch import attributes, numbers, reference
from validate_mesh_remesh import load

ROOT=Path(__file__).resolve().parent
BASELINE=Path('/private/tmp/fusion-extrusion-reconstruction-baseline.json')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def near(a,b):
    assert len(a)==len(b) and all(math.isfinite(x) for x in list(a)+list(b)),(a,b)
    assert max((abs(x-y) for x,y in zip(a,b)),default=0.)<1e-8,(a,b)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def key(value):
    if isinstance(value,(int,float)):return round(value,9)
    return tuple(key(x) for x in value)


def independent_stations(controls):
    extent,start=controls['extent'],controls['start'];one=extent['side_one'];distance=one['distance_cm']
    taper=one['taper_angle_radians'];offset=start.get('offset_cm',0.)
    if extent['mode']=='OneSided':
        rows=[(offset,0.),(offset+distance,taper)]
    elif extent['mode']=='Symmetric':
        half=distance/2 if extent['distance_convention']=='FullLength' else distance
        rows=[(-half,0.),(half,0.)]
    else:rows=[(-extent['side_two']['distance_cm'],0.),(distance,0.)]
    return sorted(rows)


def raw_source(data,records,owner):
    group=owner['native_source_provenance']['source_groups'][0];by={r.object_id:r for r in records if r.is_primary}
    transform=group['source_sketch_frame_provenance']['transform'];r=by[transform['object_id']]
    payload=data[r.body:r.end]
    matrix=([1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.] if len(payload)==15 else numbers(payload,3,16))
    assert matrix==group['source_sketch']['placement']['sketch_to_component_matrix']
    points={}
    for row in group['native_profile_points']:
        record=by[row['point_object_id']];body=data[record.body:record.end];_,cursor=attributes(body,2)
        local=numbers(body,cursor+19,3);assert local==row['position_cm']
        points[record.object_id]=[sum(matrix[4*i+j]*local[j] for j in range(3))+matrix[4*i+3] for i in range(3)]
    axis=[matrix[2],matrix[6],matrix[10]];near(axis,group['stored_direction_vector']);near(axis,group['sketch_normal_component'])
    assert group['binding']['stored_handle']==group['binding']['asm_stored_entity_id']
    assert group['binding']['previous_ordinal_candidate'] is None
    return group,by,matrix,points,axis


def independent_circle(data,records,members,owner):
    group,by,matrix,points,axis=raw_source(data,records,owner)
    circle=group['native_profile_circles'][0];record=by[circle['circle_object_id']];body=data[record.body:record.end]
    props,cursor=attributes(body,2);values=numbers(body,cursor,12)
    radius=values[9];center_id=reference(body,cursor+96)
    assert center_id==circle['center_point_id'] and props['crv_primary_id']==circle['entity_tag']
    center=points[center_id];near(values[:3],circle['center_cm']);near([radius],[circle['radius_cm']])
    controls=owner['native_source_provenance']['settings'];stations=independent_stations(controls)
    expected=[]
    for height,taper in stations:
        r=radius
        if taper:r+=controls['extent']['side_one']['distance_cm']*math.tan(taper)
        expected.append(dict(height_cm=height,center_cm=[c+height*n for c,n in zip(center,axis)],radius_cm=r))
    model=owner['derived_geometry'];observed=owner['native_cache_geometry_corroboration']
    for independent,published in zip(expected,model['axial_stations']):
        near([independent['height_cm'],independent['radius_cm']],[published['axial_distance_cm'],published['radius_cm']])
        near(independent['center_cm'],published['center_cm'])
    length=expected[1]['height_cm']-expected[0]['height_cm'];r0,r1=[s['radius_cm'] for s in expected]
    volume=math.pi*length*(r0*r0+r0*r1+r1*r1)/3
    near([volume],[model['volume_cm3']])
    slope=(r1-r0)/length;intercept=r0-slope*expected[0]['height_cm']
    near([slope,intercept],[model['lateral_carrier']['radial_slope'],model['lateral_carrier']['radial_intercept_cm']])
    bounds=dict(minimum=[min(s['center_cm'][i]-s['radius_cm']*math.sqrt(max(0.,1-axis[i]*axis[i])) for s in expected) for i in range(3)],
        maximum=[max(s['center_cm'][i]+s['radius_cm']*math.sqrt(max(0.,1-axis[i]*axis[i])) for s in expected) for i in range(3)])
    near(bounds['minimum'],model['component_axis_aligned_bounds_cm']['minimum']);near(bounds['maximum'],model['component_axis_aligned_bounds_cm']['maximum'])
    blob=members[owner['history_blob_member']];raw=inspect_asm(blob)['records'];circles=[];endpoint_rows=[]
    for row in observed['native_boundary_circles']:
        edge_id=row['native_EDGE']['index'];edge=raw[edge_id]['tokens'];curve=raw[edge[8]['value']]
        assert curve['name']=='ellipse-curve'
        origin,normal,reference_axis=[curve['tokens'][i]['value'] for i in (3,4,5)]
        radius=math.hypot(*reference_axis);near([curve['tokens'][6]['value']],[1.])
        near([abs(dot(normal,axis))],[1.]);near([abs(edge[6]['value']-edge[4]['value'])],[2*math.pi])
        assert edge[3]['value']==edge[5]['value']
        point_id=raw[edge[3]['value']]['tokens'][5]['value'];point=raw[point_id]['tokens'][3]['value']
        relative=[p-c for p,c in zip(point,origin)];near([dot(relative,normal),math.hypot(*relative)],[0.,radius])
        cap=raw[row['native_cap_FACE']['index']]['tokens'];plane=raw[cap[7]['value']]['tokens']
        plane_origin,plane_normal=plane[3]['value'],plane[4]['value']
        near([abs(dot(plane_normal,normal)),dot(plane_normal,[c-o for c,o in zip(origin,plane_origin)])],[1.,0.])
        coedges=[c['index'] for c in row['native_COEDGEs']]
        assert len(coedges)==2 and edge[7]['value'] in coedges
        for c,other in (coedges,list(reversed(coedges))):
            tokens=raw[c]['tokens'];assert tokens[5]['value']==other and tokens[6]['value']==edge_id
            assert tokens[3]['value']==c and tokens[4]['value']==c
            loop=raw[tokens[8]['value']]['tokens'];assert loop[4]['value']==c
        circles.append(origin+[radius])
        endpoint_rows.append(dict(edge_index=edge_id,vertex_index=edge[3]['value'],point_index=point_id,
            circle_center_cm=origin,raw_major_radius=radius,typed_point_cm=point,
            complete_turn_domain=[edge[4]['value'],edge[6]['value']]))
    assert key(sorted(circles,key=key))==key(sorted([s['center_cm']+[s['radius_cm']] for s in expected],key=key))
    # Exact circular cone coefficients, read directly from serialized tokens.
    carrier_id=observed['native_lateral_carrier']['index'];carrier=raw[carrier_id]['tokens']
    origin,normal,reference_axis=[carrier[i]['value'] for i in (3,4,5)]
    cosine,sine=carrier[10]['value'],carrier[9]['value'];near([sine*sine+cosine*cosine],[1.])
    relative=[o-c for o,c in zip(origin,center)];axial=dot(relative,axis)
    near([x-axial*n for x,n in zip(relative,axis)],[0.,0.,0.])
    orientation=dot(normal,axis);near([abs(orientation)],[1.])
    observed_slope=math.atan2(sine,cosine)
    raw_slope=math.tan(observed_slope)*orientation
    raw_intercept=math.hypot(*reference_axis)-raw_slope*axial
    near([raw_slope,raw_intercept],[slope,intercept])
    return dict(native_circle_object_id=circle['circle_object_id'],native_center_point_id=center_id,
        independently_derived_stations=expected,independent_lateral_coefficients=dict(radial_slope=slope,radial_intercept_cm=intercept),
        raw_lateral_carrier_record_index=carrier_id,raw_lateral_coefficients=dict(radial_slope=raw_slope,radial_intercept_cm=raw_intercept),
        independent_volume_cm3=volume,independent_bounds_cm=bounds,raw_closed_circle_checks=endpoint_rows,
        entity_mapping=None,scope='Raw native Circle/POINT/frame/control algebra and complete serialized cap/carrier equations; no coordinate identity selection')


def independent_rectangle(data,records,members,owner):
    group,by,matrix,points,axis=raw_source(data,records,owner);lines={}
    for row in group['native_profile_lines']:
        record=by[row['line_object_id']];body=data[record.body:record.end];_,cursor=attributes(body,2)
        ends=[reference(body,cursor+107),reference(body,cursor+96)]
        assert ends==[row['start_point_id'],row['end_point_id']];lines[record.object_id]=ends
    assert len(lines)==len(points)==4 and all(sum(p in e for e in lines.values())==2 for p in points)
    heights=[r[0] for r in independent_stations(owner['native_source_provenance']['settings'])]
    predicted=[[x+h*n for x,n in zip(p,axis)] for h in heights for p in points.values()]
    model=owner['derived_geometry'];observed=owner['native_cache_geometry_corroboration']
    assert key(sorted(predicted,key=key))==key(sorted([v['derived_position_cm'] for v in model['constructed_vertices']],key=key))
    raw=inspect_asm(members[owner['history_blob_member']])['records'];cached=[]
    for row in observed['native_vertices']:
        vertex=raw[row['native_VERTEX']['index']]['tokens'];cached.append(raw[vertex[5]['value']]['tokens'][3]['value'])
    assert key(sorted(predicted,key=key))==key(sorted(cached,key=key))
    # Whole Line coefficients and finite domains independently reproduce edges.
    for row in observed['native_straight_segments']:
        edge=raw[row['native_EDGE']['index']]['tokens'];curve=raw[edge[8]['value']]['tokens']
        sign=-1 if edge[9]['value'] else 1
        for field,parameter in ((3,edge[4]['value']),(5,edge[6]['value'])):
            point=raw[raw[edge[field]['value']]['tokens'][5]['value']]['tokens'][3]['value']
            near([o+sign*parameter*d for o,d in zip(curve[3]['value'],curve[4]['value'])],point)
    for row in observed['native_planar_boundaries']:
        face=raw[row['native_FACE']['index']]['tokens'];plane=raw[face[7]['value']]['tokens']
        for vertex in row['loop']['vertex_cycle']:
            point=raw[raw[vertex]['tokens'][5]['value']]['tokens'][3]['value']
            near([dot(plane[4]['value'],[p-o for p,o in zip(point,plane[3]['value'])])],[0.])
    return dict(native_profile_line_endpoints=lines,independent_axial_stations_cm=heights,
        independently_predicted_vertex_set_cm=predicted,complete_cached_vertex_set_cm=cached,
        segment_count=12,planar_quad_count=6,entity_mapping=None,
        scope='Native endpoint/frame/extent-derived prism and complete unordered stored straight/Plane boundary; no ENTITY assignment')


def altered_blob(blob,record,field,value):
    token=record['tokens'][field];changed=bytearray(blob)
    if token['tag'] in (4,12):struct.pack_into('<q',changed,token['offset']+1,value)
    elif isinstance(value,(list,tuple)):struct.pack_into('<3d',changed,token['offset']+1,*value)
    elif token['kind']=='boolean_token':changed[token['offset']]=10 if value else 11
    else:struct.pack_into('<d',changed,token['offset']+1,value)
    return bytes(changed)


def validate(root,zstd):
    baseline=json.loads(BASELINE.read_text());samples=[];saved={};checks=[];guards=[];positives=[]
    totals=dict(decoded_owners=0,circular_solids=0,rectangular_prisms=0,explicit_unresolved=0,empty_controls=0,
        native_circle_edges=0,analytic_side_carriers=0,planar_caps=0,rectangle_edges=0,rectangle_faces=0,API_bounds=0)
    truth=json.loads((root/'extents-f0f33a9a605f/ground_truth.json').read_text())
    for archive,old in zip(baseline['files'],baseline['before']):
        data,records,features,member,members=load(root,archive,zstd);bindings=old['streams'][0]['body_blob_bindings']
        before=copy.deepcopy((features,bindings,members))
        result=decode_extrusion_reconstruction(data,records,features,member,members,bindings)
        assert (features,bindings,members)==before;checks.append(archive+' caller purity')
        assert len(result['decoded'])+len(result['unresolved'])==sum(f.get('kind')=='Extrude' for f in features)
        checks.append(archive+' explicit per-Extrude outcome')
        evidence=[]
        for owner in result['decoded']:
            totals['decoded_owners']+=1
            if owner['native_source_provenance']['source_groups'][0]['native_profile_kind']=='Circle':
                row=independent_circle(data,records,members,owner);totals['circular_solids']+=1
                totals['native_circle_edges']+=2;totals['analytic_side_carriers']+=1;totals['planar_caps']+=2
            else:
                row=independent_rectangle(data,records,members,owner);totals['rectangular_prisms']+=1
                totals['rectangle_edges']+=12;totals['rectangle_faces']+=6
            evidence.append(row);checks.extend([archive+' raw native operands '+str(owner['feature_object_id']),
                archive+' independent complete geometry '+str(owner['feature_object_id'])])
            assert all(owner[k] is None for k in ('source_to_cache_entity_mapping','exact_API_handle_identity','qualified_historical_state','current_or_final_geometry_identity'))
            if archive.startswith('extents-'):
                api=next(s for s in truth['samples'] if s['file']==Path(archive).name)
                near(row['independent_bounds_cm']['minimum'],api['body_bounds_cm'][0]);near(row['independent_bounds_cm']['maximum'],api['body_bounds_cm'][1])
                row['actual_API_bounds_cm']=api['body_bounds_cm'];totals['API_bounds']+=1
            if archive not in saved:saved[archive]=(data,records,features,member,members,bindings,result)
        totals['explicit_unresolved']+=len(result['unresolved'])
        if not result['decoded'] and not result['unresolved']:totals['empty_controls']+=1
        samples.append(dict(archive=archive,archive_sha256=sha(root/archive),expected_summary=result,
            independent_raw_native_geometry=evidence,caller_inputs_unchanged=True))
    assert totals['decoded_owners']==13 and totals['circular_solids']==12 and totals['rectangular_prisms']==1,totals
    assert totals['explicit_unresolved']==14 and totals['empty_controls']==2,totals
    # Mutate actual serialized token bytes, retaining each intended token type.
    saved_case=saved['extents-f0f33a9a605f/taper.f3d'];data,records,features,member,members,bindings,positive=saved_case
    owner=positive['decoded'][0];name=owner['history_blob_member'];blob=members[name];raw=inspect_asm(blob)['records']
    def reject(name,mutant,expected):
        changed=dict(members);changed[owner['history_blob_member']]=mutant
        result=decode_extrusion_reconstruction(data,records,features,member,changed,bindings)
        reasons=[r['reason'] for r in result['unresolved']]
        assert not result['decoded'] and any(expected in r for r in reasons),(name,result)
        guards.append(dict(name=name,reasons=reasons,intended_failure=expected))
    observation=owner['native_cache_geometry_corroboration'];side=raw[observation['native_lateral_carrier']['index']]
    angle=math.atan2(side['tokens'][9]['value'],side['tokens'][10]['value'])+.02
    mutant=altered_blob(blob,side,9,math.sin(angle));mutant=altered_blob(mutant,side,10,math.cos(angle))
    reject('Cone finite radial slope',mutant,'lateral radial-slope coefficient')
    origin=side['tokens'][3]['value'];axis=side['tokens'][4]['value']
    reject('Cone finite radial intercept',altered_blob(blob,side,3,[o+.1*n for o,n in zip(origin,axis)]),'lateral radial-intercept coefficient')
    boundary=observation['native_boundary_circles'][0];circle=raw[boundary['native_Circle']['index']]
    reject('Cap Circle finite radius',altered_blob(blob,circle,5,[1.1*x for x in circle['tokens'][5]['value']]),'closed-circle native endpoint evaluation')
    plane=raw[boundary['native_cap_Plane']['index']]
    reject('Cap Plane finite constant',altered_blob(blob,plane,3,[o+.1*n for o,n in zip(plane['tokens'][3]['value'],plane['tokens'][4]['value'])]),'cap Plane contains whole circular boundary')
    # Rotate both normal and reference axis so canonical primitive parsing still
    # succeeds and the intended cap coefficient proof must reject the mutant.
    mutant=altered_blob(blob,plane,4,[.1,0.,math.sqrt(.99)])
    ref=plane['tokens'][5]['value'];length=math.hypot(*ref)
    mutant=altered_blob(mutant,plane,5,[length*math.sqrt(.99),0.,-.1*length])
    reject('Cap Plane finite normal coefficients',mutant,'cap Plane normal coefficients')
    coedge=raw[boundary['native_COEDGEs'][0]['index']]
    reject('Actual pointer self partner',altered_blob(blob,coedge,5,coedge['index']),'other-use partner reciprocity')
    edge=raw[boundary['native_EDGE']['index']]
    other=next(row for row in observation['native_boundary_circles'] if row['native_EDGE']['index']!=edge['index'])
    reject('Actual pointer nonincident EDGE head',altered_blob(blob,edge,7,other['native_COEDGEs'][0]['index']),'head/two-FACE/other-use partner reciprocity')
    reject('Finite circular EDGE domain changed',altered_blob(blob,edge,6,edge['tokens'][6]['value']+.1),'closed-circle finite EDGE domain')
    reject('NaN analytic origin rejected at fresh native mapping',altered_blob(blob,side,3,[float('nan'),0.,0.]),'unique same-asset stored-ID mapping')
    # Native source vector is a design payload field, not an ASM coordinate.
    record=next(r for r in records if r.is_primary and r.object_id==owner['feature_object_id'])
    changed=bytearray(data);body=data[record.body:record.end];cursor=7 if body[6]==0 else 17
    struct.pack_into('<3d',changed,record.body+cursor+2+18,.6,0.,.8);changed=bytes(changed)
    altered_members=dict(members);altered_members[member]=changed
    result=decode_extrusion_reconstruction(changed,records,features,member,altered_members,bindings)
    assert not result['decoded'] and any('stored direction/component Sketch normal frame relation unsupported' in r['reason'] for r in result['unresolved']),result
    guards.append(dict(name='Actual native source frame vector disagreement',reasons=[r['reason'] for r in result['unresolved']]))
    # Literal UV flag has no geometric interpretation in this proof.
    changed=dict(members);changed[name]=altered_blob(blob,side,12,not side['tokens'][12]['value'])
    result=decode_extrusion_reconstruction(data,records,features,member,changed,bindings)
    assert len(result['decoded'])==1 and not result['unresolved']
    assert result['decoded'][0]['native_cache_geometry_corroboration']['complete_coefficient_residuals_raw']==observation['complete_coefficient_residuals_raw']
    positives.append(dict(name='Lateral native U flag changes only retained literal',passed=True))
    # Caller annotations never become source geometry or inferred native mapping.
    injected=copy.deepcopy(features);injected[0]['unrelated_caller_annotation']='ignored'
    annotated=copy.deepcopy(bindings)
    for mapping in annotated['decoded']:
        for binding in mapping['bindings']:binding['candidate_asm_body_index']=123456
    assert decode_extrusion_reconstruction(data,records,injected,member,members,annotated)==positive
    positives.append(dict(name='Caller annotations and ordinal candidates ignored',passed=True))
    return dict(scope='Fixed23 independent raw-native/capped analytic/rectangle checks; zero main/live calls',
        baseline_commit=baseline['baseline_commit'],baseline_sha256=sha(BASELINE),acquisition_main_calls=0,live_API_calls=0,
        samples=samples,totals=totals,checks=checks,check_count=len(checks),guards=guards,guard_count=len(guards),positive_controls=positives,
        limitations=['No source-before/final/current state assignment.','Native component/world direction ambiguities remain explicit for two assembly sources.',
            'ToEntity/FromEntity/ThroughAll/booleans/trimmed profile portions remain unsupported.',
            'Saved numerical API bounds support only five direct extent fixtures; other mathematical bodies use native coefficient proofs.'],
        source_sha256={n:sha(root/n) for n in ('decode_extrusion_reconstruction.py','validate_extrusion_reconstruction.py',
            'decode_extrusion_source_operands.py','decode_circular_extrusion_geometry.py','decode_scale_prism_geometry.py')})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library',required=True);args=parser.parse_args()
    report=validate(ROOT,args.zstd_library)
    (ROOT/'extrusion-reconstruction-decoding.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(totals=report['totals'],checks=report['check_count'],guards=report['guard_count'])))
