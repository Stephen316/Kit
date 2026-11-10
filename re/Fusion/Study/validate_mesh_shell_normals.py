"""Typed dense Shell normal pools: octahedral numerical sets, no ordered association."""
import argparse
from collections import defaultdict
import copy
import hashlib
import itertools
import json
import math
from pathlib import Path
import struct

from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_mesh_normals import decode_mesh_normal_pools, unfold_octahedral
from validate_mesh_remesh import load

ROOT = Path(__file__).resolve().parent
CAPTURE = 'meshshells-f5a2d6730f62'
CELL = 1e-6
NEIGHBORS = tuple(itertools.product((-1,0,1),repeat=3))
OBSERVED = {(2745,5481,2757),(1556,3103,1567),(2745,5482,2760)}


def vectors(flat):
    assert len(flat)%3 == 0
    return [flat[i:i+3] for i in range(0,len(flat),3)]


def unique_vectors(values,normalize=False):
    result = set()
    for value in values:
        assert len(value) == 3 and all(math.isfinite(x) for x in value)
        length = math.hypot(*value)
        assert length > 0
        result.add(tuple(x/length for x in value) if normalize else tuple(value))
    return sorted(result)


def directed_grid_distance(source,target):
    """Global nearest L-infinity distance is exact when accepted (<CELL).

    A target outside the27neighbor cells has coordinate distance>=CELL in at
    least one dimension. Thus a local nearest distance<CELL excludes any
    closer omitted target. No all-pairs fallback or index association exists.
    """
    buckets = defaultdict(list)
    for value in target:
        buckets[tuple(math.floor(x/CELL) for x in value)].append(value)
    worst = 0;comparisons = 0
    for value in source:
        cell = tuple(math.floor(x/CELL) for x in value)
        best = math.inf
        for delta in NEIGHBORS:
            for candidate in buckets.get(tuple(cell[i]+delta[i] for i in range(3)),()):
                comparisons += 1
                best = min(best,max(abs(value[i]-candidate[i]) for i in range(3)))
        if best >= CELL:
            raise ValueError('No qualifying normal-set neighbor inside spatial-grid bound')
        worst = max(worst,best)
    return dict(max_nearest_Linf=worst,source_unique_count=len(source),target_unique_count=len(target),
                local_candidate_comparisons=comparisons)


def grid_comparison(a,b,normalize=False):
    a,b = unique_vectors(a,normalize),unique_vectors(b,normalize)
    return dict(forward=directed_grid_distance(a,b),reverse=directed_grid_distance(b,a),cell_size=CELL)


def prove_dense_source(mesh,actual):
    """Independent source-byte formula + actual API set check, before runtime admission."""
    geometry = mesh['geometry'];block = geometry['buffers'][2]
    assert block['descriptor_hex'] == '83a14403a15403a155c3' and 'decompression_scope' not in block
    assert mesh['asset_fusion_uuid'] == geometry['fusion_uuid']
    raw = bytes.fromhex(block['uncompressed_payload_hex'])
    assert len(raw) == block['uncompressed_size'] and len(raw)%8 == 0
    pairs = list(struct.iter_unpack('<2f',raw))
    layout = (geometry['node_count'],geometry['triangle_count'],len(pairs))
    assert layout in OBSERVED
    assert b''.join(struct.pack('<2f',*pair) for pair in pairs) == raw
    decoded = [unfold_octahedral(*pair) for pair in pairs]
    api = vectors(actual['display_triangle_mesh']['normalVectorsAsDouble'])
    directions = grid_comparison(decoded,api,normalize=True)
    assert max(directions[side]['max_nearest_Linf'] for side in ('forward','reverse')) < 1.2e-7
    scale = mesh['asset_coordinates_to_component_matrix'][0]
    assert scale > 0 and mesh['stored_matrix_copies'] == [mesh['asset_coordinates_to_component_matrix']]*2
    covectors = [[v/scale for v in vector] for vector in decoded]
    covector_comparison = grid_comparison(covectors,api)
    assert max(covector_comparison[side]['max_nearest_Linf'] for side in ('forward','reverse')) < 2e-7
    magnitude_error = max(abs(math.hypot(*vector)*scale-1) for vector in api)
    assert magnitude_error < 1e-7
    return dict(layout=list(layout),actual_API_display_vector_count=len(api),
        directions=directions,covectors=covector_comparison,inverse_scale_magnitude_max_error=magnitude_error,
        stored_unit_vector_max_length_error=max(abs(math.hypot(*vector)-1) for vector in decoded),
        stored_packed_pair_exact_replay=True,
        numerical_scope='Bidirectional nearest direction/covector sets only; native typed mesh/asset route selected before numerical comparison. Counts/order do not bind nodes/corners or unused entries.')


def old_goldens(root):
    result = {}
    for report,key in (('mesh-normal-decoding.json','expected_decoded'),
                       ('mesh-normal-variant-decoding.json','expected_decoded'),
                       ('mesh-smooth-decoding.json','expected_normal_pools'),
                       ('mesh-reverse-normal-decoding.json','expected_normal_pools')):
        for row in json.loads((root/report).read_text())['samples']:
            if row['archive'] in result:assert result[row['archive']] == row[key]
            result[row['archive']] = row[key]
    cut = json.loads((root/'mesh-reverse-normal-decoding.json').read_text())['cut_normal_holdout']
    result[cut['archive']] = cut['expected_normal_pools']
    return result


def validate(root,zstd):
    truth = json.loads((root/CAPTURE/'ground_truth.json').read_text())
    report = dict(scope='Three existing typed dense Shell current assets; spatial-grid numerical normal-set/covector corroboration only, no identity/order inference',
        samples=[],old_full_dictionary_controls=[],guards=[],source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in (
            'decode_mesh_normals.py','decode_mesh_geometry_variants.py','decode_mesh_contents.py','validate_mesh_shell_normals.py','validate_mesh_remesh.py')})
    guard_mesh = None
    for sample in truth['samples']:
        archive = CAPTURE+'/'+sample['file']
        assert hashlib.sha256((root/archive).read_bytes()).hexdigest() == sample['export']['sha256']
        data,records,features,member,members = load(root,archive,zstd)
        meshes = decode_mesh_contents_variants(data,records,member,members)
        assert len(meshes['decoded']) == 1 and not meshes['unresolved']
        before = copy.deepcopy(meshes);mesh = meshes['decoded'][0]
        actual = sample['component_meshes_after_shell']['meshes'][0]
        assert mesh['name'] == actual['name'] and mesh['component_object_id'] == 3
        proof = prove_dense_source(mesh,actual)
        decoded = decode_mesh_normal_pools(meshes)
        assert len(decoded['decoded']) == 1 and not decoded['unresolved'],decoded
        pool = decoded['decoded'][0]
        assert pool['mesh_object_id'] == mesh['mesh_object_id'] and pool['asset_object_id'] == mesh['asset_object_id']
        assert pool['asset_member'] == mesh['asset_member'] and pool['asset_fusion_uuid'] == mesh['asset_fusion_uuid']
        assert pool['stored_unit_vector_count'] == proof['layout'][2]
        assert 'unresolved' in pool['association_status'] and meshes == before
        report['samples'].append(dict(archive=archive,export_sha256=sample['export']['sha256'],expected_decoded=decoded,proof=proof))
        if guard_mesh is None:guard_mesh = mesh
    for archive,expected in old_goldens(root).items():
        data,records,features,member,members = load(root,archive,zstd)
        meshes = decode_mesh_contents_variants(data,records,member,members)
        decoded = decode_mesh_normal_pools(meshes)
        assert decoded == expected,(archive,'Old full normal dictionary changed')
        report['old_full_dictionary_controls'].append(dict(archive=archive,decoded_pool_count=len(expected['decoded']),full_normal_dictionary_exact=True))
    def guard(label,alter):
        mesh = copy.deepcopy(guard_mesh);alter(mesh)
        decoded = decode_mesh_normal_pools(dict(decoded=[mesh]))
        assert not decoded['decoded'] and len(decoded['unresolved']) == 1
        report['guards'].append(dict(check=label,passed=True,reason=decoded['unresolved'][0]['reason']))
    def extra_pair(mesh):
        block = mesh['geometry']['buffers'][2]
        block['uncompressed_payload_hex'] += struct.pack('<2f',0.,0.).hex()
        block['uncompressed_size'] += 8
    guard('No unobserved dense pool count admitted',extra_pair)
    guard('Typed source UUID must agree',lambda mesh:mesh.__setitem__('asset_fusion_uuid','wrong-uuid'))
    guard('Descriptor must remain typed pair layout',lambda mesh:mesh['geometry']['buffers'][2].__setitem__('descriptor_hex','82a14403a15403'))
    guard('No auxiliary continuation in normal pool',lambda mesh:mesh['geometry']['buffers'][2].__setitem__('decompression_scope','opaque-prefix'))
    try:grid_comparison([[0.,1.,0.]],[[1.,0.,0.]],normalize=True)
    except ValueError as error:report['guards'].append(dict(check='Spatial grid rejects distant unmatched direction',passed=True,reason=str(error)))
    else:raise AssertionError('Grid must not claim unmatched direction agreement')
    report['counts'] = dict(actual_Shell_normal_pools=3,
        actual_stored_vectors=sum(s['proof']['layout'][2] for s in report['samples']),
        actual_API_display_vectors=sum(s['proof']['actual_API_display_vector_count'] for s in report['samples']),
        old_archive_controls=len(report['old_full_dictionary_controls']),
        old_pool_dictionaries_preserved=sum(s['decoded_pool_count'] for s in report['old_full_dictionary_controls']),
        guards=len(report['guards']),all_pairs_fallbacks=0,full_main_runs=0,live_API_calls=0)
    report['limits'] = [
        'Exactly three new node/triangle/pool-count tuples admitted; normal outputs for all old saved layouts remain dictionary-exact.',
        'Dense Float32 octahedral direction errors reach approximately1.04e-7; these holdouts use explicit1.2e-7 component tolerance. No prior tolerance or output was changed.',
        'Count differences2757vs2754,1567vs1565,2760vs2757 do not identify unused entries or per-node/corner ordering. Native IDs and asset routes are established independently.',
        'API display directions/covector magnitudes are numerical corroboration only; original PolygonMesh normal reconstruction and procedural normals remain unsupported.']
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--zstd-library',required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'mesh-shell-normal-decoding.json')
    args=parser.parse_args();report=validate(ROOT,args.zstd_library)
    args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['counts']))
