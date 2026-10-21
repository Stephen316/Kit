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
CONTROLS = ('advanced-627f7fe095f4/advanced.f3d', 'boundaryfills-a0953038318b/new_middle.f3d',
            'parameterexpressions-3ddbef2b20bd/product_sum.f3d', 'pipeedgecontrasts-5bd287323ae7/circle_full.f3d')


def read(name):
    return json.loads((ROOT/name).read_text())


def strip_additions(current, filename):
    """Validate bounded additions, returning an old-output view and counters.

    Also usable by earlier focused stage checks. This removes only the four
    named summaries and their exact corresponding feature attachments; source
    selection warnings, geometry, tool settings and all other fields survive.
    """
    face = {r['file']: r['expected_decoded'] for r in read('face-tracking-context-decoding.json')['samples']}
    vertex = {r['file']: r['expected_summary'] for r in read('named-vertex-selection-decoding.json')['cases']}
    boundary = {r['file']: r['expected_summary'] for r in read('boundary-modifying-face-decoding.json')['modifying_face_samples']}
    after = copy.deepcopy(current)
    counts = dict(native_registries=0, explicit_registry_diagnostics=0, FACE_tracking_contexts=0,
                  corroborated_FACE_attributes=0, modifying_FACE_correspondences=0,
                  direct_named_vertex_associations=0, incident_edge_associations=0)
    for stream in after['streams']:
        features = {r['object_id']: r for r in stream['features']}
        registry = stream.pop('native_naming_registry', None)
        if registry is not None:
            assert registry['decoded'] or registry['unresolved']
            for row in registry['decoded']:
                assert encode_native_naming_registry(row) == bytes.fromhex(row['payload_hex'])
                forward = {(k, r['native_owner_object_id']) for r in row['owner_to_keys'] for k in r['naming_keys']}
                reverse = {(r['naming_key'], r['native_owner_object_id']) for r in row['key_to_owner']}
                assert forward == reverse and len(reverse) == len(row['key_to_owner'])
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
        current = [json.loads(json.dumps(decode_basics(ROOT/f, zstd))) for f in files]
    else:
        assert saved_outputs['files'] == files
        before, current = saved_outputs['before'], saved_outputs['after']
    rows = []
    for filename, old, actual in zip(files, before, current):
        members = read_members(ROOT/filename, zstd)
        for stream in actual['streams']:
            data = members[stream['member']]
            records, _ = design_records(data, members[stream['member'].replace('BulkStream.dat', 'MetaStream.dat')])
            expected = decode_native_naming_registry(data, records)
            if expected['decoded'] or expected['unresolved']:
                assert stream['native_naming_registry'] == expected
                for registry in expected['decoded']:
                    assert bytes.fromhex(registry['payload_hex']) == data[registry['payload_offset']:registry['payload_offset']+registry['payload_byte_count']]
        rows.append(compare_outputs(old, actual, filename))
    totals = {key: sum(r[key] for r in rows) for key in rows[0] if isinstance(rows[0][key], int) and not isinstance(rows[0][key], bool)}
    assert totals['FACE_tracking_contexts'] == 15 and totals['corroborated_FACE_attributes'] == 78
    assert totals['modifying_FACE_correspondences'] == 16
    assert totals['direct_named_vertex_associations'] == 2 and totals['incident_edge_associations'] == 4
    return {'scope': 'Twenty-three saved main-reader designs against461010f, including two actual new vertex-selection exports; complete old-output comparison outside qualified new metadata',
            'baseline_commit': BASELINE, 'samples': rows,
            'summary': {'saved_files': len(files), **totals, 'prior_output_changes_outside_qualified_additions': 0,
                        'existing_ASM_output_changes': 0, 'old_selection_warnings_cleared': 0,
                        'new_live_API_calls_in_validator': 0},
            'limits': ['Naming tables establish literal key ownership in the observed schema;97 registry variants remain unresolved in the separate561-archive census.',
                'Tracked FACE body context is not selected-face or persistent identity.',
                'Direct vertex cache correspondence and modifying face naming groups are bounded branches, not whole recipe evaluation or lifecycle classification.',
                'Native writing, full translation and general feature regeneration remain unfinished.']}


if __name__ == '__main__':
    zstd = str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report = validate(zstd)
    (ROOT/'native-selection-integration.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], sort_keys=True))
