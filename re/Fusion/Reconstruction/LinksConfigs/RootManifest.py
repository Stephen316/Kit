import json
import struct
import sys


class Cur:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def u32(self):
        value = struct.unpack_from('<I', self.data, self.pos)[0]
        self.pos += 4
        return value

    def u8(self):
        value = self.data[self.pos]
        self.pos += 1
        return value

    def a(self):
        n = self.u32()
        value = self.data[self.pos:self.pos + n].decode('ascii')
        self.pos += n
        return value

    def w(self):
        n = self.u32()
        value = self.data[self.pos:self.pos + 2 * n].decode('utf-16-le')
        self.pos += 2 * n
        return value


def parse(data):
    c = Cur(data)
    out = {'format': [c.a(), c.a(), c.w()], 'title': c.w(), 'description': c.w(), 'ids': [c.w(), c.w()]}
    out['magic_version'] = [c.u32(), c.u32()]
    out['software'] = [c.u32(), c.u32()]
    out['versions'] = [(c.a(), c.u32()) for _ in range(c.u32())]
    out['ancestry'] = [c.w() for _ in range(c.u32())]
    out['links_flag'] = c.u8()
    links = []
    if out['links_flag']:
        for _ in range(c.u32()):
            link = {'pos': c.pos, 'id': c.w(), 'source': c.w(), 'cache': c.w(), 'xref': c.w()}
            link['words'] = [c.u32(), c.u32(), c.u32(), c.u32()]
            link['props'] = [(c.w(), c.w()) for _ in range(c.u32())]
            links.append(link)
    out['links'] = links
    out['asset_id'] = c.w()
    out['assets'] = [(c.w(), c.u32()) for _ in range(c.u32())]
    out['terminal_flag'] = c.u8()
    rest = []
    while c.pos < len(data):
        rest.append(c.w())
    out['terminal'] = rest
    return out


if __name__ == '__main__':
    print(json.dumps(parse(open(sys.argv[1], 'rb').read()), indent=1))
