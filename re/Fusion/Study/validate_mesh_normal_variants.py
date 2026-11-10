"""Five actual Remesh/Combine normal pools and exact eleven old dictionaries."""
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
from validate_mesh_normals import _direction_error


def validate(zstd):
    root = Path(__file__).resolve().parent
    reports = [json.loads((root/name).read_text()) for name in ('mesh-remesh-decoding.json', 'mesh-combine-decoding.json')]
    plan = [sample for report in reports for sample in report['samples'] if not sample['archive'].endswith('/cut.f3d')]
    checks, samples, controls, guards = [], [], [], []
    normal_count = api_count = lower_count = 0
    def check(label, condition, **evidence):
        if not condition:
            raise AssertionError(label)
        checks.append({'check': label, **evidence})
    def load(archive):
        members = read_members(root/archive, zstd)
        member = next(k for k in members if k.endswith('/FusionDesignSegmentType1/BulkStream.dat'))
        records, _ = design_records(members[member], members[member.replace('BulkStream.dat', 'MetaStream.dat')])
        return decode_mesh_contents_variants(members[member], records, member, members)
    truths = {}
    for item in plan:
        archive = item['archive']; folder = Path(archive).parent
        if str(folder) not in truths:
            truths[str(folder)] = json.loads((root/folder/'ground_truth.json').read_text())
        truth = truths[str(folder)]
        actual = next(s for s in truth['samples'] if s['file'] == Path(archive).name)
        current = actual['component_meshes_after_remesh' if str(folder).startswith('meshremeshes-') else 'component_meshes_after_combine']
        check(archive+' terminal saved capture', (root/folder/'complete.txt').is_file())
        check(archive+' exact exported archive hash', hashlib.sha256((root/archive).read_bytes()).hexdigest() == actual['export']['sha256'])
        mesh_summary = load(archive)
        check(archive+' full upstream mesh identity/assets/diagnostics equal prior focused golden', mesh_summary == item['expected_mesh_contents'])
        before = copy.deepcopy(mesh_summary)
        result = decode_mesh_normal_pools(mesh_summary)
        check(archive+' one newly qualified normalpool, no unresolved normalbranch', len(result['decoded']) == len(mesh_summary['decoded']) == 1 and not result['unresolved'])
        native = mesh_summary['decoded'][0]; pool = result['decoded'][0]
        check(archive+' exact native mesh ID213 selected before numerical comparison', native['mesh_object_id'] == pool['mesh_object_id'] == 213 and native['collection_mesh_object_ids'] == [213])
        check(archive+' actual ordered currentmesh has independently matching customname', current['count'] == 1 and current['meshes'][0]['name'] == native['name'])
        check(archive+' asset ID/UUID/member qualified upstream unchanged', pool['asset_object_id'] == native['asset_object_id'] and pool['asset_fusion_uuid'] == native['asset_fusion_uuid'] and pool['asset_member'] == native['asset_member'])
        geometry = native['geometry']; block = geometry['buffers'][2]
        shape = [len(geometry['stored_node_coordinates_float32']), len(geometry['triangle_node_indices'])//3, pool['stored_unit_vector_count']]
        check(archive+' only four specifically captured newlayouttuples', tuple(shape) in ((9, 14, 31), (16, 28, 54), (66, 128, 180), (41, 78, 124)))
        check(archive+' unitvector descriptor and complete normal-buffer extent remain strict', block['descriptor_hex'] == '83a14403a15403a155c3' and 'decompression_scope' not in block and len(bytes.fromhex(block['uncompressed_payload_hex'])) == block['uncompressed_size'])
        api_mesh = current['meshes'][0]
        flat = api_mesh['display_triangle_mesh']['normalVectorsAsDouble']
        api_vectors = [flat[i:i+3] for i in range(0, len(flat), 3)]
        direction_error = _direction_error(pool['derived_asset_unit_vectors'], api_vectors)
        check(archive+' octahedral directionset corroborates actual saved displaynormalset', direction_error < 1e-7, max_symmetric_component_discrepancy=direction_error)
        check(archive+' unfolded pool vector unitlengths', all(abs(math.hypot(*v)-1) < 1e-14 for v in pool['derived_asset_unit_vectors']))
        raw = b''.join(struct.pack('<2f', *p) for p in pool['stored_packed_pairs_float32'])
        check(archive+' exact stored pair byte/order replay', raw.hex() == block['uncompressed_payload_hex'] == pool['stored_payload_hex'])
        scale_error = max(abs(math.hypot(*v)*pool['native_uniform_scale']-1) for v in api_vectors)
        check(archive+' API vector magnitudes corroborate inverse native uniformscale', scale_error < 1e-7, max_length_times_scale_deviation=scale_error)
        covector_error = max(min(max(abs(x-y) for x, y in zip(a, b)) for b in api_vectors) for a in pool['derived_component_covectors'])
        check(archive+' derived component covectors numerically corroborated', covector_error < 1e-7, max_component_discrepancy=covector_error)
        check(archive+' distinct pool/display counts explicitly prevent ordered-node assignment', pool['stored_unit_vector_count'] != len(api_vectors) and 'unresolved' in pool['association_status'])
        check(archive+' input geometry and existing diagnostics not mutated', before == mesh_summary)
        normal_count += pool['stored_unit_vector_count']; api_count += len(api_vectors); lower_count += pool['lower_hemisphere_pair_count']
        samples.append({'archive': archive, 'expected_decoded': result,
            'actual_layout': shape, 'actual_API_display_normal_count': len(api_vectors),
            'direction_set_max_component_discrepancy': direction_error,
            'covector_set_max_component_discrepancy': covector_error,
            'API_comparison_scope': 'Native mesh/asset identities and ordered singleton collection proven before direction-set comparison; no normal-coordinate entity selection or per-corner correspondence',
            'prior_mesh_diagnostics': copy.deepcopy(mesh_summary['unresolved'])})
        if shape == [9, 14, 31]:
            guard_source = copy.deepcopy(native)
    old = json.loads((root/'mesh-normal-decoding.json').read_text())
    for item in old['samples']:
        current = decode_mesh_normal_pools(load(item['archive']))
        # Byte-for-byte canonical serialization proves every dictionary/string/
        # ordered list/value matches, not just counts or normal directions.
        encoded = json.dumps(current, sort_keys=True, separators=(',', ':')).encode()
        expected = json.dumps(item['expected_decoded'], sort_keys=True, separators=(',', ':')).encode()
        check(item['archive']+' full old normal dictionary canonical bytes unchanged', encoded == expected)
        controls.append({'archive': item['archive'], 'complete_summary_sha256': hashlib.sha256(encoded).hexdigest(), 'pool_count': len(current['decoded'])})
    def guard(label, mutate):
        bad = copy.deepcopy(guard_source); mutate(bad)
        result = decode_mesh_normal_pools({'decoded': [bad]})
        check(label, not result['decoded'] and bool(result['unresolved']))
        guards.append({'guard': label, 'reason': result['unresolved'][0]['reason']})
    def extra_pair(mesh):
        block = mesh['geometry']['buffers'][2]
        block['uncompressed_payload_hex'] += struct.pack('<2f', 0., 0.).hex()
        block['uncompressed_size'] += 8
    guard('Reject unobserved9/14/32pool despite valid extra Float32pair', extra_pair)
    guard('Reject unobserved10/14/31source tuple', lambda m: m['geometry']['stored_node_coordinates_float32'].append([0., 0., 0.]))
    guard('Reject missing unitvector flag in descriptor', lambda m: m['geometry']['buffers'][2].__setitem__('descriptor_hex', '82a14403a15403'))
    guard('Reject normal-buffer prefix-only auxiliary decode', lambda m: m['geometry']['buffers'][2].__setitem__('decompression_scope', 'Declared-size prefix only'))
    guard('Reject nonfinite packedpair in newlayout', lambda m: m['geometry']['buffers'][2].__setitem__('uncompressed_payload_hex', struct.pack('<f', float('nan')).hex()+m['geometry']['buffers'][2]['uncompressed_payload_hex'][8:]))
    guard('Reject assetUUID mismatch in newlayout', lambda m: m.__setitem__('asset_fusion_uuid', 'not-the-native-asset-uuid'))
    return {'scope': 'Five real Remesh/Join/Intersect current mesh normalpools; numerical direction checks only after explicit typed identities. No main, geometry reader or source-association changes.',
        'sample_count': len(samples), 'new_mesh_pool_count': len(samples), 'new_stored_vector_count': normal_count,
        'actual_API_display_vector_count': api_count, 'lower_hemisphere_pair_count': lower_count,
        'old_archive_control_count': len(controls), 'old_pool_dictionary_count': sum(c['pool_count'] for c in controls),
        'check_count': len(checks), 'malformed_guard_count': len(guards), 'samples': samples,
        'old_full_dictionary_controls': controls, 'checks': checks, 'malformed_guards': guards,
        'limitations': ['Only four newly observed(node,triangle,pool)tuples admitted',
            'Literal pool order retained; no node/corner/API-index association',
            'Pool and API display counts differ in every newcase', 'Original PolygonMesh normal arrays unreconstructed',
            'Join/Intersect retained-tool diagnostics and all upstream geometry remain unchanged'],
        'historical_report_scope': 'mesh-normal-decoding.json and its historical helper hash remain unchanged; complete old expected dictionaries are equality controls, not relabelled current-source provenance',
        'historical_report_sha256': hashlib.sha256((root/'mesh-normal-decoding.json').read_bytes()).hexdigest(),
        'current_helper_sha256': hashlib.sha256((root/'decode_mesh_normals.py').read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--zstd-library'); parser.add_argument('--output', default='mesh-normal-variant-decoding.json')
    args = parser.parse_args(); result = validate(args.zstd_library)
    Path(args.output).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: result[key] for key in ('sample_count', 'new_stored_vector_count', 'old_pool_dictionary_count', 'check_count', 'malformed_guard_count')}))


if __name__ == '__main__':
    main()
