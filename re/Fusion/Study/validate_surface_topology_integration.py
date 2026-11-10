"""Focused main-reader boundaries for surface variants and tolerant topology."""

import copy
import json
from pathlib import Path

from decode_basics import decode_basics
from validate_history_cache_integration import baseline_outputs

ROOT = Path(__file__).resolve().parent
BASELINE = '42ce116'
TOLERANT_FILE = 'solidsweeps-7d2677669e3d/solid_twist.f3d'
FILES = (
    'solidsweeps-5b5ecd5e01b9/solid_twist_sixty.f3d', TOLERANT_FILE,
    'embosstext-cd769aa41cdf/two_texts.f3d',
    'specialfillets-d50f7a4f04e0/rule_asymmetric.f3d',
    'tappedholes-409e96788503/modeled_full.f3d',
    'lofts-03b4a6f1ce2f/centerline.f3d',
    'sweeps-5f87eff25e24/line_twist.f3d',
    'pipeedgecontrasts-5bd287323ae7/line_full.f3d',
    'edgemodes-52695761f185/fillet_curvature.f3d',
    'bodymodes-df9b7113539f/scale_uniform.f3d',
    'sweepguides-9887de71bf9e/rail_scale.f3d',
    'solidsweeps-7d2677669e3d/solid_aligned.f3d',
    'pipepaths-3d11bd427946/spline_circular.f3d',
    'threadmodes-d51d2ae60564/modeled_full.f3d',
    'loftguides-265bcb9af34a/closure_closed_surface.f3d',
    'loftfaces-055501f619c5/edge_path_tangent_weight2.f3d',
)
GEOMETRY_FIELDS = ('spline_curves', 'spline_surfaces', 'analytic_surfaces',
                   'encoded_curves', 'encoded_surfaces', 'partial_surface_definitions')


def topology_structure(graph):
    value = copy.deepcopy(graph)
    for field in GEOMETRY_FIELDS:
        value.pop(field, None)
    for loop in value['face_trim_loops']:
        loop.pop('uv_endpoints_close_in_this_chart')
        for trim in loop['trims']:
            trim.pop('uv_curve')
    return value


def placement_recovery(before, after, filename):
    """Admit one recovered placement only through its unchanged typed BODY join."""
    old, new = before['streams'][0]['body_placement'], after['streams'][0]['body_placement']
    if old == new:
        return 0
    assert filename == TOLERANT_FILE
    a, b = dict(old), dict(new)
    old_bodies, new_bodies = a.pop('bodies'), b.pop('bodies')
    old_failures, new_failures = a.pop('unresolved'), b.pop('unresolved')
    assert a == b and not new_failures
    prior = {row['native_body_object_id']: row for row in old_bodies}
    current = {row['native_body_object_id']: row for row in new_bodies}
    assert all(current[key] == row for key, row in prior.items())
    assert current.keys()-prior.keys() == {275}
    assert len(old_failures) == 1 and old_failures[0]['native_body_object_id'] == 275
    entry = current[275]
    bindings = [binding for mapping in after['streams'][0]['body_blob_bindings']['decoded']
                if mapping['history_blob_member'] == entry['history_blob_member']
                for binding in mapping['bindings'] if binding['native_body_object_id'] == 275]
    binding, = bindings
    for field in ('asm_body_index', 'asm_stored_entity_id', 'component_object_id',
                  'association_status', 'lifecycle_status'):
        assert entry[field] == binding[field]
    stream, = [s for s in after['asm_decoding']['streams'] if s['member'] == entry['history_blob_member']]
    graph, = [g for g in stream['topology']['body_graphs'] if g['body_index'] == entry['asm_body_index']]
    assert graph['body_transform_is_identity'] is True
    assert entry['component_vertex_positions_cm'] == graph['raw_vertex_positions']
    placement, = entry['placements']
    assert placement['component_to_world_matrix'] == prior[360]['placements'][0]['component_to_world_matrix']
    assert placement['world_vertex_positions_cm'] == entry['component_vertex_positions_cm']
    return 1


def compare_outputs(before, after, filename):
    """Permit geometry additions, preserving prior graphs and all unrelated output."""
    old, new = copy.deepcopy(before), copy.deepcopy(after)
    old.pop('asm_decoding'); new.pop('asm_decoding')
    placement_count = placement_recovery(before, after, filename)
    if placement_count:
        old['streams'][0].pop('body_placement'); new['streams'][0].pop('body_placement')
    assert old == new, (filename, 'Unexpected non-ASM output change')
    old_streams = {s['member']: s for s in before['asm_decoding']['streams']}
    streams = {s['member']: s for s in after['asm_decoding']['streams']}
    assert old_streams.keys() == streams.keys()
    rows = []
    for member, current in streams.items():
        previous = old_streams[member]
        a, b = copy.deepcopy(previous), copy.deepcopy(current)
        prior, topology = a.pop('topology'), b.pop('topology')
        assert a == b, (filename, member, 'Raw framing or inline namespace changed')
        prior_keys = {(e.get('kind'), e.get('index')) for e in prior['unresolved']}
        current_keys = {(e.get('kind'), e.get('index')) for e in topology['unresolved']}
        assert current_keys <= prior_keys, (filename, member, 'New rejection')
        old_graphs = {g['body_index']: g for g in prior['body_graphs']}
        graphs = {g['body_index']: g for g in topology['body_graphs']}
        assert old_graphs.keys() <= graphs.keys()
        recovered = sorted(graphs.keys()-old_graphs.keys())
        if recovered:
            assert filename == TOLERANT_FILE and recovered == [1]
            assert ('body_graph', 1) in prior_keys and ('body_graph', 1) not in current_keys
            assert graphs[1]['all_coedges_have_partners'] is True
        new_uv = new_surfaces = new_curves = encoded_curves = encoded_surfaces = partial = 0
        for body_id, graph in graphs.items():
            prior_graph = old_graphs.get(body_id)
            if prior_graph is not None:
                assert topology_structure(graph) == topology_structure(prior_graph), (filename, member, body_id)
                for field, key in (('spline_curves', 'curve_index'), ('spline_surfaces', 'surface_index')):
                    caches = {row[key]: row for row in graph[field]}
                    for old_cache in prior_graph[field]:
                        assert caches[old_cache[key]] == old_cache
                for old_loop, loop in zip(prior_graph['face_trim_loops'], graph['face_trim_loops']):
                    for old_trim, trim in zip(old_loop['trims'], loop['trims']):
                        if old_trim['uv_curve'] is not None:
                            assert trim['uv_curve'] == old_trim['uv_curve']
                        elif trim['uv_curve'] is not None:
                            new_uv += 1
                surface_ids = {row['surface_index'] for field in ('spline_surfaces', 'encoded_surfaces', 'partial_surface_definitions')
                               for row in graph.get(field, [])}
                assert len(prior_graph['analytic_surfaces']) == len(graph['analytic_surfaces'])
                for old_surface, surface in zip(prior_graph['analytic_surfaces'], graph['analytic_surfaces']):
                    left, right = dict(old_surface), dict(surface)
                    old_status, status = left.pop('geometry_status'), right.pop('geometry_status')
                    assert left == right
                    if old_status != status:
                        assert surface['surface_index'] in surface_ids
                new_surfaces += len(graph['spline_surfaces'])-len(prior_graph['spline_surfaces'])
                new_curves += len(graph['spline_curves'])-len(prior_graph['spline_curves'])
            # Encoded helices and partial VBL definitions must remain separate
            # from evaluable B-spline dictionaries. Their evidence is checked below.
            encoded_curves += len(graph.get('encoded_curves', []))
            encoded_surfaces += len(graph.get('encoded_surfaces', []))
            partial += len(graph.get('partial_surface_definitions', []))
        rows.append({'member': member, 'prior_geometry_rejections': len(prior['unresolved']),
                     'remaining_geometry_rejections': topology['unresolved'], 'recovered_body_graph_indices': recovered,
                     'existing_structural_graphs_unchanged': True, 'prior_geometry_unchanged': True,
                     'additional_surface_caches_in_prior_graphs': new_surfaces,
                     'additional_curve_caches_in_prior_graphs': new_curves,
                     'additional_uv_caches_in_prior_graphs': new_uv,
                     'encoded_curves': encoded_curves, 'encoded_surfaces': encoded_surfaces,
                     'partial_surface_definitions': partial})
    return {'file': filename, 'unchanged_non_ASM_output_except_qualified_placement': True,
            'new_typed_BODY_vertex_placements': placement_count, 'streams': rows}


def evidence_matches(outputs):
    """Check public geometry dictionaries against independently validated reports."""
    count = 0
    for report_name in ('helix-cache-decoding.json', 'rule-blend-cache-decoding.json'):
        report = json.loads((ROOT/report_name).read_text())
        for sample in report['samples']:
            if sample['file'] not in outputs:
                continue
            stream, = [s for s in outputs[sample['file']]['asm_decoding']['streams'] if s['member'] == sample['member']]
            all_geometry = {}
            for graph in stream['topology']['body_graphs']:
                for field, index, payload in (
                    ('spline_curves', 'curve_index', 'cache'), ('spline_surfaces', 'surface_index', 'cache'),
                    ('encoded_curves', 'curve_index', 'geometry'), ('encoded_surfaces', 'surface_index', 'geometry'),
                    ('partial_surface_definitions', 'surface_index', 'definition')):
                    for row in graph.get(field, []):
                        all_geometry[row[index]] = row[payload]
            if report_name.startswith('helix'):
                expected = [(row['record_index'], row['geometry']) for row in sample['encoded_geometries']]
            else:
                expected = []
                for field in ('XYZ_caches', 'VBL_definitions'):
                    for row in sample[field]:
                        geometry = copy.deepcopy(row['expected_decoded'])
                        if field == 'VBL_definitions':
                            geometry = {'partial_surface_definition': geometry}
                        if row['subtype_expansion_provenance'] is not None:
                            geometry['inline_subtype_reference'] = row['subtype_expansion_provenance']
                        expected.append((row['record_index'], geometry))
            for index, geometry in expected:
                assert all_geometry[index] == geometry, (sample['file'], index, report_name)
                count += 1
    assert count == 56
    return count


def validate(zstd):
    baseline = baseline_outputs(FILES, zstd, revision=BASELINE)
    outputs = {filename: json.loads(json.dumps(decode_basics(ROOT/filename, zstd))) for filename in FILES}
    rows = [compare_outputs(before, outputs[filename], filename) for filename, before in zip(FILES, baseline)]
    matches = evidence_matches(outputs)
    streams = [stream for row in rows for stream in row['streams']]
    old_count = sum(row['prior_geometry_rejections'] for row in streams)
    remaining = sum(len(row['remaining_geometry_rejections']) for row in streams)
    assert remaining < old_count
    return {'scope': 'Sixteen saved main-reader cases against local42ce116; no live Fusion operations or whole-corpus rerun',
            'baseline_commit': BASELINE, 'samples': rows,
            'summary': {'saved_files': len(FILES), 'prior_geometry_rejections': old_count,
                        'remaining_geometry_rejections': remaining, 'focused_report_dictionary_matches': matches,
                        'recovered_stored_BODY_graphs': sum(len(s['recovered_body_graph_indices']) for s in streams),
                        'new_typed_BODY_vertex_placements': sum(r['new_typed_BODY_vertex_placements'] for r in rows),
                        'encoded_curves': sum(s['encoded_curves'] for s in streams),
                        'encoded_surfaces': sum(s['encoded_surfaces'] for s in streams),
                        'partial_surface_definitions': sum(s['partial_surface_definitions'] for s in streams),
                        'unexpected_prior_output_changes': 0, 'new_API_calls': 0},
            'limitations': ['Diagnostic counts are restricted to these files and do not measure format completion.',
                           'Partial VBL surfaces and unresolved geometry keep explicit diagnostics.',
                           'Loft procedural fields, tolerance meanings, arbitrary helical surface frames, parameter remapping, native writing and regeneration remain unfinished.']}


if __name__ == '__main__':
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    result = validate(str(zstd))
    (ROOT/'surface-topology-integration.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['summary'], sort_keys=True))
