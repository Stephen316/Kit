import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from CacheSpy import scene, where

import convert.formats.Fusion.GraphicsCodec.Wire.MeshStreams as Mesh
from convert.formats.Fusion.GraphicsCodec.ReadGraphics import ReadGraphics

SPANS = []


def main():
    member = int(sys.argv[1])
    source = Mesh.FinishStreams

    def spy(state):
        family = len(SPANS)
        for stream, ranges in sorted(state.Ranges.items()):
            spans = sorted(ranges)
            gaps = sum(1 for (_, end), (start, _) in zip(spans, spans[1:]) if start != end)
            used = spans[-1][1] if spans else 0
            total = len(state.Inputs[stream])
            SPANS.append((family, stream, len(spans), spans[0][0] if spans else None, gaps, used, total))
        return source(state)

    Mesh.FinishStreams = spy
    world, mesh, fusion = scene(member)
    print('streams', [(item.StreamIndex, len(item.Payload)) for item in mesh], [(item.StreamIndex, len(item.Payload)) for item in fusion])
    try:
        ReadGraphics(world, mesh, fusion)
        print('read')
    except Exception as error:
        print(error, where(error))
    for row in SPANS:
        print('family %d stream %d spans %d first %s gaps %d end %d total %d' % row)


if __name__ == '__main__':
    main()
