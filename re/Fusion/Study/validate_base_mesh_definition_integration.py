"""Fixed sixteen-file BaseMesh definition/source integration against eabb856.

Admit only full independently proved new summaries and same-row feature
attachments. Kinds, existing diagnostics and all geometry stay exact.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from validate_history_cache_integration import differences

ROOT=Path(__file__).resolve().parent
BASELINE='eabb856'
FILES=('meshconverts-4b42d39fb1d5/faceted_closed.f3d',
       'meshconverts-4b42d39fb1d5/faceted_open.f3d',
       'meshcombines-541ebb6cc93f/cut.f3d',
       'meshcombines-541ebb6cc93f/intersect.f3d',
       'meshcombines-541ebb6cc93f/join.f3d',
       'meshseparates-41126250c03f/connected_shell_control.f3d',
       'meshseparates-41126250c03f/two_face_groups.f3d',
       'meshseparates-41126250c03f/two_shells.f3d',
       'meshremoves-8b2188cd274d/one_remove_one.f3d',
       'meshremoves-8b2188cd274d/two_remove_both.f3d',
       'meshremoves-8b2188cd274d/two_remove_first.f3d',
       'meshconvertoperations-5af73924aa60/two_mesh_parametric.f3d',
       'meshcontrasts-10c2557c91a3/stl_centimeter.f3d',
       'meshcontrasts-10c2557c91a3/stl_millimeter.f3d',
       'meshcontrasts-10c2557c91a3/triangle_data_centimeter.f3d',
       'patchcontinuity-b9b0be85a281/brep_tangent.f3d')
CONTRACTS=(('base_mesh_feature_definitions','base_mesh_feature_definition','base-mesh-feature-definition-decoding.json','expected_partial'),
           ('base_mesh_sources','base_mesh_source_provenance','base-mesh-source-decoding.json','expected_decoded'))


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def evidence():
    proof={}
    for summary_key,attachment,filename,expected_key in CONTRACTS:
        report=json.loads((ROOT/filename).read_text());rows={}
        for sample in report['samples']:
            archive=sample.get('archive',sample.get('file'))
            if archive not in FILES:continue
            assert archive not in rows,('Duplicate independent summary golden',filename,archive)
            rows[archive]=sample[expected_key]
        assert set(rows)==set(FILES),('Missing independent empty/positive archive goldens',filename,set(FILES)-set(rows))
        proof[summary_key]=dict(attachment_key=attachment,summaries=rows)
    return proof


def compare(before,current,filename,proof):
    after=copy.deepcopy(current)
    counts=dict(definition_summaries=0,source_summaries=0,partial_definitions=0,partial_source_provenances=0,
                definition_feature_attachments=0,source_feature_attachments=0,unresolved_definition_rows=0,unresolved_source_rows=0)
    assert len(after['streams'])==len(before['streams'])
    seen=set()
    for old,stream in zip(before['streams'],after['streams']):
        assert old['member']==stream['member']
        for summary_key,contract in proof.items():
            expected=contract['summaries'][filename]
            present=bool(expected['partial'] or expected['unresolved'])
            assert summary_key not in old,(filename,'New baseline summary unexpectedly present',summary_key)
            if summary_key not in stream:
                continue
            assert summary_key not in seen and present,(filename,'Unexpected new summary',summary_key)
            assert stream.pop(summary_key)==expected,(filename,'Independent full summary differs',summary_key)
            seen.add(summary_key)
            definitions=summary_key=='base_mesh_feature_definitions'
            counts['definition_summaries' if definitions else 'source_summaries']+=1
            counts['partial_definitions' if definitions else 'partial_source_provenances']+=len(expected['partial'])
            counts['unresolved_definition_rows' if definitions else 'unresolved_source_rows']+=len(expected['unresolved'])
            attachment=contract['attachment_key'];by_id={row['feature_object_id']:row for row in expected['partial']}
            assert len(by_id)==len(expected['partial']),(filename,'Duplicate partial feature identity',summary_key)
            features=stream['features'];feature_ids={f['object_id'] for f in features};attached=set()
            old_by_id={f['object_id']:f for f in old['features']}
            for feature in features:
                identity=feature['object_id']
                assert identity in old_by_id and attachment not in old_by_id[identity],(filename,'Prior feature identity/attachment differs',identity)
                if identity in by_id:
                    assert feature.pop(attachment)==by_id[identity],(filename,'Independent direct feature row differs',attachment,identity)
                    attached.add(identity)
                else:
                    assert attachment not in feature,(filename,'Unqualified attachment',attachment,identity)
            assert attached==set(by_id)&feature_ids
            counts['definition_feature_attachments' if definitions else 'source_feature_attachments']+=len(attached)
        # No attachment may appear without its independently qualified summary.
        for summary_key,contract in proof.items():
            if summary_key not in seen:
                assert all(contract['attachment_key'] not in f for f in stream['features'])
    expected_seen={key for key,value in proof.items() if value['summaries'][filename]['partial'] or value['summaries'][filename]['unresolved']}
    assert seen==expected_seen,(filename,'Missing report-qualified summary',seen^expected_seen)
    assert after==before,(filename,'Unqualified prior-output change',differences(before,after))
    return dict(archive=filename,archive_sha256=sha(ROOT/filename),**counts,
        whole_output_exact_after_removing_only_independent_new_summaries_and_attachments=True,
        classifications_discovery_timeline_warnings_mesh_geometry_placement_and_ASM_exact=True,
        whole_output_unchanged=before==current,baseline_output_sha256=canonical(before),current_output_sha256=canonical(current),qualified_difference_paths=differences(before,current))


def read_cache(path,side):
    value=json.loads(Path(path).read_text())
    if isinstance(value,list):return value
    if 'files' in value:assert value['files']==list(FILES),'Cache manifest differs'
    if 'baseline_commit' in value:assert str(value['baseline_commit']).startswith(BASELINE),'Cache baseline differs'
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
    assert len(before)==len(current)==len(FILES)==16
    assert [v['file'] for v in before]==[str(ROOT/name) for name in FILES]==[v['file'] for v in current]
    proof=evidence();rows=[compare(a,b,name,proof) for a,b,name in zip(before,current,FILES)]
    keys=('definition_summaries','source_summaries','partial_definitions','partial_source_provenances','definition_feature_attachments','source_feature_attachments','unresolved_definition_rows','unresolved_source_rows')
    summary={key:sum(row[key] for row in rows) for key in keys}
    summary.update(saved_files=16,whole_output_unchanged_controls=sum(row['whole_output_unchanged'] for row in rows),unexpected_changes=0,
                   baseline_main_calls=0 if baseline_cache else 16,current_main_calls=0 if current_cache else 16,live_API_calls=0)
    caches={}
    if baseline_cache:caches['baseline']=dict(path=str(Path(baseline_cache).resolve()),sha256=sha(baseline_cache))
    if current_cache:caches['current']=dict(path=str(Path(current_cache).resolve()),sha256=sha(current_cache))
    sources=('validate_base_mesh_definition_integration.py','decode_base_mesh_feature_definitions.py','decode_base_mesh_sources.py','decode_retained_mesh_sources.py','decode_basics.py')
    return dict(scope='Fixed sixteen saved archives against eabb856; exact independent partial definition/source summaries only, with existing output preserved',baseline_commit=BASELINE,files=list(FILES),summary=summary,samples=rows,
        cache_provenance=caches,evidence_sha256={filename:sha(ROOT/filename) for _,_,filename,_ in CONTRACTS},source_sha256={p:sha(ROOT/p) for p in sources},
        limitations=['New partial definitions/provenance do not reclassify BaseMesh or establish parent API BaseFeature, replay, visibility or lifecycle',
            'All old classifications, discovery, current/retained mesh contents, warnings, timeline, placement and full ASM output remain exact',
            'Independent focused report dictionaries qualify every permitted addition; cached main outputs never supply their own expected goldens',
            'No live Fusion/API/UI, native archive writer, regeneration or wholecorpus run',
            'Cache flags avoid repeated decoding; omitting them reproduces only this fixed manifest from pinned local Git and saved files'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline-cache');p.add_argument('--current-cache');p.add_argument('--zstd-library');p.add_argument('--output',default='base-mesh-definition-integration.json');a=p.parse_args()
    z=a.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    r=validate(z,a.baseline_cache,a.current_cache);Path(a.output).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['summary'],sort_keys=True))
if __name__=='__main__':main()
