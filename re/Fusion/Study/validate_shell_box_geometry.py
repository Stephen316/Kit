"""Independent exact-volume, axis permutation and incidence checks for box Shell."""
import copy
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

from decode_shell_box_geometry import derive_box_shell

ROOT=Path(__file__).resolve().parent
BOUNDS=dict(minimum=[1.,1.,0.],maximum=[5.,4.,2.])


def validate():
    report=dict(samples=[],controls=[],guards=[])
    # Exact decimal analytic rectangular cross sections, independent of the
    # implementation's oriented-boundary triangulation and floating arithmetic.
    cases=(('Closed inside',.1,None,[],Fraction('4.848')),
        ('Open top inside',.1,None,[dict(axis=2,side=1)],Fraction('3.784')),
        ('Open top outside',None,.075,[dict(axis=2,side=1)],Fraction('3.1254375')),
        ('Open top both',.15,.075,[dict(axis=2,side=1)],Fraction('8.6439375')),
        ('Two opposite openings',.1,None,[dict(axis=2,side=0),dict(axis=2,side=1)],Fraction('2.72')))
    for name,inside,outside,removed,exact in cases:
        before=copy.deepcopy((BOUNDS,removed))
        shape=derive_box_shell(BOUNDS,inside,outside,removed)
        assert (BOUNDS,removed)==before
        assert math.isclose(shape['material_volume_cm3'],float(exact),rel_tol=0.,abs_tol=1e-10)
        assert math.isclose(shape['boundary_integral_volume_cm3'],float(exact),rel_tol=0.,abs_tol=1e-10)
        assert shape['counts']==dict(vertices=16,segments=24,planar_faces=12-len(removed),loops=12,
            connected_boundary_shells=2 if not removed else 1)
        assert sum(f['role']=='rim' for f in shape['planar_boundaries'])==len(removed)
        for face in shape['planar_boundaries']:
            normal=face['outward_material_mathematical_normal']
            assert normal[face['source_axis']] in (-1.,1.) and sum(abs(n) for n in normal)==1.
            assert len(face['loops'])==(2 if face['role']=='rim' else 1)
            for loop in face['loops']:
                assert all(abs(sum(n*x for n,x in zip(normal,p))-face['plane_constant_cm'])<1e-10
                    for p in loop['corner_positions_cm'])
        report['samples'].append(dict(case=name,exact_analytic_volume=str(exact),constructed=shape))
    base=derive_box_shell(BOUNDS,.15,.075,[dict(axis=2,side=1)])
    permutations=((0,1,2),(2,0,1),(1,2,0))
    for order in permutations:
        bounds={key:[v[i] for i in order] for key,v in BOUNDS.items()};axis=order.index(2)
        shape=derive_box_shell(bounds,.15,.075,[dict(axis=axis,side=1)])
        expected={tuple(p['position_cm'][i] for i in order) for p in base['vertices']}
        assert {tuple(p['position_cm']) for p in shape['vertices']}==expected
        assert math.isclose(shape['material_volume_cm3'],8.6439375,abs_tol=1e-10)
        report['controls'].append(dict(case='Axis permutation',new_axis_order=order,whole_point_set_and_volume_agree=True))
    for axis in range(3):
        a=derive_box_shell(BOUNDS,.1,None,[dict(axis=axis,side=0)])
        b=derive_box_shell(BOUNDS,.1,None,[dict(axis=axis,side=1)])
        assert math.isclose(a['material_volume_cm3'],b['material_volume_cm3'],abs_tol=1e-10)
        reflected={tuple(BOUNDS['minimum'][i]+BOUNDS['maximum'][i]-x if i==axis else x
            for i,x in enumerate(p['position_cm'])) for p in a['vertices']}
        assert {tuple(round(x,12) for x in p) for p in reflected}=={tuple(round(x,12) for x in p['position_cm']) for p in b['vertices']}
        report['controls'].append(dict(case='Opposite opening side reflection',axis=axis,whole_point_set_and_volume_agree=True))
    tests=(('No active thickness',copy.deepcopy(BOUNDS),None,None,[]),
        ('Negative inside',copy.deepcopy(BOUNDS),-.1,.2,[]),
        ('Nonfinite thickness',copy.deepcopy(BOUNDS),math.inf,None,[]),
        ('Collapsed cavity',copy.deepcopy(BOUNDS),1.,None,[]),
        ('Duplicate opening',copy.deepcopy(BOUNDS),.1,None,[dict(axis=2,side=1)]*2),
        ('Adjacent openings unqualified',copy.deepcopy(BOUNDS),.1,None,[dict(axis=1,side=1),dict(axis=2,side=1)]),
        ('Invalid opening axis',copy.deepcopy(BOUNDS),.1,None,[dict(axis=3,side=1)]),
        ('Boolean opening axis',copy.deepcopy(BOUNDS),.1,None,[dict(axis=True,side=1)]),
        ('Nonfinite source bound',dict(minimum=[1.,1.,math.nan],maximum=[5.,4.,2.]),.1,None,[]),
        ('Zero source dimension',dict(minimum=[1.,1.,2.],maximum=[5.,4.,2.]),.1,None,[]))
    for name,bounds,inside,outside,removed in tests:
        try:derive_box_shell(bounds,inside,outside,removed)
        except ValueError as error:report['guards'].append(dict(case=name,reason=str(error)))
        else:raise AssertionError(name+' accepted')
    report.update(scope='Pure mathematical rectangular offset material; no native cache ID, UV, history, API or generic Shell-mode claims',
        source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ('decode_shell_box_geometry.py','validate_shell_box_geometry.py')},
        summary=dict(analytic_solids=len(cases),axis_permutations=3,opposite_opening_controls=3,
            malformed_guards=len(tests),main_reader_runs=0,live_calls=0))
    return report


if __name__=='__main__':
    report=validate();(ROOT/'shell-box-geometry-decoding.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['summary'],sort_keys=True))
