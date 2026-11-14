import dataclasses
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.BrepCodec.Journal.Complex.Grammar.GrammarValue import ChoiceValue
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Spline.SplineNode import SplineNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.TsplineSurf import TsplineSurf
from convert.formats.Fusion.DocumentCodec.Auxiliary.Form.SwapFormCage import SwapFormCage
from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

WORK = ROOT / 're/Fusion/LocalOracle/FormDocuments/Stencil'
TARGET = BASE / 'StencilSwapCheck.json'
IGNORED = ('UnixMicros', 'PrimaryId', 'VersionCount')


def form_entities(model):
    for body in model.Bodies:
        if isinstance(body.History, JournalModel) and any(isinstance(e, SplineNode) and isinstance(e.Surface, TsplineSurf) for e in body.History.Entities):
            return body.History.Entities
    raise RuntimeError('no Form body')


def walk(left, right, path, gaps, other):
    if type(left) is not type(right):
        other[path + ': type'] += 1
    elif type(left) is float:
        gaps[path] = max(gaps.get(path, 0.0), abs(left - right))
    elif type(left) is tuple:
        if len(left) != len(right):
            other[path + ': length'] += 1
            return
        for one, two in zip(left, right):
            walk(one, two, path, gaps, other)
    elif isinstance(left, ChoiceValue):
        walk(left.Body, right.Body, path, gaps, other)
    elif dataclasses.is_dataclass(left):
        for field in dataclasses.fields(left):
            if field.name not in IGNORED:
                walk(getattr(left, field.name), getattr(right, field.name), path + '/' + type(left).__name__ + '.' + field.name, gaps, other)
    elif left != right:
        other[path] += 1


def main():
    preparation = json.loads((WORK / 'Preparation.json').read_text())
    probe = json.loads((WORK / 'Probe.json').read_text())
    done = {(cage['cage'], row['variant']): row for cage in probe['cages'] for row in cage['variants'] if row['status'] == 'completed'}
    chosen = set(sys.argv[1:])
    report = {'scope': 'SwapFormCage on the Fusion base archive of each probe cage, written and read back, against the Fusion archive converted from the same variant cage', 'python': sys.version.split()[0], 'cages': []}
    for cage in preparation['cages']:
        name = cage['cage']
        if chosen and name not in chosen or (name, 'Base') not in done:
            continue
        base_path = WORK / 'tmp' / name / 'Base.f3d'
        model = ReadDocument(base_path.read_bytes())
        summary = {'cage': name, 'base_sha256': hashlib.sha256(base_path.read_bytes()).hexdigest(), 'variants': 0, 'refused': [], 'roundtrip_equal': True, 'gaps': {}, 'other_differences': Counter()}
        for variant in cage['variants']:
            label = variant['variant']
            row = done.get((name, label))
            tsm = WORK / 'tmp' / name / (label + '.tsm')
            saved = tsm.with_suffix('.f3d')
            if row is None or label == 'Base' or hashlib.sha256(tsm.read_bytes()).hexdigest() != row.get('tsm_sha256', variant['tsm_sha256']) or hashlib.sha256(saved.read_bytes()).hexdigest() != row['saved_sha256']:
                continue
            try:
                swapped = SwapFormCage(model, ReadTspline(tsm.read_bytes()))
            except ValueError as error:
                summary['refused'].append([label, str(error)])
                continue
            summary['variants'] += 1
            if ReadDocument(EmitParsed(swapped)) != swapped:
                summary['roundtrip_equal'] = False
            fusion = ReadDocument(saved.read_bytes())
            walk(form_entities(swapped), form_entities(fusion), 'entities', summary['gaps'], summary['other_differences'])
            walk(swapped.Forms[0].Surface, fusion.Forms[0].Surface, 'cage', summary['gaps'], summary['other_differences'])
        summary['gaps'] = {key: value for key, value in sorted(summary['gaps'].items()) if value > 0.0}
        summary['other_differences'] = dict(summary['other_differences'])
        report['cages'].append(summary)
        print(json.dumps(summary))
    TARGET.write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
