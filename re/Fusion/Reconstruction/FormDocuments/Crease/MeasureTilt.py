"""Research: measure the wide-root split terms on Fusion's saved crease cages.

For every Fusion-saved crease probe archive under LocalOracle/FormDocuments/Crease/tmp
(or only the rounds named on the command line), take each crease curve whose
edge has one off-knot sign change with both sides unknown and the root not
turned (the case ClassifyEdges handles with WidePieces). Report the terms of
the rule in CreaseSplitNotes.md, computed by the ClassifyEdges helpers:

- root r, the cage knots, and the tangent run ends first and last;
- the 1 degree crossings a and b nearest r, and the half widths r - a, b - r;
- tilt, the relative difference of the crossing slopes |turn'(b)| and |turn'(a)|;
- the cut Fusion made, and the cut RootSplit predicts (or "raise").

Ties (symmetric cages) and real asymmetry separate by tilt at KTangentTurn^2.
Writes CreaseTilt.json.
"""

import json
import sys
from functools import partial
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(BASE.parent / 'Cages'))
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil import ClassifyEdges as Rule
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from ReadConverted import ReadConverted

SAVES = ROOT / 're/Fusion/LocalOracle/FormDocuments/Crease/tmp'
TARGET = BASE / 'CreaseTilt.json'


def wide_root(measure, spans, knots):
    starts = [0] + [index for index in range(1, len(spans)) if abs(spans[index][0][1]) <= Rule.KFlatTurn]
    if len(starts) != 2:
        return None
    try:
        return starts[1] if Rule.IsWideRoot(measure, spans, starts[1], knots) else None
    except ValueError:
        return None


def crossing_rates(measure, spans, index, reach):
    step = Rule.KSeamSlack * reach
    places = [Rule.CrossPlace(measure, spans, index, toward) for toward in (-1.0, 1.0)]
    rates = [abs(measure(place + step) - measure(place - step)) / (2.0 * step) for place in places]
    return places, rates


def measure_group(body, sides, members):
    curve = body.Edges[members[0]].Curve
    ranges = [Rule.EdgeRange(body.Edges[index]) for index in members]
    lower, upper = ranges[0][0], ranges[-1][1]
    measure = partial(Rule.TurnAngle, curve, sides[members[0]])
    spans = Rule.EdgeSpans(curve, sides[members[0]], lower, upper)
    index = wide_root(measure, spans, curve.Knots)
    if index is None:
        return None
    root = spans[index][0][0]
    cage = Rule.CageKnots(curve.Knots, lower, upper)
    place = max(order for order, value in enumerate(cage) if value < root)
    row = {'root': round(root, 9), 'cage': [round(value, 9) for value in cage], 'fusion_cuts': [round(value[1], 9) for value in ranges[:-1]]}
    try:
        row['run'] = list(Rule.RunEnds(measure, spans, cage, (place, root)))
        (cross_a, cross_b), (rate_a, rate_b) = crossing_rates(measure, spans, index, cage[-1] - cage[0])
        row.update(a=round(cross_a, 9), b=round(cross_b, 9), half_left=round(root - cross_a, 9), half_right=round(cross_b - root, 9))
        row.update(rate_a=rate_a, rate_b=rate_b, tilt=(rate_b - rate_a) / max(rate_a, rate_b))
    except ValueError:
        row['run'] = None
    try:
        mark = Rule.RootSplit(curve, measure, spans, index, curve.Knots)
        row['predicted_cut'] = round(root if mark is None else mark, 9)
    except ValueError:
        row['predicted_cut'] = 'raise'
    return row


def main():
    rounds = sys.argv[1].split(',') if len(sys.argv) > 1 else sorted(path.name for path in SAVES.iterdir() if path.is_dir())
    rows = []
    for name in rounds:
        for path in sorted((SAVES / name).glob('*.f3d')):
            try:
                body = ReadConverted(ReadDocument(path.read_bytes()))
                sides = Rule.EdgeSides(body)
                groups = Rule.CurveGroups(body, sides)
            except Exception:
                continue
            for members in groups:
                row = measure_group(body, sides, members)
                if row is not None:
                    rows.append({'round': name, 'case': path.stem, **row})
    limit = Rule.KTangentTurn * Rule.KTangentTurn
    ties = [abs(row['tilt']) for row in rows if 'tilt' in row and abs(row['tilt']) <= limit]
    leans = [abs(row['tilt']) for row in rows if 'tilt' in row and abs(row['tilt']) > limit]
    summary = {'cases': len(rows), 'tie_limit': limit, 'largest_tie': max(ties, default=None), 'smallest_lean': min(leans, default=None)}
    summary['matches'] = sum(1 for row in rows if row['predicted_cut'] != 'raise' and row['fusion_cuts'] == [row['predicted_cut']])
    summary['raises'] = sum(1 for row in rows if row['predicted_cut'] == 'raise')
    TARGET.write_text(json.dumps({'summary': summary, 'rows': rows}, indent=1) + '\n')
    print(json.dumps(summary))
    for row in rows:
        if row['predicted_cut'] != 'raise' and row['fusion_cuts'] != [row['predicted_cut']]:
            print('DIFFERENT', row['round'], row['case'], row['fusion_cuts'], row['predicted_cut'])


if __name__ == '__main__':
    main()
