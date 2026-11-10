"""Signed torus fields corroborated by owned boundary incidence and API radius."""

import copy
import json
import math
from pathlib import Path

from asm_records import inspect_asm
from decode_analytic import decode_analytic_surface
from decode_brep import decode_topology
from fusion_archive import read_members

ROOT = Path(__file__).resolve().parent
FILE = 'specialfillets-d50f7a4f04e0/rule_all_both.f3d'


def validate(zstd):
    truth = json.loads((ROOT/Path(FILE).parent/'ground_truth.json').read_text())
    api = next(s for s in truth['samples'] if s['file'] == Path(FILE).name)['actual_rule']['radius']
    rows, guards, originals = [], [], []
    for member, raw in read_members(ROOT/FILE, zstd).items():
        if not member.endswith(('.smb', '.smbh')):
            continue
        parsed = inspect_asm(raw); topology = decode_topology(parsed)
        nodes = {n['index']: n for n in topology['nodes']}
        for record in parsed['records']:
            if record['section'] != 'geometry' or record['name'] != 'torus-surface' or record['tokens'][6]['value'] >= 0:
                continue
            originals.append(record)
            geometry = decode_analytic_surface(record)
            assert nodes[record['index']]['analytic_surface'] == geometry
            radius = geometry['derived_tube_radius_magnitude']
            assert math.isclose(radius, api['value'], abs_tol=1e-12)
            assert geometry['raw_minor_radius'] == -radius
            face, = [n for n in nodes.values() if n['kind'] == 'face' and n['surface_index'] == record['index']]
            loops = [lo for graph in topology['body_graphs'] for lo in graph['face_trim_loops'] if lo['face_index'] == face['index']]
            loop, = loops
            checks = []
            for trim in loop['trims']:
                edge = nodes[trim['edge_index']]
                for key in ('start_vertex_index', 'end_vertex_index'):
                    vertex = nodes[edge[key]]
                    point = nodes[vertex['point_index']]['raw_origin']
                    delta = [a-b for a, b in zip(point, geometry['raw_origin'])]
                    height = sum(a*b for a, b in zip(delta, geometry['axis']))
                    radial = math.sqrt(max(0., sum(x*x for x in delta)-height*height))
                    observed = math.hypot(radial-geometry['raw_major_radius'], height)
                    error = abs(observed-radius)
                    assert error < 1e-12
                    checks.append({'coedge_index': trim['coedge_index'], 'edge_index': edge['index'],
                                   'vertex_index': vertex['index'], 'point_index': vertex['point_index'],
                                   'tube_locus_residual_raw': error})
            rows.append({'member': member, 'record_index': record['index'], 'face_index': face['index'],
                         'loop_index': loop['loop_index'], 'geometry': geometry, 'boundary_checks': checks})
    assert len(rows) == 4
    for label, mutate in (
        ('Zero minor radius', lambda t: t[6].update(value=0.)),
        ('Magnitude exceeds major radius', lambda t: t[6].update(value=-1.)),
        ('Nonfinite signed field', lambda t: t[6].update(value=float('nan'))),
        ('Nonorthogonal axes', lambda t: t[7].update(value=t[4]['value'])),
        ('Unsupported extra trailer', lambda t: t.append(copy.deepcopy(t[-1])))):
        record = copy.deepcopy(originals[0]); mutate(record['tokens'])
        try:
            decode_analytic_surface(record)
        except (ValueError, IndexError) as error:
            guards.append({'case': label, 'reason': str(error)})
        else:
            raise AssertionError('Unsupported signed torus accepted: '+label)
    return {'scope': 'Four observed negative-minor-radius torus fields in one saved Rule Fillet history blob',
            'file': FILE, 'saved_actual_API_rule_radius_parameter': api, 'records': rows, 'guards': guards,
            'summary': {'surface_records': len(rows), 'typed_boundary_endpoint_occurrences': sum(len(r['boundary_checks']) for r in rows),
                        'maximum_tube_locus_residual_raw': max(c['tube_locus_residual_raw'] for r in rows for c in r['boundary_checks']),
                        'malformed_guards': len(guards), 'new_API_calls': 0},
            'limitations': ['The signed minor field is retained; its orientation/UV parameterization meaning remains unresolved.',
                           'An implicit tube-locus check does not establish a surface parameter map or direct API surface evaluator equivalence.',
                           'API Rule radius corroborates magnitude in this fixture; full feature causality and final face identity are not inferred.',
                           'Spindle/horn tori, signed major radii, native writing and regeneration remain unsupported.']}


if __name__ == '__main__':
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    report = validate(str(zstd))
    (ROOT/'signed-torus-decoding.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], sort_keys=True))
