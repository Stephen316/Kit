import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
sys.setrecursionlimit(20000)

from ExampleRecords import documents
import convert.formats.Fusion.GraphicsCodec.Wire.MeshStreams as Mesh
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.Auxiliary.Graphics.ReadSceneParts import ReadSceneParts


def main():
    source = Mesh.FinishStreams

    def spy(state):
        for stream, ranges in sorted(state.Ranges.items()):
            used = sum(len(payload) for payload in ranges.values())
            total = len(state.Inputs[stream])
            if used != total:
                tail = state.Inputs[stream][used:]
                last = max(ranges)
                print('  stream', stream, 'used', used, 'total', total, 'ranges', len(ranges), 'last range', last, 'tail head', tail[:24].hex(), 'zeros', tail.count(0), 'of', len(tail))
        return source(state)

    Mesh.FinishStreams = spy
    for name, data in documents():
        if not name.endswith(('member 4', 'member 9')):
            continue
        print(name[-10:])
        try:
            ReadSceneParts(ReadContainer(data).Parts)
        except Exception as error:
            print('  ', error)


if __name__ == '__main__':
    main()
