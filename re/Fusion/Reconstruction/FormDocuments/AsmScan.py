import collections
import struct
import sys
import zipfile


def tokens(data, start):
    offset = start
    while offset < len(data):
        tag = data[offset]
        offset += 1
        if tag in (4, 12, 21, 23):
            value = struct.unpack_from('<q', data, offset)[0]
            offset += 8
        elif tag == 6:
            value = struct.unpack_from('<d', data, offset)[0]
            offset += 8
        elif tag in (7, 13, 14):
            size = data[offset]
            value = data[offset + 1:offset + 1 + size].decode('latin1')
            offset += 1 + size
        elif tag == 8:
            size = struct.unpack_from('<H', data, offset)[0]
            value = data[offset + 2:offset + 2 + size].decode('latin1')
            offset += 2 + size
        elif tag == 9:
            size = struct.unpack_from('<I', data, offset)[0]
            value = data[offset + 4:offset + 4 + size].decode('latin1')
            offset += 4 + size
        elif tag == 18:
            size = struct.unpack_from('<q', data, offset)[0]
            value = data[offset + 8:offset + 8 + size]
            offset += 8 + size
        elif tag in (19, 20):
            value = struct.unpack_from('<3d', data, offset)
            offset += 24
        elif tag == 22:
            value = struct.unpack_from('<2d', data, offset)
            offset += 16
        elif tag in (10, 11, 15, 16, 17):
            value = None
        else:
            raise ValueError('tag %d at %d' % (tag, offset - 1))
        yield tag, value, offset


def records(data):
    if data[:15] != b'ASM BinaryFile8':
        raise ValueError('header')
    offset = 15 + 32
    stream = tokens(data, offset)
    header = [next(stream) for _ in range(6)]
    result = []
    name, current = [], []
    for tag, value, end in stream:
        if not current and tag in (13, 14) and (not name or name[-1][0] == 14):
            name.append((tag, value))
            if tag == 13:
                current = ['-'.join(v for _, v in name)]
                name = []
                if current[0] in ('End-of-ASM-data',):
                    result.append((current[0], []))
                    current = []
            continue
        if tag == 17:
            result.append((current[0], current[1:]))
            current = []
            continue
        current.append((tag, value))
    return header, result


def main(path, member):
    with zipfile.ZipFile(path) as archive:
        names = [n for n in archive.namelist() if n.endswith(member)]
        data = archive.read(names[0])
    header, rows = records(data)
    print('header', header)
    counts = collections.Counter(name for name, _ in rows)
    print(counts)
    tags = collections.Counter(tag for _, row in rows for tag, _ in row)
    print(tags)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
