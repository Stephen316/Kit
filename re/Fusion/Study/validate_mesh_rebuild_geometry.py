"""Three actual Rebuild cache layouts with strict old coordinate/index codecs."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from decode_mesh_contents import _backward_differences, decode_paramesh_framing
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_mesh_normals import decode_mesh_normal_pools
from decode_mesh_face_group_caches import decode_mesh_face_group_caches
from decode_mesh_repair import decode_mesh_repair
from validate_mesh_remesh import load
from validate_mesh_normals import _direction_error
from validate_mesh_repair_geometry import asset_comparison

CAPTURE='meshrepairrebuilds-66d4316c2e8d'
SHAPES={'fast_density_eight':(132,216,368,140,120,72),
    'accurate_density_eight_offset_zero':(108,168,288,108,120,56),
    'accurate_density_eight_offset_point_zero_five':(144,240,376,140,136,80)}
NORMALS={'fast_density_eight':46,'accurate_density_eight_offset_zero':36,
    'accurate_density_eight_offset_point_zero_five':47}


def validate(root,zstd):
    truth=json.loads((root/CAPTURE/'ground_truth.json').read_text())
    journal=[json.loads(line) for line in (root/CAPTURE/'journal.jsonl').read_text().splitlines()]
    checks,samples,controls,guards=[],[],[],[]
    def check(label,condition,**fields):
        if not condition:raise AssertionError(label)
        checks.append(dict(check=label,**fields))
    check('Actual terminal3 exports/no case errors',(root/CAPTURE/'complete.txt').is_file() and truth['terminal_status']=='complete' and not truth['errors'] and len(truth['samples'])==3)
    closes=[r for r in journal if r['phase']=='owned_document_close_returned']
    check('Actual owned closeFalse3true',len(closes)==3 and all(r['returned'] is True and r['save'] is False for r in closes))
    check('Executed generator snapshot hash',hashlib.sha256((root/CAPTURE/'executed-generator-source.txt').read_bytes()).hexdigest()==truth['executed_generator_sha256'])
    normal_total=label_total=0
    for actual in truth['samples']:
        archive=CAPTURE+'/'+actual['file'];args=load(root,archive,zstd)
        data,records,features,member,members=args
        mesh=decode_mesh_contents_variants(data,records,member,members);before=copy.deepcopy(mesh)
        check(archive+' one typed current native mesh/asset fully decoded',len(mesh['decoded'])==1 and not mesh['unresolved'])
        native=mesh['decoded'][0];geometry=native['geometry']
        operation=decode_mesh_repair(*args,mesh_contents=mesh)
        check(archive+' owned Repair controls/current/additional factory fully decoded',len(operation['decoded'])==1 and not operation['unresolved'])
        settings=operation['decoded'][0]['settings']
        check(archive+' actual archive export hash',hashlib.sha256((root/archive).read_bytes()).hexdigest()==actual['export']['sha256'])
        check(archive+' actual direct input and rolled source equal owned mesh',actual['input_mesh_equals_import_handle'] is True and actual['rolled_mesh_equals_import_handle'] is True)
        check(archive+' exact native current asset377, retained additional211',native['mesh_object_id']==213 and native['asset_object_id']==settings['current_mesh_asset']['asset_object_id']==377 and settings['additional_stored_asset']['asset_object_id']==211)
        check(archive+' strict complete existing six-buffer framing',tuple(b['uncompressed_size'] for b in geometry['buffers'])==SHAPES[actual['case']] and all('decompression_scope' not in b for b in geometry['buffers']))
        frame,raw=decode_paramesh_framing(members[native['asset_member']])
        check(archive+' old default framing succeeds without relaxed options',frame['fusion_uuid']==native['asset_fusion_uuid'] and tuple(map(len,raw))==SHAPES[actual['case']])
        stored=list(struct.unpack('<'+'f'*(len(raw[0])//4),raw[0]))
        check(archive+' Float32 coordinate bytes replay',struct.pack('<'+'f'*len(stored),*stored)==raw[0] and [v for p in geometry['stored_node_coordinates_float32'] for v in p]==stored)
        differences=list(struct.unpack('<'+'i'*(len(raw[1])//4),raw[1]));indices=_backward_differences(differences)
        check(archive+' existing signedInt32 index integration and inverse byte replay',indices==geometry['triangle_node_indices'] and struct.pack('<'+'i'*len(indices),*([indices[i+1]-indices[i] for i in range(len(indices)-1)]+[indices[-1]]))==raw[1])
        after=actual['component_meshes_after_repair'];api=after['meshes'][0];polygon=api['original_polygon_mesh']
        check(archive+' actual singleton named current source agreement',after['count']==1 and api['name']==native['name'])
        check(archive+' exact ordered API coordinates/indices',[v for p in geometry['component_node_coordinates_cm'] for v in p]==polygon['nodeCoordinatesAsDouble'] and indices==polygon['triangleNodeIndices'])
        check(archive+' exact counts from strict buffer extents agree with API',len(geometry['stored_node_coordinates_float32'])==polygon['nodeCount'] and len(indices)//3==polygon['triangleCount'])
        check(archive+' closed reciprocal edge incidence independently corroborated',geometry['derived_closed_oriented_edge_incidence'] is True and geometry['derived_boundary_edge_count']==0 and api['isClosed'] is True)
        check(archive+' derived closed signed volume corroborates API current scalar',abs(geometry['derived_signed_volume_cm3']-api['volume'])<1e-7,absolute_volume_discrepancy_cm3=abs(geometry['derived_signed_volume_cm3']-api['volume']))
        normals=decode_mesh_normal_pools(mesh);groups=decode_mesh_face_group_caches(mesh)
        check(archive+' exact new normal tuple only',len(normals['decoded'])==1 and not normals['unresolved'] and normals['decoded'][0]['stored_unit_vector_count']==NORMALS[actual['case']])
        flat=api['display_triangle_mesh']['normalVectorsAsDouble'];vectors=[flat[i:i+3] for i in range(0,len(flat),3)]
        normal=normals['decoded'][0];error=_direction_error(normal['derived_asset_unit_vectors'],vectors)
        check(archive+' normal direction set corroborates actual API',error<1e-7,maximum_symmetric_component_discrepancy=error)
        check(archive+' exact Float32 pair byte replay',b''.join(struct.pack('<2f',*pair) for pair in normal['stored_packed_pairs_float32'])==raw[2])
        check(archive+' normal covector inverse scale corroborates API magnitudes',max(abs(math.hypot(*v)*normal['native_uniform_scale']-1) for v in vectors)<1e-7)
        check(archive+' ordered temporary labels exact API array',len(groups['decoded'])==1 and not groups['unresolved'] and groups['decoded'][0]['decoded_triangle_face_group_temporary_ids']==polygon['triangleFaceGroupTempIds']==[0]*polygon['triangleCount'])
        check(archive+' generic auxiliary semantics remain explicitly unresolved',geometry['unresolved_buffers']==[2,3,4,5])
        additional=asset_comparison(settings['additional_stored_asset'],native,actual['component_meshes_before_repair']['meshes'][0])
        check(archive+' additional strict4/4 asset corroborates recordedbefore arrays only',additional['node_count']==4 and additional['triangle_count']==4 and settings['additional_asset_temporal_role'] is None)
        check(archive+' no hierarchy/diagnostic mutations',mesh==before)
        normal_total+=normal['stored_unit_vector_count'];label_total+=polygon['triangleCount']
        samples.append(dict(archive=archive,expected_mesh_contents=mesh,expected_normal_pools=normals,
            expected_face_group_caches=groups,observed_buffer_sizes=list(SHAPES[actual['case']]),
            actual_API_display_vector_count=len(vectors),maximum_normal_direction_set_component_discrepancy=error,
            additional_asset_recorded_before_API_comparison=additional,
            additional_asset_temporal_role=None))
        if actual['case']=='fast_density_eight':guard_source=copy.deepcopy(native)
    # Complete old normal dictionaries include every previous encoding branch;
    # a few old mesh/group layouts additionally guard strict default geometry.
    for report_name in ('mesh-normal-decoding.json','mesh-normal-variant-decoding.json'):
        old=json.loads((root/report_name).read_text())
        for sample in old['samples']:
            args=load(root,sample['archive'],zstd);mesh=decode_mesh_contents_variants(args[0],args[1],args[3],args[4])
            result=decode_mesh_normal_pools(mesh)
            encoded=json.dumps(result,sort_keys=True,separators=(',',':')).encode()
            expected=json.dumps(sample['expected_decoded'],sort_keys=True,separators=(',',':')).encode()
            check(sample['archive']+' old full normal dictionaries canonical bytes exact',encoded==expected)
            controls.append(dict(archive=sample['archive'],control_kind='NormalPool',complete_summary_sha256=hashlib.sha256(encoded).hexdigest()))
    old=json.loads((root/'mesh-repair-geometry-decoding.json').read_text())
    for sample in old['samples']:
        args=load(root,sample['archive'],zstd);mesh=decode_mesh_contents_variants(args[0],args[1],args[3],args[4])
        check(sample['archive']+' prior Repair complete mesh/normal/group dictionaries exact',mesh==sample['expected_mesh_contents'] and decode_mesh_normal_pools(mesh)==sample['expected_normal_pools'] and decode_mesh_face_group_caches(mesh)==sample['expected_face_group_caches'])
        controls.append(dict(archive=sample['archive'],control_kind='PriorRepairMeshNormalsGroups',full_dictionaries_exact=True))
    def guard(label,mutate,decoder):
        bad=copy.deepcopy(guard_source);mutate(bad);result=decoder({'decoded':[bad]})
        check(label,not result['decoded'] and len(result['unresolved'])==1)
        guards.append(dict(guard=label,reason=result['unresolved'][0]['reason']))
    def extra_pair(mesh):
        block=mesh['geometry']['buffers'][2]
        block['uncompressed_payload_hex']+=struct.pack('<2f',0.,0.).hex();block['uncompressed_size']+=8
    guard('Reject adjacent unobserved11/18/47 normal pool',extra_pair,decode_mesh_normal_pools)
    guard('Reject prefix-only rebuilt normal pool',lambda m:m['geometry']['buffers'][2].__setitem__('decompression_scope','Declared-size prefix only'),decode_mesh_normal_pools)
    guard('Reject group buffer count mismatch',lambda m:m['geometry']['buffers'][5].__setitem__('uncompressed_size',76),decode_mesh_face_group_caches)
    return dict(interface='Existing common geometry callback and normal/group helpers with only evidenced layout tuple additions; no new codec algorithm',
        sample_count=3,current_mesh_count=3,decoded_stored_normal_vector_count=normal_total,
        ordered_API_temporary_label_count=label_total,check_count=len(checks),malformed_guard_count=len(guards),
        samples=samples,legacy_controls=controls,checks=checks,malformed_guards=guards,
        actual_document_close_journal=closes,actual_terminal_journal=journal[-1],
        limitations=['Only three exact new six-buffer geometry tuples/three normal-count tuples admitted',
            'Fast/Accurate controls are decoded independently by Repair owner; geometry is never used to infer controls or native identity',
            'All buffers are strict complete extents in these captures; unknown auxiliary semantics retained',
            'Direction-set corroboration does not assign normal vectors to vertices/corners',
            'Literal zero labels remain temporary cache values, not persistent geometry IDs',
            'Additional asset comparisons corroborate recordedbefore arrays only; temporal slot role remainsNone',
            'No Rebuild algorithm, target attainment, history replay or regeneration claim'],
        source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in (
            'validate_mesh_rebuild_geometry.py','decode_mesh_repair.py','decode_mesh_contents.py','decode_mesh_geometry_variants.py',
            'decode_mesh_normals.py','decode_mesh_face_group_caches.py')})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zstd-library');parser.add_argument('--output',default='mesh-rebuild-geometry-decoding.json');args=parser.parse_args()
    result=validate(Path(__file__).resolve().parent,args.zstd_library);Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ('sample_count','decoded_stored_normal_vector_count','ordered_API_temporary_label_count','check_count','malformed_guard_count')}))

if __name__=='__main__':main()
