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
HELPERS = runpy.run_path(str(BASE.parent / 'CuboidHistory/InspectHistory.py'))
DECODER = HELPERS['DECODER']
FIELDS = {
    **HELPERS['FIELDS'],
    'ellipse-curve': ['attribute', 'entityId', 'pattern', 'centerCm', 'normal', 'majorVectorCm', 'ratio', 'hasLowerBound', 'hasUpperBound'],
    'cone-surface': ['attribute', 'entityId', 'pattern', 'centerCm', 'axis', 'majorVectorCm', 'ratio', 'ellipseHasLowerBound', 'ellipseHasUpperBound', 'sineAngle', 'cosineAngle', 'parameterScaleCm', 'reversedSense', 'hasUMin', 'hasUMax', 'hasVMin', 'hasVMax'],
}


def describe_record(row):
    data = HELPERS['fields'](row)
    if row['name'] == 'ATTRIB_CUSTOM-attrib':
        names = ['reserved', 'marker', 'next', 'previous', 'owner', 'family']
        if data[5] == 'Timestamp_attrib_def':
            names += ['schema', 'authoredUnixMicros']
        elif data[5] == 'sketch_attrib_def':
            names += ['schema', 'schemaDuplicate', 'payloadForm', 'sourceCurveTuple']
        else:
            names += ['schema', 'schemaDuplicate', 'reservedVersion', 'repeatedFamily', 'groupCount', 'primaryByteLength', 'primaryId', 'secondaryId', 'operationCount']
            names += ['operationId'] * data[14] + ['approachId']
    else:
        names = FIELDS[row['name']]
    if len(names) != len(data):
        raise ValueError('Unsupported controlled record grammar')
    result = dict(ordinal=row['physical_record_index'], recordType=row['name'], byteOffset=row['offset'], fields=[dict(name=name, tag=item['tag'], value=value) for name, item, value in zip(names, row['fields'], data)])
    if row['name'] == 'ATTRIB_CUSTOM-attrib':
        result['genericGroups'] = HELPERS['groups'](row)
    return result


def inspect(source):
    with zipfile.ZipFile(source) as archive:
        member = next(name for name in archive.namelist() if name.endswith('.smbh'))
        payload = archive.read(member)
    model = DECODER(payload)
    boundary = next(index for index, row in enumerate(model['records']) if row['boundary_marker'])
    initial = model['records'][:boundary]
    records = [describe_record(row) for row in initial]
    summary = dict(source=str(source.relative_to(ROOT)), sourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(), member=member, memberSha256=hashlib.sha256(payload).hexdigest(), header=model['header'], initialRecordCount=len(initial), recordTypes=dict(collections.Counter(row['name'] for row in initial)), journal=HELPERS['journal'](model['records'][boundary:-1], len(initial)), records=records)
    return summary


def main():
    study = ROOT / 're/Fusion/Study/extents-f0f33a9a605f'
    samples = [inspect(study / name) for name in ('distance_positive.f3d', 'taper.f3d')]
    changes = []
    for before, after in zip(samples[0]['records'], samples[1]['records'], strict=True):
        if before['recordType'] != after['recordType']:
            raise ValueError('Control record order differs')
        for old, new in zip(before['fields'], after['fields'], strict=True):
            if old != new:
                changes.append(dict(ordinal=before['ordinal'], recordType=before['recordType'], field=old['name'], before=old['value'], after=new['value']))
    report = dict(schema='FusionControlledTaperedHistory/1', scope='Read-only complete field decoding of two native source histories; no production execution or native calls', samples=samples, changes=changes, identicalJournal=samples[0]['journal'] == samples[1]['journal'])
    (BASE / 'ControlledHistory.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(counts=[sample['initialRecordCount'] for sample in samples], identicalJournal=report['identicalJournal'], changes=changes), indent=2))


if __name__ == '__main__':
    main()
