"""Separate normal sets: typed outputs first, numerical collections without per-handle identity."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_mesh_normals import decode_mesh_normal_pools,unfold_octahedral
from decode_mesh_separate import decode_mesh_separate_definition
from validate_mesh_remesh import load
from validate_mesh_shell_normals import grid_comparison,old_goldens

ROOT=Path(__file__).resolve().parent
CAPTURE='meshseparates-41126250c03f'


def pool_values(mesh):
    geometry=mesh['geometry'];block=geometry['buffers'][2]
    assert block['descriptor_hex']=='83a14403a15403a155c3' and 'decompression_scope' not in block
    assert mesh['asset_fusion_uuid']==geometry['fusion_uuid']
    raw=bytes.fromhex(block['uncompressed_payload_hex'])
    assert len(raw)==block['uncompressed_size'] and len(raw)%8==0
    pairs=list(struct.iter_unpack('<2f',raw))
    assert b''.join(struct.pack('<2f',*pair) for pair in pairs)==raw
    units=[unfold_octahedral(*pair) for pair in pairs]
    scale=mesh['asset_coordinates_to_component_matrix'][0]
    assert scale>0 and mesh['stored_matrix_copies']==[mesh['asset_coordinates_to_component_matrix']]*2
    return units,[[v/scale for v in vector] for vector in units],scale


def triples(flat):
    assert len(flat)%3==0
    return [flat[i:i+3] for i in range(0,len(flat),3)]


def multiset_agreement(a,b,tolerance=1.2e-7):
    """Prove an unordered one-to-one numerical vector matching; publish no correspondence."""
    assert len(a)==len(b)
    remaining=list(b);worst=0
    for value in a:
        choices=[(max(abs(x-y) for x,y in zip(value,target)),i) for i,target in enumerate(remaining)]
        distance,index=min(choices)
        assert distance<tolerance
        worst=max(worst,distance);remaining.pop(index)
    assert not remaining
    return dict(vector_count=len(a),max_matched_Linf=worst,all_occurrences_used_once=True,
                scope='Aggregate numerical vector multiset only; matching indices never identify native mesh/API handles')


def prove_collection(meshes,actual):
    units=[];covectors=[];scales=[]
    for mesh in meshes:
        a,b,scale=pool_values(mesh);units+=a;covectors+=b;scales.append(scale)
    api=[v for mesh in actual for v in triples(mesh['display_triangle_mesh']['normalVectorsAsDouble'])]
    normalized_api=[[v/math.hypot(*vector) for v in vector] for vector in api]
    directions=grid_comparison(units,api,normalize=True)
    cv=grid_comparison(covectors,api)
    assert max(directions[side]['max_nearest_Linf'] for side in ('forward','reverse'))<1.2e-7
    assert max(cv[side]['max_nearest_Linf'] for side in ('forward','reverse'))<2e-7
    # All captured native result matrices share one independently parsed scale;
    # no API vector/mesh is assigned to a particular native result.
    assert len(set(scales))==1
    magnitude=max(abs(math.hypot(*v)*scales[0]-1) for v in api)
    assert magnitude<1e-7
    return dict(native_mesh_count=len(meshes),actual_API_current_mesh_count=len(actual),
        stored_vector_count=len(units),actual_API_display_vector_count=len(api),
        directions=directions,covectors=cv,inverse_scale_magnitude_max_error=magnitude,
        direction_multiset=multiset_agreement(units,normalized_api),
        covector_multiset=multiset_agreement(covectors,api,tolerance=2e-7),
        identity_scope='Native typed Separate output list and mesh/collection ownership select all current meshes before numerical checks. API collection is compared collectively, never paired by order, coordinates, directions or fabricated names.')


def validate(root,zstd):
    truth=json.loads((root/CAPTURE/'ground_truth.json').read_text())
    report=dict(scope='Three existing Separate current-result collections; one typed FaceGroup result allows a single-current-mesh holdout, multiple results remain collectively compared',
        samples=[],old_full_dictionary_controls=[],guards=[],source_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in (
            'decode_mesh_normals.py','decode_mesh_separate.py','decode_mesh_geometry_variants.py','decode_mesh_contents.py',
            'validate_mesh_separate_normals.py','validate_mesh_shell_normals.py','validate_mesh_remesh.py')})
    for sample in truth['samples']:
        archive=CAPTURE+'/'+sample['file']
        assert hashlib.sha256((root/archive).read_bytes()).hexdigest()==sample['export']['sha256']
        data,records,features,member,members=load(root,archive,zstd)
        meshes=decode_mesh_contents_variants(data,records,member,members)
        feature=next(f for f in features if f.get('native_kind_label')=='MeshSeparate')
        definition=decode_mesh_separate_definition(data,records,feature['object_id'])
        ids=definition['output_mesh_object_ids'];source=definition['source_selection']['mesh_object_id']
        assert set(ids)=={m['mesh_object_id'] for m in meshes['decoded']} and source not in ids
        assert all(m['feature_object_id']==definition['feature_object_id'] and m['component_object_id']==definition['component_object_id']
                   and m['mesh_collection_object_id']==definition['mesh_collection_object_id'] for m in meshes['decoded'])
        assert meshes['unresolved']==[dict(mesh_object_id=source,reason='Unobserved opt-in native mesh prefix')]
        actual=sample['component_meshes_after_separate']['meshes']
        assert len(actual)==len(ids)
        before=copy.deepcopy(meshes);proof=prove_collection(meshes['decoded'],actual)
        normals=decode_mesh_normal_pools(meshes)
        assert len(normals['decoded'])==len(ids) and not normals['unresolved'],normals
        assert meshes==before and {p['mesh_object_id'] for p in normals['decoded']}==set(ids)
        if definition['method']=='FaceGroup':
            assert ids==[369] and definition['feature_object_id']==352 and source==213 and len(actual)==1
            pool=normals['decoded'][0];mesh=meshes['decoded'][0]
            assert (mesh['geometry']['node_count'],mesh['geometry']['triangle_count'],pool['stored_unit_vector_count'])==(8,8,24)
        for pool in normals['decoded']:
            assert 'unresolved' in pool['association_status']
        report['samples'].append(dict(archive=archive,export_sha256=sample['export']['sha256'],expected_decoded=normals,
            expected_mesh_contents=meshes,typed_definition=definition,proof=proof,
            single_current_mesh_holdout=definition['method']=='FaceGroup',
            actual_API_current_names=[m['name'] for m in actual],native_result_names=[m['name'] for m in meshes['decoded']],
            API_names_assigned_to_native_IDs=False))
    controls=old_goldens(root)
    for row in json.loads((root/'mesh-shell-normal-decoding.json').read_text())['samples']:
        assert row['archive'] not in controls;controls[row['archive']]=row['expected_decoded']
    for archive,expected in controls.items():
        data,records,features,member,members=load(root,archive,zstd)
        meshes=decode_mesh_contents_variants(data,records,member,members)
        normals=decode_mesh_normal_pools(meshes)
        assert normals==expected,(archive,'Old full normal dictionary changed')
        report['old_full_dictionary_controls'].append(dict(archive=archive,decoded_pool_count=len(expected['decoded']),full_normal_dictionary_exact=True))
    group_sample=next(s for s in report['samples'] if s['single_current_mesh_holdout'])
    guard_mesh=group_sample['expected_mesh_contents']['decoded'][0]
    def guard(label,alter):
        mesh=copy.deepcopy(guard_mesh);alter(mesh)
        result=decode_mesh_normal_pools(dict(decoded=[mesh]))
        assert not result['decoded'] and len(result['unresolved'])==1
        report['guards'].append(dict(check=label,passed=True,reason=result['unresolved'][0]['reason']))
    def extra_pair(mesh):
        block=mesh['geometry']['buffers'][2];block['uncompressed_payload_hex']+=struct.pack('<2f',0.,0.).hex();block['uncompressed_size']+=8
    guard('Only observed8/8/24 tuple admitted',extra_pair)
    guard('Typed asset UUID mismatch rejects',lambda mesh:mesh.__setitem__('asset_fusion_uuid','wrong'))
    report['counts']=dict(actual_Separate_archives=3,single_FaceGroup_current_mesh_holdouts=1,
        native_current_result_pools=sum(len(s['expected_decoded']['decoded']) for s in report['samples']),
        collectively_compared_multi_result_collections=sum(s['proof']['native_mesh_count']>1 for s in report['samples']),
        old_archive_controls=len(controls),old_pool_dictionaries_preserved=sum(s['decoded_pool_count'] for s in report['old_full_dictionary_controls']),
        guards=len(report['guards']),full_main_runs=0,live_API_calls=0)
    report['limits']=['Only one additional exact node/triangle/pool-count tuple8/8/24 is admitted; all other unsupported counts remain rejected.',
        'Multiple result meshes lack an API per-handle native-ID bridge. Aggregated set/multiset agreements do not assign API names, collection positions or persistent topology to native results.',
        'The retained source213 remains excluded from current pools and retains its separate current-reader diagnostic.',
        'Stored pool order, per-vertex/corner assignment, original PolygonMesh normals and regeneration remain unresolved.']
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--zstd-library',required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'mesh-separate-normal-decoding.json')
    args=parser.parse_args();report=validate(ROOT,args.zstd_library)
    args.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['counts']))
