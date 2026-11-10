"""Focused saved-file validation for typed sculpt attributes; no Fusion calls."""

import argparse
from collections import Counter
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_basics import decode_basics
from decode_body_properties import BODY
from decode_sculpt_tool_attributes import decode_sculpt_tool_attributes
from fusion_archive import read_members
from fusion_metadata import design_records


def validate(root, zstd):
    audit = json.loads((root/'asm-int64-investigation.json').read_text())
    expected = {(o['file'], o['member'], o['record_index']): o for o in audit['observations']}
    truth = json.loads((root/'boundaryfills-a0953038318b/ground_truth.json').read_text())
    api = {s['file']: s for s in truth['samples']}
    rows, seen, checks, counts = [], set(), 0, Counter()

    def check(test, reason):
        nonlocal checks
        if not test:
            raise AssertionError(reason)
        checks += 1

    for name in sorted({o['file'] for o in audit['observations']}):
        file = root/name
        members = read_members(file, zstd)
        full = decode_basics(file, zstd)
        sample = api[file.name]
        stream = full['streams'][0]
        data = members[stream['member']]
        records, _ = design_records(data, members[stream['member'].replace('BulkStream.dat', 'MetaStream.dat')])
        primary = {r.object_id: r for r in records if r.is_primary}
        boundary = stream['boundary_fill_results']['decoded']
        check(len(boundary) == 1, 'one explicitly decoded Boundary Fill per saved file')
        feature = next(f for f in stream['features'] if f['object_id'] == boundary[0]['feature_object_id'])
        bodies = {b['native_body_object_id']: b for b in boundary[0]['historical_body_tools']}
        body_names = {}
        for item in stream['tool_body_inputs']['decoded']:
            if item['feature_object_id'] == feature['object_id']:
                for group in item['body_selection_groups']:
                    for b in group['bodies']:
                        body_names[b['native_body_object_id']] = b['body_properties']['name']
        planes = {t['selection']['entity']['object_id']: t for t in feature['tool_settings']['tools']
                  if t['kind'] == 'ConstructionPlane' and t['selection'] is not None}
        check(all(primary[identity].class_guid == BODY for identity in bodies), 'tool IDs are typed native BODY objects')
        check(all(primary[identity].class_guid == '8D424E29-DE23-4B1F-A3AD-84C52A497D1A' for identity in planes),
              'plane IDs are typed native construction planes')
        names = set(body_names.values()) | {t['selection']['entity']['name'] for t in planes.values()}
        check(names == set(sample['tool_names']), 'native selected tool names agree with independent saved API truth')
        for member, blob in members.items():
            if not member.endswith('.smbh'):
                continue
            counts['history_blobs'] += 1
            result = decode_sculpt_tool_attributes(blob)
            if not result['attributes']:
                check(result['unresolved'] == [], 'attribute-free component history remains an empty result')
                continue
            check(member.split('/Breps.BlobParts/')[0] == stream['member'].split('/FusionDesignSegmentType1/')[0],
                  'native and ASM numeric comparison is scoped to the same explicit asset')
            comparisons = []
            for a in result['attributes']:
                key = (name, member, a['attribute_record_index'])
                check(key in expected, 'attribute has an independent previous raw-int64 inventory entry')
                e = expected[key]
                check((a['attribute_name'], a['stored_signed_int64'], a['raw_value_hex'], a['value_token_offset']) ==
                      (e['attribute_name'], e['signed_int64'], e['raw_64bit_hex'], e['token_offset']), 'exact value/offset/raw bytes agree')
                seen.add(key)
                check(a['snapshot_topology']['body_stored_entity_id'] == -1,
                      'source tag number is distinct from unnumbered owning snapshot BODY identifier')
                check(len(a['journal_mentions']) == (1 if a['section'] == 'geometry' else 2),
                      'one initial or two trailing literal journal mentions in this captured schema')
                value = a['stored_signed_int64']
                if a['attribute_name'] == 'SCULPT_TOOL_BODY':
                    check(value in bodies, 'positive body tag exactly equals explicitly selected native historical BODY tool ID')
                    b = bodies[value]
                    comparison = {'native_body_object_id': value, 'selection_record_object_id': b['selection_record_object_id'],
                        'descriptor_object_id': b['descriptor_object_id'], 'body_anchor_object_id': b['body_anchor_object_id'],
                        'source_owner_object_id': b['source_owner_object_id'], 'name': body_names[value],
                        'evidence': 'Exact numeric equality with typed native historical body tool proven independently by proxy/descriptor/anchor links',
                        'scope': 'Face source provenance correspondence; not replacement of owning snapshot BODY identity'}
                elif value > 0:
                    check(value in planes, 'positive workplane value exactly equals independently selected native plane ID')
                    t = planes[value]
                    comparison = {'native_plane_object_id': value, 'name': t['selection']['entity']['name'],
                        'selection_record_object_id': t['selection_record_object_id'],
                        'descriptor_object_id': t['descriptor_object_id'], 'terminal_object_id': t['selection']['terminal_object_id'],
                        'evidence': 'Exact numeric equality with typed native construction plane reached through explicit proxy/descriptor/terminal chain',
                        'scope': 'Literal positive plane tag correspondence; no current selected-cell side inferred'}
                else:
                    check(value == -282 and -value in planes, 'captured negative workplane literal magnitude equals independently selected plane ID')
                    comparison = {'stored_negative_literal': value, 'magnitude_only_native_plane_candidate': -value,
                        'scope': 'Magnitude coincidence retained separately. Signed encoding, polarity and selected-cell side remain unresolved'}
                comparisons.append({'attribute_record_index': a['attribute_record_index'], **comparison})
                counts['attributes'] += 1
                counts[a['attribute_name']] += 1
                counts[a['section']] += 1
                counts['journal_mentions'] += len(a['journal_mentions'])
            rows.append({'file': name, 'member': member, 'feature_object_id': feature['object_id'],
                         'actual_API_tool_names': sample['tool_names'],
                         'numeric_correspondences': comparisons, 'expected_output': result})
    check(seen == set(expected), 'all 297 inventoried attributes covered without adding invented results')
    # Controlled corruptions target different namespaces and chain obligations.
    fixture = root/'boundaryfills-a0953038318b/plane_first.f3d'
    member, blob = next((m, b) for m, b in read_members(fixture, zstd).items() if m.endswith('.smbh'))
    parsed = inspect_asm(blob)
    result = decode_sculpt_tool_attributes(blob, parsed=parsed)
    initial = next(a for a in result['attributes'] if a['section'] == 'geometry')
    trailing = next(a for a in result['attributes'] if a['section'] == 'trailing_states')
    guards = []

    def reject(label, offset, replacement):
        changed = bytearray(blob)
        changed[offset:offset+len(replacement)] = replacement
        try:
            decode_sculpt_tool_attributes(bytes(changed))
        except ValueError as error:
            guards.append({'guard': label, 'rejected_reason': str(error)})
            check(True, label)
        else:
            raise AssertionError('Malformed input accepted: '+label)

    record = parsed['records'][initial['attribute_record_index']]
    reject('Attribute claims a different face absent from its reciprocal owner head', record['tokens'][4]['offset']+1,
           struct.pack('<q', trailing['face_owner_entity_ordinal']))
    reject('Attribute next pointer becomes a cycle', record['tokens'][2]['offset']+1,
           struct.pack('<q', initial['geometry_entity_ordinal']))
    mention = trailing['journal_mentions'][0]
    reject('Journal geometry pointer leaves its own entity table', mention['pointer_token_offset']+1,
           struct.pack('<q', result['geometry_entity_count']+1))
    state = parsed['records'][result['journal_states'][0]['inspection_record_index']]
    reject('Delta state self slot is not its own history namespace ordinal', state['tokens'][5]['offset']+1,
           struct.pack('<q', 1))
    reject('Typed int64 attribute enum prefix is unobserved', record['tokens'][5]['offset']+1, struct.pack('<q', 3))
    report = {'stage': 'Boundary Fill typed sculpt-tool face attributes and history provenance',
        'status': 'Observed typed attributes and reciprocal owner/journal framing decoded; numeric source-tool correspondence bounded to saved native selection evidence',
        'interface': {'module': 'decode_sculpt_tool_attributes.py', 'function': 'decode_sculpt_tool_attributes(blob, *, parsed=None)',
                      'returns': 'attributes, journal_states, unresolved, scope; nonempty results also include explicit geometry pointer namespace counts/neighbor chain',
                      'failure': 'ValueError for unobserved or nonreciprocal layouts; no input mutation or guessed fallback',
                      'integration': 'Optional per-history-blob summary after inspect_asm. Keep as separate provenance; do not merge trailing records into existing initial topology graphs or overwrite indices.'},
        'findings': [
            'ASM geometry pointers count initial and trailing geometry entities, excluding section markers and history entities. Global inspection record indices are retained separately.',
            'All 297 SCULPT attributes belong to reciprocal face attribute chains; 292 body-source tags share two-entry chains with typed custom attributes, while five plane tags have one-entry chains.',
            'All owner faces are members of reciprocal shell/lump/BODY chains. Every such snapshot BODY has stored entity ID -1; a single snapshot BODY can contain faces tagged with both tool IDs 275 and 354.',
            '292 positive SCULPT_TOOL_BODY values equal independently selected typed native historical BODY IDs 275 or 354, not ASM record indices or BODY stored identifiers.',
            'Four positive SCULPT_WORKPLANE_TOOL values equal selected native construction plane ID 282. One negative literal -282 has matching magnitude only; selected-cell side and sign encoding remain unresolved.',
            'Only one attribute is initial geometry: positive workplane tag 282 on the auxiliary unnumbered BODY/face. All other 296 attributes occur in trailing states.',
            'All attributes have explicit journal pointer-slot mentions: one for the initial tag and two for each trailing tag, totaling 593. Pointer-side and chronological semantics are preserved as unknown; no state replay is attempted.'
        ],
        'pointer_example': {'plane_first_initial_attribute_record_index': initial['attribute_record_index'],
                            'plane_first_initial_owner_record_index': initial['face_owner_record_index'],
                            'plane_first_first_trailing_attribute_record_index': trailing['attribute_record_index'],
                            'plane_first_first_trailing_attribute_geometry_ordinal': trailing['geometry_entity_ordinal'],
                            'explanation': 'For the first trailing attribute, global record index 229 differs from geometry pointer ordinal 221 because eight marker/history records are excluded. The count is nine in the ordinary two-body examples; no fixed global offset is used.'},
        'validation': {'checks': checks, 'saved_archives': len({r['file'] for r in rows}), **dict(counts),
                       'API_evidence': 'Original GenerateBoundaryFillSamples.py and actual saved tool names, selections/operations. API did not expose these ASM tags, history slots, face IDs or lifecycle states.',
                       'exact_replays': 'All 297 typed token payloads replay byte-for-byte from first pointer through int64 value.',
                       'guards': guards},
        'limitations': ['Numeric source tags supply bounded face source provenance correspondence, not persistent native face identities or topology regeneration.',
                       'No history entry is labeled creation/deletion, before/after, active/final or replayed.',
                       'Negative workplane literal is never converted into a resolved positive plane identity or side flag.',
                       'No reference namespace is merged: Design object ID, ASM stored BODY ID, geometry entity ordinal, journal delta-state slot and inspection record index remain distinct.',
                       'No live Fusion/API calls, new captures, shared production source changes or Git mutations.'],
        'samples': rows}
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--zstd-library', type=Path, required=True)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    report = validate(args.root, args.zstd_library)
    destination = args.report or args.root/'sculpt-tool-attribute-decoding.json'
    destination.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['validation'], indent=2))
