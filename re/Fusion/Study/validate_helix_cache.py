"""Focused encoded helix endpoint/UV checks against saved modeled threads."""

import argparse
import copy
import json
import math
from pathlib import Path

from asm_records import inspect_asm
from decode_brep import decode_topology
from decode_bspline import decode_bspline
from decode_helix_cache import decode_helix_cache, evaluate_helix_curve, evaluate_helix_surface
from decode_pcurve import evaluate_pcurve
from fusion_archive import read_members

FILES = ('tappedholes-409e96788503/modeled_full.f3d', 'threadmodes-d51d2ae60564/modeled_full.f3d')


def distance(a, b):
    return math.sqrt(sum((x-y)**2 for x, y in zip(a, b)))


def validate(root, zstd):
    checks, samples, counts, curve_errors, surface_errors, saved = 0, [], {}, [], [], []

    def check(test, reason):
        nonlocal checks
        if not test:
            raise AssertionError(reason)
        checks += 1

    for file in FILES:
        truth = json.loads((root/Path(file).parent/'ground_truth.json').read_text())
        api = next(s['settings'] for s in truth['samples'] if s['file'] == 'modeled_full.f3d')
        check(api['is_modeled'], 'saved API actual settings say modeled thread')
        members = read_members(root/file, zstd)
        member, blob = next((m, b) for m, b in members.items() if m.endswith('.smbh'))
        parsed = inspect_asm(blob)
        records = parsed['records']
        nodes = {n['index']: n for n in decode_topology(parsed)['nodes']}
        geometries = {}
        for r in records:
            if r['section'] != 'geometry' or len(r['tokens']) < 6 or r['tokens'][5]['value'] not in ('helix_int_cur', 'helix_spl_line'):
                continue
            before = copy.deepcopy(r)
            cache = decode_helix_cache(r)
            check(r == before, 'helix reader does not modify original typed tokens')
            check(not any(k in cache for k in ('degree', 'knots', 'raw_control_points', 'control_count_u')),
                  'encoded geometry does not fabricate spline control-grid fields')
            geometries[r['index']] = cache
            if 'encoded_curve_kind' in cache:
                counts['curves'] = counts.get('curves', 0)+1
            else:
                counts['surfaces'] = counts.get('surfaces', 0)+1
            saved.append(r)
        curve_checks = []
        for edge in nodes.values():
            if edge['kind'] != 'edge' or edge['curve_index'] not in geometries:
                continue
            cache = geometries[edge['curve_index']]
            if 'encoded_curve_kind' not in cache:
                continue
            endpoint_checks = []
            for end in ('start', 'end'):
                vertex = nodes[edge[end+'_vertex_index']]
                point = nodes[vertex['point_index']]
                check(vertex['kind'] == 'vertex' and point['kind'] == 'point', 'explicit typed edge/vertex/point chain')
                parameter = edge[end+'_parameter']
                value = evaluate_helix_curve(cache, parameter)
                error = distance(value, point['raw_origin'])
                check(error < 1e-10, 'literal helix parameter formula agrees with explicit edge endpoint')
                curve_errors.append(error)
                endpoint_checks.append({'which': end, 'vertex_index': vertex['index'], 'point_index': point['index'],
                    'literal_edge_parameter': parameter, 'evaluated_position': value,
                    'stored_point': point['raw_origin'], 'error_raw': error})
            domain = cache['parameter_domain']
            grid = [evaluate_helix_curve(cache, domain[0]+(domain[1]-domain[0])*q/8) for q in range(9)]
            check(all(math.isfinite(v) for p in grid for v in p), 'curve evaluation uses only encoded finite interval')
            if 'pitch_cm' in api:
                check(math.isclose(cache['derived_advance_per_turn_magnitude_raw'], api['pitch_cm'], abs_tol=1e-12),
                      'per-turn magnitude agrees with independent actual ThreadInfo pitch getter')
                radii = [api['major_diameter_cm']/2, api['minor_diameter_cm']/2]
                check(any(math.isclose(cache['derived_radius_raw'], r, abs_tol=1e-12) for r in radii),
                      'encoded helix radius agrees with actual major/minor ThreadInfo diameter')
            curve_checks.append({'curve_record_index': edge['curve_index'], 'edge_record_index': edge['index'],
                'endpoints': endpoint_checks, 'finite_grid_samples': grid,
                'parameter_scope': 'Literal stored edge parameters used directly, including negative domains; no sign/phase remapping'})
        surface_checks = []
        for coedge in nodes.values():
            if coedge['kind'] != 'coedge' or coedge.get('loop_index') not in nodes:
                continue
            loop = nodes[coedge['loop_index']]
            face = nodes.get(loop.get('face_index'))
            if not face or face.get('surface_index') not in geometries:
                continue
            cache = geometries[face['surface_index']]
            if 'encoded_surface_kind' not in cache or coedge.get('pcurve_index') not in nodes:
                continue
            pc = nodes[coedge['pcurve_index']]
            if pc['kind'] != 'pcurve' or not pc.get('uv_curve', {}).get('parameter_domain'):
                continue
            uv = pc['uv_curve']
            edge = nodes[coedge['edge_index']]
            endpoint_points = [nodes[nodes[edge[end+'_vertex_index']]['point_index']]['raw_origin'] for end in ('start', 'end')]
            evaluated = []
            for parameter in uv['parameter_domain']:
                coords = evaluate_pcurve(uv, parameter)
                value = evaluate_helix_surface(cache, *coords)
                error = min(distance(value, p) for p in endpoint_points)
                check(error < 1e-10, 'independent pcurve UV and typed parent surface recover edge endpoint set')
                surface_errors.append(error)
                evaluated.append({'pcurve_parameter': parameter, 'literal_UV': coords,
                    'surface_position': value, 'typed_endpoint_set_error_raw': error})
            # Both endpoint positions must be covered; no identity/permutation inferred.
            check(all(any(distance(p, e['surface_position']) < 1e-10 for e in evaluated) for p in endpoint_points),
                  'surface UV endpoints cover both explicit edge endpoint positions')
            surface_checks.append({'coedge_record_index': coedge['index'], 'pcurve_record_index': pc['index'],
                'loop_record_index': loop['index'], 'face_record_index': face['index'],
                'surface_record_index': face['surface_index'], 'edge_record_index': edge['index'], 'evaluations': evaluated,
                'scope': 'Typed incidence establishes membership. Unordered endpoint corroboration does not define an edge/pcurve parameter map or vertex identity.'})
        grids = []
        for index, cache in geometries.items():
            if 'encoded_surface_kind' not in cache:
                continue
            u0, u1 = cache['parameter_domain_u']; v0, v1 = cache['parameter_domain_v']
            values = [evaluate_helix_surface(cache, u0+(u1-u0)*i/4, v0+(v1-v0)*j/4) for i in range(5) for j in range(5)]
            check(all(math.isfinite(x) for p in values for x in p), 'surface grid stays within its encoded outer UV limits')
            if 'thread_angle_degrees' in api:
                radial = abs(cache['stored_line_coefficient_vector'][0]*cache['derived_radius_raw'])
                axial = abs(cache['stored_line_coefficient_vector'][2])
                angle = math.degrees(math.atan2(radial, axial))
                check(math.isclose(angle, api['thread_angle_degrees'], abs_tol=1e-9), 'restricted encoded line slope agrees with captured ThreadInfo profile angle')
            grids.append({'surface_record_index': index, 'finite_grid_sample_count': len(values)})
        check(len(curve_checks) == 4 and len(surface_checks) == 4, 'four helix edges and four explicit UV-side incidence chains per file')
        samples.append({'file': file, 'member': member, 'actual_API_settings': api,
            'encoded_geometries': [{'record_index': i, 'geometry': c} for i, c in geometries.items()],
            'typed_curve_endpoint_checks': curve_checks, 'typed_surface_UV_endpoint_checks': surface_checks,
            'finite_surface_grids': grids,
            'API_scope': 'ThreadInfo pitch/radii/profile-angle getters exist in external Thread sample. Tapped-hole truth captures designation and settings only; no unrecorded diameter or evaluator getter is claimed.'})
    guards = []
    curve = next(r for r in saved if r['name'] == 'intcurve-curve')
    surface = next(r for r in saved if r['name'] == 'spline-surface')

    def rejected(label, operation):
        try:
            operation()
        except (ValueError, IndexError) as error:
            check(True, label)
            guards.append({'guard': label, 'reason': str(error)})
        else:
            raise AssertionError('Unobserved helix accepted: '+label)

    def changed(record, field, value):
        r = copy.deepcopy(record)
        r['tokens'][field]['value'] = value
        return decode_helix_cache(r)

    rejected('Nonunit helix axis', lambda: changed(curve, 16, [0., 0., 2.]))
    rejected('Unequal radial frame vector lengths', lambda: changed(curve, 12, [1., 0., 0.]))
    rejected('Unobserved nonzero scalar after advance vector', lambda: changed(curve, 15, .1))
    rejected('Encoded interval cannot be inverted', lambda: changed(curve, 10, curve['tokens'][8]['value']-1.))
    rejected('Populated transverse line coefficient is unsupported', lambda: changed(surface, 29, [1., .1, .5]))
    bad = copy.deepcopy(surface)
    bad['tokens'].append({'kind': 'integer', 'tag': 4, 'value': 0})
    rejected('Trailing token after encoded surface limits', lambda: decode_helix_cache(bad))
    cache = decode_helix_cache(surface)
    rejected('Evaluator does not invent a wider parameter domain', lambda: evaluate_helix_surface(cache, cache['parameter_domain_u'][1]+1., cache['parameter_domain_v'][0]))
    tilted = copy.deepcopy(cache)
    tilted['raw_axis'] = [math.sin(.3), 0., math.cos(.3)]
    rejected('Arbitrary axis frame is outside restricted surface evaluator evidence', lambda: evaluate_helix_surface(tilted, cache['parameter_domain_u'][0], cache['parameter_domain_v'][0]))
    # A supported ordinary spline reader stays exact; no shared source hook here.
    control_file = root/'edgemodes-87edbf67527b/fillet_asymmetric.f3d'
    controls = inspect_asm(next(b for m, b in read_members(control_file, zstd).items() if m.endswith('.smbh')))
    ordinary = [decode_bspline(controls['records'][i]) for i in (42, 53, 60, 79)]
    check(len(ordinary) == 4, 'ordinary spline caches remain available without helix reader changes')
    return {'stage': 'Modeled thread encoded helix geometry',
        'interface': {'helper': 'decode_helix_cache.decode_helix_cache(record)',
            'curve_evaluator': 'evaluate_helix_curve(cache, parameter)', 'surface_evaluator': 'evaluate_helix_surface(cache,u,v)',
            'integration': 'Root routes helix_int_cur and helix_spl_line to separate node encoded_curve_geometry/encoded_surface_geometry and conditional graph encoded_curves/encoded_surfaces. These are not B-splines.',
            'dispatch_kinds': 'encoded_curve_kind=CircularHelix; encoded_surface_kind=HelicalLineSurface'},
        'framing': {'curve': '24 typed tokens: finite interval, origin, cosine/sine radial vectors, per-turn advance vector, zero scalar, unit axis, null support markers, exact subtype end and two outer null bounds.',
            'surface': '39 typed tokens: three stored finite interval pairs, helix frame, null support markers, line coefficient vector, subtype end and four finite outer UV bounds.',
            'domain': 'Only literal stored intervals and outer limits are used; no sampled or guessed domain is substituted.'},
        'validation': {'checks': checks, **counts, 'saved_files': len(samples),
            'typed_curve_endpoint_positions': len(curve_errors), 'typed_surface_UV_endpoint_positions': len(surface_errors),
            'maximum_curve_endpoint_error_raw': max(curve_errors), 'maximum_surface_UV_endpoint_error_raw': max(surface_errors),
            'malformed_or_unobserved_guards': guards, 'API_geometry_evaluator_getters_captured': False},
        'limitations': ['Surface evaluator is limited to captured Z-axis/+X radial frames and numerical near-zero transverse line coefficient. General Dy/frame semantics remain unresolved and reject.',
            'A nonzero transverse coefficient is retained as unsupported rather than assigned an invented geometric term.',
            'Thread handedness labels and literal helix axis signs are not generalized into a conversion rule.',
            'Typed UV endpoint sets corroborate surface geometry; edge/pcurve parameter mappings remain unassigned.',
            'Finite sampled grids and endpoint/API scalar agreement do not establish an external evaluator equivalence or global error bound.',
            'Raw geometry carries no current visibility, final-state lifecycle, placement or native persistent topology claims.'],
        'samples': samples}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    p.add_argument('--zstd-library', type=Path, required=True)
    p.add_argument('--report', type=Path)
    args = p.parse_args()
    result = validate(args.root, args.zstd_library)
    (args.report or args.root/'helix-cache-decoding.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['validation'], indent=2))
