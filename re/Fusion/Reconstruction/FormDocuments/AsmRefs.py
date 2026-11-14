import runpy
import sys
import zipfile
from pathlib import Path

SCAN = runpy.run_path(str(Path(__file__).with_name('AsmScan.py')))


def walk(rows, counted_refs):
    table = []
    links = []
    for index, (name, tokens) in enumerate(rows):
        stack = []
        for position, (tag, value) in enumerate(tokens):
            if tag == 15:
                stack.append(None)
            elif tag == 16:
                stack.pop()
            elif tag == 13 and stack and stack[-1] is None:
                stack[-1] = value
                if value == 'ref':
                    target = tokens[position + 1][1]
                    links.append((index, name, target, table[target] if 0 <= target < len(table) else None))
                    if counted_refs:
                        table.append((index, name, 'ref'))
                else:
                    table.append((index, name, value))
    return table, links


def main(path, member, counted):
    with zipfile.ZipFile(path) as archive:
        data = archive.read([n for n in archive.namelist() if n.endswith(member)][0])
    header, rows = SCAN['records'](data)
    table, links = walk(rows, counted == '1')
    for number, entry in enumerate(table):
        print('def', number, entry)
    for link in links:
        print('ref', link)


if __name__ == '__main__':
    main(*sys.argv[1:4])
