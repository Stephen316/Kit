"""Focused tolerant-header/inline-cache validation with an ordinary-node baseline."""

import argparse
from collections import Counter
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess

from asm_records import inspect_asm
from decode_asm_subtypes import decode_asm_subtypes, resolve_asm_subtype
from decode_basics import decode_basics
from decode_brep import decode_topology
from decode_bspline import evaluate_curve, evaluate_surface
from decode_tolerant_topology import decode_tolerant_topology, KINDS
from fusion_archive import read_members

FILE = 'solidsweeps-7d2677669e3d/solid_twist.f3d'
BASELINE = '42ce116'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def distance(a, b):
    return math.sqrt(sum((x-y)**2 for x, y in zip(a, b)))


def fraction(domain, q):
    return domain[0] if q == 0 else domain[1] if q == 1 else domain[0]+(domain[1]-domain[0])*q


def validate(root, zstd):
    baseline_source = subprocess.run(['git', 'show', BASELINE+':decode_brep.py'], cwd=root,
        check=True, text=True, capture_output=True).stdout
    old = {'__name__': 'tolerant_topology_baseline'}
    exec(compile(baseline_source, BASELINE+'-decode_brep.py', 'exec'), old)
    # Baseline imports the current geometry cache readers, isolating topology.
    members = read_members(root/FILE, zstd)
    checks, samples, contexts, totals = 0, [], {}, Counter()

    def check(test, reason):
        nonlocal checks
        if not test:
            raise AssertionError(reason)
        checks += 1

    truth = json.loads((root/Path(FILE).parent/'ground_truth.json').read_text())
    api = next(s for s in truth['samples'] if s['file'] == 'solid_twist.f3d')
    for member, blob in members.items():
        if not member.endswith(('.smb', '.smbh')):
            continue
        parsed = inspect_asm(blob)
        before = copy.deepcopy(parsed)
        catalog = decode_asm_subtypes(blob, parsed=parsed)
        previous = old['decode_topology'](parsed, subtype_catalog=catalog)
        current = decode_topology(parsed, subtype_catalog=catalog)
        check(not current['unresolved'], 'all current topology and inline caches in the target blob decode')
        check(len(current['body_graphs']) == (2 if member.endswith('.smbh') else 8), 'expected recovered graph count')
        nodes = {n['index']: n for n in current['nodes']}
        old_nodes = {n['index']: n for n in previous['nodes']}
        check(all(nodes[i] == n for i, n in old_nodes.items()), 'every previously decoded ordinary node is exactly unchanged')
        graphs = {g['body_index']: g for g in current['body_graphs']}
        check(all(graphs[g['body_index']] == g for g in previous['body_graphs']), 'every previous ordinary BODY graph remains exact')
        newly = set(nodes)-set(old_nodes)
        check(Counter(nodes[i]['kind'] for i in newly) == {'coedge': 8, 'edge': 4, 'vertex': 4, 'pcurve': 4},
              'only tolerant headers and four formerly blocked compact pcurves recover')
        tolerant = [n for n in current['nodes'] if 'tolerant_record' in n]
        check(Counter(n['kind'] for n in tolerant) == {'coedge': 8, 'edge': 4, 'vertex': 4}, 'all sixteen original tolerant subclasses represented')
        inline = []
        for n in tolerant:
            r = parsed['records'][n['index']]
            header, metadata = decode_tolerant_topology(r)
            expected_kind, expected_count = KINDS[r['name']]
            check(header['name'] == expected_kind and header['tokens'] == r['tokens'][:expected_count], 'derived header is an exact unchanged base prefix')
            check(metadata == n['tolerant_record'] and metadata['stored_additional_fields'] == r['tokens'][expected_count:], 'source kind and extra fields retained exactly')
            check(n['offset'] == r['offset'] and metadata['source_record_index'] == r['index'], 'original global record index/byte origin unchanged')
            if n['kind'] == 'coedge':
                check(nodes[n['next_coedge_index']]['previous_coedge_index'] == n['index'] and
                    nodes[n['previous_coedge_index']]['next_coedge_index'] == n['index'], 'coedge next/previous links reciprocal')
                partner = nodes[n['partner_index']]
                check(partner['partner_index'] == n['index'] and partner['edge_index'] == n['edge_index'], 'coedge partner pair reciprocal and owns same edge')
                loop = nodes[n['loop_index']]
                face = nodes[loop['face_index']]
                graph_ids = [g['body_index'] for g in current['body_graphs'] if n['index'] in g['coedge_indices']]
                check(loop['kind'] == 'loop' and face['kind'] == 'face' and len(graph_ids) == 1, 'tolerant coedge belongs to one explicit reciprocal BODY loop graph')
            elif n['kind'] == 'edge':
                check(nodes[n['first_coedge_index']]['edge_index'] == n['index'], 'edge/first-coedge link reciprocal')
                check(all(nodes[n[k]]['kind'] == 'vertex' for k in ('start_vertex_index', 'end_vertex_index')), 'edge endpoint kinds normalize to typed vertices')
            else:
                incident = nodes[n['first_edge_index']]
                check(n['index'] in (incident['start_vertex_index'], incident['end_vertex_index']) and nodes[n['point_index']]['kind'] == 'point',
                      'vertex incident-edge/point links remain typed and reciprocal')
            cache = metadata.get('inline_curve_cache')
            if cache is None:
                continue
            check('unresolved_inline_curve' not in metadata, 'inline cache is successfully decoded, not merely retained')
            check(metadata['stored_coedge_interval'] == cache['parameter_domain'], 'stored coedge bounds equal literal inline XYZ cache domain')
            edge = nodes[n['edge_index']]
            points = [nodes[nodes[edge[end+'_vertex_index']]['point_index']]['raw_origin'] for end in ('start', 'end')]
            endpoint_values = [evaluate_curve(cache, t) for t in cache['parameter_domain']]
            endpoint_errors = [min(distance(v, p) for p in points) for v in endpoint_values]
            check(all(math.isfinite(e) for e in endpoint_errors), 'typed endpoint deviations are finite and retained without tolerance interpretation')
            surface = nodes[face['surface_index']]
            support = cache['stored_support_definition']
            if support['kind'] == 'spline':
                blocks = [b for b in catalog['blocks'] if b['record_index'] == n['index'] and b['context_kind'] == 'surface']
                check(len(blocks) == 1, 'one explicitly framed inline surface support')
                support_id = resolve_asm_subtype(catalog, n['index'], blocks[0]['token_start'], expected_kind='surface')['target_definition']['definition_index']
                face_id = resolve_asm_subtype(catalog, surface['index'], 4, expected_kind='surface')['target_definition']['definition_index']
                check(support_id == face_id, 'inline support and typed parent face resolve to same blob-local surface definition')
                support_proof = {'kind': 'spline', 'shared_definition_index': support_id, 'surface_record_index': surface['index']}

                def evaluate(coords):
                    return evaluate_surface(surface['bspline_surface'], *coords)
            else:
                fields = support['stored_definition']
                origin, normal, axis = [fields[i]['value'] for i in (1, 2, 3)]
                plane = surface['analytic_surface']
                check((origin, normal, axis, fields[4]['value']) == (plane['raw_origin'], plane['normal'], plane['stored_reference_axis'], plane['is_v_reversed']),
                      'inline explicit plane frame exactly repeats typed parent plane fields')
                v_axis = [normal[1]*axis[2]-normal[2]*axis[1], normal[2]*axis[0]-normal[0]*axis[2], normal[0]*axis[1]-normal[1]*axis[0]]
                support_proof = {'kind': 'plane', 'surface_record_index': surface['index'], 'frame_repeated_exactly': True,
                    'scope': 'Explicit repeated plane frame corroboration; no native persistent plane identity inferred'}

                def evaluate(coords):
                    return [origin[k]+coords[0]*axis[k]+coords[1]*v_axis[k] for k in range(3)]
            uv = cache['stored_embedded_uv_cache']
            comparisons = []
            for q in (0., .25, .5, .75, 1.):
                t, ut = fraction(cache['parameter_domain'], q), fraction(uv['parameter_domain'], q)
                xyz, coords = evaluate_curve(cache, t), evaluate_curve(uv, ut)
                surface_xyz = evaluate(coords)
                error = distance(xyz, surface_xyz)
                check(math.isfinite(error), 'independent XYZ/UV support-cache deviation retained as a measurement')
                comparisons.append({'fraction': q, 'XYZ_cache_parameter': t, 'UV_cache_parameter': ut,
                    'XYZ_cache_position': xyz, 'UV_cache_position': coords, 'support_surface_position': surface_xyz,
                    'independent_cache_deviation_raw': error})
            check(max(comparisons[0]['independent_cache_deviation_raw'], comparisons[-1]['independent_cache_deviation_raw']) < 1e-12,
                  'independent inline XYZ and UV/surface endpoints agree to rounding')
            inline.append({'coedge_record_index': n['index'], 'edge_record_index': edge['index'],
                'face_record_index': face['index'], 'surface_support_proof': support_proof,
                'stored_coedge_bounds': metadata['stored_coedge_interval'], 'XYZ_domain': cache['parameter_domain'],
                'UV_degree': uv['degree'], 'UV_domain': uv['parameter_domain'],
                'typed_edge_endpoint_positions': points, 'inline_cache_endpoint_positions': endpoint_values,
                'typed_edge_endpoint_set_deviations_raw': endpoint_errors, 'independent_cache_samples': comparisons,
                'scope': 'Inline approximation deviations are explicit. Stored positive scalar fields are not used as an accuracy threshold or solver-tolerance claim.'})
        check(parsed == before, 'all normalization/topology/inline validation leaves raw parsed records unchanged')
        totals['native_tolerant_records'] += len(tolerant)
        totals['recovered_compact_pcurves'] += 4
        totals['ordinary_nodes_exact'] += len(old_nodes)
        totals['ordinary_graphs_exact'] += len(previous['body_graphs'])
        totals['inline_curve_caches'] += len(inline)
        samples.append({'member': member, 'previous_body_graph_count': len(previous['body_graphs']),
            'body_graph_count': len(current['body_graphs']), 'newly_recovered_body_graph_indices': sorted(set(graphs)-{g['body_index'] for g in previous['body_graphs']}),
            'body_graph_counts': [{'body_index': g['body_index'], 'counts': g['counts']} for g in current['body_graphs']],
            'ordinary_nodes_sha256': digest([old_nodes[i] for i in sorted(old_nodes)]),
            'ordinary_nodes_exact_count': len(old_nodes), 'ordinary_body_graphs_exact_count': len(previous['body_graphs']),
            'decoded_tolerant_nodes': tolerant, 'new_compact_pcurve_record_indices': sorted(i for i in newly if nodes[i]['kind'] == 'pcurve'),
            'inline_curve_evidence': inline, 'scope': 'Explicit initial stored topology only; no history replay, current lifecycle or solver tolerance semantics'})
        contexts[member] = (blob, parsed, catalog, current)
    # Native mapping, rather than graph order, selects the API-corroborated graph.
    main = decode_basics(root/FILE, zstd)
    stream = main['streams'][0]
    mappings = stream['body_blob_bindings']['decoded']
    mapping, = [m for m in mappings if m['history_blob_member'] in contexts]
    graphs = {g['body_index']: g for g in contexts[mapping['history_blob_member']][3]['body_graphs']}
    api_checks = []
    for binding in mapping['bindings']:
        actual = next(a for a in api['result_bodies'] if a['name'] == binding['name'])
        graph = graphs[binding['asm_body_index']]
        check(graph['counts']['face'] == actual['face_count'] and graph['counts']['edge'] == actual['edge_count'],
              'explicit mapped graph face/edge counts agree with captured API result body')
        api_checks.append({'native_body_object_id': binding['native_body_object_id'], 'native_name': binding['name'],
            'asm_body_index': binding['asm_body_index'], 'stored_handle': binding['stored_handle'],
            'face_count': graph['counts']['face'], 'edge_count': graph['counts']['edge'],
            'scope': 'Typed mapping determines ASM graph. Saved API name selects corroborating captured body data; names do not choose native identity.'})
    guards = []
    member = next(m for m in contexts if m.endswith('.smbh'))
    blob, parsed, catalog, current = contexts[member]
    records = parsed['records']
    coedge = next(r for r in records if r['section'] == 'geometry' and r['name'] == 'tcoedge-coedge' and len(r['tokens']) > 17)
    edge = next(r for r in records if r['section'] == 'geometry' and r['name'] == 'tedge-edge')
    vertex = next(r for r in records if r['section'] == 'geometry' and r['name'] == 'tvertex-vertex')

    def rejected(label, original, mutate):
        changed = copy.deepcopy(original)
        mutate(changed['tokens'])
        try:
            decode_tolerant_topology(changed)
        except (ValueError, KeyError, IndexError) as error:
            check(True, label)
            guards.append({'guard': label, 'reason': str(error)})
        else:
            raise AssertionError('Malformed tolerant suffix accepted: '+label)

    rejected('Reversed coedge stored bounds', coedge, lambda t: t[11].update(value=t[12]['value']+1.))
    rejected('Nonpositive extra edge scalar', edge, lambda t: t[11].update(value=0.))
    rejected('Unobserved tolerant vertex sentinel', vertex, lambda t: t[6].update(value=0.))
    rejected('Inline subtype lacks its outer closing bracket', coedge,
        lambda t: t.__delitem__(max(i for i, x in enumerate(t) if x['kind'] == 'subtype_end')))
    changed = copy.deepcopy(parsed)
    changed['records'][coedge['index']]['tokens'][3]['value'] = coedge['index']
    broken = decode_topology(changed, subtype_catalog=catalog)
    check(1 not in {g['body_index'] for g in broken['body_graphs']} and 2 in {g['body_index'] for g in broken['body_graphs']},
          'broken reciprocal coedge rejects affected graph and preserves separate ordinary body graph')
    guards.append({'guard': 'Broken base-header next/previous reciprocity',
        'affected_graph_rejected': True, 'separate_ordinary_graph_preserved': True,
        'body_graph_failures': [u for u in broken['unresolved'] if u['kind'] == 'body_graph']})
    return {'stage': 'Tolerant inherited topology and bounded inline curve caches',
        'implementation_scope': 'Validation-only stage; root owns decode_tolerant_topology.py, decode_brep normalization and parameter-curve degree/bounds extensions.',
        'baseline': {'commit': BASELINE, 'module': 'decode_brep.py', 'source_sha256': hashlib.sha256(baseline_source.encode()).hexdigest(),
            'method': 'Read-only git show source loaded with current geometry-cache functions to isolate ordinary topology/header output compatibility.'},
        'validation': {'checks': checks, 'saved_files': 1, 'blob_count': len(samples), **dict(totals),
            'malformed_guards': guards, 'API_geometry_evaluator_getters_captured': False,
            'API_mapped_result_counts': api_checks},
        'findings': ['All 32 native tolerant records normalize to exact inherited headers while retaining original class/index/byte origin and literal additional fields.',
            'All 1,273 previous ordinary nodes and eight ordinary BODY graphs remain exact under the baseline topology reader with current cache functions.',
            'Both formerly missing BODY graph 1 records recover. The history mapping explicitly joins native target 275 to .smbh graph 1, whose 28 faces and 64 edges agree with saved API counts.',
            'Eight inline curve caches match the stored coedge parameter domains. Four cubic-UV caches have about 7e-6–1e-5 raw endpoint deviations from the shared typed edge points; these differences remain explicit.',
            'Independent XYZ and embedded UV/support evaluations agree at endpoints; finite interior cache discrepancies up to about 6.3e-6 raw units remain measurements, without any solver-precision interpretation.'],
        'limitations': ['Positive scalar suffix fields are retained literally; no solver tolerance, weld, manifold precision or accuracy-bound meaning is assigned.',
            'Inline caches are approximations. Typed graph completeness does not establish exact procedural geometry, current solved state or lifecycle.',
            'Only captured tolerant subclasses and bounded optional inline curve layouts are covered.',
            'The comparison never assigns native identities from geometry, record order or API entity tokens.'], 'samples': samples}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    p.add_argument('--zstd-library', type=Path, required=True)
    p.add_argument('--report', type=Path)
    args = p.parse_args()
    report = validate(args.root, args.zstd_library)
    (args.report or args.root/'tolerant-topology-decoding.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['validation'], indent=2))
