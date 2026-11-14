import collections
import hashlib
import json
import lzma
from pathlib import Path
import runpy
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
API = runpy.run_path(str(BASE.parent / 'EntityGraph/DecodeGraph.py'))
CAPTURES = ROOT / 're/Fusion/LocalOracle/RectangleDimensions'
STAGES = ('Baseline', 'WidthDimension', 'WidthDepthDimensions', 'EditedDimensions')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def group_ids(value):
    if isinstance(value, dict):
        if 'identifier' in value and 'fields' in value:
            yield value['identifier'].upper()
        for member in value.values():
            yield from group_ids(member)
    elif isinstance(value, list):
        for member in value:
            yield from group_ids(member)


def inspect(name):
    path = CAPTURES / (name + '.f3d')
    archive = API['TOOLS']['read_archive'](path)
    codec = API['GraphCodec'](archive)
    stops = collections.defaultdict(set)
    for record in archive['records']:
        if not record['primary']:
            stops[record['identity']].add(record['class']['identifier'].upper())
    records = []
    schemas = {}
    for record in archive['records']:
        identity = record['class']['identifier'].upper()
        reader = API['TOOLS']['Reader'](record['payload'])
        ends = stops[record['identity']] - ({identity} if not record['primary'] else set())
        groups = codec.groups(identity, ends)
        frame = codec.read_frame(reader, record['primary'])
        values = codec.read_groups(reader, groups)
        if reader.offset != len(reader.data):
            raise ValueError('Unexplained Design record bytes at ' + str(record['identity']))
        for group in groups + [codec.own_set(value) for value in group_ids(values)]:
            key = group['metatype_identifier'].upper()
            declared = codec.classes.get(key, {})
            schema = codec.schema[key]
            schemas[key] = {
                'className': schema['name'], 'classId': key,
                'schemaVersion': declared.get('schemaVersion', schema['metatype_current_version']),
                'versionSource': 'archive metadata' if declared else 'reflected current value schema',
                'category': schema['category'],
                'baseId': schema['base_identifier'],
                'members': [{
                    'name': member['name'],
                    'cppType': API['TOOLS']['demangle'](member['debug_type_name']),
                    'optionMask': member['option_mask'], 'metatype': member['metatype'],
                } for member in codec.members(group)],
            }
        records.append({
            'entityId': record['identity'], 'primary': record['primary'],
            'className': codec.schema[identity]['name'], 'classId': identity,
            'schemaVersion': record['class']['schemaVersion'],
            'payloadBytes': len(record['payload']), 'frame': frame, 'groups': values,
        })
    return {
        'stage': name, 'source': str(path.relative_to(ROOT)), 'sourceSha256': digest(path.read_bytes()),
        'metadataSha256': archive['metadataSha256'], 'bulkSha256': archive['bulkSha256'],
        'records': records, 'schemas': schemas,
    }


def key(record):
    return record['entityId'], record['primary'], record['classId']


def changes(first, second, prefix=''):
    if type(first) is type(second) is dict:
        result = []
        for name in sorted(first.keys() | second.keys()):
            path = prefix + '/' + str(name)
            if name not in first or name not in second:
                result.append({'path': path, 'before': first.get(name), 'after': second.get(name)})
            else:
                result.extend(changes(first[name], second[name], path))
        return result
    if first != second:
        return [{'path': prefix, 'before': first, 'after': second}]
    return []


def fields(record):
    return {
        'frame': record['frame'],
        'groups': {group['identifier'].upper(): group['fields'] for group in record['groups']},
    }


def compare(first, second):
    before = {key(record): record for record in first['records']}
    after = {key(record): record for record in second['records']}
    changed = []
    for identity in sorted(before.keys() & after.keys()):
        delta = changes(fields(before[identity]), fields(after[identity]))
        if delta:
            changed.append({
                'entityId': identity[0], 'primary': identity[1],
                'className': after[identity]['className'], 'changes': delta,
            })
    return {
        'beforeStage': first['stage'], 'afterStage': second['stage'],
        'addedRecords': [after[identity] for identity in sorted(after.keys() - before.keys())],
        'removedRecords': [before[identity] for identity in sorted(before.keys() - after.keys())],
        'changedRecords': changed,
    }


def main():
    graphs = [inspect(name) for name in STAGES]
    deltas = [compare(first, second) for first, second in zip(graphs, graphs[1:])]
    report = {
        'schema': 'FusionSketchDimensionDifferential/1',
        'scope': 'Read-only research decoder analysis; no production codec execution, local tests or native calls',
        'captureSha256': digest((CAPTURES / 'Capture.json').read_bytes()),
        'captureScriptSha256': digest((CAPTURES.parent / 'CaptureRectangleDimensions.py').read_bytes()),
        'decoderSha256': digest((BASE.parent / 'EntityGraph/DecodeGraph.py').read_bytes()),
        'reflectionSha256': digest((CAPTURES.parent / 'Reflection/Versions.json').read_bytes()),
        'graphs': graphs, 'deltas': deltas,
    }
    raw = (json.dumps(report, indent=2, allow_nan=False) + '\n').encode()
    packed = lzma.compress(raw, preset=9)
    (BASE / 'DimensionGraphs.json.xz').write_bytes(packed)
    summary = {
        'schema': report['schema'], 'scope': report['scope'],
        'artifact': 'DimensionGraphs.json.xz', 'artifactSha256': digest(packed),
        'uncompressedSha256': digest(raw), 'captureSha256': report['captureSha256'],
        'captureScriptSha256': report['captureScriptSha256'],
        'decoderSha256': report['decoderSha256'], 'reflectionSha256': report['reflectionSha256'],
        'stages': [{
            'stage': graph['stage'], 'source': graph['source'], 'sourceSha256': graph['sourceSha256'],
            'recordCount': len(graph['records']), 'primaryCount': sum(row['primary'] for row in graph['records']),
            'payloadBytes': sum(row['payloadBytes'] for row in graph['records']),
        } for graph in graphs],
        'deltas': [{
            'beforeStage': delta['beforeStage'], 'afterStage': delta['afterStage'],
            'addedRecords': [{name: row[name] for name in ('entityId', 'primary', 'className', 'classId', 'schemaVersion')} for row in delta['addedRecords']],
            'removedRecords': [{name: row[name] for name in ('entityId', 'primary', 'className')} for row in delta['removedRecords']],
            'changedRecords': [{name: row[name] for name in ('entityId', 'primary', 'className')} for row in delta['changedRecords']],
        } for delta in deltas],
    }
    (BASE / 'DimensionSummary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
