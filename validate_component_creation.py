"""Compare explicit creation links with local/API evidence and focused guards."""

import argparse
import json
from pathlib import Path
import struct

from decode_basics import decode_basics
from decode_component_creation import CREATE_COMPONENT, decode_component_creation
from decode_parameters import read_string
from decode_sketch import reference, same
from fusion_archive import read_members
from fusion_metadata import design_records


def validate(root, library):
    report = {'scope': 'Explicit component creation and historical placement; no replay or solved-state inference',
              'samples': [], 'negative_checks': [], 'api_comparisons': 0}
    guard_case = None
    for filename in json.loads((root/'fusion-class-catalog.json').read_text())['files']:
        members = read_members(root/filename, library)
        for name, data in members.items():
            if not name.endswith('FusionDesignSegmentType1/BulkStream.dat'):
                continue
            records, _ = design_records(data, members.get(name.replace('BulkStream.dat', 'MetaStream.dat')))
            if not any(r.is_primary and r.class_guid == CREATE_COMPONENT for r in records):
                continue
            main = decode_basics(root/filename, library)
            stream = next(s for s in main['streams'] if s['member'] == name)
            result = decode_component_creation(data, records, stream['features'], stream['assembly_decoding'])
            assert result['decoded'] and not result['unresolved'], (filename, result['unresolved'])
            sample = {'file': filename, 'expected_summary': result, 'api_checks': []}
            truth_path = (root/filename).parent/'ground_truth.json'
            truth = json.loads(truth_path.read_text()) if truth_path.exists() else {}
            actual = None
            if filename.startswith('assembly-'):
                actual = truth.get('occurrences', [])
            elif filename.startswith('jointmodes-'):
                actual = next(t['occurrences'] for t in truth['samples'] if t['file'] == Path(filename).name)
            if actual is not None:
                for item in result['decoded']:
                    matching = [o for o in actual if o['component_name'] == item['component_name']]
                    assert matching, (filename, item['component_name'])
                    # A repeated component may have multiple occurrence paths;
                    # the explicitly created native occurrence selects its paths.
                    if filename.startswith('assembly-'):
                        selected = [o for o in matching if o['path'] in item['occurrence_paths']]
                        assert selected
                        assert all(same(item['snapshot_transform'], o['native_transform2']) for o in selected)
                        check = {'component_name': item['component_name'], 'component_and_created_path_match_api': True,
                                 'snapshot_matches_api_native_local_transform': True}
                        report['api_comparisons'] += 3
                    else:
                        assert len(matching) == 1
                        # Moving was repositioned by the joint after creation.
                        # Preserve the disagreement rather than replacing the
                        # historical snapshot with the saved solved API result.
                        agrees = same(item['snapshot_transform'], matching[0]['transform'])
                        assert agrees is (item['component_name'] == 'Fixed')
                        check = {'component_name': item['component_name'], 'component_matches_api': True,
                                 'snapshot_matches_saved_api_transform': agrees,
                                 'scope': 'Historical creation snapshot; Moving differs after joint solving'}
                        report['api_comparisons'] += 2
                    sample['api_checks'].append(check)
            if 'component_creations' in stream:
                assert stream['component_creations'] == result
                sample['main_reader_summary_exact'] = True
            report['samples'].append(sample)
            if guard_case is None:
                guard_case = data, records, stream, result
    data, records, stream, result = guard_case
    primary = {r.object_id: r for r in records if r.is_primary}
    item = result['decoded'][0]
    creation = primary[item['feature_object_id']]
    snapshot = primary[item['snapshot_object_id']]
    datum = primary[item['occurrence_datum_object_id']]
    payload = data[snapshot.body:snapshot.end]
    _, end = read_string(payload, 19 if payload[18] else 147)
    mutations = [('Creation snapshot reference mismatch', creation.body+211, struct.pack('<Q', 999999)),
                 ('Snapshot counted association changed', snapshot.body+end+38, struct.pack('<I', 2)),
                 ('Occurrence datum owner changed', datum.body+29, struct.pack('<Q', 999999))]
    if payload[18] == 0:
        mutations.append(('Snapshot matrix is not rigid', snapshot.body+19, struct.pack('<d', 2.0)))
    for label, offset, replacement in mutations:
        changed = bytearray(data)
        changed[offset:offset+len(replacement)] = replacement
        output = decode_component_creation(bytes(changed), records, stream['features'], stream['assembly_decoding'])
        failures = [u for u in output['unresolved'] if u['feature_object_id'] == item['feature_object_id']]
        assert len(failures) == 1 and all(d['feature_object_id'] != item['feature_object_id'] for d in output['decoded'])
        report['negative_checks'].append({'check': label, 'passed': True, 'reason': failures[0]['reason']})
    report['archive_count'] = len(report['samples'])
    report['creation_count'] = sum(len(s['expected_summary']['decoded']) for s in report['samples'])
    report['limitations'] = ['Only observed local creation layouts and nil namespace fields; external component creation and copy/paste are unsupported.',
                             'Internal snapshot class remains an unsupported feature with separately decoded placement/association fields.',
                             'Snapshots can disagree with saved solved API occurrence transforms; they are not a current-state or joint-solution claim.',
                             'Only assembly and joint fixtures have independent saved occurrence getters; other cases provide native structural consistency evidence.']
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zstd-library', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    result = validate(root, args.zstd_library)
    (root/'component-creation-decoding.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ('archive_count', 'creation_count', 'api_comparisons')}))
