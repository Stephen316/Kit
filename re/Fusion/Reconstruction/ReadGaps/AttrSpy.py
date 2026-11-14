import collections
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
sys.setrecursionlimit(20000)

from ExampleRecords import documents
import convert.formats.Fusion.GraphicsCodec.Fields.XferSetBaseMut as SetBase
from convert.formats.Fusion.GraphicsCodec.Schema.AttrRules import KAttrRules
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

SAMPLES = collections.defaultdict(list)
NAME = re.compile(rb'(?:[\x08-\x40]\x00\x00\x00)((?:[A-Za-z]\x00){8,64})')


def main():
    source = SetBase.XferAttrMut
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 3

    def spy(state, value):
        start = state.Position
        payload = state.Payload
        length = int.from_bytes(payload[start:start + 4], 'little')
        name = payload[start + 4:start + 4 + 2 * length].decode('utf-16le', 'replace')
        if name not in KAttrRules and len(SAMPLES[name]) < limit:
            body = start + 4 + 2 * length
            following = [(match.start() - body, match.group(1).decode('utf-16le')) for match in NAME.finditer(payload, body, body + 600)][:3]
            SAMPLES[name].append((payload[body:body + 96].hex(), following))
        return source(state, value)

    SetBase.XferAttrMut = spy
    for name, data in documents():
        if 'example1' not in name:
            continue
        try:
            ReadDocument(data)
        except Exception as error:
            pass
    for name, rows in SAMPLES.items():
        print(name)
        for body, following in rows:
            print('  ', body)
            print('   next', following)


if __name__ == '__main__':
    main()
