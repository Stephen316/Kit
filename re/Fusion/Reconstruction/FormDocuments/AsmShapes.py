import collections
import glob
import json
import runpy
import sys
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
SCAN = runpy.run_path(str(BASE / 'AsmScan.py'))


def all_records(data):
    offset = 15 + 32
    stream = SCAN['tokens'](data, offset)
    for _ in range(6):
        next(stream)
    rows, name, current = [], [], None
    for tag, value, end in stream:
        if current is None:
            if tag in (13, 14):
                name.append(value)
                if tag == 13:
                    current = ['-'.join(name), []]
                    name = []
                    if current[0] in ('End-of-ASM-data', 'Begin-of-ASM-History-Data', 'End-of-ASM-History-Section'):
                        rows.append((current[0], []))
                        current = None
                continue
            raise ValueError('unexpected tag outside record %d' % tag)
        if tag == 17:
            rows.append((current[0], current[1]))
            current = None
            continue
        current[1].append((tag, value))
    return rows


def skeleton(tokens):
    out = []
    for tag, value in tokens:
        if tag == 6:
            out.append('d')
        elif tag == 4:
            out.append('i')
        elif tag == 12:
            out.append('p')
        elif tag in (13, 7, 8):
            out.append(repr(value)[:24] if tag == 13 else 's%d' % tag)
        elif tag == 21:
            out.append('e%d' % value)
        else:
            out.append(str(tag))
    collapsed = []
    for item in out:
        if collapsed and collapsed[-1][0] == item:
            collapsed[-1][1] += 1
        else:
            collapsed.append([item, 1])
    return ' '.join(a if n == 1 else '%s*%d' % (a, n) for a, n in collapsed)


def main(names):
    wanted = names.split(',')
    shapes = collections.defaultdict(collections.Counter)
    for path in sorted(glob.glob(str(ROOT / 're/Fusion/LocalOracle/TSpline*/*.f3d'))):
        with zipfile.ZipFile(path) as archive:
            for member in archive.namelist():
                if member.endswith(('.smb', '.smbh')):
                    for name, tokens in all_records(archive.read(member)):
                        if name in wanted:
                            shapes[name][skeleton(tokens)] += 1
    for name, counter in shapes.items():
        print('==', name, len(counter))
        for shape, count in counter.most_common(12):
            print(count, shape[:1500])


if __name__ == '__main__':
    main(sys.argv[1])
