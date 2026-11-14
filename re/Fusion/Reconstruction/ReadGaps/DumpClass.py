import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from ExampleRecords import records
from TrySchema import CATALOG
from ValueVersions import show


def full(prefix):
    return next(guid for guid in CATALOG.Classes if guid.startswith(prefix.upper()))


def main():
    guid = full(sys.argv[1])
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 160
    print('class', guid)
    show(guid)
    base = max(CATALOG.Classes[guid], key=lambda item: item.SchemaVersion).BaseGuid.upper()
    while base in CATALOG.Classes:
        print('base', base)
        show(base)
        base = max(CATALOG.Classes[base], key=lambda item: item.SchemaVersion).BaseGuid.upper()
    count = 0
    for name, segment, meta, span, payload in records(guid):
        versions = {row.ClassGuid.upper(): row.SchemaVersion for row in meta.Classes}
        print(name[-24:], segment, span.ObjectId, 'v', versions[guid], len(payload))
        print('  ', payload[:width].hex())
        count += 1
        if count >= limit:
            break


if __name__ == '__main__':
    main()
