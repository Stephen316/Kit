"""Independent rational Bernstein and typed-boundary checks for sum caches."""

import copy
import hashlib
import json
import math
from pathlib import Path

from asm_records import inspect_asm
from decode_brep import decode_topology
from decode_bspline import decode_bspline, evaluate_surface
from decode_pcurve import evaluate_pcurve
from decode_sum_surface_cache import decode_sum_surface_cache
from fusion_archive import read_members

ROOT = Path(__file__).resolve().parent
FILE = 'solidsweeps-7d2677669e3d/solid_rigid.f3d'


def independent_grid(ts, fu, fv):
    """Use source U-fast weighted controls and explicit linear/quadratic basis."""
    bu, bv = [1-fu, fu], [(1-fv)**2, 2*fv*(1-fv), fv*fv]
    numerator, denominator = [0., 0., 0.], 0.
    for v in range(3):
        for u in range(2):
            start = 39+4*(2*v+u)
            weight = ts[start+3]['value']
            factor = bu[u]*bv[v]*weight
            denominator += factor
            for axis in range(3):
                numerator[axis] += factor*ts[start+axis]['value']
    return [value/denominator for value in numerator]


def validate(zstd):
    truth = json.loads((ROOT/Path(FILE).parent/'ground_truth.json').read_text())
    sample = next(row for row in truth['samples'] if row['file'] == 'solid_rigid.f3d')
    source_path, = sample['requested']['path']['entities']
    report = {'scope': 'Four observed line/ellipse sum-surface grids in two saved rigid-sweep blobs; no live Fusion access',
              'file': FILE, 'records': [], 'typed_boundaries': [], 'guards': [],
              'source_path_getters': {k: source_path[k] for k in ('kind', 'center_world_cm', 'radius_cm', 'normal', 'start_world_cm', 'end_world_cm')},
              'limitations': ['Independent cache evaluation and saved source-arc getters do not establish an exact procedural sum-surface evaluator.',
                             'The rational V coordinate is not equated with the angular ellipse parameter; measured interior differences are retained.',
                             'Typed owning-face/loop/coedge links establish boundary context. Pcurve wrapper signs and a general coedge parameter map remain unresolved.',
                             'All points remain in raw ASM coordinates. No API result-surface evaluator getter was captured.']}
    records, errors, endpoint_errors, angular_differences = [], [], [], []
    for member, raw in read_members(ROOT/FILE, zstd).items():
        if not member.endswith(('.smb', '.smbh')):
            continue
        parsed = inspect_asm(raw)
        topology = decode_topology(parsed)
        nodes = {node['index']: node for node in topology['nodes']}
        targets = [r for r in parsed['records'] if r['section'] == 'geometry' and r['name'] == 'spline-surface'
                   and len(r['tokens']) > 5 and r['tokens'][5]['value'] == 'sum_spl_sur']
        assert len(targets) == 2 and not topology['unresolved']
        for record in targets:
            cache = decode_sum_surface_cache(record)
            assert decode_bspline(record) == cache
            records.append(record)
            line, ellipse = cache['stored_line_support'], cache['stored_ellipse_support']
            assert ellipse['raw_center'] == source_path['center_world_cm']
            assert math.isclose(math.dist(ellipse['raw_major_axis'], [0., 0., 0.]), source_path['radius_cm'], abs_tol=1e-12)
            ua, ub = cache['parameter_domain_u']; va, vb = cache['parameter_domain_v']
            checks = []
            for fu, fv in ((.2, .2), (.5, .5), (.8, .8)):
                u, v = ua+fu*(ub-ua), va+fv*(vb-va)
                actual = evaluate_surface(cache, u, v)
                expected = independent_grid(record['tokens'], fu, fv)
                error = math.dist(actual, expected); errors.append(error)
                assert error < 1e-12
                # Source construction corroboration: translation follows the
                # stored circle locus and the U line, without assuming V angle.
                zero_v = evaluate_surface(cache, u, va)
                line_point = [o+u*d for o, d in zip(line['raw_origin'], line['raw_direction'])]
                assert math.dist(zero_v, line_point) < 1e-12
                path_point = [a-b+s for a, b, s in zip(actual, line_point, source_path['start_world_cm'])]
                radial = [a-b for a, b in zip(path_point, source_path['center_world_cm'])]
                assert abs(math.dist(radial, [0., 0., 0.])-source_path['radius_cm']) < 1e-12
                assert abs(path_point[2]) < 1e-12
                angle = math.atan2(radial[0], -radial[1])
                angular_differences.append(abs(angle-v))
                checks.append({'u': u, 'v': v, 'raw_point': actual, 'independent_raw_point': expected,
                               'independent_error_raw': error, 'source_locus_angle': angle, 'angle_minus_cache_v': angle-v})
            endpoint_displacement = [b-a for a, b in zip(source_path['start_world_cm'], source_path['end_world_cm'])]
            assert math.dist([a-b for a, b in zip(evaluate_surface(cache, ua, vb), evaluate_surface(cache, ua, va))], endpoint_displacement) < 1e-12
            report['records'].append({'member': member, 'record_index': record['index'],
                                      'cache_sha256': hashlib.sha256(json.dumps(cache, sort_keys=True).encode()).hexdigest(),
                                      'degrees': [1, 2], 'counts': [2, 3], 'domain_u': [ua, ub], 'domain_v': [va, vb],
                                      'stored_rational_axis': 'v', 'independent_checks': checks})
            face, = [n for n in nodes.values() if n['kind'] == 'face' and n['surface_index'] == record['index']]
            loops = [loop for graph in topology['body_graphs'] for loop in graph['face_trim_loops'] if loop['face_index'] == face['index']]
            loop, = loops
            assert len(loop['trims']) == 4
            for trim in loop['trims']:
                uv = trim['uv_curve']; assert uv is not None
                positions = [evaluate_surface(cache, *evaluate_pcurve(uv, t)) for t in uv['parameter_domain']]
                edge = nodes[trim['edge_index']]
                endpoints = [nodes[nodes[edge[k]]['point_index']]['raw_origin'] for k in ('start_vertex_index', 'end_vertex_index')]
                error = min(max(math.dist(a, b) for a, b in zip(positions, order)) for order in (endpoints, endpoints[::-1]))
                assert error < 1e-12
                endpoint_errors.append(error)
                report['typed_boundaries'].append({'member': member, 'surface_index': record['index'],
                    'face_index': face['index'], 'loop_index': loop['loop_index'], 'coedge_index': trim['coedge_index'],
                    'edge_index': edge['index'], 'pcurve_index': trim['pcurve_index'], 'endpoint_set_error_raw': error,
                    'scope': 'Exact stored topology route, with unordered endpoint corroboration; no sign-based parameter map'})
    assert len(records) == 4 and len(endpoint_errors) == 16
    assert max(angular_differences) > .001
    def reject(label, mutate):
        changed = copy.deepcopy(records[0]); mutate(changed['tokens'])
        try:
            decode_sum_surface_cache(changed)
        except (ValueError, IndexError) as error:
            report['guards'].append({'case': label, 'reason': str(error)})
        else:
            raise AssertionError('Unsupported sum cache accepted: '+label)
    reject('Unsupported rational axis flag', lambda t: t[24].update(value='both'))
    reject('V-only weights disagree along U', lambda t: t[46].update(value=2.))
    reject('Nonfinite support vector', lambda t: t[9].update(value=[float('nan'), 0., 1.]))
    reject('Non-increasing compact U knots', lambda t: t[33].update(value=t[31]['value']))
    reject('Missing outer interval field', lambda t: t.pop())
    report['summary'] = {'saved_files': 1, 'blobs': 2, 'surface_caches': len(records),
                         'independent_tensor_evaluations': len(errors), 'maximum_independent_error_raw': max(errors),
                         'typed_boundary_chains': len(endpoint_errors), 'typed_endpoint_positions': 2*len(endpoint_errors),
                         'maximum_typed_endpoint_set_error_raw': max(endpoint_errors),
                         'maximum_angle_vs_rational_v_difference': max(angular_differences), 'malformed_guards': len(report['guards']),
                         'new_API_calls': 0}
    return report


if __name__ == '__main__':
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    result = validate(str(zstd))
    (ROOT/'sum-surface-cache-decoding.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['summary'], sort_keys=True))
