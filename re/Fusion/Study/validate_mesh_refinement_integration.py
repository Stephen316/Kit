"""Pinned 28-file cached integration of mesh refinements; no main fallback."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from decode_base_feature_empty_lists import decode_base_feature_empty_lists
from decode_mesh_combine import decode_mesh_combine
from decode_mesh_geometry_variants import decode_mesh_contents_variants
from decode_mesh_normals import decode_mesh_normal_pools
from decode_mesh_reverse_normals import decode_mesh_reverse_normals
from decode_mesh_smooth import decode_mesh_smooth
from fusion_archive import read_members
from fusion_metadata import design_records
from validate_history_cache_integration import differences

ROOT = Path(__file__).resolve().parent
BASELINE = '2fed87f'
FILES = (
    'meshcontrasts-10c2557c91a3/stl_centimeter.f3d',
    'meshcontrasts-10c2557c91a3/stl_millimeter.f3d',
    'meshcontrasts-10c2557c91a3/triangle_data_centimeter.f3d',
    'meshplanecuts-18f2683c83f5/split_body_minimal_fill.f3d',
    'meshplanecuts-18f2683c83f5/trim_minimal_fill.f3d',
    'meshplanecuts-18f2683c83f5/trim_no_fill.f3d',
    'meshreduces-780954a23308/adaptive_count_six.f3d',
    'meshreduces-780954a23308/adaptive_proportion_fifty.f3d',
    'meshreduces-780954a23308/uniform_count_six.f3d',
    'meshreduces-8f01528f7f21/adaptive_proportion_fifty.f3d',
    'meshconverts-4b42d39fb1d5/faceted_closed.f3d',
    'meshconverts-4b42d39fb1d5/faceted_open.f3d',
    'meshconverts-4b42d39fb1d5/prismatic_closed.f3d',
    'meshremeshes-f07f97514069/adaptive_edge_one_point_five.f3d',
    'meshremeshes-f07f97514069/adaptive_edge_two.f3d',
    'meshremeshes-f07f97514069/uniform_edge_two.f3d',
    'meshcombines-541ebb6cc93f/cut.f3d',
    'meshcombines-541ebb6cc93f/intersect.f3d',
    'meshcombines-541ebb6cc93f/join.f3d',
    'splinepatches-ac5e846e59c0/splinepatches.f3d',
    'splinepatches-900d152c2380/splinepatches.f3d',
    'assembly-acc48a9dc05d/assembly.f3d',
    'meshreversenormals-2bc2dd3780cc/closed_once.f3d',
    'meshreversenormals-2bc2dd3780cc/closed_twice.f3d',
    'meshreversenormals-2bc2dd3780cc/open_once.f3d',
    'meshsmooths-56f38f13430a/smooth_default_point_zero_two.f3d',
    'meshsmooths-56f38f13430a/smooth_point_one.f3d',
    'meshsmooths-56f38f13430a/smooth_point_two_five.f3d',
)
CUT = FILES[16]
REVERSE_ONCE = FILES[22]
VARIANT_NORMAL_FILES = set(FILES[13:16]+FILES[17:19])
WHOLE_CONTROLS = set(FILES[:22])-VARIANT_NORMAL_FILES-{CUT}
BASE_MESH = '99F6967E-ED35-4222-B906-5CCF0AC70B53'
MESH_LEVEL = ('Observed component mesh ownership, native asset links and captured geometry buffers; '
              'general mesh formats, lifecycle and regeneration unresolved')
SPECS = (
    ('mesh_reverse_normals', 'mesh-reverse-normal-decoding.json', decode_mesh_reverse_normals,
        'MeshReverseNormal', '4AB7A6BD-C40C-4C44-B7CA-0D415B6E4412', 'class_decoded_mesh_reverse_normal_count',
        'Observed MeshReverseNormal selected mesh and stored asset links; general lifecycle and regeneration unresolved'),
    ('mesh_smooths', 'mesh-smooth-decoding.json', decode_mesh_smooth,
        'MeshSmooth', 'F84CD988-9696-458D-8AF3-795D12E6B9EF', 'class_decoded_mesh_smooth_count',
        'Observed MeshSmooth strength and owned parameter/mesh/asset routes; algorithm, lifecycle and regeneration unresolved'),
)
REPORT_NAMES = ('mesh-reverse-normal-decoding.json', 'mesh-smooth-decoding.json',
    'mesh-normal-variant-decoding.json', 'mesh-cut-index-stream-decoding.json',
    'mesh-combine-decoding.json', 'base-feature-empty-list-decoding.json')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def restore(actual, prior, keys):
    for key in keys:
        if key in prior:
            actual[key] = copy.deepcopy(prior[key])
        else:
            actual.pop(key, None)


def reports():
    values = {name: json.loads((ROOT/name).read_text()) for name in REPORT_NAMES}
    for name, value in values.items():
        assert len({s['archive'] for s in value['samples']}) == len(value['samples']), (name, 'Duplicate report archive')
    return values


def indexed(report):
    return {s['archive']: s for s in report['samples']}


def normal_golden(filename, evidence):
    variants = indexed(evidence['mesh-normal-variant-decoding.json'])
    if filename in variants:
        return variants[filename]['expected_decoded']
    for name in ('mesh-reverse-normal-decoding.json', 'mesh-smooth-decoding.json'):
        rows = indexed(evidence[name])
        if filename in rows:
            return rows[filename]['expected_normal_pools']
    cut = evidence['mesh-reverse-normal-decoding.json']['cut_normal_holdout']
    if filename == cut['archive']:
        return cut['expected_normal_pools']
    return None


def compare(before, current, filename, zstd, evidence=None):
    evidence = reports() if evidence is None else evidence
    after = copy.deepcopy(current)
    assert len(before['streams']) == len(after['streams'])
    members = read_members(ROOT/filename, zstd)
    counts = dict(new_normal_pools=0, recovered_normal_layout_errors=0,
        new_current_mesh_rows=0, new_BaseMesh_features=0, recovered_strict_mesh_errors=0,
        MeshReverseNormal=0, MeshSmooth=0, new_operation_tool_entries=0,
        refined_existing_CombineCut=0, unchanged_partial_BaseFeature_definitions=0)
    for prior, stream in zip(before['streams'], after['streams']):
        assert stream['member'] == prior['member']
        member = stream['member']
        data = members[member]
        records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
        features = {f['object_id']: f for f in stream['features']}
        old_features = {f['object_id']: f for f in prior['features']}
        assert set(features) == set(old_features), (filename, 'Native feature IDs changed')
        # This generic partial was already enabled at the pinned baseline,
        # including the six newly captured files. It must remain unchanged.
        partial = decode_base_feature_empty_lists(data, records, stream['features'])
        expected_partial = partial if partial['partial'] or partial['unresolved'] else None
        assert stream.get('base_feature_empty_lists') == prior.get('base_feature_empty_lists') == expected_partial
        for row in partial['partial']:
            identity = row['feature_object_id']
            assert features[identity]['base_feature_empty_list_definition'] == old_features[identity]['base_feature_empty_list_definition'] == row
            assert features[identity]['kind'] == old_features[identity]['kind'] == 'UnsupportedFeature'
            counts['unchanged_partial_BaseFeature_definitions'] += 1
        mesh = decode_mesh_contents_variants(data, records, member, members)
        assert stream.get('mesh_contents') == (mesh if mesh['decoded'] or mesh['unresolved'] else None)
        old_mesh = prior.get('mesh_contents', {'decoded': [], 'unresolved': []})
        by_mesh = {r['mesh_object_id']: r for r in mesh['decoded']}
        old_meshes = {r['mesh_object_id']: r for r in old_mesh['decoded']}
        assert len(by_mesh) == len(mesh['decoded']) and len(old_meshes) == len(old_mesh['decoded'])
        for identity, row in old_meshes.items():
            assert by_mesh[identity] == row, (filename, 'Prior complete mesh row changed')
        new_mesh_ids = set(by_mesh)-set(old_meshes)
        removed_mesh_errors = []
        if filename in (CUT, REVERSE_ONCE):
            assert new_mesh_ids == {213}
            golden = (indexed(evidence['mesh-cut-index-stream-decoding.json'])[filename]
                if filename == CUT else indexed(evidence['mesh-reverse-normal-decoding.json'])[filename])
            assert mesh == golden['expected_mesh_contents'], (filename, 'Recovered full mesh golden differs')
            reason = 'Mesh LZMA decoded extent/end-marker disagrees' if filename == CUT else 'Invalid mesh asset header scalar'
            removed_mesh_errors = [e for e in old_mesh['unresolved'] if e['mesh_object_id'] == 213 and e['reason'] == reason]
            assert len(removed_mesh_errors) == 1
            assert mesh['unresolved'] == [e for e in old_mesh['unresolved'] if e not in removed_mesh_errors]
        else:
            assert not new_mesh_ids and stream.get('mesh_contents') == prior.get('mesh_contents'), (filename, 'Unqualified mesh change')
        counts['new_current_mesh_rows'] += len(new_mesh_ids)
        counts['recovered_strict_mesh_errors'] += len(removed_mesh_errors)
        # Direction pools are independently qualified; complete old dictionaries
        # and all unrelated diagnostics remain exact.
        normal = decode_mesh_normal_pools(mesh)
        actual_normal = normal if normal['decoded'] or normal['unresolved'] else None
        assert stream.get('mesh_normal_pools') == actual_normal
        golden_normal = normal_golden(filename, evidence)
        if golden_normal is not None:
            assert normal == golden_normal, (filename, 'Normal pool golden differs')
        else:
            assert stream.get('mesh_normal_pools') == prior.get('mesh_normal_pools')
        old_normal = prior.get('mesh_normal_pools', {'decoded': [], 'unresolved': []})
        current_pools = {r['mesh_object_id']: r for r in normal['decoded']}
        old_pools = {r['mesh_object_id']: r for r in old_normal['decoded']}
        for identity, value in old_pools.items():
            assert current_pools[identity] == value, (filename, 'Prior normal dictionary changed')
        added_pools = set(current_pools)-set(old_pools)
        removed_normal_errors = [e for e in old_normal['unresolved'] if e['mesh_object_id'] in added_pools
            and e['reason'] == 'Normal pool count outside captured mesh layouts']
        assert normal['unresolved'] == [e for e in old_normal['unresolved'] if e not in removed_normal_errors]
        if added_pools:
            assert filename in VARIANT_NORMAL_FILES | {CUT, REVERSE_ONCE} and added_pools == {213}
        counts['new_normal_pools'] += len(added_pools)
        counts['recovered_normal_layout_errors'] += len(removed_normal_errors)
        restore(stream, prior, ('mesh_normal_pools',))
        # Only the existing Cut operation changes settings. Restore only its
        # three geometry-qualified children after full helper/report equality.
        if filename == CUT:
            cut = indexed(evidence['mesh-cut-index-stream-decoding.json'])[filename]
            combine = decode_mesh_combine(data, records, stream['features'], member, members, mesh)
            assert stream['mesh_combinations'] == combine == cut['expected_combine_summary']
            original_combine = prior['mesh_combinations']
            assert original_combine == indexed(evidence['mesh-combine-decoding.json'])[filename]['expected_decoded']
            actual_row, = combine['decoded']
            old_row, = original_combine['decoded']
            identity = actual_row['feature_object_id']
            assert identity == old_row['feature_object_id'] and actual_row['kind'] == old_row['kind'] == 'MeshCombine'
            current_settings = actual_row['settings']
            old_settings = old_row['settings']
            restored_settings = copy.deepcopy(current_settings)
            restore(restored_settings, old_settings, ('current_target_asset_geometry', 'geometry_unresolved', 'strict_current_mesh_diagnostics'))
            assert restored_settings == old_settings, 'Cut operation changed fields outside geometry/error refinement'
            assert old_settings['current_target_asset_geometry'] is None and current_settings['current_target_asset_geometry'] is not None
            assert len(old_settings['geometry_unresolved']) == 1 and not current_settings['geometry_unresolved']
            old_error, = old_settings['geometry_unresolved']
            assert old_error['asset_object_id'] == by_mesh[213]['asset_object_id'] and old_error['reason'] == 'Mesh LZMA decoded extent/end-marker disagrees'
            assert current_settings['strict_current_mesh_diagnostics'] == mesh['unresolved']
            assert features[identity]['tool_settings'] == current_settings and old_features[identity]['tool_settings'] == old_settings
            assert features[identity]['kind'] == old_features[identity]['kind'] == 'MeshCombine'
            assert features[identity]['decode_level'] == old_features[identity]['decode_level']
            restore(features[identity], old_features[identity], ('tool_settings',))
            restore(stream, prior, ('mesh_combinations',))
            counts['refined_existing_CombineCut'] += 1
        discovery = stream['feature_discovery']
        old_discovery = prior['feature_discovery']
        recovered, kinds, base_ids = set(), {}, set()
        for row in mesh['decoded']:
            identity = row['feature_object_id']
            if identity is None or identity not in features or features[identity]['class_guid'] != BASE_MESH:
                continue
            feature = features[identity]
            assert feature['kind'] == 'BaseMeshFeature' and feature['decode_level'] == MESH_LEVEL
            assert feature['mesh_contents'] == row and row['native_feature_class_guid'] == BASE_MESH
            base_ids.add(identity)
            if old_features[identity]['kind'] != 'BaseMeshFeature':
                assert old_features[identity]['kind'] == 'UnsupportedFeature' and row['mesh_object_id'] in new_mesh_ids
                recovered.add(identity)
                kinds[identity] = 'BaseMeshFeature'
                counts['new_BaseMesh_features'] += 1
            restore(feature, old_features[identity], ('kind', 'decode_level', 'mesh_contents'))
        if base_ids:
            assert discovery['class_decoded_mesh_base_feature_count'] == len(base_ids)
            restore(discovery, old_discovery, ('class_decoded_mesh_base_feature_count',))
        for key, report_name, decoder, kind, guid, counter, level in SPECS:
            summary = decoder(data, records, stream['features'], member, members, mesh)
            expected = summary if summary['decoded'] or summary['unresolved'] else None
            assert stream.get(key) == expected
            golden = indexed(evidence[report_name]).get(filename)
            if golden is None:
                assert expected is None and key not in prior
                continue
            assert summary == golden['expected_decoded'] and mesh == golden['expected_mesh_contents']
            assert normal == golden['expected_normal_pools']
            assert key not in prior
            for row in summary['decoded']:
                identity = row['feature_object_id']
                feature = features[identity]
                assert feature['class_guid'] == guid and row['kind'] == feature['kind'] == kind
                assert old_features[identity]['kind'] == 'UnsupportedFeature'
                assert feature['name'] == old_features[identity]['name'] == row['name']
                assert feature['tool_settings'] == row['settings'] and feature['decode_level'] == level
                restore(feature, old_features[identity], ('kind', 'tool_settings', 'decode_level'))
                entry = {'object_id': identity, 'kind': kind}
                assert entry not in prior['tool_decoding']['decoded']
                assert stream['tool_decoding']['decoded'].count(entry) == 1
                stream['tool_decoding']['decoded'].remove(entry)
                recovered.add(identity)
                kinds[identity] = kind
                counts[kind] += 1
                counts['new_operation_tool_entries'] += 1
            if summary['decoded'] or summary['unresolved']:
                assert discovery[counter] == len(summary['decoded'])
                restore(discovery, old_discovery, (counter,))
            restore(stream, prior, (key,))
        expected_unsupported = [r for r in old_discovery['unsupported_features'] if r['object_id'] not in recovered]
        assert discovery['unsupported_features'] == expected_unsupported
        assert discovery['unsupported_feature_count'] == len(expected_unsupported)
        assert {r['object_id'] for r in old_discovery['unsupported_features']} - {r['object_id'] for r in expected_unsupported} == recovered
        restore(discovery, old_discovery, ('unsupported_features', 'unsupported_feature_count'))
        assert stream['tool_decoding']['unresolved'] == prior['tool_decoding']['unresolved']
        def timeline(entry):
            identity = entry['object_id']
            if identity in recovered:
                assert entry['kind'] == kinds[identity]
                entry['kind'] = old_features[identity]['kind']
            for child in entry.get('children', []):
                timeline(child)
        for sequence in stream['timeline_decoding']['sequences']:
            for entry in sequence['visible_entries']:
                timeline(entry)
        restore(stream, prior, ('mesh_contents',))
    assert after == before, (filename, 'Unqualified prior-output difference', differences(before, after))
    return dict(archive=filename, archive_sha256=sha(ROOT/filename), **counts,
        all_other_prior_fields_exact=True, ASM_and_placement_exact=True,
        unrelated_warnings_exact=True, baseline_output_sha256=canonical(before), current_output_sha256=canonical(current),
        qualified_difference_paths=differences(before, current))


def cache_rows(path, side):
    value = json.loads(Path(path).read_text())
    if isinstance(value, list):
        return value
    assert value['baseline_commit'] == BASELINE and value['files'] == list(FILES)
    return value[side]


def manifest(outputs):
    assert len(outputs) == len(FILES) == 28
    for filename, output in zip(FILES, outputs):
        assert output['file'] == str(ROOT/filename)
        assert len({s['member'] for s in output['streams']}) == len(output['streams'])
        for stream in output['streams']:
            assert len({f['object_id'] for f in stream['features']}) == len(stream['features'])


def validate(zstd, baseline_path, current_path, manifest_path):
    assert json.loads(Path(manifest_path).read_text()) == list(FILES)
    before, current = cache_rows(baseline_path, 'before'), cache_rows(current_path, 'after')
    manifest(before)
    manifest(current)
    evidence = reports()
    rows = [compare(old, actual, name, zstd, evidence) for name, old, actual in zip(FILES, before, current)]
    totals = {k: sum(r[k] for r in rows) for k, v in rows[0].items() if type(v) is int}
    assert totals['MeshReverseNormal'] == 4 and totals['MeshSmooth'] == 3
    assert totals['new_operation_tool_entries'] == 7
    assert totals['new_current_mesh_rows'] == totals['new_BaseMesh_features'] == totals['recovered_strict_mesh_errors'] == 2
    assert totals['new_normal_pools'] == 7 and totals['recovered_normal_layout_errors'] == 5
    assert totals['refined_existing_CombineCut'] == 1
    assert totals['unchanged_partial_BaseFeature_definitions'] == 25
    assert len(WHOLE_CONTROLS) == 16
    assert all(old == actual for name, old, actual in zip(FILES, before, current) if name in WHOLE_CONTROLS)
    sources = ('decode_basics.py', 'decode_mesh_contents.py', 'decode_mesh_geometry_variants.py',
        'decode_mesh_normals.py', 'decode_mesh_smooth.py', 'decode_mesh_reverse_normals.py',
        'decode_mesh_combine.py', 'decode_retained_mesh_sources.py', 'decode_base_feature_empty_lists.py',
        'validate_mesh_refinement_integration.py')
    return dict(scope='28 pinned cached outputs against2fed87f; bounded mesh/control/normal refinements qualified before exact whole-output restoration',
        baseline_commit=BASELINE, files=list(FILES), samples=rows,
        inputs=dict(baseline_cache_sha256=sha(baseline_path), current_cache_sha256=sha(current_path),
            manifest_sha256=sha(manifest_path), baseline_output_set_sha256=canonical(before),
            current_output_set_sha256=canonical(current)),
        summary=dict(saved_files=28, legacy_whole_output_controls=16, **totals,
            unqualified_prior_output_changes=0, ASM_changes=0, stored_placement_changes=0,
            full_main_runs=0, live_API_calls=0),
        source_sha256={n: sha(ROOT/n) for n in sources}, focused_report_sha256={n: sha(ROOT/n) for n in REPORT_NAMES},
        limitations=['Cut declared-size index geometry retains the emitted surplus00 and unknown noEOF semantics; no general decompression relaxation.',
            'Negative native asset scalar remains literal and is not interpreted as a physical volume or flag.',
            'Direction pools remain unordered relative to corners/vertices; original PolygonMesh normal reconstruction is unclaimed.',
            'BaseFeature partials, retained inputs, stored asset temporal roles, current/final lifecycle and regeneration remain separately limited.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-outputs', type=Path, default=Path('/private/tmp/fusion-mesh-refinements-baseline.json'))
    parser.add_argument('--current-outputs', type=Path, required=True)
    parser.add_argument('--files', type=Path, default=Path('/private/tmp/fusion-mesh-refinements-files.json'))
    parser.add_argument('--zstd-library')
    parser.add_argument('--output', type=Path, default=ROOT/'mesh-refinement-integration.json')
    args = parser.parse_args()
    zstd = args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob('*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    report = validate(zstd, args.baseline_outputs, args.current_outputs, args.files)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], sort_keys=True))
