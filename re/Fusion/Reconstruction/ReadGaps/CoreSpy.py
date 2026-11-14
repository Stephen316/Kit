import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from PackageSpy import ROOT, ReadBundle, packages
from ResourceSpy import HEX, shape

TIME = re.compile(r'\d{4}-\d\d-\d\dT[\d:.]+Z')


def main():
    model = ReadBundle((ROOT / sys.argv[1]).read_bytes())
    entry = model.Documents[int(sys.argv[2])]
    seen = set()
    for _, inner, _ in packages(entry.DataValue):
        for info in inner.infolist():
            key = shape(info.filename)
            if not key.endswith('core.xml') or key in seen:
                continue
            seen.add(key)
            text = inner.read(info).decode('utf-8', 'replace')
            text = TIME.sub('TIME', HEX.sub('UUID', text))
            print(key)
            print('   ', ' '.join(text.split())[:520])


if __name__ == '__main__':
    main()
