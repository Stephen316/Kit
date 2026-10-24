"""Fixed saved PathPattern cache evidence integration against 56495ea."""
import argparse
import copy
import json
import math
from pathlib import Path

from validate_rectangular_cache_evidence_integration import sha, digest, differences

ROOT = Path(__file__).resolve().parent
BASELINE = '56495ea'
FILES = tuple('pathpatterns-de9857f6a1bc/' + name + '.f3d' for name in (
    'spacing', 'extent', 'start_offset', 'flipped', 'symmetric', 'arc_identical',
    'arc_along', 'multiple_bodies', 'suppressed_instance')) + tuple(
    'pathpatterncomposites-b6b4cf615504/' + name + '.f3d' for name in (
        'composite_identical', 'composite_along', 'spline_along', 'composite_multiple')) + (
    'pathpatterninputs-7edfa558db34/feature_optimized.f3d',
    'pathpatterninputs-7edfa558db34/feature_identical.f3d',
    'rectmodes-a069f8f4b8a2/body_one.f3d',
    'rectmodes-a069f8f4b8a2/feature_optimized.f3d',
    'circularmodes-45f859c1f1b6/body_full.f3d')
TARGETS = frozenset(FILES[:15])
SUMMARY = 'path_pattern_cache_evidence'
EVIDENCE = 'path-pattern-feature-cache-decoding.json'
BODY_EVIDENCE = 'path-pattern-cache-evidence-decoding.json'


def evidence():
    rows = {}
    for row in json.loads((ROOT / EVIDENCE).read_text())['samples']:
        if row['archive'] in FILES:
            assert row['archive'] not in rows
            rows[row['archive']] = row['expected_summary']
    assert set(rows) == set(FILES)
    body_rows = {}
    for row in json.loads((ROOT / BODY_EVIDENCE).read_text())['samples']:
        if row['archive'] in FILES:
            assert row['archive'] not in body_rows
            body_rows[row['archive']] = row['expected_summary']
    assert set(body_rows) == set(FILES)
    for filename in FILES:
        if filename in FILES[13:15]:
            assert not body_rows[filename]['decoded'] and not body_rows[filename]['unresolved']
        else:
            assert body_rows[filename] == rows[filename]
    return rows


def qualify_native_routes(row, old, feature):
    settings = feature['tool_settings']
    identity = feature['object_id']
    assert row['feature_object_id'] == identity
    for key in ('control_record_object_id', 'input_entity_collection_object_id',
                'stored_instance_ordinal_pairs', 'element_record_object_ids'):
        assert row[key] == settings[key]
    assert row['input_selection_record_object_id'] == settings['auxiliary_selection_record_object_id']
    assert row['stored_control_flags'] == [settings['is_flipped'], settings['orientation_along_path'], settings['is_symmetric']]
    assert row['owned_result_anchor_object_ids'] == settings['result_record_object_ids']
    assert row['element_record_ordinals'] == list(range(settings['quantity']))
    suppressed = settings['suppressed_element_ids']
    assert row['stored_suppressed_element_ordinals'] == suppressed and 0 not in suppressed
    active = [pair for pair in settings['stored_instance_ordinal_pairs'] if pair[0] not in suppressed]
    assert row['active_instance_ordinal_pairs'] == active
    assert row['complete_controller_source_group_bijection'] is True
    assert row['API_element_identity'] is row['logical_grid_identity'] is row['current_placement'] is None
    anchors = {a['object_id']: a for a in old['body_selections']['body_anchors']}
    descriptors = {d['object_id']: d for d in old['body_selections']['body_descriptors']}
    inputs = settings['input_descriptors']
    feature_mode = settings.get('pattern_entity_type') == 'Features'

    def same_selection(observed, enriched):
        assert observed['body_properties'] == {}
        assert {k: v for k, v in observed.items() if k != 'body_properties'} == {
            k: v for k, v in enriched.items() if k != 'body_properties'}

    if feature_mode:
        assert row['pattern_entity_type'] == 'Features' and row['stored_entity_type_code'] == 1
        assert row['stored_compute_option_code'] == settings['stored_compute_option_code']
        assert len(inputs) == 1
        source_ids = [item['source_native_body_object_id'] for item in inputs]
        source_feature_ids = [item['source_feature_object_id'] for item in inputs]
        assert row['source_feature_object_ids'] == source_feature_ids
        provenance = row['source_feature_input_provenance']
        assert provenance['full_path_input_settings'] == settings
        assert provenance['input_proxy_object_id'] == settings['auxiliary_selection_record_object_id']
        assert provenance['input_collection_object_id'] == settings['input_entity_collection_object_id']
        assert len(provenance['sources']) == 1
        for source, item in zip(provenance['sources'], inputs):
            assert source['input_descriptor'] == item
            anchor = anchors[item['source_body_anchor_object_id']]
            same_selection(source['source_body_anchor'], anchor)
            assert anchor['native_body_object_id'] == item['source_native_body_object_id']
            assert anchor['source_owner_object_id'] == item['source_feature_object_id']
            owned = [a for a in anchors.values() if a['source_owner_object_id'] == item['source_feature_object_id']]
            assert owned == [anchor]
            original_feature = next(f for f in old['features'] if f['object_id'] == item['source_feature_object_id'])
            assert original_feature['kind'] == 'Extrude'
            expected_ids = [settings['auxiliary_selection_record_object_id'], settings['input_entity_collection_object_id'],
                            item['descriptor_object_id'], item['terminal_object_id'], item['association_record_object_id'],
                            item['association_bridge_object_id'], item['association_terminal_object_id'],
                            item['source_feature_object_id'], item['source_body_anchor_object_id'], item['source_native_body_object_id']]
            assert [r['object_id'] for r in source['native_records']] == expected_ids
            assert source['native_records'][-3]['class_guid'] == original_feature['class_guid']
            assert source['native_records'][-3]['record_offset'] == original_feature['record_offset']
            for record in source['native_records']:
                assert len(bytes.fromhex(record['payload_hex'])) == record['end_offset'] - record['body_offset']
    else:
        assert row['pattern_entity_type'] == 'Bodies' and row['stored_entity_type_code'] == 2
        source_ids = [descriptors[item['descriptor_object_id']]['native_body_object_id'] for item in inputs]
        if 'native_input_body_object_ids' in settings:
            assert source_ids == settings['native_input_body_object_ids']
    assert row['source_native_body_object_ids'] == source_ids
    matches = {}
    for mapping in old['body_blob_bindings']['decoded']:
        for binding in mapping['bindings']:
            matches.setdefault(binding['native_body_object_id'], []).append((mapping, binding))

    def binding_matches(identity, observed):
        assert len(matches[identity]) == 1
        mapping, binding = matches[identity][0]
        assert observed == {key: binding[key] for key in observed}
        assert row['history_blob_member'] == mapping['history_blob_member']
        assert row['mapping_record_object_id'] == mapping['mapping_record_object_id']
        assert row['mapping_owner_object_id'] == mapping['owner_object_id']

    def face_names(proof, components):
        assert len(proof) == 6 and len({p['face_record_index'] for p in proof}) == 6
        names = {tuple(p['name_key']) for p in proof}
        assert len(names) == 6
        for face in proof:
            assert face['stored_reference_components_int32'] == components
            records = face['original_attribute_records']
            assert [r['record_index'] for r in records] == face['owner_attribute_indices']
            for record in records:
                assert len(bytes.fromhex(record['original_payload_hex'])) == record['record_end_offset'] - record['record_offset']
        return names

    seeds, source_names = {}, {}
    assert [p['source_native_body_object_id'] for p in row['source_cache_bodies']] == source_ids
    for source, item in zip(row['source_cache_bodies'], inputs):
        body_id = source['source_native_body_object_id']
        if feature_mode:
            observed = source['source_feature_descriptor']
            for key in ('descriptor_object_id', 'terminal_object_id', 'source_feature_object_id'):
                assert observed[key] == item[key]
            same_selection(observed['source_body_anchor'], anchors[item['source_body_anchor_object_id']])
        else:
            descriptor = descriptors[item['descriptor_object_id']]
            same_selection(source['source_descriptor'], descriptor)
            assert descriptor['owner_object_id'] == identity and descriptor['native_body_object_id'] == body_id
        binding_matches(body_id, source['source_body_binding'])
        prefix, = source['stored_source_naming_prefix']
        assert prefix not in seeds
        seeds[prefix] = body_id
        source_names[body_id] = face_names(source['complete_face_naming_proof'], [prefix])
    elements = dict(zip(row['element_record_ordinals'], settings['element_record_object_ids']))
    expected_suppressed = [dict(stored_element_ordinal=ordinal, stored_naming_key=key,
                               element_object_id=elements[ordinal], result_cache_assignment=None)
                           for ordinal, key in settings['stored_instance_ordinal_pairs'] if ordinal in suppressed]
    assert row['suppressed_cache_groups'] == expected_suppressed
    active_pairs = dict(active)
    groups = row['element_cache_groups']
    assert len(groups) == len(active_pairs)
    assert {g['stored_element_ordinal'] for g in groups} == set(active_pairs)
    seen_anchors, seen_keys, result_ids = set(), set(), set()
    vertex_pairs = 0
    for group in groups:
        ordinal = group['stored_element_ordinal']
        assert group['stored_naming_key'] == active_pairs[ordinal]
        assert group['element_object_id'] == elements[ordinal]
        assert len(group['cache_bodies']) == len(source_ids)
        assert {b['source_native_body_object_id'] for b in group['cache_bodies']} == set(source_ids)
        for body in group['cache_bodies']:
            source_id = body['source_native_body_object_id']
            anchor_id, body_id = body['result_anchor_object_id'], body['result_native_body_object_id']
            assert anchor_id not in seen_anchors and body_id not in result_ids and body_id not in source_ids
            seen_anchors.add(anchor_id)
            result_ids.add(body_id)
            same_selection(body['result_body_anchor'], anchors[anchor_id])
            assert anchors[anchor_id]['source_owner_object_id'] == identity
            assert anchors[anchor_id]['native_body_object_id'] == body_id
            binding_matches(body_id, body['result_body_binding'])
            components = body['stored_face_naming_components']
            assert len(components) == 3 and seeds[components[0]] == source_id
            assert components[1:] == [row['uninterpreted_common_feature_naming_component'], active_pairs[ordinal]]
            joined = (components[2], components[0])
            assert joined not in seen_keys
            seen_keys.add(joined)
            assert face_names(body['complete_result_face_naming_proof'], components) == source_names[source_id]
            fit = body['measured_relative_rigid_fit']
            assert fit['matched_vertex_count'] == len(fit['vertex_correspondence']) == 8
            assert len(fit['matrix']) == 16 and all(math.isfinite(v) for v in fit['matrix'])
            assert 0 <= fit['maximum_vertex_residual_raw'] <= 1e-8
            for vertex in fit['vertex_correspondence']:
                assert len(vertex['incident_face_name_keys']) == 3
                assert set(map(tuple, vertex['incident_face_name_keys'])) <= source_names[source_id]
            vertex_pairs += 8
    assert seen_anchors == set(settings['result_record_object_ids'])
    assert seen_keys == {(key, prefix) for key in active_pairs.values() for prefix in seeds}
    source_fpm = 0
    if feature_mode:
        naming_proofs = row['source_feature_face_naming_proofs']
        assert len(naming_proofs) == len(result_ids) + len(source_ids)
        assert {p['native_body_object_id'] for p in naming_proofs} == result_ids | set(source_ids)
        for naming in naming_proofs:
            binding_matches(naming['native_body_object_id'], naming['binding'])
            assert naming['asm_body_index'] == naming['binding']['asm_body_index']
            proof = naming['proof']
            assert proof['FPM_literal_identity'] is None and len(proof['faces']) == 6
            for face in proof['faces']:
                for tag in face['opaque_FPM_attributes']:
                    assert tag['definition_name'] == 'FPM_tracked_attrib_def'
                    assert tag['owner_kind'] == 'face' and tag['owner_record_index'] == face['face_record_index']
                if naming['native_body_object_id'] in source_ids:
                    source_fpm += len(face['opaque_FPM_attributes'])
        assert source_fpm == 6 * len(source_ids)
    source_major = 0
    if len(source_ids) > 1:
        first = min(groups, key=lambda group: group['stored_element_ordinal'])
        positions = sorted(settings['result_record_object_ids'].index(b['result_anchor_object_id']) for b in first['cache_bodies'])
        assert positions != list(range(len(source_ids)))
        source_major = 1
    return dict(qualified_element_cache_groups=len(groups), qualified_result_body_caches=len(result_ids),
                typed_vertex_pairs=vertex_pairs, literal_suppressed_groups_without_cache=len(expected_suppressed),
                feature_source_proofs=int(feature_mode), source_major_result_order_controls=source_major,
                retained_opaque_source_FPM_attributes=source_fpm)


def compare(before, current, filename, proof):
    after = copy.deepcopy(current)
    assert len(before['streams']) == len(after['streams']) == 1
    old, stream = before['streams'][0], after['streams'][0]
    assert old['member'] == stream['member'] and SUMMARY not in old
    expected = proof[filename]
    assert set(expected) == {'decoded', 'unresolved', 'scope'} and not expected['unresolved']
    counts = dict(qualified_path_cache_features=0, receiving_feature_annotations=0,
                  qualified_element_cache_groups=0, qualified_result_body_caches=0,
                  typed_vertex_pairs=0, literal_suppressed_groups_without_cache=0,
                  feature_source_proofs=0, source_major_result_order_controls=0,
                  retained_opaque_source_FPM_attributes=0)
    if filename in TARGETS:
        assert stream.pop(SUMMARY) == expected and len(expected['decoded']) == 1
        row = expected['decoded'][0]
        identity = row['feature_object_id']
        old_feature = next(f for f in old['features'] if f['object_id'] == identity)
        feature = next(f for f in stream['features'] if f['object_id'] == identity)
        assert old_feature['kind'] == feature['kind'] == 'PathPattern'
        assert SUMMARY not in old_feature and feature.pop(SUMMARY) == row
        counts.update(qualify_native_routes(row, old, old_feature))
        counts.update(qualified_path_cache_features=1, receiving_feature_annotations=1)
    else:
        assert not expected['decoded'] and SUMMARY not in stream
        assert all(SUMMARY not in f for f in stream['features'])
    assert after == before, (filename, 'Unexpected previous-output change', differences(before, after))
    return dict(archive=filename, archive_sha256=sha(ROOT / filename), **counts,
                whole_output_unchanged=before == current,
                whole_output_exact_after_removing_only_new_summary_and_owner_attachment=True,
                all_prior_settings_placements_warnings_geometry_and_ASM_exact=True,
                baseline_output_sha256=digest(before), current_output_sha256=digest(current),
                qualified_difference_paths=differences(before, current))


def read_cache(path, side):
    value = json.loads(Path(path).read_text())
    assert value['files'] == list(FILES) and value['baseline_commit'].startswith(BASELINE)
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
    assert len(before) == len(current) == len(FILES) == 18
    assert [r['file'] for r in before] == [str(ROOT / name) for name in FILES] == [r['file'] for r in current]
    proof = evidence()
    rows = [compare(b, a, name, proof) for b, a, name in zip(before, current, FILES)]
    keys = ('qualified_path_cache_features', 'receiving_feature_annotations',
            'qualified_element_cache_groups', 'qualified_result_body_caches', 'typed_vertex_pairs',
            'literal_suppressed_groups_without_cache', 'feature_source_proofs', 'source_major_result_order_controls',
            'retained_opaque_source_FPM_attributes')
    summary = {key: sum(r[key] for r in rows) for key in keys}
    summary.update(saved_files=18, whole_output_unchanged_controls=sum(r['whole_output_unchanged'] for r in rows),
                   unexpected_changes=0, comparator_baseline_main_calls=0 if baseline_cache else 18,
                   comparator_current_main_calls=0 if current_cache else 18, live_API_calls=0)
    caches = {}
    for side, path in (('baseline', baseline_cache), ('current', current_cache)):
        if path:
            caches[side] = dict(path=str(Path(path).resolve()), sha256=sha(path))
    sources = ('validate_path_pattern_cache_integration.py', 'validate_rectangular_cache_evidence_integration.py',
               'decode_path_pattern_feature_caches.py', 'decode_path_pattern_cache_evidence.py',
               'decode_path_patterns.py', 'decode_path_pattern_composites.py',
               'decode_path_pattern_inputs.py', 'decode_circular_feature_caches.py', 'decode_basics.py')
    return dict(scope='Fixed eighteen saved archives against 56495ea; only fifteen new PathPattern cache summaries and direct owner annotations',
                baseline_commit=BASELINE, files=list(FILES), summary=summary, samples=rows,
                fixed_manifest_acquisition=dict(baseline_main_calls=18, current_main_calls=18,
                    baseline_passes=1, current_passes=1,
                    scope='Original fixed-manifest acquisition; cached comparison does not repeat either pass'),
                independent_core_facade_cross_checks=dict(full_BODY_or_empty_summary_matches=16,
                    default_Feature_callback_skip_checks=2),
                cache_provenance=caches, evidence_sha256={name: sha(ROOT / name) for name in (EVIDENCE, BODY_EVIDENCE)},
                source_sha256={name: sha(ROOT / name) for name in sources},
                limitations=['Native anchors, source prefixes and literal controller naming keys fix identities before geometry',
                             'Measured cache fits are not serialized transforms, regenerated geometry or per-API-element assignments',
                             'A stored nonseed suppression mask filters the literal native product; no API visibility or history state inferred',
                             'All prior settings, placement/getter diagnostics, geometry and ASM outputs remain exact',
                             'Independent focused helper reports supply complete expected additions; no live calls or broad corpus decoding'])


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--baseline-cache')
    p.add_argument('--current-cache')
    p.add_argument('--zstd-library')
    p.add_argument('--output', default='path-pattern-cache-integration.json')
    args = p.parse_args()
    zstd = args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result = validate(zstd, args.baseline_cache, args.current_cache)
    Path(args.output).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['summary'], sort_keys=True))


if __name__ == '__main__':
    main()
