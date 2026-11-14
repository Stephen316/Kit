"""Research: Fusion conversion of box cages with non-unit grip weights.

Reads the probe archives of the weighted box cages and of the unit box,
reports whether the converted surfaces are rational, compares the weighted
conversions with the unit-weight conversion, and checks superposition and
scaling of grip moves at fixed weights.
"""

import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(BASE))
from StencilFit import geometry
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Spline.ListTsplines import ListTsplines
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

WORK = ROOT / 're/Fusion/LocalOracle/FormDocuments/Stencil'
TARGET = BASE / 'WeightProbe.json'


def spread(left, right):
    return max(abs(a - b) for p, q in zip(left, right, strict=True) for a, b in zip(p, q, strict=True))


def caches(path):
    model = ReadDocument(path.read_bytes())
    for body in model.Bodies:
        if isinstance(body.History, JournalModel) and ListTsplines(body.History.Entities):
            found = ListTsplines(body.History.Entities)
            return model, [item.Cache for item in found]
    raise RuntimeError('no Form body')


def delta(points, base):
    return [[a - b for a, b in zip(p, q)] for p, q in zip(points, base)]


def main():
    probe = json.loads((WORK / 'Probe.json').read_text())
    rows = {(cage['cage'], row['variant']): row for cage in probe['cages'] for row in cage['variants']}
    report = {'scope': 'Fusion conversion of box cages with non-unit grip weights against the unit-weight box and against grip-move superposition', 'python': sys.version.split()[0], 'cases': {}}
    unit_keys, unit_points, unit_layout = geometry(WORK / 'tmp' / 'Box' / 'Base.f3d')
    for name, variants in (('BoxWeightUniform', ('Base',)), ('BoxWeighted', ('Base', 'X0', 'X3', 'Pair0_3', 'Scale0', 'RandomA'))):
        case = {'variants': {}}
        report['cases'][name] = case
        data = {}
        for label in variants:
            row = rows.get((name, label), {'status': 'not run'})
            entry = {'status': row['status'], 'bodies': row.get('bodies'), 'form_health': row.get('form_health')}
            case['variants'][label] = entry
            if row['status'] != 'completed':
                entry['traceback_tail'] = row.get('traceback', '').strip().splitlines()[-1:] if row.get('traceback') else None
                continue
            path = WORK / 'tmp' / name / (label + '.f3d')
            try:
                model, found = caches(path)
                keys, points, layout = geometry(path)
            except Exception as error:
                entry['read'] = f'{type(error).__name__}: {error}'
                continue
            entry['read'] = 'ok'
            entry['weights'] = sorted({grip.Weight for grip in model.Forms[0].Surface.Grips})
            entry['surface_forms'] = sorted({repr((cache.DegreeU, cache.DegreeV, cache.ClosureU, cache.ClosureV, cache.SingularU, cache.SingularV)) for cache in found})
            entry['layout_equal_unit'] = keys == unit_keys and layout == unit_layout
            if entry['layout_equal_unit']:
                entry['gap_to_unit_cm'] = spread(points, unit_points)
            data[label] = (keys, points, layout)
        if name == 'BoxWeighted' and all(label in data for label in variants):
            base = data['Base'][1]
            same = all(data[label][0] == data['Base'][0] and data[label][2] == data['Base'][2] for label in variants)
            case['layout_constant'] = same
            if same:
                x0, x3 = delta(data['X0'][1], base), delta(data['X3'][1], base)
                pair, scale = delta(data['Pair0_3'][1], base), delta(data['Scale0'][1], base)
                case['superposition_gap_cm'] = max(abs(p - a - b) for row_p, row_a, row_b in zip(pair, x0, x3) for p, a, b in zip(row_p, row_a, row_b))
                case['scaling_gap_cm'] = max(abs(s - 2.5 * a) for row_s, row_a in zip(scale, x0) for s, a in zip(row_s, row_a))
                case['cross_axis_max_cm'] = max(abs(value) for row in x0 + x3 for value in row[1:])
                unit_x0 = geometry(WORK / 'tmp' / 'Box' / 'X0.f3d')[1]
                unit_delta = delta(unit_x0, unit_points)
                case['x0_response_gap_to_unit_cm'] = max(abs(a - b) for row_a, row_b in zip(x0, unit_delta) for a, b in zip(row_a, row_b))
    TARGET.write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report, indent=1)[:4000])


if __name__ == '__main__':
    main()
