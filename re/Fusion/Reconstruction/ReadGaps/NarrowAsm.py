import collections
import io
import json
import struct
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(BASE))

from ExampleRecords import documents

WIDE = {4, 12, 21, 23}


def token(data, offset, width):
    tag = data[offset]
    offset += 1
    if tag in WIDE:
        return tag, offset + width
    if tag == 6:
        return tag, offset + 8
    if tag in (7, 13, 14):
        return tag, offset + 1 + data[offset]
    if tag == 8:
        return tag, offset + 2 + struct.unpack_from('<H', data, offset)[0]
    if tag == 18:
        size = struct.unpack_from('<q' if width == 8 else '<i', data, offset)[0]
        return tag, offset + width + size
    if tag in (19, 20):
        return tag, offset + 24
    if tag in (10, 11, 15, 16, 17):
        return tag, offset
    raise ValueError(f'tag {tag} at {offset - 1}')


def walk(data):
    width = int(data[14:15].decode())
    offset = 15 + 4 * width
    tags = collections.Counter()
    names = collections.Counter()
    while offset < len(data):
        tag, end = token(data, offset, width)
        tags[tag] += 1
        if tag in (13, 14):
            names[data[offset + 2:end].decode('ascii')] += 1
        offset = end
    return width, offset == len(data), tags, names


def main():
    report = {}
    for name, data in documents():
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for member in archive.namelist():
                if member.endswith(('.smb', '.smbh')):
                    payload = archive.read(member)
                    try:
                        width, exact, tags, names = walk(payload)
                        row = {'width': width, 'exact': exact, 'tags': dict(sorted(tags.items()))}
                    except Exception as error:
                        row = {'error': str(error)}
                    report.setdefault(member.rsplit('.', 1)[1], []).append(row)
    summary = {kind: collections.Counter(json.dumps({key: value for key, value in row.items() if key != 'tags'}) for row in rows) for kind, rows in report.items()}
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()
