"""Analytic solids and rigid-frame checks, without native caches or API calls."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

from decode_circular_extrusion_geometry import derive_circular_extrusion, extrusion_stations

ROOT = Path(__file__).resolve().parent


def controls(distance=3., offset=None, taper=0., mode='OneSided', convention=None, other=2.):
    side = dict(condition='Distance', uninterpreted_flags=0, distance_cm=distance,
        taper_angle_radians=taper)
    extent = dict(mode=mode, side_one=side)
    if convention is not None:
        extent['distance_convention'] = convention
    if mode == 'TwoSided':
        extent['side_two'] = dict(condition='Distance', uninterpreted_flags=0,
            distance_cm=other, taper_angle_radians=0.)
    return dict(operation=dict(kind='NewBody'), is_solid=True,
        stored_second_extent_enabled=0 if mode == 'OneSided' else 1,
        start=dict(kind='ProfilePlane') if offset is None else dict(kind='Offset', offset_cm=offset),
        extent=extent)


def validate():
    checks, guards, samples = [], [], []

    def check(label, condition):
        if not condition:
            raise AssertionError(label)
        checks.append(label)

    def near(a, b):
        return math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-10)

    # Independent endpoint/radius expectations, including both native symmetric
    # conventions. Expected frustum radius is deliberately exactly two.
    cases = [
        ('positive cylinder', controls(), [0., 3.], [2., 2.]),
        ('negative distance', controls(-3.), [-3., 0.], [2., 2.]),
        ('positive start offset', controls(offset=.7), [.7, 3.7], [2., 2.]),
        ('negative start offset', controls(offset=-.9), [-.9, 2.1], [2., 2.]),
        ('negative distance and offset', controls(-3., offset=.7), [-2.3, .7], [2., 2.]),
        ('symmetric full length', controls(mode='Symmetric', convention='FullLength'), [-1.5, 1.5], [2., 2.]),
        ('symmetric half length', controls(mode='Symmetric', convention='HalfLength'), [-3., 3.], [2., 2.]),
        ('two independent sides', controls(mode='TwoSided'), [-2., 3.], [2., 2.]),
        ('expanding frustum', controls(taper=math.atan(1./3.)), [0., 3.], [2., 3.]),
    ]
    axis = [2./3., -1./3., 2./3.]
    u = [1./math.sqrt(5.), 2./math.sqrt(5.), 0.]
    frames = [([0., 0., 0.], [0., 0., 1.], [1., 0., 0.]), ([4., -2., 7.], axis, u)]
    for label, native, interval, radii in cases:
        before = copy.deepcopy(native)
        for frame_index, (center, normal, ref) in enumerate(frames):
            name = label + ' frame ' + str(frame_index)
            result = derive_circular_extrusion(center, normal, ref, 2., native)
            check(name+' signed axial interval', all(near(s['axial_distance_cm'], h)
                for s, h in zip(result['axial_stations'], interval)))
            check(name+' independent end radii', all(near(s['radius_cm'], r)
                for s, r in zip(result['axial_stations'], radii)))
            length = interval[1]-interval[0]
            # Simpson integration of cross-sectional area is exact for a linear
            # radius law. This is independent of the helper's frustum formula.
            expected_volume = length*math.pi/6*(radii[0]**2 + 4*((radii[0]+radii[1])/2)**2 + radii[1]**2)
            check(name+' integrated cross-section volume', near(result['volume_cm3'], expected_volume))
            for side, sign in enumerate((-1, 1)):
                cap = result['mathematical_disk_caps'][side]
                check(name+' outward cap '+str(side), all(near(a, sign*b)
                    for a, b in zip(cap['mathematical_outward_unit_normal'], normal)))
                check(name+' cap plane '+str(side), near(cap['plane_constant_cm'],
                    sign*(sum(a*b for a, b in zip(center, normal))+interval[side])))
            for coordinate in range(3):
                # Support of a disk along each coordinate comes from the normal
                # alone. No helper U/V components supply this reference.
                radial_support = math.sqrt(max(0., 1-normal[coordinate]**2))
                values = [center[coordinate]+h*normal[coordinate]+sign*r*radial_support
                    for h, r in zip(interval, radii) for sign in (-1, 1)]
                bounds = result['component_axis_aligned_bounds_cm']
                check(name+' exact support bounds '+str(coordinate),
                    near(bounds['minimum'][coordinate], min(values)) and near(bounds['maximum'][coordinate], max(values)))
            carrier = result['lateral_carrier']
            # Three independent axial cross sections and four angles satisfy the
            # complete carrier polynomial in component coordinates.
            residuals = []
            v = result['source_circle']['reference_v']
            for fraction in (0., .5, 1.):
                h = interval[0]+fraction*length
                radius = radii[0]+fraction*(radii[1]-radii[0])
                for theta in (0., .7, 2.1, 4.):
                    p = [center[i]+h*normal[i]+radius*(math.cos(theta)*ref[i]+math.sin(theta)*v[i]) for i in range(3)]
                    delta = [p[i]-center[i] for i in range(3)]
                    native_h = sum(a*b for a, b in zip(delta, normal))
                    radial_squared = sum((delta[i]-native_h*normal[i])**2 for i in range(3))
                    residuals.append(abs(radial_squared-(carrier['radial_intercept_cm']+native_h*carrier['radial_slope'])**2))
            check(name+' full implicit carrier samples', max(residuals)<1e-10)
            check(name+' no native entity or UV claims', result['source_to_cache_entity_mapping'] is None
                and carrier['native_FACE_identity'] is None and carrier['native_UV'] is None
                and all(c['native_FACE_identity'] is None and c['native_EDGE_identity'] is None and c['native_UV'] is None
                    for c in result['mathematical_disk_caps']))
            samples.append(dict(name=name, expected_interval_cm=interval, expected_radii_cm=radii,
                independent_integrated_volume_cm3=expected_volume, maximum_carrier_residual=max(residuals), result=result))
        check(label+' caller controls unchanged', native==before)

    def reject(label, native=None, radius=2., normal=None, ref=None):
        try:
            derive_circular_extrusion([0.,0.,0.], normal or [0.,0.,1.], ref or [1.,0.,0.],
                radius, controls() if native is None else native)
        except (ValueError, KeyError, TypeError) as error:
            guards.append(dict(name=label, rejected=True, reason=str(error)))
        else:
            raise AssertionError(label+' accepted')

    reject('zero radius', radius=0.)
    reject('nonfinite radius', radius=float('inf'))
    reject('boolean radius', radius=True)
    reject('nonunit axis', normal=[0.,0.,2.])
    reject('nonorthogonal reference axis', ref=[1.,0.,1.])
    reject('zero cap separation', native=controls(0.))
    reject('nonfinite distance', native=controls(float('nan')))
    reject('negative distance with unobserved taper', native=controls(-3., taper=.1))
    reject('unobserved contracting taper', native=controls(taper=-.1))
    reject('unobserved offset taper', native=controls(offset=.5, taper=.1))
    reject('unobserved symmetric taper', native=controls(mode='Symmetric', convention='FullLength', taper=.1))
    reject('unknown symmetric convention', native=controls(mode='Symmetric', convention='Unknown'))
    reject('negative side-two distance', native=controls(mode='TwoSided', other=-2.))
    changed=controls();changed['stored_second_extent_enabled']=1
    reject('inconsistent side enable', native=changed)
    changed=controls();changed['is_solid']=False
    reject('surface operation', native=changed)
    changed=controls();del changed['is_solid']
    reject('missing solid qualification', native=changed)
    changed=controls();changed['extent']['side_one']['condition']='ThroughAll'
    reject('selected or unbounded end condition', native=changed)
    changed=controls();changed['operation']['kind']='Cut'
    reject('Boolean operation', native=changed)
    check('radius-free stations preserve signed interval',
        [s['axial_distance_cm'] for s in extrusion_stations(controls(-3., offset=.7))]==[-2.3,.7])
    return dict(scope='Pure analytic solids and rigid-frame checks; no main, native cache or live API calls',
        check_count=len(checks), checks=checks, guard_count=len(guards), guards=guards, samples=samples,
        source_sha256=hashlib.sha256((ROOT/'decode_circular_extrusion_geometry.py').read_bytes()).hexdigest())


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT/'circular-extrusion-geometry-decoding.json')
    args=parser.parse_args()
    report=validate()
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:report[k] for k in ('check_count','guard_count','source_sha256')}))
