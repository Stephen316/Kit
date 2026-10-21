"""Focused literal compact seam translation proof and saved Pipe controls."""
import argparse
from collections import Counter
import copy
import json
import math
from pathlib import Path

from asm_records import inspect_asm
from decode_asm_subtypes import decode_asm_subtypes
from decode_brep import decode_topology
from decode_bspline import evaluate_curve, evaluate_surface
from decode_compact_pcurve_offsets import decode_compact_pcurve_offsets
from decode_pcurve import evaluate_pcurve
from decode_pcurve_variants import decode_compact_pcurve
from fusion_archive import read_members


def validate(root, zstd):
    checks, samples, guards = 0, [], []
    totals = Counter()
    files = sorted([*root.joinpath('pipepaths-3d11bd427946').glob('*.f3d'),
                    *root.joinpath('pipemodes-87cfa7d8d82b').glob('*.f3d'),
                    *root.joinpath('pipeedgecontrasts-5bd287323ae7').glob('*.f3d'),
                    root/'sweepguides-db118be14bfe/closed_circle.f3d'])

    def check(test, reason):
        nonlocal checks
        if not test:
            raise AssertionError(reason)
        checks += 1

    saved = None
    for filename in files:
        truth = json.loads(filename.parent.joinpath('ground_truth.json').read_text())
        check(any(s['file'] == filename.name for s in truth['samples']), 'actual saved API fixture is present')
        sample = {'file': str(filename.relative_to(root)), 'blobs': []}
        for member, blob in read_members(filename, zstd).items():
            if not member.endswith(('.smb', '.smbh')):
                continue
            parsed = inspect_asm(blob)
            original = copy.deepcopy(parsed)
            catalog = decode_asm_subtypes(blob, parsed=parsed)
            topology = decode_topology(parsed, subtype_catalog=catalog)
            nodes = {node['index']: node for node in topology['nodes']}
            original_nodes = copy.deepcopy(nodes)
            result = {'member': member, 'decoded_offsets': [], 'compact_zero_controls': [],
                      'previous_explicit_UV_cache_count': sum('uv_curve' in n for n in nodes.values()),
                      'prior_topology_unresolved': topology['unresolved']}
            totals['blobs'] += 1
            for record in parsed['records']:
                if record['section'] != 'geometry' or record['name'] != 'pcurve' or len(record['tokens']) != 7:
                    continue
                offset = [t['value'] for t in record['tokens'][5:]]
                decoded = decode_compact_pcurve_offsets(record, parsed['records'], nodes, catalog)
                if offset == [0., 0.]:
                    check(decoded == decode_compact_pcurve(record, parsed['records'], nodes, catalog), 'zero-offset default output exactly preserved')
                    result['compact_zero_controls'].append(record['index'])
                    totals['zero_offset_defaults_exact'] += 1
                    continue
                totals['new_nonzero_caches'] += 1
                surface = nodes[decoded['parent_surface_record_index']]['bspline_surface']
                edge = nodes[nodes[decoded['owning_coedge_index']]['edge_index']]
                xyz = nodes[edge['curve_index']]['bspline_curve']
                check(decoded['parameter_domain'] == xyz['parameter_domain'] == [edge['start_parameter'], edge['end_parameter']],
                      'XYZ, UV and typed edge share the same explicit stored interval; no guessed mapping')
                points = [nodes[nodes[edge[k+'_vertex_index']]['point_index']]['raw_origin'] for k in ('start', 'end')]
                measurements = []
                for q in (0., .25, .5, .75, 1.):
                    a, b = decoded['parameter_domain']
                    t = a if q == 0 else b if q == 1 else a+(b-a)*q
                    uv = evaluate_pcurve(decoded, t)
                    stored_xyz = evaluate_curve(xyz, t)
                    surface_xyz = evaluate_surface(surface, *uv)
                    raw_uv = [value-delta for value, delta in zip(uv, offset)]
                    unshifted_xyz = evaluate_surface(surface, *raw_uv)
                    error = math.dist(stored_xyz, surface_xyz)
                    check(error < 1e-12, 'independent typed support surface versus stored XYZ cache at endpoints/interiors')
                    row = {'fraction': q, 'stored_parameter': t, 'translated_UV': uv,
                           'stored_XYZ_cache': stored_xyz, 'support_surface_XYZ': surface_xyz,
                           'XYZ_cache_surface_deviation_raw': error,
                           'unshifted_UV': raw_uv, 'unshifted_surface_deviation_raw': math.dist(stored_xyz, unshifted_xyz)}
                    if q in (0., 1.):
                        endpoint_error = math.dist(stored_xyz, points[int(q)])
                        check(endpoint_error < 1e-12, 'stored XYZ endpoint agrees with typed edge vertex in stored interval order')
                        row['typed_vertex_position'] = points[int(q)]
                        row['typed_vertex_deviation_raw'] = endpoint_error
                    measurements.append(row)
                # Compare the entire two boundary rows of the stored surface grid,
                # without treating the literal axis flag as a periodicity enum.
                nv, nu = surface['control_count_v'], surface['control_count_u']
                grid = surface['raw_control_points']
                seam_errors = [math.dist(grid[v], grid[(nu-1)*nv+v]) for v in range(nv)]
                check(max(seam_errors) < 1e-12, 'all stored boundary control pairs agree to rounding, not only sampled endpoints')
                badsign_rejected = False
                try:
                    evaluate_surface(surface, decoded['raw_control_points_uv'][0][0]-offset[0], 0.)
                except ValueError:
                    badsign_rejected = True
                check(badsign_rejected, 'subtracting the literal offset is outside the stored surface chart')
                result['decoded_offsets'].append({'record_index': record['index'], 'expected_uv_cache': decoded,
                    'independent_geometry_samples': measurements, 'entire_stored_U_seam_control_pair_count': nv,
                    'maximum_stored_U_seam_control_pair_deviation_raw': max(seam_errors),
                    'opposite_offset_application_outside_stored_chart': True,
                    'scope': 'Both unshifted and shifted charts evaluate to the same seam XYZ. Literal four-corner incidence, not coordinates, distinguishes retained chart translation.'})
                if member.endswith('.smbh'):
                    saved = record, parsed['records'], nodes, catalog
            check(parsed == original, 'all original parsed records/tokens remain unchanged')
            check(nodes == original_nodes, 'all existing topology nodes and prior UV caches remain unchanged')
            sample['blobs'].append(result)
            totals['prior_UV_caches_retained'] += result['previous_explicit_UV_cache_count']
        samples.append(sample)
    record, records, nodes, catalog = saved

    def rejects(label, mutate):
        r, rs, ns, cat = copy.deepcopy((record, records, nodes, catalog))
        mutate(r, rs, ns, cat)
        try:
            decode_compact_pcurve_offsets(r, rs, ns, cat)
        except (ValueError, KeyError, IndexError) as error:
            check(True, label)
            guards.append({'guard': label, 'reason': str(error)})
        else:
            raise AssertionError('Malformed compact offset accepted: '+label)

    rejects('Opposite stored shift sign', lambda r, rs, ns, cat: r['tokens'][5].update(value=2*math.pi))
    rejects('Nonfinite stored shift', lambda r, rs, ns, cat: r['tokens'][6].update(value=float('nan')))
    rejects('Selector disagrees with captured shifted slot', lambda r, rs, ns, cat: r['tokens'][3].update(value=-2))
    base = decode_compact_pcurve_offsets(record, records, nodes, catalog)
    coedge = nodes[base['owning_coedge_index']]
    rejects('Partner no longer reciprocal', lambda r, rs, ns, cat: ns[coedge['partner_index']].update(partner_index=None))
    surface = base['parent_surface_record_index']
    rejects('Stored support chart changed', lambda r, rs, ns, cat: ns[surface]['bspline_surface'].update(parameter_domain_u=[0., 2*math.pi]))
    neighbor = next(i for i in base['compact_offset_evidence']['owning_ring_indices'] if i not in (coedge['index'], coedge['partner_index']))
    neighbor_pc = nodes[neighbor]['pcurve_index']
    rejects('Neighbor chart endpoint no longer closes the UV ring',
            lambda r, rs, ns, cat: ns[neighbor_pc]['uv_curve']['control_points_uv'][0].__setitem__(1, .125))
    target = base['parent_surface_namespace']['target_definition']['record_index']
    rejects('Stale namespace target fingerprint', lambda r, rs, ns, cat: cat['record_fingerprints'].__setitem__(str(target), 'stale'))
    return {'stage': 'Bounded compact pcurve UV seam translation',
        'interface': 'decode_compact_pcurve_offsets(record, records, nodes, subtype_catalog) -> UV cache; same call shape as existing compact reader',
        'integration': 'Keep original compact reader first. Dispatch here only after its nonzero-offset diagnostic; call before assembly/body graph consumers. Existing zero-offset reader remains unchanged. No recursive shared dispatch from the derived zero-offset proof.',
        'validation': {'checks': checks, 'saved_files': len(files), **dict(totals), 'malformed_guards': guards,
                       'API_UV_or_surface_evaluator_getters_captured': False},
        'findings': ['Two nonzero caches in the saved spline Pipe recover by explicit topology and matching blob-local surface definition, followed direct addition of the stored [-2*pi,0] vector.',
            'The upper and lower chart boundaries produce the same XYZ seam; world-coordinate agreement alone cannot determine which chart a coedge uses.',
            'The full explicit four-coedge ring has four UV corners of degree two only with the stored shift applied. Dropping it gives two degree-one and two degree-three corners.',
            'Five samples per cache independently compare translated UV evaluated on the typed parent surface with the stored parent XYZ curve; complete boundary control rows independently corroborate coincident seam geometry.',
            'The 15 related saved Pipe/closed-circle controls contain no further nonzero compact offset layout. Prepared captures or arbitrary periodic extrapolation supply no evidence here.'],
        'limitations': ['Nonzero support is bounded to captured selector -1, offset [-2*pi,0], slot0 par_int_cur, circular sweep U=[-pi,pi]/V=[0,1], reciprocal same-loop seam partners and four-segment UV chart.',
            'No general period, modulo wrapping, sign reversal or unknown axis-flag semantics are inferred. Positive V shifts, other charts/degrees/support families and ambiguous native support identities remain rejected.',
            'All comparisons evaluate stored approximation caches only. No live API evaluator, exact procedural surface or lifecycle claim is made.',
            'Two blobs of the same archive are corroborating stored representations, not two independent API experiments.'],
        'samples': samples}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    p.add_argument('--zstd-library', type=Path, required=True)
    p.add_argument('--report', type=Path)
    args = p.parse_args()
    result = validate(args.root, args.zstd_library)
    (args.report or args.root/'compact-pcurve-offset-decoding.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['validation'], indent=2))
