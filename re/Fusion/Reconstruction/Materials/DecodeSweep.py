import io
import json
import sys
import traceback
from dataclasses import asdict
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import TrialGrammar  # noqa: E402,F401
from convert.formats.Fusion.MaterialCodec.Package.ReadPackage import ReadPackage  # noqa: E402

SWEEP = ROOT / 're/Fusion/LocalOracle/MaterialFamilies/Sweep'


def plain(value):
    if isinstance(value, tuple):
        return [plain(item) for item in value]
    if hasattr(value, '__dataclass_fields__'):
        return asdict(value)
    return value


def decode(path):
    with ZipFile(path) as outer:
        names = [name for name in outer.namelist() if name.endswith('.protein')]
        if len(names) != 1:
            raise ValueError('expected one protein member')
        package = ReadPackage(outer.read(names[0]))
    assets = []
    for asset in package.Assets:
        assets.append({'schema': asset.SchemaName, 'role': asset.AssetRole, 'instance': asset.InstanceId, 'definition': asset.DefinitionId, 'definitions': {item.FieldName: plain(item.Value) for item in asset.Definitions}, 'properties': {item.FieldName: plain(item.Value) if item.Connections is None else {'links': plain(item.Connections), 'value': plain(item.Value)} for item in asset.Properties}})
    schemas = sorted(dict(child.Attributes)['val'] for node in package.Schemas for child in node.Children if child.TagName == 'UID')
    return {'schemas': schemas, 'assets': assets}


def main():
    target = Path(sys.argv[1])
    result = {}
    folder = Path(sys.argv[2]) if len(sys.argv) > 2 else SWEEP
    for path in sorted(folder.glob('*.f3d')):
        try:
            result[path.stem] = decode(path)
        except Exception:
            result[path.stem] = {'error': traceback.format_exc().splitlines()[-1]}
    target.write_text(json.dumps(result, indent=1) + '\n')
    errors = {key: value['error'] for key, value in result.items() if 'error' in value}
    print(len(result), 'decoded', len(errors), 'errors')
    for key, value in list(errors.items())[:10]:
        print(key, value)


if __name__ == '__main__':
    main()
