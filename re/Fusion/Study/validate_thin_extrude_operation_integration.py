"""Fifty-eight cached main outputs: bounded Thin Extrude operation additions.

Only report-qualified thin definitions and body-route attachments are restored.
Common Extrude fields, source selections, warnings, tools, ASM and placements
must remain exact. No main decoder fallback or live Fusion calls.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from validate_history_cache_integration import differences

ROOT=Path(__file__).resolve().parent
BASELINE='2d06620'
FILES=(
    'meshcontrasts-10c2557c91a3/stl_centimeter.f3d',
    'meshcontrasts-10c2557c91a3/stl_millimeter.f3d',
    'meshcontrasts-10c2557c91a3/triangle_data_centimeter.f3d',
    'meshplanecuts-18f2683c83f5/split_body_minimal_fill.f3d',
    'meshplanecuts-18f2683c83f5/trim_minimal_fill.f3d',
    'meshplanecuts-18f2683c83f5/trim_no_fill.f3d',
    'meshreduces-780954a23308/adaptive_count_six.f3d',
    'meshreduces-780954a23308/adaptive_proportion_fifty.f3d',
    'meshreduces-780954a23308/uniform_count_six.f3d',
    'meshreduces-8f01528f7f21/adaptive_proportion_fifty.f3d',
    'meshconverts-4b42d39fb1d5/faceted_closed.f3d',
    'meshconverts-4b42d39fb1d5/faceted_open.f3d',
    'meshconverts-4b42d39fb1d5/prismatic_closed.f3d',
    'meshremeshes-f07f97514069/adaptive_edge_one_point_five.f3d',
    'meshremeshes-f07f97514069/adaptive_edge_two.f3d',
    'meshremeshes-f07f97514069/uniform_edge_two.f3d',
    'meshcombines-541ebb6cc93f/cut.f3d',
    'meshcombines-541ebb6cc93f/intersect.f3d',
    'meshcombines-541ebb6cc93f/join.f3d',
    'splinepatches-ac5e846e59c0/splinepatches.f3d',
    'splinepatches-900d152c2380/splinepatches.f3d',
    'assembly-acc48a9dc05d/assembly.f3d',
    'meshreversenormals-2bc2dd3780cc/closed_once.f3d',
    'meshreversenormals-2bc2dd3780cc/closed_twice.f3d',
    'meshreversenormals-2bc2dd3780cc/open_once.f3d',
    'meshsmooths-56f38f13430a/smooth_default_point_zero_two.f3d',
    'meshsmooths-56f38f13430a/smooth_point_one.f3d',
    'meshsmooths-56f38f13430a/smooth_point_two_five.f3d',
    'meshshells-f5a2d6730f62/closed_thickness_point_one.f3d',
    'meshshells-f5a2d6730f62/open_thickness_point_one.f3d',
    'meshshells-f5a2d6730f62/open_thickness_point_two.f3d',
    'meshfacegroups-0b682fa7d749/accurate_boundary_point_zero_zero_one.f3d',
    'meshfacegroups-0b682fa7d749/fast_eighty_degrees.f3d',
    'meshfacegroups-0b682fa7d749/fast_twenty_degrees.f3d',
    'meshseparates-41126250c03f/connected_shell_control.f3d',
    'meshseparates-41126250c03f/two_face_groups.f3d',
    'meshseparates-41126250c03f/two_shells.f3d',
    'meshremoves-8b2188cd274d/one_remove_one.f3d',
    'meshremoves-8b2188cd274d/two_remove_both.f3d',
    'meshremoves-8b2188cd274d/two_remove_first.f3d',
    'meshcombinefacegroups-33142f03b86e/adjacent_pair.f3d',
    'meshcombinefacegroups-33142f03b86e/adjacent_pair_reversed.f3d',
    'meshcombinefacegroups-33142f03b86e/connected_triple.f3d',
    'meshrepairs-2387e4f9c2d2/closed_close_holes_control.f3d',
    'meshrepairs-2387e4f9c2d2/open_close_holes.f3d',
    'meshrepairs-2387e4f9c2d2/open_stitch_remove.f3d',
    'meshrepairrebuilds-66d4316c2e8d/accurate_density_eight_offset_point_zero_five.f3d',
    'meshrepairrebuilds-66d4316c2e8d/accurate_density_eight_offset_zero.f3d',
    'meshrepairrebuilds-66d4316c2e8d/fast_density_eight.f3d',
    'meshreducedeviations-05a5d48e46d0/adaptive_deviation_point_one.f3d',
    'meshreducedeviations-05a5d48e46d0/adaptive_deviation_point_zero_five.f3d',
    'meshreducedeviations-05a5d48e46d0/requested_uniform_deviation_point_one.f3d',
    'meshconvertoperations-5af73924aa60/base_feature_closed.f3d',
    'meshconvertoperations-5af73924aa60/base_feature_open.f3d',
    'meshconvertoperations-5af73924aa60/two_mesh_parametric.f3d',
    'thinextrudeoperations-edb76642a509/cut.f3d',
    'thinextrudeoperations-edb76642a509/intersect.f3d',
    'thinextrudeoperations-edb76642a509/join.f3d',
)
OPERATION_REPORT='thin-extrude-operation-decoding.json'
BODY_REPORT='thin-extrude-body-route-decoding.json'
THIN_LEVEL='Observed Thin Extrude common/wall controls and owned sketch source; wall geometry and regeneration unresolved'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def restore(actual,prior,keys):
    for key in keys:
        if key in prior:actual[key]=copy.deepcopy(prior[key])
        else:actual.pop(key,None)


def goldens(name):
    rows=json.loads((ROOT/name).read_text())['samples']
    assert len({row['archive'] for row in rows})==len(rows)
    return {row['archive']:row for row in rows}


def manifest(outputs):
    assert len(outputs)==len(FILES)==58
    for name,output in zip(FILES,outputs):
        assert output['file']==str(ROOT/name)
        assert len({s['member'] for s in output['streams']})==len(output['streams'])
        for stream in output['streams']:
            assert len({f['object_id'] for f in stream['features']})==len(stream['features'])


def compare(before,current,filename,operations,bodies):
    after=copy.deepcopy(current)
    counts=dict(Thin_Extrude_operations=0,qualified_body_route_proofs=0,tool_additions=0,
        feature_kind_changes=0,common_extrusion_changes=0)
    if filename not in operations:
        assert current==before,(filename,'Previous55 complete output changed',differences(before,current))
    else:
        assert len(before['streams'])==len(after['streams'])
        for prior,stream in zip(before['streams'],after['streams']):
            assert stream['member']==prior['member']
            features={f['object_id']:f for f in stream['features']};old_features={f['object_id']:f for f in prior['features']}
            assert set(features)==set(old_features)
            expected=operations[filename]['expected_decoded']
            assert len(expected['decoded'])==1 and not expected['unresolved']
            row=expected['decoded'][0];identity=row['feature_object_id'];feature=features[identity];old=old_features[identity]
            assert feature['kind']==old['kind']=='Extrude' and feature['class_guid']==old['class_guid']=='DD405BC2-D673-44F0-8833-5CB2A1C186C7'
            assert feature['name']==old['name']
            prior_thin=operations[filename]['expected_legacy_thin_summary']
            assert prior['thin_extrudes']==prior_thin
            assert prior_thin['decoded']==[] and prior_thin['unresolved']==[dict(feature_object_id=identity,reason='Only observed solid NewBody untapered distance Thin Extrude family supported')]
            merged=copy.deepcopy(prior_thin)
            merged['decoded'].extend(expected['decoded'])
            merged['unresolved']=[r for r in merged['unresolved'] if r['feature_object_id']!=identity]
            merged['operation_variant_scope']=expected['scope']
            assert stream['thin_extrudes']==merged
            assert feature['is_thin_extrude'] is True and feature['thin_extrusion']==row['thin_metadata']
            source={k:v for k,v in row.items() if k not in ('feature_object_id','is_thin_extrude','thin_metadata','common_extrusion_controls')}
            assert feature['thin_extrusion_source']==source and feature['decode_level']==THIN_LEVEL
            assert feature['operation']==old['operation']==row['common_extrusion_controls']['operation']
            assert feature['start']==old['start']==row['common_extrusion_controls']['start']
            assert feature['extent']==old['extent']==row['common_extrusion_controls']['extent']
            restore(feature,old,('is_thin_extrude','thin_extrusion','thin_extrusion_source','decode_level'))
            restore(stream,prior,('thin_extrudes',))
            counts['Thin_Extrude_operations']+=1
            # B's independently qualified late body/ASM proof is not required by
            # early wall/control decoding. Exact focused output qualifies it here.
            proof=bodies[filename]['expected_body_routes_summary']
            assert stream['thin_extrude_body_routes']==proof
            assert len(proof['decoded'])==1 and not proof['unresolved']
            body_row=proof['decoded'][0]
            assert body_row['feature_object_id']==identity
            assert feature['thin_extrusion_body_routes']==body_row
            feature.pop('thin_extrusion_body_routes')
            restore(stream,prior,('thin_extrude_body_routes',))
            counts['qualified_body_route_proofs']+=1
            assert stream['tool_decoding']==prior['tool_decoding']
            assert stream['feature_discovery']==prior['feature_discovery']
            assert stream['modeling_decoding']==prior['modeling_decoding']
    assert after==before,(filename,'Unqualified prior-output difference',differences(before,after))
    return dict(archive=filename,archive_sha256=sha(ROOT/filename),**counts,all_other_fields_exact=True,
        prior_tools_warnings_common_Extrude_sources_ASM_and_placement_exact=True,
        baseline_output_sha256=canonical(before),current_output_sha256=canonical(current),
        qualified_difference_paths=differences(before,current))


def cache_rows(path,side):
    cache=json.loads(Path(path).read_text())
    if isinstance(cache,list):return cache
    assert cache['baseline_commit']==BASELINE and cache['files']==list(FILES)
    return cache[side]


def validate(baseline_path,current_path,manifest_path):
    assert json.loads(Path(manifest_path).read_text())==list(FILES)
    before=cache_rows(baseline_path,'before');current=cache_rows(current_path,'after')
    manifest(before);manifest(current)
    operations=goldens(OPERATION_REPORT);bodies=goldens(BODY_REPORT)
    assert set(operations)==set(bodies)==set(FILES[-3:])
    rows=[compare(a,b,name,operations,bodies) for name,a,b in zip(FILES,before,current)]
    totals={key:sum(row[key] for row in rows) for key,value in rows[0].items() if type(value) is int}
    assert totals==dict(Thin_Extrude_operations=3,qualified_body_route_proofs=3,tool_additions=0,feature_kind_changes=0,common_extrusion_changes=0)
    assert all(a==b for a,b in zip(before[:55],current[:55]))
    sources=['validate_thin_extrude_operation_integration.py','decode_basics.py','decode_extrude.py','decode_thin_extrudes.py',
        'decode_thin_extrude_operations.py','decode_thin_extrude_body_routes.py',OPERATION_REPORT,BODY_REPORT]
    return dict(scope='58 fixed cached outputs pinned2d06620; only three report-qualified Thin Extrude definition/body-route additions restored before exact whole-output comparison',
        baseline_commit=BASELINE,files=list(FILES),samples=rows,
        inputs=dict(baseline_cache_sha256=sha(baseline_path),current_cache_sha256=sha(current_path),manifest_sha256=sha(manifest_path),
            baseline_output_set_sha256=canonical(before),current_output_set_sha256=canonical(current)),
        summary=dict(saved_files=58,legacy_complete_output_controls=55,**totals,unqualified_output_changes=0,ASM_changes=0,placement_changes=0,full_main_runs=0,live_API_calls=0),
        evidence_sha256={name:sha(ROOT/name) for name in sources},
        limitations=['Qualified Thin Extrude controls and serialized participant/result ownership do not reconstruct wall offsets, Boolean operations or regeneration.',
            'Common Extrude classifications/controls and tool rows already existed in the baseline; they remain exact rather than being counted as new feature decoding.',
            'Early native wall definitions and late ASM provenance are separately scoped; no persistent face/edge identity or general lifecycle is inferred.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-outputs',type=Path,default=Path('/private/tmp/fusion-thin-operations-baseline.json'))
    parser.add_argument('--current-outputs',type=Path,default=Path('/private/tmp/fusion-thin-operations-current.json'))
    parser.add_argument('--files',type=Path,default=Path('/private/tmp/fusion-thin-operations-files.json'))
    parser.add_argument('--output',type=Path,default=ROOT/'thin-extrude-operation-integration.json')
    args=parser.parse_args();report=validate(args.baseline_outputs,args.current_outputs,args.files)
    args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],sort_keys=True))
