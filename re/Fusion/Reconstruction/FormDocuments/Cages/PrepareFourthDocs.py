import hashlib
import json
import math
import random
import sys
from dataclasses import replace
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(BASE))
from ReadConverted import ReadConverted
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.ConvertForm import ConvertForm
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.ConvertCage import ConvertCage
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.Form.EmitFormDoc import EmitFormDoc
from convert.formats.Fusion.DocumentCodec.Form.FormSpec import FormSpec
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.TSplineCodec.EmitTspline import EmitTspline
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

ORACLE = 're/Fusion/LocalOracle/FormDocuments/'
WORK = ROOT / ORACLE / 'FourthDocuments'
CASES = {
    'Valence7Fresh': ('Stencil/Valence7.tsm', 0.12, 0.03, {}),
    'Valence7Weighted': ('Stencil/Valence7.tsm', 0.1, 0.03, {14: 2.0, 0: 0.6, 20: 1.7}),
    'BoxWeightedFresh': ('Sourceless/Box.tsm', 0.2, 0.05, {0: 2.5, 5: 0.5, 11: 1.8, 17: 3.0, 22: 0.7, 25: 1.3}),
    'Box3Weighted': ('Stencil/Box3.tsm', 0.0, 0.0, {0: 2.0}),
    'Valence5Weighted': ('Stencil/Valence5.tsm', 0.15, 0.04, {10: 2.0, 11: 1.5, 3: 0.8}),
}


def fresh(case, surface, spread, warp, weights):
    generator = random.Random(case)
    grips = []
    for index, grip in enumerate(surface.Grips):
        x, y, z = grip.CoordX / grip.Weight, grip.CoordY / grip.Weight, grip.CoordZ / grip.Weight
        moved = (x + warp * math.sin(1.3 * y) + generator.uniform(-spread, spread), y + warp * math.cos(1.1 * z) + generator.uniform(-spread, spread), z + warp * math.sin(0.9 * x) + generator.uniform(-spread, spread))
        weight = weights.get(index, 1.0)
        grips.append(replace(grip, CoordX=round(moved[0], 9) * weight, CoordY=round(moved[1], 9) * weight, CoordZ=round(moved[2], 9) * weight, Weight=weight))
    return replace(surface, Grips=tuple(grips))


def gap(left, right):
    if len(left) != len(right):
        return float('inf')
    return max((abs(a - b) for p, q in zip(left, right) for a, b in zip(p, q, strict=True)), default=0.0)


def check(cage, model):
    native = ReadConverted(model)
    result = ConvertCage(cage)
    faces = {face.FaceIndex: face for face in result.Faces}
    row = {'surface_gap_cm': 0.0, 'weight_gap': 0.0, 'curve_gap_cm': 0.0, 'forms_equal': True, 'jumps_equal': True}
    for face in native.Faces:
        mine = faces[face.Surface.Region]
        cache = face.Surface.Cache
        row['forms_equal'] &= (cache.Form, len(cache.Weights)) == (mine.Surface.Form, len(mine.Surface.Weights))
        row['jumps_equal'] &= face.Surface.Jumps == mine.Jumps
        row['surface_gap_cm'] = max(row['surface_gap_cm'], gap(cache.Points, mine.Surface.Points))
        row['weight_gap'] = max(row['weight_gap'], gap([(value,) for value in cache.Weights], [(value,) for value in mine.Surface.Weights]))
    for edge in native.Edges:
        mine = min(result.Curves, key=lambda curve: gap(curve.Poles, edge.Curve.Poles))
        row['forms_equal'] &= (mine.Rational, mine.Knots, mine.Multiplicity) == (edge.Curve.Rational, edge.Curve.Knots, edge.Curve.Multiplicity)
        row['curve_gap_cm'] = max(row['curve_gap_cm'], gap(mine.Poles, edge.Curve.Poles))
    row['rational_faces'] = sum(1 for face in result.Faces if face.Surface.Weights)
    row['rational_curves'] = sum(1 for curve in result.Curves if curve.Rational)
    return row


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    WORK.mkdir(exist_ok=True)
    rows = []
    for case, (source, spread, warp, weights) in CASES.items():
        base = ReadTspline((ROOT / ORACLE / source).read_bytes())
        cage = fresh(case, base, spread, warp, weights)
        text = EmitTspline(cage)
        if ReadTspline(text) != cage:
            raise RuntimeError(case + ' TSM does not read back')
        tsm = WORK / (case + '.tsm')
        tsm.write_bytes(text)
        payload = EmitFormDoc(FormSpec('Kit ' + case, cage, ConvertForm(cage)))
        model = ReadDocument(payload)
        if len(model.Forms) != 1 or model.Forms[0].Surface != cage:
            raise RuntimeError(case + ': written cage differs')
        if ReadDocument(EmitParsed(model)) != model:
            raise RuntimeError(case + ': written document does not round-trip')
        document = WORK / (case + '.f3d')
        document.write_bytes(payload)
        row = {'case': case, 'layout_source': ORACLE + source, 'grips': len(cage.Grips), 'weights': {str(index): value for index, value in sorted(weights.items())}, 'tsm_file': str(tsm.relative_to(ROOT)), 'tsm_sha256': digest(text), 'document_file': str(document.relative_to(ROOT)), 'document_sha256': digest(payload)}
        row.update(check(cage, model))
        rows.append(row)
        print(json.dumps(row))
    report = {'scope': 'Fourth pass source-free Kit Form documents: a fresh cage of the new valence-7 table and weighted cages of the box, three-by-three box, valence-5 and valence-7 layouts, each written by EmitFormDoc from the cage alone', 'python': sys.version.split()[0], 'rows': rows}
    (WORK / 'Preparation.json').write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
