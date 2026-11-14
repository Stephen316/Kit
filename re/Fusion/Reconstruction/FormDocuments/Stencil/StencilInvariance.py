import dataclasses
import json
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import ChoiceValue
from convert.formats.Fusion.BrepCodec.Journal.Complex.Spline.BsCurve import BsCurve
from convert.formats.Fusion.BrepCodec.Journal.Complex.Typed.CurveRecords import CurveContext
from convert.formats.Fusion.BrepCodec.Journal.Geometry.PointNode import PointNode
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Spline.NubsSurface import NubsSurface
from convert.formats.Fusion.BrepCodec.Journal.Spline.PcurveNode import PcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.TSplineCodec.Model.TsplineSurface import TsplineSurface

WORK = ROOT / 're/Fusion/LocalOracle/FormDocuments/Stencil'
TARGET = BASE / 'StencilInvariance.json'


def mask(value):
    if isinstance(value, NubsSurface):
        return dataclasses.replace(value, Points=())
    if isinstance(value, TsplineSurf):
        return dataclasses.replace(value, Cache=mask(value.Cache), Jumps=(), Subtrans=mask(value.Subtrans))
    if isinstance(value, TsplineSurface):
        return dataclasses.replace(value, Grips=(), Header=dataclasses.replace(value.Header, VersionCount=0))
    if isinstance(value, BsCurve) and value.Dimension == 3:
        return dataclasses.replace(value, Poles=())
    if isinstance(value, PointNode):
        return dataclasses.replace(value, PositionCm=())
    if isinstance(value, CurveContext):
        value = dataclasses.replace(value, Discontinuities=((), (), ()))
    if isinstance(value, ChoiceValue):
        return ChoiceValue(value.ChoiceKey, mask(value.Body))
    if type(value) is tuple:
        return tuple(mask(item) for item in value)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclasses.replace(value, **{field.name: mask(getattr(value, field.name)) for field in dataclasses.fields(value) if field.init})
    return value


def form_entities(model):
    for body in model.Bodies:
        if isinstance(body.History, JournalModel) and any(isinstance(e, SplineNode) and isinstance(e.Surface, TsplineSurf) for e in body.History.Entities):
            return body.History.Entities
    raise RuntimeError('no Form body')


def describe(left, right, path='entity'):
    if type(left) is not type(right):
        return [path + ': type']
    if type(left) is tuple:
        if len(left) != len(right):
            return [path + ': length']
        return [found for index, (one, two) in enumerate(zip(left, right)) for found in describe(one, two, path + '[%d]' % index)]
    if dataclasses.is_dataclass(left):
        return [found for field in dataclasses.fields(left) for found in describe(getattr(left, field.name), getattr(right, field.name), path + '.' + field.name)]
    if isinstance(left, ChoiceValue):
        return describe(left.Body, right.Body, path + '.choice')
    return [] if left == right else [path]


def main():
    preparation = json.loads((WORK / 'Preparation.json').read_text())
    probe = json.loads((WORK / 'Probe.json').read_text())
    done = {(cage['cage'], row['variant']) for cage in probe['cages'] for row in cage['variants'] if row['status'] == 'completed'}
    report = {'scope': 'Converted Form body of every probe variant against its base after masking surface poles, jump lists, boundary curve poles and lists, vertex points and cage grips', 'python': sys.version.split()[0], 'cages': []}
    for cage in preparation['cages']:
        name = cage['cage']
        if (name, 'Base') not in done:
            continue
        base = form_entities(ReadDocument((WORK / 'tmp' / name / 'Base.f3d').read_bytes()))
        masked = mask(base)
        differences = Counter()
        noise = {'pcurve_fit_max': 0.0, 'pcurve_pole_offset_max': 0.0}
        compared = 0
        for variant in cage['variants']:
            label = variant['variant']
            if label == 'Base' or (name, label) not in done:
                continue
            other = mask(form_entities(ReadDocument((WORK / 'tmp' / name / (label + '.f3d')).read_bytes())))
            compared += 1
            for found in describe(masked, other):
                if not found.startswith('entity['):
                    differences['structure ' + found + ' in ' + label] += 1
                    continue
                index = int(found[len('entity['):found.index(']')])
                differences[type(base[index]).__name__ + found[found.index(']') + 1:]] += 1
            for entity in form_entities(ReadDocument((WORK / 'tmp' / name / (label + '.f3d')).read_bytes())):
                if isinstance(entity, PcurveNode):
                    curve, fit = entity.Curve.Body.Spline, entity.Curve.Body.FitTolerance
                    noise['pcurve_fit_max'] = max(noise['pcurve_fit_max'], fit)
                    noise['pcurve_pole_offset_max'] = max([noise['pcurve_pole_offset_max']] + [abs(value - round(value * 4) / 4) for pole in curve.Poles for value in pole])
        row = {'cage': name, 'entities': len(base), 'entity_types': dict(Counter(type(item).__name__ for item in base)), 'variants_compared': compared, 'masked_differences': dict(sorted(differences.items())), 'pcurve_noise': noise}
        report['cages'].append(row)
        print(json.dumps(row))
    TARGET.write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
