"""Typed boundary-locus proof for the observed noncircular Loft cone."""

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

from asm_records import inspect_asm
from decode_analytic import decode_analytic_surface
from decode_brep import decode_topology
from decode_elliptic_cone import decode_elliptic_cone, elliptic_cone_locus_residual, dot, cross
from fusion_archive import read_members

ROOT = Path(__file__).resolve().parent
FILE = 'moretools-88a2cd6cad0b/Loft.f3d'


def curve_vectors(curve):
    center, major = curve['raw_origin'], curve['stored_reference_axis']
    radius = math.hypot(*major)
    minor_unit = cross(curve['normal'], [x/radius for x in major])
    minor = [curve['raw_minor_radius']*x for x in minor_unit]
    return center, major, minor


def harmonic_residual_coefficients(geometry, curve):
    """Expand the entire stored ellipse curve into the quadric analytically.

    Its exact trigonometric residual has only1,cos(t),sin(t),cos(2t),sin(2t)
    coefficients. Vanishing coefficients corroborate the whole boundary locus,
    rather than selecting a few matching points or guessing surface parameters.
    """
    center, major, minor = curve_vectors(curve)
    delta = [x-y for x, y in zip(center, geometry['raw_origin'])]
    locus = geometry['geometric_locus']; e, f = locus['major_basis_unit'], locus['minor_basis_unit']
    a, b, rate = geometry['raw_major_radius'], geometry['raw_minor_radius'], locus['axial_relative_radius_rate']
    p = [dot(v, e)/a for v in (delta, major, minor)]
    q = [dot(v, f)/b for v in (delta, major, minor)]
    r = [1+rate*dot(delta, geometry['axis']), rate*dot(major, geometry['axis']), rate*dot(minor, geometry['axis'])]
    square_cos = p[1]**2+q[1]**2-r[1]**2
    square_sin = p[2]**2+q[2]**2-r[2]**2
    return {'constant': p[0]**2+q[0]**2-r[0]**2+.5*(square_cos+square_sin),
            'cos_t': 2*(p[0]*p[1]+q[0]*q[1]-r[0]*r[1]),
            'sin_t': 2*(p[0]*p[2]+q[0]*q[2]-r[0]*r[2]),
            'cos_2t': .5*(square_cos-square_sin),
            'sin_2t': p[1]*p[2]+q[1]*q[2]-r[1]*r[2]}


def validate(zstd_library):
    truth = json.loads((ROOT / 'moretools-88a2cd6cad0b/ground_truth.json').read_text())
    actual = next(s for s in truth['samples'] if s['file'] == 'Loft.f3d')
    report = {'scope': 'Two copies of one observed elliptic cone in Loft.f3d; explicit noncircular geometry with boundary-qualified implicit locus, no native UV evaluator',
              'integration': {'helper': 'decode_elliptic_cone.decode_elliptic_cone(record)',
                              'hook': 'Root may dispatch cone-surface with nonunit axis ratio after the old circular branch rejects, preserving all circular defaults.',
                              'geometry_kind': 'EllipticCone', 'expected_dictionary_field': 'records[].geometry',
                              'validation_command': '/usr/bin/python3 validate_elliptic_cone.py', 'shared_edits_by_this_task': False},
              'actual_api_context': {'fusion_version': truth['fusion_version'], 'file': FILE, 'feature_kind': actual['kind'],
                                     'settings': actual['settings'], 'body_count': actual['body_count'],
                                     'surface_evaluator_getters_captured': False},
              'file': FILE, 'records': [], 'circular_controls': [], 'guards': [],
              'limitations': ['Only the observed noncircular, positive-cosine, nonzero-slope layout with physical major radius matching stored parameter scale is qualified.',
                              'The separate parameter scale and major radius are indistinguishable numerically here; differing-scale elliptic cones remain unsupported.',
                              'The signed pair defines the tested geometric axial-scale rate in this bounded case; no native UV sign, half-angle, circular-cone label or parameter-to-angle formula is assigned.',
                              'Harmonic coefficients establish the stored boundary curves lie on the candidate quadric within floating precision. This does not reconstruct trimmed-face topology, establish final visible lifecycle or compare an API surface evaluator.',
                              'Raw ellipse axes/radii and the native signed pair remain literal. Assembly placement, exact regeneration and native file writing are outside scope.']}
    sources = []; all_residuals = []; coefficients = []; counterexamples = []
    for member, raw in read_members(ROOT / FILE, zstd_library).items():
        if not member.endswith(('.smb', '.smbh')):
            continue
        parsed = inspect_asm(raw); assert parsed['complete_token_stream']
        nodes = {n['index']: n for n in decode_topology(parsed)['nodes']}
        index = 18 if member.endswith('.smbh') else 45
        source = parsed['records'][index]; geometry = decode_elliptic_cone(source); sources.append(source)
        assert geometry['kind'] == 'EllipticCone' and not any('half_angle' in key for key in geometry)
        assert math.isclose(geometry['raw_minor_radius']/geometry['raw_major_radius'], source['tokens'][6]['value'], abs_tol=1e-15)
        parent_faces = [f for f in nodes.values() if f['kind'] == 'face' and f['surface_index'] == index]
        face, = parent_faces
        sample = {'file': FILE, 'member': member, 'record_index': index, 'geometry': geometry,
                  'parent_face_index': face['index'], 'boundary_curves': []}
        for coedge in nodes.values():
            if coedge['kind'] != 'coedge' or nodes[coedge['loop_index']]['face_index'] != face['index']:
                continue
            loop = nodes[coedge['loop_index']]; edge = nodes[coedge['edge_index']]; curve = nodes[edge['curve_index']]
            assert loop['kind'] == 'loop' and edge['kind'] == 'edge' and curve['kind'] == 'ellipse-curve'
            harmonic = harmonic_residual_coefficients(geometry, curve); coefficients.extend(harmonic.values())
            assert max(abs(v) for v in harmonic.values()) < 1e-12
            center, major, minor = curve_vectors(curve)
            points = [[center[j]+math.cos(i*math.pi/4)*major[j]+math.sin(i*math.pi/4)*minor[j] for j in range(3)] for i in range(8)]
            residuals = [elliptic_cone_locus_residual(geometry, p) for p in points]; all_residuals.extend(residuals)
            assert max(abs(v) for v in residuals) < 1e-12
            wrong_sign = copy.deepcopy(geometry)
            wrong_sign['geometric_locus']['axial_relative_radius_rate'] *= -1
            circular = copy.deepcopy(geometry); circular['raw_minor_radius'] = circular['raw_major_radius']
            sign_error = max(abs(elliptic_cone_locus_residual(wrong_sign, p)) for p in points)
            circular_error = max(abs(elliptic_cone_locus_residual(circular, p)) for p in points)
            assert sign_error > 1e-3 and circular_error > 1e-3
            counterexamples.append([sign_error, circular_error])
            endpoint_checks = []
            for name in ('start_vertex_index', 'end_vertex_index'):
                vertex = nodes[edge[name]]; point = nodes[vertex['point_index']]
                assert vertex['kind'] == 'vertex' and point['kind'] == 'point'
                residual = elliptic_cone_locus_residual(geometry, point['raw_origin'])
                assert abs(residual) < 1e-12
                endpoint_checks.append({'vertex_index': vertex['index'], 'point_index': point['index'],
                                        'raw_point': point['raw_origin'], 'dimensionless_locus_residual': residual})
            sample['boundary_curves'].append({'coedge_index': coedge['index'], 'loop_index': loop['index'],
                'edge_index': edge['index'], 'curve_index': curve['index'], 'explicit_curve_geometry': curve,
                'entire_curve_harmonic_residual_coefficients': harmonic, 'eight_sample_residuals': residuals,
                'native_endpoint_checks': endpoint_checks,
                'reversed_rate_counterexample_max_residual': sign_error,
                'falsely_circular_counterexample_max_residual': circular_error})
        assert len(sample['boundary_curves']) == 2
        report['records'].append(sample)
    # Capture dictionaries from the untouched circular reader, and independently
    # show that the new noncircular helper refuses those same inputs.
    for relative, desired_kind in [('analytic-86a12b291d0a/analytic.f3d', 'Cone'),
                                   ('holes-926347c1eaa8/simple.f3d', 'Cylinder')]:
        chosen = None
        for member, raw in read_members(ROOT / relative, zstd_library).items():
            if not member.endswith(('.smb', '.smbh')):
                continue
            for source in inspect_asm(raw)['records']:
                if source['name'] != 'cone-surface' or source['section'] != 'geometry':
                    continue
                try:
                    expected = decode_analytic_surface(source)
                except ValueError:
                    continue
                if expected['kind'] == desired_kind:
                    chosen = member, source, expected; break
            if chosen:
                break
        assert chosen
        member, source, expected = chosen
        try:
            decode_elliptic_cone(source)
        except ValueError:
            pass
        else:
            raise AssertionError('Circular control accepted by elliptic helper')
        assert decode_analytic_surface(source) == expected
        report['circular_controls'].append({'file': relative, 'member': member, 'record_index': source['index'],
                                            'kind': desired_kind, 'expected_geometry': expected,
                                            'dictionary_sha256': hashlib.sha256(json.dumps(expected, sort_keys=True).encode()).hexdigest(),
                                            'new_helper_rejects_circular': True})
    def reject(label, mutate):
        source = copy.deepcopy(sources[0]); mutate(source['tokens'])
        try:
            decode_elliptic_cone(source)
        except (ValueError, IndexError) as error:
            report['guards'].append({'case': label, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError('Malformed elliptic cone accepted: '+label)
    reject('Non-unit axis', lambda t: t[4].update(value=[1., 1., 1.]))
    reject('Reference parallel to cone axis', lambda t: t[5].update(value=t[4]['value']))
    reject('Invalid ellipse ratio', lambda t: t[6].update(value=-.5))
    reject('Invalid signed angular pair', lambda t: t[9].update(value=.5))
    reject('Unqualified differing parameter scale', lambda t: t[11].update(value=2.))
    report['summary'] = {'saved_files': 1, 'elliptic_cone_records': len(report['records']),
                         'typed_parent_boundary_curves': sum(len(s['boundary_curves']) for s in report['records']),
                         'entire_boundary_harmonic_coefficients_checked': len(coefficients),
                         'maximum_absolute_harmonic_coefficient': max(abs(v) for v in coefficients),
                         'boundary_curve_sample_points': len(all_residuals),
                         'maximum_absolute_dimensionless_locus_residual': max(abs(v) for v in all_residuals),
                         'native_endpoint_occurrences': sum(len(b['native_endpoint_checks']) for s in report['records'] for b in s['boundary_curves']),
                         'wrong_sign_and_circular_counterexamples': len(counterexamples)*2,
                         'circular_controls_preserved': len(report['circular_controls']), 'malformed_guards': len(report['guards'])}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='elliptic-cone-decoding.json')
    args = parser.parse_args()
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    report = validate(str(zstd))
    Path(args.output).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], sort_keys=True))
