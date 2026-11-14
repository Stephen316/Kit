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
DECODER = runpy.run_path(str(BASE.parent / 'BrepTokens.py'))['read_stream']
CONTROL = 're/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d'
FIELDS = {
    'asmheader': ['attribute', 'qualifiedIdentity', 'version'],
    'body': ['attribute', 'bodyKey', 'pattern', 'firstLump', 'firstWire', 'transform'],
    'lump': ['attribute', 'entityId', 'pattern', 'nextLump', 'firstShell', 'body'],
    'shell': ['attribute', 'entityId', 'pattern', 'nextShell', 'firstSubshell', 'firstFace', 'wire', 'lump'],
    'face': ['attribute', 'entityId', 'pattern', 'nextFace', 'firstLoop', 'shell', 'qualifiedNull', 'surface', 'reversed', 'doubleSided'],
    'loop': ['attribute', 'entityId', 'pattern', 'nextLoop', 'firstCoedge', 'face'],
    'coedge': ['attribute', 'entityId', 'pattern', 'nextCoedge', 'previousCoedge', 'partner', 'edge', 'reversed', 'loop', 'qualifiedZero', 'pcurve'],
    'edge': ['attribute', 'entityId', 'pattern', 'startVertex', 'startParameter', 'endVertex', 'endParameter', 'ownerCoedge', 'curve', 'reversed', 'convexity'],
    'vertex': ['attribute', 'entityId', 'pattern', 'ownerEdge', 'ownerEndpointIndex', 'point'],
    'point': ['attribute', 'entityId', 'pattern', 'positionCm'],
    'straight-curve': ['attribute', 'entityId', 'pattern', 'originCm', 'parametricDirection', 'hasLowerBound', 'lowerBound', 'hasUpperBound', 'upperBound'],
    'plane-surface': ['attribute', 'entityId', 'pattern', 'originCm', 'normal', 'referenceVector', 'vSense', 'hasUMin', 'hasUMax', 'hasVMin', 'hasVMax'],
}


def fields(record):
    return [item['tag'] == 10 if item['tag'] in (10, 11) else item['value'] for item in record['fields']]


def groups(record):
    data = fields(record)
    if data[5] != 'generic_tag_attrib_def':
        return []
    result = []
    cursor = 11
    for _ in range(data[10]):
        length, primary, secondary, count = data[cursor:cursor + 4]
        operations = data[cursor + 4:cursor + 4 + count]
        approach = data[cursor + 4 + count]
        result.append(dict(primaryByteLength=length, primaryId=primary, secondaryId=secondary, operationIds=operations, approachId=approach, byteLengthMatches=length == len(primary.encode())))
        cursor += 5 + count
    if cursor != len(data):
        raise ValueError('Generic attribute has unexplained fields')
    return result


def journal(rows, count):
    preamble, current, initial = map(fields, rows)
    preamble_tags, current_tags, initial_tags = ([item['tag'] for item in row['fields']] for row in rows)
    changes = current[12:-3]
    triples = [changes[index:index + 3] for index in range(0, len(changes), 3)]
    current_shape = current[:12] == [current[0], 1, 0, -1, 1, 0, -1, 0, False, 1, 0, current[11]]
    initial_shape = initial == [initial[0], 1, 0, 0, -1, 1, -1, 0, False, 0, 0]
    preamble_shape = preamble == [preamble[0], preamble[0], 0, preamble[3], -1, 0, 1, -1]
    insertion_only = all(len(row) == 3 and row[:2] == [1, -1] for row in triples)
    complete = insertion_only and sorted(row[2] for row in triples) == list(range(1, count))
    typed = preamble_tags == [4] * 4 + [12] * 4 and current_tags == [4] * 3 + [12] * 5 + [11, 4, 12, 4] + [4, 12, 12] * len(triples) + [4] * 3 and initial_tags == [4] * 3 + [12] * 5 + [11, 4, 4]
    simple = typed and current_shape and initial_shape and preamble_shape and complete and current[-3:] == [0, 0, 0]
    return dict(preamble=preamble, currentPrefix=current[:12], currentTrailer=current[-3:], initialState=initial, fieldCount=len(current), insertionCount=len(triples), insertionOnly=insertion_only, coversInitialRecords=complete, typedFieldsMatch=typed, simpleInsertionJournal=simple, insertionIds=[row[2] for row in triples if len(row) == 3], initialCurrentIds=[initial[0], current[0]])


def load_member(entry):
    with zipfile.ZipFile(ROOT / entry['path']) as archive:
        payload = archive.read(entry['member'])
    if hashlib.sha256(payload).hexdigest() != entry['sha256']:
        raise ValueError('Corpus member digest changed')
    parsed = DECODER(payload)
    boundary = next(index for index, record in enumerate(parsed['records']) if record['boundary_marker'])
    return parsed, parsed['records'][:boundary], parsed['records'][boundary:-1]


def inspect(entry):
    parsed, records, history = load_member(entry)
    attributes = []
    for index, record in enumerate(records):
        if record['name'] != 'ATTRIB_CUSTOM-attrib':
            continue
        data = fields(record)
        owner = data[4]
        attributes.append(dict(ordinal=index, owner=owner, ownerType=records[owner]['name'], family=data[5], next=data[2], previous=data[3], genericGroups=groups(record), sketchTuple=data[9] if data[5] == 'sketch_attrib_def' and data[8] == 3 else None))
    expected_attributes = collections.Counter({('body', 'Timestamp_attrib_def'): 1, ('body', 'generic_tag_attrib_def'): 1, ('face', 'generic_tag_attrib_def'): 6, ('coedge', 'sketch_attrib_def'): 8})
    ordinary = len(records) == 102 and collections.Counter((item['ownerType'], item['family']) for item in attributes) == expected_attributes and all(len(item['genericGroups']) == 1 for item in attributes if item['family'] == 'generic_tag_attrib_def')
    result = dict(source=entry, initialRecordCount=len(records), recordCounts=dict(collections.Counter(record['name'] for record in records)), ordinaryAttributeShape=ordinary, header={**{key: value for key, value in parsed['header'].items() if key != 'tagged_values'}, 'values': [item['value'] for item in parsed['header']['tagged_values']]}, journal=journal(history, len(records)), attributes=attributes)
    return result, records


def control_report(report, records):
    semantic = []
    for index, record in enumerate(records):
        data = fields(record)
        if record['name'] == 'ATTRIB_CUSTOM-attrib':
            names = ['reserved', 'marker', 'next', 'previous', 'owner', 'family']
            if data[5] == 'Timestamp_attrib_def':
                names += ['schema', 'authoredUnixMicros']
            elif data[5] == 'sketch_attrib_def':
                names += ['schema', 'schemaDuplicate', 'payloadForm', 'sourceCurveTuple']
            else:
                names += ['schema', 'schemaDuplicate', 'reservedVersion', 'repeatedFamily', 'groupCount', 'primaryByteLength', 'primaryId', 'secondaryId', 'operationCount']
                names += ['operationId'] * data[14] + ['approachId']
        else:
            names = FIELDS[record['name']]
            if record['name'] == 'straight-curve':
                names = names[:5]
                cursor = 5
                for bound in ('Lower', 'Upper'):
                    names.append('has' + bound + 'Bound')
                    present = data[cursor]
                    cursor += 1
                    if present:
                        names.append(bound.lower() + 'Bound')
                        cursor += 1
        if len(names) != len(data):
            raise ValueError(f'Incomplete control field schema: {index} {record["name"]}')
        semantic.append(dict(ordinal=index, recordType=record['name'], byteOffset=record['offset'], fields=[dict(name=name, tag=item['tag'], value=value) for name, item, value in zip(names, record['fields'], data)]))
    faces = []
    for index, record in enumerate(records):
        if record['name'] != 'face':
            continue
        data = fields(record)
        loop = fields(records[data[4]])
        first = loop[4]
        cursor = first
        rim = []
        while True:
            coedge = fields(records[cursor])
            edge = fields(records[coedge[6]])
            positions = []
            for vertex in (edge[3], edge[5]):
                positions.append(fields(records[fields(records[vertex])[5]])[3])
            rim.append(dict(coedge=cursor, reversed=coedge[7], edge=coedge[6], endpointsCm=positions, sketchTuple=fields(records[coedge[0]])[9] if coedge[0] != -1 else None))
            cursor = coedge[3]
            if cursor == first:
                break
            if len(rim) > 4:
                raise ValueError('Unexpected control face rim')
        faces.append(dict(ordinal=index, group=groups(records[data[0]])[0], reversed=data[8], plane=fields(records[data[7]])[3:], rim=rim))
    return {**report, 'schema': 'FusionControlledCuboidHistory/1', 'records': semantic, 'faces': faces}


def main():
    inventory_path = BASE.parent / 'BrepCoverage/Inventory.json.xz'
    inventory = json.loads(lzma.decompress(inventory_path.read_bytes()))
    selected = []
    known = {'Timestamp_attrib_def', 'generic_tag_attrib_def', 'sketch_attrib_def'}
    for entry in inventory['members']:
        shape = inventory['uniqueBlobs'][entry['sha256']]
        bodies = shape['bodies']
        if entry['extension'] == '.smbh' and len(bodies) == 1 and bodies[0].get('axisAlignedBoxCandidate') and shape['historyRecordTypes'] == {'history_stream': 1, 'delta_state': 2, 'End-of-ASM-data': 1} and set(shape['attributeTypes']) <= known:
            selected.append(entry)
    reports = []
    for entry in selected:
        report, records = inspect(entry)
        reports.append(report)
        if entry['path'] == CONTROL:
            (BASE / 'ControlledHistory.json').write_text(json.dumps(control_report(report, records), indent=2) + '\n')
    histogram = lambda values: dict(collections.Counter(str(value) for value in values))
    attributes = [attribute for report in reports for attribute in report['attributes']]
    generic = [group for attribute in attributes for group in attribute['genericGroups']]
    summary = dict(schema='FusionCuboidHistoryCandidates/1', scope='Read-only token and named-field inspection of frozen candidate set; not independent writer or vendor acceptance', sourceInventorySha256=hashlib.sha256(inventory_path.read_bytes()).hexdigest(), members=len(reports), archives=len({report['source']['path'] for report in reports}), simpleInsertionJournalCount=sum(report['journal']['simpleInsertionJournal'] for report in reports), initialRecordCounts=histogram(report['initialRecordCount'] for report in reports), attributeCounts=histogram(len(report['attributes']) for report in reports), attributeOwnership=histogram((attribute['ownerType'], attribute['family']) for attribute in attributes), genericGroupCounts=histogram(len(attribute['genericGroups']) for attribute in attributes if attribute['family'] == 'generic_tag_attrib_def'), genericSecondaryIds=histogram(group['secondaryId'] for group in generic), genericApproachIds=histogram(group['approachId'] for group in generic), primaryByteLengthMismatches=sum(not group['byteLengthMatches'] for group in generic), historyStatePairs=histogram(report['journal']['initialCurrentIds'] for report in reports), details='CandidateHistories.json.xz')
    raw = (json.dumps({'schema': summary['schema'], 'members': reports}, separators=(',', ':')) + '\n').encode()
    packed = lzma.compress(raw, preset=9)
    (BASE / 'CandidateHistories.json.xz').write_bytes(packed)
    summary['detailsSha256'] = hashlib.sha256(packed).hexdigest()
    summary['ordinary102RecordAttributeShape'] = sum(report['ordinaryAttributeShape'] for report in reports)
    (BASE / 'CandidateSummary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
