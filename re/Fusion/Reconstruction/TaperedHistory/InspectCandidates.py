import collections
import hashlib
import json
import lzma
import runpy
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
HELPERS = runpy.run_path(str(BASE.parent / 'CuboidHistory/InspectHistory.py'))


def inspect(entry):
    with zipfile.ZipFile(ROOT / entry['path']) as archive:
        payload = archive.read(entry['member'])
    if hashlib.sha256(payload).hexdigest() != entry['sha256']:
        raise ValueError('Corpus member digest changed')
    model = HELPERS['DECODER'](payload)
    boundary = next(index for index, row in enumerate(model['records']) if row['boundary_marker'])
    records = model['records'][:boundary]
    surface = next(row for row in records if row['name'] == 'cone-surface')
    cone = HELPERS['fields'](surface)
    curves = [HELPERS['fields'](row) for row in records if row['name'] == 'ellipse-curve']
    attrs = []
    for row in records:
        if row['name'] != 'ATTRIB_CUSTOM-attrib':
            continue
        data = HELPERS['fields'](row)
        attrs.append(dict(ownerType=records[data[4]]['name'], family=data[5], groups=HELPERS['groups'](row)))
    journal_rows = model['records'][boundary:-1]
    journal_names = [row['name'] for row in journal_rows]
    if journal_names == ['history_stream', 'delta_state', 'delta_state']:
        journal = HELPERS['journal'](journal_rows, len(records))
    else:
        journal = dict(simpleInsertionJournal=False, unsupportedShape=True, recordTypes=dict(collections.Counter(journal_names)), fieldCounts=[len(row['fields']) for row in journal_rows])
    return dict(source=entry, initialRecordCount=len(records), coneFields=cone[3:], circleFields=[row[3:] for row in curves], signedSine=cone[9], cosine=cone[10], journal=journal, attributes=attrs)


def main():
    path = BASE.parent / 'BrepCoverage/Inventory.json.xz'
    inventory = json.loads(lzma.decompress(path.read_bytes()))
    selected = [entry for entry in inventory['members'] if entry['extension'] == '.smbh' and inventory['uniqueBlobs'][entry['sha256']]['initialRecordCount'] == 35]
    samples = [inspect(entry) for entry in selected]
    report = dict(schema='FusionCircularHistoryCandidates/1', scope='Read-only inventory of all 35-record histories in the frozen corpus; cone fields classify geometry, record count alone does not establish parser support', inventorySha256=hashlib.sha256(path.read_bytes()).hexdigest(), archives=len({entry['path'] for entry in selected}), members=len(samples), uniqueMembers=len({entry['sha256'] for entry in selected}), zeroAngle=sum(row['signedSine'] == 0 for row in samples), nonzeroAngle=sum(row['signedSine'] != 0 for row in samples), simpleInsertionJournals=sum(row['journal']['simpleInsertionJournal'] for row in samples), samples=samples)
    (BASE / 'CandidateHistories.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'samples'}, indent=2))
    print(json.dumps([dict(source=row['source']['path'], sine=row['signedSine'], cosine=row['cosine']) for row in samples if row['signedSine'] != 0], indent=2))


if __name__ == '__main__':
    main()
