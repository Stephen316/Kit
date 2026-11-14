import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from PackageSpy import ROOT, ReadBundle, packages

HEX = re.compile(r'[0-9A-Fa-f]{8}-[0-9A-Fa-f-]{27}')


def shape(name):
    return re.sub(r'\b[0-9a-f]{11}(_png)?\b', 'NAME', HEX.sub('UUID', name))


def main():
    model = ReadBundle((ROOT / sys.argv[1]).read_bytes())
    entry = model.Documents[int(sys.argv[2])]
    for _, inner, _ in packages(entry.DataValue):
        shapes = {}
        for info in inner.infolist():
            key = shape(info.filename)
            shapes.setdefault(key, []).append(info.file_size)
        for key, sizes in shapes.items():
            print(len(sizes), key, min(sizes), max(sizes))
        for info in inner.infolist():
            parts = info.filename.split('/')
            if len(parts) == 3 and parts[1] == 'Resources' or parts[-1] == 'core.xml' and 'Resources' in parts:
                text = inner.read(info).decode('utf-8', 'replace')
                print(shape(info.filename), ' '.join(HEX.sub('UUID', text).split())[:400])
                break


if __name__ == '__main__':
    main()
