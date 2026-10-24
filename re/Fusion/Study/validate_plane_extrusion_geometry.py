"""Focused plane/axis algebra and rigid-frame invariance; no native/API calls."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

from decode_plane_extrusion_geometry import derive_plane_limited_circular_extrusion

ROOT=Path(__file__).resolve().parent


def controls(kind='ToEntity',offset=0.):
    return dict(operation=dict(kind='NewBody'),is_solid=True,stored_second_extent_enabled=0,
        start=dict(kind='ProfilePlane') if kind=='ToEntity' else dict(kind='FromEntity',offset_cm=offset),
        extent=dict(mode='OneSided',side_one=dict(condition='ToEntity',uninterpreted_flags=1,taper_angle_radians=0.,offset_cm=offset)
            if kind=='ToEntity' else dict(condition='Distance',uninterpreted_flags=0,taper_angle_radians=0.,distance_cm=1.7)))


def validate():
    checks,guards,samples=[],[],[]
    def check(label,condition):
        if not condition:raise AssertionError(label)
        checks.append(label)
    def near(a,b):return math.isclose(a,b,rel_tol=0.,abs_tol=1e-10)
    frames=[([0.,0.,0.],[0.,0.,1.],[1.,0.,0.]),
        ([4.,-2.,7.],[2./3.,-1./3.,2./3.],[1./math.sqrt(5.),2./math.sqrt(5.),0.])]
    cases=[('ToEntity',0.,[0.,3.]),('ToEntity',.4,[0.,3.4]),('FromEntity',.5,[3.5,5.2])]
    for kind,offset,expected in cases:
        for frame,(center,axis,u) in enumerate(frames):
            name=kind+' offset '+str(offset)+' frame '+str(frame)
            native=controls(kind,offset);role='side_one' if kind=='ToEntity' else 'start'
            # Add an in-plane displacement: the limit must come from the plane
            # equation, not the distance to its stored origin.
            plane=dict(origin_cm=[c+3*n+2*a for c,n,a in zip(center,axis,u)],normal=axis[:])
            operands=copy.deepcopy((center,axis,u,native,plane))
            result=derive_plane_limited_circular_extrusion(center,axis,u,1.25,native,{role:plane})
            derivation=result['plane_limit_derivation']
            check(name+' line-plane intersection',near(derivation['selected_plane_intersection_distance_cm'],3.))
            check(name+' signed limit interval',all(near(a,b) for a,b in zip(derivation['derived_axial_interval_cm'],expected)))
            for end,height in enumerate(expected):
                check(name+' cap centre '+str(end),all(near(a,c+height*n)
                    for a,c,n in zip(result['axial_stations'][end]['center_cm'],center,axis)))
            volume=math.pi*1.25**2*(expected[1]-expected[0])
            check(name+' cylinder volume',near(result['volume_cm3'],volume))
            check(name+' original native controls retained',(center,axis,u,native,plane)==operands)
            check(name+' equivalent mathematical controls labeled',
                derivation['mathematical_equivalent_controls_are_native_records'] is False
                and derivation['native_start_kind']==native['start']['kind']
                and derivation['native_end_kind']==native['extent']['side_one']['condition'])
            samples.append(dict(name=name,expected_interval_cm=expected,independent_volume_cm3=volume,result=result))

    def reject(label,native=None,plane=None,role='side_one'):
        try:
            derive_plane_limited_circular_extrusion([0.,0.,0.],[0.,0.,1.],[1.,0.,0.],1.,
                controls() if native is None else native,{role:dict(origin_cm=[0.,0.,3.],normal=[0.,0.,1.]) if plane is None else plane})
        except (ValueError,KeyError,TypeError) as error:
            guards.append(dict(name=label,rejected=True,reason=str(error)))
        else:raise AssertionError(label+' accepted')
    reject('reversed plane normal',plane=dict(origin_cm=[0.,0.,3.],normal=[0.,0.,-1.]))
    angle=1e-5
    reject('small oblique normal passes dot-only tolerance but fails vector coefficients',
        plane=dict(origin_cm=[0.,0.,3.],normal=[math.sin(angle),0.,math.cos(angle)]))
    reject('nonfinite selected plane',plane=dict(origin_cm=[0.,0.,float('nan')],normal=[0.,0.,1.]))
    reject('target lies on profile plane',plane=dict(origin_cm=[2.,0.,0.],normal=[0.,0.,1.]))
    reject('target behind profile plane',plane=dict(origin_cm=[0.,0.,-3.],normal=[0.,0.,1.]))
    reject('unverified negative ToEntity offset',native=controls(offset=-.4))
    reject('unverified negative FromEntity offset',native=controls('FromEntity',-.5),role='start')
    reject('nonfinite selected offset',native=controls(offset=float('inf')))
    changed=controls();changed['extent']['side_one']['uninterpreted_flags']=0
    reject('unobserved selected limit flags',native=changed)
    changed=controls();changed['extent']['side_one']['taper_angle_radians']=.1
    reject('unverified selected limit taper',native=changed)
    changed=controls();changed['extent']['mode']='TwoSided';changed['stored_second_extent_enabled']=1
    reject('unverified two-sided selected limits',native=changed)
    changed=controls('FromEntity',.5);changed['extent']['side_one']['distance_cm']=-1.7
    reject('unverified negative FromEntity distance',native=changed,role='start')
    changed=controls();changed['is_solid']=False
    reject('surface extrusion',native=changed)
    changed=controls();changed['operation']['kind']='Cut'
    reject('Boolean operation',native=changed)
    reject('selected operand role mismatch',role='start')
    files=('decode_plane_extrusion_geometry.py','decode_circular_extrusion_geometry.py','validate_plane_extrusion_geometry.py')
    return dict(scope='Six analytic selected-plane cylinders, including rigid-frame and in-plane-origin invariance; no main/native cache/live API calls',
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files},
        check_count=len(checks),checks=checks,guard_count=len(guards),guards=guards,samples=samples)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'plane-extrusion-geometry-decoding.json')
    args=parser.parse_args();report=validate()
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({key:report[key] for key in ('check_count','guard_count')}))
