"""Focused main-reader boundaries for datum, pattern and BODY tracking evidence."""

import copy
import json
from pathlib import Path
import subprocess

from decode_basics import decode_basics
from validate_history_cache_integration import baseline_outputs, differences

ROOT = Path(__file__).resolve().parent
BASELINE = 'eeb5363'
STAGE = '3910bdc'
CONTROLS = ('parameterexpressions-3ddbef2b20bd/product_sum.f3d',
            'edgemodes-52695761f185/fillet_curvature.f3d',
            'mirrorfeatures-1ffa1b15c612/feature_optimized.f3d')


def read(name):
    """Pin original evidence to the commit whose integration facts it proves."""
    return json.loads(subprocess.check_output(['git','show',STAGE+':'+name],cwd=ROOT))


def validate(zstd):
    circular = read('circular-placement-evidence-decoding.json')
    mirror = read('mirror-datum-reflection-decoding.json')
    fpm = read('fpm-partial-coverage-decoding.json')
    circular_cases = {row['file']: row for row in circular['cases']}
    circular_unsupported = {row['file']: row for row in circular['unsupported_controls']}
    mirror_cases = {row['file']: row for row in mirror['samples']}
    fpm_cases = {row['file']: row for row in fpm['samples'] if row['expected_summary']['associations']}
    files = sorted(set(circular_cases) | set(circular_unsupported) | set(mirror_cases) | set(fpm_cases) | set(CONTROLS))
    baseline = baseline_outputs(files, zstd, revision=BASELINE)
    stage_outputs = baseline_outputs(files, zstd, revision=STAGE)
    rows, measured_bodies, measured_vertices, reflections, tracked, covered_mapping_errors = [], 0, 0, 0, 0, 0
    for filename, before, stage_output in zip(files, baseline, stage_outputs):
        after = copy.deepcopy(stage_output)
        assert after['asm_decoding'] == before['asm_decoding'], filename
        original = copy.deepcopy(after)
        stream, = after['streams']; old_stream, = before['streams']
        features = {f['object_id']: f for f in stream['features']}
        old_features = {f['object_id']: f for f in old_stream['features']}
        changes = differences(before, original)
        if filename in circular_cases or filename in circular_unsupported:
            summary = stream.pop('circular_placement_evidence')
            if filename in circular_cases:
                assert summary == circular_cases[filename]['expected_summary'] and not summary['unresolved']
                for evidence in summary['decoded']:
                    feature = features[evidence['feature_object_id']]
                    assert feature.pop('circular_placement_evidence') == evidence
                    for group in evidence['element_cache_groups']:
                        measured_bodies += len(group['cache_bodies'])
                        measured_vertices += sum(b['measured_relative_rigid_fit']['matched_vertex_count'] for b in group['cache_bodies'])
            else:
                assert not summary['decoded'] and summary['unresolved'] == circular_unsupported[filename]['unresolved']
            assert stream['pattern_placements'] == old_stream['pattern_placements']
            assert stream['pattern_placements']['unresolved'], 'Original API getter uncertainty must remain explicit'
        if filename in mirror_cases:
            summary = stream.pop('mirror_datum_reflections')
            assert summary == mirror_cases[filename]['expected_summary'] and not summary['unresolved']
            for evidence in summary['decoded']:
                identity = evidence['feature_object_id']; feature = features[identity]
                assert feature.pop('datum_reflection') == evidence
                assert feature['unresolved_inputs'] == evidence['unresolved_controls']
                assert evidence['is_combine'] is evidence['stitch_tolerance_cm'] is None
                assert 'tool_settings' not in feature
                feature['decode_level'] = old_features[identity]['decode_level']
                feature['unresolved_inputs'] = old_features[identity]['unresolved_inputs']
                old_errors = [e for e in old_stream['tool_decoding']['unresolved'] if e['object_id'] == identity]
                new_errors = [e for e in stream['tool_decoding']['unresolved'] if e['object_id'] == identity]
                old_error, = old_errors; new_error, = new_errors
                assert old_error['reason'] == 'Unsupported reference encoding'
                assert new_error['reason'] == 'Datum Mirror inputs/output and reflected cache decoded; combine/stitch control semantics and general regeneration remain unresolved'
                new_error['reason'] = old_error['reason']
                reflections += 1
        if filename in fpm_cases:
            summary = stream.pop('fpm_body_tracking')
            assert summary == fpm_cases[filename]['expected_summary'] and not summary['unresolved']
            assert len(summary['associations']) == 2
            for correspondence in summary['associations']:
                assert features[correspondence['feature_object_id']].pop('fpm_body_correspondences') == [correspondence]
                assert correspondence['exact_selected_source_identity'] is None
                assert correspondence['qualified_historical_state'] is None
                assert correspondence['literal_is_serialized_native_reference'] is False
                tracked += 1
            coverage, = summary['coverage']
            assert coverage['initial_BODY_naming_complete'] is True and coverage['global_generic_tag_coverage_complete'] is False
            assert len(coverage['remaining_other_kind_generic_tag_failures']) == 6
            old_tracking, tracking = old_stream['fpm_selection_tracking'], stream['fpm_selection_tracking']
            assert tracking['tracks'] == old_tracking['tracks'] == []
            assert not tracking['unresolved'] and len(old_tracking['unresolved']) == 1
            error, = old_tracking['unresolved']
            assert error['reason'] == 'Incomplete FPM attribute coverage prevents unique literal correspondence'
            assert error['mapping_record_object_id'] == coverage['mapping_record_object_id']
            successful = {r['FPM_attribute']['attribute_record_index'] for r in summary['associations']}
            assert successful == set(coverage['handled_initial_BODY_FPM_attribute_record_indices']) == {4, 6}
            tracking['unresolved'] = old_tracking['unresolved']
            covered_mapping_errors += 1
        assert after == before, (filename, 'Unexpected prior output change', differences(before, after))
        if filename in CONTROLS:
            assert original == before
        rows.append({'file': filename, 'all_ASM_output_unchanged': True,
                     'all_prior_output_unchanged_except_qualified_fields': True,
                     'whole_output_control': filename in CONTROLS, 'qualified_difference_paths': changes})
    assert (measured_bodies, measured_vertices, reflections, tracked, covered_mapping_errors) == (18, 144, 3, 2, 1)
    # The current comparator is deliberately lazy: the historical validator
    # remains tied to its original outputs and evidence, while later qualified
    # changes get a separate report rather than rewriting old facts.
    from validate_counted_name_integration import compare_outputs
    followups = []
    for filename, stage_output in zip(files, stage_outputs):
        current = json.loads(json.dumps(decode_basics(ROOT/filename, zstd)))
        followups.append(compare_outputs(stage_output, current, filename))
    return {'scope': 'Fourteen saved main-reader cases: frozen eeb5363 to 3910bdc feature-cache stage, with separately qualified current followup; no live Fusion access',
            'baseline_commit': BASELINE, 'stage_commit': STAGE, 'samples': rows,
            'current_followup': {'baseline_commit': STAGE,
                'scope': 'Current outputs compared separately against the frozen historical stage using the counted-name followup comparator; original fourteen-case facts remain unchanged',
                'saved_files': len(followups), 'samples': followups},
            'summary': {'saved_files': len(files), 'measured_pattern_body_caches': measured_bodies,
                        'typed_pattern_vertex_pairs': measured_vertices, 'datum_reflections': reflections,
                        'initial_BODY_FPM_correspondences': tracked, 'fully_accounted_BODY_only_edge_reader_mapping_errors': covered_mapping_errors,
                        'circular_getter_warnings_retained': len(circular_cases)+len(circular_unsupported),
                        'datum_control_warnings_retained': reflections, 'whole_output_controls_exact': len(CONTROLS),
                        'ASM_output_changes': 0, 'unexpected_prior_output_changes': 0, 'new_API_calls': 0},
            'limitations': ['Circular transforms are measured between explicitly joined cache BODYs, not read serialized matrices or repaired API getters.',
                           'Construction-plane datum reflection has bounded membership/frame evidence; unavailable controls and general replay stay unresolved.',
                           'BODY-kind FPM coverage does not resolve global FACE naming or assign exact historical source/lifecycle semantics.',
                           'Native expression operand/dependency records remain unproven; no text-derived graph is promoted.',
                           'Full translation, feature regeneration and native writing remain unfinished.']}


if __name__ == '__main__':
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    result = validate(str(zstd))
    (ROOT/'feature-cache-integration.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['summary'], sort_keys=True))
