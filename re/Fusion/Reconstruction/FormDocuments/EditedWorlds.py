import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))
import convert.formats.Fusion.DocumentCodec.Reading.ReadDocParts as DocParts
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.GraphicsCodec.Wire import SceneCodec

NAMES = ('BoxEdited', 'PlaneEdited', 'SymmetricBoxEdited')
SEEN = []
ORIGINAL_INTEGER = SceneCodec.SceneCodec.Integer
ORIGINAL_SCENE = DocParts.ReadSceneParts


def integer(self, *args, **kwargs):
    value = ORIGINAL_INTEGER(self, *args, **kwargs)
    SEEN.append(value)
    return value


def production(data):
    SEEN.clear()
    try:
        ReadDocument(data)
        return {'status': 'read'}
    except ValueError as error:
        return {'status': 'ValueError', 'message': str(error), 'last_integer_before_error': SEEN[-1] if SEEN else None}


def without_graphics(data):
    DocParts.ReadSceneParts = lambda values: None
    try:
        model = ReadDocument(data)
        return {'status': 'read', 'forms': len(model.Forms), 'bodies': len(model.Bodies), 'snapshots': len(model.Snapshots)}
    except ValueError as error:
        return {'status': 'ValueError', 'message': str(error)}
    finally:
        DocParts.ReadSceneParts = ORIGINAL_SCENE


def main():
    SceneCodec.SceneCodec.Integer = integer
    rows = []
    for name in NAMES:
        path = ROOT / 're/Fusion/LocalOracle/TSpline' / (name + '.f3d')
        data = path.read_bytes()
        rows.append({'file': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest(), 'production': production(data), 'graphics_reader_disabled': without_graphics(data)})
    report = {'scope': 'Research isolation of the edited Form archive failure; the graphics reader is disabled only inside this script', 'python': sys.version.split()[0], 'rows': rows}
    (BASE / 'EditedWorlds.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
