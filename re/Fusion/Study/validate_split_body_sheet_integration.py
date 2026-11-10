"""Ninety-two cached outputs: bounded SplitBody sheet-tool refinements and provenance.

Previous84 whole outputs and five legacy plane-tool SplitBody controls remain exact.
Existing successful tool rows and common modeling/ASM/placement are unchanged.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from validate_history_cache_integration import differences

ROOT=Path(__file__).resolve().parent
BASELINE='388f658'
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
    'threadmodes-d51d2ae60564/cosmetic_full.f3d',
    'threadmodes-d51d2ae60564/modeled_full.f3d',
    'threadmodes-d51d2ae60564/partial_high.f3d',
    'threadmodes-d51d2ae60564/partial_low.f3d',
    'threadmodes-d51d2ae60564/left_handed.f3d',
    'threadmodes-d51d2ae60564/internal.f3d',
    'threadmodes-9574579d310b/left_handed.f3d',
    'threadmultifaces-e4bc4a120fbf/external_two_full.f3d',
    'threadmultifaces-e4bc4a120fbf/external_two_partial.f3d',
    'threadmultifaces-e4bc4a120fbf/internal_two_full.f3d',
    'tappedholes-409e96788503/cosmetic_full.f3d',
    'tappedholes-409e96788503/cosmetic_partial.f3d',
    'tappedholes-409e96788503/modeled_full.f3d',
    'threadfamilies-459264fae49b/ansi_unified_external.f3d',
    'threadfamilies-459264fae49b/bsp_pipe_internal.f3d',
    'threadfamilies-459264fae49b/iso_trapezoidal_external.f3d',
    'faceedits-3f120cbee8d9/offset_positive.f3d',
    'faceedits-3f120cbee8d9/offset_negative.f3d',
    'faceedits-3f120cbee8d9/offset_two_faces.f3d',
    'faceedits-3f120cbee8d9/offset_cylinder.f3d',
    'faceedits-3f120cbee8d9/replace_plane.f3d',
    'faceedits-3f120cbee8d9/replace_plane_tangent.f3d',
    'faceedits-3f120cbee8d9/delete_hole_face.f3d',
    'replacefacetargets-670e35eedbc8/sheet_body.f3d',
    'replacefacetargets-670e35eedbc8/sheet_face.f3d',
    'replacefacetargets-670e35eedbc8/sheet_face_tangent.f3d',
    'splits-efce4ef164c9/yz_extend.f3d',
    'splits-efce4ef164c9/yz_no_extend.f3d',
    'splits-efce4ef164c9/xz_extend.f3d',
    'splits-efce4ef164c9/offset_plane.f3d',
    'splits-efce4ef164c9/multiple_bodies.f3d',
    'splitbodysheets-b7548618fb65/sheet_body_no_extend.f3d',
    'splitbodysheets-b7548618fb65/sheet_face_no_extend.f3d',
    'splitbodysheets-b7548618fb65/small_sheet_face_extend.f3d',
)
OPERATION_REPORT='split-body-sheet-tool-decoding.json'
BODY_REPORT='split-body-sheet-route-decoding.json'
TARGET_STREAM='split_body_sheet_tools'
BODY_STREAM='split_body_sheet_routes'
BODY_ATTACHMENT='split_body_sheet_routes'
TARGET_LEVEL='Observed SplitBody sheet face/body tool, extension control and typed source/result routes; persistent topology and regeneration unresolved'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def restore(actual,prior,keys):
    for key in keys:
        if key in prior:actual[key]=copy.deepcopy(prior[key])
        else:actual.pop(key,None)


def goldens(name):
    rows=json.loads((ROOT/name).read_text())['samples']
    assert len({r['archive'] for r in rows})==len(rows)
    return {r['archive']:r for r in rows}


def manifest(outputs):
    assert len(outputs)==len(FILES)==92
    for name,output in zip(FILES,outputs):
        assert output['file']==str(ROOT/name)
        assert len({s['member'] for s in output['streams']})==len(output['streams'])
        for stream in output['streams']:
            assert len({f['object_id'] for f in stream['features']})==len(stream['features'])


def compare(before,current,filename,operations,bodies):
    after=copy.deepcopy(current)
    counts=dict(SplitBody_tool_refinements=0,qualified_body_route_proofs=0,tool_additions=0,
        tool_warning_changes=0,feature_kind_changes=0,common_Extrude_changes=0)
    if filename not in operations:
        assert current==before,(filename,'Previous89 complete output changed',differences(before,current))
    else:
        assert len(before['streams'])==len(after['streams'])
        for prior,stream in zip(before['streams'],after['streams']):
            assert stream['member']==prior['member']
            features={f['object_id']:f for f in stream['features']};old_features={f['object_id']:f for f in prior['features']}
            assert set(features)==set(old_features)
            summary=operations[filename]['expected_decoded']
            assert len(summary['decoded'])==1 and not summary['unresolved']
            assert stream[TARGET_STREAM]==summary
            row=summary['decoded'][0];identity=row['feature_object_id'];feature=features[identity];old=old_features[identity]
            assert feature['class_guid']==old['class_guid']=='65CA3206-E33A-471E-8E40-2C72B57C6181'
            assert feature['kind']==old['kind']==row['kind']=='SplitBody' and feature.get('name')==old.get('name')==row['name']
            assert old['tool_settings']==operations[filename]['expected_default_settings']
            assert old['tool_settings']['tool'] is None and old['tool_settings']['tool_selection_status']=='Split tool reference unresolved'
            refined=copy.deepcopy(old['tool_settings'])
            assert row['settings']['tool'] is not None and 'tool_selection_status' not in row['settings']
            refined['tool']=row['settings']['tool'];refined.pop('tool_selection_status')
            assert row['settings']==refined,(filename,'Only tool and exact unresolved tool child may change')
            assert feature['tool_settings']==row['settings'] and feature['decode_level']==TARGET_LEVEL
            restore(feature,old,('tool_settings','decode_level'))
            restore(stream,prior,(TARGET_STREAM,))
            counts['SplitBody_tool_refinements']+=1
            proof=bodies[filename]['expected_body_routes_summary']
            assert stream[BODY_STREAM]==proof and len(proof['decoded'])==1 and not proof['unresolved']
            route=proof['decoded'][0]
            assert route['feature_object_id']==identity and feature[BODY_ATTACHMENT]==route
            feature.pop(BODY_ATTACHMENT);restore(stream,prior,(BODY_STREAM,))
            counts['qualified_body_route_proofs']+=1
            assert stream['tool_decoding']==prior['tool_decoding'],(filename,'Existing successful SplitBody tools/warnings changed')
            assert stream['feature_discovery']==prior['feature_discovery']
            assert stream['modeling_decoding']==prior['modeling_decoding']
            assert stream['timeline_decoding']==prior['timeline_decoding']
    assert after==before,(filename,'Unqualified output difference',differences(before,after))
    return dict(archive=filename,archive_sha256=sha(ROOT/filename),**counts,all_other_fields_exact=True,
        prior_kinds_common_Extrude_other_warnings_ASM_and_placement_exact=True,
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
    assert totals==dict(SplitBody_tool_refinements=3,qualified_body_route_proofs=3,tool_additions=0,
        tool_warning_changes=0,feature_kind_changes=0,common_Extrude_changes=0)
    assert all(a==b for a,b in zip(before[:89],current[:89]))
    evidence=['validate_split_body_sheet_integration.py','decode_basics.py','decode_split.py','decode_split_body_sheet_tools.py',
        'decode_split_body_sheet_routes.py',OPERATION_REPORT,BODY_REPORT,'split-decoding.json']
    return dict(scope='92 cached outputs pinned388f658; three report-qualified SplitBody sheet-tool refinements/routes restored before whole-output equality; existing tool rows and warnings stay exact',
        baseline_commit=BASELINE,files=list(FILES),samples=rows,
        inputs=dict(baseline_cache_sha256=sha(baseline_path),current_cache_sha256=sha(current_path),manifest_sha256=sha(manifest_path),
            baseline_output_set_sha256=canonical(before),current_output_set_sha256=canonical(current)),
        summary=dict(saved_files=92,legacy_complete_output_controls=89,prior_complete_output_controls=84,added_legacy_plane_split_controls=5,
            **totals,unqualified_output_changes=0,ASM_changes=0,placement_changes=0,full_main_runs=0,live_API_calls=0),
        evidence_sha256={name:sha(ROOT/name) for name in evidence},
        limitations=['Qualified SplitBody sheet-tool controls and explicit native body provenance do not reconstruct persistent faces or splitting geometry.',
            'Face and whole surface-body tool representations remain distinct; actual API result collections do not establish persistent topology or arbitrary splitting-tool support.',
            'Existing SplitBody kinds, all tool rows/warnings and source/result/placement dictionaries remain unchanged after strictly qualified additions are restored.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-outputs',type=Path,default=Path('/private/tmp/fusion-split-body-sheet-baseline.json'))
    parser.add_argument('--current-outputs',type=Path,default=Path('/private/tmp/fusion-split-body-sheet-current.json'))
    parser.add_argument('--files',type=Path,default=Path('/private/tmp/fusion-split-body-sheet-files.json'))
    parser.add_argument('--output',type=Path,default=ROOT/'split-body-sheet-integration.json')
    args=parser.parse_args();report=validate(args.baseline_outputs,args.current_outputs,args.files)
    args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],sort_keys=True))
