import hashlib
import json
import math
import sys
from dataclasses import replace
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.ConvertGrid import ConvertGrid
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.SwapGridCage import SwapGridCage
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

SOURCE = 're/Fusion/LocalOracle/TSpline/Plane.f3d'
TARGET = ROOT / 're/Fusion/LocalOracle/FormDocuments/Grid'
ANGLE = math.radians(25.0)


def affine(x, y, z):
    u, v = 1.2 * x, 0.8 * y
    return (u * math.cos(ANGLE) - v * math.sin(ANGLE) + 0.5, u * math.sin(ANGLE) + v * math.cos(ANGLE) - 0.3, z + 0.3 * x - 0.2 * y + 0.2)


def warped(x, y, z):
    return (x + 0.08 * math.sin(2.0 * y), y + 0.06 * math.cos(3.0 * x), z + 0.25 * math.sin(1.7 * x) * math.cos(1.3 * y))


def moved(surface, mapping):
    grips = tuple(replace(grip, CoordX=point[0], CoordY=point[1], CoordZ=point[2]) for grip in surface.Grips for point in (mapping(grip.CoordX, grip.CoordY, grip.CoordZ),))
    return replace(surface, Grips=grips)


def expectation(result):
    surface = result.Surface
    return {
        'knots_u': [[knot.Value, knot.Count] for knot in surface.KnotsU],
        'knots_v': [[knot.Value, knot.Count] for knot in surface.KnotsV],
        'poles_cm': [list(point) for point in surface.Points],
        'corners_cm': [list(point) for point in result.Corners],
        'bounds': [{'knots': list(curve.Knots), 'multiplicity': list(curve.Multiplicity), 'poles_cm': [list(point) for point in curve.Poles]} for curve in result.Bounds],
    }


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    data = (ROOT / SOURCE).read_bytes()
    model = ReadDocument(data)
    rows = []
    for name, mapping in (('Affine', affine), ('Warped', warped)):
        surface = moved(model.Forms[0].Surface, mapping)
        text = EmitTspline(surface)
        if ReadTspline(text) != surface:
            raise RuntimeError('TSM text does not read back')
        document = SwapGridCage(model, surface)
        payload = EmitParsed(document)
        if ReadDocument(payload) != document:
            raise RuntimeError('Swapped document does not read back')
        (TARGET / (name + '.tsm')).write_bytes(text)
        (TARGET / (name + '.f3d')).write_bytes(payload)
        rows.append({
            'case': name,
            'tsm_file': str((TARGET / (name + '.tsm')).relative_to(ROOT)),
            'tsm_sha256': hashlib.sha256(text).hexdigest(),
            'document_file': str((TARGET / (name + '.f3d')).relative_to(ROOT)),
            'document_sha256': hashlib.sha256(payload).hexdigest(),
            'graphics_written': document.Graphics is not None,
            'expected': expectation(ConvertGrid(surface)),
        })
    report = {
        'scope': 'New plane control nets on the native 2x3 plane topology: Kit TSM text, Kit-converted complete document and Kit conversion expectation',
        'python': sys.version.split()[0],
        'carrier': SOURCE,
        'carrier_sha256': hashlib.sha256(data).hexdigest(),
        'rows': rows,
    }
    (TARGET / 'Preparation.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps([{key: value for key, value in row.items() if key != 'expected'} for row in rows], indent=1))


if __name__ == '__main__':
    main()
