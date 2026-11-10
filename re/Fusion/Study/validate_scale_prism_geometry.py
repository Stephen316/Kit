"""Independent analytic solids and adversarial incidence for pure prism math."""
import copy
import hashlib
import json
import math
from pathlib import Path

from decode_scale_prism_geometry import derive_scaled_prism

ROOT=Path(__file__).resolve().parent


def operands():
    points=[[0.,0.,0.],[4.,0.,0.],[4.,3.,0.],[0.,3.,0.]]
    vertices=[dict(vertex_index=i+4*layer,native_sketch_point_object_id=101+i,layer=layer,
        derived_position_cm=[p[0],p[1],p[2]+2*layer]) for layer in (0,1) for i,p in enumerate(points)]
    pairs=[(i,(i+1)%4) for i in range(4)]+[(i+4,(i+1)%4+4) for i in range(4)]+[(i,i+4) for i in range(4)]
    edges=[dict(edge_index=200+i,vertex_indices=list(pair)) for i,pair in enumerate(pairs)]
    cycles=[[0,1,2,3],[4,5,6,7]]+[[i,(i+1)%4,(i+1)%4+4,i+4] for i in range(4)]
    faces=[dict(face_index=300+i,vertex_cycle=cycle) for i,cycle in enumerate(cycles)]
    return [vertices,edges,faces]


def validate():
    samples=[];guards=[];checks=[]
    for name,center,factors,bounds,volume in (
        ('Uniform about origin',[0.,0.,0.],[1.75]*3,[[0.,0.,0.],[7.,5.25,3.5]],128.625),
        ('Nonuniform about displaced point',[2.,-1.,0.],[1.2,.8,1.6],[[-.4,-.2,0.],[4.4,2.2,3.2]],36.864),
        ('Contraction about an outside point',[-2.,5.,1.],[.65]*3,[[-.7,1.75,.35],[1.9,3.7,1.65]],6.591),
    ):
        args=operands();row=derive_scaled_prism(*args,center,factors);solid=row['scaled_prism']
        assert math.isclose(solid['volume_cm3'],volume,rel_tol=0.,abs_tol=1e-10)
        actual=solid['axis_aligned_bounds_cm']
        assert math.dist(actual['minimum'],bounds[0])<1e-10 and math.dist(actual['maximum'],bounds[1])<1e-10
        assert row['source_prism']['volume_cm3']==24.
        # Six independent axis-aligned carrier equations define the analytic
        # rectangular solid, including signs chosen away from its centre.
        wanted={(axis,sign):sign*bounds[0 if sign==-1 else 1][axis] for axis in range(3) for sign in (-1,1)}
        observed={}
        for face in solid['planar_quadrilateral_boundaries']:
            n=face['outward_mathematical_unit_normal'];axis=max(range(3),key=lambda i:abs(n[i]));sign=1 if n[axis]>0 else -1
            assert math.isclose(n[axis],sign,abs_tol=1e-12) and all(abs(n[i])<1e-12 for i in range(3) if i!=axis)
            assert math.isclose(face['plane_constant_cm'],wanted[(axis,sign)],abs_tol=1e-10)
            observed[(axis,sign)]=face['face_index']
        assert set(observed)==set(wanted)
        for segment in solid['segments']:
            delta=segment['direction_cm'];assert sum(abs(v)>1e-10 for v in delta)==1
            assert all(math.dist(p,[a+(b-a)*t for a,b in zip(segment['start_position_cm'],segment['end_position_cm'])])<1e-10
                for t,p in ((0,segment['start_position_cm']),(1,segment['end_position_cm'])))
        samples.append(dict(case=name,analytical_volume_cm3=volume,analytical_bounds_cm=bounds,derived=row))
        checks.append(name+': independent volume, bounds and all six whole plane carriers')
    # Entity IDs and input enumeration carry no metric information. Keep the
    # same algebraic source positions but permute IDs and reverse cycle sense.
    args=operands();ids={i:80-3*i for i in range(8)}
    for v in args[0]:v['vertex_index']=ids[v['vertex_index']]
    for e in args[1]:e['vertex_indices']=[ids[v] for v in reversed(e['vertex_indices'])]
    for f in args[2]:f['vertex_cycle']=[ids[v] for v in reversed(f['vertex_cycle'])]
    for rows in args:rows.reverse()
    permuted=derive_scaled_prism(*args,[2.,-1.,0.],[1.2,.8,1.6])
    assert math.isclose(permuted['scaled_prism']['volume_cm3'],36.864,abs_tol=1e-10)
    checks.append('Permuted identities, enumeration, EDGE endpoints and FACE cycle sense preserve the independently defined solid')
    for name,mutate,center,factors in (
        ('Duplicate source vertex identity',lambda a:a[0][1].update(vertex_index=0),[0.,0.,0.],[1.,1.,1.]),
        ('Missing layer point partner',lambda a:a[0][4].update(native_sketch_point_object_id=999),[0.,0.,0.],[1.,1.,1.]),
        ('Nonuniform extrusion vector',lambda a:a[0][4].update(derived_position_cm=[0.,0.,3.]),[0.,0.,0.],[1.,1.,1.]),
        ('Repeated EDGE endpoint pair',lambda a:a[1][1].update(vertex_indices=[0,1]),[0.,0.,0.],[1.,1.,1.]),
        ('FACE diagonal instead of boundary EDGE',lambda a:a[2][0].update(vertex_cycle=[0,2,1,3]),[0.,0.,0.],[1.,1.,1.]),
        ('Open solid from repeated FACE',lambda a:a[2][1].update(vertex_cycle=[0,1,2,3]),[0.,0.,0.],[1.,1.,1.]),
        ('Unsupported zero Scale factor',lambda a:None,[0.,0.,0.],[1.,0.,1.]),
        ('Unsupported negative Scale factor',lambda a:None,[0.,0.,0.],[1.,-1.,1.]),
        ('Nonfinite source coordinate',lambda a:a[0][0].update(derived_position_cm=[math.inf,0.,0.]),[0.,0.,0.],[1.,1.,1.]),
        ('Nonfinite Scale centre',lambda a:None,[0.,math.nan,0.],[1.,1.,1.]),
    ):
        args=operands();mutate(args)
        try:derive_scaled_prism(*args,center,factors)
        except ValueError as error:guards.append(dict(case=name,reason=str(error)))
        else:raise AssertionError('Malformed pure prism accepted: '+name)
    return dict(scope='Analytic independent rectangular-solid equations and topology adversaries for pure mathematical construction; no native/API or history claims',
        source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ('decode_scale_prism_geometry.py','validate_scale_prism_geometry.py')},
        checks=checks,guards=guards,samples=samples,
        summary=dict(analytic_solids=3,whole_plane_equations=18,identity_permutation_controls=1,malformed_guards=len(guards),main_reader_runs=0,live_calls=0))


if __name__=='__main__':
    report=validate();(ROOT/'scale-prism-geometry-decoding.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['summary'],sort_keys=True))
