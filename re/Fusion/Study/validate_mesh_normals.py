"""Saved-API octahedral normal-direction evidence; no correspondence inference."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from fusion_archive import read_members
from fusion_metadata import design_records
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_mesh_normals import decode_mesh_normal_pools

FOLDERS = ('meshcontrasts-10c2557c91a3', 'meshplanecuts-18f2683c83f5',
           'meshreduces-780954a23308', 'meshreduces-8f01528f7f21')


def _normalize(vector):
    length = math.hypot(*vector)
    return [x/length for x in vector] if length else list(vector)


def _direction_error(a, b):
    """Symmetric nearest-direction discrepancy, never an entity association."""
    a, b = [_normalize(v) for v in a], [_normalize(v) for v in b]
    forward = max(min(max(abs(x-y) for x, y in zip(p, q)) for q in b) for p in a)
    reverse = max(min(max(abs(x-y) for x, y in zip(p, q)) for q in a) for p in b)
    return max(forward, reverse)


def validate(zstd):
    root = Path(__file__).resolve().parent
    checks, samples, guards, exclusions = [], [], [], []
    vector_count = api_vector_count = lower_count = 0
    def check(label, condition, **evidence):
        if not condition:
            raise AssertionError(label)
        checks.append({'check': label, **evidence})
    old_reports = [json.loads((root/name).read_text()) for name in ('mesh-decoding.json', 'mesh-plane-cut-decoding.json', 'mesh-reduce-decoding.json')]
    goldens = {}
    for report in old_reports:
        for sample in report['samples']:
            goldens[sample['archive']] = sample.get('expected_mesh_contents', sample.get('expected_decoded'))
    for folder_name in FOLDERS:
        folder = root/folder_name
        truth = json.loads((folder/'ground_truth.json').read_text())
        check(folder_name+' actual terminal capture', (folder/'complete.txt').is_file())
        for sample in truth['samples']:
            archive = folder_name+'/'+sample['file']
            path = root/archive
            check(archive+' original export hash unchanged', hashlib.sha256(path.read_bytes()).hexdigest() == sample['export']['sha256'])
            members = read_members(path, zstd)
            member = next(k for k in members if k.endswith('/FusionDesignSegmentType1/BulkStream.dat'))
            data = members[member]
            records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
            mesh_summary = decode_mesh_contents_variants(data, records, member, members)
            check(archive+' upstream complete ownership/asset summary exact old focused golden', mesh_summary == goldens[archive])
            before = copy.deepcopy(mesh_summary)
            decoded = decode_mesh_normal_pools(mesh_summary)
            check(archive+' qualified normal pools without unresolved branches', len(decoded['decoded']) == len(mesh_summary['decoded']) and decoded['unresolved'] == [])
            if folder_name.startswith('meshcontrasts-'):
                actual_meshes = sample['after_edit']['component_mesh_bodies']
            elif folder_name.startswith('meshplanecuts-'):
                actual_meshes = sample['component_meshes_after_cut']['meshes']
            else:
                actual_meshes = sample['component_meshes_after_reduce']['meshes']
            check(archive+' API and explicit native ordered mesh collection lengths', len(actual_meshes) == len(mesh_summary['decoded']))
            evidence_rows = []
            for native, pool, actual in zip(mesh_summary['decoded'], decoded['decoded'], actual_meshes):
                label = archive+' mesh'+str(native['mesh_object_id'])
                check(label+' mesh asset/UUID reference provenance retained', pool['asset_object_id'] == native['asset_object_id'] and pool['asset_member'] == native['asset_member'] and pool['asset_fusion_uuid'] == native['asset_fusion_uuid'])
                check(label+' native ordered identity route retained independent of normals', pool['mesh_object_id'] == native['mesh_object_id'] and (not native['name'] or native['name'] == actual['name']))
                display = actual['display_triangle_mesh']
                flat = display['normalVectorsAsDouble']
                api = [flat[i:i+3] for i in range(0, len(flat), 3)]
                error = _direction_error(pool['derived_asset_unit_vectors'], api)
                check(label+' octahedral direction set matches independently saved display-normal direction set', error < 1e-7, max_symmetric_component_discrepancy=error)
                check(label+' decoded vectors are unit length', all(abs(math.hypot(*v)-1) < 1e-14 for v in pool['derived_asset_unit_vectors']))
                check(label+' packed Float32 pair exact replay', b''.join(struct.pack('<2f', *pair) for pair in pool['stored_packed_pairs_float32']).hex() == pool['stored_payload_hex'])
                api_lengths = [math.hypot(*v) for v in api]
                scale_error = max(abs(length*pool['native_uniform_scale']-1) for length in api_lengths)
                check(label+' actual display normal magnitude follows inverse native uniform scale', scale_error < 1e-7, max_length_times_scale_deviation=scale_error)
                covector_error = max(min(max(abs(x-y) for x, y in zip(p, q)) for q in api) for p in pool['derived_component_covectors'])
                check(label+' derived inverse-scale covector set corroborates actual API values within Float32 precision', covector_error < 1e-6, max_component_discrepancy=covector_error)
                check(label+' association remains explicitly unresolved', 'association' in pool['association_status'].lower() and 'unresolved' in pool['association_status'].lower())
                raw = bytes.fromhex(pool['stored_payload_hex'])
                values = list(struct.unpack('<'+'f'*(len(raw)//4), raw))
                triples = [values[i:i+3] for i in range(0, len(values)-2, 3)]
                direct_error = _direction_error(triples, api)
                exclusions.append({'archive': archive, 'mesh_object_id': native['mesh_object_id'],
                    'candidate': 'Direct Float32 XYZ triples', 'symmetric_direction_discrepancy': direct_error,
                    'candidate_vector_count': len(triples), 'octahedral_pair_vector_count': pool['stored_unit_vector_count'],
                    'status': 'Excluded by actual API directions' if direct_error >= 1e-7 else 'Not excluded by this control alone'})
                check(label+' direct XYZ triples contradicted by actual API normal directions', direct_error > 1e-3)
                if pool['lower_hemisphere_pair_count']:
                    nofold = [[x, y, 1-abs(x)-abs(y)] for x, y in pool['stored_packed_pairs_float32']]
                    nofold_error = _direction_error(nofold, api)
                    check(label+' lower-hemisphere unfolding is independently required', nofold_error > 1e-3)
                    exclusions.append({'archive': archive, 'mesh_object_id': native['mesh_object_id'], 'candidate': 'Octahedral upper-hemisphere formula without lower fold', 'symmetric_direction_discrepancy': nofold_error, 'status': 'Excluded'})
                original_flat = actual['original_polygon_mesh']['normalVectorsAsDouble']
                original = [original_flat[i:i+3] for i in range(0, len(original_flat), 3)]
                original_error = _direction_error(pool['derived_asset_unit_vectors'], original)
                vector_count += pool['stored_unit_vector_count']; api_vector_count += len(api); lower_count += pool['lower_hemisphere_pair_count']
                evidence_rows.append({'mesh_object_id': native['mesh_object_id'], 'asset_object_id': native['asset_object_id'],
                    'stored_vector_count': pool['stored_unit_vector_count'], 'actual_display_normal_count': len(api),
                    'actual_original_polygon_normal_count': len(original), 'direction_set_max_component_discrepancy': error,
                    'covector_set_max_component_discrepancy': covector_error,
                    'original_polygon_direction_discrepancy': original_error,
                    'api_display_magnitude_range': [min(api_lengths), max(api_lengths)],
                    'stored_order_is_API_order': 'Unproved; no reordering or corner/node association published',
                    'count_mismatch_scope': 'Counts differ; excludes direct one-pool-entry-per-display-node indexing' if len(api) != pool['stored_unit_vector_count'] else 'Equal counts alone do not establish ordered indexing'})
                if archive.endswith('stl_centimeter.f3d'):
                    guard_mesh = copy.deepcopy(native)
            check(archive+' upstream geometry/asset output not mutated', mesh_summary == before)
            samples.append({'archive': archive, 'expected_decoded': decoded, 'api_evidence': evidence_rows})
    def guard(label, alter):
        bad = copy.deepcopy(guard_mesh); alter(bad)
        result = decode_mesh_normal_pools({'decoded': [bad]})
        check(label, not result['decoded'] and bool(result['unresolved']))
        guards.append({'guard': label, 'reason': result['unresolved'][0]['reason']})
    guard('Reject non-unit-vector descriptor', lambda m: m['geometry']['buffers'][2].__setitem__('descriptor_hex', '82a14403a15403'))
    guard('Reject normal source UUID mismatch', lambda m: m.__setitem__('asset_fusion_uuid', 'not-the-asset-uuid'))
    guard('Reject nonfinite packed normal', lambda m: m['geometry']['buffers'][2].__setitem__('uncompressed_payload_hex', struct.pack('<f', float('nan')).hex()+m['geometry']['buffers'][2]['uncompressed_payload_hex'][8:]))
    guard('Reject packed pair outside observed square', lambda m: m['geometry']['buffers'][2].__setitem__('uncompressed_payload_hex', struct.pack('<f', 2.).hex()+m['geometry']['buffers'][2]['uncompressed_payload_hex'][8:]))
    guard('Reject auxiliary continuation for a normal pool', lambda m: m['geometry']['buffers'][2].__setitem__('decompression_scope', 'opaque prefix'))
    guard('Reject unequal native normal matrix copies', lambda m: m['stored_matrix_copies'][1].__setitem__(0, 2.))
    return {'scope': 'Offline actual API direction/covector comparisons across10savedarchives/11qualified current native meshes; vector matching is a numerical check only and never selects native entities/assets',
        'sample_count': len(samples), 'mesh_pool_count': sum(len(s['expected_decoded']['decoded']) for s in samples),
        'decoded_stored_unit_vector_count': vector_count, 'saved_API_display_normal_count': api_vector_count,
        'lower_hemisphere_pair_count': lower_count, 'check_count': len(checks), 'malformed_guard_count': len(guards),
        'samples': samples, 'checks': checks, 'malformed_guards': guards, 'excluded_candidates': exclusions,
        'limitations': ['Only observed descriptor/count layouts accepted', 'Serialized pool order retained; API array order/vertex/corner binding unproved',
            'Split-result22pool entries versus18display normals excludes direct ordered indexing',
            'Original PolygonMesh normals remain unreconstructed; display direction set evidence is separately scoped',
            'No temporal/source asset role assigned, no topology change or regeneration claim',
            'No shared reader changes; existing geometry/mesh dictionaries remain exact'],
        'helper_sha256': hashlib.sha256((root/'decode_mesh_normals.py').read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--zstd-library'); parser.add_argument('--output', default='mesh-normal-decoding.json')
    args = parser.parse_args(); result = validate(args.zstd_library)
    Path(args.output).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: result[key] for key in ('sample_count', 'mesh_pool_count', 'decoded_stored_unit_vector_count', 'check_count', 'malformed_guard_count')}))


if __name__ == '__main__':
    main()
