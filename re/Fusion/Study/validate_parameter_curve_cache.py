"""Targeted par_int_cur family framing and saved native geometry evidence."""

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

from asm_records import inspect_asm
from decode_brep import decode_topology
from decode_bspline import decode_bspline, evaluate_curve, evaluate_surface
from decode_parameter_curve_cache import decode_parameter_curve_cache
from decode_pcurve import evaluate_pcurve
from fusion_archive import read_members
from validate_fillet_spline_caches import OLD_CACHE_HASHES

ROOT = Path(__file__).resolve().parent
FOCUSED = ['lofts-03b4a6f1ce2f/centerline.f3d', 'sweeps-5f87eff25e24/line_twist.f3d',
           'solidsweeps-5b5ecd5e01b9/solid_twist_sixty.f3d']


def _inside(domain, values):
    return all(domain[0]-1e-12 <= v <= domain[1]+1e-12 for v in values)


def validate(zstd_library):
    contexts = {}
    def load(relative):
        if relative not in contexts:
            contexts[relative] = {m: inspect_asm(raw) for m, raw in read_members(ROOT / relative, zstd_library).items()
                                  if m.endswith(('.smb', '.smbh'))}
        return contexts[relative]
    report = {
        'scope': 'Targeted226-record par_int_cur family catalog from19 saved archives; focused native-geometry checks in3 primary fixtures, not a full main-reader corpus audit',
        'baseline': {'revision': 'b6372ab', 'discovery_overview': 'asm-geometry-frontier-b6372ab.json', 'archive_manifest': 'validate_parameter_curve_cache.FAMILY_FILES',
                     'purpose': 'Only the19 family archive names were taken from the existing baseline; all record layouts/results are read anew from saved archives.'},
        'integration': {'helper': 'decode_parameter_curve_cache.decode_parameter_curve_cache(record)',
                        'dispatch': 'intcurve-curve with subtype par_int_cur -> helper before existing unsupported-wrapper/procedural rejection',
                        'inline_support_dependency': 'decode_sweep_surface_cache.decode_sweep_surface_inline(tokens,start) returns(cache,next_cursor); start is the support Boolean before subtype_start',
                        'validation_command': '/usr/bin/python3 validate_parameter_curve_cache.py',
                        'shared_reader_changes_by_this_task': False},
        'native_framing': {
            'xyz': 'Version23100, enum0, cubic NUBS/NURBS form0, counted compact clamped knots and XYZ[/positive weight] controls.',
            'support': 'One explicit plane or spline/ref or strictly decoded inline sweep_sur; second support literal null_surface.',
            'uv': 'Separate non-rational form0 degree1/5 UV cache; no universal XYZ/UV parameter correspondence inferred.',
            'trailer': 'nullbs, twoFalse flags, four counted scalar lists, literalTrue/False flags, subtype end, two optional bound fields, exact record exhaustion.'},
        'family_catalog': [], 'focused_geometry': [], 'api_context': [], 'compatibility': [], 'guards': [],
        'limitations': [
            'XYZ and UV grids are stored approximations. No exact procedural curve, topology solver, parameter remapping or approximation-error bound is provided.',
            'Raw wrapper/outer interval flags are retained without assigning coordinate reversal or edge/cache parameter roles.',
            'Inline support refs are not global ASM record IDs. Explicit coedge/loop/face links identify parent surfaces separately for validation.',
            'Direct native edge parameters are tested only when they lie inside the stored cache domain. Counterexamples are retained rather than silently negating parameters.',
            'API fixtures provide modeling/source context; no direct XYZ/UV-cache or surface-evaluator equivalence is claimed.',
            'Raw ASM geometry remains independent of active/final lifecycle, assembly placement, current visibility and regeneration.'
        ]}
    caches = {}
    for relative in FAMILY_FILES:
        for member, parsed in load(relative).items():
            assert parsed['complete_token_stream']
            for record in parsed['records']:
                if (record['section'] != 'geometry' or record['name'] != 'intcurve-curve'
                        or record['tokens'][5].get('value') != 'par_int_cur'):
                    continue
                cache = decode_parameter_curve_cache(record)
                key = (relative, member, record['index'])
                caches[key] = cache
                domain = cache['parameter_domain']
                evaluated = [evaluate_curve(cache, domain[0]+(domain[1]-domain[0])*i/4) for i in range(5)]
                uv = cache['stored_embedded_uv_cache']
                uv_values = [evaluate_curve(uv, uv['parameter_domain'][0]+(uv['parameter_domain'][1]-uv['parameter_domain'][0])*i/4)
                             for i in range(5)]
                assert all(math.isfinite(v) for point in evaluated+uv_values for v in point)
                support = cache['stored_support_definition']
                report['family_catalog'].append({
                    'file': relative, 'member': member, 'record_index': record['index'],
                    'stored_wrapper_flag': cache['stored_wrapper_flag'], 'is_rational': cache['is_rational'],
                    'xyz_control_count': len(cache['raw_control_points']), 'xyz_domain': domain,
                    'uv_degree': uv['degree'], 'uv_control_count': len(uv['raw_control_points']),
                    'support_kind': support['kind'], 'support_subtype': support.get('procedural_subtype'),
                    'stored_inline_ref': support.get('stored_inline_surface_ref'),
                    'stored_parameter_interval': cache['stored_parameter_interval'],
                    'stored_interval_flags': cache['stored_interval_flags'],
                    'five_xyz_and_five_uv_evaluations_finite': True})
    assert len(caches) == 226 and len(FAMILY_FILES) == 19
    assert sum(c['stored_wrapper_flag'] for c in caches.values()) == 26
    assert sum(c['is_rational'] for c in caches.values()) == 24
    direct_errors, uv_errors = [], []
    for relative in FOCUSED:
        truth = json.loads((ROOT / Path(relative).parent / 'ground_truth.json').read_text())
        actual = next(s for s in truth['samples'] if s['file'] == Path(relative).name)
        report['api_context'].append({'file': relative, 'fusion_version': truth['fusion_version'],
                                      'actual_settings': actual.get('settings'),
                                      'result_body_count': len(actual.get('result_bodies', [])) if 'result_bodies' in actual else None,
                                      'scope': 'Saved actual modeling context only; no API cache-evaluator agreement inferred.'})
        for member, parsed in load(relative).items():
            topology = decode_topology(parsed)
            nodes = {n['index']: n for n in topology['nodes']}
            for edge in nodes.values():
                key = (relative, member, edge.get('curve_index'))
                if edge['kind'] != 'edge' or key not in caches:
                    continue
                cache = caches[key]
                parameters = [edge['start_parameter'], edge['end_parameter']]
                vertices = [nodes[edge[which+'_vertex_index']] for which in ('start', 'end')]
                points = [nodes[v['point_index']] for v in vertices]
                assert all(v['kind'] == 'vertex' and p['kind'] == 'point' for v, p in zip(vertices, points))
                entry = {'file': relative, 'member': member, 'curve_index': key[2], 'edge_index': edge['index'],
                         'wrapper_flag': cache['stored_wrapper_flag'], 'xyz_cache_domain': cache['parameter_domain'],
                         'native_edge_parameters': parameters,
                         'endpoint_vertices': [{'vertex_index': v['index'], 'point_index': p['index'], 'raw_position': p['raw_origin']}
                                               for v, p in zip(vertices, points)], 'parent_uv_checks': []}
                if _inside(cache['parameter_domain'], parameters):
                    values = [evaluate_curve(cache, p) for p in parameters]
                    errors = [math.dist(a, b['raw_origin']) for a, b in zip(values, points)]
                    entry['direct_native_parameter_evaluation'] = {'raw_values': values, 'errors_raw': errors,
                                                                  'matches_within1e_8': max(errors) < 1e-8}
                    direct_errors.extend(errors)
                else:
                    entry['direct_native_parameter_evaluation'] = {'status': 'unresolved_parameter_correspondence',
                                                                  'reason': 'Native edge parameters lie outside cache domain; no remapping applied'}
                coedges = [c for c in nodes.values() if c['kind'] == 'coedge' and c['edge_index'] == edge['index']]
                for coedge in coedges:
                    loop = nodes.get(coedge['loop_index']); face = nodes.get(loop['face_index']) if loop else None
                    surface_node = nodes.get(face['surface_index']) if face else None
                    pcurve = nodes.get(coedge['pcurve_index'])
                    if not surface_node or not pcurve or 'bspline_surface' not in surface_node or 'uv_curve' not in pcurve:
                        continue
                    surface, uv = surface_node['bspline_surface'], pcurve['uv_curve']
                    # Compare the two independently stored cache domains by
                    # fractions for corroboration, without installing a mapping.
                    domain = cache['parameter_domain']; ud = uv['parameter_domain']
                    sample_errors = []
                    for fraction in (0, .25, .5, .75, 1):
                        xyz_parameter = domain[0]+(domain[1]-domain[0])*fraction
                        uv_parameter = ud[0]+(ud[1]-ud[0])*fraction
                        try:
                            value = evaluate_surface(surface, *evaluate_pcurve(uv, uv_parameter))
                        except ValueError:
                            sample_errors = []
                            break
                        sample_errors.append(math.dist(value, evaluate_curve(cache, xyz_parameter)))
                    if sample_errors:
                        uv_errors.extend(sample_errors)
                        entry['parent_uv_checks'].append({'coedge_index': coedge['index'], 'loop_index': loop['index'],
                                                         'face_index': face['index'], 'surface_index': surface_node['index'],
                                                         'pcurve_index': pcurve['index'],
                                                         'five_fractional_cache_deviations_raw': sample_errors,
                                                         'naive_fraction_alignment_matches_within1e_8': max(sample_errors) < 1e-8,
                                                         'scope': 'Independent-domain fractional counterexample probe only; full UV domain may extend beyond the trimmed edge. No persistent inline-ref or general parameter mapping inferred'})
                report['focused_geometry'].append(entry)
    # Stable previous cache controls, from snapshots predating these branches.
    controls = [next(c for c in OLD_CACHE_HASHES if c['file'].startswith('moretools') and c['index'] == 18),
                next(c for c in OLD_CACHE_HASHES if c['file'].startswith('splinepatches') and c['index'] == 11),
                next(c for c in OLD_CACHE_HASHES if c['file'].startswith('splines') and c['index'] == 18)]
    for control in controls:
        record = load(control['file'])[control['member']]['records'][control['index']]
        digest = hashlib.sha256(json.dumps(decode_bspline(record), sort_keys=True).encode()).hexdigest()
        assert digest == control['sha256']
        report['compatibility'].append(dict(control, unchanged=True))
    base_member, base_parsed = next((m, p) for m, p in load(FOCUSED[0]).items() if m.endswith('.smbh'))
    base = base_parsed['records'][37]
    def reject(label, record, mutate):
        changed = copy.deepcopy(record); mutate(changed['tokens'])
        try:
            decode_parameter_curve_cache(changed)
        except (ValueError, IndexError) as error:
            report['guards'].append({'case': label, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError('Malformed parameter cache accepted: '+label)
    reject('Unsupported XYZ form', base, lambda t: t[10].update(value=1))
    reject('Non-increasing compact XYZ knots', base, lambda t: t[14].update(value=t[12]['value']))
    reject('Negative inline support reference', base, lambda t: t[33].update(value=-1))
    reject('Second support must be null_surface', base, lambda t: t[39].update(value='unknown_surface'))
    reject('Unsupported embedded UV degree', base, lambda t: t[41].update(value=2))
    reject('Wrong literal procedural trailer flag', base, lambda t: t[59].update(value=False))
    rational_key = next(k for k, c in caches.items() if c['is_rational'])
    rational_record = load(rational_key[0])[rational_key[1]]['records'][rational_key[2]]
    weight_index = 12+2*rational_record['tokens'][11]['value']+3
    reject('Rational XYZ weight must be positive', rational_record, lambda t: t[weight_index].update(value=0.0))
    reject('Trailing unexpected field', base, lambda t: t.append({'kind': 'integer', 'value': 0}))
    report['summary'] = {'family_archives': len(FAMILY_FILES), 'decoded_parameter_curve_caches': len(caches),
                         'wrapper_false': sum(not c['stored_wrapper_flag'] for c in caches.values()),
                         'wrapper_true': sum(c['stored_wrapper_flag'] for c in caches.values()),
                         'rational_xyz_caches': sum(c['is_rational'] for c in caches.values()),
                         'polynomial_xyz_caches': sum(not c['is_rational'] for c in caches.values()),
                         'inline_sweep_supports': sum(c['stored_support_definition'].get('procedural_subtype') == 'sweep_sur' for c in caches.values()),
                         'focused_saved_files': len(FOCUSED), 'focused_typed_edges': len(report['focused_geometry']),
                         'direct_native_parameter_endpoint_evaluations': len(direct_errors),
                         'direct_native_endpoint_matches_within1e_8': sum(e < 1e-8 for e in direct_errors),
                         'unresolved_edge_parameter_correspondences': sum(e['direct_native_parameter_evaluation'].get('status') == 'unresolved_parameter_correspondence' for e in report['focused_geometry']),
                         'sampled_parent_uv_comparisons': len(uv_errors),
                         'maximum_direct_native_endpoint_error_raw': max(direct_errors) if direct_errors else None,
                         'maximum_sampled_parent_uv_deviation_raw': max(uv_errors) if uv_errors else None,
                         'malformed_guards': len(report['guards']), 'previous_cache_controls_unchanged': len(controls)}
    assert report['focused_geometry'] and direct_errors
    return report


# Explicit family-only archive inventory from the saved b6372ab diagnostic snapshot.
FAMILY_FILES = ['loftcompositeguides-8ea2ef593872/centerline_connected_chain.f3d',
 'loftcompositeguides-8ea2ef593872/centerline_explicit_members.f3d',
 'loftcompositeguides-8ea2ef593872/rail_line_arc.f3d',
 'loftcompositeguides-8ea2ef593872/spline_centerline.f3d',
 'loftcurvedguides-79a1266af54e/quarter_arc_centerline.f3d',
 'lofts-03b4a6f1ce2f/centerline.f3d',
 'pipepaths-3d11bd427946/spline_circular.f3d',
 'solidsweeps-5b5ecd5e01b9/solid_twist_sixty.f3d',
 'solidsweeps-7d2677669e3d/solid_aligned.f3d',
 'solidsweeps-7d2677669e3d/solid_twist.f3d',
 'specialfillets-d50f7a4f04e0/rule_asymmetric.f3d',
 'sweepguides-9887de71bf9e/rail_full_extents.f3d',
 'sweepguides-9887de71bf9e/rail_no_scaling.f3d',
 'sweepguides-9887de71bf9e/rail_scale.f3d',
 'sweepguides-9887de71bf9e/rail_stretch.f3d',
 'sweepoperations-62378e7c0294/guided_cut.f3d',
 'sweepoperations-62378e7c0294/rail_flip_false.f3d',
 'sweepoperations-62378e7c0294/rail_flip_true.f3d',
 'sweeps-5f87eff25e24/line_twist.f3d']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='parameter-curve-cache-decoding.json')
    args = parser.parse_args()
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    report = validate(str(zstd))
    Path(args.output).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], sort_keys=True))
