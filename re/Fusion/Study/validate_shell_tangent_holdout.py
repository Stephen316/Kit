"""Separate saved tangent-chain Shell holdout, with no main-reader baseline."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

from decode_body_bindings import decode_body_bindings
from decode_extrude import decode_extrude
from decode_shell_reconstruction import decode_shell_reconstruction
from decode_sketch import attributes,numbers,reference
from validate_mesh_remesh import load

ROOT=Path(__file__).resolve().parent
FILE='bodymodes-d696a14d5f0b/shell_tangent.f3d'
TRUTH='bodymodes-d696a14d5f0b/ground_truth.json'


def validate(zstd):
    data,records,features,member,members=load(ROOT,FILE,zstd)
    # Native table fields only. No ordinal candidate or prior main output enters
    # the source proof; the decoder freshly qualifies same-blob BODY identifiers.
    mappings=decode_body_bindings(data,records,member,dict(streams=[dict(member=m)
        for m in members if m.endswith('.smbh')]))
    assert not mappings['unresolved']
    before=copy.deepcopy((features,members,mappings,records))
    summary=decode_shell_reconstruction(data,records,features,member,members,mappings)
    assert (features,members,mappings,records)==before
    assert len(summary['decoded'])==1 and not summary['unresolved']
    row=summary['decoded'][0];source=row['native_source_provenance'];settings=source['settings']
    assert settings['is_tangent_chain'] is True and settings['shell_type']=='SharpOffset'
    actual=next(s for s in json.loads((ROOT/TRUTH).read_text())['samples'] if s['file']==Path(FILE).name)
    assert actual['settings']['is_tangent_chain'] is True and actual['settings']['shell_type']==0
    assert settings['inside_thickness_cm']==actual['settings']['inside_cm']
    assert settings['outside_thickness_cm']==actual['settings']['outside_cm'] is None
    assert len(row['source_groups'])==len(source['source_groups'])==1
    native_group=source['source_groups'][0];group=row['source_groups'][0]
    primary={r.object_id:r for r in records if r.is_primary}
    points=[]
    for p in native_group['native_profile_points']:
        r=primary[p['point_object_id']];payload=data[r.body:r.end]
        _,cursor=attributes(payload,2)
        assert reference(payload,len(payload)-11)==native_group['source_sketch']['sketch_object_id']
        points.append(numbers(payload,cursor+19,3))
    assert len(points)==4 and all(p[2]==0 for p in points)
    low=[min(p[i] for p in points) for i in range(2)];high=[max(p[i] for p in points) for i in range(2)]
    assert {tuple(p[:2]) for p in points}=={(x,y) for x in (low[0],high[0]) for y in (low[1],high[1])}
    extrusion=primary[native_group['source_feature_object_id']]
    metadata=next(f for f in features if f['object_id']==extrusion.object_id)
    controls,errors=decode_extrude(data[extrusion.body:extrusion.end],metadata)
    assert not errors and controls['operation']['kind']=='NewBody'
    assert controls['extent']['stored_direction_vector']==[0.,0.,1.]
    distance=controls['extent']['side_one']['distance_cm']
    assert len(group['removed_face_operands'])==1
    removed=group['removed_face_operands'][0]
    assert removed['source_axis_side']==dict(axis=2,side=1)
    identity=group['literal_source_prism']['identity_provenance']
    assert set(removed['selected_source_loop']['vertex_cycle'])==set(identity['opposite'].values())
    dimensions=[high[0]-low[0],high[1]-low[1],distance];thickness=settings['inside_thickness_cm']
    independent_volume=math.prod(dimensions)-(dimensions[0]-2*thickness)*(dimensions[1]-2*thickness)*(dimensions[2]-thickness)
    shape=group['derived_shell']
    assert math.isclose(shape['material_volume_cm3'],independent_volume,rel_tol=0.,abs_tol=1e-10)
    assert shape['counts']==dict(vertices=16,segments=24,planar_faces=11,loops=12,connected_boundary_shells=1)
    cached=group['collective_cache_geometry_corroboration']
    assert cached['semantic_role_to_native_entity_mapping'] is None
    assert max(cached['collective_residuals_raw'].values())<1e-8
    return dict(scope='Additional direct-reader saved tangent-chain Shell holdout; outside the fixed fifteen-file main integration manifest, no main acquisition or API numerical geometry claim',
        archive=FILE,inputs_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in (FILE,TRUTH)},
        source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in (
            'validate_shell_tangent_holdout.py','decode_shell_reconstruction.py','decode_shell_source_operands.py',
            'decode_shell_box_geometry.py','decode_body_bindings.py','decode_extrude.py')},
        independent_native_profile_points_cm=points,independent_source_dimensions_cm=dimensions,
        independently_computed_material_volume_cm3=independent_volume,expected_summary=summary,
        actual_saved_API_settings=actual['settings'],API_numerical_geometry=None,
        validation=dict(tangent_chain_controls=1,source_prisms=1,vertices=16,segments=24,planar_faces=11,
            caller_inputs_unchanged=True,main_reader_calls=0,live_API_calls=0))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--zstd');args=p.parse_args()
    zstd=args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report=validate(zstd);(ROOT/'shell-tangent-holdout-decoding.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['validation'],sort_keys=True))
