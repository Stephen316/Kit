"""Research: does the fold check separate the cages Fusion refuses to convert.

Fusion refused four large single-grip moves of the creased cages with
ASM_TSP_IG_SURFACE_IRREGULAR or ASM_TSP_IG_CURVE_IRREGULAR (LimitProbe.json).
For those cages and for the cage of every Fusion-saved archive that Kit can
convert, this script builds the Kit body without the fold check and reports
the smallest cosine between neighbouring face normal samples and between
neighbouring edge tangent samples, and the CheckFolds verdict. The probe
folders under Stencil/tmp are ignored by git, so each row records the
SHA-256 of the file it read.
"""

import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 're/Fusion/Reconstruction/FormDocuments/Tables'))
sys.path.insert(0, str(BASE))
from CreaseCheck import kit_written
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.ConvertGrid import ConvertGrid
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted import CheckFolds as Rule
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.GridBody import GridBody
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.CageBody import ShapeBody
from ReadShapes import ReadShapes
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.SplineFrame import CurveFrame
from StencilKey import StencilKey
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

TARGET = BASE / 'FoldCheck.json'
LIMITS = ROOT / 're/Fusion/Reconstruction/FormDocuments/Stencil/LimitProbe.json'
PROBES = ROOT / 're/Fusion/LocalOracle/FormDocuments/Stencil/tmp'


def cosine(first, second):
    lengths = math.sqrt(sum(x * x for x in first) * sum(x * x for x in second))
    return sum(a * b for a, b in zip(first, second)) / lengths if lengths else -2.0


def measures(body):
    face = 1.0
    for item in body.Faces:
        grid = Rule.FaceNormals(item.Surface.Cache)
        for row in grid:
            face = min([face] + [cosine(a, b) for a, b in zip(row, row[1:])])
        for lower, upper in zip(grid, grid[1:]):
            face = min([face] + [cosine(a, b) for a, b in zip(lower, upper)])
    edge = 1.0
    for item in body.Edges:
        knots = item.Curve.Knots
        lower, upper = item.Bounds or (knots[0], knots[-1])
        breaks = [lower] + [value for value in knots if lower < value < upper] + [upper]
        tangents = [CurveFrame(item.Curve, param)[1] for param in Rule.SpanParams(breaks)]
        edge = min([edge] + [cosine(a, b) for a, b in zip(tangents, tangents[1:])])
    return face, edge


def study(cage):
    body = ShapeBody(cage) if StencilKey(cage) in ReadShapes() else GridBody(ConvertGrid(cage))
    face, edge = measures(body)
    try:
        Rule.CheckFolds(body)
        verdict = 'accepted'
    except ValueError as error:
        verdict = 'refused: ' + str(error)
    return {'face_cosine_min': face, 'edge_cosine_min': edge, 'verdict': verdict}


def limits():
    report = json.loads(LIMITS.read_text())
    rows = []
    for cage in report['cages']:
        for variant in cage['variants']:
            path = PROBES / cage['cage'] / (variant['variant'] + '.tsm')
            data = path.read_bytes()
            row = {'file': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest(), 'fusion_status': variant['status'], 'fusion_messages': variant.get('messages')}
            row.update(study(ReadTspline(data)))
            rows.append(row)
    return rows


def archives():
    rows, seen = [], set()
    for path in sorted(ROOT.glob('re/Fusion/**/*.f3d')):
        relative = str(path.relative_to(ROOT))
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if kit_written(relative) or digest in seen:
            continue
        seen.add(digest)
        try:
            model = ReadDocument(data)
            if len(model.Forms) != 1:
                continue
            row = study(model.Forms[0].Surface)
        except Exception:
            continue
        rows.append({'file': relative, 'sha256': digest, **row})
    return rows


def main():
    report = {'scope': 'Fold check of Kit cage bodies: cages Fusion refused as irregular against the cages of every Fusion-saved archive that Kit converts', 'python': sys.version.split()[0], 'fold_cosine': Rule.KFoldCosine, 'samples_per_span': Rule.KFoldSamples, 'limits': limits(), 'archives': archives()}
    report['totals'] = dict(Counter(('limit ' if row in report['limits'] else 'archive ') + row['fusion_status' if row in report['limits'] else 'verdict'].split(':')[0] + ' / ' + row['verdict'].split(':')[0] for row in report['limits'] + report['archives']))
    report['archive_face_cosine_min'] = min(row['face_cosine_min'] for row in report['archives'])
    report['archive_edge_cosine_min'] = min(row['edge_cosine_min'] for row in report['archives'])
    TARGET.write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report['totals']), report['archive_face_cosine_min'], report['archive_edge_cosine_min'])
    for row in report['limits']:
        print(row['file'].split('/')[-2:], row['fusion_status'], row['verdict'], round(row['face_cosine_min'], 3), round(row['edge_cosine_min'], 3))


if __name__ == '__main__':
    main()
