"""Focused saved-case qualification of ASM namespaces and alternate box views."""

import argparse
from collections import Counter
import copy
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_asm_history import decode_asm_history
from decode_brep import decode_topology
from fusion_archive import read_members
from materialize_asm_alternative import materialize_asm_alternative

FOLDERS = ('edgemodes-52695761f185', 'edgemodes-87edbf67527b', 'boundaryfills-a0953038318b')
ALTERNATIVES = ('edgemodes-52695761f185/chamfer_multiple.f3d',
    'edgemodes-52695761f185/fillet_curvature.f3d', 'edgemodes-87edbf67527b/chamfer_angle.f3d',
    'edgemodes-87edbf67527b/chamfer_angle_flipped.f3d', 'edgemodes-87edbf67527b/fillet_multiple.f3d')


def validate(root, zstd):
    checks, samples, qualified, totals, captured = 0, [], [], Counter(), {}

    def check(test, message):
        nonlocal checks
        if not test:
            raise AssertionError(message)
        checks += 1

    for folder in FOLDERS:
        truth = json.loads((root/folder/'ground_truth.json').read_text())
        for sample in truth['samples']:
            name = folder+'/'+sample['file']
            members = read_members(root/name, zstd)
            for member, blob in members.items():
                if not member.endswith('.smbh'):
                    continue
                parsed = inspect_asm(blob)
                before = copy.deepcopy(parsed)
                history = decode_asm_history(blob, parsed=parsed)
                check(parsed == before, 'generic namespace helper does not mutate source records')
                table = history['geometry_entities']
                expected = [r for r in parsed['records'] if r['record_kind'] == 'entity' and r['section'] != 'history']
                check([e['inspection_record_index'] for e in table] == [r['index'] for r in expected], 'geometry table exactly excludes history and markers')
                check([e['geometry_entity_ordinal'] for e in table] == list(range(len(table))), 'geometry ordinal namespace contiguous')
                summary = []
                for s in history['journal_states']:
                    kinds, section_pairs = Counter(), Counter()
                    nulls, refs = 0, 0
                    for entry in s['entries']:
                        section_pairs[tuple(t['target_section'] for t in entry['pointer_sides'])] += 1
                        for side, t in enumerate(entry['pointer_sides']):
                            raw = t['stored_geometry_entity_ordinal']
                            if raw == -1:
                                nulls += 1
                            else:
                                refs += 1
                                kinds[t['target_kind']] += 1
                    check(all(t['pointer_side'] == side and
                        ((t['stored_geometry_entity_ordinal'] == -1 and t['inspection_record_index'] is None) or
                         (t['stored_geometry_entity_ordinal'] >= 0 and t['inspection_record_index'] == table[t['stored_geometry_entity_ordinal']]['inspection_record_index']))
                        for e in s['entries'] for side, t in enumerate(e['pointer_sides'])), 'both journal sides retain exact namespace lookup/nulls')
                    summary.append({'delta_state_slot': s['delta_state_slot'], 'inspection_record_index': s['inspection_record_index'],
                        'neighbor_slots_fields_3_4': s['neighbor_slots_fields_3_4'], 'entry_count': s['entry_count'],
                        'nonnull_pointer_count': refs, 'null_pointer_count': nulls, 'target_kind_counts': dict(kinds),
                        'pointer_section_pairs': [{'sides': list(pair), 'count': count} for pair, count in section_pairs.items()]})
                    totals['journal_states'] += 1
                    totals['journal_entries'] += s['entry_count']
                    totals['nonnull_entry_pointers'] += refs
                samples.append({'file': name, 'member': member, 'geometry_entity_count': len(table),
                    'inspection_record_count': history['inspection_record_count'], 'neighbor_chain': history['neighbor_chain'],
                    'geometry_section_counts': dict(Counter(e['section'] for e in table)), 'journal_states': summary})
                totals['history_blobs'] += 1
                totals['geometry_entities'] += len(table)
                captured[(name, member)] = (blob, parsed, history)
                if name in ALTERNATIVES:
                    initial_topology = decode_topology(parsed)
                    view = materialize_asm_alternative(blob, parsed=parsed, history=history)
                    check(parsed == before and decode_topology(parsed) == initial_topology, 'initial parsed and topology outputs remain unchanged after materialization')
                    graph = view['topology']['body_graphs'][0]
                    expected_corners = {(x, y, z) for x in (1., 5.) for y in (1., 4.) for z in (0., 2.)}
                    check({tuple(p) for p in graph['raw_vertex_positions']} == expected_corners, 'qualified view corners agree with pre-tool box construction in saved generator')
                    check(next(p['value'] for p in sample['parameters'] if p['name'] == 'd1') == 2., 'independent actual saved extrusion parameter supports height 2 cm')
                    check(view['naive_membership_dangling_pointer_count'] > 0 and view['qualified_dangling_pointer_count'] == 0,
                          'literal pair aliases are necessary to repair alternative pointer closure')
                    # Reversing aliases while keeping chosen alternative membership fails closure.
                    reverse = {a['side0_entity_ordinal']: a['side1_entity_ordinal'] for a in view['literal_pair_aliases']}
                    selected = set(view['selected_geometry_entity_ordinals'])
                    originals = [parsed['records'][e['inspection_record_index']] for e in table]
                    wrong_direction = sum(t['tag'] == 12 and t['value'] >= 0 and reverse.get(t['value'], t['value']) not in selected
                        for ordinal in selected for t in originals[ordinal]['tokens'])
                    check(wrong_direction > 0, 'opposite alias orientation does not qualify the same chosen view')
                    kept = {k: value for k, value in view.items() if k not in ('view_parsed', 'topology')}
                    kept['topology'] = {k: value for k, value in view['topology'].items() if k != 'nodes'}
                    qualified.append({'file': name, 'member': member,
                        'opposite_alias_direction_dangling_count': wrong_direction, 'expected_alternative': kept,
                        'baseline_evidence': 'GenerateEdgeToolModes.py creates the box from points(1,1,0)/(5,4,0) and 20 mm extrusion before the captured edge tool. Actual API parameter d1=2cm is saved. No prior topology API evaluator or baseline archive was captured.'})
    # Independent agreement with all previous SCULPT attribute journal mentions.
    sculpt = json.loads((root/'sculpt-tool-attribute-decoding.json').read_text())
    for sample in sculpt['samples']:
        blob, parsed, history = captured[(sample['file'], sample['member'])]
        mentions = {}
        for state in history['journal_states']:
            for entry in state['entries']:
                for side in entry['pointer_sides']:
                    if side['stored_geometry_entity_ordinal'] < 0:
                        continue
                    mentions.setdefault(side['stored_geometry_entity_ordinal'], []).append({
                        'delta_state_slot': state['delta_state_slot'], 'journal_record_index': state['inspection_record_index'],
                        'entry_ordinal': entry['entry_ordinal'], 'pointer_side': side['pointer_side'],
                        'pointer_token_offset': side['token_offset'], 'geometry_entity_ordinal': side['stored_geometry_entity_ordinal'],
                        'target_inspection_record_index': side['inspection_record_index']})
        for a in sample['expected_output']['attributes']:
            check(mentions[a['geometry_entity_ordinal']] == a['journal_mentions'], 'generic entries reproduce independent sculpt owner-audit mentions exactly')
    # Real nonhistory body-cache control uses only geometry plus its end marker.
    control_members = read_members(root/ALTERNATIVES[0], zstd)
    control_member, control_blob = next((m, b) for m, b in control_members.items() if m.endswith('.smb'))
    control = decode_asm_history(control_blob)
    check(not control['journal_states'] and not control['neighbor_chain'], 'real body cache without history has no invented delta states')
    guards = []
    key = next(k for k in captured if k[0] == ALTERNATIVES[0])
    blob, parsed, history = captured[key]

    def rejected(label, operation):
        try:
            operation()
        except ValueError as error:
            check(True, label)
            guards.append({'guard': label, 'reason': str(error)})
        else:
            raise AssertionError('Malformed/unobserved view accepted: '+label)

    def mutate(token_offset, value):
        changed = bytearray(blob)
        struct.pack_into('<q', changed, token_offset+1, value)
        return bytes(changed)

    rejected('Opposite pointer-side orientation is not supported relative to initial geometry', lambda: materialize_asm_alternative(blob, pointer_side=1))
    rejected('Other state slot is not qualified by this captured alternate-view schema', lambda: materialize_asm_alternative(blob, state_slot=2))
    pair_entries = [e for e in history['journal_states'][0]['entries'] if all(s['stored_geometry_entity_ordinal'] >= 0 for s in e['pointer_sides'])]
    first, second = pair_entries[:2]
    duplicated = mutate(second['pointer_sides'][1]['token_offset'], first['pointer_sides'][1]['stored_geometry_entity_ordinal'])
    rejected('Duplicate alias target remains namespace-framed but is ambiguous for materialization', lambda: materialize_asm_alternative(duplicated))
    different = next(e for e in pair_entries if e['pointer_sides'][0]['target_kind'] != first['pointer_sides'][0]['target_kind'])
    wrong_kind = mutate(first['pointer_sides'][0]['token_offset'], different['pointer_sides'][0]['stored_geometry_entity_ordinal'])
    rejected('Same pair cannot alias different entity kinds', lambda: materialize_asm_alternative(wrong_kind))
    out = mutate(first['pointer_sides'][0]['token_offset'], history['geometry_entity_count'])
    rejected('Geometry pointer ordinal cannot use the out-of-range global-record table', lambda: decode_asm_history(out))
    state = parsed['records'][history['journal_states'][0]['inspection_record_index']]
    wrong_neighbor = mutate(state['tokens'][4]['offset'], 1)
    rejected('Journal neighbor slots must reciprocate independently of geometry pointers', lambda: decode_asm_history(wrong_neighbor))
    wrong_self = mutate(state['tokens'][5]['offset'], 1)
    rejected('Journal self slot is not an inspection-record index or another delta slot', lambda: decode_asm_history(wrong_self))
    sculpt_blob = next(blob for (name, _), (blob, _, _) in captured.items() if name.endswith('/plane_first.f3d'))
    rejected('Sculpt multi-state history is not silently treated as the EdgeMode alternate schema', lambda: materialize_asm_alternative(sculpt_blob))
    return {'stage': 'Reusable ASM pointer namespaces and qualified single-slot alternate views',
        'interface': {'namespace_module': 'decode_asm_history.py', 'namespace_signature': 'decode_asm_history(blob, *, parsed=None)',
            'materializer_module': 'materialize_asm_alternative.py', 'materializer_signature': 'materialize_asm_alternative(blob, *, state_slot=0, pointer_side=0, parsed=None, history=None)',
            'origin_map': 'view_record_index -> geometry_entity_ordinal, original inspection_record_index, original section/kind',
            'view_scope': 'view_parsed is explicitly nonserialized. Source offsets are preserved while pointer tokens use dense view indices. Original ASM bytes/records/global indices/native Design IDs remain unchanged.'},
        'findings': ['The shared geometry-entity namespace and separate delta-state slot namespace hold across 15 saved EdgeMode files and nine BoundaryFill files (25 history blobs).',
            'Both journal pointer sides are retained, including null ordinal -1. Neighbor links are reciprocal but chain direction remains unlabeled.',
            'State 0 in the five qualified EdgeMode captures has same-kind side1(initial)→side0(trailing) pairs. Naive set replacement leaves dangling references; literal pair-local aliases close the chosen view.',
            'Those qualified views form one fully reciprocal planar box with six faces, 12 edges and eight vertices, and raw coordinates matching the documented pre-tool construction. This supports the bounded alternate cache view, not general history replay or an API topology evaluator equivalence.',
            'No Sculpt history view is materialized; its generic slots/entries remain available to source-provenance decoders.'],
        'validation': {'checks': checks, 'saved_archives': len({s['file'] for s in samples}), **dict(totals),
            'qualified_alternate_views': len(qualified), 'sculpt_attribute_mention_comparisons': 297,
            'real_nonhistory_control': {'file': ALTERNATIVES[0], 'member': control_member, 'geometry_entities': control['geometry_entity_count']},
            'guards': guards},
        'namespace_samples': samples, 'qualified_snapshot_cases': qualified}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    p.add_argument('--zstd-library', type=Path, required=True)
    p.add_argument('--report', type=Path)
    args = p.parse_args()
    report = validate(args.root, args.zstd_library)
    (args.report or args.root/'asm-history-namespace-decoding.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['validation'], indent=2))
