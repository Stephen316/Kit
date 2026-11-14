import io
import sys
import traceback
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.setrecursionlimit(20000)

from convert.formats.Fusion.BundleCodec.ReadBundle import ReadBundle
from convert.formats.Fusion.GraphicsCodec.Model.State.GraphicsStream import GraphicsStream

PREFIX = 'OGS.BlobFolder/OGS/DefaultScene/'
BUNDLE = 're/Fusion/examples/.f3z/example1.f3z'


def scene(member, bundle=BUNDLE):
    data = ReadBundle((ROOT / bundle).read_bytes()).Documents[member].DataValue
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        parts = {info.filename.split('/', 1)[-1]: archive.read(info) for info in archive.infolist() if PREFIX in info.filename}
    world = parts[PREFIX + 'world']
    mesh = tuple(GraphicsStream(int(name[-3:]), value) for name, value in sorted(parts.items()) if '/stream_mesh_' in name)
    fusion = tuple(GraphicsStream(int(name[-3:]), value) for name, value in sorted(parts.items()) if '/Fusion_mesh_' in name)
    return world, mesh, fusion


def where(error):
    frames = traceback.extract_tb(error.__traceback__)
    return ' <- '.join(f'{Path(f.filename).stem}:{f.lineno}' for f in reversed(frames[-5:]))


def strings(payload, start, stop):
    found = []
    position = start
    while position < stop - 4:
        length = int.from_bytes(payload[position:position + 4], 'little')
        if 3 <= length <= 64:
            text = payload[position + 4:position + 4 + 2 * length]
            try:
                value = text.decode('utf-16le')
            except UnicodeError:
                value = ''
            if value.isprintable() and len(value) == length and value.replace('<', '').replace('>', '').replace('_', '').isalnum():
                found.append((position, value))
                position += 4 + 2 * length
                continue
        position += 1
    return found
