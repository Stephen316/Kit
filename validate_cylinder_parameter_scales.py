"""Independent saved ThreadInfo and boundary controls for resized cylinders."""

import copy
import json
import math
from pathlib import Path
import subprocess

from asm_records import inspect_asm
from decode_analytic import decode_analytic_surface
from decode_basics import decode_basics
from decode_brep import decode_topology
from fusion_archive import read_members


def validate(zstd):
    root = Path(__file__).resolve().parent
    namespace = {}
    source = subprocess.check_output(['git', 'show', '9446c2d:decode_analytic.py'], text=True)
    exec(compile(source, '9446c2d:decode_analytic.py', 'exec'), namespace)
    old = namespace['decode_analytic_surface']
    report = {'scope': 'Nine observed Thread caches distinguish physical base-ellipse radius from independently stored U parameter scale',
              'samples': [], 'limitations': ['ThreadInfo dimensions corroborate the physical radius; direct API cylinder-surface getters were not captured.',
                  'Initial cached surfaces are not universally final visible surfaces. UV evaluation, other thread topology and regeneration remain partial.']}
    for folder in ['threadmodes-9574579d310b', 'threadmodes-6b6a0a9b4a69', 'threadmodes-d51d2ae60564']:
        truth = json.loads((root / folder / 'ground_truth.json').read_text())
        for sample in truth['samples']:
            relative = folder+'/'+sample['file']
            settings = sample['settings']
            expected = settings['minor_diameter_cm' if settings['is_internal'] else 'major_diameter_cm']/2
            members = read_members(root / relative, zstd)
            found = []
            for member, blob in members.items():
                if not member.endswith('.smbh'):
                    continue
                parsed = inspect_asm(blob)
                topology = decode_topology(parsed)
                nodes = {n['index']: n for n in topology['nodes']}
                for record in parsed['records']:
                    if record['name'] != 'cone-surface' or record['section'] != 'geometry':
                        continue
                    try:
                        old(record)
                    except ValueError as error:
                        if str(error) != 'Cone radius and reference vector length disagree':
                            continue
                    else:
                        continue
                    geometry = decode_analytic_surface(record)
                    assert geometry['kind'] == 'Cylinder'
                    assert math.isclose(geometry['raw_radius'], expected, abs_tol=1e-10)
                    assert math.isclose(geometry['stored_u_parameter_scale'], .6, abs_tol=1e-12)
                    assert not math.isclose(geometry['raw_radius'], geometry['stored_u_parameter_scale'], abs_tol=1e-5)
                    assert geometry['is_u_reversed'] is False and 'is_v_reversed' not in geometry
                    faces = {n['index'] for n in nodes.values() if n['kind'] == 'face' and n['surface_index'] == record['index']}
                    endpoints = []
                    for coedge in nodes.values():
                        if coedge['kind'] != 'coedge' or nodes.get(coedge['loop_index'], {}).get('face_index') not in faces:
                            continue
                        edge = nodes[coedge['edge_index']]
                        for key in ('start_vertex_index', 'end_vertex_index'):
                            if edge[key] is not None:
                                endpoints.append(nodes[nodes[edge[key]]['point_index']]['raw_origin'])
                    assert endpoints
                    for point in endpoints:
                        delta = [a-b for a, b in zip(point, geometry['raw_origin'])]
                        along = sum(a*b for a, b in zip(delta, geometry['axis']))
                        radial = sum(a*a for a in delta)-along*along
                        assert math.isclose(radial, expected**2, abs_tol=1e-9)
                    main = decode_basics(root / relative, zstd)
                    stream = next(s for s in main['asm_decoding']['streams'] if s['member'] == member)
                    assert not any(d.get('index') == record['index'] for d in stream['topology']['unresolved'])
                    main_surfaces = [s['geometry'] for g in stream['topology']['body_graphs']
                                     for s in g['analytic_surfaces'] if s['surface_index'] == record['index']]
                    assert main_surfaces and all(s == geometry for s in main_surfaces)
                    found.append({'history_blob_member': member, 'surface_index': record['index'],
                                  'geometry': geometry, 'API_expected_radius_cm': expected,
                                  'saved_API_is_modeled': settings['is_modeled'],
                                  'saved_API_is_internal': settings['is_internal'],
                                  'own_boundary_endpoint_occurrences_checked': len(endpoints),
                                  'main_reader_geometry_matches': True})
                    varied = copy.deepcopy(record)
                    varied['tokens'][11]['value'] = 1.2
                    changed = decode_analytic_surface(varied)
                    assert changed['raw_radius'] == geometry['raw_radius'] and changed['stored_u_parameter_scale'] == 1.2
            assert len(found) == 1, (relative, found)
            report['samples'].append({'file': relative, 'recovered_surface': found[0],
                                       'positive_parameter_scale_independence_control_passed': True})
    assert len(report['samples']) == 9
    report['summary'] = {'archives': len(report['samples']), 'previous_radius_mismatch_failures_cleared': len(report['samples']),
                         'API_dimension_comparisons': len(report['samples']),
                         'boundary_endpoint_occurrences_checked': sum(s['recovered_surface']['own_boundary_endpoint_occurrences_checked'] for s in report['samples']),
                         'new_live_exports': 0}
    return report


if __name__ == '__main__':
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    report = validate(zstd)
    Path('cylinder-thread-resize-decoding.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], sort_keys=True))
