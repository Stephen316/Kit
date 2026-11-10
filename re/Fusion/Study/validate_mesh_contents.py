"""Focused real-capture mesh proof, literal replay and six malformed guards."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from fusion_archive import read_members
from fusion_metadata import design_records
from decode_mesh_contents import decode_mesh_contents, decode_paramesh_geometry, replay_paramesh_geometry

CAPTURE = 'meshcontrasts-10c2557c91a3'
FILES = ('stl_centimeter.f3d', 'stl_millimeter.f3d', 'triangle_data_centimeter.f3d')


def validate(zstd):
    root = Path(__file__).resolve().parent
    folder = root/CAPTURE
    truth = json.loads((folder/'ground_truth.json').read_text())
    checks = []
    def check(name, condition, **evidence):
        if not condition:
            raise AssertionError(name)
        checks.append({'check': name, **evidence})
    check('Capture terminal marker and zero case errors', (folder/'complete.txt').is_file() and truth['errors'] == [])
    check('Executed generator snapshot hash equals original capture hash', hashlib.sha256((folder/'executed-generator-source.txt').read_bytes()).hexdigest() == truth['executed_generator_sha256'])
    check('Owned ASCII STL snapshot hash equals capture source hash', hashlib.sha256((folder/'owned-tetra.stl').read_bytes()).hexdigest() == truth['source_mesh']['sha256'])
    events = [json.loads(line) for line in (folder/'journal.jsonl').read_text().splitlines()]
    closes = [e for e in events if e['phase'] == 'owned_document_close_returned']
    check('All three owned documents closed with actual true and saveFalse', len(closes) == 3 and all(e['returned'] is True and e['save'] is False for e in closes))
    check('Journal batch_complete after three local exports', events[-1]['phase'] == 'batch_complete' and events[-1]['exported_sample_count'] == 3)
    samples = []
    for filename in FILES:
        relative = CAPTURE+'/'+filename
        path = folder/filename
        sample = next(s for s in truth['samples'] if s['file'] == filename)
        check(relative+' export SHA', hashlib.sha256(path.read_bytes()).hexdigest() == sample['export']['sha256'])
        members = read_members(path, zstd)
        member = next(k for k in members if k.endswith('/FusionDesignSegmentType1/BulkStream.dat'))
        data = members[member]
        records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
        before = hashlib.sha256(data).hexdigest()
        summary = decode_mesh_contents(data, records, member, members)
        check(relative+' one native mesh and no unresolved routes', len(summary['decoded']) == 1 and summary['unresolved'] == [])
        row = summary['decoded'][0]; geometry = row['geometry']
        api = sample['after_edit']['component_mesh_bodies'][0]
        original = api['original_polygon_mesh']
        check(relative+' custom native mesh name equals actual API name', row['name'] == api['name'])
        check(relative+' raw triangle indices exactly equal actual API order', geometry['triangle_node_indices'] == original['triangleNodeIndices'])
        flat = [v for point in geometry['component_node_coordinates_cm'] for v in point]
        check(relative+' native transformed coordinates exactly equal actual API array', flat == original['nodeCoordinatesAsDouble'])
        check(relative+' node and face counts equal actual API', len(flat)//3 == original['nodeCount'] == 4 and geometry['triangle_count'] == original['triangleCount'] == 4 and original['quadCount'] == original['polygonCount'] == 0)
        check(relative+' typed native feature slot bounded to STL cases', row['feature_object_id'] == (None if filename.startswith('triangle') else 224))
        check(relative+' API null ownership preserved independently', api['baseOrFormFeature'] is None and sample['after_edit']['created_mesh_owner_is_base'] is False)
        check(relative+' native component/mesh collection reciprocal ownership', row['component_object_id'] == 3 and row['collection_mesh_object_ids'] == [row['mesh_object_id']])
        check(relative+' all six LZMA blocks have exact framed literal replay', replay_paramesh_geometry(geometry) == members[row['asset_member']])
        check(relative+' same asset UUID route proven', row['asset_fusion_uuid'] == geometry['fusion_uuid'])
        check(relative+' oriented reciprocal triangle edge incidence agrees with actual API', geometry['derived_closed_oriented_edge_incidence'] and api['isClosed'] is True and api['isOriented'] is True and geometry['derived_undirected_edge_count'] == 6)
        check(relative+' derived signed volume exactly equals actual API volume', geometry['derived_signed_volume_cm3'] == api['volume'])
        area_deviation = abs(geometry['derived_area_cm2']-api['area'])
        check(relative+' measured area deviation bounded without exact equality claim', math.isclose(geometry['derived_area_cm2'], api['area'], rel_tol=5e-8, abs_tol=1e-12), measured_absolute_deviation_cm2=area_deviation)
        bounds_deviation = max(abs(geometry['derived_component_bounds_cm'][k][i]-api['bounding_box_cm'][k][i]) for k in ('min', 'max') for i in range(3))
        check(relative+' API bounding-box precision difference retained', bounds_deviation <= 1e-7, measured_max_deviation_cm=bounds_deviation)
        display = api['display_triangle_mesh']
        display_points = [display['nodeCoordinatesAsDouble'][i:i+3] for i in range(0, 3*display['nodeCount'], 3)]
        def triangle_set(points, indices):
            rows = []
            for i in range(0, len(indices), 3):
                tri = [tuple(points[j]) for j in indices[i:i+3]]
                rows.append(min(tuple(tri[j:]+tri[:j]) for j in range(3)))
            return sorted(rows)
        check(relative+' display triangles independently agree with oriented stored triangles', triangle_set(geometry['component_node_coordinates_cm'], geometry['triangle_node_indices']) == triangle_set(display_points, display['nodeIndices']))
        check(relative+' actual runtime PlaneCut present despite stale defs and no call attempted', sample['runtime_plane_cut_capability']['module_has_MeshPlaneCutFeatures'] is True and sample['runtime_plane_cut_capability']['features_has_meshPlaneCutFeatures'] is True and sample['runtime_plane_cut_capability']['plane_cut_attempted'] is False)
        for phase in ('before_edit', 'during_edit', 'after_edit'):
            state = sample[phase]
            check(relative+' '+phase+' two known SWIG serializer errors retained', {e['getter'] for e in state['getter_errors']} == {'base.meshBodies', 'base.sourceBodies'} and state['base_mesh_bodies'] is None and state['base_brep_source_bodies'] is None)
            check(relative+' '+phase+' BRep result collection is independently empty', state['base_brep_bodies'] == [])
        check(relative+' absent polygon arrays retain actual getter errors', {e['getter'] for e in original['getter_errors']} == {'quadNodeIndices', 'polygonNodeIndices', 'nodeCountPerPolygon'})
        check(relative+' completed BaseFeature healthy and compute succeeded', sample['after_edit']['base']['healthState'] == 0 and sample['compute_all_returned'] is True)
        check(relative+' source native bytes unchanged', hashlib.sha256(data).hexdigest() == before)
        if filename == FILES[0]:
            guard_context = (data, records, member, members, row)
        samples.append({'archive': relative, 'api_name': api['name'], 'expected_decoded': summary,
                        'api_crosschecks': {'coordinate_array_exact': True, 'triangle_index_array_exact': True,
                            'display_oriented_triangle_set_exact': True, 'volume_exact': True,
                            'measured_area_absolute_deviation_cm2': area_deviation,
                            'measured_bounds_max_deviation_cm': bounds_deviation,
                            'baseOrFormFeature': None, 'created_mesh_owner_is_base': False,
                            'missing_base_mesh_and_brep_source_lists': 'Capture serializer error for iterable SWIG vectors; no counts/identity inferred'},
                        'export_sha256': sample['export']['sha256']})
    data, records, member, members, row = guard_context
    guards = []
    def native_guard(name, mutate):
        altered = bytearray(data); mutate(altered)
        result = decode_mesh_contents(bytes(altered), records, member, members)
        check(name, not result['decoded'] and bool(result['unresolved']))
        guards.append({'guard': name, 'reason': result['unresolved'][0]['reason']})
    mesh = next(r for r in records if r.object_id == row['mesh_object_id'] and r.is_primary)
    native_guard('Reject unequal native mesh matrix copies', lambda b: struct.pack_into('<d', b, mesh.body+152, 2.0))
    asset_record = next(r for r in records if r.object_id == row['asset_object_id'] and r.is_primary)
    native_guard('Reject UUID correspondence mismatch despite valid filename', lambda b: b.__setitem__(asset_record.body+17, ord('a') if b[asset_record.body+17] != ord('a') else ord('b')))
    collection = next(r for r in records if r.object_id == row['mesh_collection_object_id'] and not r.is_primary)
    native_guard('Reject collection member wrong native type', lambda b: struct.pack_into('<Q', b, collection.body+6, 202))
    file_record = next(r for r in records if r.object_id == row['asset_filename_object_id'] and r.is_primary)
    native_guard('Reject filename/asset backlink mismatch', lambda b: struct.pack_into('<Q', b, file_record.body+3, 202))
    blob = members[row['asset_member']]
    for name, altered in (
        ('Reject unobserved buffer descriptor', blob[:row['geometry']['buffers'][0]['asset_offset']+14]+b'\x83'+blob[row['geometry']['buffers'][0]['asset_offset']+15:]),
        ('Reject trailing unframed mesh bytes', blob+b'\0'),
    ):
        try:
            decode_paramesh_geometry(altered)
        except (ValueError, struct.error) as error:
            guards.append({'guard': name, 'reason': str(error)}); check(name, True)
        else:
            raise AssertionError(name)
    return {'scope': 'Three actual saved owned tetra mesh captures; no main corpus run or live Fusion calls',
            'sample_count': len(samples), 'decoded_mesh_count': 3, 'typed_mesh_feature_count': 2,
            'stored_node_count': 12, 'decoded_triangle_count': 12, 'lzma_buffer_count': 18,
            'check_count': len(checks), 'malformed_guard_count': len(guards),
            'capture': CAPTURE, 'capture_generator_sha256': truth['executed_generator_sha256'],
            'current_generator_sha256': hashlib.sha256((root/'GenerateMeshContrasts.py').read_bytes()).hexdigest(),
            'generator_followup': 'Future iterable SWIG vector serialization and stale SDK/runtime PlaneCut status wording corrected; original capture snapshot/hash/truth remain unchanged and missing lists stay missing.',
            'plane_cut_capability_correction': 'Initially inspected API/Python/defs/adsk/fusion.py lacks MeshPlaneCut declarations, but actual running executable package exposes both MeshPlaneCutFeatures and Features.meshPlaneCutFeatures. Actual recorded booleans are true in all three captures; captured status prose is an incorrect inherited assumption. No PlaneCut call was made. Future work must inspect executable package docs.',
            'new_native_classes': {'mesh': 'EA90DA22-556C-4C61-89BB-20C2681B7A9D',
                'mesh_asset': 'A8338A26-5436-433C-8BAC-C3CF024AD595',
                'mesh_asset_filename': 'A1BAA3F6-4B67-4A0D-BACC-75F38A2230F3',
                'mesh_collection': '443807AD-8025-41A3-8A50-5157579C3D78',
                'base_mesh_feature': '99F6967E-ED35-4222-B906-5CCF0AC70B53'},
            'limitations': ['Only observed six-buffer v2 four-node/four-triangle closed oriented assets accepted',
                'Normals and four auxiliary buffers retained without semantic interpretation',
                'API BaseFeature association null; original BaseFeature202 not classified as mesh owner',
                'PlaneCut runtime capability is present despite stale inspected SDK defs; no PlaneCut feature generated or decoded',
                'BRep conversion, general mesh regeneration, arbitrary transforms and lifecycle unresolved'],
            'samples': samples, 'checks': checks, 'malformed_guards': guards}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--zstd-library')
    parser.add_argument('--output', default='mesh-decoding.json')
    args = parser.parse_args()
    result = validate(args.zstd_library)
    Path(args.output).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: result[key] for key in ('sample_count', 'decoded_mesh_count', 'typed_mesh_feature_count', 'check_count', 'malformed_guard_count')}))


if __name__ == '__main__':
    main()
