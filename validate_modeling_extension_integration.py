"""Focused Thin Extrude, trimmed-profile and custom datum-support integration."""
import argparse
import copy
import json
from pathlib import Path

from decode_basics import decode_basics
from decode_datum_mirror_supports import decode_datum_mirror_supports
from decode_thin_extrudes import decode_thin_extrudes
from decode_trimmed_profiles import decode_trimmed_profiles
from fusion_archive import read_members
from fusion_metadata import design_records
from validate_history_cache_integration import baseline_outputs, differences

ROOT = Path(__file__).resolve().parent
BASELINE = '142a5ea'
CONTROLS = ('profiles-66b0447c28ac/concentric_annulus.f3d',
    'sweepprofiles-8d489fe02d2d/open_brep_edge_surface.f3d',
    'mirrorassemblydatum-65c867cc41d9/plane_xy_positive_offset.f3d',
    'scaleshellinputs-97ef1cfd19e4/scale_vertex.f3d')


def read(name):
    return json.loads((ROOT/name).read_text())


def compare(before, current, filename, zstd, expected):
    after = copy.deepcopy(current)
    members = read_members(ROOT/filename, zstd)
    counts = dict(thin_features=0, active_wall_bindings=0, open_line_sources=0,
                  trimmed_profile_groups=0, trimmed_source_references=0,
                  retained_trim_COEDGE_candidates=0, custom_datum_supports=0,
                  qualified_old_profile_diagnostics_resolved=0)
    for original, stream in zip(before['streams'], after['streams']):
        member = stream['member']; data = members[member]
        records, _ = design_records(data, members[member.replace('BulkStream.dat', 'MetaStream.dat')])
        features = {feature['object_id']: feature for feature in stream['features']}
        old_features = {feature['object_id']: feature for feature in original['features']}
        summaries = {
            'thin_extrudes': decode_thin_extrudes(data, records, stream['features']),
            'datum_mirror_supports': decode_datum_mirror_supports(data, records, stream['features'], stream['assembly_decoding']),
            'trimmed_profiles': decode_trimmed_profiles(data, records, stream['features'], member, members, stream['body_asm_identifiers']),
        }
        resolved = set()
        for key, summary in summaries.items():
            actual = stream.pop(key, None)
            assert actual == (summary if summary['decoded'] or summary['unresolved'] else None), (filename, key)
            if filename in expected[key]:
                assert summary == expected[key][filename], (filename, key, 'Focused evidence differs')
        for row in summaries['thin_extrudes']['decoded']:
            identity = row['feature_object_id']; feature = features[identity]; prior = old_features[identity]
            assert feature.pop('is_thin_extrude') is True
            assert feature.pop('thin_extrusion') == row['thin_metadata']
            assert feature.pop('thin_extrusion_source') == {key: value for key, value in row.items()
                if key not in ('feature_object_id', 'is_thin_extrude', 'thin_metadata', 'common_extrusion_controls')}
            assert feature['decode_level'] == 'Observed Thin Extrude common/wall controls and owned sketch source; wall geometry and regeneration unresolved'
            if 'decode_level' in prior:
                feature['decode_level'] = prior['decode_level']
            else:
                feature.pop('decode_level')
            for key, value in row['common_extrusion_controls'].items():
                assert feature[key] == prior[key] == value, (filename, key, 'Common extrusion controls changed')
            counts['thin_features'] += 1
            counts['active_wall_bindings'] += 1+int(row['thin_metadata']['side_two']['applicable'])
            if row['profile'].get('profile_kind') == 'SketchOpenProfile':
                assert feature.pop('open_profile_selection') == row['profile']
                decoded_row = dict(feature_object_id=identity, kind='SketchOpenProfile',
                    descriptor_object_id=row['profile']['descriptor_object_id'], curve_count=1)
                stream['profile_decoding']['decoded'].remove(decoded_row)
                resolved.add((identity, 'Profile source reference is unresolved'))
                counts['open_line_sources'] += 1
        grouped = {}
        for row in summaries['trimmed_profiles']['decoded']:
            identity = row['source_feature_object_id']; feature = features[identity]
            grouped.setdefault(identity, []).append(row)
            descriptor_id = row['profile_descriptor_object_id']
            choices = [entry for entry in feature['profile_selection'] if entry['descriptor_object_id'] == descriptor_id]
            assert len(choices) == 1
            selection = choices[0]
            assert selection['sketch_object_id'] == row['native_sketch_object_id']
            assert selection['sketch_name'] == row['native_sketch_name']
            assert selection['loop_definition_object_id'] == row['profile_loop_definition_object_id']
            assert selection['loops'] == row['profile_loops']
            assert selection['selection_level'] == 'Observed curve membership and literal trim selectors with qualified cached boundaries'
            assert selection['limitations'] == 'Selector-to-parameter semantics and general source trim construction remain unresolved'
            feature['profile_selection'].remove(selection)
            if not feature['profile_selection']:
                feature.pop('profile_selection')
            stream['profile_decoding']['decoded'].remove(dict(feature_object_id=identity,
                descriptor_object_id=descriptor_id, loop_count=len(row['profile_loops']), reference_layout='ObservedTrimSelectors'))
            resolved.add((identity, 'Unsupported profile curve or trim-reference layout'))
            counts['trimmed_profile_groups'] += 1
            counts['trimmed_source_references'] += len(row['source_curves'])
            counts['retained_trim_COEDGE_candidates'] += sum(len(source['cached_coedge_candidates']) for source in row['source_curves'])
        for identity, rows in grouped.items():
            assert features[identity].pop('trimmed_profile_cache_correspondences') == rows
        for row in summaries['datum_mirror_supports']['decoded']:
            assert features[row['feature_object_id']].pop('datum_mirror_support_reflection') == row
            assert row['is_combine'] is row['stitch_tolerance_cm'] is None
            counts['custom_datum_supports'] += 1
        old_errors = original['profile_decoding']['unresolved']
        matched = [error for error in old_errors if (error['feature_object_id'], error['reason']) in resolved]
        assert len(matched) == len(resolved), (filename, 'Resolved diagnostic was absent/duplicated in old output')
        assert stream['profile_decoding']['unresolved'] == [error for error in old_errors
            if (error['feature_object_id'], error['reason']) not in resolved]
        counts['qualified_old_profile_diagnostics_resolved'] += len(matched)
        stream['profile_decoding']['unresolved'] = copy.deepcopy(old_errors)
    assert after == before, (filename, 'Unexpected prior-output change', differences(before, after))
    return dict(file=filename, **counts, all_other_prior_fields_exact=True,
        all_ASM_geometry_exact=True, existing_selection_and_origin_only_reader_warnings_unchanged=True,
        qualified_difference_paths=differences(before, current))


def validate(zstd, *, baseline_cache=None):
    thin = read('thin-extrude-decoding.json')
    mirror = read('datum-mirror-support-decoding.json')
    trimmed = read('trimmed-profile-decoding.json')
    expected = {
        'thin_extrudes': {row['file']: row['expected_summary'] for row in thin['samples']},
        'datum_mirror_supports': {row['file']: row['expected_decoded'] for row in mirror['samples']},
        'trimmed_profiles': {row['file']: row['expected_summary'] for row in trimmed['samples']},
    }
    files = sorted(set(CONTROLS) | {thin['ordinary_control']['file']}
                   | set().union(*(set(values) for values in expected.values())))
    if baseline_cache is None:
        before = baseline_outputs(files, zstd, revision=BASELINE)
    else:
        cached = json.loads(Path(baseline_cache).read_text())
        assert cached['baseline_commit'] == BASELINE and cached['files'] == files
        before = cached['before']
    assert len(before) == len(files) == 16
    current = [json.loads(json.dumps(decode_basics(ROOT/name, zstd))) for name in files]
    rows = [compare(old, actual, filename, zstd, expected) for filename, old, actual in zip(files, before, current)]
    totals = {key: sum(row[key] for row in rows) for key, value in rows[0].items() if type(value) is int}
    assert totals['thin_features'] == 6 and totals['active_wall_bindings'] == 8
    assert totals['open_line_sources'] == 1 and totals['custom_datum_supports'] == 2
    assert totals['trimmed_profile_groups'] == 3 and totals['trimmed_source_references'] == 8
    assert totals['retained_trim_COEDGE_candidates'] == 16 and totals['qualified_old_profile_diagnostics_resolved'] == 4
    assert all(old == actual for filename, old, actual in zip(files, before, current) if filename in CONTROLS)
    return dict(scope='Twelve actual new exports plus four legacy main-reader controls compared with142a5ea; bounded feature additions and exactly qualified profile membership recoveries only',
        baseline_commit=BASELINE, samples=rows,
        summary=dict(saved_files=len(files), legacy_full_output_controls=len(CONTROLS), **totals,
                     unexpected_prior_output_changes=0, ASM_geometry_changes=0,
                     unrelated_selection_warnings_cleared=0, live_API_calls=0),
        limitations=['No wall/Boolean regeneration; thin wall sides describe extrusion extent sides.',
            'Open source lineage follows an owned Line; the actual completed feature.profile getter returns Path.',
            'Trim selector literals and cached boundary intervals are separate; general selector-to-parameter semantics remain unknown.',
            'Custom datum reflections require the observed three-plane same-component ownership proof.',
            'Persistent topology, full native writing, solving, lifecycle replay and complete translation remain unfinished.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-cache', type=Path)
    parser.add_argument('--zstd-library')
    args = parser.parse_args()
    zstd = args.zstd_library or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result = validate(zstd, baseline_cache=args.baseline_cache)
    (ROOT/'modeling-extension-integration.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result['summary'], sort_keys=True))
