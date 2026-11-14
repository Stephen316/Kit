"""Research: production ConvertForm against Fusion conversions of non-unit knot intervals.

Reads every Fusion-saved archive of the interval probe and of the interval
document acceptance, records whether Kit reads it, converts the stored cage
with ConvertForm and compares the Kit body with the converted body Fusion
stored, apart from the naming labels.
"""

import hashlib
import json
import sys
from dataclasses import astuple
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(BASE / 'Cages'))
from ReadConverted import ReadConverted
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.GridJumps import SpanThirds
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.ConvertForm import ConvertForm
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

WORK = ROOT / 're/Fusion/LocalOracle/FormDocuments/Intervals'


def gap(left, right):
    if len(left) != len(right):
        return float('inf')
    return max((abs(a - b) for p, q in zip(left, right) for a, b in zip(p, q, strict=True)), default=0.0)


def compare(mine, native):
    row = {'regions_equal': mine.Regions == native.Regions, 'point_gap_cm': gap(mine.PointsCm, native.PointsCm), 'surface_gap_cm': 0.0, 'curve_gap_cm': 0.0, 'pcurve_gap': 0.0, 'window_gap': 0.0, 'differences': []}
    if (len(mine.Faces), len(mine.Edges)) != (len(native.Faces), len(native.Edges)):
        row['differences'].append('face or edge count')
        return row
    for index, (left, right) in enumerate(zip(mine.Faces, native.Faces)):
        one, two = left.Surface.Cache, right.Surface.Cache
        if (one.KnotsU, one.KnotsV, one.Form, left.Surface.Jumps) != (two.KnotsU, two.KnotsV, two.Form, right.Surface.Jumps):
            row['differences'].append(f'face {index} knots, form or jumps')
        row['surface_gap_cm'] = max(row['surface_gap_cm'], gap(one.Points, two.Points))
        for use, other in zip(left.Uses, right.Uses, strict=True):
            if (use.EdgeIndex, use.Reversed, use.Pcurve.Knots) != (other.EdgeIndex, other.Reversed, other.Pcurve.Knots):
                row['differences'].append(f'face {index} pcurve use')
            row['pcurve_gap'] = max(row['pcurve_gap'], gap(use.Pcurve.Poles, other.Pcurve.Poles))
    for index, (left, right) in enumerate(zip(mine.Edges, native.Edges)):
        if (left.Curve.Knots, left.Curve.Multiplicity, left.Jumps, left.Convexity) != (right.Curve.Knots, right.Curve.Multiplicity, right.Jumps, right.Convexity):
            row['differences'].append(f'edge {index} knots, jumps or class')
        if [window.Face for window in left.Windows] != [window.Face for window in right.Windows]:
            row['differences'].append(f'edge {index} window faces')
        else:
            row['window_gap'] = max(row['window_gap'], gap([window[1:] for window in map(astuple, left.Windows)], [window[1:] for window in map(astuple, right.Windows)]))
        row['curve_gap_cm'] = max(row['curve_gap_cm'], gap(left.Curve.Poles, right.Curve.Poles))
    return row


def tangent_split(curve):
    thirds = SpanThirds(curve)
    rows = []
    for index, knot in enumerate(curve.Knots[1:-1]):
        jump = [after - before for before, after in zip(thirds[index], thirds[index + 1])]
        slope = [b - a for a, b in zip(curve.Poles[index + 1], curve.Poles[index + 2])]
        length = sum(value * value for value in slope) ** 0.5
        along = sum(a * b for a, b in zip(jump, slope)) / length
        across = max(abs(a - along * b / length) for a, b in zip(jump, slope))
        rows.append({'knot': knot, 'third_jump': max(abs(value) for value in jump), 'jump_across_tangent': across})
    return rows


def jump_study(model):
    native = ReadConverted(model)
    return [{'edge': index, 'stored_lists': edge.Jumps, 'knots': tangent_split(edge.Curve)} for index, edge in enumerate(native.Edges)]


def check(path):
    data = path.read_bytes()
    row = {'file': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest()}
    try:
        model = ReadDocument(data)
    except ValueError as error:
        row['read'] = 'ValueError: ' + str(error)
        return row
    row['read'] = 'ok'
    cage = model.Forms[0].Surface
    counts = {}
    for edge in cage.Topology.Edges:
        counts[repr(edge.KnotInterval)] = counts.get(repr(edge.KnotInterval), 0) + 1
    row['saved_intervals'] = counts
    try:
        mine = ConvertForm(cage)
    except ValueError as error:
        row['convert'] = 'ValueError: ' + str(error)
        if len(counts) > 1 and cage.Mapping is not None and len(model.Forms) == 1 and 'Plane' in row['file']:
            row['boundary_jump_study'] = jump_study(model)
        return row
    row['convert'] = 'ok'
    row.update(compare(mine, ReadConverted(model)))
    return row


def main():
    probe = json.loads((WORK / 'Probe.json').read_text())
    report = {'scope': 'Production ConvertForm against the converted bodies Fusion stored for plane grid and box cages with non-unit knot intervals, labels excluded and progenitor windows compared within their rounding gap. For refused plane grids with mixed intervals, the boundary jump study gives the parametric third-derivative jump of each stored boundary curve and its part across the control polygon direction', 'python': sys.version.split()[0], 'probe_status': probe['status'], 'documents_after': probe['documents_after'], 'archives': []}
    for cage in probe['cages']:
        for variant in cage['variants']:
            row = check(WORK / cage['cage'] / (variant['variant'] + '.f3d'))
            row['api_knots'] = variant['bodies'][0]['knots'][0] if variant.get('bodies') else None
            report['archives'].append(row)
            print(json.dumps({key: value for key, value in row.items() if key not in ('sha256', 'api_knots')}))
    documents = ROOT / 're/Fusion/LocalOracle/FormDocuments/IntervalDocuments'
    accepted = json.loads((documents / 'NativeAcceptance.json').read_text())
    report['documents'] = {'acceptance_status': accepted['status'], 'documents_after': accepted['documents_after'], 'archives': []}
    for path in sorted((documents / 'Loaded').glob('*.f3d')) + sorted((documents / 'Saved').glob('*.f3d')):
        row = check(path)
        report['documents']['archives'].append(row)
        print(json.dumps({key: value for key, value in row.items() if key not in ('sha256',)}))
    (BASE / 'IntervalCheck.json').write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
