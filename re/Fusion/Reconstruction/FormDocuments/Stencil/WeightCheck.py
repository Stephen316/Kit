"""Research: production ConvertCage against Fusion conversions of weighted cages.

Reads the Fusion-saved weighted box archives, the Kit-authored saves whose
edits left grip weights one ulp above 1 and the fourth-pass acceptance
archives (the loaded oracle, and the oracle and Kit document after the Fusion
edit), converts each stored cage with
ConvertCage and compares every face cache, curve, form flag and jump list with
the stored converted body.
"""

import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(BASE.parent / 'Cages'))
from ReadConverted import ReadConverted
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.ConvertCage import ConvertCage
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

ORACLE = 're/Fusion/LocalOracle/FormDocuments/'
ARCHIVES = [ORACLE + 'Stencil/tmp/BoxWeightUniform/Base.f3d'] + [ORACLE + 'Stencil/tmp/BoxWeighted/' + label + '.f3d' for label in ('Base', 'X0', 'X3', 'Pair0_3', 'Scale0', 'RandomA')] + [ORACLE + 'CageDocuments/Saved/KitCreasedPlaneBent.f3d'] + [ORACLE + 'FourthDocuments/' + stage + '/' + side + case + '.f3d' for case in ('Valence7Fresh', 'Valence7Weighted', 'BoxWeightedFresh', 'Box3Weighted', 'Valence5Weighted') for stage, side in (('Loaded', 'Oracle'), ('Saved', 'Oracle'), ('Saved', 'Kit'))]


def gap(left, right):
    if len(left) != len(right):
        return float('inf')
    return max((abs(a - b) for p, q in zip(left, right) for a, b in zip(p, q, strict=True)), default=0.0)


def compare(name):
    data = (ROOT / name).read_bytes()
    model = ReadDocument(data)
    cage = model.Forms[0].Surface
    native = ReadConverted(model)
    result = ConvertCage(cage)
    faces = {face.FaceIndex: face for face in result.Faces}
    row = {'file': name, 'sha256': hashlib.sha256(data).hexdigest(), 'weights': sorted({grip.Weight for grip in cage.Grips}), 'faces': len(native.Faces), 'edges': len(native.Edges), 'face_point_gap_cm': 0.0, 'face_weight_gap': 0.0, 'curve_pole_gap_cm': 0.0, 'curve_weight_gap': 0.0, 'mismatches': []}
    row['rational_faces_native'] = sum(1 for face in native.Faces if face.Surface.Cache.Weights)
    row['rational_faces_kit'] = sum(1 for face in result.Faces if face.Surface.Weights)
    row['native_face_forms'] = sorted({face.Surface.Cache.Form for face in native.Faces})
    for face in native.Faces:
        mine = faces[face.Surface.Region]
        cache = face.Surface.Cache
        if (cache.Form, len(cache.Weights)) != (mine.Surface.Form, len(mine.Surface.Weights)):
            row['mismatches'].append(['face form', face.Surface.Region])
        if face.Surface.Jumps != mine.Jumps:
            row['mismatches'].append(['face jumps', face.Surface.Region])
        row['face_point_gap_cm'] = max(row['face_point_gap_cm'], gap(cache.Points, mine.Surface.Points))
        row['face_weight_gap'] = max(row['face_weight_gap'], gap([(value,) for value in cache.Weights], [(value,) for value in mine.Surface.Weights]))
    row['rational_curves_native'] = sum(1 for edge in native.Edges if edge.Curve.Rational)
    for edge in native.Edges:
        found = [index for index, curve in enumerate(result.Curves) if (curve.Knots, curve.Multiplicity) == (edge.Curve.Knots, edge.Curve.Multiplicity)]
        best = min(found, key=lambda index: gap(result.Curves[index].Poles, edge.Curve.Poles))
        mine = result.Curves[best]
        if mine.Rational != edge.Curve.Rational:
            row['mismatches'].append(['curve rational', best])
        if result.CurveJumps[best] != edge.Jumps:
            row['mismatches'].append(['curve jumps', best])
        row['curve_pole_gap_cm'] = max(row['curve_pole_gap_cm'], gap(mine.Poles, edge.Curve.Poles))
        row['curve_weight_gap'] = max(row['curve_weight_gap'], gap([(value,) for value in mine.Weights], [(value,) for value in edge.Curve.Weights]))
    row['point_gap_cm'] = max(min(gap((point,), (other,)) for other in result.Points) for point in native.PointsCm)
    return row


def main():
    report = {'scope': 'Production ConvertCage against the converted bodies Fusion stored for weighted box cages , for a Kit cage whose edit left weights one ulp above 1 and for the fourth-pass acceptance archives. A face or curve is rational when any of its stencil rows uses a grip whose weight differs from 1 by more than 2^-51', 'python': sys.version.split()[0], 'archives': []}
    for name in ARCHIVES:
        if not (ROOT / name).exists():
            report['archives'].append({'file': name, 'status': 'missing'})
            continue
        row = compare(name)
        report['archives'].append(row)
        print(json.dumps({key: row[key] for key in ('file', 'rational_faces_native', 'rational_faces_kit', 'face_point_gap_cm', 'curve_pole_gap_cm', 'mismatches')}))
    (BASE / 'WeightCheck.json').write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
