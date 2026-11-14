import collections
import hashlib
import json
import runpy
import sys
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
SAMPLE = runpy.run_path(str(BASE / 'SketchTagSamples.py'))
API = SAMPLE['API']
FIELDS = ('version', 'secondaryTagId', 'direction', 'splitSequenceId', 'splitTotalNumber', 'objectOffset20')


def inspect(path, codec):
    archive = API['TOOLS']['read_archive'](path)
    codec.classes = {item['identifier'].upper(): item for item in archive['classes'].values()}
    continuations = collections.defaultdict(set)
    for record in archive['records']:
        if not record['primary']:
            continuations[record['identity']].add(record['class']['identifier'].upper())
    for record in archive['records']:
        reader = API['TOOLS']['Reader'](record['payload'])
        identifier = record['class']['identifier'].upper()
        stops = continuations[record['identity']] - ({identifier} if not record['primary'] else set())
        groups = codec.groups(identifier, stops)
        codec.read_frame(reader, record['primary'])
        values = codec.read_groups(reader, groups)
        if reader.offset != len(reader.data):
            raise ValueError('Trailing payload')
        for field, tag in SAMPLE['tags'](values):
            yield {'path': str(path.relative_to(ROOT)), 'entityId': record['identity'], 'className': codec.schema.get(identifier, {}).get('name', ''), 'field': field, 'tag': tag}


def main():
    source = BASE.parent / 'CorpusInventory.json'
    inventory = json.loads(source.read_text())
    codec = API['GraphCodec']({'classes': {}})
    counts = {name: collections.Counter() for name in FIELDS}
    pairs, versions = collections.Counter(), collections.Counter()
    examples, wildcards, anomalies, errors = {}, {}, [], []
    nontrivial_archives = set()
    total = 0
    for index, entry in enumerate(inventory['files']):
        try:
            for example in inspect(ROOT / entry['path'], codec):
                tag = example['tag']
                total += 1
                for field in FIELDS:
                    counts[field][tag[field]] += 1
                pair = tag['splitSequenceId'], tag['splitTotalNumber']
                pairs[pair] += 1
                versions[(tag['version'], *pair)] += 1
                if pair != (1, 1):
                    nontrivial_archives.add(entry['path'])
                    examples.setdefault(pair, example)
                if tag['direction'] == (1 << 32) - 1:
                    wildcards.setdefault(entry['path'], example)
                if not 1 <= pair[0] <= pair[1]:
                    anomalies.append(example)
        except Exception as error:
            errors.append({'path': entry['path'], 'error': repr(error)})
        if index % 100 == 0:
            print(json.dumps({'archivesProcessed': index + 1, 'tags': total}), flush=True)
    result = {'schema': 'FusionSketchSplitSamples/1', 'scope': 'Read-only saved corpus decoding; no production reader or local tests executed', 'inventorySha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'archives': len(inventory['files']), 'tagValues': total, 'archiveFailures': errors, 'fieldDistributions': {field: [{'value': value, 'count': count} for value, count in sorted(distribution.items())] for field, distribution in counts.items()}, 'splitPairs': [{'sequenceId': pair[0], 'totalNumber': pair[1], 'count': count} for pair, count in sorted(pairs.items())], 'versionSplitPairs': [{'version': key[0], 'sequenceId': key[1], 'totalNumber': key[2], 'count': count} for key, count in sorted(versions.items())], 'nontrivialArchives': sorted(nontrivial_archives), 'outsideOneBasedRange': anomalies, 'examples': [examples[pair] for pair in sorted(examples)], 'wildcardExamples': [wildcards[path] for path in sorted(wildcards)]}
    (BASE / 'SketchSplitSamples.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key not in ('examples', 'versionSplitPairs', 'nontrivialArchives', 'wildcardExamples')}), flush=True)


if __name__ == '__main__':
    main()
