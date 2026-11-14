import sys
import traceback
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'src'))

from convert.formats.Fusion.GraphicsCodec.Model.State.GraphicsStream import GraphicsStream
from convert.formats.Fusion.GraphicsCodec.Wire.SceneCodec import SceneCodec
from convert.formats.Fusion.GraphicsCodec.Worlds.XferWorldMut import XferWorldMut

PREFIX = 'FusionAssetName[Active]/OGS.BlobFolder/OGS/DefaultScene/'


def members(name):
    archive = zipfile.ZipFile(name)
    return {info.filename[len(PREFIX):]: archive.read(info.filename) for info in archive.infolist() if info.filename.startswith(PREFIX) and not info.filename.endswith('/')}


def scene(found):
    streams = tuple(GraphicsStream(int(key[-3:]), value) for key, value in found.items() if key.startswith('stream_mesh_'))
    fusion = tuple(GraphicsStream(int(key[-3:]), value) for key, value in found.items() if key.startswith('Fusion_mesh_'))
    return SceneCodec(found['world'], streams, fusion, None)


def show(data, position, before=64, after=192):
    start = max(0, position - before)
    chunk = data[start:position + after]
    for offset in range(0, len(chunk), 32):
        part = chunk[offset:offset + 32]
        text = ''.join(chr(b) if 32 <= b < 127 else '.' for b in part)
        mark = '>' if start + offset <= position < start + offset + 32 else ' '
        print(f'{mark}{start + offset:8d} {part.hex(" ")}  {text}')


if __name__ == '__main__':
    for name in sys.argv[1:]:
        found = members(name)
        print('==', name, {key: len(value) for key, value in found.items()})
        state = scene(found)
        try:
            XferWorldMut(state, None, True)
            print('decoded to', state.Position, 'of', len(found['world']))
        except Exception as error:
            print('error', error, 'at', state.Position)
            print(''.join(traceback.format_tb(error.__traceback__)[-4:]))
            show(found['world'], state.Position)
