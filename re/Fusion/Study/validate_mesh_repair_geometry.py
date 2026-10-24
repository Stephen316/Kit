"""Repair saved-asset/current-cache corroboration without codec extensions."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from decode_mesh_contents import _backward_differences
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_mesh_normals import decode_mesh_normal_pools, unfold_octahedral
from decode_mesh_face_group_caches import decode_mesh_face_group_caches
from decode_placement import transform_point
from validate_mesh_normals import _direction_error
from validate_mesh_remesh import load

CAPTURE='meshrepairs-2387e4f9c2d2'


def asset_comparison(asset,native_mesh,api_mesh):
    """Pure numerical corroboration after typed asset/mesh identity; no role assignment."""
    geometry=asset['geometry'];original=api_mesh['original_polygon_mesh']
    if asset['asset_fusion_uuid']!=geometry['fusion_uuid']:
        raise ValueError('Repair asset comparison UUID disagrees')
    points=geometry['stored_node_coordinates_float32'];indices=geometry['triangle_node_indices']
    shape=(len(points),len(indices)//3)
    if shape not in ((4,3),(4,4)):
        raise ValueError('Repair comparison outside already supported tetra/open-tetra layouts')
    matrix=native_mesh['asset_coordinates_to_component_matrix']
    flattened=[v for p in points for v in transform_point(matrix,p)]
    if flattened!=original['nodeCoordinatesAsDouble'] or indices!=original['triangleNodeIndices']:
        raise ValueError('Repair numerical ordered coordinates/triangles differ from API snapshot')
    block=geometry['buffers'][2];raw=bytes.fromhex(block['uncompressed_payload_hex'])
    if (block['descriptor_hex']!='83a14403a15403a155c3' or 'decompression_scope' in block
            or len(raw)!=block['uncompressed_size'] or len(raw)!=shape[1]*3*8):
        raise ValueError('Repair normal comparison requires complete existing pair-pool layout')
    pairs=[list(struct.unpack_from('<2f',raw,i)) for i in range(0,len(raw),8)]
    vectors=[unfold_octahedral(*pair) for pair in pairs]
    flat=api_mesh['display_triangle_mesh']['normalVectorsAsDouble']
    api_vectors=[flat[i:i+3] for i in range(0,len(flat),3)]
    error=_direction_error(vectors,api_vectors)
    if error>=1e-7:
        raise ValueError('Repair normal direction set differs from actual API display snapshot')
    group=geometry['buffers'][5];group_raw=bytes.fromhex(group['uncompressed_payload_hex'])
    if (group['descriptor_hex']!='82a15401a16401' or 'decompression_scope' in group
            or len(group_raw)!=group['uncompressed_size'] or len(group_raw)!=shape[1]*4):
        raise ValueError('Repair label comparison requires complete existing buffer5 layout')
    differences=list(struct.unpack('<'+'i'*shape[1],group_raw));labels=_backward_differences(differences)
    if labels!=original['triangleFaceGroupTempIds']:
        raise ValueError('Repair ordered triangle labels differ from actual API snapshot')
    return dict(asset_object_id=asset['asset_object_id'],asset_member=asset['asset_member'],
        node_count=shape[0],triangle_count=shape[1],buffer_declared_sizes=[b['uncompressed_size'] for b in geometry['buffers']],
        exact_ordered_coordinate_array=True,exact_ordered_triangle_index_array=True,
        decoded_asset_normal_direction_count=len(vectors),API_display_normal_direction_count=len(api_vectors),
        maximum_normal_direction_set_component_discrepancy=error,normal_buffer_payload_hex=raw.hex(),
        exact_ordered_triangle_temporary_labels=labels,group_buffer_payload_hex=group_raw.hex(),
        numerical_scope='Typed asset references fixed before this comparison. Matrix is the selected native mesh stored uniform matrix; corroboration to this saved API snapshot does not assign a general temporal slot or persistent identity.')


def validate(root,zstd):
    # Agent A owns this public typed Repair definition/asset factory. This
    # validator consumes it without reproducing feature offsets or controls.
    from decode_mesh_repair import decode_mesh_repair
    truth=json.loads((root/CAPTURE/'ground_truth.json').read_text())
    journal=[json.loads(line) for line in (root/CAPTURE/'journal.jsonl').read_text().splitlines()]
    checks,samples,controls=[],[],[]
    def check(label,condition,**evidence):
        if not condition:raise AssertionError(label)
        checks.append(dict(check=label,**evidence))
    check('Actual3 Repair captures terminal/no case errors',(root/CAPTURE/'complete.txt').is_file() and truth['terminal_status']=='complete' and not truth['errors'] and len(truth['samples'])==3)
    closes=[r for r in journal if r['phase']=='owned_document_close_returned']
    check('Actual owned closeFalse3true',len(closes)==3 and all(r['returned'] is True and r['save'] is False for r in closes))
    check('Exact executed generator snapshot hash',hashlib.sha256((root/CAPTURE/'executed-generator-source.txt').read_bytes()).hexdigest()==truth['executed_generator_sha256'])
    for actual in truth['samples']:
        archive=CAPTURE+'/'+actual['file'];args=load(root,archive,zstd)
        data,records,features,member,members=args
        meshes=decode_mesh_contents_variants(data,records,member,members);before=copy.deepcopy(meshes)
        operations=decode_mesh_repair(*args,mesh_contents=meshes)
        check(archive+' typed Repair feature/assets successful',len(operations['decoded'])==1 and not operations['unresolved'])
        check(archive+' exact actual export hash',hashlib.sha256((root/archive).read_bytes()).hexdigest()==actual['export']['sha256'])
        check(archive+' strict original current mesh/no errors',len(meshes['decoded'])==1 and not meshes['unresolved'] and meshes['decoded'][0]['geometry']['format']=='ObservedUDPMESHv2SixBufferTetra')
        native=meshes['decoded'][0];settings=operations['decoded'][0]['settings']
        current=settings['current_mesh_asset'];additional=settings['additional_stored_asset']
        check(archive+' current typed asset/UUID/member equality',native['mesh_object_id']==213 and native['asset_object_id']==current['asset_object_id'] and native['asset_member']==current['asset_member'] and native['asset_fusion_uuid']==current['asset_fusion_uuid'])
        check(archive+' actual source handle equality before add/at rollback',actual['input_mesh_equals_import_handle'] is True and actual['rolled_mesh_equals_import_handle'] is True)
        after=actual['component_meshes_after_repair'];prior=actual['component_meshes_before_repair']
        check(archive+' actual named singleton source/current mesh',after['count']==prior['count']==1 and after['meshes'][0]['name']==prior['meshes'][0]['name']==native['name'])
        current_evidence=asset_comparison(current,native,after['meshes'][0])
        additional_evidence=asset_comparison(additional,native,prior['meshes'][0])
        check(archive+' current4/4 cache and additional recorded source geometry corroborated',current_evidence['triangle_count']==4 and additional_evidence['triangle_count']==(4 if actual['case'].startswith('closed') else 3))
        normals=decode_mesh_normal_pools(meshes);groups=decode_mesh_face_group_caches(meshes)
        check(archive+' existing12vector normal helper/no errors',len(normals['decoded'])==1 and not normals['unresolved'] and normals['decoded'][0]['stored_unit_vector_count']==12)
        check(archive+' existing4label group helper/no errors',len(groups['decoded'])==1 and not groups['unresolved'] and groups['decoded'][0]['decoded_triangle_face_group_temporary_ids']==[0]*4)
        check(archive+' existing pure buffer reads match generic summaries',normals['decoded'][0]['stored_payload_hex']==current_evidence['normal_buffer_payload_hex'] and groups['decoded'][0]['stored_payload_hex']==current_evidence['group_buffer_payload_hex'])
        check(archive+' observed current geometry closed and API closed after actual operation',native['geometry']['derived_closed_oriented_edge_incidence'] is True and after['meshes'][0]['isClosed'] is True)
        check(archive+' geometry/cache inspection leaves hierarchy unchanged',meshes==before)
        samples.append(dict(archive=archive,expected_mesh_contents=meshes,expected_normal_pools=normals,
            expected_face_group_caches=groups,current_asset_API_comparison=current_evidence,
            additional_asset_recorded_before_API_comparison=additional_evidence,
            additional_asset_temporal_role=None,
            actual_API_before_isClosed=prior['meshes'][0]['isClosed'],actual_API_after_isClosed=after['meshes'][0]['isClosed'],
            typed_asset_source='decode_mesh_repair settings.current_mesh_asset/additional_stored_asset; no independent offset inference'))
        if actual['case']=='open_close_holes':saved=(current,native,after['meshes'][0])
    # Exact legacy summaries across both original tetra and PlaneCut open/closed
    # variants guard unchanged factories; no full main/corpus decode is needed.
    mesh_reports=[json.loads((root/name).read_text()) for name in ('mesh-decoding.json','mesh-plane-cut-decoding.json')]
    old_normals={s['archive']:s['expected_decoded'] for s in json.loads((root/'mesh-normal-decoding.json').read_text())['samples']}
    old_groups={s['archive']:s['expected_decoded'] for s in json.loads((root/'mesh-face-group-cache-decoding.json').read_text())['samples']}
    for report in mesh_reports:
        for old in report['samples']:
            archive=old['archive'];args=load(root,archive,zstd)
            meshes=decode_mesh_contents_variants(args[0],args[1],args[3],args[4])
            expected=old.get('expected_mesh_contents',old['expected_decoded'])
            check(archive+' full legacy current mesh dictionary exact',meshes==expected)
            check(archive+' full legacy normal dictionary exact',decode_mesh_normal_pools(meshes)==old_normals[archive])
            check(archive+' full legacy temporary-group dictionary exact',decode_mesh_face_group_caches(meshes)==old_groups[archive])
            controls.append(dict(archive=archive,current_mesh_normal_and_group_dictionaries_exact=True))
    guards=[]
    for label,mutate in (
        ('Reject auxiliary normal prefix as complete comparison',lambda a:a['geometry']['buffers'][2].__setitem__('decompression_scope','Declared-size prefix only')),
        ('Reject label-buffer extent mismatch',lambda a:a['geometry']['buffers'][5].__setitem__('uncompressed_size',20)),
        ('Reject mismatched typed asset UUID',lambda a:a.__setitem__('asset_fusion_uuid','not-this-asset'))):
        asset,native,api=saved;bad=copy.deepcopy(asset);mutate(bad)
        try:asset_comparison(bad,native,api)
        except ValueError as error:reason=str(error)
        else:raise AssertionError(label)
        check(label,True);guards.append(dict(guard=label,reason=reason))
    return dict(interface='Focused validator consumes existing native mesh, normal, group and typed Repair asset helpers; no runtime decoder or factory changes',
        sample_count=3,current_mesh_count=3,explicit_asset_comparison_count=6,current_stored_normal_vector_count=36,
        current_temporary_label_count=12,check_count=len(checks),corroboration_guard_count=len(guards),
        samples=samples,legacy_controls=controls,checks=checks,corroboration_guards=guards,
        actual_document_close_journal=closes,actual_terminal_journal=journal[-1],
        limitations=['No codec/layout extension required; all current meshes original strict4/4 layout',
            'Additional explicit assets numerically match before-operation snapshots in these captures only; temporal slot role remainsNone',
            'Normal comparison is direction-set corroboration, without per-node/corner mapping',
            'Zero temporary label meaning and original polygon normal representation remain unresolved',
            'Stored controls/successful health/current closure do not reconstruct a repair algorithm or persistent lifecycle'],
        source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in (
            'validate_mesh_repair_geometry.py','decode_mesh_repair.py','decode_mesh_contents.py','decode_mesh_geometry_variants.py',
            'decode_mesh_normals.py','decode_mesh_face_group_caches.py')})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library');parser.add_argument('--output',default='mesh-repair-geometry-decoding.json');args=parser.parse_args()
    result=validate(Path(__file__).resolve().parent,args.zstd_library);Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ('sample_count','explicit_asset_comparison_count','check_count','corroboration_guard_count')}))

if __name__=='__main__':main()
