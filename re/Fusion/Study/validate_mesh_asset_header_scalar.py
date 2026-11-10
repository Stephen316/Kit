"""Bounded saved-file evidence for the native mesh asset header scalar; no runtime semantics change."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import struct

from decode_mesh_contents import ASSET, replay_paramesh_geometry
from decode_mesh_geometry_variants import decode_mesh_asset, decode_mesh_contents_variants
from fusion_archive import read_members
from fusion_metadata import design_records

ROOT = Path(__file__).resolve().parent
CAPTURES = ('meshcontrasts-10c2557c91a3', 'meshplanecuts-18f2683c83f5',
            'meshreduces-780954a23308', 'meshreduces-8f01528f7f21')
SDK = Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production/c139e2731e42a0340acc3d34de2cbdb01237a27c/Autodesk Fusion.app/Contents/Api/Python/packages/adsk/fusion.py')


def exact_mesh_metrics(points, indices):
    """Exact rational determinant sum of stored Float32 vertices, independent of runtime mesh metric helper."""
    p = [list(map(Fraction, point)) for point in points]
    volume = Fraction(0)
    directed = Counter()
    for start in range(0, len(indices), 3):
        ids = indices[start:start+3]
        a, b, c = [p[i] for i in ids]
        volume += sum(a[k] * (b[(k+1)%3]*c[(k+2)%3]-b[(k+2)%3]*c[(k+1)%3]) for k in range(3))/6
        directed.update((ids[i], ids[(i+1)%3]) for i in range(3))
    closed = bool(directed) and all(n == 1 and directed[(b,a)] == 1 for (a,b),n in directed.items())
    low = [min(v[i] for v in p) for i in range(3)]
    high = [max(v[i] for v in p) for i in range(3)]
    return volume, closed, [[float(v) for v in low], [float(v) for v in high]]


def determinant3(matrix):
    a, b, c = [matrix[start:start+3] for start in (0, 4, 8)]
    return sum(a[k]*(b[(k+1)%3]*c[(k+2)%3]-b[(k+2)%3]*c[(k+1)%3]) for k in range(3))


def api_meshes(sample):
    if 'after_edit' in sample:
        return sample['after_edit']['component_mesh_bodies']
    if 'component_meshes_after_cut' in sample:
        return sample['component_meshes_after_cut']['meshes']
    return sample['component_meshes_after_reduce']['meshes']


def validate(root, zstd):
    report = dict(scope='17 typed assets in 10 actual saved mesh archives; header evidence only, no runtime semantic extension, full main run or live API call',
        samples=[], controls=[], source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in (
            'validate_mesh_asset_header_scalar.py', 'decode_mesh_geometry_variants.py', 'decode_mesh_contents.py',
            'fusion_archive.py', 'fusion_metadata.py')})
    sdk_text = SDK.read_text()
    mesh_body = sdk_text[sdk_text.index('class MeshBody(Base):'):]
    documented_volume = 'Returns the volume in cm ^ 3. Returns 0 in the case the mesh body is not closed.'
    assert documented_volume in mesh_body[:mesh_body.index('\nclass ')]
    report['active_sdk_volume_contract'] = dict(path=str(SDK), sha256=hashlib.sha256(SDK.read_bytes()).hexdigest(),
        class_name='MeshBody', getter='_get_volume', documentation=documented_volume,
        scope='Public API getter contract only; SDK does not identify the native asset byte field')
    totals = Counter()
    saved = {}
    for folder in CAPTURES:
        truth_path = root/folder/'ground_truth.json'
        truth = json.loads(truth_path.read_text())
        assert (root/folder/'complete.txt').is_file()
        for sample in truth['samples']:
            archive = folder+'/'+sample['file']
            assert hashlib.sha256((root/archive).read_bytes()).hexdigest() == sample['export']['sha256']
            members = read_members(root/archive, zstd)
            member = next(n for n in members if n.endswith('/FusionDesignSegmentType1/BulkStream.dat'))
            data = members[member]
            records, _ = design_records(data, members[member.replace('BulkStream.dat','MetaStream.dat')])
            current = decode_mesh_contents_variants(data, records, member, members)
            assert not current['unresolved']
            current_by_asset = {r['asset_object_id']:r for r in current['decoded']}
            assets = []
            for record in records:
                if not record.is_primary or record.class_guid != ASSET:
                    continue
                asset = decode_mesh_asset(data, records, record.object_id, member, members)
                geometry = asset['geometry']
                raw = data[record.body:record.end]
                assert raw[:2] == bytes(2) and len(raw) == 68 and raw[11:13] == b'\1\0'
                scalar = struct.unpack_from('<d', raw, 2)[0]
                assert struct.pack('<d', scalar) == raw[2:10] and scalar == asset['stored_asset_header_scalar']
                assert replay_paramesh_geometry(geometry) == members[asset['asset_member']]
                volume, closed, bounds = exact_mesh_metrics(geometry['stored_node_coordinates_float32'], geometry['triangle_node_indices'])
                assert volume > 0
                if closed:
                    assert scalar == float(volume) and raw[10] == 1
                else:
                    assert scalar == 0 and raw[10] == 0 and volume != 0
                extents = [bounds[1][i]-bounds[0][i] for i in range(3)]
                totals['assets'] += 1
                totals['closed_assets' if closed else 'open_assets'] += 1
                row = dict(asset_object_id=record.object_id, native_class_guid=record.class_guid,
                    asset_member=asset['asset_member'], asset_fusion_uuid=asset['asset_fusion_uuid'],
                    stored_asset_prefix_hex=raw[:13].hex(), stored_float64_bytes_hex=raw[2:10].hex(),
                    stored_asset_header_scalar=scalar, stored_flag_byte=raw[10],
                    exact_raw_triangle_determinant_sum_rational=str(volume),
                    raw_triangle_determinant_sum_rounded_float64=float(volume),
                    raw_closed_oriented_edge_incidence=closed,
                    raw_node_count=len(geometry['stored_node_coordinates_float32']), raw_triangle_count=len(geometry['triangle_node_indices'])//3,
                    raw_bounds=bounds, raw_extents=extents, raw_bound_product=math.prod(extents),
                    raw_coordinate_payload_sha256=hashlib.sha256(bytes.fromhex(geometry['buffers'][0]['uncompressed_payload_hex'])).hexdigest(),
                    raw_index_payload_sha256=hashlib.sha256(bytes.fromhex(geometry['buffers'][1]['uncompressed_payload_hex'])).hexdigest(),
                    exact_native_float64_replay=True, exact_paramesh_buffer_replay=True,
                    matching_current_native_mesh_object_id=None, asset_to_component_matrix=None,
                    component_volume_from_header_and_matrix=None,
                    association_scope='Typed asset UUID/filename/backlink and embedded fusion_uuid; current native mesh identity only when independently referenced')
                if record.object_id in current_by_asset:
                    mesh = current_by_asset[record.object_id]
                    matrix = mesh['asset_coordinates_to_component_matrix']
                    row.update(matching_current_native_mesh_object_id=mesh['mesh_object_id'],
                        current_mesh_native_feature_owner_object_id=mesh['feature_object_id'],
                        asset_to_component_matrix=matrix,
                        component_volume_from_header_and_matrix=scalar*abs(determinant3(matrix)))
                    totals['current_assets'] += 1
                assets.append(row)
            actual = api_meshes(sample)
            predicted = sorted(r['component_volume_from_header_and_matrix'] for r in assets if r['matching_current_native_mesh_object_id'] is not None)
            api_volumes = sorted(m['volume'] for m in actual)
            assert len(predicted) == len(actual)
            assert all(math.isclose(a,b,rel_tol=1e-14,abs_tol=1e-15) for a,b in zip(predicted,api_volumes))
            assert sorted(r['raw_closed_oriented_edge_incidence'] for r in assets if r['matching_current_native_mesh_object_id'] is not None) == sorted(m['isClosed'] for m in actual)
            evidence = dict(archive=archive, archive_sha256=sample['export']['sha256'],
                ground_truth_sha256=hashlib.sha256(truth_path.read_bytes()).hexdigest(), assets=assets,
                actual_current_API_meshes=[dict(name=m['name'],volume_cm3=m['volume'],area_cm2=m['area'],
                    isClosed=m['isClosed'],isOriented=m['isOriented'],bounds_cm=m['bounding_box_cm'],
                    polygon_mesh=m['original_polygon_mesh']) for m in actual],
                unordered_current_component_volume_multiset_matches_API=True,
                API_collection_comparison_scope='Unordered numerical corroboration only; collection order/coordinates do not select or establish persistent mesh identity')
            report['samples'].append(evidence)
            saved[archive] = evidence
            totals['archives'] += 1
    cm = saved[CAPTURES[0]+'/stl_centimeter.f3d']
    mm = saved[CAPTURES[0]+'/stl_millimeter.f3d']
    a,b = cm['assets'][0], mm['assets'][0]
    assert a['stored_asset_header_scalar'] == b['stored_asset_header_scalar'] == 4
    assert a['raw_bounds'] == b['raw_bounds']
    assert a['raw_coordinate_payload_sha256'] == b['raw_coordinate_payload_sha256']
    assert a['raw_index_payload_sha256'] == b['raw_index_payload_sha256']
    assert math.isclose(cm['actual_current_API_meshes'][0]['volume_cm3']/mm['actual_current_API_meshes'][0]['volume_cm3'],1000,rel_tol=1e-15)
    report['controls'].append(dict(contrast='Same raw tetra with centimeter vs millimeter import',
        archives=[cm['archive'],mm['archive']], stored_scalars=[4.0,4.0],
        actual_API_component_volumes_cm3=[cm['actual_current_API_meshes'][0]['volume_cm3'],mm['actual_current_API_meshes'][0]['volume_cm3']],
        proves='Raw scalar is not directly a component-cm3 value; native matrix determinant is required'))
    nofill = saved[CAPTURES[1]+'/trim_no_fill.f3d']['assets'][-1]
    fill = saved[CAPTURES[1]+'/trim_minimal_fill.f3d']['assets'][-1]
    assert nofill['raw_bounds'] == fill['raw_bounds'] and nofill['stored_asset_header_scalar'] == 0 and fill['stored_asset_header_scalar'] == 1.6875
    assert nofill['raw_node_count'] == fill['raw_node_count'] == 4
    report['controls'].append(dict(contrast='Same trimmed bounds and four nodes, open vs capped',
        scalar_values=[0.0,1.6875], node_counts=[4,4], triangle_counts=[3,4],
        raw_determinant_sums=[nofill['raw_triangle_determinant_sum_rounded_float64'],fill['raw_triangle_determinant_sum_rounded_float64']],
        proves='Not a raw bounding scalar or node count; open sentinel differs from raw determinant sum'))
    totals.update(full_main_runs=0,live_API_calls=0,runtime_semantics_changed=0)
    assert totals['archives'] == 10 and totals['assets'] == 17 and totals['closed_assets'] == 16 and totals['open_assets'] == 1
    report['counts'] = dict(totals)
    report['conclusion'] = 'All observed closed scalar values exactly equal the rounded exact raw-coordinate triangle determinant sum; open scalar0 agrees with public MeshBody.volume open-mesh behavior. Typed current-asset references plus stored matrix determinants numerically reproduce all saved current API volumes. This supports an observed raw-asset volume cache interpretation, not a universal native-field contract.'
    report['limits'] = [
        'All closed fixtures are positive oriented. Signed versus absolute cache semantics remain uncontrasted.',
        'Flag1 accompanies 16 positive closed assets and flag0 one open asset. Closed-zero-volume, invalid/nonmanifold and negative-orientation cases are absent; the flag is retained literally.',
        'Only existing origin-preserving positive uniform matrices are admitted. No arbitrary affine/assembly-world transform semantics are added.',
        'Additional assets retain unknown temporal/lifecycle role; their decoded buffers support arithmetic but do not establish source-state identity.',
        'No runtime field rename, shared parser change, mesh regeneration or physical target-attainment claim is made.',
        'A future small orientation-reversed tetra and closed degenerate control would distinguish signed/absolute and closedness/valid-volume hypotheses; no capture is run here.']
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zstd-library',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'mesh-asset-header-scalar-evidence.json')
    args=parser.parse_args()
    report=validate(ROOT,args.zstd_library)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['counts']))
