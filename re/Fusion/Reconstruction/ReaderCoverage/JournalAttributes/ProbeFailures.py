import collections
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'src'))

from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadEntityNode import ReadEntityNode
from convert.formats.Fusion.BrepCodec.Journal.Reading.ReadModelHead import ReadModelHead
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmName, ReadAsmRecord

KCAUSES = (
    'Unsupported Fusion journal qualified field',
    'Unsupported Fusion journal attribute family',
    'Unsupported Fusion journal entity kind',
)
KMARKS = {'Begin-of-ASM-History-Data', 'End-of-ASM-data', 'End-of-ASM-History-Section', 'delta_state', 'history_stream'}


def scope(report):
    rows = json.loads(Path(report).read_text())['rows']
    return [row['file'] for row in rows if row['status'] != 'pass' and any(cause in row.get('error', '') for cause in KCAUSES)]


def records(payload, history):
    cursor = MetaCursor(payload)
    ReadModelHead(cursor, history)
    index = 0
    while cursor.Offset < len(payload):
        name = ReadAsmName(cursor)
        if name in ('Begin-of-ASM-History-Data', 'End-of-ASM-data', 'End-of-ASM-History-Section'):
            yield index, name, None
            continue
        record = ReadAsmRecord(cursor, name)
        yield index, name, record
        index += 1


def failing(path):
    archive = zipfile.ZipFile(ROOT / path)
    for name in archive.namelist():
        if not (name.endswith('.smbh') or name.endswith('.smb')):
            continue
        payload = archive.read(name)
        try:
            for index, kind, record in records(payload, name.endswith('.smbh')):
                if record is None or kind in KMARKS:
                    continue
                try:
                    ReadEntityNode(record)
                except Exception as error:
                    yield name, index, record, str(error)
        except Exception as error:
            yield name, None, None, 'tokenize: %s' % error


if __name__ == '__main__':
    files = scope(sys.argv[1]) if sys.argv[1].endswith('.json') else sys.argv[1:]
    kinds = collections.Counter()
    examples = {}
    perfile = collections.defaultdict(set)
    for path in files:
        for name, index, record, error in failing(path):
            key = (record.Name if record else None, error)
            kinds[key] += 1
            perfile[key].add(path)
            examples.setdefault(key, []).append((path, name.rsplit('/', 1)[-1], index, record.Tokens if record else None))
    for key, count in kinds.most_common():
        print(count, 'files', len(perfile[key]), key)
        for path, name, index, tokens in examples[key][:2]:
            print('   ', path, name, index, tokens)


def entities(payload, history):
    return [record for index, kind, record in records(payload, history) if record is not None and kind not in KMARKS]
