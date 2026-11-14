import struct
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from CacheSpy import scene


class Reader:
    def __init__(self, data, position, verbose):
        self.data = data
        self.position = position
        self.verbose = verbose
        self.depth = 0

    def take(self, form):
        value = struct.unpack_from(form, self.data, self.position)[0]
        self.position += struct.calcsize(form)
        return value

    def text(self):
        length = self.take('<I')
        if length > 4096:
            raise ValueError(f'bad text length {length} at {self.position - 4}')
        value = self.data[self.position:self.position + 2 * length].decode('utf-16le')
        self.position += 2 * length
        return value

    def say(self, *items):
        if self.verbose:
            print('  ' * self.depth + ' '.join(str(item) for item in items))

    def path(self):
        self.text()
        handle = self.text()
        count = self.take('<I')
        entries = [(self.take('<I'), self.take('>Q')) for _ in range(count)]
        self.say('path', handle, entries)

    def attribute(self, rules):
        name = self.text()
        priority = self.take('<i')
        ties = self.take('<B')
        self.say('attr', name, priority, ties, 'at', self.position)
        rules[name](self)

    def child(self, rules):
        specific = self.take('<B')
        flags = self.take('<I')
        removed = self.take('<I')
        appends = [self.take('<I') for _ in range(self.take('<I'))]
        count = self.take('<i')
        self.say('child', specific, hex(flags), removed, appends, count)
        self.depth += 1
        for _ in range(count):
            self.attribute(rules)
        self.depth -= 1
        if specific:
            self.say('apply', [self.take('<I') for _ in range(self.take('<I'))])

    def tail(self, rules):
        if self.take('<B'):
            target = ('external', self.take('>Q'), self.take('<I'))
        else:
            target = ('node', self.text())
        count = self.take('<i')
        self.say('set tail', target, 'children', count)
        self.depth += 1
        for _ in range(count):
            self.child(rules)
        self.depth -= 1


def main():
    member = int(sys.argv[1])
    start = int(sys.argv[2])
    limit = int(sys.argv[3])
    world, _, _ = scene(member)
    reader = Reader(world, start, True)
    reader.tail(RULES)
    print('end', reader.position, world[reader.position:reader.position + limit].hex())


def transform(reader):
    reader.take('<16f')
    reader.take('<B')
    override(reader)


def visibility(reader):
    reader.say('visible', reader.take('<B'))
    override(reader)


def inactive(reader):
    reader.say('visible', reader.take('<B'))
    if reader.take('<B'):
        reader.path()


def override(reader):
    if reader.take('<B'):
        reader.path()
    if reader.take('<B'):
        target = ('external', reader.take('>Q'), reader.take('<I'))
    else:
        target = ('node', reader.text())
    reader.say('target', target)
    nested = reader.take('<I')
    reader.say('nested', nested)
    reader.depth += 1
    for _ in range(nested):
        reader.child(RULES)
        reader.tail(RULES)
    reader.depth -= 1


RULES = {'OverrideTransformAttribute': transform, 'OverrideVisibilityAttribute': visibility, 'OverrideInActivatedVisibilityAttribute': inactive}


if __name__ == '__main__':
    main()
