import collections
import io
import re
import sys
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from PackageSpy import ROOT, ReadBundle

MASK = re.compile(r'[0-9A-Fa-f]{8}-[0-9A-Fa-f-]{27}|\d+')


def main():
    model = ReadBundle((ROOT / sys.argv[1]).read_bytes())
    entry = model.Documents[int(sys.argv[2])]
    shapes = collections.Counter()
    with zipfile.ZipFile(io.BytesIO(entry.DataValue)) as outer:
        for info in outer.infolist():
            if info.filename.startswith('OGS.BlobFolder/'):
                continue
            shapes[MASK.sub('N', info.filename)] += 1
    for key, count in sorted(shapes.items()):
        print(count, key)


if __name__ == '__main__':
    main()
