"""Focused offline API/native/main checks for the five silhouette split captures.

Run with --zstd-library <local libzstd path>; --report writes the JSON evidence.
The failed solid-cylinder ShelledBody attempt is preserved as API failure evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from decode_basics import decode_basics
from decode_silhouette_splits import FEATURE, decode_silhouette_splits
from decode_sketch import attributes, same
from fusion_archive import read_members
from fusion_metadata import design_records

FOLDERS = ('silhouettesplits-7d78a686cdbb', 'silhouettesplits-f21b83e21695')
OPERATION_NAMES = {0: 'FacesOnly', 1: 'ShelledBody', 2: 'SolidBody'}


def validate(root, zstd_library=None):
    root = Path(root)
    report = {
        'scope': 'Observed SilhouetteSplit operation/direction and historical body provenance; additional anchors distinct from API result-body/root-body collections',
        'integration': {'function': 'decode_silhouette_splits(data, records, features, body_selections=None)',
                        'main_stream_key': 'silhouette_splits',
                        'validator': 'validate_silhouette_splits.validate(root, zstd_library=None)',
                        'expected_outputs': 'samples[].expected_summary contains complete main/helper summary for equality checks.'},
        'layout_evidence': {
            'operations': 'Native/API integer0 FacesOnly,1 ShelledBody,2 SolidBody verified in actual successful captures.',
            'directions': 'Typed F2A direction control ->5A1B descriptor ->90055 native identity leaf selects origin AxisX/AxisY or PlaneYZ; method7 Axis/method14 Plane, repeated descriptor and feature owners must agree.',
            'targets': 'Owned body proxy/descriptor resolves explicit historical native body/anchor; original SilhouetteCylinder owner retained even after a Shell modifies that same named body.',
            'additional_anchors': 'Captured FacesOnly stores zero additional anchors yet API Feature.bodies/root collection each contains one body. Captured SolidBody/ShelledBody stores one additional owned anchor while both API collections contain two bodies. These are observed distinctions, not a general result-collection reconstruction rule.'},
        'limitations': [
            'Only captured root-context one-target operation/direction layouts; other direction types, occurrence contexts and control combinations unverified.',
            'Persistent silhouette curves, exact result topology, native face/edge identity, regeneration and replay remain unresolved.',
            'API health/suppression, face/edge counts, volumes and bounding boxes are retained as observations only; they are not claimed as decoded native controls/geometry.',
            'One solid-cylinder ShelledBody request failed in the kernel, while one explicitly hollow-cylinder ShelledBody request succeeded; this is fixture evidence, not a universal acceptance rule.',
            'The hollow-cylinder target remains API isSolid=True; hollow construction is documented by the captured Shell setup and parameters, not inferred from isSolid=False.'],
        'samples': [], 'failed_API_attempts': [], 'malformed_checks': [], 'summary': {}}
    fixtures = []
    api_count = structural_count = 0
    for folder in FOLDERS:
        directory = root/folder
        assert (directory/'complete.txt').is_file(), folder
        truth = json.loads((directory/'ground_truth.json').read_text())
        for failure in truth['errors']:
            report['failed_API_attempts'].append({'capture_folder': folder, **failure,
                'archive_exported': (directory/(failure['case']+'.f3d')).exists()})
        for sample in truth['samples']:
            archive = directory/sample['file']
            main = decode_basics(archive, zstd_library)
            stream = next(s for s in main['streams'] if s.get('silhouette_splits', {}).get('decoded'))
            members = read_members(archive, zstd_library)
            data = members[stream['member']]
            records, _ = design_records(data, members[stream['member'].replace('BulkStream.dat', 'MetaStream.dat')])
            actual = stream['silhouette_splits']
            out = decode_silhouette_splits(data, records, stream['features'], stream['body_selections'])
            assert actual == out and len(out['decoded']) == 1 and not out['unresolved'], sample['file']
            row = out['decoded'][0]
            checks, api = {'main_helper_complete_output_equality': True}, {}

            def eq(label, a, b, api_evidence=False):
                good = same(a, b) if isinstance(a, list) and a and isinstance(a[0], (int, float)) else a == b
                assert good, (sample['file'], label, a, b)
                (api if api_evidence else checks)[label] = True

            eq('operation_code', row['operation_code'], sample['settings']['operation'], True)
            eq('operation_name', row['operation'], OPERATION_NAMES[sample['settings']['operation']], True)
            source, expected = row['view_direction']['entity'], sample['actual_direction']
            eq('exact_direction_type', 'adsk::fusion::'+source['kind'], expected['entity_type'], True)
            eq('exact_direction_name', source['name'], expected['name'], True)
            eq('direction_origin_cm', source['origin_cm'], expected['origin_cm'], True)
            geometry_field = 'direction' if source['kind'] == 'ConstructionAxis' else 'normal'
            eq('direction_vector_or_plane_normal', source[geometry_field], expected[geometry_field], True)
            eq('method_correspondence', row['stored_direction_method_code'], 7 if geometry_field == 'direction' else 14)
            bodies = {b['object_id']: b for b in stream['body_properties']['bodies']}
            target = row['target']; target_body = bodies[target['native_body_object_id']]
            eq('explicit_target_body_name', target_body['name'], sample['actual_target']['name'], True)
            owner = next(f for f in stream['features'] if f['object_id'] == target['source_owner_object_id'])
            seed_parameter = next(p for p in sample['parameters'] if p['role'] == 'AlongDistance')
            eq('historical_body_owner_name_matches_seed_parameter_createdBy', owner['name'], seed_parameter['created_by'], True)
            eq('historical_owner_is_original_seed_Extrude', owner['kind'], 'Extrude')
            collections = [c for c in stream['body_properties']['collections'] if c['object_id'] == target_body['collection_object_id']]
            eq('one_explicit_target_root_collection', len(collections), 1)
            members_ids = collections[0]['body_object_ids']
            eq('explicit_root_collection_count_matches_API', len(members_ids), len(sample['root_bodies']), True)
            eq('explicit_root_collection_names_match_API', [bodies[i]['name'] for i in members_ids], [b['name'] for b in sample['root_bodies']], True)
            eq('captured_Feature_bodies_count_matches_root_API_count', len(sample['feature_bodies']), len(sample['root_bodies']), True)
            additional = row['stored_additional_body_anchors']
            eq('additional_anchors_are_not_total_API_result_body_count', len(additional) < len(sample['feature_bodies']), True)
            eq('captured_additional_anchor_count', len(additional), 0 if row['operation_code'] == 0 else 1)
            for anchor in additional:
                eq('additional_anchor_is_owned_by_split', anchor['source_owner_object_id'], row['feature_object_id'])
                eq('additional_body_is_distinct_from_historical_target', anchor['native_body_object_id'] != target['native_body_object_id'], True)
                eq('additional_body_occurs_in_explicit_root_collection', anchor['native_body_object_id'] in members_ids, True)
                eq('additional_body_name_matches_second_API_result', bodies[anchor['native_body_object_id']]['name'], sample['feature_bodies'][1]['name'], True)
            observation = {'stored_additional_anchor_count': len(additional),
                'API_feature_body_count': len(sample['feature_bodies']), 'API_root_body_count': len(sample['root_bodies']),
                'native_root_body_ids': members_ids, 'historical_target_body_id': target['native_body_object_id'],
                'historical_target_owner_name': owner['name']}
            report['samples'].append({'file': str(archive.relative_to(root)), 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                'expected_summary': out, 'api_comparisons': api, 'native_structure_checks': checks,
                'anchor_vs_collection_observation': observation,
                'API_observations': {k: sample[k] for k in ('actual_direction', 'actual_target', 'settings', 'feature_bodies', 'root_bodies', 'parameters')},
                'getter_errors': sample['getter_errors']})
            api_count += len(api); structural_count += len(checks)
            fixtures.append((data, records, stream, row))
    assert len(fixtures) == 5 and {s['expected_summary']['decoded'][0]['operation_code'] for s in report['samples']} == {0, 1, 2}
    assert len(report['failed_API_attempts']) == 1
    failed = report['failed_API_attempts'][0]
    assert failed['case'] == 'shelled_axis_x' and not failed['archive_exported'] and 'SILHOUETTE_SPLIT_SHEET_FAIL' in failed['error']
    data, records, stream, row = fixtures[0]
    primary = {r.object_id: r for r in records if r.is_primary}
    feature_record = primary[row['feature_object_id']]
    feature_body = data[feature_record.body:feature_record.end]
    _, cursor = attributes(feature_body, 2) if feature_body[1] else ({}, 2)
    direction_record = primary[row['direction_control_object_id']]
    leaf_record = primary[row['view_direction']['terminal_object_id']]

    def bad(label, change):
        altered = bytearray(data); change(altered)
        got = decode_silhouette_splits(altered, records, stream['features'], stream['body_selections'])
        assert not got['decoded'] and got['unresolved'], label
        report['malformed_checks'].append({'name': label, 'rejected': True, 'reason': got['unresolved'][0]['reason']})

    bad('unknown operation control3', lambda b: struct.pack_into('<I', b, feature_record.body+cursor+19, 3))
    bad('additional anchor count disagrees with FacesOnly', lambda b: struct.pack_into('<I', b, feature_record.body+cursor+27, 1))
    bad('direction control owner replaced by historical seed owner', lambda b: struct.pack_into('<Q', b, direction_record.body+192, row['target']['source_owner_object_id']))
    bad('direction native identity leaf replaced by BRepBody ID', lambda b: struct.pack_into('<Q', b, leaf_record.body+2, row['target']['native_body_object_id']))
    report['summary'] = {'successful_archives': len(fixtures), 'preserved_failed_API_attempts': len(report['failed_API_attempts']),
        'getter_errors': sum(len(s['getter_errors']) for s in report['samples']),
        'API_comparisons': api_count, 'native_structure_and_main_equality_checks': structural_count,
        'malformed_checks': len(report['malformed_checks']), 'all_passed': True}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--zstd-library', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    report = validate(args.root, args.zstd_library)
    if args.report:
        args.report.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], indent=2))


if __name__ == '__main__':
    main()
