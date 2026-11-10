"""Fixed identity-qualified Mirror cache reflection integration against 88d8356."""
import argparse
import copy
import json
import math
from pathlib import Path

from validate_rectangular_cache_evidence_integration import sha, digest, differences

ROOT = Path(__file__).resolve().parent
BASELINE = '88d8356'
FILES = tuple('mirrorfeatures-1ffa1b15c612/' + name + '.f3d' for name in (
    'body_brep_face_plane', 'feature_optimized', 'feature_identical', 'feature_adjust')) + (
    'tools-fda3948848f4/Mirror.f3d',
    'bodyselections-62e42366c722/mirror_two_bodies_plane.f3d',
    'remainingbodyinputs-7b3357274e85/mirror_two_features.f3d',
    'remainingbodyinputs-7b3357274e85/mirror_boss_faces.f3d',
    'datummirrorsupport-3a854f334428/offset_selected_support.f3d',
    'surfacetools-856ca50cf4c7/offset_positive.f3d',
    'surfacebounds-ac801bb00fae/untrim_all.f3d',
    'pathpatterns-de9857f6a1bc/spacing.f3d')
TARGETS = frozenset(FILES[:7])
SUMMARY = 'mirror_cache_reflections'
ATTACHMENT = 'mirror_cache_reflection'
EVIDENCE = 'mirror-cache-reflection-decoding.json'
SOURCE_EVIDENCE = 'mirror-cache-source-decoding.json'


def evidence():
    rows = {}
    for row in json.loads((ROOT / EVIDENCE).read_text())['samples']:
        if row['archive'] in FILES:
            assert row['archive'] not in rows
            rows[row['archive']] = row['expected_summary']
    assert set(rows) == set(FILES)
    source_rows = {r['archive']: r['expected_sources'] for r in json.loads(
        (ROOT / SOURCE_EVIDENCE).read_text())['samples'] if r['archive'] in FILES}
    assert set(source_rows) == set(FILES)
    for filename in FILES:
        if filename in TARGETS:
            expected_source, = source_rows[filename]
            reflected, = rows[filename]['decoded']
            assert reflected['native_source_provenance'] == expected_source
        else:
            assert source_rows[filename] == [] and not rows[filename]['decoded']
    return rows


def qualify(row, before, feature):
    old = before['streams'][0]
    settings = feature['tool_settings']
    identity = feature['object_id']
    assert row['feature_object_id'] == identity and row['input_kind'] == settings['input_kind']
    assert row['complete_source_result_prefix_bijection'] is True
    for key in ('API_element_identity', 'persistent_topology_identity', 'current_placement', 'qualified_historical_state'):
        assert row[key] is None
    anchors = {a['object_id']: a for a in old['body_selections']['body_anchors']}
    owned = [a for a in anchors.values() if a['source_owner_object_id'] == identity]
    assert set(row['owned_result_anchor_object_ids']) == {a['object_id'] for a in owned}
    if settings['input_kind'] == 'Body':
        sources = settings['native_input_body_object_ids']
    else:
        assert settings['input_kind'] == 'Feature'
        sources = []
        for item in settings['input_features']:
            source, = [a for a in anchors.values() if a['source_owner_object_id'] == item['source_feature_object_id']]
            assert next(f for f in old['features'] if f['object_id'] == item['source_feature_object_id'])['kind'] == 'Extrude'
            sources.append(source['native_body_object_id'])
    assert row['source_native_body_object_ids'] == sources
    source_proof = row['native_source_provenance']
    assert source_proof['feature_object_id'] == identity
    assert source_proof['source_native_body_object_ids'] == sources
    assert row['stored_instance_key_pair'] == source_proof['stored_instance_key_pair']
    assert row['stored_instance_key_pair'][0] == 2
    plane = source_proof['selected_plane']
    if settings['plane'] is not None:
        origin = settings['plane']['entity']['origin_cm']
        normal = settings['plane']['entity']['normal']
    else:
        prior = feature['mirror_face_plane_cache']
        assert plane['kind'] == 'NamedBRepFaceCache'
        assert plane['history_blob_member'] == prior['history_blob_member']
        origin = prior['cache_plane']['raw_origin']
        normal = prior['cache_plane']['raw_normal']
    assert plane['origin'] == origin
    length = math.hypot(*normal)
    unit = [v / length for v in normal]
    assert plane['unit_normal'] == unit
    rotation = [[float(i == j) - 2 * unit[i] * unit[j] for j in range(3)] for i in range(3)]
    distance = sum(p*n for p, n in zip(origin, unit))
    translation = [2 * distance * n for n in unit]
    matrix = [value for line, t in zip(rotation, translation) for value in line + [t]] + [0., 0., 0., 1.]
    assert len(row['computed_householder_matrix']) == 16
    assert all(math.isclose(a, b, rel_tol=0, abs_tol=1e-12) for a, b in zip(matrix, row['computed_householder_matrix']))
    determinant = (rotation[0][0] * (rotation[1][1]*rotation[2][2] - rotation[1][2]*rotation[2][1])
                   - rotation[0][1] * (rotation[1][0]*rotation[2][2] - rotation[1][2]*rotation[2][0])
                   + rotation[0][2] * (rotation[1][0]*rotation[2][1] - rotation[1][1]*rotation[2][0]))
    assert math.isclose(determinant, -1, rel_tol=0, abs_tol=1e-10)
    assert math.isclose(row['computed_determinant'], determinant, rel_tol=0, abs_tol=1e-12)
    assert max(abs(sum(matrix[4*i+k]*matrix[4*k+j] for k in range(4)) - float(i == j))
               for i in range(4) for j in range(4)) < 1e-10
    mapping_rows = {}
    for mapping in old['body_blob_bindings']['decoded']:
        for binding in mapping['bindings']:
            mapping_rows.setdefault(binding['native_body_object_id'], []).append((mapping, binding))
    asm, = [s for s in before['asm_decoding']['streams'] if s['member'] == row['history_blob_member']]
    graphs = {g['body_index']: g for g in asm['topology']['body_graphs']}

    def binding_matches(identity, observed):
        (mapping, binding), = mapping_rows[identity]
        assert mapping['mapping_record_object_id'] == row['mapping_record_object_id']
        assert mapping['owner_object_id'] == row['mapping_owner_object_id']
        assert mapping['history_blob_member'] == row['history_blob_member']
        assert observed['previous_ordinal_candidate'] is None and observed['ordinal_candidate_conflict'] is False
        assert {k: v for k, v in observed.items() if k != 'previous_ordinal_candidate'} == {
            k: binding[k] for k in observed if k != 'previous_ordinal_candidate'}
        graph = graphs[binding['asm_body_index']]
        assert graph['body_transform_is_identity'] is True
        return graph

    def same_anchor(observed, prior):
        assert observed['body_properties'] == {}
        assert {k: v for k, v in observed.items() if k != 'body_properties'} == {
            k: v for k, v in prior.items() if k != 'body_properties'}

    copies = row['cache_body_copies']
    assert len(copies) == len(sources) == len(owned)
    assert {c['source_native_body_object_id'] for c in copies} == set(sources)
    assert {c['result_body_anchor']['object_id'] for c in copies} == {a['object_id'] for a in owned}
    seeds, target_components, pair_vertices = {}, {}, 0
    for cached in copies:
        source, target = cached['source_native_body_object_id'], cached['result_native_body_object_id']
        anchor = cached['result_body_anchor']
        assert target not in sources and anchors[anchor['object_id']]['native_body_object_id'] == target
        assert anchors[anchor['object_id']]['source_owner_object_id'] == identity
        same_anchor(anchor, anchors[anchor['object_id']])
        source_graph = binding_matches(source, cached['source_body_binding'])
        target_graph = binding_matches(target, cached['result_body_binding'])
        prefix, = cached['stored_source_naming_prefix']
        assert prefix not in seeds
        seeds[prefix] = source
        components = cached['stored_result_face_naming_components']
        assert components == [prefix, row['uninterpreted_common_feature_naming_component'], row['stored_instance_key_pair'][1]]
        target_components[target] = components
        pairs = cached['vertex_correspondence']
        assert cached['matched_vertex_count'] == len(pairs) == 8
        assert len({p['source']['vertex_index'] for p in pairs}) == 8
        assert len({p['target']['vertex_index'] for p in pairs}) == 8
        assert {p['source']['vertex_index'] for p in pairs} == set(source_graph['vertex_indices'])
        assert {p['target']['vertex_index'] for p in pairs} == set(target_graph['vertex_indices'])
        assert {tuple(p['source']['raw_position']) for p in pairs} == set(map(tuple, source_graph['raw_vertex_positions']))
        assert {tuple(p['target']['raw_position']) for p in pairs} == set(map(tuple, target_graph['raw_vertex_positions']))
        residuals = []
        for point in pairs:
            assert len(point['incident_face_name_keys']) == 3
            expected = [sum(a*b for a, b in zip(line, point['source']['raw_position'])) + t
                        for line, t in zip(rotation, translation)]
            assert all(math.isclose(a, b, rel_tol=0, abs_tol=1e-12)
                       for a, b in zip(expected, point['computed_reflected_source_position']))
            residual = math.dist(expected, point['target']['raw_position'])
            assert math.isclose(residual, point['residual_raw'], rel_tol=0, abs_tol=1e-12) and residual < 1e-8
            residuals.append(residual)
        assert math.isclose(max(residuals), cached['maximum_vertex_residual_raw'], rel_tol=0, abs_tol=1e-12)
        pair_vertices += len(pairs)
    proofs = row['complete_body_naming_proofs']
    assert len(proofs) == 2 * len(sources)
    assert {p['native_body_object_id'] for p in proofs} == set(sources) | set(target_components)
    body_names, source_fpm = {}, 0
    for named in proofs:
        native_id = named['native_body_object_id']
        graph = binding_matches(native_id, named['binding'])
        assert named['asm_body_index'] == graph['body_index']
        proof = named['proof']
        assert proof['FPM_literal_identity'] is None and len(proof['faces']) == 6
        assert {face['face_record_index'] for face in proof['faces']} == set(graph['face_indices'])
        components = [prefix for prefix, body_id in seeds.items() if body_id == native_id] if native_id in sources else target_components[native_id]
        names = set()
        for face in proof['faces']:
            for attribute in face['opaque_FPM_attributes']:
                assert attribute['definition_name'] == 'FPM_tracked_attrib_def'
                assert attribute['owner_kind'] == 'face' and attribute['owner_record_index'] == face['face_record_index']
            if native_id in sources:
                source_fpm += len(face['opaque_FPM_attributes'])
            for tag in face['generic_tags']:
                assert tag['owner_record_index'] == face['face_record_index'] and tag['owner_kind'] == 'face'
                term, = tag['terms']
                assert term['stored_reference_components_int32'] == components
                names.add((term['name'], term['stored_index']))
        assert len(names) == 6
        body_names[native_id] = names
    for cached in copies:
        source, target = cached['source_native_body_object_id'], cached['result_native_body_object_id']
        assert body_names[source] == body_names[target]
        for point in cached['vertex_correspondence']:
            assert set(map(tuple, point['incident_face_name_keys'])) <= body_names[source]
    return dict(qualified_result_body_caches=len(copies), identity_fixed_vertex_pairs=pair_vertices,
                independently_checked_improper_reflection_matrices=1,
                retained_opaque_source_FPM_attributes=source_fpm)


def compare(before, current, filename, proof):
    after = copy.deepcopy(current)
    assert len(before['streams']) == len(after['streams']) == 1
    old, stream = before['streams'][0], after['streams'][0]
    assert old['member'] == stream['member'] and SUMMARY not in old
    expected = proof[filename]
    assert set(expected) == {'decoded', 'unresolved', 'scope'} and not expected['unresolved']
    counts = dict(qualified_Mirror_cache_reflections=0, receiving_feature_annotations=0,
                  qualified_result_body_caches=0, identity_fixed_vertex_pairs=0,
                  independently_checked_improper_reflection_matrices=0,
                  independent_source_factory_dictionary_checks=0, retained_opaque_source_FPM_attributes=0)
    if filename in TARGETS:
        assert stream.pop(SUMMARY) == expected and len(expected['decoded']) == 1
        row = expected['decoded'][0]
        identity = row['feature_object_id']
        old_feature = next(f for f in old['features'] if f['object_id'] == identity)
        feature = next(f for f in stream['features'] if f['object_id'] == identity)
        assert old_feature['kind'] == feature['kind'] == 'Mirror'
        assert ATTACHMENT not in old_feature and feature.pop(ATTACHMENT) == row
        counts.update(qualify(row, before, old_feature))
        counts.update(qualified_Mirror_cache_reflections=1, receiving_feature_annotations=1,
                      independent_source_factory_dictionary_checks=1)
    else:
        assert not expected['decoded'] and SUMMARY not in stream
        assert all(ATTACHMENT not in f for f in stream['features'])
    assert after == before, (filename, 'Unexpected previous-output change', differences(before, after))
    return dict(archive=filename, archive_sha256=sha(ROOT / filename), **counts,
                whole_output_unchanged=before == current,
                whole_output_exact_after_removing_only_new_summary_and_owner_attachment=True,
                all_previous_plane_status_settings_warnings_geometry_and_ASM_exact=True,
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
    keys = ('qualified_Mirror_cache_reflections', 'receiving_feature_annotations',
            'qualified_result_body_caches', 'identity_fixed_vertex_pairs',
            'independently_checked_improper_reflection_matrices', 'independent_source_factory_dictionary_checks',
            'retained_opaque_source_FPM_attributes')
    summary = {key: sum(r[key] for r in rows) for key in keys}
    summary.update(saved_files=12, whole_output_unchanged_controls=sum(r['whole_output_unchanged'] for r in rows),
                   unexpected_changes=0, comparator_baseline_main_calls=0 if baseline_cache else 12,
                   comparator_current_main_calls=0 if current_cache else 12, live_API_calls=0)
    caches = {}
    for side, path in (('baseline', baseline_cache), ('current', current_cache)):
        if path:
            caches[side] = dict(path=str(Path(path).resolve()), sha256=sha(path))
    sources = ('validate_mirror_cache_reflections_integration.py', 'validate_rectangular_cache_evidence_integration.py',
               'decode_mirror_cache_reflections.py', 'decode_mirror_cache_sources.py', 'decode_mirror_face_planes.py',
               'decode_mirror_modes.py', 'decode_circular_feature_caches.py', 'decode_basics.py')
    return dict(scope='Fixed twelve saved archives against 88d8356; seven separate typed Mirror source/result cache reflection proofs only',
                baseline_commit=BASELINE, files=list(FILES), summary=summary, samples=rows,
                fixed_manifest_acquisition=dict(baseline_main_calls=12, current_main_calls=12,
                    baseline_passes=1, current_passes=1,
                    scope='Original fixed-manifest acquisition; cached comparison does not repeat either pass'),
                cache_provenance=caches, evidence_sha256={name: sha(ROOT / name) for name in (EVIDENCE, SOURCE_EVIDENCE)},
                source_sha256={name: sha(ROOT / name) for name in sources},
                limitations=['Typed anchors/BODY mappings, complete naming prefixes and named vertex incidence fix identities before numerical reflection checks',
                             'The selected plane computes a determinant-minus-one reflection; no proper rigid-fit substitution',
                             'Stored caches are already placed; no transform application, regeneration, API handle or current lifecycle assignment',
                             'Every prior plane/status/setting/warning/global geometry and ASM dictionary stays exact',
                             'Complete independent focused helper goldens qualify additions; no live calls or broad corpus decoding'])


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--baseline-cache')
    p.add_argument('--current-cache')
    p.add_argument('--zstd-library')
    p.add_argument('--output', default='mirror-cache-reflection-integration.json')
    args = p.parse_args()
    zstd = args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result = validate(zstd, args.baseline_cache, args.current_cache)
    Path(args.output).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result['summary'], sort_keys=True))


if __name__ == '__main__':
    main()
