"""Research preparation: source-free Form documents for native acceptance.

Plane cases take the cage of a native plane primitive, or a warped copy of
one, and let the production `ConvertGrid` and `GridBody` supply the
converted body. Closed and creased cases read the converted body that Fusion
stored in a native control archive (research only, through `ExtractBody`)
and pass it, with the cage, to the production builder as typed input.
Every document is written by the production `EmitFormDoc` with fresh
identities. No archive bytes reach the builder.
"""

import hashlib
import json
import math
import sys
from dataclasses import replace
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = HERE.parents[4]

from ExtractBody import extract  # noqa: E402

from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.ConvertGrid import ConvertGrid  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.GridBody import GridBody  # noqa: E402
from convert.formats.Fusion.DocumentCodec.Form.EmitFormDoc import EmitFormDoc  # noqa: E402
from convert.formats.Fusion.DocumentCodec.Form.FormSpec import FormSpec  # noqa: E402
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument  # noqa: E402
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline  # noqa: E402
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline  # noqa: E402

TARGET = ROOT / 're/Fusion/LocalOracle/FormDocuments/Sourceless'
PRIMITIVES = 're/Fusion/LocalOracle/FormDocuments/Grid/Primitives/'
PLANES = (
    ('Plane1x1', PRIMITIVES + 'Plane1x1.f3d', [1, 1, 2.0, 1.5]),
    ('Plane3x2', PRIMITIVES + 'Plane3x2.f3d', [3, 2, 3.0, 2.0]),
    ('Plane4x4', PRIMITIVES + 'Plane4x4.f3d', [4, 4, 2.5, 2.5]),
    ('Plane2x5', PRIMITIVES + 'Plane2x5.f3d', [2, 5, 1.7, 4.1]),
)
WARPED = ('WarpedPlane4x4', PRIMITIVES + 'Plane4x4.f3d')
CLOSED = (
    ('Box', 're/Fusion/LocalOracle/TSpline/Box.f3d'),
    ('SymmetricBox', 're/Fusion/LocalOracle/TSpline/SymmetricBox.f3d'),
    ('CreasedBox', 're/Fusion/LocalOracle/TSplineCodec/vendor_BoxCreasedControl.f3d'),
    ('CreasedPlane', 're/Fusion/LocalOracle/TSplineCodec/vendor_PlaneCreasedControl.f3d'),
)


def warp(x, y, z):
    return (x + 0.05 * math.sin(1.9 * y), y + 0.04 * math.cos(2.3 * x), z + 0.3 * math.sin(1.4 * x) * math.cos(1.1 * y))


def warped(surface):
    grips = tuple(replace(grip, CoordX=point[0], CoordY=point[1], CoordZ=point[2]) for grip in surface.Grips for point in (warp(grip.CoordX, grip.CoordY, grip.CoordZ),))
    return replace(surface, Grips=grips)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_case(name, source, cage, body, body_source, primitive=None):
    text = EmitTspline(cage)
    if ReadTspline(text) != cage:
        raise RuntimeError(f'{name}: TSM text does not read back')
    payload = EmitFormDoc(FormSpec('Kit ' + name, cage, body))
    model = ReadDocument(payload)
    if len(model.Forms) != 1 or model.Forms[0].Surface != cage:
        raise RuntimeError(f'{name}: written Form cage differs')
    (TARGET / (name + '.tsm')).write_bytes(text)
    (TARGET / (name + '.f3d')).write_bytes(payload)
    labels = sorted([face.Label for face in body.Faces if face.Label] + [edge.Label for edge in body.Edges if edge.Label], key=int)
    return {
        'case': name,
        'source_archive': source,
        'source_sha256': digest((ROOT / source).read_bytes()),
        'body_source': body_source,
        'primitive': primitive,
        'faces': len(body.Faces),
        'edges': len(body.Edges),
        'vertices': len(body.PointsCm),
        'labels': labels,
        'tsm_file': str((TARGET / (name + '.tsm')).relative_to(ROOT)),
        'tsm_sha256': digest(text),
        'document_file': str((TARGET / (name + '.f3d')).relative_to(ROOT)),
        'document_sha256': digest(payload),
        'document_parts': sorted(part for part in model_parts(payload)),
    }


def model_parts(payload):
    import io
    import zipfile
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        return [name.split('/', 1)[-1] for name in archive.namelist() if not name.endswith('/')]


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, source, primitive in PLANES:
        cage = ReadDocument((ROOT / source).read_bytes()).Forms[0].Surface
        rows.append(write_case(name, source, cage, GridBody(ConvertGrid(cage)), 'ConvertGrid + GridBody', primitive))
    name, source = WARPED
    cage = warped(ReadDocument((ROOT / source).read_bytes()).Forms[0].Surface)
    rows.append(write_case(name, source, cage, GridBody(ConvertGrid(cage)), 'ConvertGrid + GridBody (warped cage)'))
    for name, source in CLOSED:
        cage, body, _ = extract(ROOT / source)
        rows.append(write_case(name, source, cage, body, 'native converted body read by research ExtractBody'))
    report = {
        'scope': 'Source-free Kit Form documents written by EmitFormDoc from a typed cage and a typed converted body',
        'python': sys.version.split()[0],
        'rows': rows,
    }
    (TARGET / 'Preparation.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps([{key: row[key] for key in ('case', 'faces', 'edges', 'vertices', 'document_sha256')} for row in rows], indent=1))


if __name__ == '__main__':
    main()
