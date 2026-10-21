"""Focused intermediate-fillet, Circle-portion and AsBuilt integration checks."""
import argparse
import copy
import json
from pathlib import Path

from decode_basics import decode_basics
from decode_profile_circle_portions import decode_profile_circle_portions
from decode_asbuilt_joints import decode_asbuilt_joints
from decode_variable_fillets import decode_variable_fillets
from fusion_archive import read_members
from fusion_metadata import design_records
from validate_history_cache_integration import baseline_outputs, differences

ROOT = Path(__file__).resolve().parent
BASELINE = '8c9e3a9'
CONTROLS = ('assembly-acc48a9dc05d/assembly.f3d',
    'edgemodes-87edbf67527b/fillet_variable.f3d',
    'jointmodes-20d3aef2a07d/revolute.f3d',
    'thinextrudes-f758eff14202/open_line_side1.f3d')


def read(name):
    return json.loads((ROOT/name).read_text())


def strip_circle_additions(current, filename, zstd):
    """Qualify the new derived geometry without hiding membership changes.

    Older stage checks may use this for their preexisting unique-source cases.
    Added repeated-source membership is compared separately against its baseline.
    """
    expected = {row['file']: row['expected_summary']
                for row in read('profile-circle-portion-decoding.json')['samples']}
    after = copy.deepcopy(current)
    members = read_members(ROOT/filename, zstd)
    counts = dict(derived_circle_groups=0, derived_circle_portions=0,
                  corroborating_COEDGE_candidates=0, explicit_circle_diagnostics=0)
    for stream in after['streams']:
        member = stream['member']; data = members[member]
        records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
        summary = decode_profile_circle_portions(data, records, stream['features'], member,
                                                members, stream['body_asm_identifiers'])
        assert stream.pop('profile_circle_portions', None) == (summary if summary['decoded'] or summary['unresolved'] else None)
        if filename in expected:
            assert summary == expected[filename], (filename, 'Circle-portion focused evidence differs')
        features = {feature['object_id']: feature for feature in stream['features']}
        grouped = {}
        for row in summary['decoded']:
            grouped.setdefault(row['source_feature_object_id'], []).append(row)
            counts['derived_circle_groups'] += 1
            for portion in row['derived_source_portions']:
                assert portion['geometry_status'] == 'DerivedAnalyticSourceCirclePortion'
                assert portion['parameter_status'] == 'Derived reference-axis angles; not serialized trim parameters, API Arc parameters or decoded traversal direction'
                assert portion['all_full_tuple_cache_candidates_corroborate']
                counts['derived_circle_portions'] += 1
                counts['corroborating_COEDGE_candidates'] += len(portion['all_full_tuple_cache_candidates_corroborate'])
        for identity, rows in grouped.items():
            assert features[identity].pop('profile_circle_portions') == rows
        counts['explicit_circle_diagnostics'] += len(summary['unresolved'])
    return after, counts


def restore_fields(actual, original, keys):
    for key in keys:
        if key in original:
            actual[key] = copy.deepcopy(original[key])
        else:
            actual.pop(key, None)


def compare(before, current, filename, zstd):
    after, counts = strip_circle_additions(current, filename, zstd)
    counts.update(intermediate_fillets=0, active_midpoint_pairs=0, recovered_AsBuilt_features=0,
                  resolved_native_joint_diagnostics=0, recovered_repeated_source_memberships=0)
    members = read_members(ROOT/filename, zstd)
    goldens = {
        'variable_fillets': {row['file']: row['expected_summary'] for row in read('variable-fillet-decoding.json')['samples']},
        'as_built_joints': {row['file']: row['expected_decoded'] for row in read('asbuilt-joint-decoding.json')['samples']},
    }
    for original, actual, stream in zip(before['streams'], current['streams'], after['streams']):
        member = stream['member']; data = members[member]
        records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
        features = {feature['object_id']: feature for feature in stream['features']}
        old_features = {feature['object_id']: feature for feature in original['features']}
        summaries = {
            'variable_fillets': decode_variable_fillets(data, records, stream['features']),
            'as_built_joints': decode_asbuilt_joints(data, records, stream['assembly_decoding'], stream['features']),
        }
        for key, summary in summaries.items():
            assert stream.pop(key, None) == (summary if summary['decoded'] or summary['unresolved'] else None)
            if filename in goldens[key]:
                assert summary == goldens[key][filename], (filename, key, 'Focused evidence differs')
        fillet_ids = set()
        for row in summaries['variable_fillets']['decoded']:
            identity = row['feature_object_id']; feature = features[identity]
            assert feature['tool_settings'] == row['tool_settings']
            assert feature['decode_level'] == 'Observed intermediate variable-fillet controls and stored parameter order; exact selected edge and regeneration unresolved'
            assert feature['unresolved_inputs'] == ['Exact selected BRep edge identity/orientation and fillet regeneration']
            restore_fields(feature, old_features[identity], ('tool_settings', 'decode_level', 'unresolved_inputs'))
            stream['tool_decoding']['decoded'].remove(dict(object_id=identity, kind='Fillet'))
            fillet_ids.add(identity)
            counts['intermediate_fillets'] += 1
            counts['active_midpoint_pairs'] += sum(len(item.get('midRadii', [])) for item in row['tool_settings']['edge_sets'])
        old_errors = original['tool_decoding']['unresolved']
        removed = [item for item in old_errors if item['object_id'] in fillet_ids and item['reason'] == 'Unsupported fillet edge-set mode or layout']
        assert len(removed) == len(fillet_ids)
        assert stream['tool_decoding']['unresolved'] == [item for item in old_errors if item not in removed]
        stream['tool_decoding']['unresolved'] = copy.deepcopy(old_errors)

        recovered_membership = set()
        for row in actual.get('profile_circle_portions', {}).get('decoded', []):
            identity = row['source_feature_object_id']; descriptor = row['profile_descriptor_object_id']
            if any(selection['descriptor_object_id'] == descriptor for selection in old_features[identity].get('profile_selection', [])):
                continue
            feature = features[identity]
            selection, = [item for item in feature['profile_selection'] if item['descriptor_object_id'] == descriptor]
            assert selection == dict(sketch_object_id=row['native_sketch_object_id'], sketch_name=row['native_sketch_name'],
                descriptor_object_id=descriptor, loop_definition_object_id=row['profile_loop_definition_object_id'],
                loops=row['profile_loops'], selection_level='Observed Circle portion references with corroborated derived source geometry',
                limitations='Derived source angles are separate from serialized parameters; general trim reconstruction/traversal remain unresolved')
            feature['profile_selection'].remove(selection)
            if not feature['profile_selection']:
                feature.pop('profile_selection')
            stream['profile_decoding']['decoded'].remove(dict(feature_object_id=identity,
                descriptor_object_id=descriptor, loop_count=len(row['profile_loops']), reference_layout='ObservedCirclePortionSelectors'))
            recovered_membership.add(identity)
        old_errors = original['profile_decoding']['unresolved']
        removed = [item for item in old_errors if item['feature_object_id'] in recovered_membership
                   and item['reason'] == 'Unsupported profile curve or trim-reference layout']
        assert len(removed) == len(recovered_membership)
        assert stream['profile_decoding']['unresolved'] == [item for item in old_errors if item not in removed]
        stream['profile_decoding']['unresolved'] = copy.deepcopy(old_errors)
        counts['recovered_repeated_source_memberships'] += len(recovered_membership)

        asbuilt_ids = set(); native_ids = set()
        for row in summaries['as_built_joints']['decoded']:
            identity = row['feature_object_id']; feature = features[identity]; prior = old_features[identity]
            assert feature.pop('as_built_joint_settings') == row
            assert feature['kind'] == 'AsBuiltJoint' and feature['name'] == (prior.get('name') or row['name'])
            assert feature['decode_level'] == 'Observed AsBuilt occurrence associations, motion/limit bindings and stored context caches; no joint solve'
            assert row['is_suppressed'] is None
            restore_fields(feature, prior, ('kind', 'name', 'decode_level'))
            asbuilt_ids.add(identity); native_ids.add(row['object_id'])
            counts['recovered_AsBuilt_features'] += 1
        if summaries['as_built_joints']['decoded'] or summaries['as_built_joints']['unresolved']:
            discovery = stream['feature_discovery']; prior_discovery = original['feature_discovery']
            assert discovery.pop('class_decoded_as_built_joint_definition_count') == len(asbuilt_ids)
            assert discovery['unsupported_features'] == [item for item in prior_discovery['unsupported_features'] if item['object_id'] not in asbuilt_ids]
            assert discovery['unsupported_feature_count'] == len(discovery['unsupported_features'])
            restore_fields(discovery, prior_discovery, ('unsupported_features', 'unsupported_feature_count'))
        if native_ids:
            assert stream['joint_decoding'].pop('as_built_native_joint_object_ids') == sorted(native_ids)
        old_errors = original['joint_decoding']['unresolved']
        removed = [item for item in old_errors if item['object_id'] in native_ids and item['kind'] == 'NativeJoint'
                   and item['reason'] == 'Native joint not resolved through a supported Assemble definition']
        assert len(removed) == len(native_ids)
        assert stream['joint_decoding']['unresolved'] == [item for item in old_errors if item not in removed]
        stream['joint_decoding']['unresolved'] = copy.deepcopy(old_errors)
        counts['resolved_native_joint_diagnostics'] += len(removed)
        for sequence, prior_sequence in zip(stream['timeline_decoding']['sequences'], original['timeline_decoding']['sequences']):
            for entry, prior_entry in zip(sequence['visible_entries'], prior_sequence['visible_entries']):
                if entry['object_id'] in asbuilt_ids:
                    evidence = next(row for row in summaries['as_built_joints']['decoded'] if row['feature_object_id'] == entry['object_id'])
                    assert entry['kind'] == 'AsBuiltJoint' and entry['name'] == evidence['name']
                    restore_fields(entry, prior_entry, ('kind', 'name'))
    assert after == before, (filename, 'Unexpected prior-output change', differences(before, after))
    return dict(file=filename, **counts, all_other_prior_fields_exact=True,
        all_ASM_geometry_and_stored_placement_labels_exact=True,
        unrelated_selection_warnings_unchanged=True, qualified_difference_paths=differences(before, current))


def validate(zstd, *, saved_outputs=None):
    new_files = {row['file'] for name in ('variable-fillet-decoding.json', 'asbuilt-joint-decoding.json', 'profile-circle-portion-decoding.json')
                 for row in read(name)['samples']}
    files = sorted(new_files | set(CONTROLS) | {'trimmedprofiles-a804f8da1496/rectangle_overlap.f3d'})
    if saved_outputs is None:
        before = baseline_outputs(files, zstd, revision=BASELINE)
        current = [json.loads(json.dumps(decode_basics(ROOT/name, zstd))) for name in files]
    else:
        assert saved_outputs['baseline_commit'] == BASELINE and saved_outputs['files'] == files
        before, current = saved_outputs['before'], saved_outputs['after']
    assert len(before) == len(current) == len(files) == 18
    rows = [compare(old, actual, filename, zstd) for filename, old, actual in zip(files, before, current)]
    totals = {key: sum(row[key] for row in rows) for key, value in rows[0].items() if type(value) is int}
    assert totals['derived_circle_groups'] == 6 and totals['derived_circle_portions'] == 16
    assert totals['corroborating_COEDGE_candidates'] == 32 and totals['recovered_repeated_source_memberships'] == 2
    assert totals['intermediate_fillets'] == 3 and totals['active_midpoint_pairs'] == 4
    assert totals['recovered_AsBuilt_features'] == totals['resolved_native_joint_diagnostics'] == 3
    assert all(old == actual for name, old, actual in zip(files, before, current) if name in CONTROLS)
    from validate_modeling_extension_integration import compare as compare_earlier
    targets = [name for name in files if name.startswith('trimmedprofiles-a804f8da1496/')]
    assert len(targets) == 3
    cache = Path('/private/tmp/fusion-modeling-142a5ea-baseline.json')
    if cache.exists():
        prior = json.loads(cache.read_text()); lookup = dict(zip(prior['files'], prior['before']))
        assert prior['baseline_commit'] == '142a5ea'
    else:
        lookup = dict(zip(targets, baseline_outputs(targets, zstd, revision='142a5ea')))
    after_by_file = dict(zip(files, current))
    checked = [compare_earlier(lookup[name], after_by_file[name], name, zstd, {
        'thin_extrudes': {}, 'datum_mirror_supports': {}, 'trimmed_profiles': {
            row['file']: row['expected_summary'] for row in read('trimmed-profile-decoding.json')['samples']}}) for name in targets]
    earlier = dict(saved_files=len(checked), prior_stage_boundaries_preserved=True,
                   scope='Frozen142a5ea comparison for exactly the three affected old trim cases; reuse locally cached baseline when available, otherwise regenerate it; new Circle additions qualified separately')
    return dict(scope='Eleven actual new exports, two earlier Circle captures and five controls against8c9e3a9; native controls, derived source geometry and cached placement remain separately scoped',
        baseline_commit=BASELINE, samples=rows, earlier_modeling_stage_followup=earlier,
        summary=dict(saved_files=len(files), legacy_full_output_controls=len(CONTROLS), **totals,
                     unexpected_prior_output_changes=0, ASM_geometry_changes=0, solved_placement_claims=0, live_API_calls=0),
        limitations=['Intermediate fractions retain native/API list order; selected ASM edge direction and fillet interpolation remain unknown.',
            'Source Circle angles are derived in captured proper-intersection XY contexts, not serialized trim parameters or traversal.',
            'AsBuilt context/geometry matrices are unsolved caches; native suppression and arbitrary joint geometry remain unsupported.',
            'Full native writing, feature regeneration, general solving and complete translation remain unfinished.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saved-outputs', type=Path)
    parser.add_argument('--zstd-library')
    args = parser.parse_args()
    zstd = args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result = validate(zstd, saved_outputs=json.loads(args.saved_outputs.read_text()) if args.saved_outputs else None)
    (ROOT/'advanced-feature-integration.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['summary'], sort_keys=True))
