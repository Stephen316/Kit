import struct
import sys


def tokens(data, start=0):
    pos = start
    out = []
    while pos < len(data):
        if pos + 4 <= len(data):
            count = struct.unpack_from('<I', data, pos)[0]
            if 0 < count < 4096 and pos + 4 + 2 * count <= len(data):
                raw = data[pos + 4: pos + 4 + 2 * count]
                try:
                    text = raw.decode('utf-16-le')
                    if all(32 <= ord(ch) < 0xFFFE for ch in text) and (count > 1 or text.isprintable()):
                        out.append((pos, 'U16', text))
                        pos += 4 + 2 * count
                        continue
                except UnicodeDecodeError:
                    pass
            if 0 < count < 4096 and pos + 4 + count <= len(data):
                raw = data[pos + 4: pos + 4 + count]
                if all(32 <= b < 127 for b in raw):
                    out.append((pos, 'A', raw.decode('ascii')))
                    pos += 4 + count
                    continue
            out.append((pos, 'u32', count))
            pos += 4
            continue
        out.append((pos, 'byte', data[pos]))
        pos += 1
    return out


def show(data, start=0, limit=None):
    for pos, kind, value in tokens(data, start)[:limit]:
        print(f'{pos:6d} {kind:4s} {value!r}')


if __name__ == '__main__':
    show(open(sys.argv[1], 'rb').read(), int(sys.argv[2]) if len(sys.argv) > 2 else 0)
