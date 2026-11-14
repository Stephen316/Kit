import collections
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import Probe
import convert.formats.Fusion.GraphicsCodec.Nodes.XferLodsMut as LodsModule
from convert.formats.Fusion.GraphicsCodec.Nodes.XferPayloadMut import XferPayloadMut

kinds = collections.Counter()


def lod(State, Value):
    start = State.Position
    XferPayloadMut(State, None)
    mask = State.Integer(None)
    kind = State.Integer(None) if mask else None
    kinds[(mask, kind)] += 1
    if kind not in (None, 0, 6):
        print('LOD', start, 'mask', hex(mask), 'type', kind, 'next', State.Payload[State.Position:State.Position + 96].hex(' '))
    State.Position = start
    return original(State, Value)


original = LodsModule.XferLodMut
LodsModule.XferLodMut = lod

if __name__ == '__main__':
    for name in sys.argv[1:]:
        kinds.clear()
        found = Probe.members(name)
        state = Probe.scene(found)
        try:
            Probe.XferWorldMut(state, None, True)
            print(name, 'decoded', state.Position, 'of', len(found['world']))
        except Exception as error:
            print(name, 'error', error, 'at', state.Position)
        print(' ', dict(kinds))
