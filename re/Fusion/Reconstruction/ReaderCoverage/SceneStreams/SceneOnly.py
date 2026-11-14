import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'src'))

from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.DocumentCodec.Auxiliary.Graphics.EmitSceneParts import EmitSceneParts
from convert.formats.Fusion.DocumentCodec.Auxiliary.Graphics.ReadSceneParts import ReadSceneParts


def where(error):
    frames = traceback.extract_tb(error.__traceback__)
    return ' <- '.join(f'{Path(f.filename).stem}:{f.lineno}' for f in reversed(frames[-5:]))


def scene(data):
    container = ReadContainer(data)
    parts = tuple(part for part in container.Parts if part.Name.startswith('OGS.BlobFolder/'))
    if not parts:
        return {'status': 'none'}
    try:
        value = ReadSceneParts(container.Parts)
    except Exception as error:
        return {'status': 'read', 'error': f'{type(error).__name__}: {error}', 'where': where(error)}
    emitted = {part.Name: part.Payload for part in EmitSceneParts(value)}
    original = {part.Name: part.Payload for part in parts}
    again = ReadSceneParts(tuple(EmitSceneParts(value)))
    return {
        'status': 'pass' if emitted == original and again == value else 'differ',
        'members': {name.rsplit('/', 1)[1]: len(payload) for name, payload in original.items()},
        'differing': sorted(name for name in set(original) | set(emitted) if original.get(name) != emitted.get(name)),
        'model_equal': again == value,
    }


if __name__ == '__main__':
    for name in sys.argv[1:]:
        print(Path(name).name[:16], json.dumps(scene(Path(name).read_bytes())))
