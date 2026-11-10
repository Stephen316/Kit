"""Fifty-five cached outputs: qualified Convert inputs and partial BaseFeature routes.

No main fallback. Whole-output equality after explicitly golden-qualified additions
keeps old unsupported/current-source warnings, ASM and placements unchanged.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from validate_history_cache_integration import differences

ROOT = Path(__file__).resolve().parent
BASELINE = 'f9bb931'
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
)
INPUT_REPORT = 'mesh-convert-input-decoding.json'
GEOMETRY_REPORT = 'mesh-convert-operation-geometry-decoding.json'
PARTIAL_REPORT = 'base-feature-single-list-decoding.json'
RESULT_SCOPE = 'Observed singleton BaseFeature result anchor/native BODY/ASM routes only; feature classification, table-body correspondence and lifecycle unresolved'
BASE_MESH = '99F6967E-ED35-4222-B906-5CCF0AC70B53'
CONVERT = '62B85DC3-27B5-47BA-9F13-B2527B72EE49'
MESH_LEVEL = 'Observed component mesh ownership, native asset links and captured geometry buffers; general mesh formats, lifecycle and regeneration unresolved'
CONVERT_LEVEL = 'Observed Faceted MeshConvert source and owned BRep result/history routes; alternative methods, lifecycle and regeneration unresolved'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def restore(actual, prior, keys):
    for key in keys:
        if key in prior: actual[key] = copy.deepcopy(prior[key])
        else: actual.pop(key, None)


def goldens(name):
    rows = json.loads((ROOT/name).read_text())['samples']
    assert len({r['archive'] for r in rows}) == len(rows)
    return {r['archive']:r for r in rows}


def manifest(outputs):
    assert len(outputs) == len(FILES) == 55
    for filename, output in zip(FILES, outputs):
        assert output['file'] == str(ROOT/filename)
        assert len({s['member'] for s in output['streams']}) == len(output['streams'])
        for stream in output['streams']:
            assert len({f['object_id'] for f in stream['features']}) == len(stream['features'])


def compare(before, current, filename, operations, geometry, partials):
    after = copy.deepcopy(current)
    counts = dict(new_Convert_features=0, new_BaseMesh_features=0, partial_BaseFeature_definitions=0,
        new_current_mesh_rows=0, new_normal_pools=0, new_group_caches=0, operation_tool_additions=0, partial_BaseFeature_result_proofs=0)
    if filename not in operations:
        assert current == before, (filename, 'Previous52 complete output changed', differences(before,current))
    else:
        assert len(before['streams']) == len(after['streams'])
        for prior, stream in zip(before['streams'], after['streams']):
            assert stream['member'] == prior['member']
            features = {f['object_id']:f for f in stream['features']}
            old_features = {f['object_id']:f for f in prior['features']}
            assert set(features) == set(old_features)
            recovered = set();kinds = {}
            focused = geometry[filename]
            for key, expected in (('mesh_contents','expected_mesh_contents'),('mesh_normal_pools','expected_normal_pools'),('mesh_face_group_caches','expected_face_group_caches')):
                golden = focused[expected]
                if golden['decoded'] or golden['unresolved']:
                    assert stream.get(key) == golden, (filename,key,'Current geometry/cache golden differs')
                else:
                    assert key not in stream, (filename,key,'Empty optional cache summary must be absent')
            singleton = partials[filename]['expected_decoded']
            assert stream.get('base_feature_single_lists') == (singleton if singleton['partial'] or singleton['unresolved'] else None)
            assert not singleton['unresolved']
            for row in singleton['partial']:
                identity = row['feature_object_id'];feature = features[identity];old = old_features[identity]
                assert feature['base_feature_single_list_definition'] == row
                assert feature['kind'] == old['kind'] == 'UnsupportedFeature'
                assert feature.get('name') == old.get('name') is None and row['stored_name'] == ''
                feature.pop('base_feature_single_list_definition')
                routes = focused['expected_result_body_routes']
                assert feature['base_feature_single_list_result_routes'] == routes
                feature.pop('base_feature_single_list_result_routes')
                counts['partial_BaseFeature_result_proofs'] += 1
                counts['partial_BaseFeature_definitions'] += 1
            if singleton['partial']:
                expected_result_rows = [dict(feature_object_id=row['feature_object_id'], result_routes=focused['expected_result_body_routes']) for row in singleton['partial']]
                assert stream['base_feature_single_list_results']['decoded'] == expected_result_rows and stream['base_feature_single_list_results']['unresolved'] == []
                assert stream['base_feature_single_list_results']['scope'] == RESULT_SCOPE
            else:
                assert stream.get('base_feature_single_list_results') is None
            restore(stream, prior, ('base_feature_single_lists','base_feature_single_list_results'))
            if singleton['partial']:
                # Exact new native current membership is qualified by B's complete golden.
                mesh = stream['mesh_contents'];normal = stream['mesh_normal_pools'];group = stream['mesh_face_group_caches']
                assert len(mesh['decoded']) == len(normal['decoded']) == len(group['decoded']) == 1
                assert not mesh['unresolved'] and not normal['unresolved'] and not group['unresolved']
                row = mesh['decoded'][0];identity = row['mesh_object_id'];owner = row['feature_object_id']
                assert prior['mesh_contents']['decoded'] == [] and prior['mesh_contents']['unresolved'] == [dict(mesh_object_id=identity,reason='Unobserved opt-in native mesh prefix')]
                assert normal['decoded'][0]['mesh_object_id'] == group['decoded'][0]['mesh_object_id'] == identity
                feature = features[owner];old = old_features[owner]
                assert feature['class_guid'] == old['class_guid'] == row['native_feature_class_guid'] == BASE_MESH
                assert old['kind'] == 'UnsupportedFeature' and feature['kind'] == 'BaseMeshFeature'
                assert feature['mesh_contents'] == row and feature['decode_level'] == MESH_LEVEL
                restore(feature, old, ('kind','mesh_contents','decode_level'))
                assert owner not in recovered;recovered.add(owner);kinds[owner] = 'BaseMeshFeature'
                counts['new_BaseMesh_features'] += 1;counts['new_current_mesh_rows'] += 1
                counts['new_normal_pools'] += 1;counts['new_group_caches'] += 1
                assert stream['feature_discovery']['class_decoded_mesh_base_feature_count'] == 1
                restore(stream['feature_discovery'], prior['feature_discovery'], ('class_decoded_mesh_base_feature_count',))
                restore(stream, prior, ('mesh_contents','mesh_normal_pools','mesh_face_group_caches'))
            else:
                for key in ('mesh_contents','mesh_normal_pools','mesh_face_group_caches'):
                    assert stream.get(key) == prior.get(key), (filename,key,'Retained source diagnostics/cache changed')
            variant = operations[filename]['expected_decoded']
            assert not variant['unresolved']
            if variant['decoded']:
                assert len(variant['decoded']) == 1
                merged = copy.deepcopy(prior['mesh_conversions'])
                ids = {row['feature_object_id'] for row in variant['decoded']}
                exact = [r for r in merged['unresolved'] if r['feature_object_id'] in ids and r['reason'] == 'Only captured Faceted parametric Convert header supported']
                assert len(exact) == len(ids)
                merged['decoded'].extend(variant['decoded'])
                merged['unresolved'] = [r for r in merged['unresolved'] if r['feature_object_id'] not in ids]
                merged['multi_input_variant_scope'] = variant['scope']
                assert stream['mesh_conversions'] == merged
                for row in variant['decoded']:
                    identity = row['feature_object_id'];feature = features[identity];old = old_features[identity]
                    assert feature['class_guid'] == old['class_guid'] == CONVERT
                    assert old['kind'] == 'UnsupportedFeature' and row['kind'] == feature['kind'] == 'MeshConvert'
                    assert feature.get('name') == old.get('name') == row['name']
                    assert feature['tool_settings'] == row['settings'] and feature['decode_level'] == CONVERT_LEVEL
                    restore(feature, old, ('kind','tool_settings','decode_level'))
                    assert identity not in recovered;recovered.add(identity);kinds[identity] = 'MeshConvert'
                    tool = dict(object_id=identity,kind='MeshConvert')
                    assert tool not in prior['tool_decoding']['decoded'] and stream['tool_decoding']['decoded'].count(tool) == 1
                    stream['tool_decoding']['decoded'].remove(tool)
                    counts['new_Convert_features'] += 1;counts['operation_tool_additions'] += 1
                assert stream['feature_discovery']['class_decoded_mesh_convert_count'] == len(ids)
                restore(stream['feature_discovery'],prior['feature_discovery'],('class_decoded_mesh_convert_count',))
                restore(stream,prior,('mesh_conversions',))
            else:
                assert stream.get('mesh_conversions') == prior.get('mesh_conversions')
            assert stream['tool_decoding']['unresolved'] == prior['tool_decoding']['unresolved']
            discovery = stream['feature_discovery'];old_discovery = prior['feature_discovery']
            expected = [r for r in old_discovery['unsupported_features'] if r['object_id'] not in recovered]
            assert discovery['unsupported_features'] == expected and discovery['unsupported_feature_count'] == len(expected)
            assert {r['object_id'] for r in old_discovery['unsupported_features']}-{r['object_id'] for r in expected} == recovered
            restore(discovery,old_discovery,('unsupported_features','unsupported_feature_count'))
            def timeline(entry):
                identity = entry['object_id']
                if identity in recovered:
                    assert entry['kind'] == kinds[identity];entry['kind'] = old_features[identity]['kind']
                for child in entry.get('children',[]): timeline(child)
            for sequence in stream['timeline_decoding']['sequences']:
                for entry in sequence['visible_entries']: timeline(entry)
    assert after == before, (filename,'Unqualified output difference',differences(before,after))
    return dict(archive=filename,archive_sha256=sha(ROOT/filename),**counts,all_other_fields_exact=True,
        prior_source_warnings_ASM_placement_and_unsupported_BaseFeature_kinds_exact=True,
        baseline_output_sha256=canonical(before),current_output_sha256=canonical(current),
        qualified_difference_paths=differences(before,current))


def cache_rows(path,side):
    cache = json.loads(Path(path).read_text())
    if isinstance(cache,list): return cache
    assert cache['baseline_commit'] == BASELINE and cache['files'] == list(FILES)
    return cache[side]


def validate(baseline_path,current_path,manifest_path):
    assert json.loads(Path(manifest_path).read_text()) == list(FILES)
    before=cache_rows(baseline_path,'before');current=cache_rows(current_path,'after')
    manifest(before);manifest(current)
    operations=goldens(INPUT_REPORT);geometry=goldens(GEOMETRY_REPORT);partials=goldens(PARTIAL_REPORT)
    assert set(operations) == set(geometry) == set(partials) == set(FILES[-3:])
    rows=[compare(a,b,name,operations,geometry,partials) for name,a,b in zip(FILES,before,current)]
    totals={key:sum(row[key] for row in rows) for key,value in rows[0].items() if type(value) is int}
    assert totals == dict(new_Convert_features=1,new_BaseMesh_features=2,partial_BaseFeature_definitions=2,
        new_current_mesh_rows=2,new_normal_pools=2,new_group_caches=2,operation_tool_additions=1,partial_BaseFeature_result_proofs=2)
    assert all(a == b for a,b in zip(before[:52],current[:52]))
    evidence=['validate_mesh_convert_operation_integration.py','decode_basics.py','decode_mesh_convert.py','decode_mesh_convert_inputs.py',
        'decode_mesh_convert_result_bodies.py','decode_base_feature_single_lists.py','decode_mesh_geometry_variants.py',
        'decode_mesh_contents.py','decode_mesh_normals.py','decode_mesh_face_group_caches.py',INPUT_REPORT,GEOMETRY_REPORT,PARTIAL_REPORT]
    return dict(scope='55 cached outputs pinnedf9bb931; exact focused golden qualifications and full prior-output equality after narrow restoration',
        baseline_commit=BASELINE,files=list(FILES),samples=rows,
        inputs=dict(baseline_cache_sha256=sha(baseline_path),current_cache_sha256=sha(current_path),manifest_sha256=sha(manifest_path),
            baseline_output_set_sha256=canonical(before),current_output_set_sha256=canonical(current)),
        summary=dict(saved_files=55,legacy_complete_output_controls=52,**totals,unqualified_output_changes=0,ASM_changes=0,placement_changes=0,full_main_runs=0,live_API_calls=0),
        evidence_sha256={name:sha(ROOT/name) for name in evidence},
        limitations=['Partial singleton BaseFeature definitions preserve empty stored names and existing feature kinds/warnings; API display name and triggering Convert operation are not inferred as native fields.',
            'Only report-qualified current-prefix memberships and one multi-input Faceted Convert are added. Retained source diagnostics remain exact; no arbitrary lifecycle/visibility replay.',
            'Input and result body collections have explicit independent typed identities; no source/result pairing by order, coordinates or cardinality is inferred.'])


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-outputs',type=Path,default=Path('/private/tmp/fusion-mesh-convert-operations-baseline.json'))
    parser.add_argument('--current-outputs',type=Path,default=Path('/private/tmp/fusion-mesh-convert-operations-current.json'))
    parser.add_argument('--files',type=Path,default=Path('/private/tmp/fusion-mesh-convert-operations-files.json'))
    parser.add_argument('--output',type=Path,default=ROOT/'mesh-convert-operation-integration.json')
    args=parser.parse_args();report=validate(args.baseline_outputs,args.current_outputs,args.files)
    args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],sort_keys=True))
