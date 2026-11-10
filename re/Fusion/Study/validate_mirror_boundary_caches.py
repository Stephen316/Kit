"""Independent native incidence and analytic-coefficient checks for Mirror caches."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_brep import decode_topology
from decode_circular_feature_caches import _face_names
from decode_mirror_boundary_caches import decode_mirror_boundary_caches
from decode_mirror_cache_reflections import decode_mirror_cache_reflections
from decode_sketch import decode_sketches
from decode_placement import decode_placement
from validate_mesh_remesh import load

ROOT=Path(__file__).resolve().parent
FILES=tuple('mirrorfeatures-1ffa1b15c612/'+s+'.f3d' for s in (
    'body_brep_face_plane','feature_optimized','feature_identical','feature_adjust'))+(
    'tools-fda3948848f4/Mirror.f3d','bodyselections-62e42366c722/mirror_two_bodies_plane.f3d',
    'remainingbodyinputs-7b3357274e85/mirror_two_features.f3d','remainingbodyinputs-7b3357274e85/mirror_boss_faces.f3d',
    'datummirrorsupport-3a854f334428/offset_selected_support.f3d','surfacetools-856ca50cf4c7/offset_positive.f3d',
    'surfacebounds-ac801bb00fae/untrim_all.f3d','pathpatterns-de9857f6a1bc/spacing.f3d')


def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def subtract(a,b):return [x-y for x,y in zip(a,b)]
def maximum(values):
    assert all(math.isfinite(v) for v in values)
    return max([0.]+[abs(v) for v in values])


def independent_geometry(reflection,members):
    """Use raw nodes plus prior fixed names/vertices, never new-reader transports."""
    blob=members[reflection['history_blob_member']];parsed=inspect_asm(blob);top=decode_topology(parsed)
    assert not top['unresolved'];nodes={n['index']:n for n in top['nodes']};graphs={g['body_index']:g for g in top['body_graphs']}
    proofs={p['native_body_object_id']:p for p in reflection['complete_body_naming_proofs']}
    H=reflection['computed_householder_matrix'];R=[H[4*i:4*i+3] for i in range(3)];T=[H[3],H[7],H[11]]
    def vector(v):return [dot(r,v) for r in R]
    def position(p):return [v+t for v,t in zip(vector(p),T)]
    copies=[]
    for oldcopy in reflection['cache_body_copies']:
        source=oldcopy['source_native_body_object_id'];target=oldcopy['result_native_body_object_id']
        sg=graphs[proofs[source]['asm_body_index']];tg=graphs[proofs[target]['asm_body_index']]
        sn=_face_names(blob,parsed,sg)['names'];tn=_face_names(blob,parsed,tg)['names']
        byname={tuple(v['name_key']):i for i,v in tn.items()};assert len(byname)==6
        fmap={i:byname[tuple(v['name_key'])] for i,v in sn.items()};assert set(fmap.values())==set(tg['face_indices'])
        vmap={v['source']['vertex_index']:v['target']['vertex_index'] for v in oldcopy['vertex_correspondence']}
        assert set(vmap)==set(sg['vertex_indices']) and set(vmap.values())==set(tg['vertex_indices'])
        target_edges={frozenset((nodes[e]['start_vertex_index'],nodes[e]['end_vertex_index'])):e for e in tg['edge_indices']}
        assert len(target_edges)==12
        emap={e:target_edges[frozenset((vmap[nodes[e]['start_vertex_index']],vmap[nodes[e]['end_vertex_index']]))] for e in sg['edge_indices']}
        assert set(emap.values())==set(tg['edge_indices'])
        lmap={};cmap={}
        for loop in sg['loop_indices']:
            candidates=[i for i in tg['loop_indices'] if nodes[i]['face_index']==fmap[nodes[loop]['face_index']]]
            assert len(candidates)==1;lmap[loop]=candidates[0]
        for cid in sg['coedge_indices']:
            c=nodes[cid];candidates=[i for i in tg['coedge_indices'] if nodes[i]['edge_index']==emap[c['edge_index']] and nodes[i]['loop_index']==lmap[c['loop_index']]]
            assert len(candidates)==1;cmap[cid]=candidates[0]
        assert len(set(cmap.values()))==len(tg['coedge_indices'])
        facefacts=[]
        for sf,tf in fmap.items():
            a,b=nodes[sf],nodes[tf];s,t=nodes[a['surface_index']],nodes[b['surface_index']]
            assert s['kind']==t['kind']=='plane-surface'
            O,U,N=s['raw_origin'],s['stored_reference_axis'],s['normal'];Q,A,M=t['raw_origin'],t['stored_reference_axis'],t['normal']
            V=cross(N,U);B=cross(M,A)
            assert maximum([dot(U,U)-1,dot(N,N)-1,dot(U,N),dot(A,A)-1,dot(M,M)-1,dot(A,M)])<1e-10
            RU,RV=vector(U),vector(V);delta=subtract(position(O),Q)
            linear=[[dot(A,RU),dot(A,RV)],[dot(B,RU),dot(B,RV)]];offset=[dot(A,delta),dot(B,delta)]
            coeff=[subtract(delta,[A[i]*offset[0]+B[i]*offset[1] for i in range(3)]),
                subtract(RU,[A[i]*linear[0][0]+B[i]*linear[1][0] for i in range(3)]),
                subtract(RV,[A[i]*linear[0][1]+B[i]*linear[1][1] for i in range(3)])]
            assert maximum([x for v in coeff for x in v])<1e-9
            points=[]
            for sv,tv in vmap.items():
                # FACE membership is incidence of already named FACE signatures,
                # not a geometric containment test selecting a correspondence.
                incident=[v for v in oldcopy['vertex_correspondence'] if v['source']['vertex_index']==sv][0]['incident_face_name_keys']
                if list(sn[sf]['name_key']) not in incident:continue
                sp=nodes[nodes[sv]['point_index']]['raw_origin'];tp=nodes[nodes[tv]['point_index']]['raw_origin']
                local=[dot(U,subtract(sp,O)),dot(V,subtract(sp,O))]
                source_evaluated=[O[i]+U[i]*local[0]+V[i]*local[1] for i in range(3)]
                assert maximum(subtract(source_evaluated,sp))<1e-9
                mapped=[dot(r,local)+z for r,z in zip(linear,offset)]
                evaluated=[Q[i]+A[i]*mapped[0]+B[i]*mapped[1] for i in range(3)]
                residual=maximum(subtract(evaluated,tp));assert residual<1e-9
                points.append(dict(source_vertex_index=sv,target_vertex_index=tv,source_frame_coordinates=local,
                    target_frame_coordinates=mapped,source_point=sp,evaluated_source_point=source_evaluated,
                    target_point=tp,evaluated_target_point=evaluated,residual_raw=residual))
            assert len(points)==4
            facefacts.append(dict(source_face_index=sf,target_face_index=tf,name_key=list(sn[sf]['name_key']),
                source_surface=s,target_surface=t,linear=linear,offset=offset,coefficient_residual_vectors=coeff,boundary_points=points,
                raw_flags=dict(source_face_reversed=a['is_reversed'],target_face_reversed=b['is_reversed'],
                    source_plane_v_reversed=s['is_v_reversed'],target_plane_v_reversed=t['is_v_reversed'])))
        edgefacts=[]
        for se,te in emap.items():
            e,t=nodes[se],nodes[te];sc,tc=nodes[e['curve_index']],nodes[t['curve_index']]
            assert sc['kind']==tc['kind']=='straight-curve'
            source_faces={nodes[nodes[c]['loop_index']]['face_index'] for c in sg['coedge_indices'] if nodes[c]['edge_index']==se}
            target_faces={nodes[nodes[c]['loop_index']]['face_index'] for c in tg['coedge_indices'] if nodes[c]['edge_index']==te}
            assert {fmap[i] for i in source_faces}==target_faces and len(source_faces)==2
            sd,td=sc['direction'],tc['direction'];so,to=sc['raw_origin'],tc['raw_origin'];Hd=vector(sd);delta=subtract(position(so),to)
            scale=dot(td,Hd)/dot(td,td);shift=dot(td,delta)/dot(td,td)
            assert maximum(subtract(Hd,[scale*v for v in td])+subtract(delta,[shift*v for v in td]))<1e-9
            domain=[e['start_parameter'],e['end_parameter']];target_domain=[t['start_parameter'],t['end_parameter']]
            transported=[scale*x+shift for x in domain]
            assert maximum(subtract(sorted(transported),sorted(target_domain)))<1e-9
            samples=[]
            for parameter in (domain[0],sum(domain)/2,domain[1]):
                q=scale*parameter+shift;sp=[o+parameter*v for o,v in zip(so,sd)];tp=[o+q*v for o,v in zip(to,td)]
                residual=maximum(subtract(position(sp),tp));assert residual<1e-9
                samples.append(dict(source_parameter=parameter,target_parameter=q,source_point=sp,target_point=tp,residual_raw=residual))
            source_vertices=[nodes[nodes[i]['point_index']]['raw_origin'] for i in (e['start_vertex_index'],e['end_vertex_index'])]
            target_vertices=[nodes[nodes[i]['point_index']]['raw_origin'] for i in (t['start_vertex_index'],t['end_vertex_index'])]
            for field,verts in (('source_point',source_vertices),('target_point',target_vertices)):
                evaluated=[samples[0][field],samples[-1][field]]
                assert all(any(maximum(subtract(p,v))<1e-9 for v in verts) for p in evaluated)
                assert all(any(maximum(subtract(v,p))<1e-9 for p in evaluated) for v in verts)
            edgefacts.append(dict(source_edge_index=se,target_edge_index=te,source_curve=sc,target_curve=tc,
                scale=scale,offset=shift,source_domain=domain,target_domain=target_domain,transported_domain=transported,
                mapped_endpoint_vertex_indices=[vmap[e['start_vertex_index']],vmap[e['end_vertex_index']]],samples=samples))
        coedgefacts=[]
        for sc,tc in cmap.items():
            a,b=nodes[sc],nodes[tc]
            assert cmap[a['partner_index']]==b['partner_index']
            coedgefacts.append(dict(source_coedge_index=sc,target_coedge_index=tc,
                mapped_next=cmap[a['next_coedge_index']],mapped_previous=cmap[a['previous_coedge_index']],
                target_next=b['next_coedge_index'],target_previous=b['previous_coedge_index'],
                source_flag=a['is_reversed'],target_flag=b['is_reversed']))
        loopfacts=[]
        def cycle(lid):
            head=nodes[lid]['first_coedge_index'];current=head;out=[]
            while current not in out:
                assert len(out)<5 and nodes[current]['loop_index']==lid;out.append(current);current=nodes[current]['next_coedge_index']
            assert current==head and len(out)==4;return out
        for sl,tl in lmap.items():
            source_cycle=cycle(sl);target_cycle=cycle(tl);mapped=[cmap[c] for c in source_cycle]
            assert set(mapped)==set(target_cycle)
            same=all(nodes[cmap[c]]['next_coedge_index']==cmap[nodes[c]['next_coedge_index']] for c in source_cycle)
            reverse=all(nodes[cmap[c]]['previous_coedge_index']==cmap[nodes[c]['next_coedge_index']] for c in source_cycle)
            assert same!=reverse
            loopfacts.append(dict(source_loop_index=sl,target_loop_index=tl,source_cycle=source_cycle,
                target_cycle=target_cycle,mapped_source_cycle=mapped,reversed_cycle=reverse))
        copies.append(dict(source_native_body_object_id=source,result_native_body_object_id=target,
            faces=facefacts,edges=edgefacts,coedges=coedgefacts,loops=loopfacts))
    return copies,parsed,top


def compare_native_proof(row,reflection,members):
    facts,parsed,top=independent_geometry(reflection,members);nodes={n['index']:n for n in top['nodes']}
    assert row['feature_object_id']==reflection['feature_object_id'] and row['computed_householder_matrix']==reflection['computed_householder_matrix']
    assert row['source_native_body_object_ids']==reflection['source_native_body_object_ids']
    assert row['owned_result_anchor_object_ids']==reflection['owned_result_anchor_object_ids']
    output={(c['source_native_body_object_id'],c['result_native_body_object_id']):c for c in row['body_boundary_copies']}
    assert len(output)==len(facts)
    for fact in facts:
        c=output[fact['source_native_body_object_id'],fact['result_native_body_object_id']]
        assert c['complete_topology_identity_bijections'] and c['maximum_residual_raw']<1e-9
        faces={f['source_face_index']:f for f in c['face_pairs']}
        for f in fact['faces']:
            p=faces[f['source_face_index']];assert p['target_face_index']==f['target_face_index'] and p['name_key']==f['name_key']
            assert p['source_face']==nodes[f['source_face_index']] and p['target_face']==nodes[f['target_face_index']]
            assert p['source_surface']==f['source_surface'] and p['target_surface']==f['target_surface']
            t=p['mathematical_plane_transport'];assert t['matrix_2x2']==f['linear'] and t['offset_2d']==f['offset']
            assert t['stored_source_is_v_reversed']==f['raw_flags']['source_plane_v_reversed'] and t['stored_target_is_v_reversed']==f['raw_flags']['target_plane_v_reversed']
            for key,v in zip(('origin_coefficient','U_coefficient','V_coefficient'),f['coefficient_residual_vectors']):
                assert abs(t['coefficient_residuals_raw'][key]-math.hypot(*v))<1e-9
            assert t['raw_source_u_interval']==f['source_surface']['u_interval'] and t['raw_source_v_interval']==f['source_surface']['v_interval']
            assert t['raw_target_u_interval']==f['target_surface']['u_interval'] and t['raw_target_v_interval']==f['target_surface']['v_interval']
            # Point fields are checked independently against raw typed points;
            # the carrier coefficient identity alone is not face containment.
            published=p['boundary_point_correspondence'];assert len(published)==4
            assert {v['source_vertex_index'] for v in published}=={v['source_vertex_index'] for v in f['boundary_points']}
            expected_points={v['source_vertex_index']:v for v in f['boundary_points']}
            for v in published:
                expected=expected_points[v['source_vertex_index']]
                assert v['target_vertex_index']==expected['target_vertex_index']
                assert v['source_point_index']==nodes[v['source_vertex_index']]['point_index']
                assert v['target_point_index']==nodes[v['target_vertex_index']]['point_index']
                assert v['source_raw_position']==expected['source_point'] and v['target_raw_position']==expected['target_point']
                assert v['source_mathematical_coordinates']==expected['source_frame_coordinates']
                assert v['transported_source_mathematical_coordinates']==expected['target_frame_coordinates']
                assert v['source_reconstructed_raw_position']==expected['evaluated_source_point']
                assert v['transported_target_evaluation_raw_position']==expected['evaluated_target_point']
                assert v['maximum_residual_raw']<1e-9 and all(math.isfinite(r) and r<1e-9 for r in v['residuals_raw'].values())
        edges={e['source_edge_index']:e for e in c['edge_pairs']}
        for e in fact['edges']:
            p=edges[e['source_edge_index']];assert p['target_edge_index']==e['target_edge_index']
            assert p['source_edge']==nodes[e['source_edge_index']] and p['target_edge']==nodes[e['target_edge_index']]
            assert p['source_curve']==e['source_curve'] and p['target_curve']==e['target_curve']
            assert p['mapped_endpoint_vertex_indices']==e['mapped_endpoint_vertex_indices']
            t=p['affine_parameter_transport'];domain=p['domain_evidence']
            assert abs(t['scale']-e['scale'])<1e-9 and abs(t['offset']-e['offset'])<1e-9
            assert domain['source_literal_EDGE_parameters']==e['source_domain'] and domain['target_literal_EDGE_parameters']==e['target_domain']
            assert domain['source_EDGE_parameters_in_target_curve']==e['transported_domain']
            assert len(domain['native_endpoint_evaluations'])==4
            for v in domain['native_endpoint_evaluations']:
                edge=p[v['side']+'_edge'];curve=p[v['side']+'_curve'];parameter=edge[v['endpoint']+'_parameter']
                vertex=edge[v['endpoint']+'_vertex_index'];position=nodes[nodes[vertex]['point_index']]['raw_origin']
                expected=[a+parameter*b for a,b in zip(curve['raw_origin'],curve['direction'])]
                assert v['parameter']==parameter and v['stored_raw_position']==position and v['evaluated_raw_position']==expected
                assert v['residual_raw']<1e-9 and maximum(subtract(expected,position))<1e-9
        coedges={p['source_coedge_index']:p for p in c['coedge_pairs']}
        for p in fact['coedges']:
            v=coedges[p['source_coedge_index']];assert v['target_coedge_index']==p['target_coedge_index']
            assert v['source_coedge']==nodes[p['source_coedge_index']] and v['target_coedge']==nodes[p['target_coedge_index']]
            assert v['mapped_source_next']==p['mapped_next']==p['target_previous']
            assert v['mapped_source_previous']==p['mapped_previous']==p['target_next']
            assert v['stored_reversal_flags_differ']==(p['source_flag']!=p['target_flag'])
        loops={p['source_loop_index']:p for p in c['loop_pairs']}
        for p in fact['loops']:
            v=loops[p['source_loop_index']];assert v['target_loop_index']==p['target_loop_index']
            assert v['source_stored_cycle']==p['source_cycle'] and v['target_stored_cycle']==p['target_cycle']
            assert v['mapped_source_cycle']==p['mapped_source_cycle'] and v['reversed_cycle']==p['reversed_cycle']
        assert c['counts']['face_pairs']==6 and c['counts']['edge_pairs']==12 and c['counts']['coedge_pairs']==24 and c['counts']['loop_pairs']==6
        assert c['counts']['incident_FACE_vertex_pairs']==24
        assert c['counts']['native_endpoint_evaluations']==48 and c['counts']['transported_parameter_endpoints']==24
        for h in c['head_observations']['edge_first_coedge']:
            source,target=nodes[h['source_edge_index']],nodes[h['target_edge_index']]
            assert h['source_first_coedge']==source['first_coedge_index'] and h['target_first_coedge']==target['first_coedge_index']
        for h in c['head_observations']['vertex_first_edge']:
            source,target=nodes[h['source_vertex_index']],nodes[h['target_vertex_index']]
            assert h['source_first_edge']==source['first_edge_index'] and h['target_first_edge']==target['first_edge_index']
    return facts,parsed,top


def numeric_projection(summary):
    out=[]
    for row in summary['decoded']:
        copies=[]
        for c in row['body_boundary_copies']:
            faces=[]
            for f in c['face_pairs']:
                t=copy.deepcopy(f['mathematical_plane_transport'])
                for key in ('stored_source_is_v_reversed','stored_target_is_v_reversed','stored_v_flags_differ'):t.pop(key)
                faces.append((f['source_face_index'],f['target_face_index'],t,f['boundary_point_correspondence']))
            edges=[(e['source_edge_index'],e['target_edge_index'],e['affine_parameter_transport'],e['domain_evidence']) for e in c['edge_pairs']]
            copies.append((c['source_native_body_object_id'],c['result_native_body_object_id'],faces,edges))
        out.append((row['feature_object_id'],copies))
    return out


def validate(root,zstd):
    prior_path=root/'mirror-cache-reflection-decoding.json';prior=json.loads(prior_path.read_text())
    old={s['archive']:s['expected_summary'] for s in prior['samples']};assert set(old)==set(FILES)
    baseline_path=Path('/private/tmp/fusion-mirror-cache-reflections-baseline.json');baseline=json.loads(baseline_path.read_text())
    bindings_by={Path(o['file']).relative_to(root).as_posix():o['streams'][0]['body_blob_bindings'] for o in baseline['before']}
    report=dict(interface='decode_mirror_boundary_caches(data,records,features,member,members,body_blob_bindings)->decoded/unresolved/scope',
        integration=dict(stream='mirror_boundary_caches',feature_attachment='mirror_boundary_cache',feature_id='feature_object_id',expected_summary='samples[].expected_summary'),
        method='Prior native/name/vertex reflection identity is independently held exact. New FACE/EDGE/COEDGE/LOOP maps use complete names, fixed endpoints and reciprocal ownership before analytic plane/line coefficients; raw/native relationships and coefficients are recomputed here from blob nodes.',
        coordinate_scope='Mathematical plane coordinates U=stored reference,V=N cross U only; native/API UV, literal flag/traversal meaning and general BRep reconstruction unresolved',
        prior_evidence=dict(path=prior_path.name,sha256=hashlib.sha256(prior_path.read_bytes()).hexdigest()),
        samples=[],guards=[],literal_controls=[],source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in (
            'decode_mirror_boundary_caches.py','validate_mirror_boundary_caches.py','decode_mirror_cache_reflections.py',
            'decode_mirror_cache_sources.py','decode_circular_feature_caches.py','decode_circular_placement_evidence.py','decode_brep.py')})
    totals=dict(BODY_copies=0,Plane_pairs=0,EDGE_pairs=0,COEDGE_pairs=0,LOOP_pairs=0,
        incident_FACE_vertex_pairs=0,finite_EDGE_parameter_transports=0,native_endpoint_evaluations=0,independent_line_transport_samples=0,
        unchanged_prior_reflection_summaries=0)
    saved=None;head_counts={};face_flags={};coedge_flags={}
    for archive in FILES:
        data,records,features,member,members=load(root,archive,zstd);decode_sketches(data,records,features);decode_placement(data,records,features)
        bindings=bindings_by[archive];original=copy.deepcopy((features,bindings))
        reflection=decode_mirror_cache_reflections(data,records,features,member,members,bindings);assert reflection==old[archive]
        out=decode_mirror_boundary_caches(data,records,features,member,members,bindings);assert (features,bindings)==original
        totals['unchanged_prior_reflection_summaries']+=1
        sample=dict(archive=archive,archive_sha256=hashlib.sha256((root/archive).read_bytes()).hexdigest(),expected_summary=out,
            prior_full_reflection_summary_exact=True,caller_metadata_unchanged=True)
        if reflection['decoded']:
            assert len(out['decoded'])==1 and not out['unresolved'],(archive,out)
            facts,parsed,top=compare_native_proof(out['decoded'][0],reflection['decoded'][0],members)
            sample['independently_recomputed_native_geometry']=facts
            for fact,c in zip(facts,out['decoded'][0]['body_boundary_copies']):
                totals['BODY_copies']+=1;totals['Plane_pairs']+=len(fact['faces']);totals['EDGE_pairs']+=len(fact['edges'])
                totals['COEDGE_pairs']+=len(fact['coedges']);totals['LOOP_pairs']+=len(fact['loops'])
                totals['incident_FACE_vertex_pairs']+=sum(len(f['boundary_points']) for f in fact['faces'])
                totals['finite_EDGE_parameter_transports']+=2*len(fact['edges']);totals['native_endpoint_evaluations']+=4*len(fact['edges'])
                totals['independent_line_transport_samples']+=sum(len(e['samples']) for e in fact['edges'])
                for f in fact['faces']:
                    key=str(f['raw_flags']);face_flags[key]=face_flags.get(key,0)+1
                    assert f['linear']==[[1.,0.],[0.,-1.]] and f['offset']==[0.,0.]
                for p in fact['coedges']:
                    key=str((p['source_flag'],p['target_flag']));coedge_flags[key]=coedge_flags.get(key,0)+1
                for h in c['head_observations']['edge_first_coedge']+c['head_observations']['vertex_first_edge']:
                    key=h['observation'];head_counts[key]=head_counts.get(key,0)+1
            if saved is None:saved=(data,records,features,member,members,bindings,reflection,out,parsed,top)
        else:
            assert not out['decoded'] and not out['unresolved'];sample['complete_empty_control']=True
        report['samples'].append(sample)
    data,records,features,member,members,bindings,reflection,out,parsed,top=saved
    row=out['decoded'][0];first=row['body_boundary_copies'][0];blob_member=row['history_blob_member'];blob=members[blob_member]
    nodes={n['index']:n for n in top['nodes']};sf=first['face_pairs'][0];edge=first['edge_pairs'][0];coedge=first['coedge_pairs'][0]
    def run_changed(raw):return decode_mirror_boundary_caches(data,records,features,member,{**members,blob_member:bytes(raw)},bindings)
    def reject(label,raw,prior_must_remain=True):
        prior_changed=decode_mirror_cache_reflections(data,records,features,member,{**members,blob_member:bytes(raw)},bindings)
        if prior_must_remain:assert prior_changed==reflection,(label,'mutation unexpectedly changes prior vertex-only proof')
        else:assert not prior_changed['decoded'] and prior_changed['unresolved']
        changed=run_changed(raw);assert not changed['decoded'] and len(changed['unresolved'])==1,(label,changed)
        report['guards'].append(dict(case=label,prior_vertex_only_summary_still_exact=prior_changed==reflection,reason=changed['unresolved'][0]['reason']))
    curve=parsed['records'][edge['target_curve']['index']];raw=bytearray(blob)
    direction=edge['target_curve']['direction'];axis=next(i for i,v in enumerate(direction) if v==0.)
    value=edge['target_curve']['raw_origin'][axis];struct.pack_into('<d',raw,curve['tokens'][3]['offset']+1+8*axis,value+.125)
    reject('Target Line carrier shifted perpendicular while all typed vertices stay unchanged',raw)
    er=parsed['records'][edge['target_edge_index']];raw=bytearray(blob)
    struct.pack_into('<d',raw,er['tokens'][6]['offset']+1,er['tokens'][6]['value']+.125)
    reject('Finite target EDGE end parameter changed while vertices stay unchanged',raw)
    plane=parsed['records'][sf['target_surface']['index']];raw=bytearray(blob)
    struct.pack_into('<d',raw,plane['tokens'][3]['offset']+1,float('nan'))
    reject('Nonfinite target Plane origin rejected by the canonical prerequisite',raw,prior_must_remain=False)
    raw=bytearray(blob);normal=sf['target_surface']['normal'];axis=max(range(3),key=lambda i:abs(normal[i]))
    struct.pack_into('<d',raw,plane['tokens'][3]['offset']+1+8*axis,1e308)
    reject('Huge finite target Plane offset cannot pass derived residual checks',raw)
    raw=bytearray(blob);source_plane=parsed['records'][sf['source_surface']['index']]
    H=row['computed_householder_matrix'];delta=[.125*v for v in sf['source_surface']['normal']]
    for i,v in enumerate(delta):struct.pack_into('<d',raw,source_plane['tokens'][3]['offset']+1+8*i,sf['source_surface']['raw_origin'][i]+v)
    reflected=[sum(H[4*i+j]*delta[j] for j in range(3)) for i in range(3)]
    for i,v in enumerate(reflected):struct.pack_into('<d',raw,plane['tokens'][3]['offset']+1+8*i,sf['target_surface']['raw_origin'][i]+v)
    reject('Both Plane carriers shifted consistently off their typed FACE points',raw)
    raw=bytearray(blob);cr=parsed['records'][coedge['target_coedge_index']]
    struct.pack_into('<q',raw,cr['tokens'][5]['offset']+1,coedge['target_coedge']['next_coedge_index'])
    reject('COEDGE partner no longer reciprocal on the same EDGE',raw,prior_must_remain=False)
    raw=bytearray(blob);wrong=next(c['target_coedge_index'] for c in first['coedge_pairs'] if c['target_coedge']['edge_index']!=edge['target_edge_index'])
    struct.pack_into('<q',raw,er['tokens'][7]['offset']+1,wrong)
    reject('EDGE first-coedge has the right type but belongs to another EDGE',raw)
    def accepted(label,raw):
        prior_changed=decode_mirror_cache_reflections(data,records,features,member,{**members,blob_member:bytes(raw)},bindings);assert prior_changed==reflection
        changed=run_changed(raw);assert len(changed['decoded'])==1 and not changed['unresolved'],(label,changed)
        assert numeric_projection(changed)==numeric_projection(out)
        compare_native_proof(changed['decoded'][0],reflection['decoded'][0],{**members,blob_member:bytes(raw)})
        report['literal_controls'].append(dict(case=label,all_mathematical_transports_and_fixed_identity_pairs_exact=True,
            raw_flag_or_head_observations_retained=True,native_UV_or_traversal_semantics=None))
    raw=bytearray(blob);token=plane['tokens'][6];raw[token['offset']]=11 if token['value'] else 10
    accepted('Plane v-sense literal changed without redefining mathematical coordinates',raw)
    raw=bytearray(blob);fr=parsed['records'][sf['target_face_index']];token=fr['tokens'][8];raw[token['offset']]=11 if token['value'] else 10
    accepted('FACE reversal literal changed without inventing surface-parameter meaning',raw)
    raw=bytearray(blob);token=cr['tokens'][7];raw[token['offset']]=11 if token['value'] else 10
    accepted('COEDGE reversal literal changed without using it as a parameter sign',raw)
    raw=bytearray(blob);head=nodes[edge['target_edge']['first_coedge_index']];alternative=head['partner_index']
    struct.pack_into('<q',raw,er['tokens'][7]['offset']+1,alternative)
    accepted('Alternate valid incident partner chosen as stored EDGE head',raw)
    report['literal_flag_counts']=dict(face_and_plane=face_flags,coedge=coedge_flags)
    report['head_observation_counts']=head_counts
    report['summary']=dict(totals,positive_owners=7,empty_controls=5,guards=len(report['guards']),literal_positive_controls=len(report['literal_controls']),
        mathematical_frame_only=True,native_UV_or_API_parameter_claims=0,old_reflection_changes=0,main_runs=0,live_calls=0)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--zstd-library');p.add_argument('--output',default='mirror-boundary-cache-decoding.json');args=p.parse_args()
    zstd=args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(ROOT,zstd);Path(args.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],sort_keys=True))
