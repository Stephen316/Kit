"""Validate observed zero-slope negative-cosine ASM cylinder surfaces offline."""

import argparse
import copy
import json
import math
from pathlib import Path
import subprocess

from asm_records import inspect_asm
from decode_analytic import decode_analytic_surface
from decode_brep import decode_topology
from fusion_archive import read_members


def close(a, b):
    return math.isclose(a, b, abs_tol=1e-8, rel_tol=1e-8)


def validate(zstd, targets):
    # Compare only the previous analytic reader. Other topology work may evolve
    # independently, so previous successful field dictionaries are the control.
    previous_source = subprocess.check_output(
        ['git', 'show', '9f82351:decode_analytic.py'], text=True)
    namespace = {}
    exec(compile(previous_source, '9f82351:decode_analytic.py', 'exec'), namespace)
    previous = namespace['decode_analytic_surface']
    report = {'scope': 'Observed initial-geometry zero-slope negative-cosine cylinders only',
              'targets': targets, 'surfaces': [], 'unresolved': [], 'guards': [], 'API_controls': [],
              'limitations': ['No direct API surface getters were captured in these files.',
                              'Boundary points and independent Pipe dimension getters corroborate cylinder geometry, not persistent face identity.',
                              'Signed native parameter direction, UV evaluation, trimmed surface reconstruction and negative-cosine nonzero-slope cones remain unsupported.']}
    root = Path(__file__).resolve().parent
    old_successes, checked_points = 0, 0
    exemplar = None
    for relative in sorted({t['file'] for t in targets}):
        members = read_members(root / relative, zstd)
        for member in sorted({t['member'] for t in targets if t['file'] == relative}):
            parsed = inspect_asm(members[member])
            assert parsed['complete_token_stream'], relative
            topology = decode_topology(parsed)
            nodes = {n['index']: n for n in topology['nodes']}
            for record in parsed['records']:
                if record['section'] != 'geometry' or record['name'] not in ('cone-surface', 'sphere-surface', 'torus-surface'):
                    continue
                try:
                    old = previous(record)
                except (ValueError, KeyError, IndexError):
                    continue
                assert decode_analytic_surface(record) == old, (relative, record['index'])
                old_successes += 1
            for target in [t for t in targets if t['file'] == relative and t['member'] == member]:
                record = parsed['records'][target['index']]
                assert record['name'] == 'cone-surface'
                try:
                    geometry = decode_analytic_surface(record)
                except ValueError as error:
                    report['unresolved'].append({'file': relative, 'member': member,
                                                 'surface_index': record['index'], 'reason': str(error)})
                    continue
                assert geometry['kind'] == 'Cylinder'
                assert geometry['stored_cone_angular_pair'] == [target['sine'], target['cosine']] == [0., -1.]
                assert geometry['raw_origin'] == target['origin'] and geometry['axis'] == target['axis']
                assert close(geometry['raw_radius'], target['radius'])
                assert nodes[record['index']]['analytic_surface'] == geometry
                owned_faces = [n for n in nodes.values() if n['kind'] == 'face' and n['surface_index'] == record['index']]
                assert owned_faces
                surface_points = []
                for face in owned_faces:
                    for coedge in nodes.values():
                        if coedge['kind'] != 'coedge' or coedge.get('loop_index') is None:
                            continue
                        loop = nodes.get(coedge['loop_index'])
                        if not loop or loop.get('face_index') != face['index']:
                            continue
                        edge = nodes[coedge['edge_index']]
                        for key in ('start_vertex_index', 'end_vertex_index'):
                            if edge[key] is not None:
                                surface_points.append(nodes[nodes[edge[key]]['point_index']]['raw_origin'])
                for point in surface_points:
                    delta = [x-y for x, y in zip(point, geometry['raw_origin'])]
                    projection = sum(x*y for x, y in zip(delta, geometry['axis']))
                    radial_squared = sum(x*x for x in delta)-projection*projection
                    assert close(radial_squared, geometry['raw_radius']**2), (relative, record['index'], point)
                checked_points += len(surface_points)
                report['surfaces'].append({'file': relative, 'member': member,
                                           'surface_index': record['index'], 'geometry': geometry,
                                           'owning_face_indices': [f['index'] for f in owned_faces],
                                           'boundary_endpoint_occurrences_checked': len(surface_points),
                                           'scope': 'Raw initial cache geometry; no current/final face identity assigned'})
                exemplar = record
    assert len(report['surfaces'])+len(report['unresolved']) == len(targets)
    assert [(u['file'], u['surface_index'], u['reason']) for u in report['unresolved']] == [
        ('threadmodes-d51d2ae60564/internal.f3d', 10, 'Cone radius and reference vector length disagree')]
    # The independently captured Pipe getters distinguish section diameter and
    # wall thickness. Compare the unique inner cylindrical radius in each blob,
    # without identifying an API face or equating history with current state.
    relative = 'pipemodes-87cfa7d8d82b/hollow.f3d'
    truth = json.loads((root / Path(relative).parent / 'ground_truth.json').read_text())
    settings = next(s for s in truth['samples'] if s['file'] == Path(relative).name)['settings']
    assert settings['is_hollow'] is True
    expected_radius = settings['section_size_cm']/2-settings['section_thickness_cm']
    candidates = [s for s in report['surfaces'] if s['file'] == relative]
    assert len(candidates) == 2 and len({s['member'] for s in candidates}) == 2
    for s in candidates:
        assert close(s['geometry']['raw_radius'], expected_radius)
        report['API_controls'].append({'file': relative, 'member': s['member'],
                                       'saved_API_inner_radius_cm': expected_radius,
                                       'stored_radius_matches_API_section_dimensions': True,
                                       'direct_surface_getter_comparison': False})
    for label, index, value in [('nonunit angular pair', 10, -.5),
                                ('negative-cosine nonzero-slope cone', 9, .6),
                                ('nonpositive radius', 11, -1.),
                                ('unsupported elliptic ratio', 6, .5),
                                ('nonunit axis', 4, [0., 0., 2.]),
                                ('unknown prefix flag', 7, True)]:
        changed = copy.deepcopy(exemplar)
        changed['tokens'][index]['value'] = value
        if label == 'negative-cosine nonzero-slope cone':
            changed['tokens'][10]['value'] = -.8
        try:
            decode_analytic_surface(changed)
        except ValueError as error:
            report['guards'].append({'case': label, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError(label)
    report['summary'] = {'archives': len({t['file'] for t in targets}),
                         'recovered_surfaces': len(report['surfaces']),
                         'retained_unresolved_surfaces': len(report['unresolved']),
                         'boundary_endpoint_occurrences_checked': checked_points,
                         'previous_successful_analytic_outputs_unchanged': old_successes,
                         'API_dimension_comparisons': len(report['API_controls']),
                         'malformed_or_unsupported_guards': len(report['guards'])}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--targets', default='negative-cylinder-decoding.json')
    parser.add_argument('--output', default='negative-cylinder-decoding.json')
    parser.add_argument('--zstd-library')
    args = parser.parse_args()
    saved = json.loads(Path(args.targets).read_text())
    targets = saved['targets'] if isinstance(saved, dict) else saved
    zstd = args.zstd_library or next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    report = validate(zstd, targets)
    Path(args.output).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], sort_keys=True))
