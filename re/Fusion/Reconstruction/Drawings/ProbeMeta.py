import json
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


def meta(data):
    c = Cur(data)
    head = {'kind': c.a(), 'segment': c.u32(), 'namespace': c.w(), 'magic': c.u32(), 'version': c.u32(), 'words': [c.u32(), c.u32()], 'repeated': c.a(), 'storage': c.a(), 'storage_words': [c.u32(), c.u32()]}
    classes = []
    for _ in range(c.u32()):
        row = {'guid': c.a(), 'base': c.a(), 'version': c.u32(), 'space': c.a()}
        row['ids'] = [c.u64() for _ in range(c.u32())]
        classes.append(row)
    roots = [c.u64() for _ in range(c.u32())]
    primary = [(c.u64(), c.u64()) for _ in range(c.u32())]
    cont = [(c.u64(), c.u64()) for _ in range(c.u32())]
    nxt = c.u64()
    reserved = c.u32()
    props = [(c.a(), c.u32()) for _ in range(c.u32())]
    return {'head': head, 'classes': classes, 'roots': roots, 'primary': primary, 'cont': cont, 'next': nxt, 'reserved': reserved, 'props': props, 'tail': len(data) - c.pos}


if __name__ == '__main__':
    value = meta(Path(sys.argv[1]).read_bytes())
    names = {}
    if len(sys.argv) > 2:
        schema = json.loads(Path(sys.argv[2]).read_text())
        names = {row['identifier'].upper(): (row['name'], row['version']) for row in schema['metatypes']}
    print(json.dumps(value['head']))
    for index, row in enumerate(value['classes']):
        print(256 + index, row['guid'], row['base'][:8], row['version'], row['space'], names.get(row['guid'].upper()), row['ids'])
    print('roots', value['roots'])
    print('primary', len(value['primary']), 'cont', value['cont'], 'next', value['next'], 'reserved', value['reserved'], 'props', value['props'], 'tail', value['tail'])
