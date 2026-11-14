import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import Probe

if __name__ == '__main__':
    name, member, start = sys.argv[1], sys.argv[2], int(sys.argv[3])
    data = Probe.members(name)[member]
    tail = data[start:]
    head = data[:start]
    print('length', len(data), 'tail', len(tail))
    print('tail equals head prefix', tail == head[:len(tail)])
    index = head.find(tail[:64])
    print('first 64 tail bytes found in head at', index)
    floats = struct.unpack_from('<16f', tail)
    print('tail floats', [round(value, 4) for value in floats])
    zero = sum(1 for byte in tail if byte == 0)
    print('zero bytes', zero)
