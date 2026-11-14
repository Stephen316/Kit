import runpy
import sys
import zipfile
from pathlib import Path

SCAN = runpy.run_path(str(Path(__file__).with_name('AsmScan.py')))


def short(tokens, limit):
    out = []
    for tag, value in tokens[:limit]:
        if isinstance(value, float):
            out.append('%d:%.6g' % (tag, value))
        elif isinstance(value, tuple):
            out.append('%d:(%s)' % (tag, ','.join('%.6g' % v for v in value)))
        elif isinstance(value, bytes):
            out.append('%d:<%d bytes>' % (tag, len(value)))
        else:
            out.append('%d:%r' % (tag, value))
    return ' '.join(out)


def main(path, member, names, limit):
    with zipfile.ZipFile(path) as archive:
        data = archive.read([n for n in archive.namelist() if n.endswith(member)][0])
    header, rows = SCAN['records'](data)
    wanted = names.split(',')
    for index, (name, tokens) in enumerate(rows):
        if name in wanted or 'all' in wanted:
            print(index, name, len(tokens), short(tokens, limit))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]))
