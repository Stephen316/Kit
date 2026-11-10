"""Focused framing and independent polynomial evaluation of sweep caches."""

import copy
import hashlib
import json
import math
from pathlib import Path

from asm_records import inspect_asm
from decode_brep import decode_topology
from decode_bspline import decode_bspline, evaluate_surface
from decode_sweep_surface_cache import decode_sweep_surface_cache
from fusion_archive import read_members
from validate_fillet_spline_caches import OLD_CACHE_HASHES

ROOT = Path(__file__).resolve().parent
FILES = (
    'pipepaths-3d11bd427946/spline_circular.f3d',
    'solidsweeps-5b5ecd5e01b9/solid_twist_sixty.f3d',
    'solidsweeps-7d2677669e3d/solid_aligned.f3d',
    'solidsweeps-7d2677669e3d/solid_twist.f3d',
    'sweepguides-9887de71bf9e/rail_full_extents.f3d',
    'sweepguides-9887de71bf9e/rail_no_scaling.f3d',
    'sweepguides-9887de71bf9e/rail_scale.f3d',
    'sweepguides-9887de71bf9e/rail_stretch.f3d',
    'sweepoperations-62378e7c0294/guided_cut.f3d',
    'sweepoperations-62378e7c0294/rail_flip_false.f3d',
    'sweepoperations-62378e7c0294/rail_flip_true.f3d',
    'sweeps-5f87eff25e24/line_twist.f3d',
)


def bernstein(value):
    s = 1-value
    return [s**3, 3*s*s*value, 3*s*value*value, value**3]


def independent(cache, ucell, vcell, s, t):
    """Direct 16-control bicubic Bernstein tensor on observed C0 cells."""
    a, b = bernstein(s), bernstein(t)
    nv, points = cache['control_count_v'], cache['raw_control_points']
    return [sum(a[i]*b[j]*points[(3*ucell+i)*nv+3*vcell+j][axis]
                for i in range(4) for j in range(4)) for axis in range(3)]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def validate(zstd):
    parsed_files, samples, checks, modes = {}, [], 0, {}
    maximum = 0.
    guard_source = None
    for filename in FILES:
        for member, blob in read_members(ROOT/filename, zstd).items():
            if not member.endswith(('.smb', '.smbh')):
                continue
            parsed = inspect_asm(blob)
            parsed_files[(filename, member)] = parsed
            # This pass uses independently typed parent links. Inline reference
            # expansion is tested separately, rather than selecting by position.
            nodes = {n['index']: n for n in decode_topology(parsed)['nodes']}
            for record in parsed['records']:
                ts = record['tokens']
                if (record['section'] != 'geometry' or record['name'] != 'spline-surface'
                        or len(ts) < 7 or ts[5]['value'] != 'sweep_sur'):
                    continue
                cache = decode_sweep_surface_cache(record)
                assert decode_bspline(record) == cache
                assert all(m == 3 for _, m in cache['stored_compact_knots_u']+cache['stored_compact_knots_v'])
                ucells = len(cache['stored_compact_knots_u'])-1
                vcells = len(cache['stored_compact_knots_v'])-1
                assert cache['control_count_u'] == 3*ucells+1 and cache['control_count_v'] == 3*vcells+1
                evaluations = []
                for ui, vi, s, t in ((0, 0, .25, .75), (ucells//2, vcells//2, .5, .5),
                                      (ucells-1, vcells-1, .75, .25)):
                    ku, kv = cache['stored_compact_knots_u'], cache['stored_compact_knots_v']
                    u = ku[ui][0]+s*(ku[ui+1][0]-ku[ui][0])
                    v = kv[vi][0]+t*(kv[vi+1][0]-kv[vi][0])
                    expected = independent(cache, ui, vi, s, t)
                    actual = evaluate_surface(cache, u, v)
                    error = math.dist(expected, actual)
                    assert error < 1e-10 and all(math.isfinite(x) for x in actual)
                    maximum = max(maximum, error)
                    checks += 1
                    evaluations.append({'cell': [ui, vi], 'uv': [u, v], 'independent_point': expected,
                                        'cache_point': actual, 'error_raw': error})
                mode = cache['stored_sweep_mode_code']
                modes[mode] = modes.get(mode, 0)+1
                faces = {n['index'] for n in nodes.values() if n['kind'] == 'face' and n['surface_index'] == record['index']}
                vertices = set()
                for c in nodes.values():
                    if c['kind'] != 'coedge' or c.get('loop_index') is None:
                        continue
                    loop = nodes[c['loop_index']]
                    if loop['face_index'] in faces:
                        edge = nodes[c['edge_index']]
                        vertices.update((edge['start_vertex_index'], edge['end_vertex_index']))
                unavailable = [v for v in vertices if v not in nodes or nodes[v]['point_index'] not in nodes]
                owned = [nodes[nodes[v]['point_index']]['raw_origin'] for v in vertices if v not in unavailable]
                corner_errors = [min(math.dist(evaluate_surface(cache, u, v), p) for p in owned)
                                 for u in cache['parameter_domain_u'] for v in cache['parameter_domain_v']] if owned else []
                samples.append({'file': filename, 'member': member, 'record_index': record['index'],
                    'mode_code': mode, 'control_grid': [cache['control_count_u'], cache['control_count_v']],
                    'parameter_domain_u': cache['parameter_domain_u'], 'parameter_domain_v': cache['parameter_domain_v'],
                    'cache_sha256': digest(cache), 'independent_evaluations': evaluations,
                    'typed_parent_face_indices': sorted(faces), 'owned_vertex_count': len(owned),
                    'unresolved_owned_vertex_indices': unavailable,
                    'full_cache_corner_distances_to_owned_vertices_raw': corner_errors,
                    'corner_scope': 'Diagnostics only: full cache-domain corners need not be trimmed face vertices; no coordinate match chooses ownership or trim limits.'})
                if guard_source is None:
                    guard_source = copy.deepcopy(record), cache
    controls = []
    for prior in OLD_CACHE_HASHES[:3]:
        key = (prior['file'], prior['member'])
        if key not in parsed_files:
            parsed_files[key] = inspect_asm(read_members(ROOT/prior['file'], zstd)[prior['member']])
        actual = decode_bspline(parsed_files[key]['records'][prior['index']])
        assert digest(actual) == prior['sha256']
        controls.append(dict(prior, unchanged=True))
    record, cache = guard_source
    grid_start = 3+len(cache['stored_procedural_definition'])
    mode_index = 27 if cache['stored_extra_profile_frame_flag'] else 25
    frame_index = 23 if cache['stored_extra_profile_frame_flag'] else 21
    controls_start = grid_start+9+2*(len(cache['stored_compact_knots_u'])+len(cache['stored_compact_knots_v']))
    guards = []
    for label, mutation in (
            ('Unobserved native mode', lambda ts: ts[mode_index].update(value=99)),
            ('Wrong frame token kind', lambda ts: ts[frame_index].update(kind='direction_vector')),
            ('Invalid grid degree', lambda ts: ts[grid_start+1].update(value=0)),
            ('Invalid compact multiplicity', lambda ts: ts[grid_start+10].update(value=0)),
            ('Nonfinite first grid control', lambda ts: ts[controls_start].update(value=math.nan)),
            ('Trailing field after complete bounds', lambda ts: ts.append(copy.deepcopy(ts[-1])))):
        changed = copy.deepcopy(record)
        mutation(changed['tokens'])
        try:
            decode_sweep_surface_cache(changed)
        except (ValueError, IndexError, KeyError) as error:
            guards.append({'case': label, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError(label)
    assert len(samples) == 96 and checks == 288
    return {'scope': 'Ninety-six initial sweep_sur cached surfaces across twelve saved archives; strict sequential wrapper framing and independent polynomial cache evaluation, without exact procedural reconstruction',
            'integration': {'helper': 'decode_sweep_surface_cache.decode_sweep_surface_cache(record)',
                            'inline_helper': 'decode_sweep_surface_inline(tokens,start,*,allow_true_wrapper=False)',
                            'dispatch': 'spline-surface / sweep_sur; inline True wrapper admitted only by an explicit observed support-role opt-in'},
            'samples': samples, 'compatibility': controls, 'guards': guards,
            'limitations': ['No direct Fusion API surface evaluator getter comparison is claimed.',
                           'Frames, expressions, mode codes, bounds, flags and cache scalar retain literal meanings; exact sweep construction and error bounds remain unresolved.',
                           'Full cache domains are distinct from actual face trims, edge parameters and current/final geometry.'],
            'summary': {'saved_files': len(FILES), 'surface_caches': len(samples), 'mode_counts': modes,
                        'independent_polynomial_evaluations': checks, 'maximum_evaluation_difference_raw': maximum,
                        'prior_cache_controls_unchanged': len(controls), 'malformed_guards': len(guards)}}


if __name__ == '__main__':
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    result = validate(str(zstd))
    (ROOT/'sweep-surface-cache-decoding.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['summary'], sort_keys=True))
