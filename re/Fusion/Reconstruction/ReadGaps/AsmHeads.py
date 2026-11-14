import collections
import io
import struct
import sys
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from Sweep import ROOT, tracked


def head(payload):
    if not payload.startswith(b'ASM BinaryFile'):
        return None
    width = int(payload[14:15])
    offset = 15 + 4 * width
    numbers = struct.unpack_from('<4q' if width == 8 else '<4i', payload, 15)
    values = []
    for _ in range(6):
        tag = payload[offset]
        if tag == 7:
            offset += 2 + payload[offset + 1]
        elif tag == 6:
            values.append(struct.unpack_from('<d', payload, offset + 1)[0])
            offset += 9
        else:
            return ('bad token', tag)
    return width, numbers[0], numbers[3], tuple(values)


def members(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for name in archive.namelist():
            inner = archive.read(name)
            if name.lower().endswith('.f3d'):
                yield from members(inner)
            elif name.endswith(('.smb', '.smbh')):
                yield name.rsplit('.', 1)[1], inner


def main():
    found = collections.Counter()
    files = collections.defaultdict(set)
    for name in tracked():
        if not name.endswith(('.f3d', '.f3z')):
            continue
        try:
            for kind, payload in members((ROOT / name).read_bytes()):
                key = (kind, head(payload))
                found[key] += 1
                files[key].add(name)
        except Exception as error:
            found[('error', str(error)[:40])] += 1
    for key, count in sorted(found.items(), key=lambda item: -item[1]):
        print(count, len(files[key]), key, sorted(files[key])[0] if len(files[key]) < 4 else '')


if __name__ == '__main__':
    main()
