"""Analytic rotational solids and source-axis reversal/rigid-frame invariance."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

from decode_revolve_geometry import derive_revolve_geometry

ROOT=Path(__file__).resolve().parent
IDENTITY=[1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.]
PLACED=[1.,0.,0.,4.,0.,0.,-1.,-2.,0.,1.,0.,7.,0.,0.,0.,1.]


def controls(angle=math.pi/2,mode='OneSided',against=None):
    revolve=dict(mode=mode,extent_kind='Angle',angle_radians=angle)
    if against is not None:revolve['against_angle_radians']=against
    return dict(operation=dict(kind='NewBody'),is_solid=True,is_project_axis=False,revolve=revolve)


def validate():
    checks,guards,samples=[],[],[]
    def check(label,value):
        if not value:raise AssertionError(label)
        checks.append(label)
    def near(a,b):return math.isclose(a,b,rel_tol=0.,abs_tol=1e-9)
    rectangle=dict(kind='Polygon',points_cm=[[1.,0.,0.],[2.,0.,0.],[2.,3.,0.],[1.,3.,0.]])
    axis=dict(origin_cm=[0.,0.,0.],direction=[0.,1.,0.]);pi=math.pi
    cases=[('positive quarter',rectangle,controls(),axis,IDENTITY,9*pi/4,6*pi+6,[[0.,0.,0.],[2.,3.,2.]],6,6),
        ('negative quarter',rectangle,controls(-pi/2),axis,IDENTITY,9*pi/4,6*pi+6,[[0.,0.,-2.],[2.,3.,0.]],6,6),
        ('symmetric sixty per side',rectangle,controls(pi/3,'Symmetric',pi/3),axis,IDENTITY,3*pi,8*pi+6,[[.5,0.,-math.sqrt(3.)],[2.,3.,math.sqrt(3.)]],6,6),
        ('independent two sides',rectangle,controls(pi/3,'TwoSided',pi/6),axis,IDENTITY,9*pi/4,6*pi+6,[[.5,0.,-1.],[2.,3.,math.sqrt(3.)]],6,6),
        ('full annular cylinder',rectangle,controls(2*pi),axis,IDENTITY,9*pi,24*pi,[[-2.,0.,-2.],[2.,3.,2.]],4,8)]
    xrectangle=dict(kind='Polygon',points_cm=[[0.,1.,0.],[3.,1.,0.],[3.,2.,0.],[0.,2.,0.]])
    cases.append(('positive X axis',xrectangle,controls(),dict(origin_cm=[0.,0.,0.],direction=[1.,0.,0.]),IDENTITY,
        9*pi/4,6*pi+6,[[0.,0.,0.],[3.,2.,2.]],6,6))
    cases.append(('rigid placed quarter',rectangle,controls(),dict(origin_cm=[4.,-2.,7.],direction=[0.,0.,1.]),PLACED,
        9*pi/4,6*pi+6,[[4.,-4.,7.],[6.,-2.,10.]],6,6))
    sphere=dict(kind='Semicircle',center_cm=[0.,0.,0.],radius_cm=2.,normal=[0.,0.,1.],reference_axis=[0.,1.,0.],
        angle_interval_radians=[0.,pi],diameter_start_cm=[0.,2.,0.],diameter_end_cm=[0.,-2.,0.])
    cases.append(('full sphere',sphere,controls(2*pi),axis,IDENTITY,32*pi/3,16*pi,[[-2.,-2.,-2.],[2.,2.,2.]],1,0))
    torus=dict(kind='Circle',center_cm=[4.,0.,0.],radius_cm=.75,normal=[0.,0.,1.],reference_axis=[1.,0.,0.])
    cases.append(('full ring torus',torus,controls(2*pi),axis,IDENTITY,4.5*pi*pi,12*pi*pi,[[-4.75,-.75,-4.75],[4.75,.75,4.75]],1,0))
    cone=dict(kind='Polygon',points_cm=[[0.,0.,0.],[2.,0.,0.],[0.,3.,0.]])
    cases.append(('full cone with singular apex',cone,controls(2*pi),axis,IDENTITY,4*pi,4*pi+2*pi*math.sqrt(13.),[[-2.,0.,-2.],[2.,3.,2.]],2,3))
    for name,profile,native,selected,matrix,volume,area,bounds,face_count,loop_count in cases:
        before=copy.deepcopy((profile,native,selected,matrix))
        result=derive_revolve_geometry(profile,matrix,selected,native)
        check(name+' independent volume',near(result['volume_cm3'],volume))
        check(name+' independent surface area',near(result['surface_area_cm2'],area))
        actual=result['component_axis_aligned_bounds_cm']
        check(name+' independently known bounds',all(near(x,y) for a,b in zip(bounds,(actual['minimum'],actual['maximum'])) for x,y in zip(a,b)))
        check(name+' complete mathematical face/loop inventory',len(result['faces'])==face_count and sum(len(f['boundary_loops']) for f in result['faces'])==loop_count)
        check(name+' native operands untouched',(profile,native,selected,matrix)==before)
        check(name+' no native topology or UV claims',result['source_to_cache_entity_mapping'] is None and result['native_UV'] is None
            and all(f['native_FACE_identity'] is None for f in result['faces']))
        if profile['kind']=='Polygon':
            # Pappus' radial moment is checked through an independently known
            # cross section for all rectangular solids and the cone triangle.
            expected_moment=2. if name.startswith('full cone') else 4.5
            check(name+' independent radial first moment',near(result['meridian_profile']['radial_first_moment_cm3'],expected_moment))
        samples.append(dict(name=name,independent_volume_cm3=volume,independent_surface_area_cm2=area,
            independent_bounds_cm=bounds,result=result))
    forward=derive_revolve_geometry(rectangle,IDENTITY,axis,controls())
    reversed_axis=copy.deepcopy(axis);reversed_axis['direction']=[0.,-1.,0.]
    reverse=derive_revolve_geometry(rectangle,IDENTITY,reversed_axis,controls())
    check('Selected-axis reversal preserves physical construction',forward['faces']==reverse['faces']
        and forward['component_axis_aligned_bounds_cm']==reverse['component_axis_aligned_bounds_cm'])
    check('Stored selected-axis direction remains distinct',forward['source_axis']!=reverse['source_axis']
        and forward['effective_axis']['direction']==reverse['effective_axis']['direction']
        and forward['effective_axis']['stored_direction_multiplier']==-reverse['effective_axis']['stored_direction_multiplier'])
    negative_full=derive_revolve_geometry(rectangle,IDENTITY,axis,controls(-2*pi))
    positive_full=next(s['result'] for s in samples if s['name']=='full annular cylinder')
    check('Negative full turn preserves bounded solid',near(negative_full['volume_cm3'],positive_full['volume_cm3'])
        and negative_full['component_axis_aligned_bounds_cm']==positive_full['component_axis_aligned_bounds_cm'])

    def reject(label,profile=None,matrix=None,selected=None,native=None):
        try:derive_revolve_geometry(rectangle if profile is None else profile,IDENTITY if matrix is None else matrix,
            axis if selected is None else selected,controls() if native is None else native)
        except (ValueError,KeyError,TypeError) as error:guards.append(dict(name=label,rejected=True,reason=str(error)))
        else:raise AssertionError(label+' accepted')
    reject('Zero angular span',native=controls(0.))
    reject('More than one angular turn',native=controls(2*pi+.1))
    reject('Unverified negative symmetric angles',native=controls(-pi/3,'Symmetric',-pi/3))
    wrong=controls();wrong['is_project_axis']=True;reject('Projected axis',native=wrong)
    wrong=controls();wrong['is_solid']=False;reject('Surface Revolve',native=wrong)
    wrong=controls();wrong['operation']['kind']='Cut';reject('Boolean Revolve',native=wrong)
    wrong=controls();wrong['revolve']['extent_kind']='ToEntity';reject('Unresolved entity angular limit',native=wrong)
    reject('Selected axis outside Sketch plane',selected=dict(origin_cm=[0.,0.,.1],direction=[0.,1.,0.]))
    reject('Selected axis not parallel Sketch plane',selected=dict(origin_cm=[0.,0.,0.],direction=[0.,.8,.6]))
    reject('Profile crosses both radial sides',profile=dict(kind='Polygon',points_cm=[[-1.,0.,0.],[1.,0.,0.],[1.,3.,0.],[-1.,3.,0.]]))
    reject('Self-crossing source polygon',profile=dict(kind='Polygon',points_cm=[[1.,0.,0.],[2.,3.,0.],[1.,3.,0.],[2.,0.,0.]]))
    wrong=copy.deepcopy(torus);wrong['center_cm']=[.5,0.,0.];reject('Horn/spindle torus outside captured family',profile=wrong,native=controls(2*pi))
    reject('Unqualified partial circular profile',profile=torus)
    wrong=copy.deepcopy(sphere);wrong['angle_interval_radians'][1]-=.1;reject('Non-semicircle sphere source',profile=wrong,native=controls(2*pi))
    wrong=IDENTITY[:];wrong[0]=2.;reject('Nonrigid Sketch frame',matrix=wrong)
    reject('Nonfinite angle',native=controls(float('nan')))
    return dict(scope='Ten analytic rotational solids, explicit axis reversal and full-turn sign invariance; no native/result cache/main/live API inputs',
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('decode_revolve_geometry.py','validate_revolve_geometry.py')},
        check_count=len(checks),checks=checks,guard_count=len(guards),guards=guards,samples=samples)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'revolve-geometry-decoding.json');args=p.parse_args()
    report=validate();args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({key:report[key] for key in ('check_count','guard_count')}))
