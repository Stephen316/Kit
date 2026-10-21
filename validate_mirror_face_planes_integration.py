"""Fixed Mirror named planar-face cache integration against b6691d2."""
import argparse
import copy
import json
import math
from pathlib import Path

from validate_rectangular_cache_evidence_integration import sha, digest, differences

ROOT = Path(__file__).resolve().parent
BASELINE = 'b6691d2'
FILES = tuple('mirrorfeatures-1ffa1b15c612/' + name + '.f3d' for name in (
    'body_brep_face_plane', 'feature_optimized', 'feature_identical', 'feature_adjust')) + (
    'tools-fda3948848f4/Mirror.f3d',
    'surfacebounds-ac801bb00fae/untrim_all.f3d',
    'surfacetools-856ca50cf4c7/offset_positive.f3d',
    'pathpatterns-de9857f6a1bc/spacing.f3d')
SUMMARY = 'mirror_face_planes'
ATTACHMENT = 'mirror_face_plane_cache'
EVIDENCE = 'mirror-face-plane-decoding.json'
API_TRUTH = 'mirrorfeatures-1ffa1b15c612/ground_truth.json'
PLANE_STATUS = 'Owned BRepFace recipe mapped to a named initial-cache plane; qualified before-feature/current plane and persistent face identity remain unresolved'
GEOMETRY_STATUS = 'Named initial ASM plane decoded in mirror_face_plane_cache; qualified before-feature/current geometry and persistent identity unresolved'
OLD_PLANE_STATUS = 'Owned BRepFace recipe/body provenance decoded; plane equation unresolved'
OLD_GEOMETRY_STATUS = 'Owned face recipe and historical support body; native plane origin/normal and exact persistent face identity unresolved'


def evidence():
    rows, legacy = {}, {}
    for row in json.loads((ROOT / EVIDENCE).read_text())['samples']:
        if row['archive'] in FILES:
            assert row['archive'] not in rows
            rows[row['archive']] = row['expected_summary']
            if 'expected_legacy_settings' in row:
                legacy[row['archive']] = row['expected_legacy_settings']
    assert set(rows) == set(FILES)
    assert set(legacy) == set(FILES[:4])
    return dict(summaries=rows, legacy_settings=legacy)


def qualify(row, before, feature):
    old = before['streams'][0]
    settings = feature['tool_settings']
    source = settings['plane_source']
    assert row['feature_object_id'] == feature['object_id']
    assert row['plane_selection_record_object_id'] == settings['plane_selection_record_object_id']
    assert row['descriptor_object_id'] == source['descriptor_object_id']
    owned = row['native_plane_source']
    assert owned['kind'] == 'Face'
    assert owned['face'] == {k: v for k, v in source.items() if k not in (
        'kind', 'selection_object_id', 'plane_geometry', 'geometry_status')}
    anchors = {a['object_id']: a for a in old['body_selections']['body_anchors']}
    anchor = anchors[source['body_anchor_object_id']]
    assert anchor['native_body_object_id'] == source['native_body_object_id']
    assert anchor['source_owner_object_id'] == source['source_owner_object_id']
    body_id = anchor['native_body_object_id']
    support = row['support_provenance']
    assert support['historical_body_anchor_object_id'] == anchor['object_id']
    assert support['historical_anchor_source_owner_object_id'] == anchor['source_owner_object_id']
    assert support['support_contains_anchor_owner'] == (anchor['source_owner_object_id'] in support['support_source_record_object_ids'])
    source_features = {f['object_id']: f for f in old['features']}
    assert source_features[anchor['source_owner_object_id']]['kind'] == 'Extrude'
    for identity in support['support_source_record_object_ids']:
        assert source_features[identity]['kind'] == 'Extrude'
    recipe, prior_recipe = row['recipe'], source['recipe']
    for key in ('object_id', 'class_guid', 'record_offset', 'stored_header_fields',
                'payload_kind', 'payload_relative_offset', 'payload_length', 'payload_hex'):
        assert recipe[key] == prior_recipe[key]
    assert recipe['payload_hex'] == '00000000ffffffff' and row['exact_recipe_payload_replay'] is True
    entry, = recipe['name_table']
    prior_entry, = prior_recipe['name_table']
    assert entry['table_index'] == prior_entry['table_index'] == 0
    term, = entry['terms']
    prior_term, = prior_entry['terms']
    assert term['name'] == prior_term['name'] and term['stored_index'] == prior_term['stored_index']
    assert term['stored_reference_component_count'] == prior_term['stored_reference_tag'] == 1
    assert term['stored_reference_components_int32'] == [prior_term['stored_reference_value']]
    assert term['stored_reference_terminator_uint32'] == 0
    matches = [(mapping, binding) for mapping in old['body_blob_bindings']['decoded']
               for binding in mapping['bindings'] if binding['native_body_object_id'] == body_id]
    (mapping, binding), = matches
    assert row['mapping_record_object_id'] == mapping['mapping_record_object_id']
    assert row['mapping_owner_object_id'] == mapping['owner_object_id']
    assert row['history_blob_member'] == mapping['history_blob_member']
    observed_binding = row['source_body_binding']
    # Revalidating the already keyed mapping has no candidate_asm_body_index;
    # the old main retains its earlier diagnostic candidate separately.
    assert observed_binding['previous_ordinal_candidate'] is None
    assert observed_binding['ordinal_candidate_conflict'] is False
    assert {key: value for key, value in observed_binding.items() if key != 'previous_ordinal_candidate'} == {
        key: binding[key] for key in observed_binding if key != 'previous_ordinal_candidate'}
    operand = row['cached_operand']
    assert operand['body_record_index'] == binding['asm_body_index']
    match, = row['mapped_body_FACE_candidates']
    assert match['owner_kind'] == 'face'
    assert match['owner_record_index'] == operand['face_record_index']
    assert match['body_graph_membership'] == [binding['asm_body_index']]
    assert row['complete_name_match']['name_table_index'] == 0
    assert match in row['complete_name_match']['candidates']
    tag = row['selected_generic_tag']
    assert tag['attribute_record_index'] == match['attribute_record_index']
    assert tag['owner_kind'] == 'face' and tag['owner_record_index'] == operand['face_record_index']
    named_term, = tag['terms']
    for key in ('name', 'stored_index', 'stored_reference_component_count', 'stored_reference_components_int32',
                'stored_reference_components_uint32', 'stored_reference_terminator_uint32'):
        assert named_term[key] == term[key]
    original = row['selected_attribute_original_bytes']
    assert original['record_index'] == tag['attribute_record_index']
    assert len(bytes.fromhex(original['payload_hex'])) == original['end_offset'] - original['offset']
    asm, = [s for s in before['asm_decoding']['streams'] if s['member'] == row['history_blob_member']]
    graph, = [g for g in asm['topology']['body_graphs'] if g['body_index'] == binding['asm_body_index']]
    assert graph['body_transform_is_identity'] is True
    assert operand['face_record_index'] in graph['face_indices']
    selected_surface, = [s for s in graph['analytic_surfaces'] if s['face_index'] == operand['face_record_index']]
    assert selected_surface['surface_index'] == operand['surface']['index'] == operand['face']['surface_index']
    assert operand['surface']['analytic_surface'] == selected_surface['geometry']
    assert operand['face']['is_reversed'] == selected_surface['face_is_reversed']
    loops = [loop for loop in graph['face_trim_loops'] if loop['face_index'] == operand['face_record_index']]
    assert len(loops) == 1
    routes = operand['incidence_routes']
    assert len(routes) == len(operand['boundary_edges']) == 4
    assert {r['loop_record_index'] for r in routes} == {loops[0]['loop_index']}
    assert {r['edge_record_index'] for r in routes} == {t['edge_index'] for t in loops[0]['trims']}
    assert {r['coedge_record_index'] for r in routes} == {t['coedge_index'] for t in loops[0]['trims']}
    plane = row['cache_plane']
    geometry = selected_surface['geometry']
    assert plane['kind'] == geometry['kind'] == 'Plane'
    assert plane['raw_origin'] == geometry['raw_origin']
    assert plane['raw_normal'] == geometry['normal']
    assert plane['stored_reference_axis'] == geometry['stored_reference_axis']
    norm = math.sqrt(sum(v*v for v in plane['raw_normal']))
    assert norm > 0 and plane['normalized_unit_normal'] == [v/norm for v in plane['raw_normal']]
    assert plane['normalized_plane_equation'] == plane['normalized_unit_normal'] + [
        -sum(n*p for n,p in zip(plane['normalized_unit_normal'], plane['raw_origin']))]
    assert plane['derived_maximum_boundary_plane_residual_raw'] <= 1e-9
    for key in ('API_handle_identity', 'persistent_source_identity', 'current_source_identity',
                'qualified_historical_state', 'reflection_geometry'):
        assert row[key] is None
    native_records = {r['object_id']: r for r in row['native_record_proof']}
    assert feature['object_id'] in native_records
    assert native_records[feature['object_id']]['record_offset'] == feature['record_offset']
    assert native_records[feature['object_id']]['class_guid'] == feature['class_guid']
    for record in native_records.values():
        assert len(bytes.fromhex(record['payload_hex'])) == record['end_offset'] - record['body_offset']
    # These API numbers corroborate the identity-fixed stored plane. They never
    # select a native FACE or create an API-token/native-ID assignment.
    truth_path = ROOT / API_TRUTH
    truth = json.loads(truth_path.read_text())
    actual, = [s for s in truth['samples'] if s['file'] == 'body_brep_face_plane.f3d']
    assert not truth['errors'] and not actual['getter_errors'] and actual['export_exists'] is True
    assert (truth_path.parent / 'complete.txt').is_file()
    props, = [p for p in old['body_properties']['bodies'] if p['object_id'] == body_id]
    for role in ('mirror_plane_before_mirror', 'actual_mirror_plane'):
        api = actual[role]
        assert api['entity_type'] == 'adsk::fusion::BRepFace' and api['surface_type'] == 0
        assert api['source_body']['name'] == props['name']
        assert api['origin_cm'] == api['point_on_face_cm'] == plane['raw_origin']
        assert api['normal'] == plane['raw_normal'] == plane['normalized_unit_normal']
    return dict(independent_API_plane_comparisons=2)


def compare(before, current, filename, proof):
    after = copy.deepcopy(current)
    assert len(before['streams']) == len(after['streams']) == 1
    old, stream = before['streams'][0], after['streams'][0]
    assert old['member'] == stream['member'] and SUMMARY not in old
    expected = proof['summaries'][filename]
    assert set(expected) == {'decoded', 'unresolved', 'scope'} and not expected['unresolved']
    counts = dict(qualified_face_plane_caches=0, receiving_feature_annotations=0,
                  bounded_status_string_refinements=0, independent_API_plane_comparisons=0,
                  independent_prior_Mirror_settings_checks=0)
    if filename in proof['legacy_settings']:
        prior_mirror, = [f for f in old['features'] if f['kind'] == 'Mirror']
        assert prior_mirror['tool_settings'] == proof['legacy_settings'][filename]
        counts['independent_prior_Mirror_settings_checks'] = 1
    if filename == FILES[0]:
        assert stream.pop(SUMMARY) == expected and len(expected['decoded']) == 1
        row = expected['decoded'][0]
        identity = row['feature_object_id']
        old_feature = next(f for f in old['features'] if f['object_id'] == identity)
        feature = next(f for f in stream['features'] if f['object_id'] == identity)
        assert old_feature['kind'] == feature['kind'] == 'Mirror'
        assert ATTACHMENT not in old_feature and feature.pop(ATTACHMENT) == row
        counts.update(qualify(row, before, old_feature))
        settings, old_settings = feature['tool_settings'], old_feature['tool_settings']
        assert settings['plane'] is old_settings['plane'] is None
        assert settings['plane_source']['plane_geometry'] is old_settings['plane_source']['plane_geometry'] is None
        assert settings['plane_selection_status'] == PLANE_STATUS
        assert settings['plane_source']['geometry_status'] == GEOMETRY_STATUS
        assert old_settings['plane_selection_status'] == OLD_PLANE_STATUS
        assert old_settings['plane_source']['geometry_status'] == OLD_GEOMETRY_STATUS
        settings['plane_selection_status'] = old_settings['plane_selection_status']
        settings['plane_source']['geometry_status'] = old_settings['plane_source']['geometry_status']
        counts.update(qualified_face_plane_caches=1, receiving_feature_annotations=1,
                      bounded_status_string_refinements=2)
    else:
        assert not expected['decoded'] and SUMMARY not in stream
        assert all(ATTACHMENT not in f for f in stream['features'])
    assert after == before, (filename, 'Unexpected previous-output change', differences(before, after))
    return dict(archive=filename, archive_sha256=sha(ROOT / filename), **counts,
                whole_output_unchanged=before == current,
                whole_output_exact_after_only_qualified_additions_and_two_status_restorations=True,
                old_plane_geometry_None_all_other_settings_warnings_geometry_and_ASM_exact=True,
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
    assert len(before) == len(current) == len(FILES) == 8
    assert [r['file'] for r in before] == [str(ROOT / name) for name in FILES] == [r['file'] for r in current]
    proof = evidence()
    rows = [compare(b, a, name, proof) for b, a, name in zip(before, current, FILES)]
    keys = ('qualified_face_plane_caches', 'receiving_feature_annotations',
            'bounded_status_string_refinements', 'independent_API_plane_comparisons',
            'independent_prior_Mirror_settings_checks')
    summary = {key: sum(r[key] for r in rows) for key in keys}
    summary.update(saved_files=8, whole_output_unchanged_controls=sum(r['whole_output_unchanged'] for r in rows),
                   unexpected_changes=0, comparator_baseline_main_calls=0 if baseline_cache else 8,
                   comparator_current_main_calls=0 if current_cache else 8, live_API_calls=0)
    caches = {}
    for side, path in (('baseline', baseline_cache), ('current', current_cache)):
        if path:
            caches[side] = dict(path=str(Path(path).resolve()), sha256=sha(path))
    sources = ('validate_mirror_face_planes_integration.py', 'validate_rectangular_cache_evidence_integration.py',
               'decode_mirror_face_planes.py', 'decode_mirror_modes.py', 'decode_basics.py')
    return dict(scope='Fixed eight saved archives against b6691d2; one separately scoped named initial planar FACE cache and two precise status-string refinements',
                baseline_commit=BASELINE, files=list(FILES), summary=summary, samples=rows,
                fixed_manifest_acquisition=dict(baseline_main_calls=8, current_main_calls=8,
                    baseline_passes=1, current_passes=1,
                    scope='Original fixed-manifest acquisition; cached comparison does not repeat either pass'),
                cache_provenance=caches, evidence_sha256={name: sha(ROOT / name) for name in (EVIDENCE, API_TRUTH)},
                source_sha256={name: sha(ROOT / name) for name in sources},
                limitations=['Only one saved planar BRepFace support contrast; the original tool Mirror uses a ConstructionPlane',
                             'Native descriptor/anchor/BODY mapping and complete names choose the FACE before inspecting its plane',
                             'An initial-cache plane is distinct from qualified before-feature/current geometry and persistent/API face identity',
                             'Both existing plane fields remain None; no normal-sign convention, arbitrary plane-origin rule or reflection result identity inferred',
                             'Complete independent helper goldens qualify additions; all previous unqualified fields stay exact',
                             'No live calls, broader corpus decoding or regeneration'])


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--baseline-cache')
    p.add_argument('--current-cache')
    p.add_argument('--zstd-library')
    p.add_argument('--output', default='mirror-face-plane-integration.json')
    args = p.parse_args()
    zstd = args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result = validate(zstd, args.baseline_cache, args.current_cache)
    Path(args.output).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['summary'], sort_keys=True))


if __name__ == '__main__':
    main()
