"""Three actual MeshCombine controls; typed retained tools and honest geometry."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from decode_basics import decode_basics
from decode_mesh_combine import decode_mesh_combine
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_placement import transform_point
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT = Path(__file__).resolve().parent
DIRECTORY = 'meshcombines-541ebb6cc93f'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def volume(points, indices):
    terms = []
    for start in range(0, len(indices), 3):
        a, b, c = [points[index] for index in indices[start:start+3]]
        terms.append((a[0]*b[1]*c[2]+a[1]*b[2]*c[0]+a[2]*b[0]*c[1]
            -a[2]*b[1]*c[0]-a[1]*b[0]*c[2]-a[0]*b[2]*c[1])/6.)
    return abs(math.fsum(terms))


def validate(zstd):
    truth_path = ROOT/DIRECTORY/'ground_truth.json'
    truth = json.loads(truth_path.read_text())
    assert truth['terminal_status'] == 'complete' and not truth['errors'] and len(truth['samples']) == 3
    assert digest(ROOT/DIRECTORY/'executed-generator-source.txt') == truth['executed_generator_sha256']
    assert truth['executed_generator_sha256'] == truth['mesh_source_helper_sha256']
    report = {'scope': 'Three actual owned single-tool root MeshCombine exports: contrasted Join/Cut/Intersect, current-target and retained-tool provenance; unsupported Cut geometry retained',
        'interface': 'decode_mesh_combine(data,records,features,member,members,mesh_contents=None)->decoded/unresolved/scope; rows feature_object_id/kind/name/settings',
        'integration': 'Optional mesh_combinations summary; settings and bounded classification only on successful controls. Preserve strict mesh_contents tool/nonmember diagnostics and Cut geometry failure. BaseMesh owner remains separate from MeshCombine role and null API owner.',
        'capture_provenance': {'ground_truth': DIRECTORY+'/ground_truth.json', 'ground_truth_sha256': digest(truth_path),
            'executed_generator_sha256': truth['executed_generator_sha256'],
            'executed_source_snapshot': DIRECTORY+'/executed-generator-source.txt',
            'runtime_sdk_source_sha256_at_capture': truth['sdk_runtime_source_sha256']},
        'native_schema': {'primary_class_guid': 'EE0E56E8-5894-4D65-BAF4-9DAAF811307F',
            'operation_uint32_offset': 2, 'contrasted_codes': {'0': 'Join', '1': 'Cut', '2': 'Intersect'},
            'opaque_uint32_offset': 6, 'opaque_byte_offset': 10,
            'single_tool_count_uint32_offset': 11, 'tool_proxy_ref_offset': 15,
            'current_target_asset_ref_offset': 26, 'additional_asset_ref_offset': 37,
            'target_proxy_ref_offset': 52, 'nil_uuid_offset': 64,
            'repeated_order': 'target proxy/descriptor, then tool proxy/descriptor',
            'invariant_control_limit': 'API Legacy/False/False all captured. No native field is named algorithm/keepTools/newComponent from these invariants.',
            'tool_nonmembership': 'Explicit selected native mesh retained owner backlink; counted collection has target only. Reciprocal native BaseMeshFeature→tool remains separate from current member/lifecycle assertions'},
        'samples': [], 'malformed_guards': [], 'legacy_controls': [],
        'limitations': ['No Combine algorithm or keep/new-component flag byte mapping was contrasted; runtime fields stay None with raw zeros preserved.',
            'Selected tool226 is absent from current counted collection. Stored owner and BaseMesh routes are provenance, not a hidden/deleted/current-state or persistent identity conclusion.',
            'Cut index-buffer framing remains unsupported. Geometry=None and original strict error are published without truncating data, fabricating arrays or clearing global diagnostics.',
            'Additional asset temporal role remains None even when its stored geometry corroborates rolled input getters.',
            'Exact array comparisons below follow explicit typed routes; no nearest-coordinate, name, array-position or volume match selects a native object.',
            'Ideal analytic Boolean volumes differ from actual cached/API results; these references do not prove exact Boolean regeneration.']}
    contexts = {}
    current_checks = retained_checks = additional_checks = api_checks = 0
    for sample in truth['samples']:
        filename = DIRECTORY+'/'+sample['file']
        assert sample['combine_status'] == 'FeatureReturned' and not sample['getter_errors'] and not sample['setter_errors']
        assert sample['close_owned_document_returned'] is True and sample['roll_before_feature_returned'] is True
        assert sample['export']['size_bytes'] == (ROOT/filename).stat().st_size
        assert sample['export']['sha256'] == digest(ROOT/filename)
        members = read_members(ROOT/filename, zstd)
        stream, = decode_basics(ROOT/filename, zstd)['streams']
        data = members[stream['member']]
        records, _ = design_records(data, members[stream['member'].replace('BulkStream.dat', 'MetaStream.dat')])
        features = stream['features']
        before = copy.deepcopy(features)
        strict = decode_mesh_contents_variants(data, records, stream['member'], members)
        summary = decode_mesh_combine(data, records, features, stream['member'], members, strict)
        assert features == before and not summary['unresolved']
        row, = summary['decoded']
        settings = row['settings']
        assert row['kind'] == 'MeshCombine' and settings['operation'].lower() == sample['case']
        expected_operation = {'join': 0, 'cut': 1, 'intersect': 2}[sample['case']]
        for key in ('input_defaults', 'input_before_add', 'feature_before_node', 'feature_at_timeline_end'):
            actual = sample[key]
            assert actual['algorithmType'] == 0 and actual['isKeepToolBodies'] is False and actual['isNewComponent'] is False
            assert actual['meshCombineOperationType'] == (0 if key == 'input_defaults' else expected_operation)
            api_checks += 1
        assert settings['stored_operation_code'] == expected_operation
        assert settings['algorithm_type'] is settings['is_keep_tool_bodies'] is settings['is_new_component'] is None
        assert settings['stored_uninterpreted_uint32_at_6'] == settings['stored_uninterpreted_byte_at_10'] == 0
        assert sample['input_target_equals_import_handle'] is True and sample['input_tools_equal_import_handles'] == [True]
        assert sample['rolled_target_equals_import_handle'] is True and sample['rolled_tools_equal_import_handles'] == [True]
        actual_feature = sample['feature_at_timeline_end']
        assert actual_feature['healthState'] == 0 and actual_feature['errorOrWarningMessage'] == ''
        assert sample['model_parameters_after'] == [] and sample['component_meshes_after_combine']['count'] == 1
        target = settings['target_mesh_metadata']
        source, = settings['retained_tool_sources']
        rolled = sample['feature_before_node']
        assert target['name'] == rolled['targetBody']['name'] == sample['sources_before_combine']['target']['name']
        assert source['name'] == rolled['toolBodies'][0]['name'] == sample['sources_before_combine']['tool']['name']
        assert target['feature_object_id'] == 218 and source['base_mesh_feature_object_id'] == 231
        assert settings['mesh_combine_owns_native_mesh'] is None
        assert rolled['targetBody']['baseOrFormFeature'] is None and rolled['toolBodies'][0]['baseOrFormFeature'] is None
        assert source['retained_membership_status'] == 'NotInCountedMembers'
        assert target['collection_mesh_object_ids'] == source['retained_owner_collection_member_ids'] == [target['mesh_object_id']]
        assert source['mesh_object_id'] == settings['tool_selections'][0]['mesh_object_id'] == 226
        assert source['stored_mesh_index'] == 2 and source['stored_packed_prefix_hex'] == '00000200000000000000000100010000000000000000'
        geometry = source['geometry']
        api = rolled['toolBodies'][0]['original_polygon_mesh']
        assert [v for p in geometry['component_node_coordinates_cm'] for v in p] == api['nodeCoordinatesAsDouble']
        assert geometry['triangle_node_indices'] == api['triangleNodeIndices']
        retained_checks += 1
        additional = settings['additional_stored_asset']['geometry']
        points = [transform_point(target['asset_coordinates_to_component_matrix'], p) for p in additional['stored_node_coordinates_float32']]
        api_target = rolled['targetBody']['original_polygon_mesh']
        assert [v for p in points for v in p] == api_target['nodeCoordinatesAsDouble']
        assert additional['triangle_node_indices'] == api_target['triangleNodeIndices']
        assert settings['additional_asset_temporal_role'] is None
        additional_checks += 1
        layout = settings['layout']
        assert bytes.fromhex(layout['feature_body_hex']) == data[layout['feature_body_offset']:layout['feature_body_end_offset']]
        current_api, = sample['component_meshes_after_combine']['meshes']
        ideal_volume = truth['analytic_reference_only']['ideal_'+sample['case']+'_volume_cm3']
        geometry_control = {'actual_API_current_node_count': current_api['original_polygon_mesh']['nodeCount'],
            'actual_API_current_triangle_count': current_api['original_polygon_mesh']['triangleCount'],
            'actual_API_volume_cm3': current_api['volume'], 'ideal_analytic_reference_volume_cm3': ideal_volume,
            'actual_minus_ideal_cm3': current_api['volume']-ideal_volume,
            'scope': 'Post-route corroboration only; analytic ideal is not exact cached result or identity evidence'}
        if sample['case'] == 'cut':
            assert settings['current_target_asset_geometry'] is None
            failure, = settings['geometry_unresolved']
            assert failure['reason'] == 'Mesh LZMA decoded extent/end-marker disagrees'
            assert any(e['mesh_object_id'] == target['mesh_object_id'] and e['reason'] == failure['reason'] for e in strict['unresolved'])
            geometry_control['unsupported_Cut_geometry_error_retained'] = failure
        else:
            assert not settings['geometry_unresolved']
            current = settings['current_target_asset_geometry']['geometry']
            points = [transform_point(target['asset_coordinates_to_component_matrix'], p) for p in current['stored_node_coordinates_float32']]
            api = current_api['original_polygon_mesh']
            assert [v for p in points for v in p] == api['nodeCoordinatesAsDouble']
            assert current['triangle_node_indices'] == api['triangleNodeIndices']
            measured_volume = volume(points, current['triangle_node_indices'])
            assert math.isclose(measured_volume, current_api['volume'], rel_tol=0, abs_tol=2e-12)
            geometry_control.update(exact_current_node_and_triangle_arrays=True, independent_triangle_volume_cm3=measured_volume)
            current_checks += 1
        assert any(e['mesh_object_id'] == source['mesh_object_id'] for e in strict['unresolved'])
        assert settings['strict_current_mesh_diagnostics'] == strict['unresolved']
        report['samples'].append({'archive': filename, 'archive_sha256': digest(ROOT/filename),
            'expected_decoded': summary, 'expected_mesh_contents': strict,
            'actual_API_default_controls': {k: sample['input_defaults'][k] for k in
                ('meshCombineOperationType', 'algorithmType', 'isKeepToolBodies', 'isNewComponent')},
            'actual_API_configured_controls': {k: sample['input_before_add'][k] for k in
                ('meshCombineOperationType', 'algorithmType', 'isKeepToolBodies', 'isNewComponent')},
            'exact_retained_tool_and_additional_asset_arrays_match_rolled_getters': True,
            'exact_feature_payload_replay': True, 'geometry_corroboration': geometry_control,
            'strict_global_mesh_diagnostics_retained': True, 'owned_document_closed_true': True})
        contexts[sample['case']] = (data, records, features, stream['member'], members, row)
    data, records, features, member, members, row = contexts['join']
    record, = [r for r in records if r.is_primary and r.object_id == row['feature_object_id']]
    primary = {r.object_id: r for r in records if r.is_primary}
    def reject(label, mutate):
        bad = bytearray(data)
        mutate(bad)
        result = decode_mesh_combine(bytes(bad), records, features, member, members)
        assert not result['decoded'] and len(result['unresolved']) == 1
        report['malformed_guards'].append({'case': label, 'reason': result['unresolved'][0]['reason']})
    reject('Unknown operation code', lambda b: struct.pack_into('<I', b, record.body+2, 99))
    reject('Unsupported multiple tools', lambda b: struct.pack_into('<I', b, record.body+11, 2))
    tool_selection = row['settings']['tool_selections'][0]
    proxy = primary[tool_selection['proxy_object_id']]
    reject('Tool proxy owner differs', lambda b: struct.pack_into('<Q', b, proxy.end-10, record.object_id+1))
    descriptor = primary[tool_selection['descriptor_object_id']]
    reject('Tool descriptor owner differs', lambda b: struct.pack_into('<Q', b, descriptor.body+253, record.object_id+1))
    leaf = primary[tool_selection['leaf_object_id']]
    reject('Tool identity leaf differs from descriptor mesh', lambda b: struct.pack_into('<Q', b, leaf.body+2, row['settings']['target_selection']['mesh_object_id']))
    reject('Additional/current asset fields unexpectedly alias', lambda b: struct.pack_into('<Q', b, record.body+38, row['settings']['target_mesh_metadata']['asset_object_id']))
    base_mesh = primary[row['settings']['retained_tool_sources'][0]['base_mesh_feature_object_id']]
    reject('Retained tool BaseMesh backlink differs', lambda b: struct.pack_into('<Q', b, base_mesh.body+7, row['settings']['target_selection']['mesh_object_id']))
    table = record.body+row['settings']['layout']['dependency_table_body_relative_offset']
    reject('Repeated table tool descriptor differs', lambda b: struct.pack_into('<Q', b, table+34, record.object_id))
    for filename in ('meshplanecuts-18f2683c83f5/trim_no_fill.f3d', 'meshreduces-8f01528f7f21/adaptive_proportion_fifty.f3d'):
        members = read_members(ROOT/filename, zstd)
        stream, = decode_basics(ROOT/filename, zstd)['streams']
        data = members[stream['member']]
        records, _ = design_records(data, members[stream['member'].replace('BulkStream.dat', 'MetaStream.dat')])
        before = copy.deepcopy(stream['features'])
        result = decode_mesh_combine(data, records, stream['features'], stream['member'], members)
        assert not result['decoded'] and not result['unresolved'] and stream['features'] == before
        report['legacy_controls'].append({'archive': filename, 'no_new_rows_diagnostics_or_feature_mutation': True})
    report['runtime_source_sha256'] = {name: digest(ROOT/name) for name in (
        'decode_mesh_combine.py', 'decode_mesh_contents.py', 'decode_mesh_geometry_variants.py',
        'decode_mesh_selections.py', 'decode_retained_mesh_sources.py', 'validate_mesh_combine.py')}
    report['summary'] = {'actual_saved_exports': 3, 'typed_operation_controls': 3,
        'actual_default_configured_end_and_rolled_control_readbacks': api_checks,
        'exact_retained_tool_array_controls': retained_checks, 'exact_additional_asset_array_controls': additional_checks,
        'exact_current_geometry_array_and_volume_controls': current_checks,
        'retained_Cut_strict_geometry_failures': 1, 'retained_global_tool_diagnostics': 3,
        'full_feature_payload_replays': 3, 'malformed_guards': len(report['malformed_guards']),
        'legacy_controls': 2, 'feature_mutations': 0, 'native_algorithm_or_flag_mapping_claims': 0,
        'mesh_combine_current_owner_claims': 0, 'live_API_calls': 0}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--zstd-library')
    parser.add_argument('--output', type=Path, default=ROOT/'mesh-combine-decoding.json')
    args = parser.parse_args()
    zstd = args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result = validate(zstd)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['summary'], sort_keys=True))
