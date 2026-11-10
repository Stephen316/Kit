"""Actual ReduceDeviation current/additional assets; no codec extensions."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from decode_mesh_contents import _backward_differences
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_mesh_normals import decode_mesh_normal_pools,unfold_octahedral
from decode_mesh_face_group_caches import decode_mesh_face_group_caches
from decode_placement import transform_point
from validate_mesh_normals import _direction_error
from validate_mesh_remesh import load

CAPTURE='meshreducedeviations-05a5d48e46d0'
SHAPES={(72,96,176,64,72,32),(72,96,192,72,96,32)}


def asset_comparison(asset,native,api):
    """Compare fixed typed asset numerically to a saved snapshot, assigning no temporal role."""
    g=asset['geometry'];polygon=api['original_polygon_mesh']
    if g['fusion_uuid']!=asset['asset_fusion_uuid']:raise ValueError('Deviation asset UUID disagreement')
    if tuple(b['uncompressed_size'] for b in g['buffers']) not in SHAPES or any('decompression_scope' in b for b in g['buffers']):
        raise ValueError('Deviation comparison outside complete previously supported6/8 layouts')
    points=g['stored_node_coordinates_float32'];indices=g['triangle_node_indices']
    if len(points)!=6 or len(indices)!=24:raise ValueError('Deviation comparison outside6-node/8-triangle source')
    flat=[v for point in points for v in transform_point(native['asset_coordinates_to_component_matrix'],point)]
    if flat!=polygon['nodeCoordinatesAsDouble'] or indices!=polygon['triangleNodeIndices']:
        raise ValueError('Deviation ordered geometry arrays differ from saved API snapshot')
    normal=g['buffers'][2];raw=bytes.fromhex(normal['uncompressed_payload_hex'])
    if normal['descriptor_hex']!='83a14403a15403a155c3' or len(raw)!=normal['uncompressed_size'] or len(raw) not in (176,192):
        raise ValueError('Deviation normal comparison requires complete old22/24-pair buffer')
    pairs=[struct.unpack_from('<2f',raw,i) for i in range(0,len(raw),8)]
    vectors=[unfold_octahedral(*pair) for pair in pairs]
    values=api['display_triangle_mesh']['normalVectorsAsDouble'];api_vectors=[values[i:i+3] for i in range(0,len(values),3)]
    error=_direction_error(vectors,api_vectors)
    if error>=1e-7:raise ValueError('Deviation asset display-normal directions disagree')
    group=g['buffers'][5];group_raw=bytes.fromhex(group['uncompressed_payload_hex'])
    if group['descriptor_hex']!='82a15401a16401' or len(group_raw)!=group['uncompressed_size'] or len(group_raw)!=32:
        raise ValueError('Deviation temporary-label comparison requires complete8-entry buffer5')
    labels=_backward_differences(list(struct.unpack('<8i',group_raw)))
    if labels!=polygon['triangleFaceGroupTempIds']:raise ValueError('Deviation ordered temporary-label array differs from saved API')
    return dict(asset_object_id=asset['asset_object_id'],asset_member=asset['asset_member'],
        observed_buffer_sizes=[b['uncompressed_size'] for b in g['buffers']],node_count=6,triangle_count=8,
        exact_ordered_coordinate_and_index_arrays=True,stored_normal_vector_count=len(vectors),
        actual_API_display_vector_count=len(api_vectors),maximum_normal_direction_set_component_discrepancy=error,
        exact_ordered_triangle_temporary_labels=labels,
        scope='Only numerical corroboration after typed asset/selected-mesh proof. Current native uniform matrix applied for this comparison; no universal temporal slot role or persistent identity assigned.')


def validate(root,zstd):
    from decode_mesh_reduce import decode_mesh_reduce
    truth=json.loads((root/CAPTURE/'ground_truth.json').read_text())
    journal=[json.loads(line) for line in (root/CAPTURE/'journal.jsonl').read_text().splitlines()]
    checks,samples,controls,guards=[],[],[],[]
    def check(label,condition,**fields):
        if not condition:raise AssertionError(label)
        checks.append(dict(check=label,**fields))
    check('Actual3 captures terminal/no case errors',(root/CAPTURE/'complete.txt').is_file() and truth['terminal_status']=='complete' and truth['errors']==[] and len(truth['samples'])==3)
    closes=[r for r in journal if r['phase']=='owned_document_close_returned']
    check('Actual owned closeFalse3true',len(closes)==3 and all(r['returned'] is True and r['save'] is False for r in closes))
    check('Executed generator snapshot hash',hashlib.sha256((root/CAPTURE/'executed-generator-source.txt').read_bytes()).hexdigest()==truth['executed_generator_sha256'])
    for actual in truth['samples']:
        archive=CAPTURE+'/'+actual['file'];args=load(root,archive,zstd);data,records,features,member,members=args
        mesh=decode_mesh_contents_variants(data,records,member,members);before=copy.deepcopy(mesh)
        operations=decode_mesh_reduce(*args,mesh_contents=mesh)
        check(archive+' typed Deviation controls/assets decode',len(operations['decoded'])==1 and not operations['unresolved'])
        check(archive+' one current native mesh without errors',len(mesh['decoded'])==1 and not mesh['unresolved'])
        check(archive+' actual export hash',hashlib.sha256((root/archive).read_bytes()).hexdigest()==actual['export']['sha256'])
        native=mesh['decoded'][0];g=native['geometry'];settings=operations['decoded'][0]['settings']
        check(archive+' current mesh/typed asset equality',native['mesh_object_id']==213 and native['asset_object_id']==settings['current_mesh_asset']['asset_object_id'] and native['asset_member']==settings['current_mesh_asset']['asset_member'])
        check(archive+' actual before-add/rollback input handle equality',actual['input_mesh_equals_import_handle'] is True and actual['feature_input_mesh_equals_import_handle'] is True)
        current=actual['component_meshes_after_reduce'];prior=actual['component_meshes_before_reduce']
        check(archive+' actual singleton current/source name agrees',current['count']==prior['count']==1 and current['meshes'][0]['name']==prior['meshes'][0]['name']==native['name'])
        current_evidence=asset_comparison(settings['current_mesh_asset'],native,current['meshes'][0])
        additional_evidence=asset_comparison(settings['additional_stored_asset'],native,prior['meshes'][0])
        check(archive+' current complete existing24-pair layout',current_evidence['observed_buffer_sizes']==[72,96,192,72,96,32] and current_evidence['stored_normal_vector_count']==24)
        check(archive+' additional existing24-pair layout role remains unassigned',additional_evidence['observed_buffer_sizes']==[72,96,192,72,96,32] and settings['additional_asset_temporal_role'] is None)
        normals=decode_mesh_normal_pools(mesh);groups=decode_mesh_face_group_caches(mesh)
        check(archive+' existing current normal helper exact24vectors',len(normals['decoded'])==1 and not normals['unresolved'] and normals['decoded'][0]['stored_unit_vector_count']==24)
        check(archive+' existing current group helper exact8literalzeros',len(groups['decoded'])==1 and not groups['unresolved'] and groups['decoded'][0]['decoded_triangle_face_group_temporary_ids']==[0]*8)
        check(archive+' exact ordered current API geometry',[v for point in g['component_node_coordinates_cm'] for v in point]==current['meshes'][0]['original_polygon_mesh']['nodeCoordinatesAsDouble'] and g['triangle_node_indices']==current['meshes'][0]['original_polygon_mesh']['triangleNodeIndices'])
        check(archive+' closed oriented edge incidence and API closure',g['derived_closed_oriented_edge_incidence'] is True and g['derived_boundary_edge_count']==0 and current['meshes'][0]['isClosed'] is True)
        check(archive+' derived closed current volume corroborated',abs(g['derived_signed_volume_cm3']-current['meshes'][0]['volume'])<1e-7)
        check(archive+' generic auxiliary diagnostics retained',g['unresolved_buffers']==[2,3,4,5])
        check(archive+' no mesh hierarchy/diagnostic changes during corroboration',mesh==before)
        samples.append(dict(archive=archive,expected_mesh_contents=mesh,expected_normal_pools=normals,
            expected_face_group_caches=groups,current_asset_API_comparison=current_evidence,
            additional_asset_recorded_before_API_comparison=additional_evidence,additional_asset_temporal_role=None))
        if actual['case']=='adaptive_deviation_point_zero_five':saved=(settings['current_mesh_asset'],native,current['meshes'][0])
    # Three previous Repair and Rebuild cases are complete existing goldens.
    for report_name in ('mesh-repair-geometry-decoding.json','mesh-rebuild-geometry-decoding.json'):
        for old in json.loads((root/report_name).read_text())['samples']:
            args=load(root,old['archive'],zstd);mesh=decode_mesh_contents_variants(args[0],args[1],args[3],args[4])
            check(old['archive']+' prior complete mesh/normal/group dictionaries exact',mesh==old['expected_mesh_contents'] and decode_mesh_normal_pools(mesh)==old['expected_normal_pools'] and decode_mesh_face_group_caches(mesh)==old['expected_face_group_caches'])
            controls.append(dict(archive=old['archive'],complete_mesh_normal_group_dictionaries_exact=True))
    normal_old={s['archive']:s['expected_decoded'] for s in json.loads((root/'mesh-normal-decoding.json').read_text())['samples']}
    group_old={s['archive']:s['expected_decoded'] for s in json.loads((root/'mesh-face-group-cache-decoding.json').read_text())['samples']}
    for old in json.loads((root/'mesh-reduce-decoding.json').read_text())['samples']:
        args=load(root,old['archive'],zstd);mesh=decode_mesh_contents_variants(args[0],args[1],args[3],args[4])
        check(old['archive']+' prior Reduce complete mesh/normal/group dictionaries exact',mesh==old['expected_mesh_contents'] and decode_mesh_normal_pools(mesh)==normal_old[old['archive']] and decode_mesh_face_group_caches(mesh)==group_old[old['archive']])
        controls.append(dict(archive=old['archive'],complete_mesh_normal_group_dictionaries_exact=True))
    for label,mutate in (
        ('Reject normal-prefix continuation as full asset proof',lambda a:a['geometry']['buffers'][2].__setitem__('decompression_scope','Declared-size prefix only')),
        ('Reject label-buffer extent mismatch',lambda a:a['geometry']['buffers'][5].__setitem__('uncompressed_size',36)),
        ('Reject asset UUID mismatch',lambda a:a.__setitem__('asset_fusion_uuid','wrong'))):
        asset,native,api=saved;bad=copy.deepcopy(asset);mutate(bad)
        try:asset_comparison(bad,native,api)
        except ValueError as error:reason=str(error)
        else:raise AssertionError(label)
        check(label,True);guards.append(dict(guard=label,reason=reason))
    return dict(interface='Focused geometry corroboration consumes typed ReduceDeviation assets and existing common mesh/normal/group helpers; no shared source changes',
        sample_count=3,current_mesh_count=3,explicit_asset_comparison_count=6,current_stored_normal_vector_count=72,
        current_temporary_label_count=24,check_count=len(checks),corroboration_guard_count=len(guards),
        samples=samples,legacy_controls=controls,checks=checks,corroboration_guards=guards,
        actual_document_close_journal=closes,actual_terminal_journal=journal[-1],
        limitations=['All current/additional geometry layouts already supported; no codec extension',
            'Requested deviation and method semantics remain the independent control helper responsibility',
            'Geometry/counts do not prove maximum-deviation target attainment or method normalization',
            'Additional asset match to recordedbefore snapshot is numerical corroboration only; temporal roleNone',
            'Normal vectors remain unordered direction pools; no corner/node mapping',
            'Zero labels are literal temporary cache values; no persistent native geometry identity',
            'No reduction algorithm, regeneration or history/lifecycle claim'],
        source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in (
            'validate_mesh_reduce_deviation_geometry.py','decode_mesh_reduce.py','decode_mesh_contents.py',
            'decode_mesh_geometry_variants.py','decode_mesh_normals.py','decode_mesh_face_group_caches.py')})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library');parser.add_argument('--output',default='mesh-reduce-deviation-geometry-decoding.json');args=parser.parse_args()
    result=validate(Path(__file__).resolve().parent,args.zstd_library);Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ('sample_count','explicit_asset_comparison_count','check_count','corroboration_guard_count')}))

if __name__=='__main__':main()
