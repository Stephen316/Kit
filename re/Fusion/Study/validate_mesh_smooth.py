"""Three actual Smooth controls, current geometry and independent normal-pool holdouts."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from decode_mesh_contents import replay_paramesh_geometry
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_mesh_normals import decode_mesh_normal_pools
from decode_mesh_smooth import decode_mesh_smooth
from validate_mesh_remesh import load
from validate_mesh_normals import _direction_error

ROOT = Path(__file__).resolve().parent
CAPTURE = 'meshsmooths-56f38f13430a'


def validate(root,zstd):
    truth = json.loads((root/CAPTURE/'ground_truth.json').read_text())
    assert (root/CAPTURE/'complete.txt').is_file() and not truth['errors']
    executed = (root/CAPTURE/'executed-generator-source.txt').read_bytes()
    dependency = (root/CAPTURE/'executed-mesh-source-helper.txt').read_bytes()
    assert hashlib.sha256(executed).hexdigest() == truth['executed_generator_sha256']
    assert hashlib.sha256(dependency).hexdigest() == truth['mesh_source_helper_sha256']
    journal_path = root/CAPTURE/'journal.jsonl'
    journal = [json.loads(line) for line in journal_path.read_text().splitlines() if line]
    closes = [row for row in journal if row['phase'] == 'owned_document_close_returned']
    assert len(closes) == 3 and all(row['returned'] is True and row['save'] is False for row in closes)
    assert journal[-1]['phase'] == 'batch_terminal' and journal[-1]['sample_count'] == 3 and journal[-1]['error_count'] == 0
    report = dict(interface='decode_mesh_smooth(data,records,features,member,members,mesh_contents=None) -> decoded/unresolved/scope; rows feature_object_id/kind/name/settings',
        capture=CAPTURE,executed_generator_sha256=truth['executed_generator_sha256'],
        mesh_source_helper_sha256=truth['mesh_source_helper_sha256'],journal_sha256=hashlib.sha256(journal_path.read_bytes()).hexdigest(),
        actual_terminal_journal=journal[-1],actual_document_close_journal=closes,samples=[],old_controls=[],guards=[],
        source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in (
            'GenerateMeshSmoothContrasts.py','decode_mesh_smooth.py','validate_mesh_smooth.py',
            'decode_mesh_selections.py','decode_mesh_geometry_variants.py','decode_mesh_contents.py','decode_parameters.py',
            'decode_mesh_normals.py','validate_mesh_remesh.py','validate_mesh_normals.py')})
    saved = None
    for sample in truth['samples']:
        archive = CAPTURE+'/'+sample['file']
        loaded = load(root,archive,zstd)
        data,records,features,member,members = loaded
        before = copy.deepcopy(features)
        meshes = decode_mesh_contents_variants(data,records,member,members)
        assert not meshes['unresolved'] and len(meshes['decoded']) == 1
        decoded = decode_mesh_smooth(data,records,features,member,members,meshes)
        assert not decoded['unresolved'] and len(decoded['decoded']) == 1,decoded
        row = decoded['decoded'][0];settings = row['settings'];mesh = meshes['decoded'][0];geometry = mesh['geometry']
        actual = sample['feature_before_node'];parameter = sample['model_parameters_after'][0]
        source = sample['source_before_smooth'];current = sample['component_meshes_after_smooth']['meshes'][0]
        source_polygon = source['original_polygon_mesh'];current_polygon = current['original_polygon_mesh']
        normals = decode_mesh_normal_pools(meshes)
        assert len(normals['decoded']) == 1 and not normals['unresolved'],normals
        pool = normals['decoded'][0];flat = current['display_triangle_mesh']['normalVectorsAsDouble']
        api_normals = [flat[i:i+3] for i in range(0,len(flat),3)]
        direction_error = _direction_error(pool['derived_asset_unit_vectors'],api_normals)
        magnitude_error = max(abs(math.hypot(*v)*pool['native_uniform_scale']-1) for v in api_normals)
        covector_error = max(min(max(abs(x-y) for x,y in zip(p,q)) for q in api_normals) for p in pool['derived_component_covectors'])
        checks = dict(
            export_hash_exact=hashlib.sha256((root/archive).read_bytes()).hexdigest() == sample['export']['sha256'],
            success_and_document_close=sample['smooth_status'] == 'FeatureReturned' and sample['close_owned_document_returned'] is True,
            no_top_level_getter_setter_errors=sample['getter_errors'] == [] and sample['setter_errors'] == [],
            actual_healthy=sample['feature_at_timeline_end']['healthState'] == 0 and sample['feature_at_timeline_end']['errorOrWarningMessage'] == '',
            actual_input_and_rollback_feature_handle_equal=sample['input_mesh_equals_import_handle'] is True and sample['feature_input_mesh_equals_import_handle'] is True,
            requested_actual_native_smoothness_agree=sample['requested']['smoothness'] == sample['requested_value_input']['realValue'] == sample['input_before_add']['smoothness']['realValue'] == actual['smoothness']['value'] == settings['smoothness'],
            one_owned_unitless_parameter= len(sample['model_parameters_after']) == 1 and parameter['role'] == 'Smoothness' and parameter['value'] == settings['smoothness'] and parameter['unit'] == '' and parameter['createdBy']['name'] == row['name'],
            parameter_name_matches_native=settings['scalar_binding']['parameter_name'] == parameter['name'],
            control_getter_errors_absent=sample['input_before_add']['control_getter_errors'] == [] and actual['control_getter_errors'] == [],
            actual_BRep_results_empty=actual['brep_bodies'] == [] and actual['brep_faces'] == [],
            source_and_current_counts_six_eight=source_polygon['nodeCount'] == current_polygon['nodeCount'] == geometry['node_count'] == 6 and source_polygon['triangleCount'] == current_polygon['triangleCount'] == geometry['triangle_count'] == 8,
            actual_current_ordered_coordinates_exact=[x for p in geometry['component_node_coordinates_cm'] for x in p] == current_polygon['nodeCoordinatesAsDouble'],
            actual_current_ordered_indices_exact=geometry['triangle_node_indices'] == current_polygon['triangleNodeIndices'],
            actual_current_volume_within_float64_roundoff=math.isclose(geometry['derived_signed_volume_cm3'],current['volume'],rel_tol=1e-14,abs_tol=0),
            actual_current_arrays_and_volume_change=source_polygon['nodeCoordinatesAsDouble'] != current_polygon['nodeCoordinatesAsDouble'] and source['volume'] > current['volume'] > 0,
            selected_current_asset_exact=settings['native_mesh_object_id'] == mesh['mesh_object_id'] and settings['current_mesh_asset']['asset_object_id'] == mesh['asset_object_id'],
            BaseMesh_owner_separate=settings['current_mesh_native_feature_owner_object_id'] == mesh['feature_object_id'] != row['feature_object_id'] and settings['mesh_smooth_owns_current_mesh'] is None,
            additional_asset_temporal_role_unknown=settings['additional_asset_temporal_role'] is None,
            actual_display_normal_direction_set_holdout=direction_error < 1e-7,
            actual_display_normal_covector_magnitude_holdout=magnitude_error < 1e-7 and covector_error < 1e-6,
            normal_pool_packed_pair_replay=b''.join(struct.pack('<2f',*pair) for pair in pool['stored_packed_pairs_float32']).hex() == pool['stored_payload_hex'],
            features_unchanged=features == before)
        for key in ('current_mesh_asset','additional_stored_asset'):
            asset = settings[key];checks[key+'_exact_buffer_replay'] = replay_paramesh_geometry(asset['geometry']) == members[asset['asset_member']]
        assert all(checks.values()),(archive,checks,direction_error,magnitude_error,covector_error)
        report['samples'].append(dict(archive=archive,expected_decoded=decoded,expected_mesh_contents=meshes,
            expected_normal_pools=normals,export_sha256=sample['export']['sha256'],checks=checks,
            actual_input=sample['input_before_add'],actual_parameters=sample['model_parameters_after'],
            actual_source_polygon_mesh=source_polygon,actual_current_polygon_mesh=current_polygon,
            actual_source_and_current_volumes_cm3=[source['volume'],current['volume']],
            volume_roundoff=dict(native_derived_cm3=geometry['derived_signed_volume_cm3'],API_current_cm3=current['volume'],
                absolute_error_cm3=abs(geometry['derived_signed_volume_cm3']-current['volume']),
                relative_error=abs(geometry['derived_signed_volume_cm3']-current['volume'])/current['volume']),
            normal_holdout=dict(direction_set_max_component_error=direction_error,inverse_scale_magnitude_max_error=magnitude_error,
                component_covector_max_error=covector_error,stored_vector_count=pool['stored_unit_vector_count'],actual_display_normal_count=len(api_normals),
                association_scope='Unordered direction/covector numerical corroboration only; no pool order, corner or vertex association')))
        if sample['case'] == 'smooth_default_point_zero_two':saved = loaded,decoded,meshes
    for report_name,archive,key in (
        ('mesh-decoding.json','meshcontrasts-10c2557c91a3/stl_centimeter.f3d','expected_decoded'),
        ('mesh-reduce-decoding.json','meshreduces-780954a23308/adaptive_count_six.f3d','expected_mesh_contents'),
        ('mesh-remesh-decoding.json','meshremeshes-f07f97514069/adaptive_edge_two.f3d','expected_mesh_contents')):
        golden = next(s for s in json.loads((root/report_name).read_text())['samples'] if s['archive'] == archive)
        data,records,features,member,members = load(root,archive,zstd)
        meshes = decode_mesh_contents_variants(data,records,member,members)
        assert meshes == golden[key],(archive,'Prior mesh dictionary changed')
        empty = decode_mesh_smooth(data,records,features,member,members,meshes)
        assert not empty['decoded'] and not empty['unresolved']
        report['old_controls'].append(dict(archive=archive,old_full_mesh_summary_exact=True,no_false_Smooth=True))
    loaded,decoded,meshes = saved;data,records,features,member,members = loaded
    row = decoded['decoded'][0];settings = row['settings'];by = {r.object_id:r for r in records if r.is_primary}
    def guard(label,identity,offset,replacement):
        changed = bytearray(data);record = by[identity]
        changed[record.body+offset:record.body+offset+len(replacement)] = replacement
        result = decode_mesh_smooth(bytes(changed),records,features,member,members,meshes)
        assert not result['decoded'] and len(result['unresolved']) == 1,(label,result)
        report['guards'].append(dict(check=label,passed=True,reason=result['unresolved'][0]['reason']))
    owner = row['feature_object_id'];binding = settings['scalar_binding']['binding_object_id']
    guard('Feature prefix must be observed',owner,0,b'\1')
    guard('Two assets must remain distinct',owner,24,data[by[owner].body+13:by[owner].body+24])
    guard('Repeated dependency count',owner,130,struct.pack('<I',4))
    guard('Repeated binding must agree',owner,157,struct.pack('<Q',settings['input_selection']['descriptor_object_id']))
    guard('Binding owner must reciprocate',binding,6,struct.pack('<Q',204))
    guard('Parameter numeric copy must agree',binding,21,struct.pack('<d',0.3))
    guard('Binding parameter reference must be typed',binding,30,struct.pack('<Q',204))
    guard('Selection leaf must repeat mesh identity',settings['input_selection']['leaf_object_id'],2,struct.pack('<Q',204))
    guard('Selection proxy must reciprocate feature owner',settings['input_selection']['proxy_object_id'],95,struct.pack('<Q',204))
    report['counts'] = dict(actual_samples=3,successful_native_Smooth_features=3,changed_current_coordinates_with_unchanged_six_eight_counts=3,
        actual_normal_pool_holdouts=3,old_full_mesh_summary_controls=3,malformed_guards=len(report['guards']),full_main_runs=0,live_API_calls=0)
    report['limits'] = [
        'Only Smoothness0.02/0.1/0.25 closed-octahedron captures are admitted. General controls, other layouts and a smoothing algorithm remain unsupported.',
        'Actual current coordinates and volumes change despite counts remaining6nodes/8triangles. Neither density preservation nor geometric behavior is generalized beyond these cached facts.',
        'Smoothness0.1 actual expression0.10000000000000001 is retained as getter evidence; the owned stored/API numeric value is0.1.',
        'Additional asset has exact typed UUID/file/buffer provenance but its temporal/source lifecycle role remains unqualified.',
        'Native BaseMeshFeature remains the independently decoded current mesh owner. API baseOrFormFeature and general regeneration are not inferred.',
        'Normal pool holdouts compare saved display direction sets and inverse uniform-scale magnitudes; serialized pool order and per-node/corner identity remain unresolved.']
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__);parser.add_argument('--zstd-library',required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'mesh-smooth-decoding.json')
    args=parser.parse_args();report=validate(ROOT,args.zstd_library)
    args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['counts']))
