"""Saved-file integration of closed curves, seam charts and bounded surfaces."""

import copy
import hashlib
import json
from pathlib import Path

from decode_basics import decode_basics
from validate_history_cache_integration import baseline_outputs
from validate_surface_topology_integration import compare_outputs

ROOT = Path(__file__).resolve().parent
BASELINE = '543b789'
FILES = (
    'loftguides-265bcb9af34a/closure_closed_surface.f3d',
    'loftguides-265bcb9af34a/closure_closed_four.f3d',
    'pipepaths-3d11bd427946/spline_circular.f3d',
    'solidsweeps-7d2677669e3d/solid_rigid.f3d',
    'specialfillets-d50f7a4f04e0/rule_all_both.f3d',
    'specialfillets-d50f7a4f04e0/rule_asymmetric.f3d',
    'edgemodes-87edbf67527b/fillet_asymmetric.f3d',
    'moretools-380212ab6368/LoftThreeSections.f3d',
    'analytic-86a12b291d0a/analytic.f3d',
    'moretools-88a2cd6cad0b/Loft.f3d',
)


def report(name):
    return json.loads((ROOT/name).read_text())


def stream(output, member):
    result, = [s for s in output['asm_decoding']['streams'] if s['member'] == member]
    return result


def geometry(output, member, field, index_key, index, payload):
    values = [row[payload] for graph in stream(output, member)['topology']['body_graphs']
              for row in graph.get(field, []) if row[index_key] == index]
    assert values
    assert all(v == values[0] for v in values)
    return values[0]


def analytic_recoveries(before, after, filename):
    """Normalize only independently qualified formerly absent analytic fields."""
    normalized = copy.deepcopy(before)
    candidates = [report(name) for name in ('signed-torus-decoding.json', 'elliptic-cone-decoding.json')]
    expected, = [r for r in candidates if r['file'] == filename] or [None]
    if expected is None:
        return normalized, 0
    for record in expected['records']:
        index, member = record['record_index'], record['member']
        actual = geometry(after, member, 'analytic_surfaces', 'surface_index', index, 'geometry')
        assert actual == record['geometry']
        prior = stream(normalized, member)['topology']
        current = stream(after, member)['topology']
        assert any(e['kind'] in ('torus-surface', 'cone-surface') and e['index'] == index for e in prior['unresolved'])
        assert not any(e['kind'] in ('torus-surface', 'cone-surface') and e['index'] == index for e in current['unresolved'])
        for graph in prior['body_graphs']:
            current_graph, = [g for g in current['body_graphs'] if g['body_index'] == graph['body_index']]
            for row in graph['analytic_surfaces']:
                if row['surface_index'] != index:
                    continue
                assert row['geometry'] is None
                replacement, = [r for r in current_graph['analytic_surfaces'] if r['surface_index'] == index]
                row['geometry'] = actual
                row['geometry_status'] = replacement['geometry_status']
    return normalized, len(expected['records'])


def evidence_matches(outputs):
    counts = dict(closed_curve_caches=0, sum_surface_caches=0, shifted_uv_caches=0, VBL_boundary_components=0)
    for row in report('exact-curve-form-two-decoding.json')['samples']:
        actual = geometry(outputs[row['file']], row['member'], 'spline_curves', 'curve_index', row['record_index'], 'cache')
        assert actual == row['cache']
        counts['closed_curve_caches'] += 1
    sums = report('sum-surface-cache-decoding.json')
    for row in sums['records']:
        actual = geometry(outputs[sums['file']], row['member'], 'spline_surfaces', 'surface_index', row['record_index'], 'cache')
        assert hashlib.sha256(json.dumps(actual, sort_keys=True).encode()).hexdigest() == row['cache_sha256']
        counts['sum_surface_caches'] += 1
    for case in report('compact-pcurve-offset-decoding.json')['samples']:
        for blob in case['blobs']:
            for row in blob['decoded_offsets']:
                matches = [trim['uv_curve'] for graph in stream(outputs[case['file']], blob['member'])['topology']['body_graphs']
                           for loop in graph['face_trim_loops'] for trim in loop['trims'] if trim['pcurve_index'] == row['record_index']]
                assert matches and all(cache == row['expected_uv_cache'] for cache in matches)
                counts['shifted_uv_caches'] += 1
    for case in report('vbl-component-decoding.json')['samples']:
        topology = stream(outputs[case['file']], case['member'])['topology']
        if not case['expected_summary']['decoded'] and not case['expected_summary']['unresolved']:
            assert topology.get('vbl_component_boundaries') in (None, case['expected_summary'])
            continue
        actual = topology['vbl_component_boundaries']
        assert actual == case['expected_summary'] and not actual['unresolved']
        for row in actual['decoded']:
            assert row['VBL_interior_geometry'] is None
            assert any(e['index'] == row['surface_record_index'] and 'standalone XYZ surface evaluator remains unsupported' in e['reason']
                       for e in topology['unresolved'])
            counts['VBL_boundary_components'] += len(row['components'])
    assert counts == dict(closed_curve_caches=4, sum_surface_caches=4, shifted_uv_caches=2, VBL_boundary_components=48)
    return counts


def validate(zstd):
    before = baseline_outputs(FILES, zstd, revision=BASELINE)
    outputs = {filename: json.loads(json.dumps(decode_basics(ROOT/filename, zstd))) for filename in FILES}
    rows, analytic_count = [], 0
    for filename, old in zip(FILES, before):
        normalized, recovered = analytic_recoveries(old, outputs[filename], filename)
        comparison = compare_outputs(normalized, outputs[filename], filename)
        comparison['qualified_analytic_surface_recoveries'] = recovered
        analytic_count += recovered
        rows.append(comparison)
    matches = evidence_matches(outputs)
    prior = sum(s['prior_geometry_rejections'] for row in rows for s in row['streams'])
    remaining = sum(len(s['remaining_geometry_rejections']) for row in rows for s in row['streams'])
    assert (prior, remaining, analytic_count) == (24, 8, 6)
    controls = {'edgemodes-87edbf67527b/fillet_asymmetric.f3d',
                'moretools-380212ab6368/LoftThreeSections.f3d', 'analytic-86a12b291d0a/analytic.f3d'}
    assert all(outputs[name] == previous for name, previous in zip(FILES, before) if name in controls)
    return {'scope': 'Ten saved main-reader cases against543b789; bounded recoveries and three whole-output controls, no live Fusion actions',
            'baseline_commit': BASELINE, 'samples': rows,
            'summary': {'saved_files': len(FILES), 'prior_geometry_rejections': prior, 'remaining_geometry_rejections': remaining,
                        **matches, 'qualified_analytic_surface_records': analytic_count, 'whole_output_controls_exact': 3,
                        'prior_structural_graphs_and_geometry_preserved': True, 'non_ASM_output_changes': 0, 'new_API_calls': 0},
            'limitations': ['Eight VBL surface-interior warnings remain explicit; recovered boundaries do not evaluate the full VBL surface.',
                           'Closed-curve form codes, signed torus UV orientation and general periodic/coedge parameter mapping remain partially interpreted.',
                           'Diagnostic counts concern these ten saved cases only, not total format completion.',
                           'Native writing, full translation, exact procedural geometry and regeneration remain unfinished.']}


if __name__ == '__main__':
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    result = validate(str(zstd))
    (ROOT/'closed-cache-integration.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['summary'], sort_keys=True))
