"""Fixed ten-file Untrim alternate-face refinement against d673008.

Only External/All nested alternate FACE status and independently qualified
candidate may change. Existing initial geometry and all controls stay exact.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from validate_history_cache_integration import differences
ROOT=Path(__file__).resolve().parent
BASELINE='d673008'
FILES=tuple('surfacebounds-ac801bb00fae/untrim_'+name+'.f3d' for name in ('internal','external','all','manual'))+(
 'surfacebounds-ac801bb00fae/extend_natural.f3d',
 'surfacebounds-ac801bb00fae/extend_two_edges.f3d',
 'surfacebounds-ac801bb00fae/ruled_tangent.f3d',
 'patchcontinuity-b9b0be85a281/brep_tangent.f3d',
 'namedbodies-3c7c11fc2924/namedbodies.f3d',
 'edgemodes-52695761f185/fillet_curvature.f3d')
TARGETS={FILES[1],FILES[2]}
SUMMARY='untrim_sources'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

EVIDENCE='untrim-six-state-source-decoding.json'
MATERIALIZER_EVIDENCE='untrim-six-state-cache-decoding.json'


def evidence():
    rows={}
    for row in json.loads((ROOT/EVIDENCE).read_text())['samples']:
        name=row['archive']
        if name not in FILES:continue
        assert name not in rows
        rows[name]=row['expected_summary']
    assert set(rows)==set(FILES)
    materializers={}
    for row in json.loads((ROOT/MATERIALIZER_EVIDENCE).read_text())['samples']:
        if row['archive'] not in TARGETS:continue
        assert row['archive'] not in materializers
        materializers[row['archive']]=row
    assert set(materializers)==TARGETS
    return dict(sources=rows,materializers=materializers)


def qualify_six_state_face(candidate,material):
    provenance=candidate['alternate_cache_provenance']
    assert provenance==material['expected_provenance'],'Independent complete six-state provenance differs'
    assert provenance['state_slot']==provenance['pointer_side']==0
    assert all(provenance[key] is None for key in ('native_historical_BODY_identity','chronological_state','geometry_before_feature','current_state','semantic_loop_roles'))
    origins={row['view_record_index']:row for row in provenance['origin_map']}
    for origin in candidate['selected_cache_origins']:
        assert origin==origins[origin['view_record_index']]
    nodes={row['index']:row for row in material['expected_topology']['nodes']}
    face=candidate['cached_face']
    assert face['face']==nodes[face['face_record_index']]
    assert face['surface']==nodes[face['face']['surface_index']]
    count=0
    for boundary in face['boundary_edges']:
        for node in [boundary['edge'],boundary['curve']]+boundary['vertices']+boundary['points']:
            assert node==nodes[node['index']];count+=1
    return count


def compare(before,current,filename,proof):
    after=copy.deepcopy(current);expected=proof['sources'][filename]
    assert len(before['streams'])==len(after['streams'])==1
    old=before['streams'][0];stream=after['streams'][0]
    assert old['member']==stream['member']
    present=bool(expected['associations'] or expected['unresolved'])
    if present:assert stream[SUMMARY]==expected,(filename,'Independent complete source summary differs')
    else:assert SUMMARY not in stream
    refined=attachments=geometry_copies=0
    if filename in TARGETS:
        prior_summary=old[SUMMARY];summary=stream[SUMMARY]
        assert not summary['unresolved'] and not prior_summary['unresolved']
        assert len(summary['associations'])==len(prior_summary['associations'])==1
        row=summary['associations'][0];prior=prior_summary['associations'][0]
        assert row['owner_object_id']==prior['owner_object_id']
        face=row['face_operand'];prior_face=prior['face_operand']
        assert prior_face['alternate_cache_status']==dict(status='UnsupportedAlternateCache',
            reason='Untrim cache view is outside the observed five-state journal family',
            scope='Initial face/name provenance remains qualified; no alternate state inferred')
        assert 'qualified_alternate_face_candidate' not in prior_face
        assert face['alternate_cache_status']==dict(status='QualifiedLiteralAlternateCache',qualified_historical_state=None)
        candidate=face['qualified_alternate_face_candidate'];material=proof['materializers'][filename]
        assert row['history_blob_member']==material['member']
        assert all(candidate[k] is None for k in ('exact_selected_source_identity','current_source_identity','persistent_source_identity','qualified_historical_state','API_handle_identity'))
        geometry_copies+=qualify_six_state_face(candidate,material)
        normalized=copy.deepcopy(row)
        normalized['face_operand'].pop('qualified_alternate_face_candidate')
        normalized['face_operand']['alternate_cache_status']=copy.deepcopy(prior_face['alternate_cache_status'])
        assert normalized==prior,(filename,'Existing source fields changed beyond alternate FACE refinement')
        features={f['object_id']:f for f in stream['features']};old_features={f['object_id']:f for f in old['features']}
        owner=row['owner_object_id']
        assert features[owner]['kind']==old_features[owner]['kind']=='SurfaceUntrim'
        assert features[owner][SUMMARY]==[row] and old_features[owner][SUMMARY]==[prior]
        features[owner][SUMMARY]=copy.deepcopy(old_features[owner][SUMMARY]);attachments+=1
        summary['associations'][0]=normalized;refined+=1
    assert after==before,(filename,'Unqualified previous-output change',differences(before,after))
    return dict(archive=filename,archive_sha256=sha(ROOT/filename),qualified_alternate_FACE_refinements=refined,
        refined_owner_list_rows=attachments,independently_corroborated_boundary_geometry_copies=geometry_copies,
        whole_output_unchanged=before==current,whole_output_exact_after_restoring_only_qualified_nested_FACE_status_and_candidate=True,
        old_source_fields_settings_warnings_geometry_placement_and_ASM_exact=True,
        baseline_output_sha256=digest(before),current_output_sha256=digest(current),qualified_difference_paths=differences(before,current))


def read_cache(path,side):
    value=json.loads(Path(path).read_text())
    if isinstance(value,list):return value
    assert value['files']==list(FILES)
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
    assert len(before)==len(current)==len(FILES)==10
    assert [r['file'] for r in before]==[str(ROOT/name) for name in FILES]==[r['file'] for r in current]
    proof=evidence();rows=[compare(b,a,name,proof) for b,a,name in zip(before,current,FILES)]
    keys=('qualified_alternate_FACE_refinements','refined_owner_list_rows','independently_corroborated_boundary_geometry_copies')
    summary={k:sum(r[k] for r in rows) for k in keys}
    summary.update(saved_files=10,whole_output_unchanged_controls=sum(r['whole_output_unchanged'] for r in rows),unexpected_changes=0,
        baseline_main_calls=0 if baseline_cache else 10,current_main_calls=0 if current_cache else 10,live_API_calls=0)
    caches={}
    if baseline_cache:caches['baseline']=dict(path=str(Path(baseline_cache).resolve()),sha256=sha(baseline_cache))
    if current_cache:caches['current']=dict(path=str(Path(current_cache).resolve()),sha256=sha(current_cache))
    sources=('validate_untrim_six_state_source_integration.py','decode_untrim_sources.py','materialize_untrim_cache.py','materialize_untrim_six_state_cache.py','materialize_asm_literal_view.py','decode_basics.py')
    return dict(scope='Fixed ten saved files against d673008; only External/All existing nested Untrim alternate-FACE status/candidate refinements',baseline_commit=BASELINE,files=list(FILES),summary=summary,samples=rows,cache_provenance=caches,
        evidence_sha256={p:sha(ROOT/p) for p in (EVIDENCE,MATERIALIZER_EVIDENCE)},source_sha256={p:sha(ROOT/p) for p in sources},limitations=['Existing Untrim source summaries remain; only two FACE status/candidate pairs and exact same owner-list copies are normalized','Complete alternate provenance and all published geometry/origins match independent materializer evidence','Literal alternate views establish neither chronology, pre-feature/current geometry, API handle identity, persistent topology nor regeneration','Eight controls and every existing initial source field, warning, classification, placement and global ASM dictionary remain exact','No current-main output supplies its own expected golden; no live calls or corpus-wide main run','Optional caches avoid repeated main calls; omitting flags regenerates only this fixed manifest at pinned baseline/current sources'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline-cache');p.add_argument('--current-cache');p.add_argument('--zstd-library');p.add_argument('--output',default='untrim-six-state-source-integration.json');a=p.parse_args()
    z=a.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(z,a.baseline_cache,a.current_cache);Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__':main()
