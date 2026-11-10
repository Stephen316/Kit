"""Closed-loft form2 cache framing, raw-basis and typed closure evidence."""

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

from asm_records import inspect_asm
from decode_asm_subtypes import decode_asm_subtypes
from decode_brep import decode_topology
from decode_bspline import decode_bspline, evaluate_curve, evaluate_surface
from decode_exact_curve_form_two import decode_exact_curve_form_two
from decode_pcurve import evaluate_pcurve
from fusion_archive import read_members
from validate_fillet_spline_caches import OLD_CACHE_HASHES
from validate_surface_cache_variants import cox_basis

ROOT = Path(__file__).resolve().parent
FILES = ['loftguides-265bcb9af34a/closure_closed_surface.f3d',
         'loftguides-265bcb9af34a/closure_closed_four.f3d']


def validate(zstd_library):
    truth = json.loads((ROOT / 'loftguides-265bcb9af34a/ground_truth.json').read_text())
    report = {'scope': 'Four direct clamped cubic exact_int_cur form2 caches in two saved closed-loft captures; no general periodic or sign interpretation',
              'integration': {'helper': 'decode_exact_curve_form_two.decode_exact_curve_form_two(record)',
                              'dispatch': 'Root base-first fallback for intcurve-curve/exact_int_cur/form2; existing form0/form1 readers remain unchanged.',
                              'schema': 'Evaluator-compatible degree/knots/raw_control_points/weights/parameter_domain fields; stored_form_code2 and is_periodicNone.',
                              'validation_command': '/usr/bin/python3 validate_exact_curve_form_two.py', 'shared_edits_by_this_task': False},
              'native_framing': 'False wrapper, exact_int_cur23100 enum0, nubs cubic/form2, counted compact knots/control triples, scalar/null_surface/null_surface/nullbs/nullbs/twoFalse flags, four counted scalar lists, twoTrue+double fields, enum0/0, subtype end, twoFalse outer fields, exact exhaustion.',
              'samples': [], 'old_output_controls': [], 'guards': [],
              'limitations': ['Form2 is a literal stored form code. Coincident cache endpoints and repeated endpoint vertex identity do not prove general periodicity, parameter extension or exact procedural continuity.',
                              'The four counted trailer lists, two flagged scalar values and trailer enums are preserved without assigning solver or periodic-knot roles.',
                              'Independent Cox-basis evaluation uses raw stored controls and knots; it validates the cache, not an API curve evaluator.',
                              'Negative-domain coedge UV caches are retained as parameter-correspondence counterexamples; no sign mapping is installed.',
                              'API actual isClosed values corroborate these two loft features only. No API cache/evaluator getters were captured for these records.',
                              'Body lifecycle, current placement, assembly solving, exact trimming and native regeneration remain outside this helper.']}
    sources = []; all_errors = []; uv_errors = []
    for relative in FILES:
        actual = next(s for s in truth['samples'] if s['file'] == Path(relative).name)['settings']
        assert actual['is_closed'] is True
        for member, raw in read_members(ROOT / relative, zstd_library).items():
            if not member.endswith(('.smb', '.smbh')):
                continue
            parsed = inspect_asm(raw); assert parsed['complete_token_stream']
            catalog = decode_asm_subtypes(raw, parsed=parsed)
            nodes = {n['index']: n for n in decode_topology(parsed, subtype_catalog=catalog)['nodes']}
            for record in parsed['records']:
                ts = record['tokens']
                if (record['section'] != 'geometry' or record['name'] != 'intcurve-curve'
                        or ts[5].get('value') != 'exact_int_cur' or ts[10]['value'] != 2):
                    continue
                cache = decode_exact_curve_form_two(record); sources.append(record)
                # Independent compact expansion and original source control order.
                compact = [[ts[12+2*i]['value'], ts[13+2*i]['value']] for i in range(ts[11]['value'])]
                expanded = [v for v, multiple in compact for _ in range(multiple)]
                full_knots = [expanded[0]]+expanded+[expanded[-1]]
                degree = ts[9]['value']; count = len(full_knots)-degree-1
                start = 12+2*len(compact)
                controls = [[ts[start+3*i+j]['value'] for j in range(3)] for i in range(count)]
                assert degree == 3 and count == 10 and cache['knots'] == full_knots and cache['raw_control_points'] == controls
                checks = []
                # Two distinct interior points per native span; no periodic wrap.
                for (a, _), (b, _) in zip(compact, compact[1:]):
                    for fraction in (1/3, 2/3):
                        parameter = a+(b-a)*fraction
                        basis = cox_basis(full_knots, degree, count, parameter)
                        independent = [sum(w*p[axis] for w, p in zip(basis, controls)) for axis in range(3)]
                        actual_point = evaluate_curve(cache, parameter)
                        error = math.dist(independent, actual_point); all_errors.append(error)
                        assert error < 1e-12
                        checks.append({'parameter': parameter, 'independent_raw_point': independent, 'cache_raw_point': actual_point, 'error_raw': error})
                domain = cache['parameter_domain']
                cache_endpoints = [evaluate_curve(cache, parameter) for parameter in domain]
                assert math.dist(*cache_endpoints) < 1e-12
                edges = [n for n in nodes.values() if n['kind'] == 'edge' and n['curve_index'] == record['index']]
                edge, = edges
                assert edge['start_vertex_index'] == edge['end_vertex_index']
                vertex = nodes[edge['start_vertex_index']]; point = nodes[vertex['point_index']]
                assert vertex['kind'] == 'vertex' and point['kind'] == 'point'
                edge_values = [evaluate_curve(cache, parameter) for parameter in (edge['start_parameter'], edge['end_parameter'])]
                assert max(math.dist(v, point['raw_origin']) for v in edge_values) < 1e-12
                entry = {'file': relative, 'member': member, 'record_index': record['index'],
                         'actual_api_is_closed': actual['is_closed'], 'actual_api_is_solid': actual['is_solid'],
                         'cache': cache, 'independent_raw_basis_checks': checks,
                         'cache_domain_endpoints': cache_endpoints,
                         'explicit_closed_edge': {'edge_index': edge['index'], 'shared_start_end_vertex_index': vertex['index'],
                                                  'point_index': point['index'], 'raw_point': point['raw_origin'],
                                                  'native_edge_parameters': [edge['start_parameter'], edge['end_parameter']],
                                                  'native_parameter_cache_values': edge_values}, 'parent_uv_checks': []}
                for coedge in nodes.values():
                    if coedge['kind'] != 'coedge' or coedge['edge_index'] != edge['index']:
                        continue
                    loop = nodes[coedge['loop_index']]; face = nodes[loop['face_index']]
                    surface_node = nodes.get(face['surface_index']); uv_node = nodes.get(coedge['pcurve_index'])
                    if not surface_node or 'bspline_surface' not in surface_node or not uv_node or 'uv_curve' not in uv_node:
                        continue
                    uv = uv_node['uv_curve']; surface = surface_node['bspline_surface']
                    uv_check = {'coedge_index': coedge['index'], 'loop_index': loop['index'], 'face_index': face['index'],
                                'surface_index': surface_node['index'], 'pcurve_index': uv_node['index'],
                                'curve_domain': domain, 'uv_domain': uv['parameter_domain']}
                    if uv['parameter_domain'] == domain:
                        errors = []
                        for fraction in (0, .25, .5, .75, 1):
                            parameter = domain[0]+(domain[1]-domain[0])*fraction
                            value = evaluate_surface(surface, *evaluate_pcurve(uv, parameter))
                            errors.append(math.dist(value, evaluate_curve(cache, parameter)))
                        assert max(errors[0], errors[-1]) < 1e-10
                        uv_errors.extend(errors)
                        uv_check['five_same_parameter_cache_deviations_raw'] = errors
                        uv_check['same_parameter_alignment_matches_within1e_10'] = max(errors) < 1e-10
                        uv_check['scope'] = 'Literal same-number parameter comparison; nonzero interior discrepancies retained, not an inferred exact procedural parameterization'
                    else:
                        uv_check['status'] = 'unresolved_parameter_correspondence; literal negative/other domain retained without remapping'
                    entry['parent_uv_checks'].append(uv_check)
                report['samples'].append(entry)
    assert len(sources) == 4
    for control in [next(c for c in OLD_CACHE_HASHES if c['file'].startswith('moretools') and c['index'] == 37),
                    next(c for c in OLD_CACHE_HASHES if c['file'].startswith('splines') and c['index'] == 18),
                    next(c for c in OLD_CACHE_HASHES if c['file'].startswith('splinepatches') and c['index'] == 11)]:
        members = read_members(ROOT / control['file'], zstd_library)
        source = inspect_asm(members[control['member']])['records'][control['index']]
        assert hashlib.sha256(json.dumps(decode_bspline(source), sort_keys=True).encode()).hexdigest() == control['sha256']
        report['old_output_controls'].append(dict(control, exact_old_output_preserved=True))
    base = sources[0]
    def reject(label, mutate):
        source = copy.deepcopy(base); mutate(source['tokens'])
        try:
            decode_exact_curve_form_two(source)
        except (ValueError, IndexError) as error:
            report['guards'].append({'case': label, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError('Malformed form2 accepted: '+label)
    reject('Wrong observed degree', lambda t: t[9].update(value=2))
    reject('Non-increasing compact knots', lambda t: t[14].update(value=t[12]['value']))
    reject('Multiplicity exceeds degree', lambda t: t[13].update(value=4))
    reject('Nonfinite control coordinate', lambda t: t[22].update(value=float('nan')))
    reject('Unobserved finite outer interval', lambda t: t[74].update(value=True))
    report['summary'] = {'saved_files': len(FILES), 'form2_curve_caches': len(sources),
                         'independent_raw_basis_evaluations': len(all_errors), 'maximum_independent_error_raw': max(all_errors),
                         'explicit_same_vertex_closed_edges': len(report['samples']), 'native_endpoint_evaluations': 2*len(report['samples']),
                         'same_parameter_parent_uv_cache_checks': len(uv_errors),
                         'maximum_same_parameter_parent_uv_deviation_raw': max(uv_errors) if uv_errors else None,
                         'unresolved_parent_uv_domains': sum('status' in c for sample in report['samples'] for c in sample['parent_uv_checks']),
                         'old_output_controls_preserved': len(report['old_output_controls']), 'malformed_guards': len(report['guards'])}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='exact-curve-form-two-decoding.json')
    args = parser.parse_args()
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    report = validate(str(zstd))
    Path(args.output).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], sort_keys=True))
