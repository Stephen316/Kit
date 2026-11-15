"""Prepare independently emitted Form documents for TSM cap-declaration acceptance.

Usage: PYTHONPATH=src python3.14 PrepareCapVariants.py
The Box3 variants reproduce existing one-field research controls. The HeldPrism5
variants are held out from those controls and are emitted by the same typed rule.
"""

import hashlib
import json
import sys
import time
from dataclasses import replace
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
SOURCE = ROOT / 're/Fusion/LocalOracle/FormDocuments/General'
TARGET = SOURCE / 'CapAccept'
sys.path.insert(0, str(ROOT / 'src'))

from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.ConvertForm import ConvertForm  # noqa: E402
from convert.formats.Fusion.DocumentCodec.Form.EmitFormDoc import EmitFormDoc  # noqa: E402
from convert.formats.Fusion.DocumentCodec.Form.FormSpec import FormSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument  # noqa: E402
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline  # noqa: E402
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline  # noqa: E402

VARIANTS = (
    ('Same', 'G1CAPS', 0.0),
    ('G0', 'G0CAPS', 0.0),
    ('G2', 'G2CAPS', 0.0),
    ('Star1', 'G1CAPS', 1.0),
    ('Star2', 'G1CAPS', 2.0),
)
SOURCES = (
    ('Box3', 'probe', SOURCE / 'Box3Same.tsm'),
    ('HeldPrism5', 'held-out', SOURCE / 'HeldOut' / 'HeldPrism5.tsm'),
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def prepare(stem, group, source, suffix, cap_type, star, shift=(0.0, 0.0, 0.0)):
    cage = ReadTspline(source.read_bytes())
    header = replace(cage.Header, CapType=cap_type, StarSmoothness=star)
    variant = replace(cage, Header=header)
    if shift != (0.0, 0.0, 0.0):
        variant = replace(
            variant,
            Grips=tuple(
                replace(
                    grip,
                    CoordX=grip.CoordX + shift[0],
                    CoordY=grip.CoordY + shift[1],
                    CoordZ=grip.CoordZ + shift[2],
                )
                for grip in variant.Grips
            ),
        )
    name = stem + suffix
    text = EmitTspline(variant)
    if ReadTspline(text) != variant:
        raise RuntimeError(f'{name}: TSM text does not read back')
    if stem == 'Box3' and shift == (0.0, 0.0, 0.0):
        control = SOURCE / (name + '.tsm')
        if control.read_bytes() != text:
            raise RuntimeError(f'{name}: typed variant differs from its one-field control')
    started = time.time()
    body = ConvertForm(variant)
    payload = EmitFormDoc(FormSpec('Kit ' + name, variant, body))
    parsed = ReadDocument(payload)
    if len(parsed.Forms) != 1 or parsed.Forms[0].Surface != variant:
        raise RuntimeError(f'{name}: written Form cage differs')
    (TARGET / (name + '.tsm')).write_bytes(text)
    (TARGET / (name + '.f3d')).write_bytes(payload)
    row = {
        'case': name,
        'group': group,
        'cage_source': str(source.relative_to(ROOT)),
        'cap_type': cap_type,
        'star_smoothness': star,
        'translation_cm': list(shift),
        'grips': len(variant.Grips),
        'convert_seconds': round(time.time() - started, 2),
        'status': 'prepared',
        'faces': len(body.Faces),
        'edges': len(body.Edges),
        'vertices': len(body.PointsCm),
        'rational_faces': sum(1 for face in body.Faces if face.Surface.Cache.Weights),
        'tsm_file': str((TARGET / (name + '.tsm')).relative_to(ROOT)),
        'tsm_sha256': digest(text),
        'document_file': str((TARGET / (name + '.f3d')).relative_to(ROOT)),
        'document_sha256': digest(payload),
    }
    print(json.dumps({key: row[key] for key in ('case', 'group', 'status', 'faces', 'edges', 'vertices')}))
    return row


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    rows = [
        prepare(stem, group, source, suffix, cap_type, star)
        for stem, group, source in SOURCES
        for suffix, cap_type, star in VARIANTS
    ]
    rows.append(
        prepare('Box3Shifted', 'held-out', SOURCE / 'Box3Same.tsm', 'G2', 'G2CAPS', 0.0, (13.0, -21.0, 42.0))
    )
    report = {
        'scope': 'Independent Kit Form documents for every observed cap type and star smoothness on Box3 and held-out HeldPrism5 cages',
        'acceptance_scope': 'Kit Form documents with G0CAPS, G1CAPS or G2CAPS and star smoothness 0, 1 or 2, against Fusion conversion of the same TSM',
        'report': 'NativeAcceptance.json',
        'python': sys.version.split()[0],
        'rows': rows,
    }
    (TARGET / 'Preparation.json').write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
