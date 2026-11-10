"""Independent analytic areas, perimeters, bounds and malformed source loops."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

from decode_trimmed_extrusion_geometry import derive_trimmed_extrusion
from validate_circular_extrusion_geometry import controls

ROOT=Path(__file__).resolve().parent
IDENTITY=[1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.]
PLACED=[1.,0.,0.,4.,0.,0.,-1.,-2.,0.,1.,0.,7.,0.,0.,0.,1.]


def arc(role,identity,center,a,b):
    return dict(role_key=role,source_primitive_id=identity,kind='CircleArc',
        source_geometry=dict(center_cm=center,radius_cm=1.,normal=[0.,0.,1.],reference_axis=[1.,0.,0.]),
        parameter_interval=[a,b])


def line(role,identity,start,end):
    return dict(role_key=role,source_primitive_id=identity,kind='LineSegment',
        source_geometry=dict(start_cm=start,end_cm=end),parameter_interval=[0.,1.])


def validate():
    checks,guards,samples=[],[],[]
    def check(label,value):
        if not value:raise AssertionError(label)
        checks.append(label)
    def near(a,b):return math.isclose(a,b,rel_tol=0.,abs_tol=1e-9)
    pi=math.pi;sqrt3=math.sqrt(3.)
    lens=[arc('a',1,[-.5,0.,0.],5*pi/3,7*pi/3),arc('b',2,[.5,0.,0.],2*pi/3,4*pi/3)]
    split=[arc('a0',1,[-.5,0.,0.],5*pi/3,2*pi),arc('a1',1,[-.5,0.,0.],2*pi,7*pi/3),
        arc('b0',2,[.5,0.,0.],2*pi/3,pi),arc('b1',2,[.5,0.,0.],pi,4*pi/3)]
    crescent=[lens[0],arc('b',2,[.5,0.,0.],4*pi/3,8*pi/3)]
    chord=sqrt3/2
    segment=[arc('arc',1,[0.,0.,0.],pi/6,5*pi/6),line('chord',2,[-chord,.5,0.],[chord,.5,0.])]
    rectangle=[line(str(i),i+1,a,b) for i,(a,b) in enumerate(zip(
        ([0.,0.,0.],[2.,0.,0.],[2.,3.,0.],[0.,3.,0.]),
        ([2.,0.,0.],[2.,3.,0.],[0.,3.,0.],[0.,0.,0.])))]
    lens_area=2*pi/3-sqrt3/2
    cases=[('lens',lens,lens_area,4*pi/3,[-.5,-chord],[.5,chord]),
        ('repeated Circle split lens',split,lens_area,4*pi/3,[-.5,-chord],[.5,chord]),
        ('concave crescent',crescent,pi-lens_area,2*pi,[0.,-1.],[1.5,1.]),
        ('mixed circular segment',segment,pi/3-sqrt3/4,2*pi/3+sqrt3,[-chord,.5],[chord,1.]),
        ('rectangle',rectangle,6.,10.,[0.,0.],[2.,3.])]
    native=controls(distance=2.,offset=-.7)
    for name,portions,area,perimeter,minimum,maximum in cases:
        for placed,matrix in enumerate((IDENTITY,PLACED)):
            label=name+' frame '+str(placed);before=copy.deepcopy((portions,matrix,native))
            result=derive_trimmed_extrusion(portions,matrix,native)
            check(label+' independently known area',near(result['profile']['area_cm2'],area))
            check(label+' independently known perimeter',near(result['profile']['perimeter_cm'],perimeter))
            check(label+' exact volume',near(result['volume_cm3'],2*area))
            check(label+' exact material areas',near(result['lateral_area_cm2'],2*perimeter)
                and near(result['total_area_cm2'],2*perimeter+2*area))
            bounds=([minimum+[-.7],maximum+[1.3]] if not placed else
                [[4+minimum[0],-3.3,7+minimum[1]],[4+maximum[0],-1.3,7+maximum[1]]])
            actual=result['component_axis_aligned_bounds_cm']
            check(label+' exact arc extrema and station bounds',all(near(x,y) for a,b in zip(bounds,(actual['minimum'],actual['maximum'])) for x,y in zip(a,b)))
            check(label+' original source operands unchanged',(portions,matrix,native)==before)
            check(label+' complete source role coverage',len(result['boundary_curves'])==len(portions)
                and {p['role_key'] for p in portions}=={p['role_key'] for p in result['profile']['mathematical_positive_boundary_cycle']})
            check(label+' no native topology assignments',result['source_to_cache_entity_mapping'] is None
                and all(r['native_ENTITY_identity'] is None and r['native_UV'] is None for r in result['boundary_curves']))
            samples.append(dict(name=label,independent_area_cm2=area,independent_perimeter_cm=perimeter,independent_bounds_cm=bounds,result=result))
    # Membership order is deliberately not treated as traversal order.
    permuted=derive_trimmed_extrusion(list(reversed(split)),IDENTITY,native)
    check('Source membership permutation preserves area/volume',near(permuted['profile']['area_cm2'],lens_area) and near(permuted['volume_cm3'],2*lens_area))

    def reject(label,parts=None,matrix=None,settings=None):
        try:derive_trimmed_extrusion(lens if parts is None else parts,IDENTITY if matrix is None else matrix,native if settings is None else settings)
        except (ValueError,KeyError,TypeError) as error:guards.append(dict(name=label,rejected=True,reason=str(error)))
        else:raise AssertionError(label+' accepted')
    wrong=copy.deepcopy(lens);wrong[1]['role_key']='a';reject('Duplicate full portion role',parts=wrong)
    wrong=copy.deepcopy(lens);wrong[0]['source_geometry']['radius_cm']=0.;reject('Nonpositive source radius',parts=wrong)
    wrong=copy.deepcopy(lens);wrong[0]['parameter_interval']=[0.,2*pi];reject('Whole Circle masquerading as bounded portion',parts=wrong)
    wrong=copy.deepcopy(lens);wrong[0]['parameter_interval']=[0.,float('nan')];reject('Nonfinite source interval',parts=wrong)
    wrong=copy.deepcopy(split);wrong[1]['source_geometry']['radius_cm']=1.2;reject('Inconsistent repeated native source',parts=wrong)
    wrong=copy.deepcopy(rectangle);wrong[0]['source_geometry']['start_cm'][0]=.1;reject('Open source boundary',parts=wrong)
    points=[[0.,0.,0.],[2.,2.,0.],[0.,2.,0.],[2.,0.,0.]]
    bowtie=[line(str(i),i+1,points[i],points[(i+1)%4]) for i in range(4)]
    reject('Self-crossing closed boundary',parts=bowtie)
    disjoint=[arc('a0',1,[0.,0.,0.],0.,pi),arc('a1',1,[0.,0.,0.],pi,2*pi),
        arc('b0',2,[4.,0.,0.],0.,pi),arc('b1',2,[4.,0.,0.],pi,2*pi)]
    reject('Two disconnected source cycles',parts=disjoint)
    wrong=IDENTITY[:];wrong[0]=2.;reject('Nonrigid source frame',matrix=wrong)
    wrong=copy.deepcopy(native);wrong['extent']['side_one']['taper_angle_radians']=.1
    reject('Unsupported profile taper',settings=wrong)
    wrong=copy.deepcopy(lens);wrong[0]['source_geometry']['center_cm'][0]=float('inf');reject('Nonfinite source primitive',parts=wrong)
    return dict(scope='Ten analytic simple profile extrusions in two rigid frames; membership permutation and malformed/simple-loop guards, zero main/cache/live inputs',
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in (
            'decode_trimmed_extrusion_geometry.py','decode_circular_extrusion_geometry.py','validate_trimmed_extrusion_geometry.py')},
        check_count=len(checks),checks=checks,guard_count=len(guards),guards=guards,samples=samples)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'trimmed-extrusion-geometry-decoding.json');args=p.parse_args()
    report=validate();args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({key:report[key] for key in ('check_count','guard_count')}))
