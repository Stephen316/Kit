"""Actual open/closed Shell thickness controls and independently captured dense meshes."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from decode_mesh_contents import replay_paramesh_geometry, decode_paramesh_framing
from decode_mesh_geometry_variants import decode_mesh_contents_variants, decode_mesh_asset, decode_geometry_layout
from decode_mesh_normals import decode_mesh_normal_pools
from decode_mesh_shell import decode_mesh_shell
from validate_mesh_remesh import load

ROOT = Path(__file__).resolve().parent
CAPTURE = 'meshshells-f5a2d6730f62'


def canonical(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def validate(root,zstd):
    truth = json.loads((root/CAPTURE/'ground_truth.json').read_text())
    assert (root/CAPTURE/'complete.txt').is_file() and not truth['errors']
    assert hashlib.sha256((root/CAPTURE/'executed-generator-source.txt').read_bytes()).hexdigest() == truth['executed_generator_sha256']
    assert hashlib.sha256((root/CAPTURE/'executed-mesh-source-helper.txt').read_bytes()).hexdigest() == truth['mesh_source_helper_sha256']
    journal_path = root/CAPTURE/'journal.jsonl'
    journal = [json.loads(line) for line in journal_path.read_text().splitlines() if line]
    closes = [row for row in journal if row['phase'] == 'owned_document_close_returned']
    assert len(closes) == 3 and all(row['returned'] is True and row['save'] is False for row in closes)
    assert journal[-1]['phase'] == 'batch_terminal' and journal[-1]['sample_count'] == 3 and journal[-1]['error_count'] == 0
    report = dict(interface='decode_mesh_shell(data,records,features,member,members,mesh_contents=None) -> decoded/unresolved/scope; rows feature_object_id/kind/name/settings',
        capture=CAPTURE,executed_generator_sha256=truth['executed_generator_sha256'],mesh_source_helper_sha256=truth['mesh_source_helper_sha256'],
        journal_sha256=hashlib.sha256(journal_path.read_bytes()).hexdigest(),actual_terminal_journal=journal[-1],actual_document_close_journal=closes,
        samples=[],old_controls=[],guards=[],source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in (
            'GenerateMeshShellContrasts.py','decode_mesh_shell.py','validate_mesh_shell.py','decode_mesh_geometry_variants.py',
            'decode_mesh_contents.py','decode_mesh_selections.py','decode_parameters.py','decode_mesh_normals.py','validate_mesh_remesh.py',
            'validate_mesh_shell_normals.py','mesh-shell-normal-decoding.json')})
    saved = None; geometries = {}
    for sample in truth['samples']:
        archive = CAPTURE+'/'+sample['file'];loaded = load(root,archive,zstd)
        data,records,features,member,members = loaded;before = copy.deepcopy(features)
        meshes = decode_mesh_contents_variants(data,records,member,members)
        assert len(meshes['decoded']) == 1 and not meshes['unresolved'],meshes
        decoded = decode_mesh_shell(data,records,features,member,members,meshes)
        assert len(decoded['decoded']) == 1 and not decoded['unresolved'],decoded
        row = decoded['decoded'][0];settings = row['settings'];mesh = meshes['decoded'][0];geometry = mesh['geometry']
        normal_status = decode_mesh_normal_pools(meshes)
        assert len(normal_status['decoded']) == 1 and not normal_status['unresolved']
        normal_evidence = next(row for row in json.loads((root/'mesh-shell-normal-decoding.json').read_text())['samples'] if row['archive'] == archive)
        assert normal_status == normal_evidence['expected_decoded']
        actual = sample['feature_before_node'];parameter = sample['model_parameters_after'][0]
        source = sample['source_before_shell'];current = sample['component_meshes_after_shell']['meshes'][0]
        source_polygon = source['original_polygon_mesh'];polygon = current['original_polygon_mesh']
        closed = sample['requested']['closed_source']
        expected_counts = ((2745,5482) if closed else (2745,5481)) if settings['thickness_cm'] == 0.1 else (1556,3103)
        checks = dict(
            export_hash_exact=hashlib.sha256((root/archive).read_bytes()).hexdigest() == sample['export']['sha256'],
            success_and_actual_close=sample['shell_status'] == 'FeatureReturned' and sample['close_owned_document_returned'] is True,
            no_top_level_getter_setter_errors=sample['getter_errors'] == [] and sample['setter_errors'] == [],
            actual_healthy=sample['feature_at_timeline_end']['healthState'] == 0 and sample['feature_at_timeline_end']['errorOrWarningMessage'] == '',
            input_and_rollback_feature_mesh_handle_equal=sample['input_mesh_equals_import_handle'] is True and sample['feature_input_mesh_equals_import_handle'] is True,
            requested_actual_native_thickness_agree=sample['requested']['thickness_cm'] == sample['requested_value_input']['realValue'] == sample['input_before_add']['thickness']['realValue'] == actual['thickness']['value'] == settings['thickness_cm'],
            one_owned_mm_parameter=len(sample['model_parameters_after']) == 1 and parameter['role'] == 'Thickness' and parameter['value'] == settings['thickness_cm'] and parameter['unit'] == 'mm' and parameter['createdBy']['name'] == row['name'],
            parameter_name_matches_native=settings['scalar_binding']['parameter_name'] == parameter['name'],
            actual_control_getters_healthy=sample['input_before_add']['control_getter_errors'] == [] and actual['control_getter_errors'] == [],
            actual_BRep_results_empty=actual['brep_bodies'] == [] and actual['brep_faces'] == [],
            source_has_four_nodes_and_correct_facets=source_polygon['nodeCount'] == 4 and source_polygon['triangleCount'] == (4 if closed else 3) and source['isClosed'] is closed,
            actual_current_counts_match_native=(polygon['nodeCount'],polygon['triangleCount']) == (geometry['node_count'],geometry['triangle_count']) == expected_counts,
            actual_current_ordered_coordinates_exact=[x for point in geometry['component_node_coordinates_cm'] for x in point] == polygon['nodeCoordinatesAsDouble'],
            actual_current_ordered_indices_exact=geometry['triangle_node_indices'] == polygon['triangleNodeIndices'],
            actual_current_closedness_matches_native=current['isClosed'] == settings['current_cache_is_closed'] == geometry['derived_closed_oriented_edge_incidence'],
            actual_dense_geometry_differs_from_source=polygon['nodeCount'] > source_polygon['nodeCount'] and polygon['triangleCount'] > source_polygon['triangleCount'],
            selected_current_asset_exact=settings['native_mesh_object_id'] == mesh['mesh_object_id'] and settings['current_mesh_asset']['asset_object_id'] == mesh['asset_object_id'],
            BaseMesh_owner_separate=settings['current_mesh_native_feature_owner_object_id'] == mesh['feature_object_id'] != row['feature_object_id'] and settings['mesh_shell_owns_current_mesh'] is None,
            additional_temporal_role_unknown=settings['additional_asset_temporal_role'] is None,features_unchanged=features == before)
        volume_observation = dict(API_volume_cm3=current['volume'],API_isClosed=current['isClosed'])
        if current['isClosed']:
            native_volume = geometry['derived_signed_volume_cm3']
            checks['closed_current_volume_matches_API_within_roundoff'] = math.isclose(native_volume,current['volume'],rel_tol=1e-12,abs_tol=0)
            volume_observation.update(native_derived_volume_cm3=native_volume,absolute_roundoff_cm3=abs(native_volume-current['volume']))
        else:
            checks['open_current_not_promoted_to_enclosed_volume'] = current['volume'] == 0 and geometry['derived_enclosed_volume_cm3'] is None
            volume_observation.update(raw_triangle_determinant_sum_cm3=geometry['raw_signed_tetrahedral_sum_cm3'],native_enclosed_volume_cm3=None)
        for key in ('current_mesh_asset','additional_stored_asset'):
            asset = settings[key];checks[key+'_exact_buffer_replay'] = replay_paramesh_geometry(asset['geometry']) == members[asset['asset_member']]
        assert all(checks.values()),(archive,checks)
        report['samples'].append(dict(archive=archive,expected_decoded=decoded,expected_mesh_contents=meshes,
            expected_normal_pools=normal_status,normal_holdout_proof=normal_evidence['proof'],export_sha256=sample['export']['sha256'],checks=checks,actual_input=sample['input_before_add'],actual_parameters=sample['model_parameters_after'],
            actual_source_polygon_mesh_sha256=canonical(source_polygon),actual_current_polygon_mesh_sha256=canonical(polygon),
            actual_source_counts=[source_polygon['nodeCount'],source_polygon['triangleCount']],
            actual_current_counts=[polygon['nodeCount'],polygon['triangleCount']],actual_source_isClosed=source['isClosed'],
            volume_observation=volume_observation,actual_requested_source=sample['requested']['source_mesh']))
        geometries[sample['case']] = geometry
        if sample['case'] == 'open_thickness_point_one':saved = loaded,decoded,meshes
    for name,archive in (
        ('mesh-reduce-decoding.json','meshreduces-780954a23308/adaptive_count_six.f3d'),
        ('mesh-remesh-decoding.json','meshremeshes-f07f97514069/adaptive_edge_two.f3d'),
        ('mesh-smooth-decoding.json','meshsmooths-56f38f13430a/smooth_point_one.f3d')):
        golden = next(s for s in json.loads((root/name).read_text())['samples'] if s['archive'] == archive)
        data,records,features,member,members = load(root,archive,zstd)
        meshes = decode_mesh_contents_variants(data,records,member,members)
        assert meshes == golden['expected_mesh_contents']
        empty = decode_mesh_shell(data,records,features,member,members,meshes)
        assert not empty['decoded'] and not empty['unresolved']
        report['old_controls'].append(dict(archive=archive,old_full_mesh_summary_exact=True,no_false_Shell=True))
    loaded,decoded,meshes = saved;data,records,features,member,members = loaded
    row = decoded['decoded'][0];settings = row['settings'];by = {r.object_id:r for r in records if r.is_primary}
    def guard(label,identity,offset,replacement):
        changed = bytearray(data);record = by[identity]
        changed[record.body+offset:record.body+offset+len(replacement)] = replacement
        failed = decode_mesh_shell(bytes(changed),records,features,member,members,meshes)
        assert not failed['decoded'] and len(failed['unresolved']) == 1,(label,failed)
        report['guards'].append(dict(check=label,passed=True,reason=failed['unresolved'][0]['reason']))
    owner = row['feature_object_id'];binding = settings['scalar_binding']['binding_object_id']
    guard('Observed feature prefix',owner,0,b'\1')
    guard('Two assets distinct',owner,24,data[by[owner].body+13:by[owner].body+24])
    guard('Repeated dependency count',owner,130,struct.pack('<I',4))
    guard('Repeated binding reference',owner,157,struct.pack('<Q',settings['input_selection']['descriptor_object_id']))
    guard('Owned scalar binding',binding,6,struct.pack('<Q',204))
    guard('Binding numeric copy',binding,21,struct.pack('<d',0.3))
    guard('Typed parameter reference',binding,30,struct.pack('<Q',204))
    guard('Selected leaf repeats native mesh',settings['input_selection']['leaf_object_id'],2,struct.pack('<Q',204))
    guard('Proxy reciprocal feature owner',settings['input_selection']['proxy_object_id'],95,struct.pack('<Q',204))
    # Geometry/cap guards use only copied buffers or an in-memory asset mutation.
    def geometry_guard(label,callback):
        try:callback()
        except (ValueError,IndexError,struct.error) as error:reason = str(error)
        else:raise AssertionError(label)
        report['guards'].append(dict(check=label,passed=True,reason=reason))
    current_asset = settings['current_mesh_asset'];asset_path = current_asset['asset_member'];blob = members[asset_path]
    geometry_guard('Default uncompressed cap65536 remains unchanged',lambda:decode_paramesh_framing(blob,allow_auxiliary_prefix=True))
    geometry_guard('Opt-in cap cannot exceed131072',lambda:decode_paramesh_framing(blob,max_uncompressed_buffer_size=131073))
    block = current_asset['geometry']['buffers'][1];offset = block['asset_offset']
    descriptor_length = struct.unpack_from('<H',blob,offset+12)[0];size_offset = offset+14+descriptor_length
    altered = bytearray(blob);struct.pack_into('<I',altered,size_offset,65785)
    bad_members = dict(members);bad_members[asset_path] = bytes(altered)
    geometry_guard('Observed wrapper cap65784 rejects declared65785',lambda:decode_mesh_asset(data,records,current_asset['asset_object_id'],member,bad_members))
    def mutated_indices(geometry,mutator):
        idx = list(geometry['triangle_node_indices']);mutator(idx)
        encoded = [idx[i+1]-idx[i] for i in range(len(idx)-1)]+[idx[-1]]
        buffers = [bytes.fromhex(block['uncompressed_payload_hex']) for block in geometry['buffers']]
        buffers[1] = struct.pack('<'+'i'*len(encoded),*encoded)
        framing = dict(buffers=copy.deepcopy(geometry['buffers']))
        framing['buffers'][1]['uncompressed_payload_hex'] = buffers[1].hex()
        return decode_geometry_layout(framing,buffers)
    open_geometry = geometries['open_thickness_point_one']
    closed_geometry = geometries['closed_thickness_point_one']
    geometry_guard('Index outside current node table',lambda:mutated_indices(open_geometry,lambda idx:idx.__setitem__(0,2745)))
    def reverse_first(idx):idx[1],idx[2] = idx[2],idx[1]
    geometry_guard('OpenShell requires captured three boundary edges',lambda:mutated_indices(open_geometry,reverse_first))
    geometry_guard('ClosedShell requires fully reciprocal closed incidence',lambda:mutated_indices(closed_geometry,reverse_first))
    report['counts'] = dict(actual_samples=3,successful_native_Shell_features=3,actual_open_results=2,actual_closed_results=1,actual_dense_normal_pools=3,
        actual_current_nodes=sum(s['actual_current_counts'][0] for s in report['samples']),
        actual_current_triangles=sum(s['actual_current_counts'][1] for s in report['samples']),
        old_full_mesh_summary_controls=3,malformed_guards=len(report['guards']),full_main_runs=0,live_API_calls=0)
    report['limits'] = [
        'Only captured Thickness0.1/0.2cm open-tetrahedron and0.1cm closed-tetrahedron layouts admitted; no general shelling algorithm, mesh density rule or target attainment claim.',
        'Both open-source captures return healthy Shell features but current meshes remain API-open with volume0. No successful feature is equated with closure.',
        'Open-mesh raw triangle determinant sums are retained separately and not treated as enclosed physical volumes.',
        'Current dense mesh remains independently owned by native BaseMeshFeature; additional typed asset temporal/source lifecycle role and API baseOrFormFeature are not inferred.',
        'Source/current complete arrays are checked in exact captured order; API snapshots are hashed without using coordinates to select native topology identities.',
        'Three dense normal pools are independently corroborated by bidirectional spatial-grid direction/covector sets; counts/order do not establish per-node/corner association or unused entries.']
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--zstd-library',required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'mesh-shell-decoding.json')
    args=parser.parse_args();report=validate(ROOT,args.zstd_library)
    args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['counts']))
