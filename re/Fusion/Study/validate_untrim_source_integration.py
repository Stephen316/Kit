"""Fixed nine-file Untrim source integration against 8a636ec.

Only independent source summaries and per-feature provenance may be added.
All previous decoding, diagnostics, geometry and placement must remain exact.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from validate_history_cache_integration import differences
ROOT=Path(__file__).resolve().parent
BASELINE='8a636ec'
FILES=tuple('surfacebounds-ac801bb00fae/untrim_'+name+'.f3d' for name in ('internal','external','all','manual'))+(
 'surfacebounds-ac801bb00fae/extend_natural.f3d',
 'surfacebounds-ac801bb00fae/ruled_tangent.f3d',
 'patchcontinuity-b9b0be85a281/brep_tangent.f3d',
 'namedbodies-3c7c11fc2924/namedbodies.f3d',
 'edgemodes-52695761f185/fillet_curvature.f3d')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

EVIDENCE='untrim-source-decoding.json'
SUMMARY='untrim_sources'
MATERIALIZER_EVIDENCE='untrim-cache-decoding.json'


def evidence():
    report=json.loads((ROOT/EVIDENCE).read_text());rows={}
    for sample in report['samples']:
        name=sample['archive']
        if name not in FILES:continue
        assert name not in rows,('Duplicate independent source golden',name)
        rows[name]=sample['expected_summary']
    assert set(rows)==set(FILES),('Missing positive/empty source golden',set(FILES)-set(rows))
    materialized=json.loads((ROOT/MATERIALIZER_EVIDENCE).read_text())['samples']
    materials={r['archive']:r for r in materialized}
    assert len(materials)==len(materialized)==4
    assert set(materials)==set(FILES[:4])
    return dict(sources=rows,materializers=materials)


def qualify_alternate(candidate,material):
    provenance=candidate['alternate_cache_provenance']
    assert provenance==material['expected_provenance'],'Independent complete alternate provenance differs'
    assert provenance['state_slot']==provenance['pointer_side']==0
    assert all(provenance[key] is None for key in ('native_historical_BODY_identity','chronological_state','geometry_before_feature','current_state','inner_outer_loop_classification'))
    origins={r['view_record_index']:r for r in provenance['origin_map']}
    for origin in candidate['selected_cache_origins']:
        assert origin==origins[origin['view_record_index']]
    nodes={n['index']:n for n in material['expected_topology']['nodes']}
    if 'cached_face' in candidate:
        face=candidate['cached_face']
        assert face['face']==nodes[face['face_record_index']]
        assert face['surface']==nodes[face['face']['surface_index']]
        for boundary in face['boundary_edges']:
            for node in [boundary['edge'],boundary['curve']]+boundary['vertices']+boundary['points']:
                assert node==nodes[node['index']]
    if 'geometric_loop_candidate' in candidate:
        loop=candidate['geometric_loop_candidate']
        assert loop['geometry']==nodes[loop['curve_view_record_index']]
        assert loop['raw_endpoint_point']==nodes[loop['point_view_record_index']]['raw_origin']
    return 1


def compare(before,current,filename,golden):
    after=copy.deepcopy(current);expected=golden['sources'][filename]
    assert len(after['streams'])==len(before['streams'])==1
    old=before['streams'][0];stream=after['streams'][0]
    assert old['member']==stream['member']
    assert SUMMARY not in old
    present=bool(expected['associations'] or expected['unresolved'])
    if present:assert stream.pop(SUMMARY)==expected,(filename,'Full independent source summary differs')
    else:assert SUMMARY not in stream,(filename,'Unexpected empty source summary')
    by_owner={};face_count=manual_count=alternate_count=alternate_faces=unsupported_views=0
    for row in expected['associations']:
        owner=row['owner_object_id']
        assert owner not in by_owner,(filename,'Duplicate Untrim association owner')
        assert row['face_operand'] and owner!=row['historical_source_owner_object_id']
        face_count+=1
        material=golden['materializers'][filename]
        assert row['history_blob_member']==material['member']
        face=row['face_operand'];status=face['alternate_cache_status']
        if 'expected_provenance' in material:
            assert status['status']=='QualifiedLiteralAlternateCache'
            candidate=face['qualified_alternate_face_candidate']
            assert all(candidate[key] is None for key in ('exact_selected_source_identity','current_source_identity','persistent_source_identity','qualified_historical_state','API_handle_identity'))
            alternate_count+=qualify_alternate(candidate,material);alternate_faces+=1
        else:
            assert status['status']=='UnsupportedAlternateCache' and status['reason']==material['materializer_rejection']
            assert 'qualified_alternate_face_candidate' not in face
            unsupported_views+=1
        assert all(row[key] is None for key in ('exact_selected_source_identity','current_source_identity','persistent_source_identity','qualified_historical_state','API_handle_identity'))
        manual=row['manual_loop_operands']
        assert len(manual)==(1 if row['stored_loop_type_code']==3 else 0)
        for operand in manual:
            manual_count+=1
            candidate=operand['geometric_loop_candidate']
            assert candidate['semantic_loop_role'] is candidate['API_manual_loop_identity'] is None
            assert all(operand[key] is None for key in ('exact_selected_source_identity','qualified_historical_state','current_source_identity','persistent_source_identity','API_handle_identity'))
            provenance=operand['alternate_cache_provenance']
            assert provenance['state_slot']==provenance['pointer_side']==0
            assert all(provenance[key] is None for key in ('native_historical_BODY_identity','chronological_state','geometry_before_feature','current_state','inner_outer_loop_classification'))
            alternate_count+=qualify_alternate(operand,material)
        by_owner.setdefault(owner,[]).append(row)
    old_features={f['object_id']:f for f in old['features']};attached=set()
    for feature in stream['features']:
        identity=feature['object_id'];assert identity in old_features
        assert SUMMARY not in old_features[identity]
        if identity in by_owner:
            assert feature['kind']==old_features[identity]['kind']=='SurfaceUntrim'
            assert feature.pop(SUMMARY)==by_owner[identity],(filename,'Source provenance attached to wrong feature/row')
            attached.add(identity)
        else:assert SUMMARY not in feature,(filename,'Unqualified source annotation',identity)
    assert attached==set(by_owner),(filename,'Independent successful source owner absent')
    assert after==before,(filename,'Unqualified output change',differences(before,after))
    return dict(archive=filename,archive_sha256=sha(ROOT/filename),published_source_summaries=int(present),
        qualified_source_associations=len(expected['associations']),qualified_face_operands=face_count,qualified_manual_loop_candidates=manual_count,nested_alternate_cache_provenances=alternate_count,qualified_alternate_face_candidates=alternate_faces,explicit_unsupported_alternate_views=unsupported_views,unresolved_source_rows=len(expected['unresolved']),
        feature_annotation_lists=len(attached),feature_annotation_rows=sum(len(v) for v in by_owner.values()),
        whole_output_unchanged=before==current,whole_output_exact_after_removing_only_independent_new_sources=True,
        old_profile_membership_warnings_errors_classifications_geometry_placement_and_ASM_exact=True,
        baseline_output_sha256=digest(before),current_output_sha256=digest(current),qualified_difference_paths=differences(before,current))


def read_cache(path,side):
    value=json.loads(Path(path).read_text())
    if isinstance(value,list):return value
    assert value['files']==list(FILES),'Cache manifest differs'
    if 'baseline_commit' in value:assert value['baseline_commit'].startswith(BASELINE)
    return value[side]


def validate(zstd,baseline_cache=None,current_cache=None):
    if baseline_cache:before=read_cache(baseline_cache,'before')
    else:
        from validate_history_cache_integration import baseline_outputs
        before=baseline_outputs(FILES,zstd,revision=BASELINE)
    if current_cache:current=read_cache(current_cache,'after')
    else:
        from decode_basics import decode_basics
        current=json.loads(json.dumps([decode_basics(ROOT/name,zstd) for name in FILES]))
    assert len(before)==len(current)==len(FILES)==9
    assert [v['file'] for v in before]==[str(ROOT/name) for name in FILES]==[v['file'] for v in current]
    proof=evidence();rows=[compare(b,a,name,proof) for b,a,name in zip(before,current,FILES)]
    keys=('published_source_summaries','qualified_source_associations','qualified_face_operands','qualified_manual_loop_candidates','nested_alternate_cache_provenances','qualified_alternate_face_candidates','explicit_unsupported_alternate_views','unresolved_source_rows','feature_annotation_lists','feature_annotation_rows')
    totals={key:sum(row[key] for row in rows) for key in keys}
    totals.update(saved_files=9,whole_output_unchanged_controls=sum(row['whole_output_unchanged'] for row in rows),unexpected_changes=0,
        baseline_main_calls=0 if baseline_cache else 9,current_main_calls=0 if current_cache else 9,live_API_calls=0)
    caches={}
    if baseline_cache:caches['baseline']=dict(path=str(Path(baseline_cache).resolve()),sha256=sha(baseline_cache))
    if current_cache:caches['current']=dict(path=str(Path(current_cache).resolve()),sha256=sha(current_cache))
    return dict(scope='Fixed nine saved archives against 8a636ec; only independently proved Untrim face/manual-loop operand summary and receiving-Untrim provenance lists',baseline_commit=BASELINE,files=list(FILES),summary=totals,samples=rows,cache_provenance=caches,evidence_sha256={name:sha(ROOT/name) for name in (EVIDENCE,MATERIALIZER_EVIDENCE)},source_sha256={p:sha(ROOT/p) for p in ('validate_untrim_source_integration.py','decode_untrim_sources.py','decode_asm_name_versions.py','materialize_untrim_cache.py','decode_basics.py')},limitations=['Alternate cache views remain separately qualified nested provenance; original initial/current ASM dictionaries are not replaced','Source provenance is attached to the receiving Untrim, separately from historical source owner and existing sketch-profile warnings','No geometry-selected identity, API temporary ID assignment, historical replay, regeneration or persistent topology claim','Independent focused full dictionaries qualify every addition; cached main never supplies its own expected golden','All old profile results, diagnostics, feature classification, timeline, geometry, placement and ASM remain exact','No live Fusion/API/UI or corpus-wide main run; optional caches avoid duplicate fixed-manifest decoding'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline-cache');p.add_argument('--current-cache');p.add_argument('--zstd-library');p.add_argument('--output',default='untrim-source-integration.json');a=p.parse_args()
    z=a.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(z,a.baseline_cache,a.current_cache);Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__':main()
