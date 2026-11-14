"""Report the classes that stitch_hint and vertedge system attributes point at."""
import collections
import json
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))

import AsmScan  # noqa: E402

KINDS = ('stitch_hint-sys-attrib', 'vertedge-sys-attrib')


def main():
    inventory = json.loads((HERE / 'Inventory.json').read_text())
    paths = sorted({item['path'] for item in inventory if any(name.split(':', 1)[1] in KINDS for name in item.get('names', {}))})
    seen = collections.Counter()
    for path in paths:
        with zipfile.ZipFile(ROOT / path) as archive:
            for member in archive.namelist():
                if not member.endswith(('.smb', '.smbh')):
                    continue
                _, _, records = AsmScan.records(archive.read(member))
                for record in records:
                    if record['name'] not in KINDS:
                        continue
                    refs = [value for tag, value in record['tokens'] if tag == 12]
                    names = [records[value]['name'] if 0 <= value < len(records) else str(value) for value in refs]
                    ints = [value for tag, value in record['tokens'] if tag == 4]
                    seen[(record['name'], tuple(names[1:3]), tuple(sorted(set(names[3:]))), len(record['tokens']), tuple(ints[1:2]))] += 1
    for key, count in sorted(seen.items()):
        print(count, key)


if __name__ == '__main__':
    main()
