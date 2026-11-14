import collections
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from ExampleRecords import documents, segments
from RecordFailures import failures, label
import convert.formats.Fusion.EntityCodec.Values.ReadValueMut as Values

SEEN = collections.Counter()


def main():
    check = Values.CheckReference

    def spy(value, target, catalog):
        try:
            return check(value, target, catalog)
        except ValueError:
            actual = catalog.LocalClasses.get(getattr(value, 'ObjectId', None))
            chain = []
            guid = actual
            while guid and guid in catalog.Classes and len(chain) < 12:
                schema = catalog.Classes[guid]
                chain.append(f'{label(guid)}v{schema.SchemaVersion}{"(opaque)" if schema.IsOpaque else ""}')
                guid = schema.BaseGuid.upper()
            SEEN[(label(target), ' > '.join(chain), guid or '')] += 1
            raise

    Values.CheckReference = spy
    for name, data in documents():
        if 'member 1' in name:
            failures(data)
            rows = {}
            for segment, meta, spans, bulk in segments(data):
                for row in meta.Classes:
                    rows[row.ClassGuid.upper()] = row
    for key, count in SEEN.items():
        print(count, *key)
    for key in SEEN:
        for part in key[1].split(' > '):
            for guid, row in rows.items():
                if label(guid) == part.split('v')[0]:
                    print('meta', part, row.BaseGuid[:8], row.SchemaVersion)


if __name__ == '__main__':
    main()
