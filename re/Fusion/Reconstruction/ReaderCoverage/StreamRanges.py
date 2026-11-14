import collections
import inspect
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))

import convert.formats.Fusion.GraphicsCodec.Wire.MeshStreams as MeshModule
from convert.formats.Fusion.GraphicsCodec.Model.State.GraphicsStream import GraphicsStream
from convert.formats.Fusion.GraphicsCodec.ReadGraphics import ReadGraphics

PREFIX = 'FusionAssetName[Active]/OGS.BlobFolder/OGS/DefaultScene/'
calls = []


def transfer(self, stream, offset, length, payload):
    caller = inspect.stack()[1].function
    calls.append((caller, stream, offset, length))
    source = self.Inputs.get(stream, b'')
    data = source[offset:offset + length]
    return data + bytes(length - len(data))


MeshModule.MeshStreams.Transfer = transfer
MeshModule.MeshStreams.Finalize = lambda self: ()

for name in sys.argv[1:]:
    calls.clear()
    archive = zipfile.ZipFile(name)
    members = {info.filename[len(PREFIX):]: archive.read(info.filename) for info in archive.infolist() if info.filename.startswith(PREFIX) and not info.filename.endswith('/')}
    print('==', name, {key: len(value) for key, value in members.items()})
    streams = tuple(GraphicsStream(int(key[-3:]), value) for key, value in members.items() if key.startswith('stream_mesh_'))
    fusion = tuple(GraphicsStream(int(key[-3:]), value) for key, value in members.items() if key.startswith('Fusion_mesh_'))
    try:
        ReadGraphics(members['world'], streams, fusion)
    except Exception as error:
        print('error', error)
    extent = collections.defaultdict(int)
    count = collections.Counter()
    for caller, stream, offset, length in calls:
        extent[(caller, stream)] = max(extent[(caller, stream)], offset + length)
        count[(caller, stream)] += 1
    for key in sorted(extent):
        print(' ', key, 'transfers', count[key], 'max end', extent[key])
    for caller in ('XferVerticesMut', 'XferIndicesMut'):
        spans = sorted((offset, offset + length) for c, stream, offset, length in calls if c == caller)
        print(' ', caller, 'first spans', spans[:6], 'last', spans[-3:])
