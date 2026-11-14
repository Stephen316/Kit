import struct
import sys
from pathlib import Path


class Cur:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def take(self, n):
        out = self.data[self.pos:self.pos + n]
        if len(out) != n:
            raise ValueError('truncated at %d' % self.pos)
        self.pos += n
        return out

    def u32(self):
        return struct.unpack('<I', self.take(4))[0]

    def u64(self):
        return struct.unpack('<Q', self.take(8))[0]

    def a(self):
        return self.take(self.u32()).decode('ascii')

    def w(self):
        return self.take(self.u32() * 2).decode('utf-16le')


def root(data):
    c = Cur(data)
    out = [('format', c.a()), ('type', c.a()), ('ext', c.w()), ('title', c.w()), ('desc', c.w()), ('docid', c.w()), ('current', c.w())]
    magic = c.u32()
    out.append(('magic', magic))
    if magic == 1234:
        out += [('version', c.u32()), ('sw0', c.u32()), ('sw1', c.u32())]
    else:
        out += [('version', c.u32())]
    n = c.u32()
    out.append(('modules', [(c.a(), c.u32()) for _ in range(n)]))
    n = c.u32()
    out.append(('vguids', [c.w() for _ in range(n)]))
    out.append(('refbyte', c.take(1).hex()))
    n = c.u32()
    refs = []
    for _ in range(n):
        r = {'role': c.w(), 'unres': c.w(), 'src': c.w(), 'tgt': c.w(), 'local': c.w(), 'words': [c.u32() for _ in range(4)]}
        m = c.u32()
        r['props'] = [(c.w(), c.w()) for _ in range(m)]
        refs.append(r)
    out.append(('refs', refs))
    out.append(('active', c.w()))
    n = c.u32()
    assets = []
    for _ in range(n):
        assets.append((c.w(), c.u32(), c.take(1).hex()))
    out.append(('assets', assets))
    out.append(('name', c.w()))
    if c.pos < len(data):
        out.append(('label', c.w()))
    out.append(('tail', data[c.pos:].hex()))
    return out


def asset(data):
    c = Cur(data)
    out = [('name', c.w()), ('id', c.w()), ('rev', c.w()), ('type', c.a()), ('version', c.u32())]
    n = c.u32()
    out.append(('modules', [(c.a(), c.u32()) for _ in range(n)]))
    out.append(('kind', c.a()))
    out.append(('word', c.u32()))
    out.append(('byte', c.take(1).hex()))
    n = c.u32()
    out.append(('links', [(c.w(), c.w(), c.w()) for _ in range(n)]))
    out.append(('w1', c.u32()))
    out.append(('next', c.u32()))
    n = c.u32()
    out.append(('segments', [(c.u32(), c.a(), c.a()) for _ in range(n)]))
    out.append(('tail', data[c.pos:].hex()))
    return out


if __name__ == '__main__':
    which = sys.argv[1]
    data = Path(sys.argv[2]).read_bytes()
    for key, value in (root(data) if which == 'root' else asset(data)):
        print(key, value)
