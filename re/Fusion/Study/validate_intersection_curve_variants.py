"""Focused two-support int_int_cur cache framing and typed endpoint checks."""

import argparse
import copy
import json
import math
from pathlib import Path

from asm_records import inspect_asm
from decode_brep import decode_topology
from decode_bspline import decode_bspline, evaluate_curve
from decode_fillet_spline_caches import decode_intersection_curve_cache
from decode_intersection_curve_variants import decode_intersection_curve_variants
from fusion_archive import read_members

ROOT = Path(__file__).resolve().parent
FILES = ['solidsweeps-5b5ecd5e01b9/solid_twist_sixty.f3d',
         'solidsweeps-7d2677669e3d/solid_twist.f3d',
         'tappedholes-409e96788503/modeled_full.f3d',
         'threadmodes-d51d2ae60564/modeled_full.f3d']


def validate(zstd_library):
    contexts = {}
    def load(relative):
        if relative not in contexts:
            contexts[relative] = {m: inspect_asm(raw) for m, raw in read_members(ROOT / relative, zstd_library).items()
                                  if m.endswith(('.smb', '.smbh'))}
        return contexts[relative]
    report = {'scope': 'Fifty-six saved remaining int_int_cur cache records in four explicit archives; ordered support/UV slots and bounded source framing',
              'integration': {'helper': 'decode_intersection_curve_variants.decode_intersection_curve_variants(record)',
                              'dispatch': 'Use as fallback only when existing decode_fillet_spline_caches.decode_intersection_curve_cache rejects int_int_cur. This preserves prior successful dictionaries exactly.',
                              'slot_contract': 'stored_supports[0/1] include slot,kind,token_start,subtype_token_start for spline,token_end,stored_definition literal tokens with original offsets. stored_embedded_uv_caches[0/1] preserveNone for nullbs; stored_uv_slot_spans match raw source positions.',
                              'compact_pcurve_resolution': 'A separate source-ordered subtype catalog may resolve explicit support identity; this helper does not choose UV slots by geometry or map inline refs to global IDs.',
                              'validation_command': '/usr/bin/python3 validate_intersection_curve_variants.py',
                              'shared_edits_by_this_task': False},
              'native_framing': {'xyz': 'Non-rational clamped cubic form0 XYZ NUBS cache, version23100 and enum0.',
                                 'supports': 'Exactly two independently bounded plane or spline/ref or strict inline-sweep descriptions. Plane sense flag and four optional bounds, or spline wrapper/subtype and four optional bounds, remain literal.',
                                 'uv': 'Exactly two ordered non-rational cubic form0 UV-cache/nullbs fields; absent slots are not compacted.',
                                 'tail': 'Two optional-double flags/values, four counted scalar lists, exact subtype end, two optional outer bounds and exact record exhaustion.'},
              'catalog': [], 'representative_caches': [], 'typed_endpoint_checks': [], 'old_output_controls': [], 'guards': [],
              'limitations': ['Stored XYZ/UV/sweep surface caches are approximations; exact procedural intersection and global error bounds remain unresolved.',
                              'Inline support refs are in a separate source-ordered namespace. No body/surface identity or UV-slot role is inferred from numerical coincidences.',
                              'Raw wrapper, sense, optional bounds and trailer flags remain literal; no edge/cache sign mapping or current-state semantics are installed.',
                              'The actual API fixtures contain modeling controls, with no independent cache/evaluator getter equality asserted by this report.',
                              'Endpoint tests use only explicit edge/vertex/point links and native parameters inside the stored cache domain. Other parameter correspondences remain unresolved.',
                              'Assembly placements, active/final lifecycle, exact trimming and regeneration are outside this helper.']}
    source_records, decoded = {}, {}
    for relative in FILES:
        for member, parsed in load(relative).items():
            assert parsed['complete_token_stream']
            for record in parsed['records']:
                if record['name'] != 'intcurve-curve' or record['section'] != 'geometry' or record['tokens'][5].get('value') != 'int_int_cur':
                    continue
                cache = decode_intersection_curve_variants(record)
                key = relative, member, record['index']
                source_records[key] = record; decoded[key] = cache
                uv = cache['stored_embedded_uv_caches']
                supports = cache['stored_supports']
                assert len(uv) == len(supports) == 2
                for slot, support in enumerate(supports):
                    assert support['slot'] == slot
                    assert support['stored_definition'] == record['tokens'][support['token_start']:support['token_end']]
                    if support['kind'] == 'spline':
                        assert record['tokens'][support['subtype_token_start']]['kind'] == 'subtype_start'
                for grid in [cache]+[c for c in uv if c is not None]:
                    a, b = grid['parameter_domain']
                    parameters = [a]+[a+(b-a)*i/4 for i in (1, 2, 3)]+[b]
                    assert all(math.isfinite(v) for parameter in parameters for v in evaluate_curve(grid, parameter))
                entry = {'file': relative, 'member': member, 'record_index': record['index'],
                         'xyz_controls': len(cache['raw_control_points']), 'xyz_domain': cache['parameter_domain'],
                         'support_kinds': [s.get('procedural_subtype', s['kind']) for s in supports],
                         'support_token_spans': [[s['token_start'], s['token_end']] for s in supports],
                         'uv_controls_by_slot': [len(c['raw_control_points']) if c is not None else None for c in uv],
                         'trailer_optional_flags': cache['stored_trailer_optional_flags'],
                         'trailer_optional_scalars': cache['stored_trailer_optional_scalars']}
                report['catalog'].append(entry)
                # One representative for each old failure grammar/layout.
                shape = (tuple(entry['support_kinds']), tuple(c is not None for c in uv), tuple(entry['trailer_optional_flags']))
                existing = [s['shape'] for s in report['representative_caches']]
                label = repr(shape)
                if label not in existing:
                    report['representative_caches'].append({'shape': label, 'file': relative, 'member': member,
                                                           'record_index': record['index'], 'cache': cache})
    assert len(decoded) == 56
    for relative in FILES:
        for member, parsed in load(relative).items():
            nodes = {n['index']: n for n in decode_topology(parsed)['nodes']}
            for edge in nodes.values():
                key = relative, member, edge.get('curve_index')
                if edge['kind'] != 'edge' or key not in decoded:
                    continue
                cache = decoded[key]; domain = cache['parameter_domain']
                parameters = [edge['start_parameter'], edge['end_parameter']]
                vertices = [nodes[edge[which+'_vertex_index']] for which in ('start', 'end')]
                points = [nodes[v['point_index']] for v in vertices]
                assert all(v['kind'] == 'vertex' and p['kind'] == 'point' for v, p in zip(vertices, points))
                check = {'file': relative, 'member': member, 'curve_index': key[2], 'edge_index': edge['index'],
                         'vertex_indices': [v['index'] for v in vertices], 'point_indices': [p['index'] for p in points],
                         'native_edge_parameters': parameters, 'cache_domain': domain,
                         'raw_endpoint_points': [p['raw_origin'] for p in points]}
                if all(domain[0] <= parameter <= domain[1] for parameter in parameters):
                    values = [evaluate_curve(cache, parameter) for parameter in parameters]
                    errors = [math.dist(v, p['raw_origin']) for v, p in zip(values, points)]
                    check.update(cache_evaluations=values, direct_parameter_errors_raw=errors,
                                 direct_parameter_matches_within1e_8=max(errors) < 1e-8)
                else:
                    check['status'] = 'unresolved_edge_cache_parameter_correspondence'
                report['typed_endpoint_checks'].append(check)
    for relative in ['edgemodes-52695761f185/fillet_curvature.f3d',
                     'edgemodes-87edbf67527b/fillet_chord.f3d', 'edgemodes-87edbf67527b/fillet_asymmetric.f3d']:
        for member, parsed in load(relative).items():
            if not member.endswith('.smbh'):
                continue
            for index in (42, 79):
                record = parsed['records'][index]
                previous = decode_intersection_curve_cache(record)
                assert decode_bspline(record) == previous
                report['old_output_controls'].append({'file': relative, 'member': member, 'record_index': index,
                                                       'exact_existing_reader_dictionary_equality': True})
    base_key = next(k for k in source_records if k[0] == FILES[0] and k[2] == 130)
    base, base_cache = source_records[base_key], decoded[base_key]
    def reject(label, record, mutate):
        changed = copy.deepcopy(record); mutate(changed['tokens'])
        try:
            decode_intersection_curve_variants(changed)
        except (ValueError, IndexError) as error:
            report['guards'].append({'case': label, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError('Malformed intersection variant accepted: '+label)
    reject('Negative first support ref', base, lambda t: t[41].update(value=-1))
    reject('Unknown second support kind', base, lambda t: t[49].update(value='unknown_surface'))
    reject('Optional finite support bound has wrong type', base, lambda t: t[46].update(kind='integer'))
    reject('UV control knot multiplicity exceeds cubic degree', base, lambda t: t[63].update(value=4))
    reject('Optional trailer scalar has wrong type', base, lambda t: t[85].update(kind='integer'))
    reject('Trailing unsupported data', base, lambda t: t.append({'kind': 'integer', 'value': 0}))
    errors = [e for check in report['typed_endpoint_checks'] for e in check.get('direct_parameter_errors_raw', [])]
    report['summary'] = {'saved_files': len(FILES), 'new_intersection_caches': len(decoded),
                         'ordered_support_slots': 2*len(decoded),
                         'populated_uv_slots': sum(sum(c is not None for c in cache['stored_embedded_uv_caches']) for cache in decoded.values()),
                         'absent_uv_slots_preserved': sum(sum(c is None for c in cache['stored_embedded_uv_caches']) for cache in decoded.values()),
                         'inline_sweep_support_slots': sum(sum(s.get('procedural_subtype') == 'sweep_sur' for s in cache['stored_supports']) for cache in decoded.values()),
                         'typed_edges_checked': len(report['typed_endpoint_checks']),
                         'direct_native_parameter_endpoint_evaluations': len(errors),
                         'direct_endpoint_matches_within1e_8': sum(e < 1e-8 for e in errors),
                         'maximum_direct_parameter_endpoint_error_raw': max(errors) if errors else None,
                         'unresolved_parameter_edges': sum(c.get('status') == 'unresolved_edge_cache_parameter_correspondence' for c in report['typed_endpoint_checks']),
                         'old_reader_outputs_preserved': len(report['old_output_controls']), 'malformed_guards': len(report['guards'])}
    assert errors
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='intersection-curve-variant-decoding.json')
    args = parser.parse_args()
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    report = validate(str(zstd))
    Path(args.output).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], sort_keys=True))
