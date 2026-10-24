"""Fixed thirteen-file Extend alternate-cache source integration against 4c20419.

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
BASELINE='4c20419'
FILES=tuple('surfacebounds-ac801bb00fae/extend_'+name+'.f3d' for name in ('natural','tangent','perpendicular','perpendicular_negative','aligned','two_edges'))+(
 'surfacebounds-8804bbf80755/extend_no_chain.f3d',
 'surfacebounds-ac801bb00fae/untrim_manual.f3d',
 'surfacebounds-ac801bb00fae/untrim_internal.f3d',
 'surfacebounds-ac801bb00fae/ruled_tangent.f3d',
 'patchcontinuity-b9b0be85a281/brep_tangent.f3d',
 'namedbodies-3c7c11fc2924/namedbodies.f3d',
 'edgemodes-52695761f185/fillet_curvature.f3d')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

EVIDENCE='extend-cache-source-decoding.json'
SUMMARY='extend_cache_sources'
MATERIALIZER_EVIDENCE='extend-cache-decoding.json'


def evidence():
    report=json.loads((ROOT/EVIDENCE).read_text());rows={}
    for sample in report['samples']:
        name=sample['archive']
        if name not in FILES:continue
        assert name not in rows,('Duplicate independent source golden',name)
        rows[name]=sample['expected_summary']
    assert set(rows)==set(FILES),('Missing positive/empty source golden',set(FILES)-set(rows))
    samples=json.loads((ROOT/MATERIALIZER_EVIDENCE).read_text())['samples']
    materials={}
    for row in samples:
        if row['archive'] not in FILES[:7]:continue
        assert row['archive'] not in materials
        materials[row['archive']]=row
    assert set(materials)==set(FILES[:7])
    return dict(sources=rows,materializers=materials)


def qualify_view(row,material):
    assert row['history_blob_member']==material['member']
    provenance=row['alternate_cache_provenance']
    assert provenance==material['expected_provenance'],'Independent complete literal-view provenance differs'
    nodes={n['index']:n for n in material['expected_topology']['nodes']}
    origins={o['view_record_index']:o for o in provenance['origin_map']}
    owner=row['owner_object_id'];assert owner!=row['historical_source_owner_object_id']
    unknowns=('exact_selected_source_identity','current_source_identity','persistent_source_identity','API_handle_identity','qualified_historical_state','traversal')
    assert all(row[key] is None for key in unknowns)
    operands=row['descriptor_operands'];assert len(operands) in (1,2)
    assert [o['operand_ordinal'] for o in operands]==list(range(len(operands)))
    assert len({o['selection_record_object_id'] for o in operands})==1
    for key in ('descriptor_object_id','recipe_object_id'):
        assert len({o[key] for o in operands})==len(operands)
    assert len({o['cached_operand']['edge']['index'] for o in operands})==len(operands)
    geometry_count=0
    for operand in operands:
        assert all(operand[key] is None for key in unknowns)
        cache=operand['cached_operand'];edge=cache['edge'];curve=cache['curve'];face=cache['face']
        assert edge==nodes[edge['index']] and curve==nodes[edge['curve_index']]
        assert face['face']==nodes[face['face_record_index']]
        assert face['surface']==nodes[face['face']['surface_index']]
        for boundary in face['boundary_edges']:
            for node in [boundary['edge'],boundary['curve']]+boundary['vertices']+boundary['points']:
                assert node==nodes[node['index']];geometry_count+=1
        assert cache['parameter_domain']==[edge['start_parameter'],edge['end_parameter']]
        assert cache['stored_edge_reversal']==edge['is_reversed']
        endpoints=operand['ordered_endpoint_intersections'];assert len(endpoints)==2
        assert operand['operand_vertex_order']==[e['vertex_view_record_index'] for e in endpoints]
        assert operand['stored_edge_vertex_order']==[edge['start_vertex_index'],edge['end_vertex_index']]
        assert set(operand['operand_vertex_order'])==set(operand['stored_edge_vertex_order'])
        for endpoint in endpoints:
            vertex=nodes[endpoint['vertex_view_record_index']]
            assert endpoint['vertex']==vertex
            assert endpoint['point']==nodes[vertex['point_index']]
            role='Start' if vertex['index']==edge['start_vertex_index'] else 'End'
            assert endpoint['stored_edge_endpoint_role']==role
        assert operand['operand_to_stored_endpoint_order']==[e['stored_edge_endpoint_role'] for e in endpoints]
        for origin in operand['selected_cache_origins']:
            assert origin==origins[origin['view_record_index']]
    return len(operands),geometry_count


def compare(before,current,filename,golden):
    after=copy.deepcopy(current);expected=golden['sources'][filename]
    assert len(after['streams'])==len(before['streams'])==1
    old=before['streams'][0];stream=after['streams'][0]
    assert old['member']==stream['member']
    assert SUMMARY not in old
    present=bool(expected['associations'] or expected['unresolved'])
    if present:assert stream.pop(SUMMARY)==expected,(filename,'Full independent source summary differs')
    else:assert SUMMARY not in stream,(filename,'Unexpected empty source summary')
    by_owner={};operand_count=geometry_count=0
    for row in expected['associations']:
        owner=row['owner_object_id']
        assert owner not in by_owner,(filename,'Duplicate Extend alternate-cache association owner')
        count,geometry=qualify_view(row,golden['materializers'][filename])
        operand_count+=count;geometry_count+=geometry
        by_owner.setdefault(owner,[]).append(row)
    old_features={f['object_id']:f for f in old['features']};attached=set()
    for feature in stream['features']:
        identity=feature['object_id'];assert identity in old_features
        assert SUMMARY not in old_features[identity]
        if identity in by_owner:
            assert feature['kind']==old_features[identity]['kind']=='SurfaceExtend'
            assert feature.pop(SUMMARY)==by_owner[identity],(filename,'Source provenance attached to wrong feature/row')
            attached.add(identity)
        else:assert SUMMARY not in feature,(filename,'Unqualified source annotation',identity)
    assert attached==set(by_owner),(filename,'Independent successful source owner absent')
    assert after==before,(filename,'Unqualified output change',differences(before,after))
    return dict(archive=filename,archive_sha256=sha(ROOT/filename),published_source_summaries=int(present),
        qualified_source_associations=len(expected['associations']),qualified_alternate_operands=operand_count,independently_corroborated_boundary_geometry_copies=geometry_count,unresolved_source_rows=len(expected['unresolved']),
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
    assert len(before)==len(current)==len(FILES)==13
    assert [v['file'] for v in before]==[str(ROOT/name) for name in FILES]==[v['file'] for v in current]
    proof=evidence();rows=[compare(b,a,name,proof) for b,a,name in zip(before,current,FILES)]
    keys=('published_source_summaries','qualified_source_associations','qualified_alternate_operands','independently_corroborated_boundary_geometry_copies','unresolved_source_rows','feature_annotation_lists','feature_annotation_rows')
    totals={key:sum(row[key] for row in rows) for key in keys}
    totals.update(saved_files=13,whole_output_unchanged_controls=sum(row['whole_output_unchanged'] for row in rows),unexpected_changes=0,
        baseline_main_calls=0 if baseline_cache else 13,current_main_calls=0 if current_cache else 13,live_API_calls=0)
    caches={}
    if baseline_cache:caches['baseline']=dict(path=str(Path(baseline_cache).resolve()),sha256=sha(baseline_cache))
    if current_cache:caches['current']=dict(path=str(Path(current_cache).resolve()),sha256=sha(current_cache))
    return dict(scope='Fixed thirteen saved archives against 4c20419; only independently proved literal alternate-cache operand summary and receiving-Extend provenance lists',baseline_commit=BASELINE,files=list(FILES),summary=totals,samples=rows,cache_provenance=caches,evidence_sha256={name:sha(ROOT/name) for name in (EVIDENCE,MATERIALIZER_EVIDENCE)},source_sha256={p:sha(ROOT/p) for p in ('validate_extend_cache_source_integration.py','decode_extend_cache_sources.py','decode_asm_name_versions.py','materialize_extend_cache.py','materialize_asm_literal_view.py','decode_basics.py')},limitations=['Literal alternate cache views do not qualify pre-Extend geometry, exact selected source identity, traversal or historical lifecycle','Source provenance is attached to the receiving Extend, separately from historical source owner and existing sketch-profile warnings','No geometry-selected identity, API temporary ID assignment, historical replay, regeneration or persistent topology claim','Independent focused full dictionaries qualify every addition; cached main never supplies its own expected golden','All old profile results, diagnostics, feature classification, timeline, geometry, placement and ASM remain exact','No live Fusion/API/UI or corpus-wide main run; optional caches avoid duplicate fixed-manifest decoding'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline-cache');p.add_argument('--current-cache');p.add_argument('--zstd-library');p.add_argument('--output',default='extend-cache-source-integration.json');a=p.parse_args()
    z=a.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(z,a.baseline_cache,a.current_cache);Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__':main()
