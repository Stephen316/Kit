import collections
import hashlib
import json
import lzma
import runpy
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
API = runpy.run_path(str(BASE.parent / 'EntityGraph/DecodeGraph.py'))


def inspect(path, codec):
    archive = API['TOOLS']['read_archive'](path)
    codec.classes = {item['identifier'].upper(): item for item in archive['classes'].values()}
    continuations = collections.defaultdict(set)
    for record in archive['records']:
        if not record['primary']:
            continuations[record['identity']].add(record['class']['identifier'].upper())
    records = []
    counts = collections.Counter()
    recipes = collections.Counter()
    for record in archive['records']:
        reader = API['TOOLS']['Reader'](record['payload'])
        identifier = record['class']['identifier'].upper()
        result = {'entityId': record['identity'], 'primary': record['primary'], 'classIdentifier': identifier, 'className': codec.schema.get(identifier, {}).get('name', ''), 'version': record['class']['schemaVersion'], 'payloadBytes': len(reader.data), 'payloadOffset': record['payloadBulkOffset']}
        try:
            stops = continuations[record['identity']] - ({identifier} if not record['primary'] else set())
            groups = codec.groups(identifier, stops)
            frame = codec.read_frame(reader, record['primary'])
            values = codec.read_groups(reader, groups)
            for evidence in reader.evidence:
                item = evidence['value']
                if isinstance(item, dict) and 'lwdTags' in item and 'type' in item:
                    recipes[(item['version'], item['type'])] += 1
            remaining = len(reader.data) - reader.offset
            result.update(status='decoded' if remaining == 0 else 'tail', consumedBytes=reader.offset, remainingBytes=remaining, fieldCount=len(reader.evidence))
            if remaining:
                result['error'] = 'Unexplained trailing bytes'
        except (ValueError, KeyError, UnicodeError, struct.error, RecursionError, OverflowError) as error:
            result.update(status='unresolved', consumedBytes=reader.offset, remainingBytes=len(reader.data) - reader.offset, error=str(error), lastField=reader.evidence[-1]['name'] if reader.evidence else '')
        counts[result['status']] += 1
        records.append(result)
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'metadataSha256': archive['metadataSha256'], 'bulkSha256': archive['bulkSha256'], 'recordCount': len(records), 'counts': dict(counts), 'records': records, 'recipes': [{'version': version, 'type': kind, 'count': count} for (version, kind), count in sorted(recipes.items())]}


def main():
    inventory = json.loads((BASE.parent / 'CorpusInventory.json').read_text())
    codec = API['GraphCodec']({'classes': {}})
    samples, failures = [], []
    for index, entry in enumerate(inventory['files']):
        path = ROOT / entry['path']
        try:
            sample = inspect(path, codec)
            samples.append(sample)
        except Exception as error:
            failures.append({'path': entry['path'], 'error': repr(error)})
        if index % 50 == 0:
            print(json.dumps({'archivesProcessed': index + 1, 'archiveFailures': len(failures)}), flush=True)
    records = [record for sample in samples for record in sample['records']]
    recipes = collections.Counter()
    for sample in samples:
        for recipe in sample['recipes']:
            recipes[(recipe['version'], recipe['type'])] += recipe['count']
    unresolved = collections.Counter((record['className'], record.get('error', '')) for record in records if record['status'] != 'decoded')
    report = {'schema': 'FusionCorpusSemanticInventory/1', 'scope': 'Read-only research decoding of saved corpus Design records; structural byte accounting does not prove complete field semantics, independent writing, or target application acceptance', 'inventorySha256': hashlib.sha256((BASE.parent / 'CorpusInventory.json').read_bytes()).hexdigest(), 'reflectionSha256': hashlib.sha256(API['SCHEMA_PATH'].read_bytes()).hexdigest(), 'samples': samples, 'archiveFailures': failures}
    raw = (json.dumps(report, indent=2) + '\n').encode()
    compressed = lzma.compress(raw, preset=9)
    (BASE / 'Inventory.json.xz').write_bytes(compressed)
    summary = {'schema': report['schema'], 'scope': report['scope'], 'archives': len(samples), 'archiveFailureCount': len(failures), 'records': len(records), 'counts': dict(collections.Counter(record['status'] for record in records)), 'decodedPayloadBytes': sum(record['payloadBytes'] for record in records if record['status'] == 'decoded'), 'totalPayloadBytes': sum(record['payloadBytes'] for record in records), 'fullyDecodedArchives': sum(all(record['status'] == 'decoded' for record in sample['records']) for sample in samples), 'unresolvedClasses': [{'className': name, 'error': error, 'records': count} for (name, error), count in unresolved.most_common()], 'evidence': 'Inventory.json.xz', 'rawSha256': hashlib.sha256(raw).hexdigest(), 'compressedSha256': hashlib.sha256(compressed).hexdigest(), 'archiveFailures': failures}
    summary['recipes'] = [{'version': version, 'type': kind, 'count': count} for (version, kind), count in sorted(recipes.items())]
    (BASE / 'Summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({key: value for key, value in summary.items() if key not in ('unresolvedClasses', 'archiveFailures')}), flush=True)


if __name__ == '__main__':
    main()
