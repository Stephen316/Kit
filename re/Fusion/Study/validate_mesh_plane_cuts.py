"""Focused actual PlaneCut/mesh layout proof and original tetra goldens."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

from fusion_archive import read_members
from fusion_metadata import design_records
from decode_basics import named_features
from discover_features import discover_features
from decode_mesh_contents import decode_mesh_contents, decode_paramesh_geometry, replay_paramesh_geometry
from decode_mesh_geometry_variants import decode_mesh_contents_variants, decode_geometry_layout
from decode_mesh_plane_cuts import decode_mesh_plane_cuts, PLANE_CUT
from decode_placement import transform_point

CAPTURE = 'meshplanecuts-18f2683c83f5'


def validate(zstd):
    root = Path(__file__).resolve().parent
    folder = root/CAPTURE
    truth = json.loads((folder/'ground_truth.json').read_text())
    checks, samples, guards = [], [], []
    def check(name, condition, **evidence):
        if not condition:
            raise AssertionError(name)
        checks.append({'check': name, **evidence})
    def load(path):
        members = read_members(path, zstd)
        member = next(k for k in members if k.endswith('/FusionDesignSegmentType1/BulkStream.dat'))
        records, index = design_records(members[member], members[member.replace('BulkStream.dat', 'MetaStream.dat')])
        features = named_features(members[member], records)
        discover_features(members[member], records, features, index)
        return members[member], records, features, member, members
    check('Three successful actual PlaneCut exports/zero case errors/terminal', len(truth['samples']) == 3 and truth['errors'] == [] and (folder/'complete.txt').is_file())
    check('Executed source snapshot SHA equals capture truth', hashlib.sha256((folder/'executed-generator-source.txt').read_bytes()).hexdigest() == truth['executed_generator_sha256'])
    check('Mesh source dependency snapshot SHA equals capture truth', hashlib.sha256((folder/'executed-mesh-source-helper.txt').read_bytes()).hexdigest() == truth['mesh_source_helper_sha256'])
    check('Owned STL SHA equals capture truth', hashlib.sha256((folder/'owned-tetra.stl').read_bytes()).hexdigest() == truth['source_mesh']['sha256'])
    events = [json.loads(line) for line in (folder/'journal.jsonl').read_text().splitlines()]
    closes = [e for e in events if e['phase'] == 'owned_document_close_returned']
    check('Three owned closeFalse calls actually returned true', len(closes) == 3 and all(e['returned'] is True and e['save'] is False for e in closes))
    check('Terminal journal after three completed exports', events[-1]['phase'] == 'batch_complete' and events[-1]['exported_sample_count'] == 3)
    for sample in truth['samples']:
        archive = CAPTURE+'/'+sample['file']; path = root/archive
        check(archive+' export hash', hashlib.sha256(path.read_bytes()).hexdigest() == sample['export']['sha256'])
        data, records, features, member, members = load(path)
        original_hash = hashlib.sha256(data).hexdigest()
        meshes = decode_mesh_contents_variants(data, records, member, members)
        result = decode_mesh_plane_cuts(data, records, features, member, members, meshes)
        check(archive+' full explicit feature/mesh routes', len(result['decoded']) == 1 and not result['unresolved'] and not meshes['unresolved'])
        row = result['decoded'][0]; settings = row['settings']; api = sample['feature_at_timeline_end']; inp = sample['input_before_add']
        check(archive+' actual feature name', row['name'] == api['name'])
        check(archive+' native cut code equals actual input and feature', settings['stored_mesh_plane_cut_type_code'] == api['meshPlaneCutType'] == inp['meshPlaneCutType'])
        check(archive+' native fill code equals actual input and feature', settings['stored_mesh_plane_cut_fill_type_code'] == api['meshPlaneCutFillType'] == inp['meshPlaneCutFillType'])
        check(archive+' unvaried native flip explicitly unresolved', api['isFlip'] is False and inp['isFlip'] is False and settings['is_flip'] is None)
        check(archive+' healthy actual feature', api['healthState'] == 0 and api['errorOrWarningMessage'] == '' and sample['plane_cut_status'] == 'FeatureReturned')
        check(archive+' source input and selected plane handle identity checks', sample['input_mesh_equals_import_handle'] is True and sample['input_plane_equals_owned_plane'] is True)
        plane = settings['selected_plane']
        check(archive+' actual selected-plane origin/normal', plane['origin_cm'] == sample['cut_plane']['origin_cm'] == inp['cutPlane']['origin_cm'] and plane['normal'] == sample['cut_plane']['normal'] == inp['cutPlane']['normal'])
        check(archive+' plane custom name', plane['name'] == sample['cut_plane']['name'])
        check(archive+' restored timeline before export', sample['timeline_marker_position'] == sample['timeline_count'])
        check(archive+' no source mesh BaseFeature association invented', sample['source_before_cut']['baseOrFormFeature'] is None)
        expected_current = sample['component_meshes_after_cut']['meshes']
        check(archive+' ordered native/current API mesh collection counts', len(meshes['decoded']) == sample['component_meshes_after_cut']['count'] == len(expected_current))
        mesh_evidence = []
        for native, actual in zip(meshes['decoded'], expected_current):
            geometry = native['geometry']; polygon = actual['original_polygon_mesh']
            label = archive+' mesh'+str(native['mesh_object_id'])
            if native['name']:
                check(label+' stored custom name matches actual API', native['name'] == actual['name'])
            check(label+' exact original API coordinate array', sum(geometry['component_node_coordinates_cm'], []) == polygon['nodeCoordinatesAsDouble'])
            check(label+' exact original API triangle index array', geometry['triangle_node_indices'] == polygon['triangleNodeIndices'])
            check(label+' dimensional counts come from framed byte lengths', geometry['node_count'] == polygon['nodeCount'] and geometry['triangle_count'] == polygon['triangleCount'])
            check(label+' exact literal asset replay', replay_paramesh_geometry(geometry) == members[native['asset_member']])
            check(label+' derived incidence matches actual isClosed/isOriented', geometry['derived_closed_oriented_edge_incidence'] == actual['isClosed'] and actual['isOriented'] is True)
            if actual['isClosed']:
                deviation = abs(geometry['derived_signed_volume_cm3']-actual['volume'])
                check(label+' derived closed volume matches API within floating accumulation', math.isclose(geometry['derived_signed_volume_cm3'], actual['volume'], abs_tol=1e-12), measured_deviation_cm3=deviation)
            else:
                check(label+' open signed sum never published as enclosed volume', 'derived_signed_volume_cm3' not in geometry and 'derived_absolute_volume_cm3' not in geometry and geometry['derived_enclosed_volume_cm3'] is None and actual['volume'] == 0)
            mesh_evidence.append({'mesh_object_id': native['mesh_object_id'], 'node_count': polygon['nodeCount'], 'triangle_count': polygon['triangleCount'],
                                 'closed': actual['isClosed'], 'API_collection_position_scope': 'Native ordered collection/typed result route compared to saved ordered API array; coordinates do not choose identity'})
        current = next(m for m in meshes['decoded'] if m['mesh_object_id'] == settings['qualified_current_mesh_object_id'])
        extra = settings['additional_stored_asset']['geometry']
        extra_points = [transform_point(current['asset_coordinates_to_component_matrix'], point) for point in extra['stored_node_coordinates_float32']]
        pre_cut = sample['source_before_cut']['original_polygon_mesh']
        check(archive+' additional stored asset coordinates independently match actual pre-cut source snapshot', sum(extra_points, []) == pre_cut['nodeCoordinatesAsDouble'])
        check(archive+' additional stored asset triangle order independently matches pre-cut source snapshot', extra['triangle_node_indices'] == pre_cut['triangleNodeIndices'])
        check(archive+' source bytes remain unchanged', hashlib.sha256(data).hexdigest() == original_hash)
        samples.append({'archive': archive, 'expected_decoded': result, 'expected_mesh_contents': meshes,
                        'export_sha256': sample['export']['sha256'], 'actual_mesh_layout_evidence': mesh_evidence})
        if sample['case'] == 'trim_minimal_fill':
            guard_context = data, records, features, member, members, meshes, row
    old = json.loads((root/'mesh-decoding.json').read_text())
    for sample in old['samples']:
        data, records, features, member, members = load(root/sample['archive'])
        check(sample['archive']+' strict-default golden exact after factoring', decode_mesh_contents(data, records, member, members) == sample['expected_decoded'])
        check(sample['archive']+' opt-in wrapper preserves complete old dictionary/scope exact', decode_mesh_contents_variants(data, records, member, members) == sample['expected_decoded'])
    reduce_controls = []
    for folder_name in ('meshreduces-780954a23308', 'meshreduces-8f01528f7f21'):
        for path in sorted((root/folder_name).glob('*.f3d')):
            data, records, features, member, members = load(path)
            summary = decode_mesh_contents_variants(data, records, member, members)
            check(path.parent.name+'/'+path.name+' bounded6/8 mesh ownership/asset layout', len(summary['decoded']) == 1 and not summary['unresolved'] and summary['decoded'][0]['geometry']['node_count'] == 6 and summary['decoded'][0]['geometry']['triangle_count'] == 8)
            continued = [b for b in summary['decoded'][0]['geometry']['buffers'] if 'decompression_scope' in b]
            for block in continued:
                check('Opaque auxiliary bounded prefix continuation never allowed in geometry/index buffers', block['buffer_ordinal'] >= 2 and block['bounded_plus_one_probe_size_bytes'] == block['declared_size_bytes']+1)
            reduce_controls.append({'archive': str(path.relative_to(root)), 'continued_auxiliary_buffer_ordinals': [b['buffer_ordinal'] for b in continued]})
    data, records, features, member, members, meshes, row = guard_context
    feature_record = next(r for r in records if r.is_primary and r.object_id == row['feature_object_id'])
    def bad_native(name, offset, fmt, value):
        altered = bytearray(data); struct.pack_into(fmt, altered, offset, value)
        result = decode_mesh_plane_cuts(bytes(altered), records, features, member, members, meshes)
        check(name, not result['decoded'] and bool(result['unresolved']))
        guards.append({'guard': name, 'reason': result['unresolved'][0]['reason']})
    bad_native('Reject unobserved PlaneCut mode', feature_record.body+2, '<I', 2)
    bad_native('Reject unobserved PlaneCut fill', feature_record.body+138, '<I', 2)
    bad_native('Reject current asset redirected to additional source asset', feature_record.body+167, '<Q', row['settings']['additional_stored_asset']['asset_object_id'])
    source = row['settings']['source_mesh_selection']
    leaf_record = next(r for r in records if r.is_primary and r.object_id == source['leaf_object_id'])
    bad_native('Reject source descriptor direct mesh/identity leaf disagreement', leaf_record.body+2, '<Q', 202)
    plane_leaf = next(r for r in records if r.is_primary and r.object_id == row['settings']['selected_plane']['leaf_object_id'])
    bad_native('Reject selected plane identity leaf redirected to mesh', plane_leaf.body+2, '<Q', source['mesh_object_id'])
    asset = meshes['decoded'][0]['geometry']; blob = members[meshes['decoded'][0]['asset_member']]
    first = asset['buffers'][0]; descriptor_size = len(bytes.fromhex(first['descriptor_hex']))
    corrupted = bytearray(blob); struct.pack_into('<I', corrupted, first['asset_offset']+14+descriptor_size, first['uncompressed_size']-4)
    try:
        decode_paramesh_geometry(bytes(corrupted), geometry_decoder=decode_geometry_layout)
    except ValueError as error:
        check('Reject position buffer extent mismatch even in opt-in', True); guards.append({'guard': 'Strict geometry buffer extent', 'reason': str(error)})
    else:
        raise AssertionError('Geometry LZMA extent guard failed')
    return {'scope': 'Three actual PlaneCut files, original three exact-default controls and four saved Reduce geometry controls; no full main corpus run',
        'sample_count': len(samples), 'decoded_feature_count': 3, 'decoded_current_mesh_count': 4,
        'decoded_current_node_count': 18, 'decoded_current_triangle_count': 19,
        'check_count': len(checks), 'malformed_guard_count': len(guards),
        'samples': samples, 'checks': checks, 'malformed_guards': guards, 'reduce_geometry_controls': reduce_controls,
        'count_framing_findings': 'No independent metadata vertex/triangle scalar count proved. Dynamic uncompressed lengths48/72 bytes for Float32 triples and36/48/96 bytes for Int32 triangle triples establish counts. Buffer kind4 remains4 across4/3,4/4 and6/8 and must not be called a count.',
        'auxiliary_prefix_scope': 'Only opaque buffers2..5 may expose a declared-size prefix when a bounded+1 probe continues. Positions and triangle indices retain strict full declared-size/+1 extent validation.',
        'limitations': ['Only captured shape tuples accepted; arbitrary meshes unsupported', 'Flip remains native-encoding unknown; actual API false in all3',
            'No feature.cutPlane getter exists; actual input/ConstructionPlane/native selected-plane evidence used',
            'Additional stored asset matches actual pre-cut arrays in captures but has no universal lifecycle label',
            'Normals/auxiliary transformations, regeneration and unofficial API stability unresolved'],
        'source_sha256': {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ('decode_mesh_contents.py', 'decode_mesh_geometry_variants.py', 'decode_mesh_plane_cuts.py', 'decode_mesh_selections.py')}}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--zstd-library'); parser.add_argument('--output', default='mesh-plane-cut-decoding.json')
    args = parser.parse_args(); result = validate(args.zstd_library)
    Path(args.output).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: result[key] for key in ('sample_count', 'decoded_feature_count', 'decoded_current_mesh_count', 'check_count', 'malformed_guard_count')}))


if __name__ == '__main__':
    main()
