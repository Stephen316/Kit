import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import Probe
import convert.formats.Fusion.GraphicsCodec.Wire.MeshStreams as MeshModule
from convert.formats.Fusion.GraphicsCodec.ReadGraphics import ReadGraphics
from convert.formats.Fusion.GraphicsCodec.Model.State.GraphicsStream import GraphicsStream

reports = []


def finalize(self):
    for stream, ranges in sorted(self.Ranges.items()):
        spans = sorted(ranges)
        end = 0
        gaps = []
        for start, stop in spans:
            if start != end:
                gaps.append((end, start))
            end = max(end, stop)
        total = len(self.Inputs.get(stream, b''))
        reports.append({'stream': stream, 'spans': len(spans), 'covered_end': end, 'length': total, 'gaps': gaps[:5], 'last': spans[-3:]})
    return ()


MeshModule.MeshStreams.Finalize = finalize

if __name__ == '__main__':
    for name in sys.argv[1:]:
        reports.clear()
        found = Probe.members(name)
        streams = tuple(GraphicsStream(int(key[-3:]), value) for key, value in found.items() if key.startswith('stream_mesh_'))
        fusion = tuple(GraphicsStream(int(key[-3:]), value) for key, value in found.items() if key.startswith('Fusion_mesh_'))
        try:
            ReadGraphics(found['world'], streams, fusion)
        except Exception as error:
            print('error', error)
        print(Path(name).name[:12], {key: len(value) for key, value in found.items()})
        for row in reports:
            print('  ', row)
