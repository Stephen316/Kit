"""Focused stored spring-cache endpoint and independent cache comparisons."""

import argparse
import copy
import json
import math
from pathlib import Path

from asm_records import inspect_asm
from decode_brep import decode_topology
from decode_bspline import evaluate_curve, evaluate_surface
from decode_pcurve import evaluate_pcurve
from decode_spring_curve_cache import decode_spring_curve_cache
from decode_variable_blend_cache import decode_variable_blend_cache
from fusion_archive import read_members

FILES = ('edgemodes-87edbf67527b/fillet_asymmetric.f3d', 'edgemodes-87edbf67527b/fillet_chord.f3d')


def distance(a, b):
    return math.sqrt(sum((x-y)**2 for x, y in zip(a, b)))


def fraction(domain, value):
    return domain[0] if value == 0 else domain[1] if value == 1 else domain[0]+(domain[1]-domain[0])*value


def validate(root, zstd):
    checks, samples, captures, endpoint_count, comparison_count = 0, [], [], 0, 0

    def check(test, reason):
        nonlocal checks
        if not test:
            raise AssertionError(reason)
        checks += 1

    api = {s['file']: s for s in json.loads((root/'edgemodes-87edbf67527b/ground_truth.json').read_text())['samples']}
    for relative in FILES:
        members = read_members(root/relative, zstd)
        member, blob = next((m, b) for m, b in members.items() if m.endswith('.smbh'))
        parsed = inspect_asm(blob)
        check(parsed['complete_token_stream'], 'source ASM tokens complete')
        records = parsed['records']
        nodes = {n['index']: n for n in decode_topology(parsed)['nodes']}
        surface = decode_variable_blend_cache(records[10])
        curves = []
        for curve_id in (53, 60):
            record = records[curve_id]
            before = copy.deepcopy(record)
            cache = decode_spring_curve_cache(record)
            check(record == before, 'new helper leaves original tokens unchanged')
            check(len(cache['raw_control_points']) == 11 and len(cache['weights']) == 11 and all(w == 1. for w in cache['weights']),
                  'captured rational grid retains eleven unit weights')
            check(cache['stored_compact_knots'][0][1] == cache['stored_compact_knots'][-1][1] == 3,
                  'clamped cubic knot ends retained')
            check([m for _, m in cache['stored_compact_knots']] == [3, 2, 3, 2, 3],
                  'captured compact multiplicity sequence exact')
            edge, = [n for n in nodes.values() if n['kind'] == 'edge' and n['curve_index'] == curve_id]
            endpoints = []
            for which in ('start', 'end'):
                vertex = nodes[edge[which+'_vertex_index']]
                point = nodes[vertex['point_index']]
                check(vertex['kind'] == 'vertex' and point['kind'] == 'point', 'typed edge/vertex/point endpoint chain')
                endpoints.append({'which': which, 'vertex_index': vertex['index'], 'point_index': point['index'],
                                  'edge_parameter': edge[which+'_parameter'], 'stored_position': point['raw_origin']})
            domain = cache['parameter_domain']
            raw_cache_endpoints = [evaluate_curve(cache, parameter) for parameter in domain]
            check(all(any(distance(p, e['stored_position']) < 1e-9 for e in endpoints) for p in raw_cache_endpoints),
                  'raw cache endpoint set agrees with explicit typed edge endpoint set')
            hypotheses = []
            for multiplier in (1, -1):
                errors, mapped_parameters, outside = [], [], False
                for e in endpoints:
                    parameter = multiplier*e['edge_parameter']
                    if parameter < domain[0] and domain[0]-parameter < 1e-12:
                        parameter = domain[0]
                    elif parameter > domain[1] and parameter-domain[1] < 1e-12:
                        parameter = domain[1]
                    mapped_parameters.append(parameter)
                    if not domain[0] <= parameter <= domain[1]:
                        outside = True
                    else:
                        errors.append(distance(evaluate_curve(cache, parameter), e['stored_position']))
                hypotheses.append({'edge_to_raw_cache_parameter_multiplier': multiplier,
                    'mapped_parameters': mapped_parameters, 'outside_raw_domain': outside,
                    'endpoint_errors_raw': errors, 'matches_both_typed_endpoints': not outside and len(errors) == 2 and max(errors) < 1e-9})
            matching = [h for h in hypotheses if h['matches_both_typed_endpoints']]
            check(len(matching) == 1, 'one sign hypothesis matches captured typed endpoints')
            check(matching[0]['edge_to_raw_cache_parameter_multiplier'] == (-1 if cache['stored_wrapper_flag'] else 1),
                  'observed wrapper/sign correspondence documented without changing raw cache')
            endpoint_count += 2
            # Parent surface comes from independent topology, never inline ref0.
            coedges = [c for c in nodes.values() if c['kind'] == 'coedge' and c['edge_index'] == edge['index']
                and c.get('loop_index') in nodes and nodes[c['loop_index']]['face_index'] in nodes
                and nodes[nodes[c['loop_index']]['face_index']]['surface_index'] == 10]
            coedge, = coedges
            loop = nodes[coedge['loop_index']]
            face = nodes[loop['face_index']]
            uv_node = nodes[coedge['pcurve_index']]
            check(loop['kind'] == 'loop' and face['kind'] == 'face' and uv_node['kind'] == 'pcurve',
                  'typed coedge/loop/face/pcurve independently selects support surface')
            uv = uv_node['uv_curve']
            check(len(cache['stored_embedded_uv_cache']['raw_control_points']) == 2,
                  'separate embedded linear UV cache count exact')
            comparisons, linear_differences = [], []
            first, last = raw_cache_endpoints
            for q in (0., .125, .25, .375, .5, .625, .75, .875, 1.):
                parameter = fraction(domain, q)
                uv_parameter = fraction(uv['parameter_domain'], q)
                xyz = evaluate_curve(cache, parameter)
                coords = evaluate_pcurve(uv, uv_parameter)
                surface_xyz = evaluate_surface(surface, *coords)
                error = distance(xyz, surface_xyz)
                check(error < 1e-9, 'independent stored XYZ and UV/surface cache samples agree')
                linear_xyz = [(1-q)*a+q*b for a, b in zip(first, last)]
                linear_error = distance(xyz, linear_xyz)
                linear_differences.append(linear_error)
                comparisons.append({'fraction': q, 'XYZ_cache_parameter': parameter, 'linked_pcurve_parameter': uv_parameter,
                    'XYZ_cache_position': xyz, 'linked_pcurve_UV': coords, 'surface_cache_position': surface_xyz,
                    'independent_cache_deviation_raw': error, 'linear_endpoint_chord_position': linear_xyz,
                    'linear_parameterization_deviation_raw': linear_error})
                comparison_count += 1
            curves.append({'record_index': curve_id, 'edge_index': edge['index'], 'cache': cache,
                'typed_endpoints': endpoints, 'sign_hypotheses': hypotheses,
                'parameter_scope': 'Sign hypotheses are limited to these explicit endpoint links. Raw cache domain and wrapper are preserved; no general edge evaluator/reversal rule is added.',
                'typed_support_chain': {'coedge_index': coedge['index'], 'loop_index': loop['index'],
                    'face_index': face['index'], 'surface_index': 10, 'pcurve_index': uv_node['index']},
                'independent_cache_samples': comparisons,
                'maximum_sampled_cache_deviation_raw': max(c['independent_cache_deviation_raw'] for c in comparisons),
                'maximum_sampled_linear_parameterization_deviation_raw': max(linear_differences),
                'comparison_scope': 'Each stored domain is sampled independently at equal fractions; tiny domain endpoint differences are retained. Finite agreement is internal cache corroboration, not exact procedural/API evaluator equivalence or a global error bound.'})
            captures.append(record)
        samples.append({'file': relative, 'member': member, 'actual_API_settings': api[Path(relative).name]['settings'], 'curves': curves})
    guards = []
    reference = captures[0]

    def reject(label, change):
        changed = copy.deepcopy(reference)
        change(changed['tokens'])
        try:
            decode_spring_curve_cache(changed)
        except (ValueError, IndexError) as error:
            check(True, label)
            guards.append({'guard': label, 'reason': str(error)})
        else:
            raise AssertionError('Malformed spring record accepted: '+label)

    reject('Nonpositive rational weight', lambda t: t[25].update(value=0.))
    reject('Nonfinite XYZ control coordinate', lambda t: t[22].update(value=float('nan')))
    reject('Non-increasing compact knot sequence', lambda t: t[14].update(value=t[12]['value']))
    reject('Unobserved inline support reference', lambda t: t[71].update(value=1))
    reject('UV grid degree is unobserved', lambda t: t[87].update(value=3))
    reject('Wrapper/terminal enum pair is unobserved', lambda t: t[105].update(value=2))
    reject('Trailing token after exact outer wrapper', lambda t: t.append({'kind': 'integer', 'value': 0, 'tag': 4}))
    return {'stage': 'Spring procedural curve approximation caches',
        'integration': {'helper': 'decode_spring_curve_cache.decode_spring_curve_cache(record)',
            'dispatch': 'In decode_bspline, dispatch intcurve-curve with subtype_start at token 4 and spring_int_cur at token 5 before the generic false-wrapper check. Existing readers remain unchanged.',
            'returns': 'Canonical XYZ degree/knots/controls/weights/domain, separate embedded UV cache, raw support/trailer/flags.',
            'evaluation': 'decode_bspline.evaluate_curve(cache, raw_cache_parameter). Edge parameter sign mapping is evidence-only, never silently applied.'},
        'framing': {'wrapper': 'Boolean true/false; spring_int_cur version 23100 enum 0; cubic form 0 rational XYZ grid; counted compact knots and four-value controls.',
            'support': 'Spline/ref0 with exact bounded false flags; explicit planar origin/normal/axis; degree 1 form 0 two-control non-rational UV grid.',
            'trailer': 'nullbs; two false flags; four empty scalar lists; observed terminal enum 0 (true wrapper) / 2 (false wrapper); outer subtype end and two false flags.',
            'unknowns': 'Wrapper/enum meaning, inline ref0 identity, cache scalar meaning and exact spring construction remain unresolved.'},
        'validation': {'checks': checks, 'saved_files': len(samples), 'spring_curve_caches': len(captures),
            'typed_endpoint_checks': endpoint_count, 'independent_cache_comparisons': comparison_count,
            'guards': guards, 'API_curve_or_surface_evaluator_getters_captured': False,
            'maximum_sampled_independent_cache_deviation_raw': max(c['maximum_sampled_cache_deviation_raw'] for s in samples for c in s['curves'])},
        'limitations': ['Caches are stored approximations; finite sampled agreement provides no exact procedural equivalence or global error bound.',
            'Direct API truth contains Fillet settings, not curve/surface evaluator outputs.',
            'True wrapper examples have negative edge parameters and only sign-negated endpoint hypotheses fit the raw XYZ cache; this is not generalized into a production orientation rule.',
            'The spline inline ref0 remains opaque. Surface 10 correspondence is independently established through typed coedge/loop/face links.',
            'Raw ASM coordinates are retained; component/body transforms, unit/context conversions and lifecycle classification are not applied.'],
        'samples': samples}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    p.add_argument('--zstd-library', type=Path, required=True)
    p.add_argument('--report', type=Path)
    args = p.parse_args()
    report = validate(args.root, args.zstd_library)
    (args.report or args.root/'spring-curve-cache-decoding.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['validation'], indent=2))
