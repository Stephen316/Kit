import collections
import struct
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from CacheSpy import scene

WINDOW = 60


def text(world, position):
    length = struct.unpack_from('<I', world, position)[0]
    return world[position + 4:position + 4 + 2 * length].decode('utf-16le'), position + 4 + 2 * length


def marker(name):
    encoded = name.encode('utf-16le')
    return struct.pack('<I', len(name)) + encoded


def paths(world):
    shapes = collections.Counter()
    tails = collections.Counter()
    start = 0
    key = marker('PersistentPassiveNodePath')
    while (start := world.find(key, start)) >= 0:
        position = start + len(key)
        handle, position = text(world, position)
        count = struct.unpack_from('<I', world, position)[0]
        position += 4
        entries = []
        for _ in range(count):
            segment = struct.unpack_from('<I', world, position)[0]
            entity = struct.unpack_from('>Q', world, position + 4)[0]
            entries.append((segment, entity))
            position += 12
        flag = world[position]
        position += 1
        if flag:
            entity = struct.unpack_from('>Q', world, position)[0]
            segment = struct.unpack_from('<I', world, position + 8)[0]
            target = ('external', segment, entity)
            position += 12
        else:
            node, position = text(world, position)
            target = ('node', node)
        shapes[(count, target[0], tuple(segment for segment, _ in entries))] += 1
        tails[(target[0], world[position:position + WINDOW].hex())] += 1
        start = position
    return shapes, tails


def follow(world, name, size):
    found = collections.Counter()
    key = marker(name)
    start = 0
    while (start := world.find(key, start)) >= 0:
        found[world[start + len(key):start + len(key) + size].hex()] += 1
        start += len(key)
    return found


def main():
    member = int(sys.argv[1])
    world, _, _ = scene(member)
    shapes, tails = paths(world)
    print('path shapes', dict(shapes))
    print('path tails')
    for (kind, value), count in tails.most_common(10):
        print(' ', count, kind, value)
    for name in sys.argv[2:]:
        print(name)
        for value, count in follow(world, name, 48).most_common(6):
            print(' ', count, value)


if __name__ == '__main__':
    main()
