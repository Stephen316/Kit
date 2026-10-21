"""Focused offline checks for same-asset native sculpt source provenance."""

import argparse
import copy
from collections import Counter
import json
from pathlib import Path
import struct

from decode_basics import decode_basics
from decode_boundary_sculpt_provenance import decode_boundary_sculpt_provenance, SCOPE
from fusion_archive import read_members
from fusion_metadata import design_records


def validate(root, zstd):
    previous = json.loads((root/'sculpt-tool-attribute-decoding.json').read_text())
    api = {s['file']: s for s in json.loads((root/'boundaryfills-a0953038318b/ground_truth.json').read_text())['samples']}
    checks, rows, counts, captures = 0, [], Counter(), {}

    def check(test, reason):
        nonlocal checks
        if not test:
            raise AssertionError(reason)
        checks += 1

    def load(file):
        members = read_members(file, zstd)
        full = decode_basics(file, zstd)
        s = full['streams'][0]
        data = members[s['member']]
        records, _ = design_records(data, members[s['member'].replace('BulkStream.dat', 'MetaStream.dat')])
        return data, records, members, s

    def run(capture):
        d, rs, ms, s = capture
        return decode_boundary_sculpt_provenance(d, rs, s['member'], ms, s['features'], s['body_blob_bindings'])

    for old in previous['samples']:
        name = old['file']
        capture = load(root/name)
        captures[Path(name).name] = capture
        d, rs, ms, s = capture
        saved_features = copy.deepcopy(s['features'])
        saved_mappings = copy.deepcopy(s['body_blob_bindings'])
        result = run(capture)
        check(result['unresolved'] == [], 'no unexpected provenance feature failures')
        check(len(result['decoded']) == 1, 'one bounded source-provenance feature group')
        check(s['features'] == saved_features and s['body_blob_bindings'] == saved_mappings, 'source summaries remain unmodified')
        group = result['decoded'][0]
        check(group['history_blob_member'] == old['member'], 'same explicit blob as independent prior owner audit')
        lookup = {a['attribute_record_index']: a for a in old['expected_output']['attributes']}
        comparisons = {a['attribute_record_index']: a for a in old['numeric_correspondences']}
        seen = set()
        for a in group['attributes']:
            original = lookup[a['attribute_record_index']]
            comparison = comparisons[a['attribute_record_index']]
            check(a['stored_signed_int64'] > 0, 'only positive exact IDs are associated')
            check(all(a[k] == original[k] for k in ('geometry_entity_ordinal', 'section', 'stored_signed_int64',
                    'face_owner_record_index', 'face_owner_entity_ordinal', 'snapshot_topology', 'journal_mentions')),
                  'independent prior face-owner/journal provenance remains exact')
            check(a['snapshot_topology']['body_stored_entity_id'] == -1, 'ASM owner BODY identity never replaced with native source identity')
            check(len(a['source_tools']) == 1, 'captured source selection correspondence unique within this feature')
            tool = a['source_tools'][0]
            key = 'native_body_object_id' if tool['kind'] == 'Body' else 'native_plane_object_id'
            check(tool[key] == a['stored_signed_int64'] == comparison[key], 'new production association agrees with prior independent numeric comparison')
            for key in ('selection_record_object_id', 'descriptor_object_id'):
                check(tool[key] == comparison[key], 'source proxy/descriptor chain agrees with prior audit')
            if tool['kind'] == 'Body':
                check(tool['body_anchor_object_id'] == comparison['body_anchor_object_id'], 'source BODY anchor agrees independently')
            else:
                check(tool['terminal_object_id'] == comparison['terminal_object_id'], 'source plane terminal agrees independently')
                check(tool['name'] in api[Path(name).name]['tool_names'], 'actual saved API ToolPlane name agrees')
            counts['positive_attributes'] += 1
            counts[tool['kind']] += 1
            seen.add(a['attribute_record_index'])
        unresolved = result['unresolved_attributes']
        check(len(unresolved) == (1 if Path(name).stem == 'plane_first' else 0), 'negative literal alone remains unresolved')
        if unresolved:
            item = unresolved[0]
            check(item['stored_signed_int64'] == -282 and item['magnitude_only_candidates'][0]['native_plane_object_id'] == 282,
                  'negative workplane magnitude is a candidate only')
            check('native_plane_object_id' not in item and item['attribute_record_index'] not in seen,
                  'negative literal never promoted to a resolved source identity')
            counts['unresolved_negative_literals'] += 1
        check(seen | {a['attribute_record_index'] for a in unresolved} == set(lookup), 'every source attribute accounted without omission')
        rows.append({'file': name, 'actual_API_tool_names': api[Path(name).name]['tool_names'], 'expected_output': result})
    # Explicitly verify initial auxiliary-plane publication, separate from owner.
    plane = next(r['expected_output']['decoded'][0] for r in rows if r['file'].endswith('/plane_first.f3d'))
    initial = next(a for a in plane['attributes'] if a['section'] == 'geometry')
    check(initial['face_owner_record_index'] == 15 and initial['attribute_record_index'] == 21,
          'initial auxiliary plane face/attribute retain original initial ASM indices')
    check(initial['source_tools'][0]['native_plane_object_id'] == 282 and initial['snapshot_topology']['body_record_index'] == 2
          and initial['snapshot_topology']['body_stored_entity_id'] == -1, 'plane source provenance does not fabricate an owning native BODY')
    controls = []
    for name in ('body_full', 'body_negative'):
        empty = run(load(root/'circularmodes-45f859c1f1b6'/(name+'.f3d')))
        check(empty['decoded'] == [] and empty['unresolved'] == [] and empty['unresolved_attributes'] == [], 'non-BoundaryFill is an exact empty result')
        controls.append('circularmodes-45f859c1f1b6/'+name+'.f3d')
    guards = []
    d, rs, ms, s = captures['plane_first.f3d']
    baseline = run((d, rs, ms, s))
    mapping = baseline['decoded'][0]['blob_context']

    def guarded(label, capture, predicate):
        value = run(capture)
        check(predicate(value), label)
        guards.append({'guard': label, 'feature_failures': value['unresolved'],
                       'unresolved_attribute_count': len(value['unresolved_attributes'])})

    changed = copy.deepcopy(s)
    changed['body_blob_bindings']['decoded'][0]['history_blob_member'] = 'OtherAsset/'+mapping['stored_history_filename']
    guarded('Supplied mapping points outside raw same-asset filename', (d, rs, ms, changed), lambda r: not r['decoded'] and bool(r['unresolved']))
    changed_bytes = bytearray(d)
    # read_string is UTF-16; preserve extent while changing only the first letter.
    filename_offset = mapping['mapping_filename_offset']
    struct.pack_into('<H', changed_bytes, filename_offset+4, ord('X'))
    changed_members = dict(ms)
    changed_members[s['member']] = bytes(changed_bytes)
    guarded('Stored filename changes while decoded mapping is stale', (bytes(changed_bytes), rs, changed_members, s), lambda r: not r['decoded'] and bool(r['unresolved']))
    source = next(a['source_tools'][0] for a in plane['attributes'] if a['source_tools'][0]['kind'] == 'Body')
    anchor = next(r for r in rs if r.is_primary and r.object_id == source['body_anchor_object_id'])
    changed_bytes = bytearray(d)
    struct.pack_into('<Q', changed_bytes, anchor.body+81, 282)
    changed_members = dict(ms)
    changed_members[s['member']] = bytes(changed_bytes)
    guarded('Body anchor native reference points to plane class', (bytes(changed_bytes), rs, changed_members, s), lambda r: not r['decoded'] and bool(r['unresolved']))
    source_plane = initial['source_tools'][0]
    terminal = next(r for r in rs if r.is_primary and r.object_id == source_plane['terminal_object_id'])
    changed_bytes = bytearray(d)
    struct.pack_into('<Q', changed_bytes, terminal.body+2, 275)
    changed_members = dict(ms)
    changed_members[s['member']] = bytes(changed_bytes)
    guarded('Plane terminal numeric ID points to a BODY instead of ConstructionPlane', (bytes(changed_bytes), rs, changed_members, s),
        lambda r: bool(r['unresolved']) and all(t['kind'] != 'ConstructionPlane' for g in r['decoded'] for a in g['attributes'] for t in a['source_tools']))
    blob_member = plane['history_blob_member']
    positive = next(a for a in plane['attributes'] if a['attribute_name'] == 'SCULPT_TOOL_BODY')
    changed_blob = bytearray(ms[blob_member])
    struct.pack_into('<q', changed_blob, positive['value_token_offset']+1, 355)  # Valid BODY, not a source tool.
    changed_members = dict(ms)
    changed_members[blob_member] = bytes(changed_blob)
    guarded('Valid resulting native BODY ID is not accepted as a selected source', (d, rs, changed_members, s),
        lambda r: any(a['attribute_record_index'] == positive['attribute_record_index'] for a in r['unresolved_attributes'])
          and all(t.get('native_body_object_id') != 355 for g in r['decoded'] for a in g['attributes'] for t in a['source_tools']))
    return {'stage': 'Boundary Fill native sculpt source provenance', 'scope': SCOPE,
        'integration': {'module': 'decode_boundary_sculpt_provenance.py',
            'signature': 'decode_boundary_sculpt_provenance(data, records, member, members, features, body_bindings)',
            'placement': 'After native Boundary Fill/construction geometry and body-binding recovery. Output is a separate stream summary; attach per-feature only via explicit feature_object_id.',
            'returns': 'decoded feature/blob/attribute groups, unresolved_attributes, unresolved, scope',
            'mutation': 'None; no shared source changes, reindexing or topology/body owner replacement'},
        'evidence': ['Every positive value equals a native selected tool reached independently through its counted owned selection chain.',
            'A raw typed mapping names the exact same-asset history blob. All historical body tools retain references to that mapping collection, even when tools are absent from active lists.',
            'The initial auxiliary workplane face may carry observed source provenance for native plane 282, while its own auxiliary ASM BODY remains unnumbered.',
            'Negative workplane literal -282 is unresolved; only magnitude-based candidate selections are retained.',
            'Source-selection correspondence is not exclusive attribution that the feature generated a particular history face. Multiple matching selections are preserved independently.'],
        'validation': {'checks': checks, 'saved_archives': len(rows), **dict(counts), 'empty_controls': controls, 'guards': guards,
            'independent_evidence': 'Prior 297-attribute owner/journal audit plus raw native selection/mapping records and saved API tool names. No new API calls/captures.'},
        'samples': rows}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--zstd-library', type=Path, required=True)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    p.add_argument('--report', type=Path)
    args = p.parse_args()
    report = validate(args.root, args.zstd_library)
    (args.report or args.root/'boundary-sculpt-provenance-decoding.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['validation'], indent=2))
