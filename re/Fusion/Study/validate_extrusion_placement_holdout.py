"""Separate native translated-Circle holdout; no main-reader acquisition."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

from decode_body_bindings import decode_body_bindings
from decode_extrusion_reconstruction import decode_extrusion_reconstruction
from decode_sketch import attributes, numbers, reference
from validate_mesh_remesh import load

ROOT=Path(__file__).resolve().parent
FILE='loftbrepends-e07e3859ed20/edge_both_tangent.f3d'
TRUTH='loftbrepends-e07e3859ed20/ground_truth.json'


def validate(zstd):
    data,records,features,member,members=load(ROOT,FILE,zstd)
    bindings=decode_body_bindings(data,records,member,dict(streams=[dict(member=m)
        for m in members if m.endswith('.smbh')]))
    assert not bindings['unresolved']
    before=copy.deepcopy((records,features,members,bindings))
    summary=decode_extrusion_reconstruction(data,records,features,member,members,bindings)
    assert (records,features,members,bindings)==before
    assert len(summary['decoded'])==2 and not summary['unresolved']
    by={r.object_id:r for r in records if r.is_primary}
    independent=[]
    for row in summary['decoded']:
        source=row['native_source_provenance'];group,=source['source_groups']
        circle,=group['native_profile_circles']
        cr=by[circle['circle_object_id']];cb=data[cr.body:cr.end];_,cursor=attributes(cb,2)
        native_circle=numbers(cb,cursor,12);radius=native_circle[9]
        point_id=reference(cb,cursor+96);point=by[point_id];pb=data[point.body:point.end]
        _,pc=attributes(pb,2);center_local=numbers(pb,pc+19,3)
        assert center_local==native_circle[:3]==[0.,0.,0.]
        frame=group['source_sketch_frame_provenance']['canonical_placement']
        transform=by[frame['transform_object_id']];tb=data[transform.body:transform.end]
        if len(tb)==143:
            matrix=numbers(tb,3,16)
        else:
            assert len(tb)==15 and tb[:4]==bytes.fromhex('00000100')
            matrix=[1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.]
        # This saved holdout has translation only. Qualify that property directly
        # in the native matrix before using the simple independent box formula.
        assert [matrix[i] for i in (0,1,2,4,5,6,8,9,10)]==[1.,0.,0.,0.,1.,0.,0.,0.,1.]
        assert matrix[12:]==[0.,0.,0.,1.]
        center=[matrix[3],matrix[7],matrix[11]]
        controls=source['settings'];side=controls['extent']['side_one']
        assert controls['start']['kind']=='ProfilePlane' and controls['extent']['mode']=='OneSided'
        assert controls['extent']['stored_direction_vector']==[0.,0.,1.]
        assert side['condition']=='Distance' and side['distance_cm']==1. and side['taper_angle_radians']==0.
        expected_min=[center[0]-radius,center[1]-radius,center[2]]
        expected_max=[center[0]+radius,center[1]+radius,center[2]+1.]
        expected_volume=math.pi*radius**2
        model=row['derived_geometry'];caps=model['axial_stations']
        assert caps[0]['center_cm']==center and caps[1]['center_cm']==[center[0],center[1],center[2]+1.]
        assert model['component_axis_aligned_bounds_cm']==dict(minimum=expected_min,maximum=expected_max)
        assert math.isclose(model['volume_cm3'],expected_volume,rel_tol=0.,abs_tol=1e-10)
        assert row['source_to_cache_entity_mapping'] is None and row['current_or_final_geometry_identity'] is None
        proof=row['native_cache_geometry_corroboration']
        assert proof['semantic_cap_to_native_ENTITY_mapping'] is None
        assert max(proof['complete_coefficient_residuals_raw'].values())<1e-8
        independent.append(dict(feature_object_id=row['feature_object_id'],center_component_cm=center,
            radius_cm=radius,volume_cm3=expected_volume,bounds_cm=[expected_min,expected_max]))
    assert sorted((r['center_component_cm'][2],r['radius_cm']) for r in independent)==[(0.,1.),(4.,.6)]
    actual=next(s for s in json.loads((ROOT/TRUTH).read_text())['samples'] if s['file']==Path(FILE).name)
    api_bodies=[face['body'] for face in actual['source_parent_faces_before_loft']]
    assert len(api_bodies)==2 and len({b['name'] for b in api_bodies})==2
    # Independent saved numerical API evidence is compared collectively. No API
    # entity token, collection order or numerical match assigns native identity.
    expected=sorted(([b['volume_cm3']]+b['bounding_box_min_cm']+b['bounding_box_max_cm'] for b in api_bodies))
    derived=sorted(([r['volume_cm3']]+r['bounds_cm'][0]+r['bounds_cm'][1] for r in independent))
    residual=max(abs(x-y) for a,b in zip(expected,derived) for x,y in zip(a,b))
    assert residual<1e-10
    files=(FILE,TRUTH,'decode_extrusion_reconstruction.py','decode_extrusion_source_operands.py',
        'decode_circular_extrusion_geometry.py','validate_extrusion_placement_holdout.py')
    return dict(scope='Separate translated-Circle saved holdout outside fixed23 integration manifest; native body proof and collectively corroborated saved API numerical geometry, without chronological or per-entity API identity',
        archive=FILE,inputs_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files},
        independently_read_native_cylinders=independent,expected_summary=summary,
        actual_saved_API_body_geometry=api_bodies,collective_API_residual_cm_or_cm3=residual,
        validation=dict(qualified_extrudes=2,translated_sketches=1,complete_cylinders=2,
            collective_saved_API_body_checks=2,main_reader_calls=0,live_API_calls=0,caller_inputs_unchanged=True))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--zstd');args=p.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd)
    (ROOT/'extrusion-placement-holdout-decoding.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(report['validation'],sort_keys=True))
