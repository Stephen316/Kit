"""Strict saved-output integration for mesh operations and SplitFace metadata.

Only helper/report-qualified fields may be restored before exact comparison.
Supplied caches avoid rerunning the main decoder. The standalone fallback uses
the fixed sixteen-file manifest and pinned local baseline.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from decode_basics import decode_basics
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_mesh_plane_cuts import decode_mesh_plane_cuts
from decode_mesh_reduce import decode_mesh_reduce
from decode_split_face_metadata_variants import decode_split_face_metadata_variants
from fusion_archive import read_members
from fusion_metadata import design_records
from validate_history_cache_integration import baseline_outputs, differences

ROOT = Path(__file__).resolve().parent
BASELINE = 'e3b3c24'
FILES = (
    'meshplanecuts-18f2683c83f5/split_body_minimal_fill.f3d',
    'meshplanecuts-18f2683c83f5/trim_minimal_fill.f3d',
    'meshplanecuts-18f2683c83f5/trim_no_fill.f3d',
    'meshreduces-780954a23308/adaptive_count_six.f3d',
    'meshreduces-780954a23308/adaptive_proportion_fifty.f3d',
    'meshreduces-780954a23308/uniform_count_six.f3d',
    'meshreduces-8f01528f7f21/adaptive_proportion_fifty.f3d',
    'partinglinedrafts-c4d07c76fcd5/fixed_seven.f3d',
    'partinglinedrafts-c4d07c76fcd5/fixed_three.f3d',
    'partinglinedrafts-c4d07c76fcd5/moving_both_three.f3d',
    'meshcontrasts-10c2557c91a3/stl_centimeter.f3d',
    'meshcontrasts-10c2557c91a3/stl_millimeter.f3d',
    'meshcontrasts-10c2557c91a3/triangle_data_centimeter.f3d',
    'splitfacemodes-4fc4adf2a868/plane.f3d',
    'splitfacemodes-4fc4adf2a868/plane_extended.f3d',
    'assembly-acc48a9dc05d/assembly.f3d',
)
CONTROLS = FILES[10:]
FAILED_EXPRESSION = FILES[4]
SPLIT_ERROR = 'Unsupported SplitFace table metadata or kind label'
SPLIT_LEVEL = ('Observed SplitFace plane-intersection controls and owned target/tool references; '
               'table metadata meaning, exact faces and regeneration unresolved')
BASE_MESH = '99F6967E-ED35-4222-B906-5CCF0AC70B53'
BASE_FEATURE = 'D7015B81-AB4D-4C89-BED7-AA4411E1964A'
MESH_LEVEL = ('Observed component mesh ownership, native asset links and captured geometry buffers; '
              'general mesh formats, lifecycle and regeneration unresolved')
MESH_SPECS = (
    ('mesh_plane_cuts', 'mesh-plane-cut-decoding.json', decode_mesh_plane_cuts, 'MeshPlaneCut',
        'E3EB3760-4362-48D6-ABF3-698B0C12C5A9', 'class_decoded_mesh_plane_cut_count',
        'Observed MeshPlaneCut controls, selected plane and owned mesh/asset routes; flip encoding, historical lifecycle and regeneration unresolved'),
    ('mesh_reductions', 'mesh-reduce-decoding.json', decode_mesh_reduce, 'MeshReduce',
        'BE693D4C-741E-4794-A93E-5BFED71E9E13', 'class_decoded_mesh_reduce_count',
        'Observed MeshReduce method/target controls and owned parameter/mesh/asset routes; target attainment, historical lifecycle and regeneration unresolved'),
)


def read(name):
    return json.loads((ROOT/name).read_text())


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def restore_fields(actual, prior, keys):
    for key in keys:
        if key in prior:
            actual[key] = copy.deepcopy(prior[key])
        else:
            actual.pop(key, None)


def check_output_manifest(outputs):
    assert len(outputs) == len(FILES) == 16
    for filename, output in zip(FILES, outputs):
        assert output['file'] == str(ROOT/filename), (filename, 'Cache source path or output order differs')
        members = [s['member'] for s in output['streams']]
        assert len(members) == len(set(members)), (filename, 'Duplicate design stream')
        for stream in output['streams']:
            identities = [f['object_id'] for f in stream['features']]
            assert len(identities) == len(set(identities)), (filename, 'Duplicate feature object ID')


def mesh_goldens(report):
    rows = read(report)['samples']
    assert len({r['archive'] for r in rows}) == len(rows), (report, 'Duplicate report archive')
    return {r['archive']: r for r in rows}


def strip_mesh_operations(original, stream, data, records, member, members, filename):
    mesh = decode_mesh_contents_variants(data, records, member, members)
    assert stream.get('mesh_contents') == (mesh if mesh['decoded'] or mesh['unresolved'] else None)
    goldens = {}
    for spec in MESH_SPECS:
        for archive, row in mesh_goldens(spec[1]).items():
            assert archive not in goldens, (archive, 'Overlapping mesh report archives')
            goldens[archive] = row['expected_mesh_contents']
    if filename in goldens:
        assert mesh == goldens[filename], (filename, 'Mesh contents focused evidence differs')
    else:
        assert stream.get('mesh_contents') == original.get('mesh_contents'), (filename, 'Unqualified mesh summary change')
    # Older successes must remain dictionary-exact even when another mesh in
    # the same stream requires the opt-in variant. No geometry fields are stripped.
    meshes = {m['mesh_object_id']: m for m in mesh['decoded']}
    old_mesh = original.get('mesh_contents', {'decoded': []})
    for row in old_mesh['decoded']:
        assert meshes[row['mesh_object_id']] == row, (filename, 'Prior decoded mesh changed')
    features = {f['object_id']: f for f in stream['features']}
    prior = {f['object_id']: f for f in original['features']}
    assert set(features) == set(prior), (filename, 'Mesh feature discovery added/removed native identities')
    for identity, feature in features.items():
        if feature['class_guid'] == BASE_FEATURE:
            assert feature == prior[identity] and feature['kind'] == 'UnsupportedFeature', (filename, 'BaseFeature improperly promoted')
    base_ids = set()
    newly_decoded_base = set()
    for row in mesh['decoded']:
        identity = row['feature_object_id']
        if identity is None or identity not in features:
            continue
        feature = features[identity]
        if feature['class_guid'] != BASE_MESH:
            assert feature['kind'] != 'BaseMeshFeature' and 'mesh_contents' not in feature, (filename, 'Mesh operation promoted by geometry ownership alone')
            continue
        assert row['native_feature_class_guid'] == BASE_MESH
        assert feature['kind'] == 'BaseMeshFeature' and feature['decode_level'] == MESH_LEVEL
        assert feature['mesh_contents'] == row
        base_ids.add(identity)
        if prior[identity]['kind'] != 'BaseMeshFeature':
            assert prior[identity]['kind'] == 'UnsupportedFeature'
            newly_decoded_base.add(identity)
        restore_fields(feature, prior[identity], ('kind', 'decode_level', 'mesh_contents'))
    discovery = stream['feature_discovery']
    old_discovery = original['feature_discovery']
    if base_ids:
        assert discovery['class_decoded_mesh_base_feature_count'] == len(base_ids)
        restore_fields(discovery, old_discovery, ('class_decoded_mesh_base_feature_count',))
    else:
        assert discovery.get('class_decoded_mesh_base_feature_count') == old_discovery.get('class_decoded_mesh_base_feature_count')
    counts = {'mesh_plane_cut_features': 0, 'mesh_reduce_features': 0,
        'new_base_mesh_features': len(newly_decoded_base),
        'new_mesh_contents_rows': len(set(meshes)-{m['mesh_object_id'] for m in old_mesh['decoded']}),
        'mesh_operation_tool_additions': 0}
    operation_ids = set()
    kinds = {identity: 'BaseMeshFeature' for identity in base_ids}
    for key, report, decoder, kind, guid, counter, level in MESH_SPECS:
        summary = decoder(data, records, stream['features'], member, members, mesh)
        assert stream.pop(key, None) == (summary if summary['decoded'] or summary['unresolved'] else None)
        expected = mesh_goldens(report)
        if filename in expected:
            assert summary == expected[filename]['expected_decoded'], (filename, key, 'Operation focused evidence differs')
        else:
            assert not summary['decoded'] and not summary['unresolved'], (filename, key, 'Unqualified operation summary')
        ids = set()
        for row in summary['decoded']:
            identity = row['feature_object_id']
            feature = features[identity]
            assert row['kind'] == kind and feature['kind'] == kind and feature['class_guid'] == guid
            assert prior[identity]['kind'] == 'UnsupportedFeature'
            assert feature.get('name') == prior[identity].get('name') == row['name']
            assert feature['tool_settings'] == row['settings'] and feature['decode_level'] == level
            restore_fields(feature, prior[identity], ('kind', 'tool_settings', 'decode_level'))
            entry = {'object_id': identity, 'kind': kind}
            assert entry not in original['tool_decoding']['decoded']
            assert stream['tool_decoding']['decoded'].count(entry) == 1
            stream['tool_decoding']['decoded'].remove(entry)
            ids.add(identity)
            kinds[identity] = kind
            counts['mesh_operation_tool_additions'] += 1
        if summary['decoded'] or summary['unresolved']:
            assert discovery[counter] == len(ids)
            restore_fields(discovery, old_discovery, (counter,))
        else:
            assert discovery.get(counter) == old_discovery.get(counter)
        operation_ids.update(ids)
        counts['mesh_plane_cut_features' if kind == 'MeshPlaneCut' else 'mesh_reduce_features'] += len(ids)
    changed_ids = newly_decoded_base | operation_ids
    expected_unsupported = [r for r in old_discovery['unsupported_features'] if r['object_id'] not in changed_ids]
    assert discovery['unsupported_features'] == expected_unsupported
    assert discovery['unsupported_feature_count'] == len(expected_unsupported)
    if changed_ids:
        removed_ids = {r['object_id'] for r in old_discovery['unsupported_features']} - {r['object_id'] for r in expected_unsupported}
        assert removed_ids == changed_ids
    restore_fields(discovery, old_discovery, ('unsupported_features', 'unsupported_feature_count'))
    assert stream['tool_decoding']['unresolved'] == original['tool_decoding']['unresolved'], (filename, 'Mesh tool error changed')
    def restore_entry(entry):
        identity = entry['object_id']
        if identity in changed_ids:
            assert entry['kind'] == kinds[identity]
            entry['kind'] = prior[identity]['kind']
        for child in entry.get('children', []):
            restore_entry(child)
    for sequence in stream['timeline_decoding']['sequences']:
        for entry in sequence['visible_entries']:
            restore_entry(entry)
    restore_fields(stream, original, ('mesh_contents',))
    return counts


def strip_split_face(original, stream, data, records, filename):
    summary = decode_split_face_metadata_variants(data, records, stream['features'])
    assert stream.pop('split_face_metadata_variants', None) == (summary if summary['decoded'] or summary['unresolved'] else None)
    goldens = {s['archive']: s['expected_decoded'] for s in read('split-face-metadata-variant-decoding.json')['samples']}
    if filename in goldens:
        assert summary == goldens[filename], (filename, 'SplitFace focused evidence differs')
    else:
        assert not summary['decoded'], (filename, 'New positive SplitFace absent from focused report')
    features = {f['object_id']: f for f in stream['features']}
    prior = {f['object_id']: f for f in original['features']}
    recovered = set()
    for row in summary['decoded']:
        identity = row['feature_object_id']
        feature = features[identity]
        assert feature['kind'] == prior[identity]['kind'] == 'SplitFace'
        assert feature['tool_settings'] == row['settings']
        assert feature['decode_level'] == SPLIT_LEVEL
        assert feature.pop('split_face_table_metadata') == {k: row[k] for k in ('stored_table_metadata', 'table_metadata_layout')}
        restore_fields(feature, prior[identity], ('tool_settings', 'decode_level'))
        entry = {'object_id': identity, 'kind': 'SplitFace'}
        if entry not in original['tool_decoding']['decoded']:
            assert stream['tool_decoding']['decoded'].count(entry) == 1
            stream['tool_decoding']['decoded'].remove(entry)
            recovered.add(identity)
    old_errors = original['tool_decoding']['unresolved']
    removed = [e for e in old_errors if e['object_id'] in recovered and e['kind'] == 'SplitFace' and e['reason'] == SPLIT_ERROR]
    assert len(removed) == len(recovered)
    assert stream['tool_decoding']['unresolved'] == [e for e in old_errors if e not in removed]
    stream['tool_decoding']['unresolved'] = copy.deepcopy(old_errors)
    return {'split_face_metadata_records': len(summary['decoded']), 'recovered_split_face_tool_errors': len(removed)}


def compare(before, current, filename, zstd):
    after = copy.deepcopy(current)
    members = read_members(ROOT/filename, zstd)
    assert len(before['streams']) == len(after['streams'])
    if filename == FAILED_EXPRESSION:
        truth = read('meshreduces-780954a23308/ground_truth.json')
        negative, = [s for s in truth['samples'] if s['file'] == 'adaptive_proportion_fifty.f3d']
        assert negative['reduce_status'] == 'AttemptError'
        assert 'RuntimeError: 3 : invalid expression' in negative['reduce_error']['error']
        assert negative['feature_at_timeline_end'] is None
        assert negative['reduce_collection_count_before'] == negative['reduce_collection_count_after'] == 0
        assert not any(f.get('class_guid') == 'BE693D4C-741E-4794-A93E-5BFED71E9E13'
            or f['kind'] == 'MeshReduce' for s in current['streams'] for f in s['features'])
    counts = {'split_face_metadata_records': 0, 'recovered_split_face_tool_errors': 0,
        'mesh_plane_cut_features': 0, 'mesh_reduce_features': 0, 'new_base_mesh_features': 0,
        'new_mesh_contents_rows': 0, 'mesh_operation_tool_additions': 0}
    for original, stream in zip(before['streams'], after['streams']):
        assert stream['member'] == original['member']
        data = members[stream['member']]
        records, _ = design_records(data, members[stream['member'].replace('BulkStream.dat', 'MetaStream.dat')])
        for key, value in strip_split_face(original, stream, data, records, filename).items():
            counts[key] += value
        for key, value in strip_mesh_operations(original, stream, data, records, stream['member'], members, filename).items():
            counts[key] += value
    assert after == before, (filename, 'Unqualified prior-output change', differences(before, after))
    return {'archive': filename, **counts, 'all_other_prior_fields_exact': True,
        'ASM_geometry_and_stored_placement_labels_exact': True,
        'qualified_difference_paths': differences(before, current),
        'archive_sha256': sha256(ROOT/filename),
        'baseline_output_canonical_sha256': canonical_hash(before),
        'current_output_canonical_sha256': canonical_hash(current),
        'failed_expression_has_no_reduction_feature': filename == FAILED_EXPRESSION}


def validate(zstd, saved_outputs=None, *, baseline_cache=None, current_cache=None):
    if saved_outputs is not None:
        assert saved_outputs['baseline_commit'] == BASELINE and saved_outputs['files'] == list(FILES)
        before, current = saved_outputs['before'], saved_outputs['after']
    else:
        if baseline_cache is None:
            default = Path('/private/tmp/fusion-mesh-operations-baseline.json')
            baseline_cache = json.loads(default.read_text()) if default.exists() else None
        if baseline_cache is not None:
            assert baseline_cache['baseline_commit'] == BASELINE and baseline_cache['files'] == list(FILES)
            before = baseline_cache['before']
        else:
            before = baseline_outputs(list(FILES), zstd, revision=BASELINE)
        if current_cache is not None:
            assert current_cache['baseline_commit'] == BASELINE and current_cache['files'] == list(FILES)
            current = current_cache['after']
        else:
            current = [json.loads(json.dumps(decode_basics(ROOT/name, zstd))) for name in FILES]
    assert len(before) == len(current) == len(FILES) == 16
    check_output_manifest(before)
    check_output_manifest(current)
    rows = [compare(old, actual, name, zstd) for name, old, actual in zip(FILES, before, current)]
    totals = {k: sum(r[k] for r in rows) for k, v in rows[0].items() if type(v) is int}
    assert totals['split_face_metadata_records'] == totals['recovered_split_face_tool_errors'] == 3
    assert totals['mesh_plane_cut_features'] == totals['mesh_reduce_features'] == 3
    assert totals['mesh_operation_tool_additions'] == 6
    assert totals['new_base_mesh_features'] == 7 and totals['new_mesh_contents_rows'] == 8
    assert all(old == actual for name, old, actual in zip(FILES, before, current) if name in CONTROLS)
    return {'scope': 'Sixteen fixed saved files against frozen e3b3c24; exact output restoration after helper/report-qualified additions only',
        'baseline_commit': BASELINE, 'files': list(FILES), 'samples': rows,
        'inputs': {'current_cache_used': saved_outputs is not None or current_cache is not None,
            'baseline_output_set_canonical_sha256': canonical_hash(before),
            'current_output_set_canonical_sha256': canonical_hash(current),
            'ground_truth_sha256': {name: sha256(ROOT/name) for name in (
                'meshplanecuts-18f2683c83f5/ground_truth.json',
                'meshreduces-780954a23308/ground_truth.json',
                'meshreduces-8f01528f7f21/ground_truth.json',
                'partinglinedrafts-c4d07c76fcd5/ground_truth.json')}},
        'summary': {'saved_files': 16, 'legacy_full_output_controls': len(CONTROLS), **totals,
            'unqualified_prior_output_changes': 0, 'ASM_geometry_changes': 0, 'stored_placement_changes': 0,
            'live_API_calls': 0},
        'evidence_sha256': {name: sha256(ROOT/name) for name in (
            'decode_basics.py', 'decode_split_face.py', 'decode_split_face_metadata_variants.py',
            'split-face-metadata-variant-decoding.json', 'decode_mesh_contents.py',
            'decode_mesh_geometry_variants.py', 'decode_mesh_selections.py', 'decode_mesh_plane_cuts.py',
            'decode_mesh_reduce.py', 'mesh-plane-cut-decoding.json', 'mesh-reduce-decoding.json',
            'validate_mesh_operation_integration.py')},
        'limitations': ['SplitFace metadata8/12 remains uninterpreted and selected/result face topology remains unresolved.',
            'Stored mesh caches and provenance do not establish exact mesh regeneration, current/final body lifecycle or universal topology identity.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saved-outputs', type=Path)
    parser.add_argument('--baseline-outputs', type=Path)
    parser.add_argument('--current-outputs', type=Path)
    parser.add_argument('--zstd-library')
    parser.add_argument('--output', type=Path, default=ROOT/'mesh-operation-integration.json')
    args = parser.parse_args()
    zstd = args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result = validate(zstd, json.loads(args.saved_outputs.read_text()) if args.saved_outputs else None,
        baseline_cache=json.loads(args.baseline_outputs.read_text()) if args.baseline_outputs else None,
        current_cache=json.loads(args.current_outputs.read_text()) if args.current_outputs else None)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['summary'], sort_keys=True))
