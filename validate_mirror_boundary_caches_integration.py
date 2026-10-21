"""Fixed Mirror boundary topology/geometry integration against b2846f1."""
import argparse
import copy
import json
import math
from pathlib import Path

from validate_rectangular_cache_evidence_integration import sha, digest, differences

ROOT = Path(__file__).resolve().parent
BASELINE = 'b2846f1'
FILES = tuple('mirrorfeatures-1ffa1b15c612/' + name + '.f3d' for name in (
    'body_brep_face_plane', 'feature_optimized', 'feature_identical', 'feature_adjust')) + (
    'tools-fda3948848f4/Mirror.f3d',
    'bodyselections-62e42366c722/mirror_two_bodies_plane.f3d',
    'remainingbodyinputs-7b3357274e85/mirror_two_features.f3d',
    'remainingbodyinputs-7b3357274e85/mirror_boss_faces.f3d',
    'datummirrorsupport-3a854f334428/offset_selected_support.f3d',
    'surfacetools-856ca50cf4c7/offset_positive.f3d',
    'surfacebounds-ac801bb00fae/untrim_all.f3d',
    'pathpatterns-de9857f6a1bc/spacing.f3d')
TARGETS = frozenset(FILES[:7])
SUMMARY = 'mirror_boundary_caches'
ATTACHMENT = 'mirror_boundary_cache'
EVIDENCE = 'mirror-boundary-cache-decoding.json'
COUNT_KEYS = ('qualified_Mirror_boundary_features', 'receiving_feature_annotations',
              'result_body_caches', 'plane_correspondences', 'edge_correspondences',
              'coedge_correspondences', 'loop_correspondences', 'incident_FACE_vertex_pairs',
              'native_endpoint_evaluations', 'transported_parameter_endpoints',
              'reversed_loop_cycles', 'coedge_reversal_flags_differ', 'plane_v_flags_differ',
              'edge_head_same', 'edge_head_partner', 'vertex_head_same', 'vertex_head_different')


def evidence():
    rows = {}
    for row in json.loads((ROOT / EVIDENCE).read_text())['samples']:
        if row['archive'] in FILES:
            assert row['archive'] not in rows
            rows[row['archive']] = row['expected_summary']
    assert set(rows) == set(FILES)
    return rows


def qualify(row, before, feature):
    prior = feature['mirror_cache_reflection']
    for key in ('feature_object_id', 'history_blob_member', 'mapping_record_object_id',
                'source_native_body_object_ids', 'owned_result_anchor_object_ids', 'computed_householder_matrix'):
        assert row[key] == prior[key]
    matrix = prior['computed_householder_matrix']
    def vector(p):
        return [sum(matrix[4*i+j]*p[j] for j in range(3)) for i in range(3)]
    def point(p):
        return [v+matrix[4*i+3] for i,v in enumerate(vector(p))]
    def close(a, b):
        if isinstance(a, (tuple, list)):
            assert len(a) == len(b)
            for x,y in zip(a,b): close(x,y)
        else:
            assert math.isfinite(a) and math.isfinite(b) and math.isclose(a,b,rel_tol=0,abs_tol=1e-9), (a,b)
    def dot(a,b): return sum(x*y for x,y in zip(a,b))
    def cross(a,b): return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
    def evaluate(frame,uv): return [o+uv[0]*u+uv[1]*v for o,u,v in zip(frame['origin'],frame['U'],frame['V'])]
    def naming(native_id):
        proof, = [p for p in prior['complete_body_naming_proofs'] if p['native_body_object_id']==native_id]
        result = {}
        for f in proof['proof']['faces']:
            terms = [t for tag in f['generic_tags'] for t in tag['terms']]
            term, = terms
            result[f['face_record_index']] = ([term['name'],term['stored_index']],term['stored_reference_components_int32'])
        assert len(result)==6
        return result
    asm, = [s for s in before['asm_decoding']['streams'] if s['member']==row['history_blob_member']]
    graphs = {g['body_index']:g for g in asm['topology']['body_graphs']}
    old_copies = {(c['source_native_body_object_id'],c['result_native_body_object_id']):c for c in prior['cache_body_copies']}
    new_copies = {(c['source_native_body_object_id'],c['result_native_body_object_id']):c for c in row['body_boundary_copies']}
    assert len(new_copies)==len(row['body_boundary_copies']) and set(new_copies)==set(old_copies)
    totals = dict(result_body_caches=0, plane_correspondences=0,edge_correspondences=0,
                  coedge_correspondences=0,loop_correspondences=0,incident_FACE_vertex_pairs=0,
                  native_endpoint_evaluations=0,transported_parameter_endpoints=0,
                  reversed_loop_cycles=0,coedge_reversal_flags_differ=0,plane_v_flags_differ=0,
                  edge_head_same=0,edge_head_partner=0,vertex_head_same=0,vertex_head_different=0)
    for identity,c in new_copies.items():
        old = old_copies[identity]
        for key in ('source_body_binding','result_body_binding'): assert c[key]==old[key]
        sg,tg = [graphs[c[k]['asm_body_index']] for k in ('source_body_binding','result_body_binding')]
        vp = old['vertex_correspondence']
        vmap = {p['source']['vertex_index']:p['target']['vertex_index'] for p in vp}
        positions = {side:{p[side]['vertex_index']:p[side] for p in vp} for side in ('source','target')}
        sn,tn = naming(identity[0]),naming(identity[1])
        fmap = {s:next(t for t,n in tn.items() if n[0]==name[0]) for s,name in sn.items()}
        pairs = {kind:{p['source_'+kind+'_index']:p for p in c[kind+'_pairs']} for kind in ('face','edge','coedge','loop')}
        maps = {kind:{s:p['target_'+kind+'_index'] for s,p in ps.items()} for kind,ps in pairs.items()}
        assert maps['face']==fmap
        for kind,number in (('face',6),('edge',12),('coedge',24),('loop',6)):
            assert len(pairs[kind])==number
            assert set(maps[kind])==set(sg[kind+'_indices'])
            assert set(maps[kind].values())==set(tg[kind+'_indices'])
        nodes = {side:{p[side+'_'+kind]['index']:p[side+'_'+kind]
                       for kind,ps in pairs.items() for p in ps.values()}
                 for side in ('source','target')}
        for kind,ps in pairs.items():
            for s,p in ps.items():
                assert p['source_'+kind]['index']==s and p['target_'+kind]['index']==maps[kind][s]
        for s,p in pairs['edge'].items():
            se,te=p['source_edge'],p['target_edge']
            mapped=[vmap[se[k]] for k in ('start_vertex_index','end_vertex_index')]
            assert p['mapped_endpoint_vertex_indices']==mapped==[te[k] for k in ('start_vertex_index','end_vertex_index')]
            assert p['stored_endpoint_order']=='PreservedStoredEndpointOrder'
            assert p['stored_EDGE_flags_equal'] is True and se['is_reversed']==te['is_reversed']
            sf={nodes['source'][x['source_coedge_index']]['loop_index'] for x in pairs['coedge'].values() if x['source_coedge']['edge_index']==s}
            tf={nodes['target'][x['target_coedge_index']]['loop_index'] for x in pairs['coedge'].values() if x['target_coedge']['edge_index']==maps['edge'][s]}
            sf={nodes['source'][l]['face_index'] for l in sf};tf={nodes['target'][l]['face_index'] for l in tf}
            assert len(sf)==len(tf)==2 and {fmap[f] for f in sf}==tf
            assert {tuple(n) for n in p['incident_face_name_keys']}=={tuple(sn[f][0]) for f in sf}
            assert {q['source_face_index'] for q in p['incident_complete_FACE_pairs']}==sf
            for q in p['incident_complete_FACE_pairs']:
                assert q['target_face_index']==fmap[q['source_face_index']]
                assert (q['name_key'],q['source_components'])==sn[q['source_face_index']]
                assert (q['name_key'],q['target_components'])==tn[q['target_face_index']]
            sc,tc=p['source_curve'],p['target_curve']
            assert sc['index']==se['curve_index'] and tc['index']==te['curve_index']
            assert sc['kind']==tc['kind']=='straight-curve'
            affine=p['affine_parameter_transport'];a,b=affine['scale'],affine['offset']
            close(vector(sc['direction']),[a*x for x in tc['direction']])
            close(point(sc['raw_origin']),[o+b*d for o,d in zip(tc['raw_origin'],tc['direction'])])
            close(a,1);close(b,0)
            domain=p['domain_evidence']
            for side,e,curve in (('source',se,sc),('target',te,tc)):
                bounds=[e[k] for k in ('start_parameter','end_parameter')]
                assert domain[side+'_literal_EDGE_parameters']==bounds
                checks=[x for x in domain['native_endpoint_evaluations'] if x['side']==side]
                assert len(checks)==2
                for check,key,t in zip(checks,('start_vertex_index','end_vertex_index'),bounds):
                    stored=positions[side][e[key]]['raw_position']
                    expected=[o+t*d for o,d in zip(curve['raw_origin'],curve['direction'])]
                    close(expected,stored);close(check['evaluated_raw_position'],expected)
                    assert check['stored_raw_position']==stored and check['parameter']==t
                    close(check['residual_raw'],math.dist(expected,stored))
            mapped_bounds=[a*t+b for t in domain['source_literal_EDGE_parameters']]
            close(mapped_bounds,domain['target_literal_EDGE_parameters'])
            close(domain['source_EDGE_parameters_in_target_curve'],mapped_bounds)
            close(domain['target_parameters_for_mapped_source_vertices'],mapped_bounds)
            assert domain['raw_source_curve_interval']==sc['parameter_interval']==tc['parameter_interval']==domain['raw_target_curve_interval']
        for s,p in pairs['coedge'].items():
            sc,tc=p['source_coedge'],p['target_coedge']
            assert tc['edge_index']==maps['edge'][sc['edge_index']]
            assert nodes['target'][tc['loop_index']]['face_index']==fmap[nodes['source'][sc['loop_index']]['face_index']]
            for side,cnode in (('source',sc),('target',tc)):
                ns=nodes[side]
                assert ns[cnode['partner_index']]['partner_index']==cnode['index']
                assert ns[cnode['next_coedge_index']]['previous_coedge_index']==cnode['index']
                assert ns[cnode['previous_coedge_index']]['next_coedge_index']==cnode['index']
            assert maps['coedge'][sc['next_coedge_index']]==tc['previous_coedge_index']==p['mapped_source_next']
            assert maps['coedge'][sc['previous_coedge_index']]==tc['next_coedge_index']==p['mapped_source_previous']
            assert maps['coedge'][sc['partner_index']]==tc['partner_index']==p['mapped_source_partner']
            assert p['stored_reversal_flags_differ'] is True and sc['is_reversed']!=tc['is_reversed']
        for s,p in pairs['loop'].items():
            assert fmap[p['source_loop']['face_index']]==p['target_loop']['face_index']
            for side in ('source','target'):
                cycle=p[side+'_stored_cycle'];assert len(set(cycle))==4
                assert cycle[0]==p[side+'_loop']['first_coedge_index']
                for i,coedge in enumerate(cycle):
                    assert nodes[side][coedge]['next_coedge_index']==cycle[(i+1)%4]
                    assert nodes[side][coedge]['loop_index']==p[side+'_loop_index']
            mapped=[maps['coedge'][i] for i in p['source_stored_cycle']]
            assert mapped==p['mapped_source_cycle']
            reverse=list(reversed(mapped));offset=p['reverse_cycle_rotation_offset']
            assert reverse[offset:]+reverse[:offset]==p['target_stored_cycle'] and p['reversed_cycle'] is True
            assert p['mapped_source_first_coedge']==p['target_first_coedge']
        for s,p in pairs['face'].items():
            assert (p['name_key'],p['source_components'])==sn[s]
            assert (p['name_key'],p['target_components'])==tn[fmap[s]]
            sf,tf=p['source_face'],p['target_face']
            assert maps['loop'][sf['first_loop_index']]==tf['first_loop_index']
            assert p['stored_FACE_flags_equal'] is True and sf['is_reversed']==tf['is_reversed']
            ss,ts=p['source_surface'],p['target_surface'];transport=p['mathematical_plane_transport']
            frames=[]
            for side,surface in (('source',ss),('target',ts)):
                frame=transport[side+'_frame']
                assert frame['origin']==surface['raw_origin'] and frame['N']==surface['normal'] and frame['U']==surface['stored_reference_axis']
                close(frame['V'],cross(frame['N'],frame['U']));frames.append(frame)
            sfm,tfm=frames;A=transport['matrix_2x2'];b=transport['offset_2d']
            close(vector(sfm['U']),[A[0][0]*u+A[1][0]*v for u,v in zip(tfm['U'],tfm['V'])])
            close(vector(sfm['V']),[A[0][1]*u+A[1][1]*v for u,v in zip(tfm['U'],tfm['V'])])
            close(point(sfm['origin']),evaluate(tfm,b))
            close(abs(A[0][0]*A[1][1]-A[0][1]*A[1][0]),1)
            assert transport['stored_v_flags_differ'] is True and ss['is_v_reversed']!=ts['is_v_reversed']
            assert ss['u_interval']==ts['u_interval'] and ss['v_interval']==ts['v_interval']
            incident={v for e in pairs['edge'].values() if s in {q['source_face_index'] for q in e['incident_complete_FACE_pairs']} for v in (e['source_edge']['start_vertex_index'],e['source_edge']['end_vertex_index'])}
            checks=p['boundary_point_correspondence'];assert len(checks)==len(incident)==4
            assert {x['source_vertex_index'] for x in checks}==incident
            for x in checks:
                sv,tv=x['source_vertex_index'],x['target_vertex_index'];assert vmap[sv]==tv
                for side,vertex,frame in (('source',sv,sfm),('target',tv,tfm)):
                    stored=positions[side][vertex]
                    assert x[side+'_point_index']==stored['point_index'] and x[side+'_raw_position']==stored['raw_position']
                    delta=[v-o for v,o in zip(stored['raw_position'],frame['origin'])]
                    uv=[dot(delta,frame['U']),dot(delta,frame['V'])]
                    close(x[side+'_mathematical_coordinates'],uv)
                    close(evaluate(frame,uv),stored['raw_position'])
                uv=x['source_mathematical_coordinates'];mapped=[dot(line,uv)+offset for line,offset in zip(A,b)]
                close(mapped,x['target_mathematical_coordinates']);close(evaluate(tfm,mapped),x['target_raw_position'])
                close(x['transported_target_evaluation_raw_position'],x['target_raw_position'])
        for h in c['head_observations']['edge_first_coedge']:
            s,t=h['source_edge_index'],h['target_edge_index'];assert maps['edge'][s]==t
            mapped=maps['coedge'][nodes['source'][s]['first_coedge_index']]
            actual=nodes['target'][t]['first_coedge_index']
            assert h['mapped_source_first_coedge']==mapped and h['target_first_coedge']==actual
            label='MappedSameCoedge' if mapped==actual else 'MappedPartnerCoedge'
            if mapped!=actual:assert nodes['target'][mapped]['partner_index']==actual
            assert h['observation']==label
            totals['edge_head_same' if mapped==actual else 'edge_head_partner']+=1
        for h in c['head_observations']['vertex_first_edge']:
            s,t=h['source_vertex_index'],h['target_vertex_index'];assert vmap[s]==t
            mapped=maps['edge'][h['source_first_edge']];actual=h['target_first_edge']
            assert h['mapped_source_first_edge']==mapped and t in (nodes['target'][actual]['start_vertex_index'],nodes['target'][actual]['end_vertex_index'])
            assert s in (nodes['source'][h['source_first_edge']]['start_vertex_index'],nodes['source'][h['source_first_edge']]['end_vertex_index'])
            assert h['observation']==('MappedSameEdge' if mapped==actual else 'DifferentIncidentEdge')
            totals['vertex_head_same' if mapped==actual else 'vertex_head_different']+=1
        assert c['counts']==dict(face_pairs=6,edge_pairs=12,coedge_pairs=24,loop_pairs=6,incident_FACE_vertex_pairs=24,native_endpoint_evaluations=48,transported_parameter_endpoints=24)
        assert c['complete_topology_identity_bijections'] is True and c['maximum_residual_raw']<=1e-9
        for key,value in dict(result_body_caches=1,plane_correspondences=6,edge_correspondences=12,coedge_correspondences=24,loop_correspondences=6,incident_FACE_vertex_pairs=24,native_endpoint_evaluations=48,transported_parameter_endpoints=24,reversed_loop_cycles=6,coedge_reversal_flags_differ=24,plane_v_flags_differ=6).items():totals[key]+=value
    assert row['counts']=={k:sum(c['counts'][k] for c in new_copies.values()) for k in next(iter(new_copies.values()))['counts']}
    return totals

def compare(before, current, filename, proof):
    after = copy.deepcopy(current)
    assert len(before['streams']) == len(after['streams']) == 1
    old, stream = before['streams'][0], after['streams'][0]
    assert old['member'] == stream['member'] and SUMMARY not in old
    expected = proof[filename]
    assert set(expected) == {'decoded', 'unresolved', 'scope'} and not expected['unresolved']
    counts = dict.fromkeys(COUNT_KEYS, 0)
    if filename in TARGETS:
        assert stream.pop(SUMMARY) == expected and len(expected['decoded']) == 1
        row = expected['decoded'][0]
        identity = row['feature_object_id']
        old_feature = next(f for f in old['features'] if f['object_id'] == identity)
        feature = next(f for f in stream['features'] if f['object_id'] == identity)
        assert old_feature['kind'] == feature['kind'] == 'Mirror'
        assert ATTACHMENT not in old_feature and feature.pop(ATTACHMENT) == row
        counts.update(qualify(row, before, old_feature))
        counts.update(qualified_Mirror_boundary_features=1, receiving_feature_annotations=1)
    else:
        assert not expected['decoded'] and SUMMARY not in stream
        assert all(ATTACHMENT not in f for f in stream['features'])
    assert after == before, (filename, 'Unexpected previous-output change', differences(before, after))
    return dict(archive=filename, archive_sha256=sha(ROOT / filename), **counts,
                whole_output_unchanged=before == current,
                whole_output_exact_after_removing_only_new_summary_and_owner_attachment=True,
                all_previous_reflection_plane_status_settings_warnings_geometry_and_ASM_exact=True,
                baseline_output_sha256=digest(before), current_output_sha256=digest(current),
                qualified_difference_paths=differences(before, current))


def read_cache(path, side):
    value = json.loads(Path(path).read_text())
    assert value['files'] == list(FILES) and value['baseline_commit'].startswith(BASELINE)
    return value[side]


def validate(zstd, baseline_cache=None, current_cache=None):
    if baseline_cache:
        before = read_cache(baseline_cache, 'before')
    else:
        from validate_history_cache_integration import baseline_outputs
        before = baseline_outputs(FILES, zstd, revision=BASELINE)
    if current_cache:
        current = read_cache(current_cache, 'after')
    else:
        from decode_basics import decode_basics
        current = json.loads(json.dumps([decode_basics(ROOT / name, zstd) for name in FILES]))
    assert len(before) == len(current) == len(FILES) == 12
    assert [r['file'] for r in before] == [str(ROOT / name) for name in FILES] == [r['file'] for r in current]
    proof = evidence()
    rows = [compare(b, a, name, proof) for b, a, name in zip(before, current, FILES)]
    summary = {key: sum(r[key] for r in rows) for key in COUNT_KEYS}
    summary.update(saved_files=12, whole_output_unchanged_controls=sum(r['whole_output_unchanged'] for r in rows),
                   unexpected_changes=0, comparator_baseline_main_calls=0 if baseline_cache else 12,
                   comparator_current_main_calls=0 if current_cache else 12, live_API_calls=0)
    assert (summary['qualified_Mirror_boundary_features'], summary['result_body_caches'],
            summary['plane_correspondences'], summary['edge_correspondences'],
            summary['coedge_correspondences'], summary['loop_correspondences'],
            summary['incident_FACE_vertex_pairs'], summary['native_endpoint_evaluations'],
            summary['transported_parameter_endpoints']) == (7,9,54,108,216,54,216,432,216)
    assert (summary['edge_head_same'],summary['edge_head_partner'],
            summary['vertex_head_same'],summary['vertex_head_different']) == (60,48,37,35)
    caches = {}
    for side, path in (('baseline', baseline_cache), ('current', current_cache)):
        if path:
            caches[side] = dict(path=str(Path(path).resolve()), sha256=sha(path))
    sources = ('validate_mirror_boundary_caches_integration.py', 'validate_rectangular_cache_evidence_integration.py',
               'decode_mirror_boundary_caches.py', 'decode_mirror_cache_reflections.py',
               'decode_mirror_cache_sources.py', 'decode_basics.py')
    return dict(scope='Fixed twelve saved archives against b2846f1; seven separate Mirror boundary cache topology and serialized geometry correspondence summaries only',
                baseline_commit=BASELINE, files=list(FILES), summary=summary, samples=rows,
                fixed_manifest_acquisition=dict(baseline_main_calls=12, current_main_calls=12,
                    baseline_passes=1, current_passes=1,
                    scope='Original fixed-manifest acquisition; cached comparison does not repeat either pass'),
                cache_provenance=caches, evidence_sha256={EVIDENCE: sha(ROOT / EVIDENCE)},
                source_sha256={name: sha(ROOT / name) for name in sources},
                limitations=['Existing native source/result BODY, complete FACE names and named vertices fix identities before new incidence or geometry checks',
                             'Cycle direction, reversal flags and head-pointer choices are literal observations, without universal API traversal semantics',
                             'Plane/Line serialized cache equations are checked against the prior selected-plane reflection; no history/current geometry or regeneration claim',
                             'No existing output field is normalized or changed, including prior Mirror reflection and plane statuses',
                             'Independent focused helper goldens qualify additions; no live calls or broad corpus decoding'])


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--baseline-cache')
    p.add_argument('--current-cache')
    p.add_argument('--zstd-library')
    p.add_argument('--output', default='mirror-boundary-cache-integration.json')
    args = p.parse_args()
    zstd = args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result = validate(zstd, args.baseline_cache, args.current_cache)
    Path(args.output).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['summary'], sort_keys=True))


if __name__ == '__main__':
    main()
