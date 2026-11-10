"""Fixed eleven-file Extend edge-source integration against d0caf99.

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
BASELINE='d0caf99'
FILES=tuple('surfacebounds-ac801bb00fae/extend_'+name+'.f3d' for name in ('natural','tangent','perpendicular','perpendicular_negative','aligned','two_edges'))+(
 'surfacebounds-8804bbf80755/extend_no_chain.f3d',
 'surfacebounds-ac801bb00fae/ruled_tangent.f3d',
 'surfacebounds-ac801bb00fae/untrim_manual.f3d',
 'patchcontinuity-b9b0be85a281/brep_tangent.f3d',
 'namedbodies-3c7c11fc2924/namedbodies.f3d')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

EVIDENCE='extend-edge-source-decoding.json'
SUMMARY='extend_edge_sources'


def evidence():
    report=json.loads((ROOT/EVIDENCE).read_text());rows={}
    for sample in report['samples']:
        name=sample['archive']
        if name not in FILES:continue
        assert name not in rows,('Duplicate independent source golden',name)
        rows[name]=sample['expected_summary']
    assert set(rows)==set(FILES),('Missing positive/empty source golden',set(FILES)-set(rows))
    return rows


def compare(before,current,filename,golden):
    after=copy.deepcopy(current);expected=golden[filename]
    assert len(after['streams'])==len(before['streams'])==1
    old=before['streams'][0];stream=after['streams'][0]
    assert old['member']==stream['member']
    assert SUMMARY not in old
    present=bool(expected['associations'] or expected['unresolved'])
    if present:assert stream.pop(SUMMARY)==expected,(filename,'Full independent source summary differs')
    else:assert SUMMARY not in stream,(filename,'Unexpected empty source summary')
    by_owner={};operand_count=0
    for row in expected['associations']:
        owner=row['owner_object_id']
        operands=row['descriptor_operands']
        assert len(operands) in (1,2)
        for key in ('descriptor_object_id','recipe_object_id'):
            assert len({r[key] for r in operands})==len(operands),(filename,'Distinct selected operands collapsed',key)
        operand_count+=len(operands)
        assert owner not in by_owner,(filename,'More than one source association per Extend feature')
        assert len({r['stored_initial_operand_cache']['edge_record_index'] for r in operands})==len(operands)
        assert [r['operand_ordinal'] for r in operands]==list(range(len(operands)))
        for operand in operands:
            assert operand['selection_record_object_id']==row['selection_record_object_id']
            assert owner!=operand['historical_source_owner_object_id'],(filename,'Receiving Extend conflated with historical source')
            assert all(operand[key] is None for key in ('exact_selected_source_identity','API_handle_identity','current_source_identity','persistent_source_identity','qualified_historical_state','traversal'))
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
        qualified_source_associations=len(expected['associations']),qualified_source_operands=operand_count,unresolved_source_rows=len(expected['unresolved']),
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
    assert len(before)==len(current)==len(FILES)==11
    assert [v['file'] for v in before]==[str(ROOT/name) for name in FILES]==[v['file'] for v in current]
    proof=evidence();rows=[compare(b,a,name,proof) for b,a,name in zip(before,current,FILES)]
    keys=('published_source_summaries','qualified_source_associations','qualified_source_operands','unresolved_source_rows','feature_annotation_lists','feature_annotation_rows')
    totals={key:sum(row[key] for row in rows) for key in keys}
    totals.update(saved_files=11,whole_output_unchanged_controls=sum(row['whole_output_unchanged'] for row in rows),unexpected_changes=0,
        baseline_main_calls=0 if baseline_cache else 11,current_main_calls=0 if current_cache else 11,live_API_calls=0)
    caches={}
    if baseline_cache:caches['baseline']=dict(path=str(Path(baseline_cache).resolve()),sha256=sha(baseline_cache))
    if current_cache:caches['current']=dict(path=str(Path(current_cache).resolve()),sha256=sha(current_cache))
    return dict(scope='Fixed eleven saved archives against d0caf99; only independently proved literal naming-version / initial-cache operand summary and receiving-Extend provenance lists',baseline_commit=BASELINE,files=list(FILES),summary=totals,samples=rows,cache_provenance=caches,evidence_sha256={EVIDENCE:sha(ROOT/EVIDENCE)},source_sha256={p:sha(ROOT/p) for p in ('validate_extend_edge_source_integration.py','decode_extend_edge_sources.py','decode_asm_name_versions.py','decode_basics.py')},limitations=['Stored initial operand caches do not qualify the pre-Extend geometry, exact selected source identity, traversal or historical lifecycle','Source provenance is attached to the receiving Extend, separately from historical source owner and existing sketch-profile warnings','No geometry-selected identity, API temporary ID assignment, historical replay, regeneration or persistent topology claim','Independent focused full dictionaries qualify every addition; cached main never supplies its own expected golden','All old profile results, diagnostics, feature classification, timeline, geometry, placement and ASM remain exact','No live Fusion/API/UI or corpus-wide main run; optional caches avoid duplicate fixed-manifest decoding'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline-cache');p.add_argument('--current-cache');p.add_argument('--zstd-library');p.add_argument('--output',default='extend-edge-source-integration.json');a=p.parse_args()
    z=a.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result=validate(z,a.baseline_cache,a.current_cache);Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__':main()
