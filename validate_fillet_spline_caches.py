"""Focused cache framing, typed endpoint and old spline compatibility checks."""

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

from asm_records import inspect_asm
from decode_brep import decode_topology
from decode_bspline import decode_bspline, evaluate_curve, evaluate_surface
from decode_pcurve import evaluate_pcurve
from fusion_archive import read_members

ROOT = Path(__file__).resolve().parent
TARGET = 'edgemodes-52695761f185/fillet_curvature.f3d'
HOLDOUTS = ['edgemodes-87edbf67527b/fillet_chord.f3d',
            'edgemodes-87edbf67527b/fillet_asymmetric.f3d']


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def distance(a, b):
    return math.sqrt(sum((x-y)**2 for x, y in zip(a, b)))


def validate(zstd_library):
    parsed_files = {}

    def load(relative):
        if relative not in parsed_files:
            parsed_files[relative] = {m: inspect_asm(raw) for m, raw in
                                      read_members(ROOT / relative, zstd_library).items()
                                      if m.endswith(('.smb', '.smbh'))}
        return parsed_files[relative]

    report = {
        'scope': 'Observed stored G2-blend surface and planar/spline-supported intersection-curve caches; exact procedural geometry is unresolved',
        'integration': {'entrypoint': 'decode_bspline.decode_bspline(record)',
                        'helper': 'decode_fillet_spline_caches.decode_g2_blend_surface_cache / decode_intersection_curve_cache',
                        'dispatch': 'Only spline-surface/g2_blend_spl_sur and intcurve-curve/int_int_cur use the new strict branches; prior branches remain exact',
                        'validation_command': '/usr/bin/python3 validate_fillet_spline_caches.py'},
        'native_framing': {
            'surface': 'Boolean True wrapper; g2_blend_spl_sur23100; two explicit planar blend_support_surface descriptions; straight spine; exact bounded prefix; non-rational degree4/3 tensor cache at token62; counted knots/control grid and six scalar lists; bounded trailer/intervals.',
            'curve': 'Boolean False wrapper; int_int_cur23100 enum0; clamped cubic XYZ NUBS; spline/ref support; explicit plane; separate clamped cubic UV NUBS; nullbs; four scalar lists and exact outer terminator.',
            'reference_namespace': 'Inline ref0 is stored literally. No entity-index, surface identity, persistent topology or body correspondence is inferred from it.'},
        'api_evidence': {}, 'samples': [], 'compatibility': [], 'guards': [],
        'limitations': [
            'API truth captured fillet controls only; no independent API surface grid/evaluator getters exist in these fixtures.',
            'Cached surface/curves are approximations. Endpoint agreement and finite sample grids are internal stored-geometry corroboration, not a global error bound or proof of exact G2 continuity.',
            'The surface wrapper flag and curve support flags remain uninterpreted. No coordinate reversal, sense, active/final lifecycle or current placement is inferred.',
            'Surface cache V domain extends beyond its stored trim interval. Exact trimmed-face reconstruction and procedural support definitions remain unresolved.',
            'Only the observed planar-support G2 blend surface and cubic XYZ/UV intersection layout are supported; spring_int_cur and srf_srf_v_bl_spl_sur remain unresolved.',
            'Only raw ASM coordinates are evaluated; component placements, units/context and regeneration are not applied.'
        ]}
    truth = json.loads((ROOT / 'edgemodes-52695761f185/ground_truth.json').read_text())
    actual = next(s for s in truth['samples'] if s['file'] == 'fillet_curvature.f3d')['settings']
    edge_set, = actual['edge_sets']
    assert edge_set['continuity'] == 2 and edge_set['tangencyWeight']['value'] == .75
    report['api_evidence'] = {'source': 'edgemodes-52695761f185/ground_truth.json',
                              'fusion_version': truth['fusion_version'], 'actual_settings': actual,
                              'surface_evaluator_getters_captured': False,
                              'settings_corroboration': 'Native blend prefix has two literal0.75 scalars and two literal-0.2 scalars, corroborating captured tangencyWeight0.75/radius0.2; no general field semantics assigned from one surface.'}
    sample_counts = {'surface_caches': 0, 'intersection_curve_caches': 0,
                     'typed_curve_endpoint_checks': 0, 'surface_uv_endpoint_checks': 0}
    for relative in [TARGET]+HOLDOUTS:
        member, parsed = next((m, p) for m, p in load(relative).items() if m.endswith('.smbh'))
        assert parsed['complete_token_stream']
        records = parsed['records']
        topology = decode_topology(parsed)
        nodes = {n['index']: n for n in topology['nodes']}
        sample = {'file': relative, 'member': member, 'curves': [],
                  'remaining_unresolved': topology['unresolved']}
        if relative == TARGET:
            assert not topology['unresolved']
            surface = nodes[10]['bspline_surface']
            assert (surface['degree_u'], surface['degree_v'], surface['control_count_u'], surface['control_count_v']) == (4, 3, 6, 11)
            assert len(surface['raw_control_points']) == 66
            assert surface['stored_parameter_interval_v'] == [-.75, 2.25]
            grid = [evaluate_surface(surface, u, v)
                    for u in [i/4 for i in range(5)]
                    for v in [-.75+3*i/4 for i in range(5)]]
            assert all(math.isfinite(c) for point in grid for c in point)
            sample['surface'] = {'record_index': 10, 'record_offset': records[10]['offset'],
                                 'degree_u': 4, 'degree_v': 3, 'control_grid': [6, 11],
                                 'compact_knots_u': surface['stored_compact_knots_u'],
                                 'compact_knots_v': surface['stored_compact_knots_v'],
                                 'cache_domain_u': surface['parameter_domain_u'],
                                 'cache_domain_v': surface['parameter_domain_v'],
                                 'stored_trim_u': surface['stored_parameter_interval_u'],
                                 'stored_trim_v': surface['stored_parameter_interval_v'],
                                 'finite_grid_evaluations': len(grid), 'grid_samples': grid,
                                 'procedural_definition_preserved': surface['stored_procedural_definition'],
                                 'body_graph_exposes_cache': any(any(s['surface_index'] == 10 for s in g['spline_surfaces']) for g in topology['body_graphs'])}
            sample_counts['surface_caches'] += 1
        for edge in nodes.values():
            if edge['kind'] != 'edge' or edge['curve_index'] not in (42, 79):
                continue
            cache = nodes[edge['curve_index']]['bspline_curve']
            assert cache['procedural_subtype'] == 'int_int_cur'
            domain = cache['parameter_domain']
            curve_check = {'curve_index': edge['curve_index'], 'edge_index': edge['index'],
                           'control_count': len(cache['raw_control_points']),
                           'uv_control_count': len(cache['stored_embedded_uv_cache']['raw_control_points']),
                           'compact_knots': cache['stored_compact_knots'],
                           'support_flag': cache['stored_support_surface_flag'],
                           'inline_support_ref': cache['stored_inline_surface_ref'], 'endpoints': []}
            for which, parameter in zip(('start', 'end'), (edge['start_parameter'], edge['end_parameter'])):
                vertex = nodes[edge[which+'_vertex_index']]
                point = nodes[vertex['point_index']]
                assert vertex['kind'] == 'vertex' and point['kind'] == 'point'
                actual_point = point['raw_origin']
                evaluated = evaluate_curve(cache, parameter)
                error = distance(evaluated, actual_point)
                assert error < 1e-9
                curve_check['endpoints'].append({'vertex_index': vertex['index'], 'point_index': point['index'],
                                                'parameter': parameter, 'stored_point': actual_point,
                                                'cache_evaluation': evaluated, 'error_raw': error})
                sample_counts['typed_curve_endpoint_checks'] += 1
            assert all(math.isfinite(v) for k in range(5)
                       for v in evaluate_curve(cache, domain[0]+(domain[1]-domain[0])*k/4))
            if relative == TARGET:
                coedges = [c for c in nodes.values() if c['kind'] == 'coedge'
                           and c['edge_index'] == edge['index']
                           and nodes[nodes[c['loop_index']]['face_index']]['surface_index'] == 10]
                coedge, = coedges
                uv = nodes[coedge['pcurve_index']]['uv_curve']
                errors = []
                for k in range(5):
                    parameter = domain[0]+(domain[1]-domain[0])*k/4
                    surface_point = evaluate_surface(surface, *evaluate_pcurve(uv, parameter))
                    errors.append(distance(surface_point, evaluate_curve(cache, parameter)))
                assert max(errors[0], errors[-1]) < 1e-9
                curve_check['typed_coedge_surface_chain'] = {
                    'coedge_index': coedge['index'], 'loop_index': coedge['loop_index'],
                    'face_index': nodes[coedge['loop_index']]['face_index'],
                    'surface_index': 10, 'pcurve_index': coedge['pcurve_index'],
                    'five_sample_cache_cross_deviations_raw': errors,
                    'scope': 'Independent coedge/loop/face links establish the parent surface; inline ref0 is not used as an index. Interior cache differences are retained, with no error bound inferred.'}
                sample_counts['surface_uv_endpoint_checks'] += 2
            sample['curves'].append(curve_check)
            sample_counts['intersection_curve_caches'] += 1
        assert len(sample['curves']) == 2
        if relative != TARGET:
            assert records[10]['tokens'][5]['value'] == 'srf_srf_v_bl_spl_sur'
            assert any(u['index'] == 10 for u in topology['unresolved'])
        report['samples'].append(sample)
    for previous in OLD_CACHE_HASHES:
        record = load(previous['file'])[previous['member']]['records'][previous['index']]
        actual_hash = digest(decode_bspline(record))
        assert actual_hash == previous['sha256']
        report['compatibility'].append(dict(previous, unchanged=True))
    target_records = next(p['records'] for m, p in load(TARGET).items() if m.endswith('.smbh'))
    def rejected(label, index, mutate):
        record = copy.deepcopy(target_records[index]); mutate(record['tokens'])
        try:
            decode_bspline(record)
        except (ValueError, IndexError) as error:
            report['guards'].append({'case': label, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError('Malformed record accepted: '+label)
    rejected('Surface true-wrapper changed', 10, lambda t: t[3].update(value=False))
    rejected('Surface support marker changed', 10, lambda t: t[9].update(value='unknown_support'))
    rejected('Surface nonfinite control', 10, lambda t: t[87].update(value=float('nan')))
    rejected('Surface non-increasing knots', 10, lambda t: t[73].update(value=0.0))
    rejected('Surface trailing data', 10, lambda t: t.append({'kind': 'integer', 'value': 0}))
    rejected('Curve negative inline support reference', 42, lambda t: t[65].update(value=-1))
    rejected('Curve invalid UV knot multiplicity', 42, lambda t: t[85].update(value=4))
    rejected('Curve truncated subtype terminator', 42, lambda t: t.__delitem__(135))
    report['summary'] = dict(sample_counts, prior_cache_outputs_unchanged=len(report['compatibility']),
                             malformed_guards=len(report['guards']), saved_files=3,
                             unknown_surface_wrappers_retained=2)
    return report


# SHA256 snapshots taken from the unmodified decoder before adding either branch.
OLD_CACHE_HASHES = [{'file': 'moretools-380212ab6368/LoftThreeSections.f3d',
  'member': 'FusionAssetName[Active]/Breps.BlobParts/BREP.6c02db9b-cfd5-447b-b1a3-d82b5aa7b12d.smbh',
  'index': 18,
  'sha256': '7990268eedf02ff8e50431366dfbcb00038a19feb8cb553179572eb4cbf03f64'},
 {'file': 'moretools-380212ab6368/LoftThreeSections.f3d',
  'member': 'FusionAssetName[Active]/Breps.BlobParts/BREP.6c02db9b-cfd5-447b-b1a3-d82b5aa7b12d.smbh',
  'index': 37,
  'sha256': '6b5fba3a948316c29e7cfd30fb6b76be9d5831941b1812079364f941683118de'},
 {'file': 'moretools-380212ab6368/LoftThreeSections.f3d',
  'member': 'FusionAssetName[Active]/Breps.BlobParts/BREP.d02c452f-94a9-468c-b988-446c3ac61293.smb',
  'index': 60,
  'sha256': 'ec33f4330f41b0a3e8e332d4a43255c16e1e31e96b7b12e045b98b6239b18999'},
 {'file': 'moretools-380212ab6368/LoftThreeSections.f3d',
  'member': 'FusionAssetName[Active]/Breps.BlobParts/BREP.d02c452f-94a9-468c-b988-446c3ac61293.smb',
  'index': 115,
  'sha256': 'bbd20392853516200c9245d1abac07daaae1d4ad1eea413035b5b6d2e5f1357c'},
 {'file': 'splines-9a18bae21127/splines.f3d',
  'member': 'FusionAssetName[Active]/Breps.BlobParts/BREP.6b3a0333-d53f-4a1e-a46d-fff522ed1067.smb',
  'index': 18,
  'sha256': 'af399015765251db012aed77367c4d9f844c8f1ad59204fd8bc3a9b3963e755f'},
 {'file': 'splines-9a18bae21127/splines.f3d',
  'member': 'FusionAssetName[Active]/Breps.BlobParts/BREP.6b3a0333-d53f-4a1e-a46d-fff522ed1067.smb',
  'index': 23,
  'sha256': 'c9b7abd94e566afc1c52df79ee6687c4f610b8c1d94204e9bf82871d59e884f8'},
 {'file': 'splines-9a18bae21127/splines.f3d',
  'member': 'FusionAssetName[Active]/Breps.BlobParts/BREP.6b3a0333-d53f-4a1e-a46d-fff522ed1067.smb',
  'index': 27,
  'sha256': '8c4e742da18759e0afc8ac9ca624d9e17772341a2ccc7e11e2ad9916c7de1c58'},
 {'file': 'splinepatches-ac5e846e59c0/splinepatches.f3d',
  'member': 'FusionAssetName[Active]/Breps.BlobParts/BREP.ce4d73fa-1614-40c4-b2a0-86d90f5b97f1.smb',
  'index': 11,
  'sha256': '77d79818f1a04079e17d7796f6005032d3b74d88b946b4690acf74144bf48682'},
 {'file': 'splinepatches-ac5e846e59c0/splinepatches.f3d',
  'member': 'FusionAssetName[Active]/Breps.BlobParts/BREP.ce4d73fa-1614-40c4-b2a0-86d90f5b97f1.smb',
  'index': 14,
  'sha256': 'ff001ebb966b1dbe67c80e62755d796490fbdc11373e099cfd26488ae3f7e99d'},
 {'file': 'splinepatches-ac5e846e59c0/splinepatches.f3d',
  'member': 'FusionAssetName[Active]/Breps.BlobParts/BREP.ce4d73fa-1614-40c4-b2a0-86d90f5b97f1.smb',
  'index': 47,
  'sha256': '0ed32fe40733d193e47c2dee6e1f4fbc0240fd904c0d0af838f02c8aa46e3e0c'},
 {'file': 'splinepatches-ac5e846e59c0/splinepatches.f3d',
  'member': 'FusionAssetName[Active]/Breps.BlobParts/BREP.ce4d73fa-1614-40c4-b2a0-86d90f5b97f1.smb',
  'index': 50,
  'sha256': 'ae80c928f9dd9b025a3c2786c445d897d7f4195f5e5267c09174fabb5e26b3f8'},
 {'file': 'splinepatches-ac5e846e59c0/splinepatches.f3d',
  'member': 'FusionAssetName[Active]/Breps.BlobParts/BREP.ce4d73fa-1614-40c4-b2a0-86d90f5b97f1.smb',
  'index': 68,
  'sha256': '60cb102f5a656eb215af62a3eddf963343c72c6dbc6491e5fd02a1dcaaa7076e'},
 {'file': 'splinepatches-ac5e846e59c0/splinepatches.f3d',
  'member': 'FusionAssetName[Active]/Breps.BlobParts/BREP.87a3aee2-5c8c-4441-b151-2d20d05d857f.smbh',
  'index': 15,
  'sha256': '573865516b139f022400ddac8df45d5e9e6f7a4688cda3da3f48342538a1a7aa'},
 {'file': 'splinepatches-ac5e846e59c0/splinepatches.f3d',
  'member': 'FusionAssetName[Active]/Breps.BlobParts/BREP.87a3aee2-5c8c-4441-b151-2d20d05d857f.smbh',
  'index': 18,
  'sha256': '2b271b3d1643cee111c1b2e50cdcf470df6d02e7a2bf1a14940f887e9d072211'},
 {'file': 'splinepatches-ac5e846e59c0/splinepatches.f3d',
  'member': 'FusionAssetName[Active]/Breps.BlobParts/BREP.87a3aee2-5c8c-4441-b151-2d20d05d857f.smbh',
  'index': 51,
  'sha256': '29a51b381d250fb8bf8efa6ab6ddd6a97058560e9850ab1074fabe50f60f340a'},
 {'file': 'splinepatches-ac5e846e59c0/splinepatches.f3d',
  'member': 'FusionAssetName[Active]/Breps.BlobParts/BREP.87a3aee2-5c8c-4441-b151-2d20d05d857f.smbh',
  'index': 54,
  'sha256': '89864751221ef48c586620c4a6046439ed7abb8238ad489f83caef3df4a8f8f8'},
 {'file': 'splinepatches-ac5e846e59c0/splinepatches.f3d',
  'member': 'FusionAssetName[Active]/Breps.BlobParts/BREP.87a3aee2-5c8c-4441-b151-2d20d05d857f.smbh',
  'index': 72,
  'sha256': 'c1fadfc5317239eece88c7343114ced63d5f71756872421573dea2f5dc47e49e'}]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='fillet-spline-cache-decoding.json')
    args = parser.parse_args()
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    report = validate(str(zstd))
    Path(args.output).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], sort_keys=True))
