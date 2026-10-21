"""Independent native source orientation/integrals and raw analytic BODY checks."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_revolve_reconstruction import decode_revolve_reconstruction
from validate_extrusion_reconstruction import altered_blob,near
from validate_mesh_remesh import load
from validate_revolve_reconstruction_integration import FILES,rectangle_source_reference

ROOT=Path(__file__).resolve().parent
BASELINE=Path('/private/tmp/fusion-revolve-reconstruction-baseline.json')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def sub(a,b):return [x-y for x,y in zip(a,b)]
def canonical(a):
    assert math.isfinite(math.hypot(*a));near([dot(a,a)],[1.])
    first=next(x for x in a if abs(x)>1e-10)
    return [x if first>0 else -x for x in a]
def nested(a,b):
    if isinstance(a,str) or isinstance(b,str):assert a==b;return
    if isinstance(a,(int,float)) and isinstance(b,(int,float)):near([a],[b]);return
    assert len(a)==len(b)
    for x,y in zip(a,b):nested(x,y)


def raw_source(data,records,row):
    source=row['native_source_provenance'];group,=source['source_groups'];by={}
    for record in records:
        if record.is_primary:by.setdefault(record.object_id,[]).append(record)
    checked=set()
    def replay(value):
        if isinstance(value,dict):
            keys={'object_id','class_guid','record_offset','body_offset','end_offset','payload_hex'}
            if keys<=value.keys():
                r,=by[value['object_id']]
                assert (r.class_guid,r.start,r.body,r.end)==(value['class_guid'],value['record_offset'],value['body_offset'],value['end_offset'])
                assert data[r.body:r.end].hex()==value['payload_hex'];checked.add(r.object_id)
            for child in value.values():replay(child)
        elif isinstance(value,list):
            for child in value:replay(child)
    replay(source)
    assert row['feature_object_id'] in checked
    assert group['native_body_object_id']==row['source_native_body_object_id'] and group['binding']==row['binding']
    assert group['binding']['stored_handle']==group['binding']['asm_stored_entity_id']
    matrix=group['mathematical_inputs']['sketch_to_component_matrix']
    assert matrix==group['source_sketch']['placement']['sketch_to_component_matrix']
    profile=group['mathematical_profile'];effective=row['derived_geometry']['effective_axis']
    axis=group['mathematical_inputs']['source_axis'];origin=axis['origin_cm'];direction=axis['direction']
    normal=[matrix[2],matrix[6],matrix[10]]
    def transform(p):return [sum(matrix[4*i+j]*p[j] for j in range(3))+matrix[4*i+3] for i in range(3)]
    if profile['kind']=='Polygon':
        points=[transform(p) for p in profile['points_cm']]
        center=[sum(p[i] for p in points)/len(points) for i in range(3)]
    elif profile['kind']=='Circle':center=transform(profile['center_cm'])
    else:
        # A source-only interior point of the selected semicircle determines
        # orientation; never use the target Sphere's arbitrary native axes.
        g=profile;mid=sum(g['angle_interval_radians'])/2
        n,u=g['normal'],g['reference_axis'];v=cross(n,u)
        p=[o+g['radius_cm']*(math.cos(mid)*x+math.sin(mid)*y) for o,x,y in zip(g['center_cm'],u,v)]
        center=transform(p)
    delta=sub(center,origin);height=dot(delta,direction);radial=[x-height*a for x,a in zip(delta,direction)]
    triple=dot(cross(direction,radial),normal);assert abs(triple)>1e-10
    sign=1 if triple>0 else -1;wanted=[sign*x for x in direction]
    near(effective['origin_cm'],origin);near(effective['direction'],wanted)
    assert effective['stored_direction_multiplier']==sign
    controls=source['original_controls'];rev=controls['revolve']
    if rev['mode']=='OneSided':interval=sorted([0.,rev['angle_radians']])
    elif rev['mode']=='Symmetric':interval=[-rev['angle_radians'],rev['angle_radians']]
    else:interval=[-rev['against_angle_radians'],rev['angle_radians']]
    near(interval,row['derived_geometry']['angular_interval_radians'])
    assert controls==group['mathematical_inputs']['controls']
    return dict(native_records_replayed=len(checked),source_only_angular_orientation_triple_product=triple,
        independent_effective_axis=wanted,independent_native_angular_interval_radians=interval,
        stored_axis_direction=direction,native_ENTITY_assignment=None)


def raw_cache(members,row):
    raw=inspect_asm(members[row['history_blob_member']])['records'];proof=row['native_cache_geometry_corroboration']
    edgeproof=[];carrierproof=[];coedges=set();loops=set();endpoint_count=0
    def point(v):return raw[raw[v]['tokens'][5]['value']]['tokens'][3]['value']
    for item in proof['native_bounded_edges']:
        edge=item['native_EDGE'];e=raw[edge['index']]['tokens']
        assert [e[3]['value'],e[5]['value'],e[7]['value'],None if e[8]['value']==-1 else e[8]['value']]==[edge[k] for k in ('start_vertex_index','end_vertex_index','first_coedge_index','curve_index')]
        assert edge['is_reversed']==e[9]['value']
        positions=[point(e[k]['value']) for k in (3,5)];parameters=[e[4]['value'],e[6]['value']]
        if e[8]['value']==-1:
            assert e[3]['value']==e[5]['value'];nested(item['complete_geometric_signature'],['PointSingularity',positions[0]])
            edgeproof.append(dict(edge_index=edge['index'],singular_null_curve=True,raw_parameter_literals=parameters,evaluator_meaning=None));continue
        curve=raw[e[8]['value']];c=curve['tokens']
        if curve['name']=='straight-curve':
            origin,direction=c[3]['value'],c[4]['value'];near([dot(direction,direction)],[1.])
            evaluated=[[o+t*d for o,d in zip(origin,direction)] for t in parameters]
            signature=item['complete_geometric_signature'];assert signature[0]=='LineSegment'
            nested(sorted(evaluated),sorted(signature[1]))
        else:
            assert curve['name']=='ellipse-curve' and c[6]['value']==1.
            origin,normal,reference=[c[k]['value'] for k in (3,4,5)];radius=math.hypot(*reference)
            u=[x/radius for x in reference];v=cross(normal,u);near([dot(normal,normal),dot(u,u),dot(normal,u)],[1.,1.,0.])
            evaluated=[[o+radius*(math.cos(t)*x+math.sin(t)*y) for o,x,y in zip(origin,u,v)] for t in parameters]
            span=abs(parameters[1]-parameters[0]);signature=item['complete_geometric_signature']
            nested(signature[1:4],[origin,radius,canonical(normal)])
            if abs(span-2*math.pi)<1e-8:assert signature[0]=='Circle' and e[3]['value']==e[5]['value']
            else:
                assert signature[0]=='CircleArc';middle=sum(parameters)/2
                q=[o+radius*(math.cos(middle)*x+math.sin(middle)*y) for o,x,y in zip(origin,u,v)]
                nested(signature[4:],[span,q])
        # Rounded sorting is only a set-comparison key, never ENTITY selection.
        key=lambda p:tuple(round(x,9) for x in p)
        nested(sorted(evaluated,key=key),sorted(positions,key=key));endpoint_count+=2
        edgeproof.append(dict(edge_index=edge['index'],curve_index=curve['index'],raw_finite_EDGE_domain=parameters,
            independently_evaluated_endpoints_cm=evaluated,raw_is_reversed=e[9]['value']))
    for item in proof['native_analytic_faces']:
        face=item['native_FACE'];f=raw[face['index']]['tokens'];surface=raw[f[7]['value']];s=surface['tokens']
        signature=item['complete_geometric_signature'][0];kind=signature[0];origin=s[3]['value']
        if kind=='Plane':
            normal=canonical(s[4]['value']);wanted=['Plane',normal,dot(normal,origin)]
        elif kind in ('Cylinder','Cone'):
            a=canonical(s[4]['value']);h=dot(origin,a);p=[x-h*y for x,y in zip(origin,a)];radius=math.hypot(*s[5]['value'])
            if kind=='Cylinder':near([s[9]['value']],[0.]);wanted=[kind,a,p,radius]
            else:
                m=math.tan(math.atan2(s[9]['value'],s[10]['value']))*dot(s[4]['value'],a)
                wanted=[kind,a,p,m,radius-m*h]
        elif kind=='Sphere':wanted=[kind,origin,s[4]['value']]
        else:
            assert kind=='Torus';wanted=[kind,origin,canonical(s[4]['value']),s[5]['value'],abs(s[6]['value'])]
        nested(signature,wanted)
        for loop in item['native_boundary_loops']:
            lid=loop['loop_index'];assert raw[lid]['tokens'][5]['value']==face['index'];loops.add(lid)
            cycle=loop['coedge_cycle'];assert raw[lid]['tokens'][4]['value']==cycle[0]
            for i,cid in enumerate(cycle):
                c=raw[cid]['tokens'];assert c[3]['value']==cycle[(i+1)%len(cycle)] and c[4]['value']==cycle[(i-1)%len(cycle)]
                assert c[8]['value']==lid;coedges.add(cid)
                if c[5]['value']==-1:
                    edge=raw[c[6]['value']]['tokens'];assert edge[8]['value']==-1 and len(cycle)==1
                else:
                    partner=raw[c[5]['value']]['tokens'];assert partner[5]['value']==cid and partner[6]['value']==c[6]['value'] and c[5]['value']!=cid
        carrierproof.append(dict(face_index=face['index'],surface_index=surface['index'],raw_kind=surface['name'],full_carrier_signature=wanted))
    counts=proof['counts'];assert len(edgeproof)==counts['edge'] and len(carrierproof)==counts['face'] and len(loops)==counts['loop'] and len(coedges)==counts['coedge']
    return dict(raw_carrier_proofs=carrierproof,raw_bounded_EDGE_proofs=edgeproof,
        complete_counts=counts,native_endpoint_evaluations=endpoint_count,
        mathematical_role_to_native_ENTITY_mapping=None,scope='Literal raw carrier coefficients, complete angular span/phase and finite domains plus reciprocal native loop topology; no coordinate entity assignment')


def analytic_reference(row):
    group,=row['native_source_provenance']['source_groups'];profile=group['mathematical_profile'];model=row['derived_geometry']
    if model['kind']=='Sphere':
        radius=profile['radius_cm'];volume=4*math.pi*radius**3/3;area=4*math.pi*radius**2
    elif model['kind']=='Torus':
        matrix=group['mathematical_inputs']['sketch_to_component_matrix'];center=[sum(matrix[4*i+j]*profile['center_cm'][j] for j in range(3))+matrix[4*i+3] for i in range(3)]
        axis=group['mathematical_inputs']['source_axis'];delta=sub(center,axis['origin_cm']);h=dot(delta,axis['direction']);major=math.hypot(*[x-h*a for x,a in zip(delta,axis['direction'])]);minor=profile['radius_cm']
        volume=2*math.pi**2*major*minor**2;area=4*math.pi**2*major*minor
    else:
        vertices=model['meridian_profile']['vertices'];radius=max(v['radial_distance_cm'] for v in vertices)
        height=max(v['axial_coordinate_cm'] for v in vertices)-min(v['axial_coordinate_cm'] for v in vertices)
        volume=math.pi*radius*radius*height/3;area=math.pi*radius*(radius+math.hypot(radius,height))
    near([model['volume_cm3'],model['surface_area_cm2']],[volume,area])
    return dict(independent_volume_cm3=volume,independent_surface_area_cm2=area)


def validate(root,zstd):
    baseline=json.loads(BASELINE.read_text());assert baseline['files']==list(FILES)
    source_report=json.loads((root/'revolve-source-operand-decoding.json').read_text());sources={s['archive']:s['expected_sources'] for s in source_report['samples']}
    samples=[];checks=[];guards=[];positives=[];saved={};models={}
    totals=dict(decoded_owners=0,rectangle_solids=0,singular_analytic_solids=0,explicit_unresolved=0,empty_controls=0,
        analytic_FACEs=0,EDGEs=0,VERTEXs=0,native_endpoint_evaluations=0,actual_API_analytic_bodies=0)
    for index,(archive,old) in enumerate(zip(FILES,baseline['before'])):
        data,records,features,member,members=load(root,archive,zstd);bindings=old['streams'][0]['body_blob_bindings'];before=copy.deepcopy((features,bindings,members))
        result=decode_revolve_reconstruction(data,records,features,member,members,bindings)
        assert (features,bindings,members)==before;checks.append(archive+' full caller purity')
        assert len(result['decoded'])==(1 if index<12 else 3 if index==12 else 0)
        assert len(result['unresolved'])==(2 if 13<=index<=15 else 1 if 16<=index<=20 else 0)
        checks.append(archive+' exact positive/unsupported/empty boundary')
        source_by_id={r['feature_object_id']:r for r in sources[archive]};independent=[]
        for row in result['decoded']:
            assert source_by_id[row['feature_object_id']]==row['native_source_provenance'];checks.append(archive+' full independent native source row '+str(row['feature_object_id']))
            sourceproof=raw_source(data,records,row);checks.append(archive+' literal source payloads and native-only effective axis '+str(row['feature_object_id']))
            cacheproof=raw_cache(members,row);checks.append(archive+' complete raw analytic carriers/domains/topology '+str(row['feature_object_id']))
            if index<12:
                reference=rectangle_source_reference(old,row['feature_object_id']);model=row['derived_geometry']
                near(model['effective_axis']['direction'],reference['effective_axis_direction']);near(model['angular_interval_radians'],reference['independently_derived_angular_interval_radians'])
                near([model['volume_cm3']],[reference['independently_derived_volume_cm3']])
                near(model['component_axis_aligned_bounds_cm']['minimum'],reference['independently_derived_bounds_cm'][0]);near(model['component_axis_aligned_bounds_cm']['maximum'],reference['independently_derived_bounds_cm'][1])
                totals['rectangle_solids']+=1
            else:reference=analytic_reference(row);totals['singular_analytic_solids']+=1
            checks.append(archive+' independent source volume/bounds or analytic area '+str(row['feature_object_id']))
            independent.append(dict(feature_object_id=row['feature_object_id'],native_source_verification=sourceproof,
                independent_source_geometry=reference,raw_native_geometry_verification=cacheproof))
            c=cacheproof['complete_counts'];totals['analytic_FACEs']+=c['face'];totals['EDGEs']+=c['edge'];totals['VERTEXs']+=c['vertex']
            totals['native_endpoint_evaluations']+=cacheproof['native_endpoint_evaluations'];totals['decoded_owners']+=1
            models[archive,row['feature_object_id']]=row['derived_geometry']
        if index in (0,2,12):saved[index]=(data,records,features,member,members,bindings,result)
        totals['explicit_unresolved']+=len(result['unresolved']);totals['empty_controls']+=not result['decoded'] and not result['unresolved']
        samples.append(dict(archive=archive,archive_sha256=sha(root/archive),expected_summary=result,independent_verification=independent))
    # API analytic classes/coefficients are corroboration after creator/BODY joins,
    # never an API face index or coordinate-based ENTITY pairing.
    truth=json.loads((root/'analytic-86a12b291d0a/ground_truth.json').read_text());analytic_rows=saved[12][-1]['decoded'];api=[]
    for row in analytic_rows:
        kind=row['derived_geometry']['kind'];label='Cone' if kind=='PolygonRevolve' else kind
        body,=[b for b in truth['bodies'] if b['name']==label];counts=row['native_cache_geometry_corroboration']['counts']
        assert [body['face_count'],body['edge_count'],body['vertex_count']]==[counts['face'],counts['edge'],counts['vertex']]
        carriers=row['native_cache_geometry_corroboration']['native_analytic_faces'];api_coefficients=[]
        for surface in body['surfaces']:
            target,=[f['native_surface'] for f in carriers if f['complete_geometric_signature'][0][0]==surface['kind']]
            a=target.get('analytic_surface',{})
            if surface['kind']=='Sphere':
                near(surface['origin'],a['raw_origin']);near([surface['radius']],[a['raw_radius']])
            elif surface['kind']=='Torus':
                near(surface['origin'],a['raw_origin']);near(canonical(surface['axis']),canonical(a['axis']))
                near([surface['majorRadius'],surface['minorRadius']],[a['raw_major_radius'],abs(a['raw_minor_radius'])])
            elif surface['kind']=='Cone':
                near(surface['origin'],a['raw_origin']);near(canonical(surface['axis']),canonical(a['axis']))
                near([surface['radius'],surface['halfAngle']],[a['raw_radius'],a['half_angle_radians']])
            else:
                near(canonical(surface['normal']),canonical(target['normal']))
                near([dot(target['normal'],surface['origin'])],[dot(target['normal'],target['raw_origin'])])
            api_coefficients.append(copy.deepcopy(surface))
        if label=='Cone':
            actual=sorted(body['vertex_positions_cm']);native=sorted(v['native_POINT']['raw_origin'] for v in row['native_cache_geometry_corroboration']['native_vertices']);nested(actual,native)
        api.append(dict(feature_object_id=row['feature_object_id'],saved_API_body_name=label,actual_counts=[body['face_count'],body['edge_count'],body['vertex_count']],actual_API_carriers=api_coefficients,API_ENTITY_assignment=None,
            scope='Full analytic carrier coefficient collection after native creator/BODY qualification, not API face-handle identity'))
        totals['actual_API_analytic_bodies']+=1
    data,records,features,member,members,bindings,original=saved[2];row,=original['decoded'];name=row['history_blob_member'];blob=members[name];raw=inspect_asm(blob)['records'];proof=row['native_cache_geometry_corroboration']
    def reject(label,changed,expected,context=saved[2]):
        d,r,f,m,ms,b,out=context;target_name=out['decoded'][0]['history_blob_member'];new=dict(ms);new[target_name]=changed
        result=decode_revolve_reconstruction(d,r,f,m,new,b)
        target=out['decoded'][0]['feature_object_id'];assert not any(x['feature_object_id']==target for x in result['decoded'])
        reason=next(x['reason'] for x in result['unresolved'] if x['feature_object_id']==target);assert expected in reason,(label,reason)
        guards.append(dict(name=label,reason=reason,passed=True))
    arc=next(p for p in proof['native_bounded_edges'] if p['complete_geometric_signature'][0]=='CircleArc');edge=raw[arc['native_EDGE']['index']];curve=raw[edge['tokens'][8]['value']]
    # Same endpoints, opposite angular window: local endpoint evaluations still
    # match; only the whole bounded domain distinguishes the complementary arc.
    p,q=edge['tokens'][4]['value'],edge['tokens'][6]['value'];changed=altered_blob(blob,edge,4,q);changed=altered_blob(changed,edge,6,p+2*math.pi)
    reject('Complementary circular domain preserves endpoints but changes whole window',changed,'complete carrier/bounded nested geometry')
    cylinder=next(f for f in proof['native_analytic_faces'] if f['complete_geometric_signature'][0][0]=='Cylinder');s=raw[cylinder['native_surface']['index']]
    reject('Lateral Cylinder radius differs from full circular boundary',altered_blob(blob,s,5,[1.01*x for x in s['tokens'][5]['value']]),'Cylinder generatrix radius')
    plane=next(f for f in proof['native_analytic_faces'] if f['complete_geometric_signature'][0][0]=='Plane');s=raw[plane['native_surface']['index']]
    normal=s['tokens'][4]['value'];origin=s['tokens'][3]['value'];moved=[o+.01*n for o,n in zip(origin,normal)]
    reject('Plane carrier shifted while native boundary stays fixed',altered_blob(blob,s,3,moved),'Plane complete boundary containment')
    line=next(e for e in proof['native_bounded_edges'] if e['complete_geometric_signature'][0]=='LineSegment');l=raw[line['native_curve']['index']]
    moved=list(l['tokens'][3]['value']);direction=l['tokens'][4]['value'];perpendicular=cross(direction,[1.,0.,0.])
    if math.hypot(*perpendicular)<.1:perpendicular=cross(direction,[0.,1.,0.])
    moved=[p+.03*d for p,d in zip(moved,perpendicular)]
    reject('Whole Line carrier/domain fails its typed endpoints',altered_blob(blob,l,3,moved),'complete native Line domain endpoints')
    coedge=raw[edge['tokens'][7]['value']]
    reject('True self-partner pointer remains typed but not reciprocal other-use',altered_blob(blob,coedge,5,coedge['index']),'other-use partner')
    other=next(c for f in proof['native_analytic_faces'] for loop in f['native_boundary_loops'] for c in loop['coedge_cycle'] if raw[c]['tokens'][6]['value']!=edge['index'])
    reject('Nonmember EDGE head pointer',altered_blob(blob,edge,7,other),'EDGE head incidence')
    # Sphere/Torus/Cone guards use independent owned BODY routes in the same blob.
    context=saved[12];arows=context[-1]['decoded'];aname=arows[0]['history_blob_member'];ab=context[4][aname];ar=inspect_asm(ab)['records']
    sphere=next(x for x in arows if x['derived_geometry']['kind']=='Sphere');sf=ar[sphere['native_cache_geometry_corroboration']['native_analytic_faces'][0]['native_surface']['index']]
    # reject() targets the first Sphere owner for this context.
    reject('Complete Sphere radius coefficient differs',altered_blob(ab,sf,4,sf['tokens'][4]['value']+.1),'complete carrier/bounded nested geometry',context)
    cone=next(x for x in arows if x['derived_geometry']['profile_kind']=='Polygon' and len(x['derived_geometry']['meridian_profile']['vertices'])==3)
    apex=next(x for x in cone['native_cache_geometry_corroboration']['native_bounded_edges'] if x['complete_geometric_signature'][0]=='PointSingularity')
    ce=ar[apex['native_EDGE']['index']];cc=ar[ce['tokens'][7]['value']]
    selected=dict(decoded=[cone]);ccontext=(*context[:-1],selected)
    reject('Singular apex COEDGE cannot invent a self partner',altered_blob(ab,cc,5,cc['index']),'singular EDGE/COEDGE framing',ccontext)
    coneface=next(f for f in cone['native_cache_geometry_corroboration']['native_analytic_faces'] if f['complete_geometric_signature'][0][0]=='Cone')
    cs=ar[coneface['native_surface']['index']];theta=math.atan2(cs['tokens'][9]['value'],cs['tokens'][10]['value'])+.01
    changed=altered_blob(ab,cs,9,math.sin(theta));changed=altered_blob(changed,cs,10,math.cos(theta))
    reject('Cone full radial slope disagrees with apex and full base circle',changed,'Cone singular point zero radius',ccontext)
    torus=next(x for x in arows if x['derived_geometry']['kind']=='Torus');ts=ar[torus['native_cache_geometry_corroboration']['native_analytic_faces'][0]['native_surface']['index']]
    tcontext=(*context[:-1],dict(decoded=[torus]))
    reject('Whole Torus tube radius coefficient differs',altered_blob(ab,ts,6,ts['tokens'][6]['value']+.02),'complete carrier/bounded nested geometry',tcontext)
    # A 2pi parameter translation and chart flag change preserve complete geometry;
    # literals remain different and no native traversal meaning is inferred.
    changed=altered_blob(blob,edge,4,p+2*math.pi);changed=altered_blob(changed,edge,6,q+2*math.pi)
    new=dict(members);new[name]=changed;actual=decode_revolve_reconstruction(data,records,features,member,new,bindings)
    assert len(actual['decoded'])==1 and not actual['unresolved'];assert actual['decoded'][0]['derived_geometry']==row['derived_geometry']
    positives.append(dict(name='Circular native parameter seam shift retained; full geometric window unchanged',passed=True))
    a=models[FILES[8],296];b=models[FILES[9],296]
    near(a['effective_axis']['direction'],b['effective_axis']['direction']);near([a['volume_cm3']],[b['volume_cm3']])
    assert a['source_axis']['direction']==[-x for x in b['source_axis']['direction']]
    positives.append(dict(name='Reversed native SketchLine axis gives same source-relative physical geometry',passed=True))
    return dict(scope='Fixed23 source-only Revolve construction and complete analytic raw topology/carrier proof, no main/live calls',
        baseline_commit=baseline['baseline_commit'],baseline_sha256=sha(BASELINE),samples=samples,totals=totals,
        checks=checks,check_count=len(checks),guards=guards,guard_count=len(guards),positive_controls=positives,
        actual_API_analytic_corroboration=api,API_geometry_for_rectangle_cases='Not captured; saved API axes/controls are retained independently',
        acquisition_main_calls=0,live_API_calls=0,
        source_sha256={n:sha(root/n) for n in ('decode_revolve_reconstruction.py','validate_revolve_reconstruction.py',
            'decode_revolve_source_operands.py','decode_revolve_geometry.py','decode_extrusion_reconstruction.py','validate_extrusion_reconstruction.py')})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library',required=True);args=parser.parse_args()
    report=validate(ROOT,args.zstd_library)
    (ROOT/'revolve-reconstruction-decoding.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(totals=report['totals'],checks=report['check_count'],guards=report['guard_count'])))
