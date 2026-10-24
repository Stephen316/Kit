"""Three actual Remesh captures: owned controls, optional parameter and independent current mesh arrays."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import struct

from decode_basics import named_features, attach_parameters
from decode_mesh_contents import replay_paramesh_geometry
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_mesh_remesh import decode_mesh_remesh, REMESH
from decode_parameters import decode_stream
from discover_features import discover_features
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT = Path(__file__).resolve().parent
CAPTURE = 'meshremeshes-f07f97514069'


def load(root, archive, zstd):
    members = read_members(root/archive, zstd)
    member = next(n for n in members if n.endswith('/FusionDesignSegmentType1/BulkStream.dat'))
    data = members[member]
    records, index = design_records(data, members[member.replace('BulkStream.dat','MetaStream.dat')])
    features = named_features(data, records)
    discover_features(data, records, features, index)
    parameters, _ = decode_stream(data, records)
    attach_parameters(data, records, features, parameters)
    return data, records, features, member, members


def validate(root, zstd):
    truth = json.loads((root/CAPTURE/'ground_truth.json').read_text())
    assert (root/CAPTURE/'complete.txt').is_file() and not truth['errors']
    journal_path = root/CAPTURE/'journal.jsonl'
    journal = [json.loads(line) for line in journal_path.read_text().splitlines() if line]
    closes = [row for row in journal if row['phase'] == 'owned_document_close_returned']
    assert len(closes) == 3 and all(row['returned'] is True and row['save'] is False for row in closes)
    assert journal[-1]['phase'] == 'batch_terminal' and journal[-1]['sample_count'] == 3 and journal[-1]['error_count'] == 0
    executed = (root/CAPTURE/'executed-generator-source.txt').read_bytes()
    assert hashlib.sha256(executed).hexdigest() == truth['executed_generator_sha256']
    report = dict(interface='decode_mesh_remesh(data,records,features,member,members,mesh_contents=None) -> decoded/unresolved/scope; rows feature_object_id/kind/name/settings',
        capture=CAPTURE, executed_generator_sha256=truth['executed_generator_sha256'],
        journal_sha256=hashlib.sha256(journal_path.read_bytes()).hexdigest(),
        actual_terminal_journal=journal[-1],actual_document_close_journal=closes,
        samples=[], old_controls=[], guards=[],
        source_sha256={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in (
            'GenerateMeshRemeshContrasts.py','decode_mesh_remesh.py','validate_mesh_remesh.py',
            'decode_mesh_selections.py','decode_mesh_geometry_variants.py','decode_mesh_contents.py','decode_parameters.py')})
    saved = None
    for sample in truth['samples']:
        archive = CAPTURE+'/'+sample['file']
        loaded = load(root,archive,zstd)
        data,records,features,member,members = loaded
        before = copy.deepcopy(features)
        meshes = decode_mesh_contents_variants(data,records,member,members)
        assert not meshes['unresolved'] and len(meshes['decoded']) == 1, meshes
        decoded = decode_mesh_remesh(data,records,features,member,members,meshes)
        assert not decoded['unresolved'] and len(decoded['decoded']) == 1, decoded
        row = decoded['decoded'][0];settings = row['settings']
        mesh = meshes['decoded'][0];geometry = mesh['geometry']
        actual = sample['feature_before_node']
        api_source = sample['source_before_remesh']
        api_current = sample['component_meshes_after_remesh']['meshes'][0]
        source_polygon = api_source['original_polygon_mesh'];current_polygon = api_current['original_polygon_mesh']
        parameters = {p['role']:p for p in sample['model_parameters_after']}
        adaptive = settings['method'] == 'Adaptive'
        input_errors = {e['getter'] for e in sample['input_before_add']['control_getter_errors']}
        checks = dict(
            actual_export_hash_matches=hashlib.sha256((root/archive).read_bytes()).hexdigest() == sample['export']['sha256'],
            actual_success_and_document_close=sample['remesh_status'] == 'FeatureReturned' and sample['close_owned_document_returned'] is True,
            top_level_getter_setter_errors_absent=sample['getter_errors'] == [] and sample['setter_errors'] == [],
            feature_inputs_and_mesh_handle_explicitly_equal=sample['feature_input_mesh_equals_import_handle'] is True and sample['input_mesh_equals_import_handle'] is True,
            actual_native_method_and_target_agree=settings['stored_method_code'] == actual['meshRemeshMethodType'] == sample['input_before_add']['meshRemeshMethodType'] and settings['stored_target_code'] == actual['meshRemeshTargetType'] == sample['input_before_add']['meshRemeshTargetType'] == 1,
            actual_ValueInput_real_matches_native_cm_length=sample['requested_value_input']['realValue'] == sample['input_before_add']['edgeLength']['realValue'] == settings['requested_edge_length_cm'],
            actual_ModelParameters_match_all_native_roles_values_units=all(r['stored_value'] == parameters[role]['value'] and r['display_units'] == parameters[role]['unit'] and parameters[role]['createdBy']['name'] == row['name'] for role,r in settings['scalar_bindings'].items()),
            active_length_API_parameter_and_display_mm_agree=actual['edgeLength']['value'] == settings['requested_edge_length_cm'] and actual['edgeLength']['unit'] == 'mm',
            optional_shape_parameter_presence_matches=len(parameters) == (2 if adaptive else 1) and ('Shape Preservation' in settings['scalar_bindings']) == adaptive,
            Adaptive_shape_or_Uniform_absence_preserved=(actual['shapePreservation']['value'] == settings['shape_preservation'] == 0.5) if adaptive else actual['shapePreservation'] is None and settings['shape_preservation'] is None,
            actual_control_getter_errors_preserved=input_errors == ({'density','shapePreservation'} if adaptive else {'density'}),
            actual_preservation_false_not_inferred_as_decoded_flags=actual['isPreserveSharpEdgesEnabled'] is False and actual['isPreserveBoundariesEnabled'] is False and settings['preserve_sharp_edges'] is None and settings['preserve_boundaries'] is None,
            healthy_empty_warning=sample['feature_at_timeline_end']['healthState'] == 0 and sample['feature_at_timeline_end']['errorOrWarningMessage'] == '',
            actual_BRep_results_empty=actual['brep_bodies'] == [] and actual['brep_faces'] == [],
            source_four_nodes_four_triangles=source_polygon['nodeCount'] == 4 and source_polygon['triangleCount'] == 4,
            actual_current_counts_match_native=geometry['node_count'] == current_polygon['nodeCount'] and geometry['triangle_count'] == current_polygon['triangleCount'],
            actual_current_ordered_coordinates_match_native=[x for p in geometry['component_node_coordinates_cm'] for x in p] == current_polygon['nodeCoordinatesAsDouble'],
            actual_current_ordered_indices_match_native=geometry['triangle_node_indices'] == current_polygon['triangleNodeIndices'],
            actual_current_volume_matches_native=geometry['derived_signed_volume_cm3'] == api_current['volume'],
            actual_current_geometry_differs_from_source=current_polygon['nodeCount'] != source_polygon['nodeCount'] and current_polygon['triangleCount'] != source_polygon['triangleCount'],
            selected_current_asset_explicit=settings['native_mesh_object_id'] == mesh['mesh_object_id'] and settings['current_mesh_asset']['asset_object_id'] == mesh['asset_object_id'],
            BaseMesh_owner_separate_from_Remesh=settings['current_mesh_native_feature_owner_object_id'] == mesh['feature_object_id'] != row['feature_object_id'] and settings['mesh_remesh_owns_current_mesh'] is None,
            temporal_role_and_target_attainment_unknown=settings['additional_asset_temporal_role'] is None and settings['requested_edge_length_target_attained'] is None,
            feature_inputs_not_mutated=features == before)
        for key in ('current_mesh_asset','additional_stored_asset'):
            asset = settings[key]
            checks[key+'_exact_buffer_replay'] = replay_paramesh_geometry(asset['geometry']) == members[asset['asset_member']]
        assert all(checks.values()),(archive,checks)
        report['samples'].append(dict(archive=archive,expected_decoded=decoded,expected_mesh_contents=meshes,
            export_sha256=sample['export']['sha256'],checks=checks,
            actual_input=sample['input_before_add'],actual_parameters=sample['model_parameters_after'],
            actual_feature_control_getter_errors=actual['control_getter_errors'],
            actual_source_polygon_mesh=source_polygon,actual_current_polygon_mesh=current_polygon,
            actual_source_and_current_volumes_cm3=[api_source['volume'],api_current['volume']],
            actual_requested_preservation_flags=[False,False]))
        if sample['case'] == 'adaptive_edge_two':
            saved = loaded,decoded,meshes
    # Old summaries stay exact; new helper admits no false Remesh features.
    control_specs = (
        ('mesh-decoding.json','meshcontrasts-10c2557c91a3/stl_centimeter.f3d','expected_decoded'),
        ('mesh-plane-cut-decoding.json','meshplanecuts-18f2683c83f5/split_body_minimal_fill.f3d','expected_mesh_contents'),
        ('mesh-reduce-decoding.json','meshreduces-780954a23308/adaptive_count_six.f3d','expected_mesh_contents'))
    for report_name,archive,key in control_specs:
        old = next(s for s in json.loads((root/report_name).read_text())['samples'] if s['archive'] == archive)
        data,records,features,member,members = load(root,archive,zstd)
        meshes = decode_mesh_contents_variants(data,records,member,members)
        assert meshes == old[key]
        decoded = decode_mesh_remesh(data,records,features,member,members,meshes)
        assert not decoded['decoded'] and not decoded['unresolved']
        report['old_controls'].append(dict(archive=archive,old_full_mesh_summary_exact=True,no_false_Remesh=True))
    loaded,decoded,meshes = saved
    data,records,features,member,members = loaded
    row = decoded['decoded'][0];settings = row['settings'];by = {r.object_id:r for r in records if r.is_primary}
    def guard(label,identity,offset,replacement):
        changed = bytearray(data);record = by[identity]
        changed[record.body+offset:record.body+offset+len(replacement)] = replacement
        result = decode_mesh_remesh(bytes(changed),records,features,member,members,meshes)
        assert not result['decoded'] and len(result['unresolved']) == 1,(label,result)
        report['guards'].append(dict(check=label,passed=True,reason=result['unresolved'][0]['reason']))
    owner = row['feature_object_id']
    guard('Unobserved native method',owner,4,struct.pack('<I',9))
    guard('Adaptive optional binding marker must match layout',owner,8,b'\0')
    guard('Uncaptured Density target',owner,31,struct.pack('<I',0))
    guard('Uncontrasted preservation literal remains strict',owner,2,b'\1')
    guard('Two assets must remain distinct',owner,46,data[by[owner].body+35:by[owner].body+46])
    guard('Repeated dependency count',owner,152,struct.pack('<I',3))
    edge_binding = settings['scalar_bindings']['Target Edge Length']['binding_object_id']
    guard('Scalar binding ownership',edge_binding,6,struct.pack('<Q',204))
    guard('Scalar binding and parameter copies must agree',edge_binding,21,struct.pack('<d',3.0))
    guard('Typed selection leaf repeats native mesh',settings['input_selection']['leaf_object_id'],2,struct.pack('<Q',204))
    guard('Typed proxy reciprocal feature owner',settings['input_selection']['proxy_object_id'],95,struct.pack('<Q',204))
    report['counts'] = dict(actual_samples=3,Adaptive_features=2,Uniform_features=1,
        current_9node14triangle_caches=2,current_16node28triangle_caches=1,
        old_full_mesh_summary_controls=3,malformed_guards=len(report['guards']),full_main_runs=0,live_API_calls=0)
    report['limits'] = [
        'Both preservation API getters are false in all captures. Stored zero bytes2/3 lack role/true contrasts; production preservation fields remain None.',
        'Density is unobserved and its actual input getters throw. Adaptive input Shape Preservation also throws even though the resulting feature exposes a real owned0.5 parameter. These errors remain captured, never normalized to defaults.',
        'Uniform has no native Shape Preservation binding or ModelParameter; inactive getterNone is preserved without a synthetic0.5 value.',
        'New current arrays/counts and volume are actual cache facts. No reconstructed remeshing algorithm or universal maximum-edge-length guarantee is supplied.',
        'Typed selected mesh remains independently owned by native BaseMeshFeature. The additional asset has exact buffers/UUID/file proof but no qualified historical/source lifecycle role.',
        'Only observed EdgeLength2/1.5cm Adaptive and2cm Uniform are admitted; general values, Density and preservation-enabled modes remain unsupported.']
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zstd-library',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'mesh-remesh-decoding.json')
    args=parser.parse_args();report=validate(ROOT,args.zstd_library)
    args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['counts']))
