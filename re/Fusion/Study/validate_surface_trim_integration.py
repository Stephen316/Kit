"""169 cached outputs: SurfaceTrim tool settings and typed source routes.

No main fallback: root owns the pinned baseline and final current caches.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from validate_history_cache_integration import differences

ROOT=Path(__file__).resolve().parent
BASELINE='a8e8e93'
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
    'splitbodyprofiles-be9787c7a7d8/full_profile_one_body.f3d',
    'splitbodyprofiles-be9787c7a7d8/full_profile_two_bodies.f3d',
    'splitbodyprofiles-be9787c7a7d8/small_profile_extended.f3d',
    'splitbodymultisheets-c78bec32dc3f/sheet_body_no_extend.f3d',
    'splitbodymultisheets-c78bec32dc3f/sheet_face_no_extend.f3d',
    'splitbodymultisheets-c78bec32dc3f/small_sheet_face_extend.f3d',
    'sweeps-5f87eff25e24/line_perpendicular.f3d',
    'sweeps-5f87eff25e24/arc_perpendicular.f3d',
    'sweeps-5f87eff25e24/arc_parallel.f3d',
    'sweeps-5f87eff25e24/arc_partial.f3d',
    'sweeps-5f87eff25e24/line_taper.f3d',
    'sweeps-5f87eff25e24/line_twist.f3d',
    'sweeps-5f87eff25e24/line_surface.f3d',
    'sweeps-5f87eff25e24/line_cut.f3d',
    'moretools-88a2cd6cad0b/Sweep.f3d',
    'moretools-380212ab6368/SweepPartial.f3d',
    'sweepguides-db118be14bfe/composite_line_arc.f3d',
    'sweepguides-db118be14bfe/closed_circle.f3d',
    'sweepguides-9887de71bf9e/rail_scale.f3d',
    'sweepguides-9887de71bf9e/rail_stretch.f3d',
    'sweepguides-9887de71bf9e/rail_no_scaling.f3d',
    'sweepguides-9887de71bf9e/rail_full_extents.f3d',
    'sweepguides-9887de71bf9e/guide_surface.f3d',
    'sweepguides-9887de71bf9e/guide_surface_chain.f3d',
    'sweepoperations-62378e7c0294/join.f3d',
    'sweepoperations-62378e7c0294/intersect.f3d',
    'sweepoperations-62378e7c0294/two_sided.f3d',
    'sweepoperations-62378e7c0294/rail_flip_false.f3d',
    'sweepoperations-62378e7c0294/rail_flip_true.f3d',
    'sweepoperations-62378e7c0294/guided_cut.f3d',
    'sweepprofiles-b2b7a2774752/planar_face.f3d',
    'sweepprofiles-b2b7a2774752/open_sketch_surface.f3d',
    'sweepprofiles-b2b7a2774752/open_brep_edge_surface.f3d',
    'sweepprofiles-b2b7a2774752/two_profile_collection.f3d',
    'sweepprofiles-8d489fe02d2d/open_sketch_surface.f3d',
    'sweepprofiles-8d489fe02d2d/open_brep_edge_surface.f3d',
    'sweepprofiles-f20861d6c5c2/open_brep_edge_partial.f3d',
    'sweepprofiles-f20861d6c5c2/open_brep_edge_reversed.f3d',
    'solidsweeps-7d2677669e3d/solid_perpendicular.f3d',
    'solidsweeps-7d2677669e3d/solid_rigid.f3d',
    'solidsweeps-7d2677669e3d/solid_aligned.f3d',
    'solidsweeps-7d2677669e3d/solid_twist.f3d',
    'solidsweeps-5b5ecd5e01b9/solid_twist_zero.f3d',
    'solidsweeps-5b5ecd5e01b9/solid_twist_sixty.f3d',
    'sweepnurbspaths-7ded30a4b9ae/polynomial_cubic.f3d',
    'sweepnurbspaths-7ded30a4b9ae/polynomial_multispan.f3d',
    'sweepnurbspaths-7ded30a4b9ae/rational_cubic.f3d',
    'surfacebounds-ac801bb00fae/extend_natural.f3d',
    'surfacebounds-ac801bb00fae/extend_tangent.f3d',
    'surfacebounds-ac801bb00fae/extend_perpendicular.f3d',
    'surfacebounds-ac801bb00fae/extend_perpendicular_negative.f3d',
    'surfacebounds-ac801bb00fae/extend_aligned.f3d',
    'surfacebounds-ac801bb00fae/extend_two_edges.f3d',
    'surfacebounds-ac801bb00fae/untrim_internal.f3d',
    'surfacebounds-ac801bb00fae/untrim_external.f3d',
    'surfacebounds-ac801bb00fae/untrim_all.f3d',
    'surfacebounds-ac801bb00fae/untrim_manual.f3d',
    'surfacebounds-ac801bb00fae/ruled_tangent.f3d',
    'surfacebounds-ac801bb00fae/ruled_normal.f3d',
    'surfacebounds-ac801bb00fae/ruled_direction.f3d',
    'surfacebounds-ac801bb00fae/ruled_mitered.f3d',
    'surfacebounds-ac801bb00fae/trim_positive.f3d',
    'surfacebounds-ac801bb00fae/trim_negative.f3d',
    'surfacebounds-8804bbf80755/extend_no_chain.f3d',
    'surfacetools-856ca50cf4c7/patch_rectangle.f3d',
    'surfacetools-856ca50cf4c7/patch_circle.f3d',
    'surfacetools-856ca50cf4c7/offset_positive.f3d',
    'surfacetools-856ca50cf4c7/offset_negative.f3d',
    'surfacetools-856ca50cf4c7/offset_rounded.f3d',
    'surfacetools-856ca50cf4c7/stitch_tight.f3d',
    'surfacetools-856ca50cf4c7/stitch_loose.f3d',
    'surfacetools-856ca50cf4c7/unstitch_face.f3d',
    'surfacetools-856ca50cf4c7/unstitch_chain.f3d',
    'surfacetools-856ca50cf4c7/reverse_normal.f3d',
    'surfacetools-856ca50cf4c7/delete_opening.f3d',
    'surfacetrimtools-c507461585b5/sheet_face.f3d',
    'surfacetrimtools-ce3c7e1c703e/sheet_body.f3d',
)
OPERATION_REPORT='surface-trim-tool-decoding.json'
BODY_REPORT='surface-trim-source-decoding.json'
TARGET_STREAM='surface_trim_tools'
BODY_STREAM='surface_trim_sources'
BODY_ATTACHMENT='surface_trim_source'
TARGET_LEVEL='Observed SurfaceTrim face/body tool and typed source; selected-cell recipe, persistent topology and regeneration unresolved'


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
    assert len(outputs)==len(FILES)==169
    for name,output in zip(FILES,outputs):
        assert output['file']==str(ROOT/name)
        assert len({s['member'] for s in output['streams']})==len(output['streams'])
        for stream in output['streams']:
            assert len({f['object_id'] for f in stream['features']})==len(stream['features'])


def compare(before,current,filename,operations,bodies):
    after=copy.deepcopy(current)
    counts=dict(SurfaceTrim_tool_settings=0,qualified_source_proofs=0,tool_additions=0,
        exact_prior_planar_warnings_replaced=0,feature_kind_changes=0,common_Extrude_changes=0)
    if filename not in operations:
        assert current==before,(filename,'Previous167 complete output changed',differences(before,current))
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
            assert feature['class_guid']==old['class_guid']=='FF1741AE-E78B-4A5F-8418-751899E12F66'
            assert feature['kind']==old['kind']==row['kind']=='SurfaceTrim' and feature.get('name')==old.get('name')==row['name']
            assert feature['tool_settings']==row['settings'] and feature['decode_level']==TARGET_LEVEL
            restore(feature,old,('tool_settings','decode_level'))
            restore(stream,prior,(TARGET_STREAM,))
            counts['SurfaceTrim_tool_settings']+=1
            proof=bodies[filename]['expected_source_summary']
            assert stream[BODY_STREAM]==proof and len(proof['decoded'])==1 and not proof['unresolved']
            route=proof['decoded'][0]
            assert route==bodies[filename]['expected_source_row']
            assert row['settings']['tool']==bodies[filename]['expected_tool']
            assert route['native_source_evidence']==row['settings']['tool']['native_source_evidence']
            assert route['feature_object_id']==identity and feature[BODY_ATTACHMENT]==route
            feature.pop(BODY_ATTACHMENT);restore(stream,prior,(BODY_STREAM,))
            counts['qualified_source_proofs']+=1
            tool=dict(object_id=identity,kind='SurfaceTrim')
            assert tool not in prior['tool_decoding']['decoded'] and stream['tool_decoding']['decoded'].count(tool)==1
            stream['tool_decoding']['decoded'].remove(tool);counts['tool_additions']+=1
            exact=dict(object_id=identity,kind='SurfaceTrim',reason='Only observed planar trim tools supported')
            assert prior['tool_decoding']['unresolved'].count(exact)==1
            assert stream['tool_decoding']['unresolved']==[r for r in prior['tool_decoding']['unresolved'] if r!=exact]
            restore(stream['tool_decoding'],prior['tool_decoding'],('unresolved',))
            counts['exact_prior_planar_warnings_replaced']+=1
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


def capture_evidence():
    rows=[]
    for archive,case in zip(FILES[-2:],('sheet_face','sheet_body')):
        folder=(ROOT/archive).parent
        truth_path=folder/'ground_truth.json';journal_path=folder/'journal.jsonl'
        truth=json.loads(truth_path.read_text())
        events=[json.loads(line) for line in journal_path.read_text().splitlines()]
        assert not (folder/'complete.txt').exists() and truth.get('terminal_status') is None
        assert truth['errors']==[] and len(truth['samples'])==1
        sample=truth['samples'][0]
        assert sample['case']==case and sample['file']==Path(archive).name
        assert sample['trim_status']=='FeatureReturned' and sample['transaction_completion']=='add returned feature'
        assert sample['close_owned_document_returned'] is True
        assert sample['feature_at_timeline_end']['healthState']==0
        assert sample['feature_at_timeline_end']['errorOrWarningMessage']==''
        assert sample['export']['returned_success'] is True and sample['export']['sha256']==sha(ROOT/archive)
        assert events[-1]['phase']=='owned_document_close_returned' and events[-1]['returned'] is True
        assert not any(event['phase']=='batch_complete' for event in events)
        executed=folder/'executed-generator-source.txt'
        assert sha(executed)==truth['executed_generator_sha256']
        entrypoint=truth.get('entrypoint_provenance')
        if entrypoint is not None:
            assert sha(folder/entrypoint['executed_snapshot'])==entrypoint['sha256']
        rows.append(dict(archive=archive,status='PartialNoTerminalMarker',
            truth_sha256=sha(truth_path),journal_sha256=sha(journal_path),
            executed_generator_sha256=sha(executed),entrypoint_provenance=entrypoint,
            terminal_status=None,complete_marker_present=False,successful_export_count=1,
            feature_health_state=0,transaction_completion=sample['transaction_completion'],owned_document_closed_true=True,
            final_recorded_phase=events[-1]['phase'],final_recorded_time_utc=events[-1]['time_utc'],
            planned_cases=truth['planned_cases'],
            uncompleted_planned_cases=[name for name in truth['planned_cases'] if name!=case],
            input_cell_count=len(sample['input_cells_before_selection']),
            original_cell_selection_flags=[cell['isSelected'] for cell in sample['input_cells_before_selection']],
            selected_cell_flags=[cell['isSelected'] for cell in sample['input_cells_after_selection']]))
    return dict(runs=rows,observed_sheet_tool_exports=2,observed_SketchLine_exports=0,
        complete_batches=0,live_API_calls=0,
        crash_evidence_scope='Saved journals establish the last recorded successful close. Root separately inspected CER crash evidence showing native TrimFeature wrapper destruction committing a transaction after document close; this validator does not reproduce the crash or independently parse the dump.',
        reported_native_crash_stack=['Ns::Asset::transactionMgr','TransactionUtil::commitTransaction','TransactedRequestProcessor destructor','Fusion::RequestProcessor','MultiStepInput','TrimFeatureInput destructor','TrimFeature destructor','_wrap_delete_TrimFeature','SwigPyObject_dealloc','Python'],
        lifecycle_fix_verified=False,
        missing_cancel_claim=False,
        prevention_proposals=['Keep live capture disabled after process loss; no automatic resume.',
            'Before any separately authorized future attempt, consider releasing all Trim wrappers while the document remains alive, limiting an invocation to one case, and journaling lifecycle boundaries. These proposals have not been reproduced or validated.'])


def validate(baseline_path,current_path,manifest_path):
    assert json.loads(Path(manifest_path).read_text())==list(FILES)
    before=cache_rows(baseline_path,'before');current=cache_rows(current_path,'after')
    manifest(before);manifest(current)
    operations=goldens(OPERATION_REPORT);bodies=goldens(BODY_REPORT)
    assert set(operations)==set(bodies)==set(FILES[-2:])
    rows=[compare(a,b,name,operations,bodies) for name,a,b in zip(FILES,before,current)]
    totals={key:sum(row[key] for row in rows) for key,value in rows[0].items() if type(value) is int}
    assert totals==dict(SurfaceTrim_tool_settings=2,qualified_source_proofs=2,tool_additions=2,
        exact_prior_planar_warnings_replaced=2,feature_kind_changes=0,common_Extrude_changes=0)
    assert all(a==b for a,b in zip(before[:167],current[:167]))
    evidence=['validate_surface_trim_integration.py','decode_basics.py','decode_surface_tools.py','decode_surface_trim_tools.py',
        'decode_surface_trim_sources.py',OPERATION_REPORT,BODY_REPORT,'surface-boundary-decoding.json','surface-tool-decoding.json','fusion-trim-crash-investigation.json']
    return dict(scope='169 cached outputs pinned to a8e8e93; two report-qualified SurfaceTrim sheet tool settings/sources and exact old tool-warning replacements restored before whole-output equality',
        baseline_commit=BASELINE,files=list(FILES),samples=rows,capture_evidence=capture_evidence(),
        inputs=dict(baseline_cache_sha256=sha(baseline_path),current_cache_sha256=sha(current_path),manifest_sha256=sha(manifest_path),
            baseline_output_set_sha256=canonical(before),current_output_set_sha256=canonical(current)),
        summary=dict(saved_files=169,legacy_complete_output_controls=167,prior_complete_output_controls=139,added_legacy_surface_controls=28,
            **totals,unqualified_output_changes=0,ASM_changes=0,placement_changes=0,full_main_runs=0,live_API_calls=0),
        evidence_sha256={name:sha(ROOT/name) for name in evidence},
        limitations=['Qualified SurfaceTrim sheet tool provenance does not replay the kernel operation or reconstruct selected cells or persistent topology.',
            'Actual API cell enumeration and explicit selection flags remain independent from native recipe fields; no ordinal or geometry-only persistent identity inferred.',
            'Existing SurfaceTrim kinds, all other warnings and source/result/placement dictionaries remain unchanged after strictly qualified additions are restored.',
            'Both capture runs lack a terminal marker after one successful export and close each. The SketchLine case was not captured and remains unsupported; no batch completion or crash cause is inferred.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-outputs',type=Path,default=Path('/private/tmp/fusion-surface-trim-baseline.json'))
    parser.add_argument('--current-outputs',type=Path,default=Path('/private/tmp/fusion-surface-trim-current.json'))
    parser.add_argument('--files',type=Path,default=Path('/private/tmp/fusion-surface-trim-files.json'))
    parser.add_argument('--output',type=Path,default=ROOT/'surface-trim-integration.json')
    args=parser.parse_args();report=validate(args.baseline_outputs,args.current_outputs,args.files)
    args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],sort_keys=True))
