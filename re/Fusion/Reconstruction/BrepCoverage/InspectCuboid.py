import collections
import hashlib
import json
import runpy
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
TOKEN = runpy.run_path(str(BASE.parent / 'BrepTokens.py'))
CONTROL = ROOT / 're/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d'


def main():
    with zipfile.ZipFile(CONTROL) as archive:
        member = next(name for name in archive.namelist() if name.endswith('.smbh'))
        payload = archive.read(member)
    parsed = TOKEN['read_stream'](payload)
    initial = []
    for record in parsed['records']:
        if record['boundary_marker'] or record['name'] == 'End-of-ASM-data':
            break
        initial.append(record)
    examples = {}
    for index, record in enumerate(initial):
        examples.setdefault(record['name'], {'ordinal': index, 'byteOffset': record['offset'], 'fields': [{'tag': field['tag'], 'value': field['value']} for field in record['fields']]})
    truth_path = CONTROL.with_name('ground_truth.json')
    truth = next(sample for sample in json.loads(truth_path.read_text())['samples'] if sample['case'] == 'ordinary_rectangle_control')
    history = parsed['records'][len(initial):-1]
    current = history[1]['fields']
    insertion_rows = current[12:-3]
    insertions = [insertion_rows[index + 2]['value'] for index in range(0, len(insertion_rows), 3)]
    result = {'schema': 'FusionCuboidControl/1', 'scope': 'Existing vendor control inspected with research token decoder; semantic expansion proposal, not newly verified production support', 'archive': str(CONTROL.relative_to(ROOT)), 'archiveSha256': hashlib.sha256(CONTROL.read_bytes()).hexdigest(), 'member': member, 'memberSha256': hashlib.sha256(payload).hexdigest(), 'header': parsed['header'], 'groundTruth': {'path': str(truth_path.relative_to(ROOT)), 'sha256': hashlib.sha256(truth_path.read_bytes()).hexdigest(), 'requested': truth['requested'], 'actualInput': truth['actual_input'], 'body': truth['result_bodies'][0], 'computeAll': truth['compute_all_returned'], 'healthState': truth['health_state'], 'featureType': truth['settings']['feature_type']}, 'initialRecordCount': len(initial), 'recordCounts': dict(collections.Counter(record['name'] for record in initial)), 'fieldExamples': examples, 'vertexEdgeIndices': dict(collections.Counter(record['fields'][4]['value'] for record in initial if record['name'] == 'vertex')), 'history': {'records': [record['name'] for record in history], 'currentFieldCount': len(current), 'insertionCount': len(insertions), 'insertionIds': sorted(insertions), 'coversEveryOwnedInitialEntity': sorted(insertions) == list(range(1, len(initial))), 'insertionTriples': all(insertion_rows[index]['value'] == 1 and insertion_rows[index + 1]['value'] == -1 for index in range(0, len(insertion_rows), 3)), 'preamble': [(field['tag'], field['value']) for field in history[0]['fields']], 'currentPrefix': [(field['tag'], field['value']) for field in current[:12]], 'currentTrailer': [(field['tag'], field['value']) for field in current[-3:]], 'initialState': [(field['tag'], field['value']) for field in history[2]['fields']]}}
    (BASE / 'CuboidControl.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key not in ('header', 'fieldExamples', 'history')}))


if __name__ == '__main__':
    main()
