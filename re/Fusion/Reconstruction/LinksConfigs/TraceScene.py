import sys
import traceback
import zipfile
from pathlib import Path

repository = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repository / 'src'))

from convert.formats.Fusion.GraphicsCodec.Wire.SceneWire import SceneWire
from convert.formats.Fusion.GraphicsCodec.Model.State.GraphicsStream import GraphicsStream
from convert.formats.Fusion.GraphicsCodec.ReadGraphics import ReadGraphics

original_links = SceneWire.EmptyLinks
original_text = SceneWire.TextValue
recent = []


def traced_text(self, value):
    start = self.Position
    result = original_text(self, value)
    if self.IsReading:
        recent.append((start, result))
        del recent[:-12]
    return result


def traced_links(self, count):
    start = self.Position
    flags = self.Payload[start:start + count]
    if any(flags):
        print('linked flags at', start, flags.hex(' '), 'recent texts', recent[-6:])
        print('  before', self.Payload[max(0, start - 96):start].hex(' '))
        print('  after ', self.Payload[start:start + 160].hex(' '))
    return original_links(self, count)


SceneWire.EmptyLinks = traced_links
SceneWire.TextValue = traced_text
archive = zipfile.ZipFile(sys.argv[1])
world = None
streams = []
fusion = []
for info in archive.infolist():
    if info.filename.endswith('/world'):
        world = archive.read(info)
    elif '/stream_mesh_' in info.filename:
        streams.append((info.filename.rsplit('/', 1)[1], archive.read(info)))
    elif '/Fusion_mesh_' in info.filename:
        fusion.append((info.filename.rsplit('/', 1)[1], archive.read(info)))
print('world bytes', len(world), [name for name, _ in streams])
try:
    scene = ReadGraphics(
        world,
        tuple(GraphicsStream(int(name.rsplit('_', 1)[1]), data) for name, data in streams),
        tuple(GraphicsStream(int(name.rsplit('_', 1)[1]), data) for name, data in fusion),
    )
    print('ok')
except Exception as error:
    frames = traceback.extract_tb(error.__traceback__)
    print('fail', error, ' <- '.join(f'{Path(f.filename).stem}:{f.lineno}' for f in frames[-8:]))
