"""Independent source integrals and complete raw bounded-carrier checks; no main/live."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

from asm_records import inspect_asm
from decode_trimmed_extrusion_reconstruction import decode_trimmed_extrusion_reconstruction
from validate_mesh_remesh import load
from validate_extrusion_reconstruction import altered_blob,near,raw_source
from validate_trimmed_extrusion_reconstruction_integration import FILES,source_reference,saved_API_result

ROOT=Path(__file__).resolve().parent
BASELINE=Path('/private/tmp/fusion-trimmed-extrusion-reconstruction-baseline.json')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def sub(a,b):return [x-y for x,y in zip(a,b)]
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def sort_points(points):return sorted(points,key=lambda p:tuple(round(x,9) for x in p))


def raw_carriers(members,row):
    """Evaluate raw serialized coefficients, not published residual assertions."""
    raw=inspect_asm(members[row['history_blob_member']])['records']
    proof=row['native_cache_geometry_corroboration'];identity=proof['identity_provenance'];model=row['derived_geometry']
    curves={p['role_key']:p for p in model['boundary_curves']};reports=[];seen_edges=set();seen_faces=set();endpoints=0
    base,top=identity['base_cap_face_index'],identity['top_cap_face_index']
    loop_by_face={l['face_index']:l for l in identity['loops']}
    def vertex(v):return raw[raw[v]['tokens'][5]['value']]['tokens'][3]['value']
    def curve(edge_id):
        e=raw[edge_id]['tokens'];r=raw[e[8]['value']];return e,r,r['tokens']
    def incidence(edge_id):
        matches=[r for r in raw if r['name']=='coedge' and r['tokens'][6]['value']==edge_id]
        # Restrict to exact BODY-owned loop table before geometric inspection.
        matches=[r for r in matches if r['tokens'][8]['value'] in {l['loop_index'] for l in identity['loops']}]
        assert len(matches)==2 and matches[0]['tokens'][5]['value']==matches[1]['index']
        assert matches[1]['tokens'][5]['value']==matches[0]['index']
        return {raw[r['tokens'][8]['value']]['tokens'][5]['value'] for r in matches}
    for part in proof['portion_boundaries']:
        bound=part['identity'];derived=curves[part['role_key']]
        assert incidence(bound['base_edge_index'])=={base,bound['side_face_index']}
        assert incidence(bound['top_edge_index'])=={top,bound['side_face_index']}
        windows=[]
        for eid,layer in zip((bound['base_edge_index'],bound['top_edge_index']),derived['layer_curves']):
            e,r,t=curve(eid);m=layer['geometry'];params=[e[4]['value'],e[6]['value']]
            native_positions=[vertex(e[k]['value']) for k in (3,5)];seen_edges.add(eid)
            if m['kind']=='CircleArc':
                assert r['name']=='ellipse-curve' and t[6]['value']==1.
                center,normal,reference=[t[k]['value'] for k in (3,4,5)]
                radius=math.hypot(*reference);u=[x/radius for x in reference];v=cross(normal,u)
                near(center,m['center_cm']);near([radius],[m['radius_cm']])
                a,b=m['angle_interval_radians'];du=[dot(m['reference_u'],basis) for basis in (u,v)]
                dv=[dot(m['reference_v'],basis) for basis in (u,v)]
                orientation=1 if dot(normal,m['unit_axis'])>=0 else -1
                near(normal,[orientation*x for x in m['unit_axis']]);near([dot(u,u),dot(u,normal)],[1.,0.])
                # Full Fourier coefficient equality plus bounded angle window;
                # same endpoints alone cannot establish a major/complement arc.
                phase=math.atan2(du[1],du[0])
                near(du,[math.cos(phase),math.sin(phase)])
                near(dv,[-orientation*math.sin(phase),orientation*math.cos(phase)])
                near([abs(params[1]-params[0])],[b-a])
                native_middle=sum(params)/2;source_middle=orientation*(a+b)/2+phase
                near([math.cos(native_middle),math.sin(native_middle)],[math.cos(source_middle),math.sin(source_middle)])
                evaluated=[[o+radius*(math.cos(p)*x+math.sin(p)*y) for o,x,y in zip(center,u,v)] for p in params]
                windows.append(dict(edge_index=eid,kind='CircleArc',raw_EDGE_parameters=params,
                    independent_full_parameter_relation=dict(scale=orientation,phase_radians=phase),span_radians=b-a))
            else:
                assert r['name']=='straight-curve';origin,direction=t[3]['value'],t[4]['value']
                wanted=sub(m['end_cm'],m['start_cm']);length=math.hypot(*wanted);wanted=[x/length for x in wanted]
                sign=1 if dot(direction,wanted)>=0 else -1
                near(direction,[sign*x for x in wanted]);relative=sub(m['start_cm'],origin);d=dot(relative,direction)
                near([x-d*y for x,y in zip(relative,direction)],[0.,0.,0.])
                evaluated=[[o+p*x for o,x in zip(origin,direction)] for p in params]
                for x,y in zip(sort_points(evaluated),sort_points([m['start_cm'],m['end_cm']])):near(x,y)
                windows.append(dict(edge_index=eid,kind='LineSegment',raw_EDGE_parameters=params,full_direction_sign=sign))
            for x,y in zip(sort_points(evaluated),sort_points(native_positions)):near(x,y)
            endpoints+=2
        f=raw[bound['side_face_index']]['tokens'];s=raw[f[7]['value']];carrier=derived['side_carrier'];st=s['tokens']
        assert f[4]['value']==loop_by_face[bound['side_face_index']]['loop_index']
        if carrier['kind']=='Cylinder':
            assert s['name']=='cone-surface'
            near([math.hypot(*st[5]['value']),st[6]['value'],st[9]['value']],[carrier['radius_cm'],1.,0.])
            axis=st[4]['value'];sign=1 if dot(axis,carrier['unit_axis'])>=0 else -1
            near(axis,[sign*x for x in carrier['unit_axis']]);delta=sub(st[3]['value'],carrier['axis_origin_cm']);height=dot(delta,axis)
            near([x-height*y for x,y in zip(delta,axis)],[0.,0.,0.])
        else:
            assert s['name']=='plane-surface';n=st[4]['value'];sign=1 if dot(n,carrier['unit_normal'])>=0 else -1
            near(n,[sign*x for x in carrier['unit_normal']]);near([dot(n,st[3]['value'])],[sign*carrier['plane_constant_cm']])
        seen_faces.add(bound['side_face_index']);reports.append(dict(role_key=part['role_key'],fixed_side_FACE=bound['side_face_index'],complete_window_proofs=windows))
    connector_pairs=[]
    for connector in proof['connector_edges']:
        c=connector['incidence'];eid=c['edge_index'];e,r,t=curve(eid)
        assert r['name']=='straight-curve' and {e[3]['value'],e[5]['value']}=={c['base_vertex_index'],c['top_vertex_index']}
        parameters=[e[4]['value'],e[6]['value']];evaluated=[[o+p*d for o,d in zip(t[3]['value'],t[4]['value'])] for p in parameters]
        for x,y in zip(sort_points(evaluated),sort_points([vertex(e[3]['value']),vertex(e[5]['value'])])):near(x,y)
        connector_pairs.append([vertex(c['base_vertex_index']),vertex(c['top_vertex_index'])]);seen_edges.add(eid);endpoints+=2
    expected=[[r['lower_cm'],r['upper_cm']] for r in model['connector_segments']]
    for pair,wanted in zip(sorted(connector_pairs,key=lambda r:tuple(round(x,9) for p in r for x in p)),sorted(expected,key=lambda r:tuple(round(x,9) for p in r for x in p))):
        for p,q in zip(pair,wanted):near(p,q)
    cap_proofs=[]
    for face_id,cap in zip((base,top),model['caps']):
        f=raw[face_id]['tokens'];s=raw[f[7]['value']];assert s['name']=='plane-surface'
        origin,normal=[s['tokens'][k]['value'] for k in (3,4)];sign=1 if dot(normal,cap['unit_outward_normal'])>=0 else -1
        near(normal,[sign*x for x in cap['unit_outward_normal']]);near([dot(normal,origin)],[sign*cap['plane_constant_cm']])
        for vertex_id in loop_by_face[face_id]['vertex_cycle']:near([dot(normal,sub(vertex(vertex_id),origin))],[0.])
        cap_proofs.append(dict(face_index=face_id,complete_boundary_edge_indices=loop_by_face[face_id]['edge_indices'],normal_sign=sign))
        seen_faces.add(face_id)
    assert len(seen_edges)==proof['counts']['edge'] and len(seen_faces)==proof['counts']['face']
    # All raw heads/partners are independently checked, including untagged connectors.
    for l in identity['loops']:
        cycle=l['coedge_cycle'];assert raw[l['loop_index']]['tokens'][4]['value']==cycle[0]
        for i,c in enumerate(cycle):
            t=raw[c]['tokens'];assert t[3]['value']==cycle[(i+1)%len(cycle)] and t[4]['value']==cycle[(i-1)%len(cycle)]
            assert raw[t[5]['value']]['tokens'][5]['value']==c and t[5]['value']!=c
    for e in seen_edges:
        t=raw[e]['tokens'];assert raw[t[7]['value']]['tokens'][6]['value']==e
    return dict(portion_carrier_and_window_proofs=reports,cap_plane_proofs=cap_proofs,
        complete_EDGE_count=len(seen_edges),complete_FACE_count=len(seen_faces),native_endpoint_evaluations=endpoints,
        mathematical_endpoint_to_native_VERTEX_assignment=None,scope='Raw serialized complete coefficients/windows and exact reciprocal topology after source tuple identities; no sample-only or coordinate identity proof')


def validate(root,zstd):
    baseline=json.loads(BASELINE.read_text());assert baseline['files']==list(FILES)
    source_report=json.loads((root/'trimmed-extrusion-source-decoding.json').read_text())
    sources={s['archive']:s['expected_sources'] for s in source_report['samples']}
    samples=[];checks=[];guards=[];positives=[];saved={}
    totals=dict(decoded_owners=0,empty_controls=0,source_portions=0,arc_portions=0,line_portions=0,
        native_EDGEs=0,native_FACEs=0,native_ENDPOINT_evaluations=0,actual_API_bounds_and_volumes=0)
    for i,(archive,old) in enumerate(zip(FILES,baseline['before'])):
        data,records,features,member,members=load(root,archive,zstd);bindings=old['streams'][0]['body_blob_bindings']
        before=copy.deepcopy((features,bindings,members))
        result=decode_trimmed_extrusion_reconstruction(data,records,features,member,members,bindings)
        assert not result['unresolved'],(archive,result['unresolved'])
        assert (features,bindings,members)==before;checks.append(archive+' caller purity')
        assert len(result['decoded'])==(1 if i<15 else 0);checks.append(archive+' exact native tuple candidate gate')
        independent=[]
        for row in result['decoded']:
            assert sources[archive]==[row['native_source_provenance']];checks.append(archive+' full independently qualified native source row')
            group,by,matrix,points,axis=raw_source(data,records,row)
            for item in group['derived_source_portions']:
                ref=item['stored_profile_reference'];definition=by[group['native_profile_selection']['profile_loop_definition_object_id']]
                offset=definition.body+ref['stored_tuple_offset_in_definition']
                import struct
                assert struct.unpack_from('<IQQIIIQ',data,offset)==tuple(ref['stored_tuple_fields'])
            checks.append(archive+' raw complete selected tuple replay and source frame/POINTs')
            reference=source_reference(old);model=row['derived_geometry']
            near([model['profile']['area_cm2'],model['volume_cm3']],[reference['independent_profile_area_cm2'],reference['independent_volume_cm3']])
            near(model['component_axis_aligned_bounds_cm']['minimum'],reference['independent_bounds_cm'][0]);near(model['component_axis_aligned_bounds_cm']['maximum'],reference['independent_bounds_cm'][1])
            checks.append(archive+' independently enumerated source integral and analytic bounds')
            rawproof=raw_carriers(members,row);checks.append(archive+' complete raw topology/carriers/windows/endpoints')
            api=saved_API_result(archive,reference);checks.append(archive+' independent captured API volume/bounds after native joins')
            independent.append(dict(independent_source_reference=reference,raw_cache_proof=rawproof,saved_API_corroboration=api))
            totals['decoded_owners']+=1;totals['source_portions']+=len(model['boundary_curves'])
            totals['arc_portions']+=sum(c['kind']=='CircleArc' for c in model['boundary_curves'])
            totals['line_portions']+=sum(c['kind']=='LineSegment' for c in model['boundary_curves'])
            totals['native_EDGEs']+=rawproof['complete_EDGE_count'];totals['native_FACEs']+=rawproof['complete_FACE_count']
            totals['native_ENDPOINT_evaluations']+=rawproof['native_endpoint_evaluations'];totals['actual_API_bounds_and_volumes']+=1
            if i in (0,6):saved[i]=(data,records,features,member,members,bindings,row)
        if not result['decoded']:totals['empty_controls']+=1
        samples.append(dict(archive=archive,archive_sha256=sha(root/archive),expected_summary=result,independent_verification=independent))
    data,records,features,member,members,bindings,row=saved[0];name=row['history_blob_member'];blob=members[name];raw=inspect_asm(blob)['records']
    proof=row['native_cache_geometry_corroboration'];part=proof['portion_boundaries'][0]
    top=part['identity']['top_edge_index'];edge=raw[top];curve=raw[edge['tokens'][8]['value']]
    def reject(label,changed,expected,context=None):
        d,r,f,m,ms,b,_=context or saved[0];newmembers=dict(ms);newmembers[row['history_blob_member'] if context is None else context[-1]['history_blob_member']]=changed
        actual=decode_trimmed_extrusion_reconstruction(d,r,f,m,newmembers,b)
        assert not actual['decoded'] and actual['unresolved'],(label,actual)
        reason=actual['unresolved'][0]['reason'];assert expected in reason,(label,expected,reason)
        guards.append(dict(name=label,reason=reason,passed=True))
    reject('Top arc finite span differs despite unchanged source recipe',altered_blob(blob,edge,6,edge['tokens'][6]['value']+.1),'complete bounded arc span')
    changed=altered_blob(blob,edge,4,edge['tokens'][4]['value']+.1);changed=altered_blob(changed,edge,6,edge['tokens'][6]['value']+.1)
    reject('Same arc span but different whole window',changed,'bounded arc midpoint phase')
    changed=altered_blob(blob,edge,4,edge['tokens'][6]['value']);changed=altered_blob(changed,edge,6,edge['tokens'][4]['value']+2*math.pi)
    reject('Complementary arc has same endpoint set but wrong span',changed,'complete bounded arc span')
    reject('Top arc circular carrier radius differs',altered_blob(blob,curve,5,[1.01*x for x in curve['tokens'][5]['value']]),'full circular radii')
    cylinder=raw[part['native_side_FACE']['surface_index']]
    reject('Whole side Cylinder radial coefficient differs',altered_blob(blob,cylinder,5,[1.01*x for x in cylinder['tokens'][5]['value']]),'whole Cylinder radius')
    plane=raw[proof['caps'][1]['native_FACE']['surface_index']];angle=1e-5
    changed=altered_blob(blob,plane,4,[math.sin(angle),0.,math.cos(angle)])
    length=math.hypot(*plane['tokens'][5]['value']);changed=altered_blob(changed,plane,5,[length*math.cos(angle),0.,-length*math.sin(angle)])
    reject('Small coherent cap Plane rotation fails vector coefficients',changed,'cap Plane full normal coefficients')
    connector=proof['connector_edges'][0];cid=connector['incidence']['edge_index'];ce=raw[cid];line=raw[ce['tokens'][8]['value']]
    moved=list(line['tokens'][3]['value']);moved[0]+=.1
    reject('Connector Line carrier displaced from its typed endpoints',altered_blob(blob,line,3,moved),'whole Line locus')
    coedge=raw[ce['tokens'][7]['value']]
    reject('Actual self partner pointer, with valid typed target',altered_blob(blob,coedge,5,coedge['index']),'other-use partner reciprocity')
    other=next(c for l in proof['identity_provenance']['loops'] for c in l['coedge_cycle'] if raw[c]['tokens'][6]['value']!=cid)
    reject('Actual nonmember EDGE head',altered_blob(blob,ce,7,other),'other-use partner reciprocity')
    reject('Huge finite top circle center',altered_blob(blob,curve,3,[1e150,0.,1.]),'full circle center')
    # Raw Plane chart flag has no effect on the mathematical carrier proof.
    changed=altered_blob(blob,plane,6,not plane['tokens'][6]['value']);ms=dict(members);ms[name]=changed
    actual=decode_trimmed_extrusion_reconstruction(data,records,features,member,ms,bindings)
    assert len(actual['decoded'])==1 and not actual['unresolved']
    assert actual['decoded'][0]['native_cache_geometry_corroboration']['caps'][1]['plane_corroboration']['native_Plane']['is_v_reversed']!=proof['caps'][1]['plane_corroboration']['native_Plane']['is_v_reversed']
    assert actual['decoded'][0]['derived_geometry']==row['derived_geometry']
    positives.append(dict(name='Literal cap Plane chart flag change retained without native UV interpretation',passed=True))
    injected=copy.deepcopy(features)
    for f in injected:f['invented_profile_annotations']={'cached_points_as_inputs':False}
    assert decode_trimmed_extrusion_reconstruction(data,records,injected,member,members,bindings)==samples[0]['expected_summary']
    positives.append(dict(name='Caller annotations do not supply source geometry or candidate identities',passed=True))
    return dict(scope='Fixed19 native selected-portion/source-integral/full-carrier/window/topology proof; no main or live calls',
        baseline_commit=baseline['baseline_commit'],baseline_sha256=sha(BASELINE),samples=samples,totals=totals,
        checks=checks,check_count=len(checks),guards=guards,guard_count=len(guards),positive_controls=positives,
        acquisition_main_calls=0,live_API_calls=0,
        source_sha256={n:sha(root/n) for n in ('decode_trimmed_extrusion_reconstruction.py','validate_trimmed_extrusion_reconstruction.py',
            'decode_trimmed_extrusion_geometry.py','decode_trimmed_extrusion_sources.py','decode_extrusion_source_operands.py',
            'decode_extrusion_reconstruction.py','validate_extrusion_reconstruction.py')})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library',required=True);args=parser.parse_args()
    report=validate(ROOT,args.zstd_library)
    (ROOT/'trimmed-extrusion-reconstruction-decoding.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(totals=report['totals'],checks=report['check_count'],guards=report['guard_count'])))
