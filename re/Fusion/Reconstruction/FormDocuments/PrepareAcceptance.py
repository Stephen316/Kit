import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

OUTPUT = ROOT / 're/Fusion/LocalOracle/FormDocuments/Acceptance'
CONTROLS = ('Plane', 'Box', 'PlaneCreased', 'SymmetricBox')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reemitted():
    rows = []
    for name in CONTROLS:
        source = ROOT / ('re/Fusion/LocalOracle/TSplineCodec/vendor_%sControl.f3d' % name)
        model = ReadDocument(source.read_bytes())
        target = OUTPUT / ('Reemitted%s.f3d' % name)
        target.write_bytes(EmitParsed(model))
        if ReadDocument(target.read_bytes()) != model:
            raise ValueError('Re-emitted model changed for ' + name)
        rows.append({'name': name, 'kind': 'reemitted', 'control_file': str(source.relative_to(ROOT)), 'control_sha256': sha(source), 'file': str(target.relative_to(ROOT)), 'sha256': sha(target)})
    return rows


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report = {'scope': 'Native acceptance inputs for production Form document re-emission', 'cases': reemitted()}
    (OUTPUT / 'Preparation.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
