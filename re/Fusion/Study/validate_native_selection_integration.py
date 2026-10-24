"""Focused main-reader native naming and selection-context boundaries."""
from collections import defaultdict
import copy
import json
from pathlib import Path

from decode_basics import decode_basics
from decode_native_naming_registry import decode_native_naming_registry, encode_native_naming_registry
from fusion_archive import read_members
from fusion_metadata import design_records
from validate_history_cache_integration import baseline_outputs, differences

ROOT = Path(__file__).resolve().parent
BASELINE = '461010f'
STAGE = '1bdc9bc'
CONTROLS = ('advanced-627f7fe095f4/advanced.f3d', 'boundaryfills-a0953038318b/new_middle.f3d',
            'parameterexpressions-3ddbef2b20bd/product_sum.f3d', 'pipeedgecontrasts-5bd287323ae7/circle_full.f3d')


def read(name):
    return json.loads((ROOT/name).read_text())


def strip_additions(current, filename):
    """Validate bounded additions, returning an old-output view and counters.

    Also usable by earlier focused stage checks. A lazy later-stage helper first
    qualifies its three provenance summaries, then this removes the four native
    summaries and their exact corresponding feature attachments; source
    selection warnings, geometry, tool settings and all other fields survive.
    """
    face = {r['file']: r['expected_decoded'] for r in read('face-tracking-context-decoding.json')['samples']}
    vertex = {r['file']: r['expected_summary'] for r in read('named-vertex-selection-decoding.json')['cases']}
    boundary = {r['file']: r['expected_summary'] for r in read('boundary-modifying-face-decoding.json')['modifying_face_samples']}
    newer_keys = ('profile_cache_correspondences', 'component_display_colors', 'scope_update_times')
    if any(key in stream for stream in current['streams'] for key in newer_keys):
        from validate_registry_provenance_integration import strip_additions as strip_provenance
        after, provenance_counts = strip_provenance(current, filename)
    else:
        # Frozen historical outputs precede these summaries. They must not be
        # checked as if the absent current-stage additions were already present.
        after, provenance_counts = copy.deepcopy(current), {}
    counts = dict(native_registries=0, explicit_registry_diagnostics=0, FACE_tracking_contexts=0,
                  corroborated_FACE_attributes=0, modifying_FACE_correspondences=0,
                  direct_named_vertex_associations=0, incident_edge_associations=0,
                  reverse_only_native_registries=0, reverse_only_native_second_table_rows=0)
    counts.update({'registry_provenance_followup_'+key: value for key, value in provenance_counts.items()})
    for stream in after['streams']:
        features = {r['object_id']: r for r in stream['features']}
        registry = stream.pop('native_naming_registry', None)
        if registry is not None:
            assert registry['decoded'] or registry['unresolved']
            for row in registry['decoded']:
                assert encode_native_naming_registry(row) == bytes.fromhex(row['payload_hex'])
                forward = {(k, r['native_owner_object_id']) for r in row['owner_to_keys'] for k in r['naming_keys']}
                reverse = {(r['naming_key'], r['native_owner_object_id']) for r in row['key_to_owner']}
                assert len(reverse) == len(row['key_to_owner'])
                if row.get('table_layout') == 'StoredReverseOnly':
                    assert not row['owner_to_keys'] and row['key_to_owner']
                    assert row['reciprocity_status'] == 'ForwardTableAbsent' and row['registry_is_empty'] is False
                    assert len({r['naming_key'] for r in row['key_to_owner']}) == len(row['key_to_owner'])
                    assert all(1 <= r['naming_key'] <= 0x7fffffff and r['native_owner_class_guid'] for r in row['key_to_owner'])
                    counts['reverse_only_native_registries'] += 1
                    counts['reverse_only_native_second_table_rows'] += len(row['key_to_owner'])
                else:
                    assert forward == reverse

            counts['native_registries'] += len(registry['decoded'])
            counts['explicit_registry_diagnostics'] += len(registry['unresolved'])
        for key, expected, row_key, attachment, owner_key in (
                ('face_tracking_contexts', face, 'decoded', 'face_tracking_contexts', 'feature_object_id'),
                ('boundary_modifying_face_correspondences', boundary, 'decoded', 'boundary_modifying_face_correspondences', 'feature_object_id'),
                ('named_vertex_selections', vertex, 'associations', 'named_vertex_cache_correspondences', 'descriptor_owner_feature_object_id')):
            summary = stream.pop(key, None)
            if summary is None:
                continue
            if filename in expected:
                assert summary == expected[filename], (filename, key, 'Focused evidence mismatch')
            else:
                assert not summary[row_key] and summary['unresolved'], (filename, key, 'Unqualified positive association')
            grouped = defaultdict(list)
            for row in summary[row_key]: grouped[row[owner_key]].append(row)
            for identity, rows in grouped.items():
                actual = features[identity].pop(attachment)
                assert actual == (rows[0] if key == 'boundary_modifying_face_correspondences' else rows)
            if key == 'face_tracking_contexts':
                counts['FACE_tracking_contexts'] += len(summary['decoded'])
                for row in summary['decoded']:
                    assert row['exact_selected_source_FACE_identity'] is row['persistent_FACE_identity'] is row['qualified_historical_state'] is None
                    assert row['literal_is_serialized_native_reference'] is False
                    counts['corroborated_FACE_attributes'] += row['tracked_FACE_count']
            elif key == 'boundary_modifying_face_correspondences':
                counts['modifying_FACE_correspondences'] += sum(len(r['result_FACE_correspondences']) for r in summary['decoded'])
            else:
                counts['direct_named_vertex_associations'] += len(summary['associations'])
                counts['incident_edge_associations'] += sum(len(r['incident_edge_matches']) for r in summary['associations'])
    return after, counts


def compare_outputs(before, current, filename):
    after, counts = strip_additions(current, filename)
    assert after == before, (filename, 'Unexpected prior output change', differences(before, after))
    return {'file': filename, **counts, 'all_prior_output_unchanged': True,
            'ASM_geometry_and_existing_selection_warnings_unchanged': True,
            'qualified_difference_paths': differences(before, current)}


def validate(zstd, *, saved_outputs=None):
    face = read('face-tracking-context-decoding.json')['samples']
    vertex = read('named-vertex-selection-decoding.json')['cases']
    boundary = read('boundary-modifying-face-decoding.json')['modifying_face_samples']
    files = sorted({r['file'] for r in face+vertex+boundary} | set(CONTROLS))
    if saved_outputs is None:
        before = baseline_outputs(files, zstd, revision=BASELINE)
        stage = baseline_outputs(files, zstd, revision=STAGE)
        current = [json.loads(json.dumps(decode_basics(ROOT/f, zstd))) for f in files]
    else:
        assert saved_outputs['files'] == files
        before, current = saved_outputs['before'], saved_outputs['after']
        stage = saved_outputs.get('stage')
        if stage is None:
            stage = baseline_outputs(files, zstd, revision=STAGE)
    rows = []
    for filename, old, frozen in zip(files, before, stage):
        row = compare_outputs(old, frozen, filename)
        # Preserve the actual original stage facts rather than relabeling them
        # with newly recovered registry counts from the current reader.
        assert row.pop('reverse_only_native_registries') == 0
        assert row.pop('reverse_only_native_second_table_rows') == 0
        assert not any(key.startswith('registry_provenance_followup_') for key in row)
        rows.append(row)
    from validate_registry_provenance_integration import compare_outputs as compare_provenance
    followups = []
    for filename, old, frozen, actual in zip(files, before, stage, current):
        # This comparator independently re-reads the source registry and proves
        # all old paired dictionaries plus only the qualified new layout.
        followup = compare_provenance(frozen, actual, filename)
        followup['current_native_stage_comparison'] = compare_outputs(old, actual, filename)
        followups.append(followup)
    totals = {key: sum(r[key] for r in rows) for key in rows[0] if isinstance(rows[0][key], int) and not isinstance(rows[0][key], bool)}
    assert totals['FACE_tracking_contexts'] == 15 and totals['corroborated_FACE_attributes'] == 78
    assert totals['modifying_FACE_correspondences'] == 16
    assert totals['direct_named_vertex_associations'] == 2 and totals['incident_edge_associations'] == 4
    current_native_totals = {key: sum(row['current_native_stage_comparison'].get(key, 0) for row in followups)
                             for key, value in followups[0]['current_native_stage_comparison'].items()
                             if type(value) is int}
    provenance_totals = {key: sum(row.get(key, 0) for row in followups)
                         for key, value in followups[0].items() if type(value) is int}
    assert totals['native_registries'] == 22 and totals['explicit_registry_diagnostics'] == 1
    return {'scope': 'Twenty-three saved designs: frozen461010f to1bdc9bc native-selection stage plus separately qualified current registry/provenance followup; original historical counts remain unchanged',
            'baseline_commit': BASELINE, 'stage_commit': STAGE, 'samples': rows,
            'current_followup': {'baseline_commit': STAGE,
                'scope': 'Current reverse-only registry recovery and profile/color/scope additions compared separately to the frozen original native stage; nested current-native comparison also retains all pre-native output boundaries',
                'saved_files': len(followups), 'samples': followups,
                'summary': {'registry_provenance_stage': provenance_totals,
                            'current_native_stage_counts': current_native_totals,
                            'unexpected_prior_output_changes': 0}},
            'summary': {'saved_files': len(files), **totals, 'prior_output_changes_outside_qualified_additions': 0,
                        'existing_ASM_output_changes': 0, 'old_selection_warnings_cleared': 0,
                        'new_live_API_calls_in_validator': 0},
            'limits': ['The historical1bdc9bc snapshot retains its original22 decoded registries/one diagnostic in these23 files. New reverse-only layouts and provenance summaries are qualified only in the separately labeled current followup.',
                'Tracked FACE body context is not selected-face or persistent identity.',
                'Direct vertex cache correspondence and modifying face naming groups are bounded branches, not whole recipe evaluation or lifecycle classification.',
                'Native writing, full translation and general feature regeneration remain unfinished.']}


if __name__ == '__main__':
    zstd = str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report = validate(zstd)
    (ROOT/'native-selection-integration.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], sort_keys=True))
