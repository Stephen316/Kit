"""One-archive explicit cyl_spl_sur grids and qualified topology evidence."""

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

from asm_records import inspect_asm
from decode_asm_subtypes import decode_asm_subtypes, expand_asm_subtype_record, resolve_asm_subtype
from decode_brep import decode_topology
from decode_bspline import decode_bspline, evaluate_curve, evaluate_surface
from decode_cylindrical_spline_cache import decode_cylindrical_spline_cache
from decode_pcurve import evaluate_pcurve
from fusion_archive import read_members
from validate_fillet_spline_caches import OLD_CACHE_HASHES

ROOT = Path(__file__).resolve().parent
FILE = 'embosstext-cd769aa41cdf/two_texts.f3d'


def independent_tensor(cache, fu, fv):
    """Direct quadratic/linear Bernstein formula, independent of de Boor."""
    assert (cache['control_count_u'], cache['control_count_v']) == (3, 2)
    weights_u = ((1-fu)**2, 2*(1-fu)*fu, fu**2)
    points = cache['raw_control_points']
    return [sum(weights_u[u]*((1-fv)*points[2*u][axis]+fv*points[2*u+1][axis]) for u in range(3)) for axis in range(3)]


def validate(zstd_library):
    members = read_members(ROOT / FILE, zstd_library)
    report = {'scope': 'Observed explicit quadratic/linear cyl_spl_sur caches in one EmbossText archive and its two ASM blobs; finite V domain comes from stored knots',
              'source': FILE,
              'integration': {'helper': 'decode_cylindrical_spline_cache.decode_cylindrical_spline_cache(record)',
                              'dispatch': 'spline-surface/cyl_spl_sur -> helper; existing decode_asm_subtype_cache expansion then recovers qualified top-level surface refs with their original wrapper/tail',
                              'output': 'Standard evaluate_surface-compatible non-rational tensor cache plus literal embedded curve cache, native extrusion fields, knot domains and optional trim fields.',
                              'validation_command': '/usr/bin/python3 validate_cylindrical_spline_cache.py',
                              'shared_edits_by_this_task': False},
              'native_framing': {'prefix': 'Boolean wrapper; cyl_spl_sur23100; bounded embedded quadratic exact_int_cur NUBS curve with its own optional interval; direction vector, origin vector, enum0.',
                                 'grid': 'Explicit nubs/degreeU2/degreeV1, four enum0 flags, counted clamped U/V knots, three doubles per grid control; U-fast normalized to V-fast.',
                                 'trailer': 'Scalar, six counted scalar lists, literalFalse flag, exact subtype end, four optional interval fields and exact record exhaustion.',
                                 'domains': 'Explicit cache U knots[0,1], V knots[0,0.2] in the observed fixture. Outer interval fields are all absent and are not replaced by invented finite bounds.'},
              'catalog': [], 'representatives': [], 'qualified_boundary_checks': [], 'curve_reference_proofs': [],
              'old_output_controls': [], 'guards': [],
              'limitations': ['The helper decodes stored tensor grids and embedded curve caches; it does not reconstruct the exact procedural surface or provide a global approximation bound.',
                              'Direction/origin and wrapper/sense/bound flags remain source facts. Their universal procedural parameter meanings are not inferred.',
                              'API modeling truth supplies context only; no surface-evaluator or cache getter equality is asserted.',
                              'Parent surface and embedded curve associations use explicit topology and independently qualified blob-local subtype references. Geometry is only subsequent corroboration.',
                              'UV domain endpoint ordering may differ from edge ordering. Endpoint sets are corroborated without installing reversal or parameter remapping.',
                              'Raw ASM geometry remains independent of native current/final body lifecycle, units/context transforms, assembly solving or regeneration.']}
    context = json.loads((ROOT / 'embosstext-cd769aa41cdf/ground_truth.json').read_text())
    actual = next(s for s in context['samples'] if s['file'] == 'two_texts.f3d')
    report['api_context'] = {'fusion_version': context['fusion_version'],
                             'actual_settings': actual.get('settings'), 'surface_evaluator_getters_captured': False}
    total_tensor = total_extrusion = 0
    tensor_errors, extrusion_errors, endpoint_errors = [], [], []
    sources = []
    for member, raw in members.items():
        if not member.endswith(('.smb', '.smbh')):
            continue
        parsed = inspect_asm(raw); assert parsed['complete_token_stream']
        records = parsed['records']; catalog = decode_asm_subtypes(raw, parsed=parsed)
        caches, source_proofs = {}, {}
        for record in records:
            if record['name'] != 'spline-surface' or record['section'] != 'geometry':
                continue
            subtype = record['tokens'][5].get('value')
            if subtype == 'ref':
                proof = resolve_asm_subtype(catalog, record['index'], 4, expected_kind='surface')
                if proof['target_definition']['subtype_name'] != 'cyl_spl_sur':
                    continue
                expanded = expand_asm_subtype_record(record, catalog, records)
                source, kind = expanded['record'], 'qualified_reference'
            elif subtype == 'cyl_spl_sur':
                proof = resolve_asm_subtype(catalog, record['index'], 4, expected_kind='surface')
                source, kind = record, 'direct_definition'
            else:
                continue
            cache = decode_cylindrical_spline_cache(source)
            sources.append(source)
            caches[record['index']] = cache; source_proofs[record['index']] = proof
            assert (cache['control_count_u'], cache['control_count_v']) == (3, 2)
            assert cache['parameter_domain_u'] == [0., 1.] and cache['parameter_domain_v'] == [0., .2]
            assert cache['stored_interval_flags'] == [False]*4
            assert cache['stored_parameter_interval_u'] == cache['stored_parameter_interval_v'] == [None, None]
            entry = {'member': member, 'record_index': record['index'], 'source_kind': kind,
                     'target_definition_index': proof['target_definition']['definition_index'],
                     'target_record_index': proof['target_definition']['record_index'],
                     'target_subtype_token_start': proof['target_definition']['token_start'],
                     'cache_domain_u': cache['parameter_domain_u'], 'cache_domain_v': cache['parameter_domain_v'],
                     'outer_interval_fields_remain_absent': True}
            report['catalog'].append(entry)
            if not any(s['member'] == member and s['source_kind'] == kind for s in report['representatives']):
                report['representatives'].append(dict(entry, cache=cache))
            for fu in (.25, .5, .75):
                for fv in (.25, .5, .75):
                    u, v = fu, .2*fv
                    result = evaluate_surface(cache, u, v)
                    independent = independent_tensor(cache, fu, fv)
                    tensor_errors.append(math.dist(result, independent)); total_tensor += 1
                    curve = evaluate_curve(cache['stored_embedded_curve_cache'], u)
                    extrusion = [p+v*d for p, d in zip(curve, cache['stored_extrusion_direction'])]
                    extrusion_errors.append(math.dist(result, extrusion)); total_extrusion += 1
            assert max(tensor_errors) < 1e-12 and max(extrusion_errors) < 1e-12
        topology = decode_topology(parsed, subtype_catalog=catalog)
        nodes = {n['index']: n for n in topology['nodes']}
        chosen = {r['record_index'] for r in report['representatives'] if r['member'] == member}
        for coedge in nodes.values():
            if coedge['kind'] != 'coedge':
                continue
            loop = nodes.get(coedge['loop_index']); face = nodes.get(loop['face_index']) if loop else None
            if not face or face['surface_index'] not in chosen:
                continue
            surface_index = face['surface_index']; surface = caches[surface_index]
            edge = nodes[coedge['edge_index']]; uv_node = nodes[coedge['pcurve_index']]
            assert (loop['kind'], face['kind'], edge['kind'], uv_node['kind']) == ('loop', 'face', 'edge', 'pcurve')
            uv = uv_node['uv_curve']; uv_record = records[uv_node['index']]
            # Resolve the literal pcurve support bracket and parent surface
            # independently, before performing any geometric comparison.
            surface_blocks = [b for b in catalog['blocks'] if b['record_index'] == uv_node['index'] and b['context_kind'] == 'surface']
            if len(surface_blocks) != 1:
                raise AssertionError(('Expected one qualified pcurve support', member, uv_node['index'], surface_blocks))
            support_start = surface_blocks[0]['token_start']
            uv_ref = resolve_asm_subtype(catalog, uv_node['index'], support_start, expected_kind='surface')
            surface_ref = source_proofs[surface_index]
            assert uv_ref['target_definition']['definition_index'] == surface_ref['target_definition']['definition_index']
            evaluated = [evaluate_surface(surface, *evaluate_pcurve(uv, parameter)) for parameter in uv['parameter_domain']]
            vertices = [nodes[edge[which+'_vertex_index']] for which in ('start', 'end')]
            points = [nodes[v['point_index']] for v in vertices]
            assert all(v['kind'] == 'vertex' and p['kind'] == 'point' for v, p in zip(vertices, points))
            values = [p['raw_origin'] for p in points]
            error = max(max(min(math.dist(a, b) for b in values) for a in evaluated),
                        max(min(math.dist(a, b) for b in evaluated) for a in values))
            endpoint_errors.append(error); assert error < 1e-9
            report['qualified_boundary_checks'].append({'member': member, 'coedge_index': coedge['index'],
                'loop_index': loop['index'], 'face_index': face['index'], 'surface_index': surface_index,
                'edge_index': edge['index'], 'pcurve_index': uv_node['index'],
                'qualified_surface_definition': uv_ref['target_definition']['definition_index'],
                'uv_domain_surface_endpoints': evaluated,
                'explicit_vertex_indices': [v['index'] for v in vertices], 'explicit_point_indices': [p['index'] for p in points],
                'raw_endpoint_points': values, 'unordered_endpoint_set_error_raw': error,
                'scope': 'Explicit typed parent/support namespace agreement before unordered endpoint corroboration; no orientation inferred'})
            curve_record = records[edge['curve_index']]
            if curve_record['name'] != 'intcurve-curve' or curve_record['tokens'][5].get('value') != 'ref':
                continue
            curve_proof = resolve_asm_subtype(catalog, curve_record['index'], 4, expected_kind='curve')
            target = curve_proof['target_definition']; owner = surface_ref['target_definition']
            if target['record_index'] == owner['record_index'] and target['parent_definition_index'] == owner['definition_index']:
                assert target['subtype_name'] == 'exact_int_cur' and target['context_kind'] == 'curve'
                report['curve_reference_proofs'].append({'member': member, 'surface_index': surface_index,
                    'edge_index': edge['index'], 'curve_record_index': curve_record['index'],
                    'target_embedded_curve_definition': target, 'surface_definition_index': owner['definition_index'],
                    'association': 'Typed curve reference resolves to a child exact-curve definition inside the independently resolved parent surface; no coordinate matching chooses identity'})
    assert len(report['catalog']) == 98
    assert len(report['representatives']) == 4 and report['curve_reference_proofs']
    for control in [next(c for c in OLD_CACHE_HASHES if c['file'].startswith('moretools') and c['index'] == 18),
                    next(c for c in OLD_CACHE_HASHES if c['file'].startswith('splinepatches') and c['index'] == 11),
                    next(c for c in OLD_CACHE_HASHES if c['file'].startswith('splines') and c['index'] == 18)]:
        prior_members = read_members(ROOT / control['file'], zstd_library)
        record = inspect_asm(prior_members[control['member']])['records'][control['index']]
        assert hashlib.sha256(json.dumps(decode_bspline(record), sort_keys=True).encode()).hexdigest() == control['sha256']
        report['old_output_controls'].append(dict(control, exact_previous_dictionary_unchanged=True))
    base = next(s for s in sources if len(s['tokens']) == 103)
    def reject(label, mutate):
        changed = copy.deepcopy(base); mutate(changed['tokens'])
        try:
            decode_cylindrical_spline_cache(changed)
        except (ValueError, IndexError) as error:
            report['guards'].append({'case': label, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError('Malformed cylindrical spline accepted: '+label)
    reject('Embedded curve subtype changed', lambda t: t[10].update(value='unknown_curve'))
    reject('Embedded curve subtype terminator removed', lambda t: t.__delitem__(47))
    reject('Wrong grid representation', lambda t: t[55].update(value='unknown_grid'))
    reject('Non-increasing V knots', lambda t: t[70].update(value=0.0))
    reject('Nonfinite grid coordinate', lambda t: t[72].update(value=float('nan')))
    reject('Wrong trailer subtype terminator', lambda t: t[98].update(kind='subtype_start'))
    reject('Trailing unconsumed field', lambda t: t.append({'kind': 'integer', 'value': 0}))
    report['summary'] = {'saved_archives': 1, 'asm_blobs': 2,
                         'direct_surface_definitions': sum(e['source_kind'] == 'direct_definition' for e in report['catalog']),
                         'qualified_surface_references': sum(e['source_kind'] == 'qualified_reference' for e in report['catalog']),
                         'total_surface_caches': len(report['catalog']),
                         'independent_tensor_bernstein_comparisons': total_tensor,
                         'maximum_independent_tensor_error_raw': max(tensor_errors),
                         'stored_curve_extrusion_sample_comparisons': total_extrusion,
                         'maximum_stored_curve_extrusion_sample_error_raw': max(extrusion_errors),
                         'qualified_parent_uv_boundary_chains': len(report['qualified_boundary_checks']),
                         'endpoint_positions_corroborated': 2*len(endpoint_errors),
                         'maximum_endpoint_set_error_raw': max(endpoint_errors),
                         'qualified_embedded_curve_reference_proofs': len(report['curve_reference_proofs']),
                         'old_output_controls_unchanged': len(report['old_output_controls']), 'malformed_guards': len(report['guards'])}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='cylindrical-spline-cache-decoding.json')
    args = parser.parse_args()
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    report = validate(str(zstd))
    Path(args.output).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], sort_keys=True))
