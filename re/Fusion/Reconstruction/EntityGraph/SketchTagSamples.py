import collections
import hashlib
import json
import runpy
import sys
from pathlib import Path

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
API = runpy.run_path(str(BASE / 'DecodeGraph.py'))


def tags(value, field=''):
    if isinstance(value, dict):
        if 'objectOffset20' in value and 'tagId' in value:
            yield field, value
        for key, child in value.items():
            yield from tags(child, f'{field}.{key}' if field else key)
    elif isinstance(value, (tuple, list)):
        for index, child in enumerate(value):
            yield from tags(child, f'{field}[{index}]')


def inspect(path, codec):
    archive = API['TOOLS']['read_archive'](path)
    codec.classes = {item['identifier'].upper(): item for item in archive['classes'].values()}
    continuations = collections.defaultdict(set)
    for record in archive['records']:
        if not record['primary']:
            continuations[record['identity']].add(record['class']['identifier'].upper())
    counts = collections.Counter()
    examples = {}
    failures = 0
    for record in archive['records']:
        reader = API['TOOLS']['Reader'](record['payload'])
        identifier = record['class']['identifier'].upper()
        try:
            stops = continuations[record['identity']] - ({identifier} if not record['primary'] else set())
            groups = codec.groups(identifier, stops)
            codec.read_frame(reader, record['primary'])
            values = codec.read_groups(reader, groups)
            if reader.offset != len(reader.data):
                raise ValueError('Trailing payload')
            for field, tag in tags(values):
                flag = tag['objectOffset20']
                counts[flag] += 1
                if flag and flag not in examples:
                    examples[flag] = {'path': str(path.relative_to(ROOT)), 'entityId': record['identity'], 'className': codec.schema.get(identifier, {}).get('name', ''), 'field': field, 'tag': tag}
        except (ValueError, KeyError, UnicodeError, RecursionError, OverflowError):
            failures += 1
    return counts, examples, failures


def main():
    source = BASE.parent / 'CorpusInventory.json'
    inventory = json.loads(source.read_text())
    codec = API['GraphCodec']({'classes': {}})
    counts = collections.Counter()
    examples, errors = {}, []
    failed_records = 0
    for index, entry in enumerate(inventory['files']):
        try:
            values, found, failures = inspect(ROOT / entry['path'], codec)
            counts.update(values)
            failed_records += failures
            for flag, example in found.items():
                examples.setdefault(flag, example)
        except Exception as error:
            errors.append({'path': entry['path'], 'error': repr(error)})
        if index % 100 == 0:
            print(json.dumps({'archivesProcessed': index + 1, 'tags': sum(counts.values())}), flush=True)
    result = {'schema': 'FusionSketchTagSamples/1', 'scope': 'Read-only corpus decoding; one example per nonzero discriminator value; only fully decoded records counted', 'inventorySha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'archives': len(inventory['files']), 'unresolvedRecords': failed_records, 'archiveFailures': errors, 'distribution': [{'value': flag, 'hex': hex(flag), 'count': count} for flag, count in sorted(counts.items())], 'examples': [examples[flag] for flag in sorted(examples)]}
    (BASE / 'SketchTagSamples.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'examples'}), flush=True)


if __name__ == '__main__':
    main()
