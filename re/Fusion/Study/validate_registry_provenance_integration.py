"""Focused current-stage integration without a full corpus model rerun."""
import copy
import json
from pathlib import Path

from decode_basics import decode_basics
from decode_component_display_colors import decode_component_display_colors
from decode_native_naming_registry import decode_native_naming_registry, encode_native_naming_registry
from decode_profile_cache_correspondence import decode_profile_cache_correspondence
from decode_scope_update_times import decode_scope_update_times
from fusion_archive import read_members
from fusion_metadata import design_records
from validate_history_cache_integration import baseline_outputs, differences

ROOT = Path(__file__).resolve().parent
BASELINE = '1bdc9bc'


def evidence(name, key='expected_summary'):
    return {row['file']: row[key] for row in json.loads((ROOT/name).read_text())['samples']}


def strip_additions(current, filename):
    """Qualify only this stage's three additions, retaining all earlier output.

    Saved API/negative-control reports pin their captured positive cases.
    Other files must match the same bounded readers against source records.
    Naming-registry changes are deliberately retained for separate comparison.
    """
    expected = {
        'profile_cache_correspondences': evidence('profile-cache-correspondence-decoding.json'),
        'component_display_colors': evidence('component-display-color-decoding.json'),
        'scope_update_times': evidence('parameter-identity-contrast-decoding.json', 'expected_scope_update_times'),
    }
    after = copy.deepcopy(current)
    members = read_members(ROOT/filename, ZSTD())
    counts = dict(profile_BODY_groups=0, profile_native_curves=0, profile_COEDGE_candidates=0,
                  component_color_prefixes=0, component_color_diagnostics=0,
                  framed_scope_support_values=0, scope_support_diagnostics=0)
    for stream in after['streams']:
        member = stream['member']; data = members[member]
        records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
        features = {row['object_id']: row for row in stream['features']}
        derived = {
            'component_display_colors': decode_component_display_colors(data, records),
            'scope_update_times': decode_scope_update_times(data, records, stream['assembly_decoding']),
            'profile_cache_correspondences': decode_profile_cache_correspondence(
                data, records, stream['features'], member, members, stream['body_asm_identifiers']),
        }
        for key, summary in derived.items():
            actual = stream.pop(key, None)
            assert actual == (summary if summary['decoded'] or summary['unresolved'] else None), (filename, key)
            if filename in expected[key]:
                assert summary == expected[key][filename], (filename, key, 'Focused evidence changed')
            if key == 'profile_cache_correspondences':
                grouped = {}
                for row in summary['decoded']:
                    grouped.setdefault(row['source_feature_object_id'], []).append(row)
                    counts['profile_BODY_groups'] += 1
                    counts['profile_native_curves'] += len(row['source_curves'])
                    counts['profile_COEDGE_candidates'] += sum(len(curve['cached_coedge_candidates']) for curve in row['source_curves'])
                for identity, rows in grouped.items():
                    assert features[identity].pop(key) == rows
                assert not any(key in feature for feature in features.values())
            elif key == 'component_display_colors':
                counts['component_color_prefixes'] += len(summary['decoded'])
                counts['component_color_diagnostics'] += len(summary['unresolved'])
                for row in summary['decoded']:
                    raw = bytes.fromhex(row['framed_prefix_hex'])
                    assert raw == data[row['framed_prefix_offset']:row['framed_prefix_end_offset']]
                    assert len(bytes.fromhex(row['stored_rgb_float32_bytes_hex'])) == 12
                    assert not any(field in row for field in ('alpha', 'RGB8', 'color_space', 'material_appearance'))
            else:
                counts['framed_scope_support_values'] += len(summary['decoded'])
                counts['scope_support_diagnostics'] += len(summary['unresolved'])
                for row in summary['decoded']:
                    assert row['specific_lifecycle_event'] is row['native_clock_epoch_and_unit'] is None
    return after, counts


def compare_outputs(before, current, filename):
    after, counts = strip_additions(current, filename)
    members = read_members(ROOT/filename, ZSTD())
    recovered = keys = preserved = 0
    for old, actual in zip(before['streams'], after['streams']):
        member = actual['member']; data = members[member]
        records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
        registry = actual.get('native_naming_registry')
        expected = decode_native_naming_registry(data, records)
        assert registry == (expected if expected['decoded'] or expected['unresolved'] else None)
        if registry is None:
            assert 'native_naming_registry' not in old
            continue
        prior = old['native_naming_registry']
        paired = [row for row in registry['decoded'] if row.get('table_layout') != 'StoredReverseOnly']
        reverse = [row for row in registry['decoded'] if row.get('table_layout') == 'StoredReverseOnly']
        assert paired == prior['decoded'], (filename, 'Old registry dictionaries changed')
        prior_errors = {row['object_id']: row for row in prior['unresolved']}
        for row in registry['decoded']:
            assert encode_native_naming_registry(row) == data[row['payload_offset']:row['payload_offset']+row['payload_byte_count']]
        for row in reverse:
            assert row['object_id'] in prior_errors
            assert not row['owner_to_keys'] and row['key_to_owner']
            assert row['reciprocity_status'] == 'ForwardTableAbsent' and not row['registry_is_empty']
            keys += len(row['key_to_owner'])
        reverse_ids = {row['object_id'] for row in reverse}
        assert registry['unresolved'] == [row for row in prior['unresolved'] if row['object_id'] not in reverse_ids]
        if not reverse:
            assert registry == prior
        recovered += len(reverse); preserved += len(paired)
        actual['native_naming_registry'] = copy.deepcopy(prior)
    assert after == before, (filename, 'Unexpected prior-output change', differences(before, after))
    return dict(file=filename, **counts, recovered_reverse_only_registries=recovered,
                recovered_actual_second_table_rows=keys, prior_registry_dictionaries_exact=preserved,
                all_other_prior_output_unchanged=True, existing_ASM_geometry_and_selection_warnings_unchanged=True,
                qualified_difference_paths=differences(before, current))


def ZSTD():
    return str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))


def validate(zstd):
    profile = evidence('profile-cache-correspondence-decoding.json')
    colors = evidence('component-display-color-decoding.json')
    clocks = evidence('parameter-identity-contrast-decoding.json', 'expected_scope_update_times')
    files = sorted(set(profile) | set(colors) | set(clocks) | {
        'advanced-627f7fe095f4/advanced.f3d',
        'constructionmodes-e355ad6031c0/axis_edge.f3d',
        'dimcontrols-2a0d0bdbc8a6/angle_driving.f3d',
        'boundaryfills-a0953038318b/new_middle.f3d'})
    before = baseline_outputs(files, zstd, revision=BASELINE)
    current = [json.loads(json.dumps(decode_basics(ROOT/name, zstd))) for name in files]
    rows = [compare_outputs(old, actual, filename) for filename, old, actual in zip(files, before, current)]
    totals = {key: sum(row[key] for row in rows) for key in rows[0]
              if type(rows[0][key]) is int}
    assert totals['profile_BODY_groups'] >= 5 and totals['profile_COEDGE_candidates'] >= 16
    assert totals['recovered_reverse_only_registries'] >= 3
    assert totals['component_color_prefixes'] >= 9 and totals['framed_scope_support_values'] >= 4
    return dict(scope='Focused main-reader comparison with1bdc9bc; qualified reverse-only registries and profile/color/scope-support additions only',
        baseline_commit=BASELINE, samples=rows,
        summary=dict(saved_files=len(files), **totals, prior_output_changes_outside_qualified_changes=0,
                     existing_ASM_output_changes=0, existing_selection_warnings_cleared=0, live_API_calls=0),
        limitations=['Stored reverse-only associations never acquire a synthesized forward table.',
            'Profile provenance retains all qualified COEDGE candidates; geometry does not choose identity.',
            'Color values remain raw float32; no general RGB8, alpha, color-space or appearance conversion.',
            'Raw scope u64 time rendering is conditional; epoch/unit and specific lifecycle event remain unknown.',
            'Native writing, complete format coverage, three-way translation and regeneration remain unfinished.'])


if __name__ == '__main__':
    result = validate(ZSTD())
    (ROOT/'registry-provenance-integration.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['summary'], sort_keys=True))
