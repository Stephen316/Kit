"""Actual Faceted positive controls, failed Prismatic negative and typed guards."""
import hashlib
import json
import math
from pathlib import Path
import struct
import argparse

from asm_records import inspect_asm
from decode_brep import decode_topology
from decode_mesh_convert import CONVERT, decode_mesh_convert
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_mesh_selections import decode_mesh_selection
from decode_retained_mesh_sources import decode_retained_mesh_source
from discover_features import discover_features
from fusion_archive import read_members
from fusion_metadata import design_records

CAPTURE = 'meshconverts-4b42d39fb1d5'


def validate(zstd):
    root = Path(__file__).resolve().parent
    folder = root/CAPTURE
    truth = json.loads((folder/'ground_truth.json').read_text())
    checks, samples, guards = [], [], []
    def check(label, condition, **evidence):
        if not condition:
            raise AssertionError(label)
        checks.append({'check': label, **evidence})
    def load(path):
        members = read_members(path, zstd)
        member = next(k for k in members if k.endswith('/FusionDesignSegmentType1/BulkStream.dat'))
        data = members[member]
        records, index = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
        features = []
        discover_features(data, records, features, index)
        return data, records, features, member, members
    check('Actual terminal3 exports', (folder/'complete.txt').is_file() and len(truth['samples']) == 3)
    check('Executed generator snapshot hash', hashlib.sha256((folder/'executed-generator-source.txt').read_bytes()).hexdigest() == truth['executed_generator_sha256'])
    check('Owned mesh helper source snapshot hash', hashlib.sha256((folder/'executed-mesh-source-helper.txt').read_bytes()).hexdigest() == truth['mesh_source_helper_sha256'])
    check('One actual Prismatic add error preserved', len(truth['errors']) == 1 and truth['errors'][0]['case'] == 'prismatic_closed' and 'MESH_FAILED_BREP' in truth['errors'][0]['error'])
    events = [json.loads(line) for line in (folder/'journal.jsonl').read_text().splitlines()]
    closes = [e for e in events if e['phase'] == 'owned_document_close_returned']
    check('Three actual owned closeFalse calls returnedtrue', len(closes) == 3 and all(e['returned'] is True and e['save'] is False for e in closes))
    for sample in truth['samples']:
        archive = CAPTURE+'/'+sample['file']
        path = root/archive
        check(archive+' exported source hash', hashlib.sha256(path.read_bytes()).hexdigest() == sample['export']['sha256'])
        data, records, features, member, members = load(path)
        original_hash = hashlib.sha256(data).hexdigest()
        prior_mesh = decode_mesh_contents_variants(data, records, member, members)
        decoded = decode_mesh_convert(data, records, features, member, members)
        check(archive+' existing general mesh summary unchanged', prior_mesh == decode_mesh_contents_variants(data, records, member, members))
        check(archive+' timeline restored beforeexport', sample['timeline_count'] == sample['timeline_marker_position'])
        input_truth = sample['input_before_add']
        check(archive+' actual explicit parametric input operation', input_truth['meshConvertOperationType'] == 0)
        api_evidence = {}
        if sample['case'] == 'prismatic_closed':
            check(archive+' no persisted Convert feature invented for actual failure', not any(r.is_primary and r.class_guid == CONVERT for r in records) and not decoded['decoded'] and not decoded['unresolved'])
            check(archive+' negative remains source mesh only', sample['convert_status'] == 'AttemptError' and sample['component_brep_after_convert']['count'] == 0 and sample['component_meshes_after_convert']['count'] == 1)
            api_evidence = {'actual_attempt_error': sample['convert_error'], 'native_Convert_feature_persisted': False}
        else:
            check(archive+' successful native feature graph', len(decoded['decoded']) == 1 and not decoded['unresolved'])
            row = decoded['decoded'][0]; settings = row['settings']; source = settings['qualified_source_mesh']
            feature_api = sample['feature_at_timeline_end']
            check(archive+' actual Faceted method and parametric getter', input_truth['meshConvertMethodType'] == feature_api['meshConvertMethodType'] == 0 and feature_api['isParametric'] is True and settings['mesh_convert_method'] == 'Faceted')
            check(archive+' actual healthy feature name', row['name'] == feature_api['name'] and feature_api['healthState'] == 0 and feature_api['errorOrWarningMessage'] == '')
            check(archive+' native input customname equals actual source', source['name'] == sample['source_before_convert']['name'] == feature_api['inputBodies'][0]['name'])
            check(archive+' actual input meshhandle agrees', sample['input_body_equals_import_handle'] is True)
            polygon = sample['source_before_convert']['original_polygon_mesh']
            check(archive+' retained source exact originalAPI coordinates', sum(source['geometry']['component_node_coordinates_cm'], []) == polygon['nodeCoordinatesAsDouble'])
            check(archive+' retained source exact originalAPI triangleindices', source['geometry']['triangle_node_indices'] == polygon['triangleNodeIndices'])
            check(archive+' retained source NOT current collection member', source['retained_membership_status'] == 'NotInCountedMembers' and source['retained_owner_collection_member_ids'] == [] and source['stored_current_collection_member_count'] == sample['component_meshes_after_convert']['count'] == 0)
            check(archive+' prior general mesh prefix rejection remains explicit', len(prior_mesh['unresolved']) == 1 and prior_mesh['unresolved'][0]['reason'] == 'Unobserved opt-in native mesh prefix')
            check(archive+' explicit result body and source mesh identities distinct', settings['result_native_body_object_id'] != source['mesh_object_id'])
            check(archive+' controller UUID agrees owned resultanchor', settings['history_controller_uuid'] == settings['result_body_anchor']['native_uuid_text'] and settings['result_body_anchor']['source_owner_object_id'] == row['feature_object_id'])
            mapping = settings['stored_asm_body_identifier']
            binding = mapping['bindings'][0]
            check(archive+' stored ASM BODY ID uses explicit native handle not ordinal', binding['native_body_object_id'] == settings['result_native_body_object_id'] and binding['asm_stored_entity_id'] == binding['stored_handle'] == (25 if sample['case'] == 'faceted_open' else 30) and binding['asm_body_index'] == 1)
            parsed = inspect_asm(members[mapping['history_blob_member']])
            topology = decode_topology(parsed)
            graphs = [g for g in topology['body_graphs'] if g['body_index'] == binding['asm_body_index']]
            check(archive+' qualified result BODY graph unique', len(graphs) == 1)
            graph = graphs[0]
            api_body = sample['component_brep_after_convert']['bodies'][0]
            check(archive+' actual component and feature BRep bodies independently present', sample['component_brep_after_convert']['count'] == feature_api['brep_bodies']['count'] == 1)
            check(archive+' BRep topology aggregate counts equal actualAPI', graph['counts']['vertex'] == len(api_body['vertices']) == 4 and graph['counts']['edge'] == len(api_body['edges']) == 6 and graph['counts']['face'] == len(api_body['faces']))
            check(archive+' qualified ASM body transform identity', graph['body_transform_is_identity'] is True)
            check(archive+' raw stored vertex set equals actual API numericset after BODYidentity established', sorted(graph['raw_vertex_positions']) == sorted(v['position_cm'] for v in api_body['vertices']))
            surfaces = graph['analytic_surfaces']
            check(archive+' all qualified stored/API faces planar', len(surfaces) == len(api_body['faces']) and all(s['geometry']['kind'] == 'Plane' for s in surfaces) and all(f['geometry']['objectType'] == 'adsk::core::Plane' for f in api_body['faces']))
            stored_normals = [s['geometry']['normal'] for s in surfaces]
            actual_normals = [f['geometry']['normal'] for f in api_body['faces']]
            normal_error = max(min(max(abs(x-y) for x, y in zip(a, b)) for b in actual_normals) for a in stored_normals)
            check(archive+' aggregate stored plane normal set corroborates API after typed resultjoin', normal_error < 1e-14, max_component_deviation=normal_error)
            check(archive+' raw plane origin set equals saved API', sorted(s['geometry']['raw_origin'] for s in surfaces) == sorted(f['geometry']['origin'] for f in api_body['faces']))
            getter_names = {e['getter'] for e in api_body['body_getter_errors']}
            check(archive+' nonexistent BRepBody.tempId capture error retained', 'tempId' in getter_names and api_body['tempId'] is None)
            if sample['case'] == 'faceted_open':
                check(archive+' open BRep volume getter failure retained without solidvolumeclaim', api_body['isSolid'] is False and api_body['volume'] is None and 'volume' in getter_names)
            else:
                check(archive+' closed BRep actual volume positive', api_body['isSolid'] is True and math.isclose(api_body['volume'], 4., abs_tol=1e-12))
                guard_context = data, records, features, member, members, row
            api_evidence = {'actual_BRep_isSolid': api_body['isSolid'], 'actual_BRep_volume_cm3': api_body['volume'],
                'actual_BRep_getter_errors': api_body['body_getter_errors'], 'qualified_ASM_BODY_graph_counts': graph['counts'],
                'stored_ASM_header_units_in_mm_literal': parsed['header']['units_in_mm'],
                'coordinate_scope': 'Typed native BODY handle joins the graph before unordered numerical API comparison; no global interpretation of header units or API tempId/native-ID correspondence',
                'inactive_accuracy_input_vs_feature': [input_truth['meshConvertAccuracyType'], feature_api['meshConvertAccuracyType']]}
        check(archive+' native bytes unchanged', hashlib.sha256(data).hexdigest() == original_hash)
        samples.append({'archive': archive, 'expected_decoded': decoded, 'prior_mesh_contents': prior_mesh, 'api_evidence': api_evidence})
    retained_controls = []
    for path in sorted((root/'meshcombines-541ebb6cc93f').glob('*.f3d')):
        data, records, features, member, members = load(path)
        selection = decode_mesh_selection(data, records, 315, 307)
        retained = decode_retained_mesh_source(data, records, 226, selection, member, members)
        check(path.name+' shared retained tool source exact nonmembership', retained['retained_membership_status'] == 'NotInCountedMembers' and retained['retained_owner_collection_member_ids'] == [213] and retained['base_mesh_feature_object_id'] == 231)
        retained_controls.append({'archive': str(path.relative_to(root)), 'expected_retained_source': retained})
    data, records, features, member, members, row = guard_context
    pri = {r.object_id: r for r in records if r.is_primary}
    def guard(name, offset, fmt, value):
        bad = bytearray(data); struct.pack_into(fmt, bad, offset, value)
        result = decode_mesh_convert(bytes(bad), records, features, member, members)
        check(name, not result['decoded'] and bool(result['unresolved']))
        guards.append({'guard': name, 'reason': result['unresolved'][0]['reason']})
    feature = pri[row['feature_object_id']]
    settings = row['settings']
    guard('Reject unobserved Convert header field', feature.body+2, '<I', 1)
    guard('Reject source-list proxy wrongtype', pri[settings['source_list_object_id']].body+4, '<Q', settings['result_native_body_object_id'])
    guard('Reject result body anchor redirected to mesh', pri[settings['result_body_anchor']['object_id']].body+81, '<Q', settings['qualified_source_mesh']['mesh_object_id'])
    controller = pri[settings['history_controller_object_id']]
    guard('Reject owned result/controller UUID mismatch', controller.body+7, '<H', ord('a') if settings['history_controller_uuid'][0] != 'a' else ord('b'))
    guard('Reject native history handle not an ASM BODY ID', pri[settings['native_history_mapping']['mapping_record_object_id']].body+6, '<Q', 31)
    guard('Reject selected retained mesh falsely counted current', next(r for r in records if not r.is_primary and r.object_id == settings['qualified_source_mesh']['retained_mesh_collection_object_id'] and r.class_guid == 'A7AEA631-985B-4DD1-8CE2-DE2C-14B54081').body+1, '<I', 1)
    return {'scope': 'Two saved successful Faceted captures plus one failed Prismatic export; three Combine retained-tool controls. No live API or full main-corpus run',
        'sample_count': 3, 'decoded_convert_feature_count': 2, 'actual_failed_Prismatic_count': 1,
        'qualified_result_BRep_BODY_count': 2, 'qualified_retained_source_count': 5,
        'check_count': len(checks), 'malformed_guard_count': len(guards), 'samples': samples,
        'retained_source_controls': retained_controls, 'checks': checks, 'malformed_guards': guards,
        'limitations': ['Faceted layout only; no independently varied native method enum or operation enum mapping',
            'Prismatic add failed withMESH_FAILED_BREP and persisted no Convert class', 'General mesh_contents diagnostic intentionally unchanged',
            'Retained selected source is not a current mesh collection member', 'ASM controller labels/tables remain literal',
            'No inactive Organic setting, API tempId/native-ID identity, global ASM unit interpretation or regeneration/lifecycle claim'],
        'source_sha256': {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ('decode_mesh_convert.py', 'decode_retained_mesh_sources.py')}}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--zstd-library'); parser.add_argument('--output', default='mesh-convert-decoding.json')
    args = parser.parse_args(); result = validate(args.zstd_library)
    Path(args.output).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: result[key] for key in ('sample_count', 'decoded_convert_feature_count', 'check_count', 'malformed_guard_count')}))


if __name__ == '__main__':
    main()
