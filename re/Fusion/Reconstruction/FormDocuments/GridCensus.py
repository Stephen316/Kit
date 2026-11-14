import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.ConvertGrid import ConvertGrid
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.GridJumps import SpanThirds
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.JumpCurve import JumpCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.ExactSubtypes import SplineCurve
from convert.formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import GeometryState
from convert.formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import IntcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SubtransNode import SubtransNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

SCOPE = 'Kit grid conversion against every converted Form body in local Fusion archives'
KIT_BODIES = ('re/Fusion/LocalOracle/FormDocuments/Grid/Affine.f3d', 're/Fusion/LocalOracle/FormDocuments/Grid/Warped.f3d')


def gap(left, right):
    if len(left) != len(right):
        return None
    return max((abs(a - b) for p, q in zip(left, right) for a, b in zip(p, q)), default=0.0)


def knot_jumps(curves):
    found = {}
    for curve in curves:
        thirds = SpanThirds(curve)
        for index, knot in enumerate(curve.Knots[1:-1]):
            size = max(abs(a - b) for a, b in zip(thirds[index], thirds[index + 1]))
            found[knot] = max(found.get(knot, 0.0), size)
    return found


def margins(result):
    surface = result.Surface
    width = len(surface.Points) // (sum(knot.Count for knot in surface.KnotsV) - 2)
    knots_u = tuple(knot.Value for knot in surface.KnotsU)
    counts_u = tuple(knot.Count for knot in surface.KnotsU)
    knots_v = tuple(knot.Value for knot in surface.KnotsV)
    counts_v = tuple(knot.Count for knot in surface.KnotsV)
    rows = [BsCurve(False, 3, 0, knots_u, counts_u, 3, surface.Points[start:start + width], ()) for start in range(0, len(surface.Points), width)]
    columns = [BsCurve(False, 3, 0, knots_v, counts_v, 3, surface.Points[start::width], ()) for start in range(width)]
    groups = [(knot_jumps(rows), result.SurfaceJumps[2]), (knot_jumps(columns), result.SurfaceJumps[5])]
    groups += [(knot_jumps([bound]), jumps) for bound, jumps in zip(result.Bounds, result.BoundJumps)]
    skipped = [size for found, recorded in groups for knot, size in found.items() if knot not in recorded]
    kept = [size for found, recorded in groups for knot, size in found.items() if knot in recorded]
    return {'largest_skipped': max(skipped, default=None), 'smallest_recorded': min(kept, default=None), 'recorded': len(kept), 'skipped': len(skipped)}


def compare(result, entities):
    row = {'surfaces': 0, 'curves': 0, 'points': 0}
    worst = 0.0
    for entity in entities:
        if isinstance(entity, SplineNode) and isinstance(entity.Surface, TsplineSurf):
            cache = entity.Surface.Cache
            row['surfaces'] += 1
            if entity.Surface.Jumps != result.SurfaceJumps:
                raise RuntimeError('surface discontinuities differ')
            if (cache.KnotsU, cache.KnotsV) != (result.Surface.KnotsU, result.Surface.KnotsV):
                raise RuntimeError('knots differ')
            distance = gap(cache.Points, result.Surface.Points)
            if distance is None:
                raise RuntimeError('pole count differs')
            worst = max(worst, distance)
            subtrans = entity.Surface.Subtrans
            if isinstance(subtrans, SubtransNode) and subtrans.Regions != (result.Patches,):
                raise RuntimeError('patch program differs')
        elif isinstance(entity, IntcurveNode):
            cache = SplineCurve(entity.Curve)
            matches = [index for index, bound in enumerate(result.Bounds) if (bound.Knots, bound.Multiplicity) == (cache.Knots, cache.Multiplicity) and gap(bound.Poles, cache.Poles) is not None and gap(bound.Poles, cache.Poles) < 1e-12]
            if len(matches) != 1:
                raise RuntimeError('boundary curve differs')
            if JumpCurve(cache, result.BoundJumps[matches[0]]) != entity.Curve:
                raise RuntimeError('curve discontinuities differ')
            worst = max(worst, gap(result.Bounds[matches[0]].Poles, cache.Poles))
            row['curves'] += 1
        elif type(entity).__name__ == 'PointNode':
            distance = min(gap((corner,), (entity.PositionCm,)) for corner in result.Corners)
            if distance >= 1e-12:
                raise RuntimeError('corner differs')
            worst = max(worst, distance)
            row['points'] += 1
    row['max_abs_cm'] = worst
    return row


def native_shapes(model):
    shapes = set()
    for body in model.Bodies:
        if not isinstance(body.History, JournalModel):
            continue
        for entity in body.History.Entities:
            if isinstance(entity, SplineNode) and isinstance(entity.Surface, TsplineSurf):
                cache = entity.Surface.Cache
                subtrans = entity.Surface.Subtrans
                cells = [len(region) for region in subtrans.Regions] if isinstance(subtrans, SubtransNode) else None
                knots = tuple((knot.Value, knot.Count) for knot in cache.KnotsU), tuple((knot.Value, knot.Count) for knot in cache.KnotsV)
                shapes.add(json.dumps({'poles': len(cache.Points), 'knots_u': knots[0], 'knots_v': knots[1], 'region_cells': cells}))
    return [json.loads(shape) for shape in sorted(shapes)]


def main():
    files = sorted(str(path.relative_to(ROOT)) for path in (ROOT / 're/Fusion').rglob('*.f3d'))
    rows = []
    for relative in files:
        data = (ROOT / relative).read_bytes()
        try:
            model = ReadDocument(data)
        except Exception:
            continue
        if not model.Forms:
            continue
        row = {'file': relative, 'sha256': hashlib.sha256(data).hexdigest(), 'body_writer': 'Kit' if relative in KIT_BODIES else 'Fusion'}
        rows.append(row)
        try:
            result = ConvertGrid(model.Forms[0].Surface)
        except ValueError as error:
            row['status'] = 'refused'
            row['reason'] = str(error)
            row['native_surfaces'] = native_shapes(model)
            continue
        try:
            members = [(body.PartName, body.History.Entities) for body in model.Bodies if isinstance(body.History, JournalModel)]
            members += [(snap.Name, snap.Snapshot.Entities) for snap in model.Snapshots if isinstance(snap.Snapshot, GeometryState)]
            row['members'] = [dict(member=name.rsplit('.', 1)[-1], **compare(result, entities)) for name, entities in members]
            row['jump_margins'] = margins(result)
            if not row['members']:
                row['status'] = 'no_body'
            elif max(member['max_abs_cm'] for member in row['members']) < 1e-12:
                row['status'] = 'equal'
            else:
                row['status'] = 'different'
                row['reason'] = 'converted poles differ'
        except RuntimeError as error:
            row['status'] = 'different'
            row['reason'] = str(error)
    summary = {}
    for row in rows:
        summary[row['status']] = summary.get(row['status'], 0) + 1
    equal = [row['jump_margins'] for row in rows if row['status'] == 'equal' and row['body_writer'] == 'Fusion']
    skipped = [item['largest_skipped'] for item in equal if item['largest_skipped'] is not None]
    kept = [item['smallest_recorded'] for item in equal if item['smallest_recorded'] is not None]
    jumps = {'scope': 'Equal archives whose converted body Fusion wrote', 'equal_archives': len(equal), 'largest_skipped': max(skipped, default=None), 'smallest_recorded': min(kept, default=None), 'recorded': sum(item['recorded'] for item in equal), 'skipped': sum(item['skipped'] for item in equal)}
    report = {'scope': SCOPE, 'python': sys.version.split()[0], 'form_archives': len(rows), 'summary': summary, 'jump_margins': jumps, 'rows': rows}
    (BASE / 'GridCensus.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'rows'}, indent=1))
    for row in rows:
        print(row['status'], row['file'], row.get('reason', ''), [(m['member'], m['surfaces'], m['curves'], m['points'], m['max_abs_cm']) for m in row.get('members', [])])


if __name__ == '__main__':
    main()
