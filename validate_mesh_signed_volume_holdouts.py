"""Actual ReverseNormal holdouts distinguish signed mesh-header volume evidence."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

from decode_mesh_contents import ASSET, replay_paramesh_geometry
from decode_mesh_geometry_variants import decode_mesh_asset, decode_mesh_contents_variants, native_layout
from fusion_archive import read_members
from fusion_metadata import design_records
from validate_mesh_asset_header_scalar import exact_mesh_metrics, determinant3

ROOT = Path(__file__).resolve().parent
FOLDER = 'meshreversenormals-2bc2dd3780cc'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(zstd):
    folder = ROOT/FOLDER
    truth = json.loads((folder/'ground_truth.json').read_text())
    assert (folder/'complete.txt').is_file() and not truth['errors']
    assert truth['terminal_status'] == 'complete' and len(truth['samples']) == 3
    assert sha(folder/'executed-generator-source.txt') == truth['executed_generator_sha256']
    assert sha(folder/'executed-mesh-source-helper.txt') == truth['mesh_source_helper_sha256']
    rows, totals, controls = [], dict(archives=0,assets=0,closed_assets=0,negative_closed_assets=0,open_assets=0,current_API_volume_comparisons=0), []
    saved = {}
    for sample in truth['samples']:
        archive = FOLDER+'/'+sample['file']
        assert sample['close_owned_document_returned'] is True
        assert sha(ROOT/archive) == sample['export']['sha256']
        members = read_members(ROOT/archive,zstd)
        member = next(k for k in members if k.endswith('/FusionDesignSegmentType1/BulkStream.dat'))
        data = members[member]
        records,_ = design_records(data,members[member.replace('BulkStream.dat','MetaStream.dat')])
        current = decode_mesh_contents_variants(data,records,member,members)
        assert not current['unresolved'] and len(current['decoded']) == 1
        mesh = current['decoded'][0]
        assets = []
        for record in records:
            if not record.is_primary or record.class_guid != ASSET:
                continue
            asset = decode_mesh_asset(data,records,record.object_id,member,members)
            geometry = asset['geometry']
            raw = data[record.body:record.end]
            scalar = struct.unpack_from('<d',raw,2)[0]
            volume,closed,bounds = exact_mesh_metrics(geometry['stored_node_coordinates_float32'],geometry['triangle_node_indices'])
            assert math.isfinite(scalar) and struct.pack('<d',scalar) == raw[2:10]
            assert scalar == asset['stored_asset_header_scalar']
            assert replay_paramesh_geometry(geometry) == members[asset['asset_member']]
            if closed:
                assert scalar == float(volume) and volume != 0 and raw[10] == 1
                totals['closed_assets'] += 1
                if scalar < 0:
                    assert scalar != abs(float(volume))
                    totals['negative_closed_assets'] += 1
            else:
                assert scalar == 0 and raw[10] == 0
                totals['open_assets'] += 1
            assets.append(dict(asset_object_id=record.object_id,asset_member=asset['asset_member'],
                embedded_fusion_uuid=asset['asset_fusion_uuid'],native_prefix_hex=raw[:13].hex(),
                stored_scalar=scalar,stored_scalar_hex=raw[2:10].hex(),stored_flag=raw[10],
                exact_raw_triangle_determinant_sum=str(volume),closed_oriented_edge_incidence=closed,
                raw_bounds=bounds,exact_literal_header_replay=True,exact_geometry_frame_replay=True,
                is_explicitly_referenced_current_asset=record.object_id==mesh['asset_object_id'],
                asset_lifecycle_scope='Only current native mesh asset equality is assigned here; other stored assets retain unqualified lifecycle'))
            totals['assets'] += 1
        selected = [row for row in assets if row['is_explicitly_referenced_current_asset']]
        assert len(selected) == 1
        actual = sample['component_meshes_after_reverse']['meshes']
        assert len(actual) == 1
        predicted = selected[0]['stored_scalar']*determinant3(mesh['asset_coordinates_to_component_matrix'])
        assert math.isclose(predicted,actual[0]['volume'],rel_tol=1e-14,abs_tol=1e-15)
        assert selected[0]['closed_oriented_edge_incidence'] == actual[0]['isClosed']
        totals['current_API_volume_comparisons'] += 1
        observed = [step['component_meshes_after']['meshes'][0]['volume'] for step in sample['steps']]
        assert all(step['status']=='FeatureReturned' and step['add_returned_feature'] for step in sample['steps'])
        row = dict(archive=archive,archive_sha256=sample['export']['sha256'],assets=assets,
            current_mesh_object_id=mesh['mesh_object_id'],current_asset_object_id=mesh['asset_object_id'],
            native_uniform_matrix=mesh['asset_coordinates_to_component_matrix'],
            component_volume_from_signed_scalar_and_determinant=predicted,actual_current_API_volume_cm3=actual[0]['volume'],
            actual_API_step_volume_sequence_cm3=observed,
            identity_scope='Current asset selected by complete native mesh/collection/UUID/file references before numerical API corroboration')
        rows.append(row);saved[sample['case']] = (sample,row)
        totals['archives'] += 1
    once,a = saved['closed_once'];twice,b = saved['closed_twice'];opened,c = saved['open_once']
    assert a['actual_current_API_volume_cm3'] < 0 and b['actual_current_API_volume_cm3'] > 0
    sequence = b['actual_API_step_volume_sequence_cm3']
    assert len(sequence)==2 and sequence[0] == a['actual_current_API_volume_cm3'] and sequence[1] == -sequence[0]
    before = twice['component_meshes_before_reverse']['meshes'][0]['original_polygon_mesh']
    after = twice['component_meshes_after_reverse']['meshes'][0]['original_polygon_mesh']
    assert before['triangleNodeIndices'] == after['triangleNodeIndices']
    assert before['nodeCoordinatesAsDouble'] == after['nodeCoordinatesAsDouble']
    controls.append(dict(control='Same owned closed tetra reversed once and twice',
        actual_API_signed_volume_sequence=sequence,twice_restores_actual_triangle_indices_and_coordinates=True,
        excludes='Absolute-only volume cache for the two observed negative closed assets',
        scope='Actual fixture observation; not a general native editing or involution proof'))
    assert c['actual_current_API_volume_cm3'] == 0 and all(row['stored_scalar']==0 for row in c['assets'])
    guards = []
    for value in (float('nan'),float('inf'),float('-inf')):
        payload = bytes(2)+struct.pack('<d',value)+b'\1\1\0'
        try:
            native_layout('AssetPrefix',payload,{})
        except ValueError as error:
            guards.append(dict(nonfinite_value=repr(value),reason=str(error)))
        else:
            raise AssertionError('Nonfinite mesh header accepted')
    assert totals == dict(archives=3,assets=7,closed_assets=5,negative_closed_assets=2,open_assets=2,current_API_volume_comparisons=3)
    sources = ['validate_mesh_signed_volume_holdouts.py','decode_mesh_contents.py','decode_mesh_geometry_variants.py',
               'validate_mesh_asset_header_scalar.py','fusion_archive.py','fusion_metadata.py']
    return dict(scope='Three actual owned ReverseNormal captures; raw signed-header evidence, no main pipeline or live API calls',
        samples=rows,controls=controls,nonfinite_guards=guards,summary=totals,
        conclusion='Observed closed mesh scalar follows signed raw-coordinate triangle volume, including two negative assets. Native matrix determinants reproduce all three current API volumes. The runtime header remains a finite literal, now accepting observed negative values.',
        limitations=['Flag1/0 closed/open association is observed, not a universal bit contract.',
            'Closed-zero-volume/nonmanifold/invalid states remain uncontrasted.',
            'Only origin-preserving positive uniform native matrices are qualified.',
            'Open tetra fixtures happen to have zero raw triangle sum; earlier open nonzero-sum control remains in historical evidence.',
            'No arbitrary historical asset lifecycle or regenerated feature geometry is inferred.'],
        source_sha256={name:sha(ROOT/name) for name in sources},
        historical_scalar_report_sha256=sha(ROOT/'mesh-asset-header-scalar-evidence.json'),
        ground_truth_sha256=sha(folder/'ground_truth.json'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zstd-library',required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'mesh-signed-volume-holdouts.json')
    args = parser.parse_args()
    result = validate(args.zstd_library)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['summary']))
