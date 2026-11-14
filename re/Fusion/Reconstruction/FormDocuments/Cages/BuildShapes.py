"""Research: per-layout converted body shapes for the Form stencil tables.

Reads the converted body that Fusion stored in one native carrier of each
stencil layout, maps its vertices, edge curves and faces onto the rows of
the stencil result by geometry, and packs the layout-invariant rest (edge
and face structure, labels, progenitor windows, edge bounds, convexity,
pcurves, fit tolerances and patch cells) into FormShapes.xz. It then checks
CageBody against every other native archive of a stencil layout.
"""

import hashlib
import json
import lzma
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 're/Fusion/Reconstruction/FormDocuments/Tables'))
sys.path.insert(0, str(BASE))
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil import ReadShapes as ShapeModule
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.CageBody import CageBody
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.ConvertCage import ConvertCage
from ReadStencils import ReadStencils
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from ReadConverted import ReadConverted

ORACLE = 're/Fusion/LocalOracle/'
CARRIERS = (
    ('Box', ORACLE + 'TSpline/Box.f3d'),
    ('CreasedPlane', ORACLE + 'TSplineCodec/vendor_PlaneCreasedControl.f3d'),
    ('CreasedBox', ORACLE + 'TSplineCodec/vendor_BoxCreasedControl.f3d'),
    ('Box3', ORACLE + 'FormDocuments/StencilAccept/Carriers/Box3.f3d'),
    ('Valence5', ORACLE + 'FormDocuments/StencilAccept/Carriers/Valence5.f3d'),
    ('Valence6', ORACLE + 'FormDocuments/StencilAccept/Carriers/Valence6.f3d'),
    ('Valence8', ORACLE + 'FormDocuments/StencilAccept/Carriers/Valence8.f3d'),
    ('Valence7', ORACLE + 'FormDocuments/StencilAccept/Carriers/Valence7.f3d'),
)
KIT_WRITTEN = ('FormDocuments/StencilAccept/Cases/', 'FormDocuments/Acceptance/Reemitted', 'FormDocuments/Sourceless/Variants/', '/tmp/')
KIT_FOLDERS = ('FormDocuments/CageDocuments/', 'FormDocuments/Sourceless/')
TARGET = ROOT / 're/Fusion/Reconstruction/FormDocuments/Tables/FormShapes.xz'
REPORT = BASE / 'StencilShapes.json'
SLACK = 1e-12


def kit_written(relative):
    if any(folder in relative for folder in KIT_FOLDERS) and not any(folder in relative for folder in ('/Saved/', '/Loaded/')):
        return True
    return any(part in relative for part in KIT_WRITTEN)


def gap(left, right):
    if len(left) != len(right):
        return float('inf')
    return max((abs(a - b) for p, q in zip(left, right) for a, b in zip(p, q, strict=True)), default=0.0)


def only(found, what):
    if len(found) != 1:
        raise RuntimeError(f'{what}: {len(found)} matches')
    return found[0]


def curve_json(curve):
    return [curve.Rational, curve.Degree, curve.Closure, list(curve.Knots), list(curve.Multiplicity), curve.Dimension, [list(pole) for pole in curve.Poles], list(curve.Weights)]


def curve_index(result, curve):
    return only([index for index, other in enumerate(result.Curves) if (other.Rational, other.Degree, other.Closure, other.Knots, other.Multiplicity, other.Dimension, other.Weights) == (curve.Rational, curve.Degree, curve.Closure, curve.Knots, curve.Multiplicity, curve.Dimension, curve.Weights) and gap(other.Poles, curve.Poles) <= SLACK], 'curve')


def point_index(result, point):
    return only([index for index, other in enumerate(result.Points) if gap((other,), (point,)) <= SLACK], 'point')


def face_check(result, face):
    found = only([item for item in result.Faces if item.FaceIndex == face.Surface.Region], 'face')
    cache = face.Surface.Cache
    if (found.Surface.KnotsU, found.Surface.KnotsV, found.Jumps) != (cache.KnotsU, cache.KnotsV, face.Surface.Jumps):
        raise RuntimeError('face knots or jumps differ')
    if gap(found.Surface.Points, cache.Points) > SLACK:
        raise RuntimeError('face poles differ')


def shape(label, relative):
    model = ReadDocument((ROOT / relative).read_bytes())
    cage = model.Forms[0].Surface
    body = ReadConverted(model)
    result = ConvertCage(cage)
    if ReadStencils()[result.LayoutKey].Label != label:
        raise RuntimeError('carrier layout differs from the table label')
    points = [point_index(result, point) for point in body.PointsCm]
    edges = []
    for edge in body.Edges:
        index = curve_index(result, edge.Curve)
        if result.CurveJumps[index] != edge.Jumps:
            raise RuntimeError('edge jumps differ')
        windows = [[item.Face, item.ULow, item.UHigh, item.VLow, item.VHigh] for item in edge.Windows]
        edges.append([edge.StartVertex, edge.EndVertex, index, edge.Convexity, edge.Label, windows, None if edge.Bounds is None else list(edge.Bounds)])
    faces = []
    for face in body.Faces:
        face_check(result, face)
        uses = [[use.EdgeIndex, use.Reversed, curve_json(use.Pcurve), use.Fit] for use in face.Uses]
        faces.append([face.Surface.Region, face.Label, face.DoubleSided, face.Contained, uses])
    regions = [[[cell.Face, list(cell.Window), list(cell.Offset)] for cell in cells] for cells in body.Regions]
    entry = {'Label': label, 'LayoutKey': result.LayoutKey, 'Points': points, 'Edges': edges, 'Faces': faces, 'Regions': regions}
    summary = {'label': label, 'carrier': relative, 'carrier_sha256': hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), 'vertices': len(points), 'edges': len(edges), 'faces': len(faces), 'uses': sum(len(face[4]) for face in faces), 'split_edges': sum(1 for edge in edges if edge[6] is not None), 'convexity': sorted({edge[3] for edge in edges}), 'labels': len([1 for edge in edges if edge[4]]) + len([1 for face in faces if face[1]])}
    return entry, summary, body


def canonical(body, result):
    edges = {}
    for edge in body.Edges:
        index = curve_index(result, edge.Curve)
        edges[index] = (point_index(result, body.PointsCm[edge.StartVertex]), point_index(result, body.PointsCm[edge.EndVertex]), edge.Jumps, edge.Bounds, [(item.Face, (item.ULow, item.UHigh, item.VLow, item.VHigh)) for item in edge.Windows], edge.Convexity, edge.Label)
    keys = [curve_index(result, edge.Curve) for edge in body.Edges]
    faces = {}
    for face in body.Faces:
        uses = [(keys[use.EdgeIndex], use.Reversed, use.Pcurve, use.Fit) for use in face.Uses]
        start = min(range(len(uses)), key=lambda index: uses[index][0])
        faces[face.Surface.Region] = (face.Surface.Jumps, face.Label, face.DoubleSided, face.Contained, uses[start:] + uses[:start])
    return edges, faces, body.Regions


def compare(native, built, result):
    left, right = canonical(native, result), canonical(built, result)
    row = {'structure': [], 'labels': 0, 'convexity': 0, 'pcurve_gap': 0.0, 'fit_gap': 0.0, 'window_gap': 0.0, 'geometry_gap': 0.0}
    if left[2] != right[2]:
        row['structure'].append('regions')
    if left[0].keys() != right[0].keys() or left[1].keys() != right[1].keys():
        row['structure'].append('edge or face keys')
        return row
    for key in left[0]:
        a, b = left[0][key], right[0][key]
        if a[:4] != b[:4] or [face for face, _ in a[4]] != [face for face, _ in b[4]]:
            row['structure'].append(f'edge {key}')
        row['window_gap'] = max([row['window_gap']] + [gap((first,), (second,)) for (_, first), (_, second) in zip(a[4], b[4])])
        row['convexity'] += a[5] != b[5]
        row['labels'] += a[6] != b[6]
    for key in left[1]:
        a, b = left[1][key], right[1][key]
        if a[0] != b[0] or a[2:4] != b[2:4] or len(a[4]) != len(b[4]):
            row['structure'].append(f'face {key}')
            continue
        row['labels'] += a[1] != b[1]
        for first, second in zip(a[4], b[4]):
            if first[:2] != second[:2] or (first[2].Knots, first[2].Multiplicity, first[2].Degree) != (second[2].Knots, second[2].Multiplicity, second[2].Degree):
                row['structure'].append(f'face {key} use')
                continue
            row['pcurve_gap'] = max(row['pcurve_gap'], gap(first[2].Poles, second[2].Poles))
            row['fit_gap'] = max(row['fit_gap'], abs(first[3] - second[3]))
    for face, other in zip(sorted(native.Faces, key=lambda item: item.Surface.Region), sorted(built.Faces, key=lambda item: item.Surface.Region)):
        row['geometry_gap'] = max(row['geometry_gap'], gap(face.Surface.Cache.Points, other.Surface.Cache.Points))
    for body in (native, built):
        if sorted(point_index(result, point) for point in body.PointsCm) != list(range(len(result.Points))):
            row['structure'].append('vertex points')
    for edge, other in zip(sorted(native.Edges, key=lambda item: curve_index(result, item.Curve)), sorted(built.Edges, key=lambda item: curve_index(result, item.Curve))):
        row['geometry_gap'] = max(row['geometry_gap'], gap(edge.Curve.Poles, other.Curve.Poles))
    return row


def verify():
    census = json.loads((BASE.parent / 'Stencil' / 'StencilCensus.json').read_text())
    rows = []
    for item in census['archives']:
        if item['status'] != 'equal' or kit_written(item['file']):
            continue
        model = ReadDocument((ROOT / item['file']).read_bytes())
        cage = model.Forms[0].Surface
        try:
            native = ReadConverted(model)
        except AssertionError:
            rows.append({'file': item['file'], 'status': 'outside the body reader'})
            continue
        result = ConvertCage(cage)
        row = {'file': item['file'], 'sha256': item['sha256'], 'table': ReadStencils()[result.LayoutKey].Label}
        row.update(compare(native, CageBody(cage), result))
        row['status'] = 'equal' if not row['structure'] and row['geometry_gap'] <= SLACK else 'different'
        rows.append(row)
        print(json.dumps(row))
    return rows


def main():
    entries, summaries = [], []
    for label, relative in CARRIERS:
        entry, summary, body = shape(label, relative)
        entries.append(entry)
        summaries.append(summary)
        print(json.dumps(summary))
    text = json.dumps({'Shapes': entries}, sort_keys=True, separators=(',', ':')).encode('ascii')
    data = lzma.compress(text, preset=9 | lzma.PRESET_EXTREME)
    TARGET.write_bytes(data)
    ShapeModule.ReadShapes.cache_clear()
    rows = verify()
    report = {'scope': 'Packaged per-layout converted body shapes read from one native carrier per stencil layout, and CageBody against the converted bodies of other native archives of the same layouts', 'python': sys.version.split()[0], 'file': str(TARGET.relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'slack_cm': SLACK, 'shapes': summaries, 'archives': rows, 'totals': {status: sum(1 for row in rows if row['status'] == status) for status in sorted({row['status'] for row in rows})}}
    REPORT.write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
