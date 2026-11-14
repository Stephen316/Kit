import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 're/Fusion/Reconstruction/FormDocuments/Topology'))
from SavedBodies import read_saved  # noqa: E402
from convert.formats.Fusion.BrepCodec.Journal.Spline.Converted.ConvertForm import ConvertForm  # noqa: E402
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline  # noqa: E402

WORK = ROOT / 're/Fusion/LocalOracle/FormDocuments/Stencil'
TARGET = BASE / 'StencilCheck.json'


def gap(left, right):
    if len(left) != len(right):
        return float('inf')
    return max((abs(a - b) for p, q in zip(left, right) for a, b in zip(p, q, strict=True)), default=0.0)


def weight_gap(left, right):
    if len(left) != len(right):
        return float('inf')
    return max((abs(a - b) for a, b in zip(left, right)), default=0.0)


def compare(result, native):
    """Kit FormBody against the FormBody read from a Fusion save, element by element in order."""
    row = {'surface_max': 0.0, 'curve_max': 0.0, 'point_max': 0.0, 'layout_equal': True, 'jumps_equal': True}
    counts = (len(result.Faces), len(result.Edges), len(result.PointsCm))
    if counts != (len(native.Faces), len(native.Edges), len(native.PointsCm)) or result.Regions != native.Regions:
        row['layout_equal'] = False
        return row
    for mine, theirs in zip(result.Faces, native.Faces):
        left, right = mine.Surface.Cache, theirs.Surface.Cache
        if replace(left, Points=(), Weights=()) != replace(right, Points=(), Weights=()):
            row['layout_equal'] = False
        if [(use.EdgeIndex, use.Reversed) for use in mine.Uses] != [(use.EdgeIndex, use.Reversed) for use in theirs.Uses]:
            row['layout_equal'] = False
        row['surface_max'] = max(row['surface_max'], gap(left.Points, right.Points), weight_gap(left.Weights, right.Weights))
        if mine.Surface.Jumps != theirs.Surface.Jumps:
            row['jumps_equal'] = False
    for mine, theirs in zip(result.Edges, native.Edges):
        if (mine.StartVertex, mine.EndVertex, mine.Convexity) != (theirs.StartVertex, theirs.EndVertex, theirs.Convexity):
            row['layout_equal'] = False
        if replace(mine.Curve, Poles=(), Weights=()) != replace(theirs.Curve, Poles=(), Weights=()):
            row['layout_equal'] = False
        row['curve_max'] = max(row['curve_max'], gap(mine.Curve.Poles, theirs.Curve.Poles), weight_gap(mine.Curve.Weights, theirs.Curve.Weights))
        if mine.Jumps != theirs.Jumps:
            row['jumps_equal'] = False
    row['point_max'] = gap(result.PointsCm, native.PointsCm)
    return row


def main():
    preparation = json.loads((WORK / 'Preparation.json').read_text())
    probe = json.loads((WORK / 'Probe.json').read_text())
    done = {(cage['cage'], row['variant']): row for cage in probe['cages'] for row in cage['variants'] if row['status'] == 'completed'}
    report = {'scope': 'Kit cage conversion (general rules, no stencil tables) of every probe cage against the Fusion conversion stored in the saved archive', 'python': sys.version.split()[0], 'converter': 'src ConvertForm (general cage rules) against the body read from the Fusion save, in element order', 'cages': []}
    for cage in preparation['cages']:
        name = cage['cage']
        rows = []
        for variant in cage['variants']:
            label = variant['variant']
            probe_row = done.get((name, label))
            tsm = WORK / 'tmp' / name / (label + '.tsm')
            saved = tsm.with_suffix('.f3d')
            if probe_row is None or hashlib.sha256(tsm.read_bytes()).hexdigest() != probe_row.get('tsm_sha256', variant['tsm_sha256']) or hashlib.sha256(saved.read_bytes()).hexdigest() != probe_row['saved_sha256']:
                continue
            try:
                result = ConvertForm(ReadTspline(tsm.read_bytes()))
            except ValueError as error:
                rows.append({'variant': label, 'refused': str(error)})
                continue
            row = {'variant': label}
            row.update(compare(result, read_saved(saved).body))
            rows.append(row)
        if not rows:
            continue
        measured = [row for row in rows if 'refused' not in row]
        summary = {'cage': name, 'variants': len(rows), 'refused': len(rows) - len(measured)}
        if measured:
            summary['old_tables'] = 'fitted from this cage' if name in preparation['fitted'] else 'not fitted from this cage'
            summary['surface_max'] = max(row['surface_max'] for row in measured)
            summary['curve_max'] = max(row['curve_max'] for row in measured)
            summary['point_max'] = max(row['point_max'] for row in measured)
            summary['layout_equal'] = all(row['layout_equal'] for row in measured)
            summary['jumps_equal'] = all(row['jumps_equal'] for row in measured)
            summary['jumps_unequal_variants'] = [row['variant'] for row in measured if not row['jumps_equal']]
        else:
            summary['refusal'] = rows[0]['refused']
        report['cages'].append(summary)
        print(json.dumps(summary))
    TARGET.write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
