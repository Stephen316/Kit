"""Focused main-reader boundaries for counted names and annotation caches."""
import copy
import json
from pathlib import Path

from decode_basics import decode_basics
from validate_history_cache_integration import baseline_outputs, differences

ROOT = Path(__file__).resolve().parent
BASELINE = '3910bdc'


def read(name):
    return json.loads((ROOT/name).read_text())


def compare_outputs(before, current, filename):
    """Qualify only additive caches and the independently replayed naming fix."""
    from validate_native_selection_integration import strip_additions
    after, native_followup = strip_additions(current, filename)
    native_paths = differences(after, current)
    raw_current_paths = differences(before, current)
    assert after['asm_decoding'] == before['asm_decoding'], (filename, 'Prior ASM geometry changed')
    boundary = {r['file']: r['expected_summary'] for r in read('boundary-face-correspondence-decoding.json')['samples']}
    dimension = {r['file']: r['expected_decoded'] for r in read('dimension-annotation-decoding.json')['samples']}
    paths = differences(before, after)
    measurements = faces = coverage_fixes = failures = 0
    for stream, old in zip(after['streams'], before['streams']):
        features = {f['object_id']: f for f in stream['features']}
        if 'dimension_measurement_caches' in stream:
            summary = stream.pop('dimension_measurement_caches')
            assert summary['decoded'] or summary['unresolved']
            if filename in dimension:
                assert summary == dimension[filename]
            expected = {r['object_id']: r for r in summary['decoded']}
            attached = {}
            for f in features.values():
                for d in f.get('dimensions', []):
                    if 'measurement_cache' in d:
                        attached[d['object_id']] = d.pop('measurement_cache')
            assert attached == expected
            measurements += len(expected)
            failures += len(summary['unresolved'])
        if 'boundary_face_correspondences' in stream:
            summary = stream.pop('boundary_face_correspondences')
            # Every BoundaryFill fixture currently in the corpus is a focused
            # supported or explicitly unsupported case in this evidence report.
            assert filename in boundary and summary == boundary[filename]
            for row in summary['decoded']:
                assert features[row['feature_object_id']].pop('boundary_face_correspondences') == row
                faces += len(row['result_FACE_correspondences'])
                for link in row['result_FACE_correspondences']:
                    assert link['exact_selected_source_identity'] is link['persistent_FACE_identity'] is None
            failures += len(summary['unresolved'])
        if stream.get('fpm_body_tracking') != old.get('fpm_body_tracking'):
            assert filename == 'boundaryfills-a0953038318b/new_middle_remove.f3d'
            summary = stream['fpm_body_tracking']
            expected = next(r['expected_summary'] for r in read('fpm-partial-coverage-decoding.json')['samples'] if r['file'] == filename)
            assert summary == expected
            previous = old['fpm_body_tracking']
            assert summary['associations'] == previous['associations']
            assert len(summary['coverage']) == len(previous['coverage']) == 1
            coverage, = summary['coverage']; old_coverage, = previous['coverage']
            assert coverage['global_generic_tag_coverage_complete'] is True
            assert old_coverage['global_generic_tag_coverage_complete'] is False
            assert not coverage['remaining_other_kind_generic_tag_failures']
            assert len(old_coverage['remaining_other_kind_generic_tag_failures']) == 6
            coverage['global_generic_tag_coverage_complete'] = False
            coverage['remaining_other_kind_generic_tag_failures'] = old_coverage['remaining_other_kind_generic_tag_failures']
            coverage_fixes += 1
    assert len(after['streams']) == len(before['streams'])
    assert after == before, (filename, 'Unexpected prior output changes', differences(before, after))
    return {'file': filename, 'measurement_caches': measurements, 'result_FACE_correspondences': faces,
            'complete_generic_naming_coverage_followups': coverage_fixes,
            'new_explicit_partial_cache_diagnostics': failures,
            'all_ASM_output_unchanged': True, 'all_other_prior_output_unchanged': True,
            'whole_output_control_exact': not paths, 'qualified_difference_paths': paths,
            'native_selection_followup': native_followup,
            'native_selection_qualified_difference_paths': native_paths,
            'whole_current_output_control_exact': not raw_current_paths}


def validate(zstd, *, saved_outputs=None):
    boundaries = read('boundary-face-correspondence-decoding.json')['samples']
    dimensions = read('dimension-annotation-decoding.json')['samples']
    representatives = read('counted-asm-name-decoding.json')['inventory_term_count_representatives']
    files = sorted({r['file'] for r in boundaries+dimensions+representatives})
    if saved_outputs is None:
        before = baseline_outputs(files, zstd, revision=BASELINE)
        after = [json.loads(json.dumps(decode_basics(ROOT/f, zstd))) for f in files]
    else:
        assert saved_outputs['files'] == files
        before, after = saved_outputs['before'], saved_outputs['after']
    rows = [compare_outputs(a, b, f) for f, a, b in zip(files, before, after)]
    assert sum(r['measurement_caches'] for r in rows) == 10
    assert sum(r['result_FACE_correspondences'] for r in rows) == 35
    assert sum(r['complete_generic_naming_coverage_followups'] for r in rows) == 1
    return {'scope': 'Focused saved main-reader cases against local3910bdc; actual whole-output equality outside qualified additive caches and complete naming coverage',
            'baseline_commit': BASELINE, 'samples': rows,
            'summary': {'saved_files': len(files), 'dimension_measurement_caches': 10,
                        'BoundaryFill_result_FACE_correspondences': 35,
                        'complete_global_generic_naming_followups': 1,
                        'explicit_unsupported_BoundaryFill_controls': 3,
                        'whole_output_controls_exact': sum(r['whole_output_control_exact'] for r in rows),
                        'ASM_output_changes': 0, 'unexpected_prior_output_changes': 0, 'new_API_calls': 0},
            'limitations': ['Generic naming framing coverage is not complete feature or format support.',
                           'BoundaryFill face naming correspondence does not establish persistent FACE identity or general source selection.',
                           'Dimension annotation caches do not provide a solver; FDM literal fields do not establish native feature identity.',
                           'Native writing, full translation and general feature regeneration remain unfinished.']}


if __name__ == '__main__':
    zstd = str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result = validate(zstd)
    (ROOT/'counted-name-integration.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['summary'], sort_keys=True))
