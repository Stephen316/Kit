"""Focused saved-edge validation of non-unit straight-curve parameter vectors."""

import copy
import json
import math
from pathlib import Path
import subprocess

from asm_records import inspect_asm
from decode_brep import decode_topology
from fusion_archive import read_members

ROOT = Path(__file__).resolve().parent
FILES = (
    'bodymodes-d696a14d5f0b/scale_holdout.f3d',
    'bodymodes-df9b7113539f/scale_nonuniform.f3d',
    'bodymodes-df9b7113539f/scale_uniform.f3d',
    'bodyselections-62e42366c722/scale_two_bodies_point.f3d',
    'edgemodes-87edbf67527b/fillet_variable.f3d',
    'scaleshellinputs-97ef1cfd19e4/scale_construction_point.f3d',
    'scaleshellinputs-97ef1cfd19e4/scale_vertex.f3d',
    'tools-fda3948848f4/Scale.f3d',
)
CONTROLS = ('revolveaxes-14700158dba9/brep_edge_offset_x.f3d',
            'pipeedgecontrasts-5bd287323ae7/line_full.f3d')


def evaluate(line, parameter):
    return [a+parameter*b for a, b in zip(line['raw_origin'], line['direction'])]


def validate(zstd):
    old = {'__name__': '_baseline_scaled_line_topology'}
    exec(subprocess.check_output(['git', 'show', 'b6372ab:decode_brep.py'], cwd=ROOT), old)
    report = {'scope': 'Stored straight-curve parameter vectors in eight saved scaled/variable-Fillet archives; initial entity namespace and existing unit-vector output retained',
              'primary_reference': {'url': 'https://github.com/mozman/ezdxf/blob/master/src/ezdxf/acis/entities.py',
                                    'symbol': 'StraightCurve.restore_data / StraightCurve.evaluate',
                                    'correspondence': 'The primary implementation retains the stored direction vector and evaluates origin plus parameter times direction; no normalizing step is applied.'},
              'samples': [], 'api_vertex_controls': [], 'controls': [], 'guards': [],
              'limitations': ['No direct API native line-parameter getter was captured for these records.',
                              'Stored edge endpoints corroborate this parameterization; curve reversal, occurrence transforms and final/current state are not newly inferred.',
                              'Plane normals and other primitive axes retain their existing unit-vector checks.']}
    recovered_count = endpoints = old_nodes = 0
    maximum = 0.
    guard_source = None
    body_truth = json.loads((ROOT/'bodycoords-2c2aa8982ad4/ground_truth.json').read_text())
    for filename in FILES+CONTROLS:
        sample = {'file': filename, 'streams': []}
        for member, blob in read_members(ROOT/filename, zstd).items():
            if not member.endswith(('.smb', '.smbh')):
                continue
            parsed = inspect_asm(blob)
            before = old['decode_topology'](parsed)
            topology = decode_topology(parsed)
            nodes = {n['index']: n for n in topology['nodes']}
            for node in before['nodes']:
                assert nodes[node['index']] == node, (filename, member, node['index'])
                old_nodes += 1
            assert topology['body_graphs'] == before['body_graphs']
            recovered = {i: n for i, n in nodes.items() if 'stored_direction_magnitude' in n}
            if filename in CONTROLS:
                assert topology == before
                continue
            removed = [e for e in before['unresolved'] if e.get('kind') == 'straight-curve']
            assert {e['index'] for e in removed} == set(recovered)
            assert topology['unresolved'] == [e for e in before['unresolved'] if e not in removed]
            row = {'member': member, 'recovered_curves': [], 'endpoint_checks': []}
            for index, line in recovered.items():
                assert line['direction'] == parsed['records'][index]['tokens'][4]['value']
                row['recovered_curves'].append({'record_index': index, 'raw_origin': line['raw_origin'],
                                                'stored_direction': line['direction'],
                                                'magnitude': line['stored_direction_magnitude']})
                recovered_count += 1
                if guard_source is None:
                    guard_source = copy.deepcopy(parsed), index
            for edge in nodes.values():
                if edge['kind'] != 'edge' or edge['curve_index'] not in recovered:
                    continue
                line = recovered[edge['curve_index']]
                for side in ('start', 'end'):
                    vertex = nodes[edge[side+'_vertex_index']]
                    point = nodes[vertex['point_index']]
                    parameter = edge[side+'_parameter']
                    actual, predicted = point['raw_origin'], evaluate(line, parameter)
                    error = math.dist(actual, predicted)
                    assert error < 1e-10
                    endpoints += 1
                    maximum = max(maximum, error)
                    normalized_prediction = [a+parameter*b/line['stored_direction_magnitude']
                                             for a, b in zip(line['raw_origin'], line['direction'])]
                    row['endpoint_checks'].append({'edge_index': edge['index'], 'curve_index': edge['curve_index'],
                        'side': side, 'vertex_index': vertex['index'], 'point_index': point['index'],
                        'parameter': parameter, 'stored_point': actual, 'evaluated_point': predicted,
                        'error_raw': error, 'normalizing_would_produce_error_raw': math.dist(actual, normalized_prediction)})
            if recovered:
                sample['streams'].append(row)
                api = [s for s in body_truth['samples'] if s['source'] == filename]
                if api:
                    placement, = api[0]['placements']
                    assert placement['path'] == ''
                    actual_vertices = placement['world_vertex_positions_cm']
                    assert all(any(math.dist(c['evaluated_point'], p) < 1e-10 for p in actual_vertices)
                               for c in row['endpoint_checks'])
                    report['api_vertex_controls'].append({'file': filename, 'member': member,
                        'source': 'bodycoords-2c2aa8982ad4/ground_truth.json', 'actual_root_body_name': placement['name'],
                        'actual_vertex_positions_cm': actual_vertices, 'endpoint_positions_match_api_vertex_set': True,
                        'direct_curve_parameter_getters_captured': False})
        if filename in CONTROLS:
            report['controls'].append({'file': filename, 'complete_topology_output_unchanged': True})
        else:
            report['samples'].append(sample)
    parsed, line_index = guard_source
    for label, mutate in (
            ('Zero stored line vector', lambda p: p['records'][line_index]['tokens'][4].update(value=[0., 0., 0.])),
            ('Nonfinite stored line vector', lambda p: p['records'][line_index]['tokens'][4].update(value=[math.inf, 0., 0.])),
            ('Wrong line vector token kind', lambda p: p['records'][line_index]['tokens'][4].update(kind='position_vector')),
            ('Non-unit plane normal remains rejected', lambda p: next(r for r in p['records'] if r['name'] == 'plane-surface')['tokens'][4].update(value=[0., 0., 2.]))):
        changed = copy.deepcopy(parsed)
        mutate(changed)
        expected_index = (next(r['index'] for r in changed['records'] if r['name'] == 'plane-surface')
                          if label.startswith('Non-unit plane') else line_index)
        failure, = [r for r in decode_topology(changed)['unresolved'] if r.get('index') == expected_index]
        report['guards'].append({'case': label, 'rejected': True, 'reason': failure['reason']})
    assert recovered_count == 98 and endpoints == 196 and len(report['api_vertex_controls']) == 2
    report['summary'] = {'saved_target_files': len(FILES), 'recovered_line_records': recovered_count,
                         'typed_endpoint_checks': endpoints, 'maximum_endpoint_error_raw': maximum,
                         'unchanged_prior_nodes': old_nodes, 'unchanged_unit_line_archive_controls': len(CONTROLS),
                         'api_root_body_vertex_controls': len(report['api_vertex_controls']),
                         'malformed_guards': len(report['guards'])}
    return report


if __name__ == '__main__':
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    result = validate(str(zstd))
    (ROOT/'scaled-line-direction-decoding.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['summary'], sort_keys=True))
