"""Three saved Patch circle sources, three controls, exact payload/API checks."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

from decode_one_face_edge_sources import decode_one_face_edge_sources
from decode_selection_recipe_incidence import decode_selection_recipe_incidence
from validate_mesh_remesh import load

ROOT = Path(__file__).resolve().parent
FILES = ('patchcontinuity-b9b0be85a281/brep_free.f3d',
         'patchcontinuity-b9b0be85a281/brep_tangent.f3d',
         'patchcontinuity-b9b0be85a281/brep_curvature.f3d',
         'surfacebounds-ac801bb00fae/untrim_manual.f3d',
         'surfacebounds-ac801bb00fae/extend_natural.f3d',
         'namedbodies-3c7c11fc2924/namedbodies.f3d')


def validate(root, zstd, baseline_path):
    baseline = json.loads(baseline_path.read_text())
    assert baseline['baseline_commit'] == '4780e22'
    before = {Path(o['file']).relative_to(root).as_posix(): o for o in baseline['before']}
    assert set(before) == set(FILES)
    truth_path = root/'patchcontinuity-b9b0be85a281/ground_truth.json'
    truth = json.loads(truth_path.read_text())
    report = dict(interface='decode_one_face_edge_sources(data,records,features,member,members,body_identifier_summary,body_selections=None)->associations/unresolved/scope',
        integration=dict(stream='one_face_edge_sources', feature_list='one_face_edge_sources',
            feature_owner_key='owner_object_id', descriptor_key='descriptor_object_id',
            old_warning_clearances=0, feature_classification_changes=0),
        scope='One direct named circular edge/one named face in an explicitly mapped saved Patch source BODY; opaque operation qualifier and context retained, no persistent/current/API identity',
        baseline=dict(commit='4780e22', path=str(baseline_path),
            sha256=hashlib.sha256(baseline_path.read_bytes()).hexdigest(), used_for_prior_outputs_only=True),
        source_API_truth_sha256=hashlib.sha256(truth_path.read_bytes()).hexdigest(),
        samples=[], guards=[], source_sha256={name: hashlib.sha256((root/name).read_bytes()).hexdigest()
            for name in ('decode_one_face_edge_sources.py', 'validate_one_face_edge_sources.py',
                'decode_patch_continuity.py', 'decode_surface_tools.py', 'decode_recipe_components.py',
                'decode_brep_recipes.py', 'decode_body_selections.py', 'decode_body_asm_identifiers.py',
                'decode_asm_recipe_tags.py', 'decode_asm_subtypes.py', 'decode_brep.py')})
    loaded = {}
    for archive in FILES:
        data, records, features, member, members = load(root, archive, zstd)
        loaded[archive] = (data, records, features, member, members)
        stream = before[archive]['streams'][0]
        identities, anchors = stream['body_asm_identifiers'], stream['body_selections']
        saved = copy.deepcopy((features, identities, anchors))
        summary = decode_one_face_edge_sources(data, records, features, member, members, identities, anchors)
        assert not summary['unresolved'], (archive, summary)
        assert (features, identities, anchors) == saved
        old = decode_selection_recipe_incidence(data, records, features, member, members, identities, anchors)
        assert old == stream['selection_recipe_incidence'], archive
        sample = dict(archive=archive, archive_sha256=hashlib.sha256((root/archive).read_bytes()).hexdigest(),
            descriptor_ids=[r['descriptor_object_id'] for r in summary['associations']],
            expected_summary=summary, expected_prior_selection_recipe_incidence=old,
            prior_summary_exact=True, input_features_and_contexts_unchanged=True)
        if archive.startswith('patchcontinuity-'):
            assert len(summary['associations']) == 1
            row = summary['associations'][0]
            assert row['owner_object_id'] == 328 and row['historical_source_owner_object_id'] == 240
            assert row['native_body_object_id'] == 267 and row['explicit_asm_body_index'] == 3
            assert all(row[k] is None for k in ('current_source_identity', 'persistent_source_identity',
                'API_handle_identity', 'qualified_historical_state', 'traversal_parameter_mapping'))
            actual = next(s for s in truth['samples'] if s['file'] == Path(archive).name)
            edge = actual['source_before_patch']['edge']
            cached = row['cached_source']; circle = cached['geometry']
            assert edge['geometry_type'] == 'adsk::core::Circle3D' and edge['face_count'] == 1
            assert edge['is_param_reversed'] is False and edge['evaluator_extents_returned'] is True
            assert cached['is_closed'] is True and cached['parameter_domain'] == edge['evaluator_extents']
            assert circle['raw_center'] == edge['center_cm'] and circle['normal'] == edge['normal']
            assert math.isclose(circle['raw_radius'], edge['radius_cm'], abs_tol=1e-12)
            assert all(abs(a-b) < 1e-12 for a,b in zip(cached['raw_endpoint_point'], edge['start_vertex_cm']))
            native_body = next(b for b in stream['body_properties']['bodies'] if b['object_id'] == 267)
            assert native_body['name'] == actual['source_before_patch']['body']['name']
            axis, normal, center = circle['raw_reference_axis'], circle['normal'], circle['raw_center']
            cross = [normal[1]*axis[2]-normal[2]*axis[1], normal[2]*axis[0]-normal[0]*axis[2],
                     normal[0]*axis[1]-normal[1]*axis[0]]
            checks = []
            for evaluation in edge['evaluator_samples']:
                assert evaluation['returned'] is True
                t = evaluation['parameter']
                p = [center[i]+math.cos(t)*axis[i]+math.sin(t)*cross[i] for i in range(3)]
                error = max(abs(a-b) for a,b in zip(p, evaluation['point_cm']))
                assert error < 1e-12
                checks.append(dict(parameter=t, API_point_cm=evaluation['point_cm'],
                    derived_natural_circle_cache_point=p, maximum_coordinate_error=error))
            sample['API_corroboration'] = dict(source_body_name=actual['source_before_patch']['body']['name'],
                selected_source_geometry_type=edge['geometry_type'], selected_source_radius_cm=edge['radius_cm'],
                single_incident_face_count=1, natural_cache_evaluator_checks=checks,
                selected_edge_API_handle_identity=None,
                scope='Numeric corroboration after exact native naming/incidence; no API token mapping or general edge traversal parameter map inferred')
        else:
            assert summary['associations'] == []
            sample['control_status'] = ('Manual Untrim28-byte qualifier/owner stays outside Patch scope' if 'untrim_' in archive else
                'Extend156-byte operation remains unsupported by this decoder' if 'extend_' in archive else
                'Unrelated named BODY control; no candidate or ASM work')
        report['samples'].append(sample)

    archive = FILES[1]
    data, records, features, member, members = loaded[archive]
    stream = before[archive]['streams'][0]
    identifiers, anchors = stream['body_asm_identifiers'], stream['body_selections']
    by = {r.object_id:r for r in records if r.is_primary}
    positive = next(s['expected_summary']['associations'][0] for s in report['samples'] if s['archive'] == archive)

    def rejected(label, changed_data=data, changed_records=records, changed_identifiers=identifiers):
        changed_members = dict(members)
        changed_members[member] = changed_data
        result = decode_one_face_edge_sources(changed_data, changed_records, features, member,
            changed_members, changed_identifiers, anchors)
        assert not result['associations'], label
        report['guards'].append(dict(label=label, associations_absent=True, diagnostics=result['unresolved']))

    descriptor = by[positive['descriptor_object_id']]
    recipe = by[positive['recipe_object_id']]
    support = by[positive['support_object_id']]
    changes = (
        ('Descriptor trailer marker rejected', descriptor.body+223, b'\0'),
        ('Opaque final qualifier mutation remains unobserved', recipe.end-4, struct.pack('<i', 0)),
        ('Complete edge-name numeric tuple mismatch rejected', recipe.body+31, struct.pack('<i', 302)),
        ('Source support redirects to receiving Patch', support.body+13, struct.pack('<Q', 328)))
    for label, offset, value in changes:
        altered = bytearray(data); altered[offset:offset+len(value)] = value
        rejected(label, bytes(altered))
    for identity, label in ((332, 'Duplicate primary descriptor'), (328, 'Duplicate receiving Patch'),
                            (8, 'Duplicate native mapping identity')):
        rejected(label, changed_records=records+[by[identity]])
    altered = copy.deepcopy(identifiers)
    for mapping in altered['decoded']:
        for binding in mapping['bindings']:
            if binding['native_body_object_id'] == 267:
                binding['asm_body_index'] = 1
    rejected('Forged supplied source BODY record index', changed_identifiers=altered)
    report['summary'] = dict(focused_archives=6, admitted_patch_sources=3, empty_controls=3,
        prior_selection_recipe_summaries_exact=6, full_recipe_and_operation_replays=3,
        independent_API_circle_samples=15, malformed_guards=len(report['guards']),
        maximum_API_sample_error=max(c['maximum_coordinate_error'] for s in report['samples']
            for c in s.get('API_corroboration',{}).get('natural_cache_evaluator_checks',[])),
        main_runs=0, live_calls=0, old_warning_clearances=0)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--zstd-library', required=True)
    parser.add_argument('--baseline-cache', type=Path, default=Path('/private/tmp/fusion-one-face-edge-baseline.json'))
    parser.add_argument('--output', type=Path, default=ROOT/'one-face-edge-source-decoding.json')
    args = parser.parse_args()
    report = validate(args.root.resolve(), args.zstd_library, args.baseline_cache)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps(report['summary']))
