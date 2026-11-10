"""Fixed saved-file integration of separately scoped rectangular BODY caches.

Independent focused helper goldens qualify the new summary. Existing decoded
fields must compare exactly after removing only that summary and its direct
receiving-feature attachment.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASELINE = '5fc60b4'
FILES = tuple('rectmodes-a069f8f4b8a2/' + name + '.f3d' for name in (
    'body_one', 'body_multiple_customaxis', 'body_sketchlines', 'body_negative')) + (
    'tools-fda3948848f4/RectangularPattern.f3d',
    'rectsymmetry-f09c57dcfd51/symmetric_one.f3d',
    'rectsymmetry-f09c57dcfd51/symmetric_both_even.f3d',
    'rectsymholdouts-cf85ce4a0382/multiple_bodies.f3d',
    'rectmodes-a069f8f4b8a2/feature_optimized.f3d',
    'circularmodes-45f859c1f1b6/body_full.f3d',
    'surfacetools-856ca50cf4c7/offset_positive.f3d',
    'surfacebounds-ac801bb00fae/untrim_all.f3d')
TARGETS = frozenset(FILES[:8])
SUMMARY = 'rectangular_cache_evidence'
EVIDENCE = 'rectangular-cache-evidence-decoding.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def differences(before, after, path=''):
    if type(before) is not type(after):
        return [path]
    if isinstance(before, dict):
        return sorted([path + '/' + key for key in before.keys() ^ after.keys()] + [
            p for key in before.keys() & after.keys()
            for p in differences(before[key], after[key], path + '/' + key)])
    if isinstance(before, list):
        if len(before) != len(after):
            return [path + '(length)']
        return [p for i, (a, b) in enumerate(zip(before, after))
                for p in differences(a, b, path + '/' + str(i))]
    return [] if before == after else [path]


def evidence():
    rows = {}
    for row in json.loads((ROOT / EVIDENCE).read_text())['samples']:
        if row['archive'] in FILES:
            assert row['archive'] not in rows
            rows[row['archive']] = row['expected_summary']
    assert set(rows) == set(FILES)
    return rows


def qualify_native_routes(row, old, feature):
    """Cross-check focused proof against pre-existing typed identities."""
    settings = feature['tool_settings']
    identity = feature['object_id']
    assert row['feature_object_id'] == identity
    assert row['pattern_entity_type'] == settings['pattern_entity_type'] == 'Bodies'
    assert row['stored_entity_type_code'] == settings['pattern_entity_type_code'] == 2
    assert row['stored_compute_option_code'] == settings['pattern_compute_option_code']
    assert row['stored_symmetry_flags'] == [settings['symmetric_one'], settings['symmetric_two']]
    assert row['control_record_object_id'] == settings['control_record_object_id']
    assert row['input_selection_record_object_id'] == settings['input_selection_record_object_id']
    assert row['input_entity_collection_object_id'] == settings['input_entity_collection_object_id']
    assert row['stored_suppressed_element_keys'] == settings['stored_suppressed_element_keys'] == []
    assert row['stored_instance_key_pairs'] == settings['stored_instance_key_pairs']
    assert row['element_record_object_ids'] == settings['element_record_object_ids']
    assert row['element_record_keys'] == settings['stored_element_keys']
    assert row['source_native_body_object_ids'] == settings['native_input_body_object_ids']
    assert row['owned_result_anchor_object_ids'] == settings['result_record_object_ids']
    assert row['complete_controller_source_group_bijection'] is True
    assert row['API_element_identity'] is row['logical_grid_identity'] is row['current_placement'] is None
    sources = row['source_native_body_object_ids']
    anchors = {a['object_id']: a for a in old['body_selections']['body_anchors']}
    descriptors = {d['object_id']: d for d in old['body_selections']['body_descriptors']}
    matches = {}
    for mapping in old['body_blob_bindings']['decoded']:
        for binding in mapping['bindings']:
            matches.setdefault(binding['native_body_object_id'], []).append((mapping, binding))

    def binding_matches(identity, observed):
        assert len(matches[identity]) == 1
        mapping, binding = matches[identity][0]
        assert observed == {key: binding[key] for key in observed}
        assert row['mapping_record_object_id'] == mapping['mapping_record_object_id']
        assert row['mapping_owner_object_id'] == mapping['owner_object_id']
        assert row['history_blob_member'] == mapping['history_blob_member']

    def named_faces(proof, components):
        assert len(proof) == 6
        assert len({p['face_record_index'] for p in proof}) == 6
        assert len({tuple(p['name_key']) for p in proof}) == 6
        for face in proof:
            assert face['stored_reference_components_int32'] == components
            attrs = face['owner_attribute_indices']
            assert len(attrs) == len(set(attrs)) and attrs
            originals = face['original_attribute_records']
            assert [r['record_index'] for r in originals] == attrs
            for record in originals:
                assert len(bytes.fromhex(record['original_payload_hex'])) == record['record_end_offset'] - record['record_offset']
        return {tuple(p['name_key']) for p in proof}

    def same_native_selection(observed, enriched):
        # The focused helper invokes the native selector without optional name /
        # collection enrichment. Compare every native field; prior enriched
        # properties remain protected by whole-output equality below.
        assert observed['body_properties'] == {}
        assert {k: v for k, v in observed.items() if k != 'body_properties'} == {
            k: v for k, v in enriched.items() if k != 'body_properties'}

    seed_prefixes, seed_names = {}, {}
    source_proofs = row['source_cache_bodies']
    assert [p['source_native_body_object_id'] for p in source_proofs] == sources
    for source in source_proofs:
        body_id = source['source_native_body_object_id']
        descriptor = source['source_descriptor']
        same_native_selection(descriptor, descriptors[descriptor['object_id']])
        assert descriptor['owner_object_id'] == identity and descriptor['native_body_object_id'] == body_id
        assert descriptor['object_id'] in {d['descriptor_object_id'] for d in settings['input_descriptors']}
        anchor = anchors[descriptor['body_anchor_object_id']]
        assert anchor['native_body_object_id'] == body_id
        assert anchor['source_owner_object_id'] == descriptor['source_owner_object_id']
        binding_matches(body_id, source['source_body_binding'])
        prefix = source['stored_source_naming_prefix']
        assert len(prefix) == 1 and prefix[0] not in seed_prefixes
        seed_prefixes[prefix[0]] = body_id
        seed_names[body_id] = named_faces(source['complete_face_naming_proof'], prefix)
    pairs = dict(settings['stored_instance_key_pairs'])
    elements = dict(zip(settings['stored_element_keys'], settings['element_record_object_ids']))
    assert len(pairs) == len(row['element_cache_groups'])
    assert {g['stored_element_key'] for g in row['element_cache_groups']} == set(pairs)
    seen_anchors, seen_keys = set(), set()
    vertex_pairs = result_count = 0
    for group in row['element_cache_groups']:
        key = group['stored_element_key']
        assert group['stored_naming_key'] == pairs[key]
        assert group['element_object_id'] == elements[key]
        assert len(group['cache_bodies']) == len(sources)
        assert {b['source_native_body_object_id'] for b in group['cache_bodies']} == set(sources)
        for body in group['cache_bodies']:
            source_id = body['source_native_body_object_id']
            result_id, anchor_id = body['result_native_body_object_id'], body['result_anchor_object_id']
            assert anchor_id not in seen_anchors
            seen_anchors.add(anchor_id)
            same_native_selection(body['result_body_anchor'], anchors[anchor_id])
            assert anchors[anchor_id]['source_owner_object_id'] == identity
            assert anchors[anchor_id]['native_body_object_id'] == result_id
            assert result_id not in sources
            binding_matches(result_id, body['result_body_binding'])
            components = body['stored_face_naming_components']
            assert len(components) == 3
            assert components[2] == group['stored_naming_key']
            assert components[1] == row['uninterpreted_common_feature_naming_component']
            assert seed_prefixes[components[0]] == source_id
            joined_key = (group['stored_naming_key'], components[0])
            assert joined_key not in seen_keys
            seen_keys.add(joined_key)
            assert named_faces(body['complete_result_face_naming_proof'], components) == seed_names[source_id]
            fit = body['measured_relative_rigid_fit']
            assert fit['matched_vertex_count'] == len(fit['vertex_correspondence']) == 8
            assert len(fit['matrix']) == 16 and all(math.isfinite(v) for v in fit['matrix'])
            assert 0 <= fit['maximum_vertex_residual_raw'] <= 1e-8
            for vertex in fit['vertex_correspondence']:
                signature = vertex['incident_face_name_keys']
                assert len(signature) == 3 and set(map(tuple, signature)) <= seed_names[source_id]
            vertex_pairs += fit['matched_vertex_count']
            result_count += 1
    assert seen_anchors == set(settings['result_record_object_ids'])
    assert seen_keys == {(value, prefix) for value in pairs.values() for prefix in seed_prefixes}
    nonordinal = 0
    if settings['symmetric_one'] or settings['symmetric_two']:
        native_keys = settings['stored_element_keys']
        assert native_keys.index(1) > 0 and native_keys[0] != min(pairs)
        by_key = {g['stored_element_key']: g for g in row['element_cache_groups']}
        first = {b['result_native_body_object_id'] for b in by_key[native_keys[0]]['cache_bodies']}
        sorted_first = {b['result_native_body_object_id'] for b in by_key[min(pairs)]['cache_bodies']}
        assert first.isdisjoint(sorted_first)
        nonordinal = 1
    return dict(qualified_element_cache_groups=len(pairs), qualified_result_body_caches=result_count,
                typed_vertex_pairs=vertex_pairs, symmetric_nonordinal_controls=nonordinal)


def compare(before, current, filename, proof):
    after = copy.deepcopy(current)
    assert len(before['streams']) == len(after['streams']) == 1
    old, stream = before['streams'][0], after['streams'][0]
    assert old['member'] == stream['member']
    expected = proof[filename]
    assert set(expected) == {'decoded', 'unresolved', 'scope'}
    assert not expected['unresolved']
    assert SUMMARY not in old
    counts = dict(qualified_rectangular_cache_features=0, receiving_feature_annotations=0,
                  qualified_element_cache_groups=0, qualified_result_body_caches=0,
                  typed_vertex_pairs=0, symmetric_nonordinal_controls=0)
    if filename in TARGETS:
        assert stream.pop(SUMMARY) == expected and len(expected['decoded']) == 1
        row = expected['decoded'][0]
        identity = row['feature_object_id']
        old_feature = next(f for f in old['features'] if f['object_id'] == identity)
        feature = next(f for f in stream['features'] if f['object_id'] == identity)
        assert old_feature['kind'] == feature['kind'] == 'RectangularPattern'
        assert SUMMARY not in old_feature and feature.pop(SUMMARY) == row
        counts.update(qualify_native_routes(row, old, old_feature))
        counts.update(qualified_rectangular_cache_features=1, receiving_feature_annotations=1)
    else:
        assert not expected['decoded'] and SUMMARY not in stream
        assert all(SUMMARY not in f for f in stream['features'])
    assert after == before, (filename, 'Unexpected previous-output change', differences(before, after))
    return dict(archive=filename, archive_sha256=sha(ROOT / filename), **counts,
                whole_output_unchanged=before == current,
                whole_output_exact_after_removing_only_independent_summary_and_attachment=True,
                all_previous_settings_placements_warnings_geometry_and_ASM_exact=True,
                baseline_output_sha256=digest(before), current_output_sha256=digest(current),
                qualified_difference_paths=differences(before, current))


def read_cache(path, side):
    value = json.loads(Path(path).read_text())
    assert value['files'] == list(FILES)
    if 'baseline_commit' in value:
        assert value['baseline_commit'].startswith(BASELINE)
    return value[side]


def validate(zstd, baseline_cache=None, current_cache=None):
    if baseline_cache:
        before = read_cache(baseline_cache, 'before')
    else:
        from validate_history_cache_integration import baseline_outputs
        before = baseline_outputs(FILES, zstd, revision=BASELINE)
    if current_cache:
        current = read_cache(current_cache, 'after')
    else:
        from decode_basics import decode_basics
        current = json.loads(json.dumps([decode_basics(ROOT / name, zstd) for name in FILES]))
    assert len(before) == len(current) == len(FILES) == 12
    assert [r['file'] for r in before] == [str(ROOT / name) for name in FILES] == [r['file'] for r in current]
    proof = evidence()
    rows = [compare(b, a, name, proof) for b, a, name in zip(before, current, FILES)]
    keys = ('qualified_rectangular_cache_features', 'receiving_feature_annotations',
            'qualified_element_cache_groups', 'qualified_result_body_caches',
            'typed_vertex_pairs', 'symmetric_nonordinal_controls')
    summary = {key: sum(r[key] for r in rows) for key in keys}
    summary.update(saved_files=12, whole_output_unchanged_controls=sum(r['whole_output_unchanged'] for r in rows),
                   unexpected_changes=0, comparator_baseline_main_calls=0 if baseline_cache else 12,
                   comparator_current_main_calls=0 if current_cache else 12, live_API_calls=0)
    caches = {}
    for side, path in (('baseline', baseline_cache), ('current', current_cache)):
        if path:
            caches[side] = dict(path=str(Path(path).resolve()), sha256=sha(path))
    sources = ('validate_rectangular_cache_evidence_integration.py', 'decode_rectangular_cache_evidence.py',
               'decode_circular_feature_caches.py', 'decode_circular_placement_evidence.py', 'decode_basics.py')
    return dict(scope='Fixed twelve saved archives against 5fc60b4; only eight new rectangular BODY cache summaries and receiving-feature annotations',
                baseline_commit=BASELINE, files=list(FILES), summary=summary, samples=rows,
                fixed_manifest_acquisition=dict(baseline_main_calls=12, current_main_calls=12,
                    baseline_passes=1, current_passes=1,
                    scope='Original fixed-manifest acquisition: one pinned baseline pass and one frozen current pass; cached report comparisons do not repeat either acquisition'),
                cache_provenance=caches, evidence_sha256={EVIDENCE: sha(ROOT / EVIDENCE)},
                source_sha256={name: sha(ROOT / name) for name in sources},
                limitations=['Literal controller/naming keys are distinct from API IDs and logical grid positions',
                             'Relative cache fits follow explicit native identity joins and are not serialized placement transforms',
                             'No suppression, current lifecycle, regeneration or feature-input support is inferred',
                             'Complete independent helper dictionaries qualify additions; current main does not supply expected goldens',
                             'All prior outputs remain exact; no live calls or corpus-wide main decoding'])


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--baseline-cache')
    p.add_argument('--current-cache')
    p.add_argument('--zstd-library')
    p.add_argument('--output', default='rectangular-cache-evidence-integration.json')
    args = p.parse_args()
    zstd = args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result = validate(zstd, args.baseline_cache, args.current_cache)
    Path(args.output).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['summary'], sort_keys=True))


if __name__ == '__main__':
    main()
