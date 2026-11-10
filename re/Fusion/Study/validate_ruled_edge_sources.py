"""Eight saved Ruled/source controls and a few native framing regressions."""
import argparse
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import struct

from asm_records import inspect_asm
from decode_asm_recipe_tags import decode_asm_generic_tags, match_recipe_tag_names
from decode_one_face_edge_sources import _replay_recipe
from decode_parameters import read_string
from decode_recipe_components import decode_counted_recipe
from decode_ruled_edge_sources import decode_ruled_edge_sources, decode_ruled_edge_operands
from decode_selection import native_origin_entities
from decode_selection_recipe_incidence import decode_selection_recipe_incidence
from decode_sketch import reference
from decode_surface_tools import decode_surface_tool
from validate_mesh_remesh import load

ROOT = Path(__file__).resolve().parent
CAPTURE = 'surfacebounds-ac801bb00fae'
FILES = tuple(CAPTURE+'/'+name+'.f3d' for name in (
    'ruled_tangent', 'ruled_normal', 'ruled_direction', 'ruled_mitered', 'extend_natural', 'extend_two_edges'))+(
    'patchcontinuity-b9b0be85a281/brep_tangent.f3d', 'namedbodies-3c7c11fc2924/namedbodies.f3d')


def validate(root, zstd, baseline_path):
    baseline = json.loads(baseline_path.read_text())
    assert baseline['baseline_commit'] == 'b6385cd'
    before = {Path(o['file']).relative_to(root).as_posix(): o for o in baseline['before']}
    assert set(before) == set(FILES)
    truth_path = root/CAPTURE/'ground_truth.json'
    truth = json.loads(truth_path.read_text())
    report = dict(interface='decode_ruled_edge_sources(data,records,features,member,members,body_identifier_summary,body_selections=None)->associations/unresolved/scope',
        operand_interface='decode_ruled_edge_operands(recipe)->complete156-byte operation fields, without source ownership inference',
        integration=dict(stream='ruled_edge_sources', owner_feature_list='ruled_edge_sources',
            owner_field='owner_object_id', old_warning_clearances=0, old_tool_changes=0),
        scope='One source edge per Ruled owner despite two native selector roles; no API geometry/handle identity, general direction, persistent topology or historical-state claim',
        baseline=dict(commit='b6385cd', path=str(baseline_path), sha256=hashlib.sha256(baseline_path.read_bytes()).hexdigest()),
        samples=[], malformed_guards=[], source_sha256={n: hashlib.sha256((root/n).read_bytes()).hexdigest()
            for n in ('decode_ruled_edge_sources.py', 'validate_ruled_edge_sources.py',
                'decode_one_face_edge_sources.py', 'decode_selection.py', 'decode_surface_tools.py',
                'decode_body_selections.py', 'decode_body_asm_identifiers.py', 'decode_recipe_components.py',
                'decode_asm_recipe_tags.py', 'decode_asm_subtypes.py', 'decode_brep.py')})
    loaded = {}
    for archive in FILES:
        data, records, features, member, members = load(root, archive, zstd)
        loaded[archive] = (data, records, features, member, members)
        stream = before[archive]['streams'][0]
        identities, selections = stream['body_asm_identifiers'], stream['body_selections']
        inputs = copy.deepcopy((features, identities, selections))
        summary = decode_ruled_edge_sources(data, records, features, member, members, identities, selections)
        assert not summary['unresolved'], (archive, summary)
        assert (features, identities, selections) == inputs
        old_incidence = decode_selection_recipe_incidence(data, records, features, member, members, identities, selections)
        assert old_incidence == stream['selection_recipe_incidence'], archive
        row = dict(archive=archive, archive_sha256=hashlib.sha256((root/archive).read_bytes()).hexdigest(),
            expected_summary=summary, expected_prior_selection_recipe_incidence=old_incidence,
            prior_incidence_exact=True, input_features_and_contexts_unchanged=True)
        primary = {r.object_id:r for r in records if r.is_primary}
        if '/ruled_' in archive:
            assert len(summary['associations']) == 1
            source = summary['associations'][0]
            assert source['owner_object_id'] == 285 and source['historical_source_owner_object_id'] == 243
            assert source['native_body_object_id'] == 278 and source['explicit_asm_body_index'] == 3
            assert [r['role'] for r in source['descriptor_roles']] == ['Profile', 'Auxiliary']
            assert [r['descriptor_object_id'] for r in source['descriptor_roles']] == [295, 302]
            assert source['same_recipe_bytes'] is True and source['same_cached_edge'] is True
            assert source['cached_source']['edge_record_index'] == 46
            assert [v['vertex_record_index'] for v in source['endpoint_incidence']] == [74, 75]
            assert [v['adjacent_edge_record_index'] for v in source['endpoint_incidence']] == [72, 70]
            assert all(source[k] is None for k in ('API_input_edge_count', 'API_handle_identity',
                'direction_parameter_mapping', 'current_source_identity', 'persistent_source_identity', 'qualified_historical_state'))
            bodies = []
            for role in source['descriptor_roles']:
                recipe_record = primary[role['recipe_object_id']]
                recipe = decode_counted_recipe(data, recipe_record)
                assert _replay_recipe(recipe) == data[recipe_record.body:recipe_record.end]
                assert decode_ruled_edge_operands(recipe)['exact_full_operation_payload_replay'] is True
                bodies.append(data[recipe_record.body:recipe_record.end])
            assert bodies[0] == bodies[1]
            feature = next(f for f in features if f['object_id'] == 285)
            rec = primary[285]
            controls = decode_surface_tool(data, records, data[rec.body:rec.end], feature,
                                           native_origin_entities(data, records))
            expected_controls = next(f for f in stream['features'] if f['object_id'] == 285)['tool_settings']
            assert controls == expected_controls, archive
            actual = next(s for s in truth['samples'] if s['file'] == Path(archive).name)
            row.update(expected_prior_tool_settings=controls,
                API_evidence=dict(ground_truth_sha256=hashlib.sha256(truth_path.read_bytes()).hexdigest(),
                    actual_saved_settings=actual['settings'], selected_edge_geometry_getters_captured=False,
                    native_API_handle_assignment=None,
                    scope='Existing saved API controls only; no independent source-edge geometry or two-input-edge claim'),
                full_recipe_replays=2, duplicate_selector_roles_name_one_edge=True)
        else:
            assert summary['associations'] == []
            row['control_status'] = 'Outside native SurfaceRuled ownership gate; no new source association'
            if '/extend_' in archive:
                descriptor_ids = [e['descriptor_object_id'] for e in old_incidence['unresolved']
                                  if e['reason'] == 'Source edge operation extent/final qualifier unsupported']
                evidence = []
                for identity in descriptor_ids:
                    descriptor = primary[identity]; payload = data[descriptor.body:descriptor.end]
                    rec = primary[reference(payload, 4)]; recipe = decode_counted_recipe(data, rec)
                    try:
                        operands = decode_ruled_edge_operands(recipe)
                        operand_status = dict(scoped_Ruled_template_replay=True, reason=None)
                    except ValueError as exc:
                        words = struct.unpack('<39i', bytes.fromhex(recipe['payload_hex']))
                        assert words[11:21] == (2, -1, 0, 0, -1, 0, -1, 0, 0, -1)
                        operand_status = dict(scoped_Ruled_template_replay=False, reason=str(exc),
                            first_endpoint_nested_name_order=[words[11], words[16]],
                            scope='Extend reversed nested-edge order is outside the frozen Ruled template')
                    assert _replay_recipe(recipe) == data[rec.body:rec.end]
                    anchor = next(a for a in selections['body_anchors'] if a['object_id'] == reference(payload, 198))
                    mappings = [m for m in identities['decoded'] if any(b['native_body_object_id'] == anchor['native_body_object_id'] for b in m['bindings'])]
                    assert len(mappings) == 1
                    raw = members[mappings[0]['history_blob_member']]
                    parsed = inspect_asm(raw); tags = decode_asm_generic_tags(raw, parsed=parsed, allow_fpm_tracking=True)
                    correspondence = match_recipe_tag_names(recipe, tags, parsed=parsed)
                    counts = [e['candidate_count'] for e in correspondence['name_entries']]
                    assert counts == [1, 0, 1, 1]
                    evidence.append(dict(descriptor_object_id=identity, full_counted_recipe_replay=True,
                        operand_template=operand_status,
                        name_candidate_counts=counts, initial_FACE_operand_match=False,
                        scoped_runtime_source_association=False, historical_face_resolution=None))
                row['Extend_operand_only_controls'] = evidence
        report['samples'].append(row)

    archive = FILES[0]
    data, records, features, member, members = loaded[archive]
    stream = before[archive]['streams'][0]
    identities, selections = stream['body_asm_identifiers'], stream['body_selections']
    by = {r.object_id:r for r in records if r.is_primary}
    success = report['samples'][0]['expected_summary']['associations'][0]

    def reject(label, altered_data=data, altered_records=records, altered_features=features,
               altered_identities=identities, expected_successes=0):
        altered_members = dict(members); altered_members[member] = altered_data
        summary = decode_ruled_edge_sources(altered_data, altered_records, altered_features, member,
            altered_members, altered_identities, selections)
        assert len(summary['associations']) == expected_successes, label
        assert summary['unresolved'], label
        report['malformed_guards'].append(dict(label=label,
            successful_owner_ids=[r['owner_object_id'] for r in summary['associations']],
            diagnostics=summary['unresolved']))

    profile, auxiliary = success['descriptor_roles']
    recipe = by[profile['recipe_object_id']]
    aux_recipe = by[auxiliary['recipe_object_id']]
    proxy_support = by[profile['proxy_support_object_id']]
    descriptor = by[profile['descriptor_object_id']]
    changes = (
        ('Unobserved outer opaque qualifier', recipe.end-4, struct.pack('<i', 0)),
        ('Nested endpoint edge-count framing', recipe.end-156+40, struct.pack('<I', 3)),
        ('Profile/auxiliary complete names disagree', aux_recipe.body+31, struct.pack('<i', 302)),
        ('Profile proxy support redirects to other proxy', proxy_support.body+32,
            struct.pack('<Q', auxiliary['selection_record_object_id'])),
        ('Descriptor trailer marker', descriptor.body+223, b'\0'))
    for label, offset, value in changes:
        changed = bytearray(data); changed[offset:offset+len(value)] = value
        reject(label, bytes(changed))
    reject('Duplicate primary profile descriptor', altered_records=records+[descriptor])
    changed = copy.deepcopy(identities)
    for mapping in changed['decoded']:
        for binding in mapping['bindings']:
            if binding['native_body_object_id'] == 278: binding['asm_body_index'] = 1
    reject('Forged supplied source BODY index', altered_identities=changed)
    # Regression for the reviewed metadata-map/local-name shadowing bug: the
    # second owner reaches metadata lookup only after the first fully succeeds.
    owner = by[285]; fake_id = 900000
    fake_record = replace(owner, object_id=fake_id)
    fake_feature = copy.deepcopy(next(f for f in features if f['object_id'] == 285))
    fake_feature['object_id'] = fake_id
    reject('Valid first Ruled owner then invalid second owner remains handled',
        altered_records=records+[fake_record], altered_features=features+[fake_feature], expected_successes=1)
    # Direction's repeated last dependency must be checked against F2.ref103,
    # rather than being copied into its own expected dependency list.
    direction_archive = FILES[2]
    d, rs, fs, m, ms = loaded[direction_archive]
    s = before[direction_archive]['streams'][0]
    rec = next(r for r in rs if r.is_primary and r.object_id == 285)
    p = d[rec.body:rec.end]; _, position = read_string(p, 99)
    count = struct.unpack_from('<I', p, position+3)[0]
    changed = bytearray(d); offset = rec.body+position+7+11*(count-1)+1
    changed[offset:offset+8] = struct.pack('<Q', 295)
    altered_members = dict(ms); altered_members[m] = bytes(changed)
    rejected = decode_ruled_edge_sources(bytes(changed), rs, fs, m, altered_members,
        s['body_asm_identifiers'], s['body_selections'])
    assert not rejected['associations'] and rejected['unresolved']
    report['malformed_guards'].append(dict(label='Direction repeated descriptor differs from independent F2 reference',
        successful_owner_ids=[], diagnostics=rejected['unresolved']))
    report['summary'] = dict(focused_archives=8, admitted_Ruled_owners=4,
        distinct_native_selector_routes=8, cached_source_edges=4, complete_recipe_replays=8,
        named_endpoint_intersections=8, prior_tool_settings_exact=4, prior_incidence_summaries_exact=8,
        empty_controls=4, malformed_guards=len(report['malformed_guards']),
        independent_API_geometry_corroboration_available=False, main_runs=0, live_calls=0)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--zstd-library', required=True)
    parser.add_argument('--baseline-cache', type=Path, default=Path('/private/tmp/fusion-ruled-edge-baseline.json'))
    parser.add_argument('--output', type=Path, default=ROOT/'ruled-edge-source-decoding.json')
    args = parser.parse_args()
    report = validate(args.root.resolve(), args.zstd_library, args.baseline_cache)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps(report['summary']))
