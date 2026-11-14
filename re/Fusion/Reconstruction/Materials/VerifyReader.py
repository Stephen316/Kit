import json
import sys
import traceback
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.MaterialCodec.Package.EmitPackage import EmitPackage  # noqa: E402
from convert.formats.Fusion.MaterialCodec.Package.ReadPackage import ReadPackage  # noqa: E402


def main():
    folder = Path(sys.argv[1])
    result = {'documents': 0, 'read': 0, 'round_trip': 0, 'errors': {}}
    for path in sorted(folder.glob('*.f3d')):
        result['documents'] += 1
        try:
            with ZipFile(path) as outer:
                name = next(item for item in outer.namelist() if item.endswith('.protein'))
                package = ReadPackage(outer.read(name))
            result['read'] += 1
            if ReadPackage(EmitPackage(package)) == package:
                result['round_trip'] += 1
            else:
                result['errors'][path.stem] = 'round trip differs'
        except Exception:
            result['errors'][path.stem] = traceback.format_exc().splitlines()[-1]
    print(json.dumps({key: value for key, value in result.items() if key != 'errors'}), list(result['errors'].items())[:5])
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(json.dumps(result, indent=1) + '\n')


if __name__ == '__main__':
    main()
