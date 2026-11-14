import runpy
import sys
import zipfile
from pathlib import Path

SCAN = runpy.run_path(str(Path(__file__).with_name('AsmScan.py')))
DUMP = runpy.run_path(str(Path(__file__).with_name('AsmDump.py')))


def main(path, member, name, which):
    with zipfile.ZipFile(path) as archive:
        data = archive.read([n for n in archive.namelist() if n.endswith(member)][0])
    header, rows = SCAN['records'](data)
    found = [tokens for row, tokens in rows if row == name]
    tokens = found[int(which)]
    index = next(i for i, (tag, value) in enumerate(tokens) if tag == 8)
    print('before', DUMP['short'](tokens[index - 40:index], 100))
    print('tsm bytes', len(tokens[index][1]))
    print('after', DUMP['short'](tokens[index + 1:], 400))


if __name__ == '__main__':
    main(*sys.argv[1:5])
