import collections
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from CacheSpy import scene, where

import convert.formats.Fusion.GraphicsCodec.Schema.GlobalVersions as Globals
from convert.formats.Fusion.GraphicsCodec.ReadGraphics import ReadGraphics
from convert.formats.Fusion.GraphicsCodec.Wire.SceneWire import SceneWire

LOG = collections.deque(maxlen=int(sys.argv[2]) if len(sys.argv) > 2 else 12)


def main():
    member = int(sys.argv[1])
    for item in [entry for entry in sys.argv[3:] if '=' in entry]:
        name, value = item.split('=')
        Globals.KGlobalVersions[name] = tuple(sorted(set(Globals.KGlobalVersions.get(name, ())) | {int(value)}))
    import convert.formats.Fusion.GraphicsCodec.Worlds.XferGroupMut as Groups
    from convert.formats.Fusion.GraphicsCodec.Model.State.SceneGlobals import SceneGlobals

    def lenient(state, value):
        count = state.CountValue(None)
        versions = tuple((state.TextValue(None), state.Integer(None)) for _ in range(count))
        return SceneGlobals(versions, state.TextValue(None))

    if 'strict' not in sys.argv:
        Groups.XferGlobalMut = lenient
    source = SceneWire.TextValue

    def spy(self, value):
        start = self.Position
        result = source(self, value)
        LOG.append((start, self.Position, result[:40]))
        return result

    SceneWire.TextValue = spy
    world, mesh, fusion = scene(member)
    try:
        ReadGraphics(world, mesh, fusion)
        print('read')
    except Exception as error:
        print(error, where(error))
    for start, stop, text in LOG:
        print(start, stop, text)
    if LOG:
        last = LOG[-1][1]
        print(last, world[last:last + 160].hex())


if __name__ == '__main__':
    main()
