import hashlib
import json
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.ExactSubtypes import SplineCurve
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import IntcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.ListTsplines import ListTsplines
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

WORK = ROOT / 're/Fusion/LocalOracle/FormDocuments/Stencil'
LIMIT = 10 ** 7


def geometry(path):
    model = ReadDocument(path.read_bytes())
    for body in model.Bodies:
        if isinstance(body.History, JournalModel) and any(isinstance(e, SplineNode) and isinstance(e.Surface, TsplineSurf) for e in body.History.Entities):
            entities = body.History.Entities
            break
    else:
        raise RuntimeError('no Form body')
    keys, points, layout = [], [], []
    for found in sorted(ListTsplines(entities), key=lambda item: item.FaceIndex):
        cache = found.Cache
        layout.append(('surface', found.FaceIndex, [(k.Value, k.Count) for k in cache.KnotsU], [(k.Value, k.Count) for k in cache.KnotsV]))
        for pole, point in enumerate(cache.Points):
            keys.append(('s', found.FaceIndex, pole))
            points.append(point)
    for index, entity in enumerate(entities):
        if isinstance(entity, IntcurveNode):
            curve = SplineCurve(entity.Curve)
            layout.append(('curve', index, list(curve.Knots), list(curve.Multiplicity)))
            for pole, point in enumerate(curve.Poles):
                keys.append(('c', index, pole))
                points.append(point)
        elif isinstance(entity, PointNode):
            keys.append(('p', index, 0))
            points.append(entity.PositionCm)
    layout.append(('types', [type(entity).__name__ for entity in entities]))
    return keys, points, layout


def rational(value):
    fraction = Fraction(value).limit_denominator(LIMIT)
    return fraction, abs(float(fraction) - value)


def fit(cage):
    name = cage['cage']
    rows = {variant['variant']: variant for variant in cage['variants']}
    base_keys, base, base_layout = geometry(WORK / 'tmp' / name / 'Base.f3d')
    surface = ReadTspline((WORK / 'tmp' / name / 'Base.tsm').read_bytes())
    grips = [(grip.CoordX, grip.CoordY, grip.CoordZ) for grip in surface.Grips]
    count = len(grips)
    data = {}
    for label in rows:
        if label == 'Base':
            continue
        keys, points, layout = geometry(WORK / 'tmp' / name / (label + '.f3d'))
        if keys != base_keys or layout != base_layout:
            raise RuntimeError('layout changed in ' + label)
        data[label] = [[a - b for a, b in zip(p, q)] for p, q in zip(points, base)]
    saved = ReadDocument((WORK / 'tmp' / name / 'Base.f3d').read_bytes()).Forms[0].Surface
    valence = Counter(Counter(link.VertexIndex for link in surface.Topology.Links).values())
    result = {'cage': name, 'valences': dict(sorted(valence.items())), 'saved_topology_equal': saved.Topology == surface.Topology, 'saved_grips_equal': saved.Grips == surface.Grips, 'saved_offsets': sorted(Counter(link.ValenceOffset for link in saved.Topology.Links).items())}
    result.update({'grips': count, 'rows': len(base_keys), 'surfaces': sum(1 for item in base_layout if item[0] == 'surface'), 'curves': sum(1 for item in base_layout if item[0] == 'curve'), 'points': sum(1 for item in base_keys if item[0] == 'p')})
    if 'X0' not in data:
        return result, None, base_keys, base
    steps = [rows['X%d' % index]['moves'][str(index)][0] for index in range(count)]
    columns = [[delta[0] / steps[index] for delta in data['X%d' % index]] for index in range(count)]
    cross = max(abs(delta[axis]) / steps[index] for index in range(count) for delta in data['X%d' % index] for axis in (1, 2))
    checks = {'cross_axis_max': cross}
    for label, variant in rows.items():
        moves = {int(key): value for key, value in variant['moves'].items()}
        if label in ('Base',) or label.startswith('X'):
            continue
        worst = 0.0
        for row in range(len(base_keys)):
            for axis in range(3):
                predicted = sum(columns[index][row] * move[axis] for index, move in moves.items())
                worst = max(worst, abs(predicted - data[label][row][axis]))
        checks[label] = worst
    sums = [sum(columns[index][row] for index in range(count)) for row in range(len(base_keys))]
    checks['partition_of_unity_max'] = max(abs(value - 1.0) for value in sums)
    tables, residuals, denominators, support = [], [], Counter(), Counter()
    for row in range(len(base_keys)):
        entries = []
        for index in range(count):
            value = columns[index][row]
            if abs(value) < 1e-13:
                continue
            fraction, error = rational(value)
            residuals.append(error)
            denominators[fraction.denominator] += 1
            entries.append((index, fraction, value))
        support[len(entries)] += 1
        tables.append(entries)
    worst_base = 0.0
    worst_exact = 0.0
    for row, entries in enumerate(tables):
        for axis in range(3):
            float_sum = sum(value * grips[index][axis] for index, _, value in entries)
            exact = float(sum(fraction * Fraction(grips[index][axis]) for index, fraction, _ in entries))
            worst_base = max(worst_base, abs(float_sum - base[row][axis]))
            worst_exact = max(worst_exact, abs(exact - base[row][axis]))
        exact_sum = sum(fraction for _, fraction, _ in entries)
        if exact_sum != 1:
            checks.setdefault('rational_rows_not_unity', 0)
            checks['rational_rows_not_unity'] += 1
    checks['base_from_float_columns_max'] = worst_base
    checks['base_from_rational_table_max'] = worst_exact
    checks['rational_residual_max'] = max(residuals)
    result['checks'] = checks
    result['support_sizes'] = dict(sorted(support.items()))
    result['denominators'] = dict(sorted(denominators.items()))
    return result, tables, base_keys, base


def predict(cage, fitted):
    name = cage['cage']
    surface = ReadTspline((WORK / 'tmp' / name / 'Base.tsm').read_bytes())
    for other, (topology, crease, keys, tables) in fitted.items():
        if topology != surface.Topology or crease != surface.Creases:
            continue
        checks = {'model_from': other}
        for variant in cage['variants']:
            label = variant['variant']
            grips = ReadTspline((WORK / 'tmp' / name / (label + '.tsm')).read_bytes()).Grips
            vectors = [(g.CoordX, g.CoordY, g.CoordZ) for g in grips]
            got_keys, points, _ = geometry(WORK / 'tmp' / name / (label + '.f3d'))
            if got_keys != keys:
                checks[label] = 'layout differs'
                continue
            worst = 0.0
            worst_exact = 0.0
            for row, entries in enumerate(tables):
                for axis in range(3):
                    value = sum(coefficient * vectors[index][axis] for index, _, coefficient in entries)
                    exact = float(sum(fraction * Fraction(vectors[index][axis]) for index, fraction, _ in entries))
                    worst = max(worst, abs(value - points[row][axis]))
                    worst_exact = max(worst_exact, abs(exact - points[row][axis]))
            checks[label] = {'float_table_max': worst, 'rational_table_max': worst_exact}
        return checks
    return None


def main():
    preparation = json.loads((WORK / 'Preparation.json').read_text())
    report = {'scope': 'Linearity of Fusion T-spline conversion in the grip coordinates, from single-grip probes; rational recovery of the coefficients', 'python': sys.version.split()[0], 'cages': []}
    fitted = {}
    chosen = set(sys.argv[1:])
    for cage in preparation['cages']:
        if chosen and cage['cage'] not in chosen or cage['cage'] in preparation.get('limits', ()):
            continue
        result, tables, keys, base = fit(cage)
        if tables is None:
            result['prediction'] = predict(cage, fitted)
        else:
            surface = ReadTspline((WORK / 'tmp' / cage['cage'] / 'Base.tsm').read_bytes())
            fitted[cage['cage']] = (surface.Topology, surface.Creases, keys, tables)
        report['cages'].append(result)
        print(json.dumps(result))
        if tables is not None:
            out = {'cage': cage['cage'], 'keys': keys, 'layout': geometry(WORK / 'tmp' / cage['cage'] / 'Base.f3d')[2], 'rows': [[[index, repr(value)] for index, _, value in entries] for entries in tables]}
            (WORK / 'tmp' / (cage['cage'] + 'Table.json')).write_text(json.dumps(out))
    (WORK / 'Fit.json').write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
