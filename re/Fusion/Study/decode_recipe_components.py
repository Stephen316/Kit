"""Observed counted32-bit recipe reference components, including count two.

The legacy0/1 layouts also fit this framing: a count, that many components,
then a zero32 terminator. Components remain opaque numeric tuples, never native
object references or persistent topology identities inferred by coincidence.
"""
import struct

from decode_brep_recipes import RECIPE_GUID, decode_recipe, decode_recipes

SCOPE = 'Observed name-reference component arrays of count0/1/2 plus explicit zero terminators; signed/unsigned values retained without native design/entity identity or topology semantics'


def decode_reference_components(count, take):
    """Shared-reader callback; consume exactly4*(count+1) bounded payload bytes."""
    if count not in (0, 1, 2):
        raise ValueError('Unobserved recipe reference component count')
    raw = take(4*count)
    if take(4) != bytes(4):
        raise ValueError('Recipe reference component terminator must be zero')
    signed = list(struct.unpack('<'+'i'*count, raw))
    unsigned = list(struct.unpack('<'+'I'*count, raw))
    return {'stored_reference_component_count': count,
            'stored_reference_components_int32': signed,
            'stored_reference_components_uint32': unsigned,
            'stored_reference_component_bytes_hex': raw.hex(),
            'stored_reference_terminator_uint32': 0,
            'reference_scope': 'Opaque counted recipe numeric tuple; native object/entity correspondence and persistent topology meaning unresolved'}


def decode_counted_recipe(data, record, primary_records=None):
    """Individual opt-in grammar reader, including count0/1 controls."""
    result = decode_recipe(data, record, primary_records, reference_decoder=decode_reference_components)
    result['scope'] = SCOPE
    return result


def decode_recipe_components(data, records, prior_summary=None):
    """Additional count-two recipes only; merge by object_id with legacy summary.

    Existing0/1 results stay with the default reader. Pass its prior summary to
    avoid recomputing that scan. Only corresponding successful failure IDs clear.
    """
    prior = prior_summary if prior_summary is not None else decode_recipes(data, records)
    candidates = {item['object_id'] for item in prior['unresolved']
                  if item['reason'] == 'Unsupported recipe reference tag'}
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {i: values[0] for i, values in grouped.items() if len(values) == 1}
    recipes, unresolved = [], []
    for record in records:
        if not record.is_primary or record.class_guid != RECIPE_GUID or record.object_id not in candidates:
            continue
        try:
            if primary.get(record.object_id) is not record:
                raise ValueError('Recipe component primary identity ambiguous')
            parsed = decode_counted_recipe(data, record, primary)
            if not any(t['stored_reference_component_count'] == 2 for entry in parsed['name_table'] for t in entry['terms']):
                raise ValueError('No new count-two recipe reference component array')
            recipes.append(parsed)
        except (ValueError, IndexError, KeyError, UnicodeError, struct.error) as error:
            unresolved.append({'object_id': record.object_id, 'reason': str(error)})
    return {'recipes': recipes, 'unresolved': unresolved, 'scope': SCOPE}


def validate_fixtures(root, zstd_library=None):
    """Validate actual11-file count-two corpus plus two legacy count controls."""
    from collections import Counter
    from dataclasses import replace
    import hashlib
    import json
    from pathlib import Path
    from fusion_archive import read_members
    from fusion_metadata import design_records

    root = Path(root)
    filenames = [
        'embossmodes-e40cc931d978/'+name+'.f3d' for name in
        ('engraved', 'multiple_profiles', 'no_chain', 'raised', 'rotated', 'shifted')]
    filenames += ['embosstext-cd769aa41cdf/'+name+'.f3d' for name in
                  ('mixed_text_profile', 'text_deboss', 'text_emboss', 'two_texts')]
    filenames += ['silhouettesplits-f21b83e21695/shelled_hollow_axis_x.f3d']
    report = {'scope': SCOPE, 'integration': {
        'individual_reader': 'decode_counted_recipe(data,record,primary_records=None)',
        'additional_summary': 'decode_recipe_components(data,records,prior_summary=None)',
        'merge': 'Merge only newly framed recipes by object_id with existing recipe_decoding; clear corresponding successful failure IDs. Existing0/1 output stays with default reader, whose record-collision diagnostic is explicitly numerical only.',
        'callback': 'decode_reference_components(count,take) consumes exactly4*(count+1) bytes for observed counts0/1/2; bounded take is supplied by shared reader.',
        'validator': 'decode_recipe_components.validate_fixtures(root,zstd_library=None)',
        'expected_outputs': 'Representative samples[].expected_recipe is complete opt-in output; corpus_files[].new_recipe_ids and fingerprints cover all184 newly framed recipes.'},
        'grammar': {
            'observed_reference_field': 'u32 component_count followed by component_count raw32 values followed by separate u32zero terminator. Signed and unsigned component interpretations are both retained, without object-ID assumptions.',
            'count0': 'Empty component tuple then zero32. Legacy reader returned stored_reference_tag0/value0.',
            'count1': 'One raw32 value then zero32. Legacy reader consumed the pair as one64-bit number; all3494 observed count-one components are positive32 and following32 is zero.',
            'count2': 'Two raw32 values then zero32; a separate global separatorzero follows the whole name table. The old8-byte branch would leave an extra zero before the payload-kind length.',
            'observed_tuple_patterns': {'[305,-307]': 7, '[305,-338]': 73, '[305,-369]': 98, '[301,303]': 6},
            'unobserved': 'Counts3+ and nonzero tuple terminators remain rejected.'},
        'audit': {'archives': 559, 'primary_recipe_records': 1296, 'count0_terms': 280, 'count1_terms': 3494,
                  'count2_terms': 184, 'unframed_records': 0,
                  'procedure': 'Offline bounded count-array diagnostic over existing saved archives; followup validation below rechecks all11 affected archives without Fusion/API calls.'},
        'identity_correction': {
            'counterexample': 'Count2 positive tuple[301,303] appears in six hollow-cylinder face recipes while neither301 nor303 is a primary record in that stream. Positive305 in Emboss tuples coincides with sketch-placement classF47A46FB without a typed recipe reference chain. Negative component magnitudes can coincide with sketch line or parameter record IDs; those numerical matches establish no association.',
            'new_reader': 'No native-identity lookup or numeric-record collision field is emitted for component tuples, even when a primary record has the same number.',
            'shared_default_repair': 'Root renamed matching_primary_record to numeric_record_collision with explicit coincidence-only scope; surface constraint field recipe_native_reference_value renamed recipe_stored_numeric_reference_value. Existing historical report snapshots are not identity evidence.'},
        'limitations': ['Structural recipe/name framing only; payloads remain explicitly retained and opaque unless an existing decoder has established their independent structure.',
            'Counted tuple roles, sign meaning, persistent body/face/edge identities and topology operations unresolved. This stage adds no geometry regeneration or full native writer.',
            'Saved API truth locates modeling scenarios, but it does not expose recipe component tuples. No API geometry comparison is invented for these fields.',
            'Recipe-frame byte reconstruction in validation copies opaque payloads unchanged; it demonstrates framing, not CAD regeneration.'],
        'samples': [], 'corpus_files': [], 'legacy_controls': [], 'malformed_checks': []}
    pattern_counts = Counter(); payload_counts = Counter(); total = 0; fixture = None

    def load(filename):
        path = root/filename; members = read_members(path, zstd_library)
        name = next(n for n in members if n.endswith('FusionDesignSegmentType1/BulkStream.dat'))
        data = members[name]; records, _ = design_records(data, members[name.replace('BulkStream.dat', 'MetaStream.dat')])
        return data, records, {r.object_id: r for r in records if r.is_primary}

    def reencode(recipe):
        raw = bytearray(bytes(2)+struct.pack('<III', *recipe['stored_header_fields'], len(recipe['name_table'])))
        for entry in recipe['name_table']:
            raw.extend(struct.pack('<I', len(entry['terms'])))
            for term in entry['terms']:
                text = term['name'].encode('ascii')
                raw.extend(struct.pack('<I', len(text))+text+struct.pack('<II', term['stored_index'], term['stored_reference_component_count']))
                raw.extend(bytes.fromhex(term['stored_reference_component_bytes_hex']))
                raw.extend(struct.pack('<I', term['stored_reference_terminator_uint32']))
        kind = recipe['payload_kind'].encode('ascii')
        raw.extend(bytes(4)+struct.pack('<I', len(kind))+kind+bytes.fromhex(recipe['payload_hex']))
        return raw

    def api_context(filename):
        directory, name = filename.split('/')
        truth = json.loads((root/directory/'ground_truth.json').read_text())
        sample = next(s for s in truth['samples'] if s['file'] == name)
        assert not sample.get('getter_errors', [])
        if directory.startswith('emboss'):
            actual = sample.get('settings', sample.get('api', {}))
            return {'source': directory+'/ground_truth.json', 'actual_depth_cm': actual.get('depth_cm'),
                    'actual_input_profile_types': [p.get('entity_type', p.get('kind')) for p in actual.get('profiles', [])],
                    'scope': 'Actual Emboss/Deboss scenario only; no recipe tuple exposed by API'}
        return {'source': directory+'/ground_truth.json', 'actual_operation': sample['settings']['operation'],
                'actual_target_name': sample['actual_target']['name'], 'actual_target_faces': sample['actual_target']['faces'],
                'scope': 'Actual hollow-cylinder ShelledBody scenario only; no recipe tuple exposed by API'}

    representatives = {'embossmodes-e40cc931d978/engraved.f3d': {384},
                       'embossmodes-e40cc931d978/multiple_profiles.f3d': {399},
                       'embosstext-cd769aa41cdf/mixed_text_profile.f3d': {661},
                       'embosstext-cd769aa41cdf/two_texts.f3d': set(),
                       'silhouettesplits-f21b83e21695/shelled_hollow_axis_x.f3d': {314}}
    selected_patterns = set()
    for filename in filenames:
        data, records, primary = load(filename)
        legacy = decode_recipes(data, records)
        out = decode_recipe_components(data, records, legacy)
        assert out == decode_recipe_components(data, records) and not out['unresolved'] and out['recipes']
        old_failures = {x['object_id'] for x in legacy['unresolved'] if x['reason'] == 'Unsupported recipe reference tag'}
        assert {r['object_id'] for r in out['recipes']} == old_failures
        fingerprints = []
        for recipe in out['recipes']:
            identity = recipe['object_id']; record = primary[identity]
            assert reencode(recipe) == data[record.body:record.end]
            assert decode_counted_recipe(data, record, {}) == recipe
            components = [t for entry in recipe['name_table'] for t in entry['terms']]
            assert all('numeric_record_collision' not in t and 'matching_primary_record' not in t for t in components)
            new_terms = [t for t in components if t['stored_reference_component_count'] == 2]
            assert len(new_terms) == 1
            pattern = tuple(new_terms[0]['stored_reference_components_int32']); pattern_counts[pattern] += 1
            payload_counts[(recipe['payload_kind'], recipe['payload_length'])] += 1
            fingerprints.append({'object_id': identity, 'payload_kind': recipe['payload_kind'],
                'payload_length': recipe['payload_length'], 'payload_relative_offset': recipe['payload_relative_offset'],
                'reference_components_int32': list(pattern), 'record_sha256': hashlib.sha256(data[record.body:record.end]).hexdigest()})
            select = identity in representatives.get(filename, set())
            if filename == 'embosstext-cd769aa41cdf/two_texts.f3d' and pattern not in selected_patterns:
                select = True; selected_patterns.add(pattern)
            if select:
                report['samples'].append({'file': filename, 'expected_recipe': recipe,
                    'recipe_frame_bytes_roundtrip': True, 'primary_lookup_independence': True,
                    'API_context': api_context(filename)})
            if fixture is None and filename.endswith('/engraved.f3d'):
                fixture = data, record, primary, recipe
        report['corpus_files'].append({'file': filename, 'new_recipe_ids': sorted(old_failures),
            'new_recipe_count': len(out['recipes']), 'all_prior_reference_tag_failures_framed': True,
            'all_recipe_frames_reencoded_exactly': True, 'all_outputs_independent_of_primary_lookup': True,
            'fingerprints': fingerprints})
        total += len(out['recipes'])
    assert total == 184 and dict(pattern_counts) == {(305, -307): 7, (305, -338): 73, (305, -369): 98, (301, 303): 6}
    for filename, identity, expected_count in (
            ('combinemodes-dcb4956eca6b/intersect_keep.f3d', 366, 0),
            ('pipepaths-3d11bd427946/brep_edge_circular.f3d', 313, 1)):
        data, records, primary = load(filename); recipe = decode_counted_recipe(data, primary[identity], primary)
        terms = [t for entry in recipe['name_table'] for t in entry['terms']]
        assert all(t['stored_reference_component_count'] == expected_count for t in terms)
        assert reencode(recipe) == data[primary[identity].body:primary[identity].end]
        assert not decode_recipe_components(data, records)['recipes']
        report['legacy_controls'].append({'file': filename, 'object_id': identity, 'expected_count': expected_count,
            'expected_recipe': recipe, 'recipe_frame_bytes_roundtrip': True, 'no_new_summary_recipe': True})
    data, record, primary, parsed = fixture
    # The representative's second term count is at52, array at56 and terminator64.
    def bad(label, mutate, replacement=None):
        altered = bytearray(data); mutate(altered)
        try:
            decode_counted_recipe(altered, replacement or record, primary)
        except (ValueError, IndexError, UnicodeError, struct.error) as error:
            report['malformed_checks'].append({'name': label, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError(label)
    bad('unobserved component count3', lambda d: struct.pack_into('<I', d, record.body+52, 3))
    bad('nonzero component tuple terminator', lambda d: struct.pack_into('<I', d, record.body+64, 1))
    bad('zero recipe entry count', lambda d: struct.pack_into('<I', d, record.body+10, 0))
    bad('oversized ASCII recipe name', lambda d: struct.pack_into('<I', d, record.body+18, 129))
    bad('truncated component tuple payload', lambda d: None, replace(record, end=record.body+62))
    report['summary'] = {'affected_archives': len(filenames), 'new_count_two_recipes': total,
        'edge_recipes': sum(n for (kind, _), n in payload_counts.items() if kind == 'edge_recipe_data'),
        'face_recipes': sum(n for (kind, _), n in payload_counts.items() if kind == 'face_recipe_data'),
        'representative_full_outputs': len(report['samples']), 'legacy_count_controls': len(report['legacy_controls']),
        'malformed_checks': len(report['malformed_checks']), 'all_passed': True}
    return report


if __name__ == '__main__':
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate', action='store_true')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--zstd-library', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if not args.validate:
        parser.error('--validate is required')
    report = validate_fixtures(args.root, args.zstd_library)
    if args.report:
        args.report.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], indent=2))
