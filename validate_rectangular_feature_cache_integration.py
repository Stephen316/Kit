"""Fixed feature-input rectangular cache integration against ccd06a7."""
import argparse
import copy
import json
import math
from pathlib import Path

from validate_rectangular_cache_evidence_integration import sha, digest, differences

ROOT = Path(__file__).resolve().parent
BASELINE = 'ccd06a7'
FILES = tuple('rectmodes-a069f8f4b8a2/' + name + '.f3d' for name in (
    'feature_optimized', 'feature_identical', 'feature_adjust')) + (
    'rectsymholdouts-cf85ce4a0382/feature_input.f3d',
    'rectmodes-a069f8f4b8a2/body_one.f3d',
    'rectmodes-a069f8f4b8a2/body_multiple_customaxis.f3d',
    'rectmodes-a069f8f4b8a2/body_sketchlines.f3d',
    'rectsymmetry-f09c57dcfd51/symmetric_one.f3d',
    'circularmodes-45f859c1f1b6/body_full.f3d',
    'circularmodes-45f859c1f1b6/feature_optimized.f3d',
    'surfacetools-856ca50cf4c7/offset_positive.f3d',
    'surfacebounds-ac801bb00fae/untrim_all.f3d')
TARGETS = frozenset(FILES[:4])
SUMMARY = 'rectangular_cache_evidence'
EVIDENCE = 'rectangular-feature-cache-decoding.json'
HOOK_EVIDENCE = 'rectangular-cache-hook-decoding.json'


def evidence():
    rows = {}
    for row in json.loads((ROOT / EVIDENCE).read_text())['samples']:
        if row['archive'] in FILES:
            assert row['archive'] not in rows
            rows[row['archive']] = row['expected_summary']
    assert set(rows) == set(FILES)
    hook = json.loads((ROOT / HOOK_EVIDENCE).read_text())
    assert hook['baseline']['commit'].startswith(BASELINE)
    assert hook['baseline']['committed_report_sha256'] == sha(ROOT / hook['baseline']['committed_report'])
    defaults = {row['archive']: row for row in hook['default_controls'] if row['archive'] in FILES}
    assert set(FILES[:8]) <= set(defaults)
    return dict(summaries=rows, defaults=defaults)


def qualify_feature(row, old, feature):
    settings = feature['tool_settings']
    identity = feature['object_id']
    assert row['feature_object_id'] == identity
    assert row['pattern_entity_type'] == settings['pattern_entity_type'] == 'Features'
    assert row['stored_entity_type_code'] == settings['pattern_entity_type_code'] == 1
    for observed, setting in (('control_record_object_id', 'control_record_object_id'),
                              ('input_selection_record_object_id', 'input_selection_record_object_id'),
                              ('input_entity_collection_object_id', 'input_entity_collection_object_id'),
                              ('stored_compute_option_code', 'pattern_compute_option_code'),
                              ('stored_instance_key_pairs', 'stored_instance_key_pairs'),
                              ('element_record_object_ids', 'element_record_object_ids'),
                              ('element_record_keys', 'stored_element_keys'),
                              ('owned_result_anchor_object_ids', 'result_record_object_ids'),
                              ('source_feature_object_ids', 'source_feature_object_ids')):
        assert row[observed] == settings[setting]
    assert row['stored_symmetry_flags'] == [settings['symmetric_one'], settings['symmetric_two']]
    assert row['stored_suppressed_element_keys'] == settings['stored_suppressed_element_keys'] == []
    assert row['complete_controller_source_group_bijection'] is True
    assert row['API_element_identity'] is row['logical_grid_identity'] is row['current_placement'] is None
    provenance = row['source_feature_input_provenance']
    assert provenance['pattern_entity_type'] == 'Features'
    assert provenance['input_proxy_object_id'] == settings['input_selection_record_object_id']
    assert provenance['input_collection_object_id'] == settings['input_entity_collection_object_id']
    assert len(provenance['sources']) == len(settings['input_descriptors']) == 1
    source = provenance['sources'][0]
    descriptor, = settings['input_descriptors']
    assert source['input_descriptor'] == descriptor
    source_id, = row['source_feature_object_ids']
    source_feature = next(f for f in old['features'] if f['object_id'] == source_id)
    assert source_feature['kind'] == descriptor['source_feature_kind'] == 'Extrude'
    anchors = {a['object_id']: a for a in old['body_selections']['body_anchors']}
    source_anchors = [a for a in anchors.values() if a['source_owner_object_id'] == source_id]
    assert len(source_anchors) == 1

    def same_selection(observed, enriched):
        assert observed['body_properties'] == {}
        assert {k: v for k, v in observed.items() if k != 'body_properties'} == {
            k: v for k, v in enriched.items() if k != 'body_properties'}

    same_selection(source['source_body_anchor'], source_anchors[0])
    source_body = source_anchors[0]['native_body_object_id']
    assert row['source_native_body_object_ids'] == [source_body]
    expected_native_ids = [settings['input_selection_record_object_id'], settings['input_entity_collection_object_id'],
                           descriptor['descriptor_object_id'], descriptor['association_record_object_id'],
                           descriptor['terminal_object_id'], source_id, source_anchors[0]['object_id'], source_body]
    native_records = source['native_records']
    assert [r['object_id'] for r in native_records] == expected_native_ids
    assert len(set(expected_native_ids)) == 8
    assert native_records[-3]['class_guid'] == source_feature['class_guid']
    assert native_records[-3]['record_offset'] == source_feature['record_offset']
    for record in native_records:
        assert record['record_offset'] < record['body_offset'] < record['end_offset']
        assert len(bytes.fromhex(record['payload_hex'])) == record['end_offset'] - record['body_offset']
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

    seed, = row['source_cache_bodies']
    assert seed['source_native_body_object_id'] == source_body
    source_descriptor = seed['source_feature_descriptor']
    assert source_descriptor['descriptor_object_id'] == descriptor['descriptor_object_id']
    assert source_descriptor['descriptor_class_guid'] == native_records[2]['class_guid']
    assert source_descriptor['terminal_object_id'] == descriptor['terminal_object_id']
    assert source_descriptor['source_feature_object_id'] == descriptor['source_feature_object_id']
    assert source_descriptor['source_body_anchor'] == source['source_body_anchor']
    binding_matches(source_body, seed['source_body_binding'])
    prefix, = seed['stored_source_naming_prefix']
    source_names = {tuple(p['name_key']) for p in seed['complete_face_naming_proof']}
    assert len(source_names) == len(seed['complete_face_naming_proof']) == 6
    assert all(p['stored_reference_components_int32'] == [prefix] for p in seed['complete_face_naming_proof'])
    pairs = dict(settings['stored_instance_key_pairs'])
    elements = dict(zip(settings['stored_element_keys'], settings['element_record_object_ids']))
    groups = row['element_cache_groups']
    assert len(groups) == len(pairs) and {g['stored_element_key'] for g in groups} == set(pairs)
    seen_anchors, seen_components, result_ids = set(), set(), set()
    vertex_pairs = 0
    for group in groups:
        key = group['stored_element_key']
        assert group['stored_naming_key'] == pairs[key] and group['element_object_id'] == elements[key]
        body, = group['cache_bodies']
        assert body['source_native_body_object_id'] == source_body
        anchor_id = body['result_anchor_object_id']
        assert anchor_id not in seen_anchors
        seen_anchors.add(anchor_id)
        same_selection(body['result_body_anchor'], anchors[anchor_id])
        assert anchors[anchor_id]['source_owner_object_id'] == identity
        result_body = body['result_native_body_object_id']
        assert result_body == anchors[anchor_id]['native_body_object_id'] and result_body != source_body
        assert result_body not in result_ids
        result_ids.add(result_body)
        binding_matches(result_body, body['result_body_binding'])
        components = body['stored_face_naming_components']
        assert components == [prefix, row['uninterpreted_common_feature_naming_component'], pairs[key]]
        assert tuple(components) not in seen_components
        seen_components.add(tuple(components))
        face_names = body['complete_result_face_naming_proof']
        assert len(face_names) == 6 and {tuple(p['name_key']) for p in face_names} == source_names
        assert all(p['stored_reference_components_int32'] == components for p in face_names)
        fit = body['measured_relative_rigid_fit']
        assert fit['matched_vertex_count'] == len(fit['vertex_correspondence']) == 8
        assert len(fit['matrix']) == 16 and all(math.isfinite(v) for v in fit['matrix'])
        assert 0 <= fit['maximum_vertex_residual_raw'] <= 1e-8
        for vertex in fit['vertex_correspondence']:
            signature = vertex['incident_face_name_keys']
            assert len(signature) == 3 and set(map(tuple, signature)) <= source_names
        vertex_pairs += 8
    assert seen_anchors == set(settings['result_record_object_ids'])
    naming_proofs = row['source_feature_face_naming_proofs']
    assert {n['native_body_object_id'] for n in naming_proofs} == result_ids | {source_body}
    assert len(naming_proofs) == len(result_ids) + 1
    source_fpm = 0
    for naming in naming_proofs:
        binding_matches(naming['native_body_object_id'], naming['binding'])
        assert naming['asm_body_index'] == naming['binding']['asm_body_index']
        proof = naming['proof']
        assert proof['FPM_literal_identity'] is None and len(proof['faces']) == 6
        for face in proof['faces']:
            for tag in face['opaque_FPM_attributes']:
                assert tag['definition_name'] == 'FPM_tracked_attrib_def'
                assert tag['owner_kind'] == 'face' and tag['owner_record_index'] == face['face_record_index']
            if naming['native_body_object_id'] == source_body:
                source_fpm += len(face['opaque_FPM_attributes'])
    assert source_fpm == 6
    nonordinal = 0
    if settings['symmetric_one'] or settings['symmetric_two']:
        keys = settings['stored_element_keys']
        assert keys.index(1) > 0 and keys[0] != min(pairs)
        by_key = {g['stored_element_key']: g['cache_bodies'][0]['result_native_body_object_id'] for g in groups}
        assert by_key[keys[0]] != by_key[min(pairs)]
        nonordinal = 1
    return dict(qualified_element_cache_groups=len(groups), qualified_result_body_caches=len(result_ids),
                typed_vertex_pairs=vertex_pairs, symmetric_nonordinal_controls=nonordinal,
                retained_opaque_source_FPM_attributes=source_fpm)


def compare(before, current, filename, proof):
    after = copy.deepcopy(current)
    assert len(before['streams']) == len(after['streams']) == 1
    old, stream = before['streams'][0], after['streams'][0]
    assert old['member'] == stream['member']
    expected = proof['summaries'][filename]
    assert set(expected) == {'decoded', 'unresolved', 'scope'} and not expected['unresolved']
    counts = dict(qualified_feature_cache_additions=0, receiving_feature_annotations=0,
                  qualified_element_cache_groups=0, qualified_result_body_caches=0,
                  typed_vertex_pairs=0, symmetric_nonordinal_controls=0,
                  retained_opaque_source_FPM_attributes=0, independent_prior_default_dictionary_checks=0)
    if filename in proof['defaults']:
        default = proof['defaults'][filename]
        assert default['member'] == old['member']
        if default['expected_default']['decoded'] or default['expected_default']['unresolved']:
            assert old[SUMMARY] == default['expected_default']
        else:
            assert SUMMARY not in old
        counts['independent_prior_default_dictionary_checks'] = 1
    if filename in TARGETS:
        assert SUMMARY not in old
        assert stream.pop(SUMMARY) == expected and len(expected['decoded']) == 1
        row = expected['decoded'][0]
        identity = row['feature_object_id']
        old_feature = next(f for f in old['features'] if f['object_id'] == identity)
        feature = next(f for f in stream['features'] if f['object_id'] == identity)
        assert old_feature['kind'] == feature['kind'] == 'RectangularPattern'
        assert SUMMARY not in old_feature and feature.pop(SUMMARY) == row
        counts.update(qualify_feature(row, old, old_feature))
        counts.update(qualified_feature_cache_additions=1, receiving_feature_annotations=1)
    elif expected['decoded']:
        assert stream[SUMMARY] == old[SUMMARY] == expected
    else:
        assert SUMMARY not in stream and SUMMARY not in old
    assert after == before, (filename, 'Unexpected previous-output change', differences(before, after))
    return dict(archive=filename, archive_sha256=sha(ROOT / filename), **counts,
                whole_output_unchanged=before == current,
                whole_output_exact_after_removing_only_new_feature_summary_and_attachment=True,
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
    assert len(before) == len(current) == len(FILES) == 12
    assert [r['file'] for r in before] == [str(ROOT / name) for name in FILES] == [r['file'] for r in current]
    proof = evidence()
    rows = [compare(b, a, name, proof) for b, a, name in zip(before, current, FILES)]
    keys = ('qualified_feature_cache_additions', 'receiving_feature_annotations',
            'qualified_element_cache_groups', 'qualified_result_body_caches',
            'typed_vertex_pairs', 'symmetric_nonordinal_controls', 'retained_opaque_source_FPM_attributes',
            'independent_prior_default_dictionary_checks')
    summary = {key: sum(r[key] for r in rows) for key in keys}
    summary.update(saved_files=12, whole_output_unchanged_controls=sum(r['whole_output_unchanged'] for r in rows),
                   unexpected_changes=0, comparator_baseline_main_calls=0 if baseline_cache else 12,
                   comparator_current_main_calls=0 if current_cache else 12, live_API_calls=0)
    caches = {}
    for side, path in (('baseline', baseline_cache), ('current', current_cache)):
        if path:
            caches[side] = dict(path=str(Path(path).resolve()), sha256=sha(path))
    sources = ('validate_rectangular_feature_cache_integration.py', 'validate_rectangular_cache_evidence_integration.py',
               'decode_rectangular_feature_caches.py', 'decode_rectangular_cache_evidence.py',
               'decode_circular_feature_caches.py', 'decode_rectangular_pattern_modes.py', 'decode_basics.py')
    return dict(scope='Fixed twelve saved archives against ccd06a7; only four new rectangular singleton Extrude-input cache summaries and direct feature annotations',
                baseline_commit=BASELINE, files=list(FILES), summary=summary, samples=rows,
                fixed_manifest_acquisition=dict(baseline_main_calls=12, current_main_calls=12,
                    baseline_passes=1, current_passes=1,
                    scope='Original fixed-manifest acquisition; cached comparison does not repeat either pass'),
                cache_provenance=caches, evidence_sha256={name: sha(ROOT / name) for name in (EVIDENCE, HOOK_EVIDENCE)},
                source_sha256={name: sha(ROOT / name) for name in sources},
                limitations=['Source feature identities follow typed descriptors and uniquely owned BODY anchors, never array order or coordinates',
                             'Measured relative cache fits are not serialized transforms or API element/grid IDs',
                             'All prior BODY evidence, analytic placements, warnings, geometry and ASM remain exact',
                             'Independent focused helper dictionaries supply expected additions; current main supplies no expected goldens',
                             'No live calls, broad corpus decoding, suppression or lifecycle inference'])


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--baseline-cache')
    p.add_argument('--current-cache')
    p.add_argument('--zstd-library')
    p.add_argument('--output', default='rectangular-feature-cache-integration.json')
    args = p.parse_args()
    zstd = args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result = validate(zstd, args.baseline_cache, args.current_cache)
    Path(args.output).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['summary'], sort_keys=True))


if __name__ == '__main__':
    main()
