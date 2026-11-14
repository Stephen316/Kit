import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
from convert.formats.Fusion.BrepCodec.Journal.Complex.Authoring.ExactSubtypes import SplineCurve
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.Spline.Conversion.OrderJumps import CurveOrders, SurfaceOrders
from convert.formats.Fusion.BrepCodec.Journal.Spline.IntcurveNode import IntcurveNode
from convert.formats.Fusion.BrepCodec.Journal.Spline.ListTsplines import ListTsplines
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

WORK = ROOT / 're/Fusion/LocalOracle/FormDocuments/Stencil'
TARGET = BASE / 'JumpCensus.json'


def stored_lists(curve):
    return tuple(tuple(values) for values in curve.Body.Context.Discontinuities)


def census(path):
    model = ReadDocument(path.read_bytes())
    counts = Counter()
    misses = []
    for body in model.Bodies:
        if not isinstance(body.History, JournalModel):
            continue
        entities = body.History.Entities
        if not ListTsplines(entities):
            continue
        for found in ListTsplines(entities):
            computed = SurfaceOrders(found.Cache)
            stored = tuple(tuple(values) for values in found.Jumps)
            counts['surfaces'] += 1
            counts['surface_lists_nonempty'] += sum(1 for values in stored if values)
            if computed != stored:
                misses.append({'kind': 'surface', 'face': found.FaceIndex, 'stored': stored, 'computed': computed})
        for entity in entities:
            if isinstance(entity, IntcurveNode):
                try:
                    curve = SplineCurve(entity.Curve)
                except ValueError:
                    continue
                computed = CurveOrders(curve)
                stored = stored_lists(entity.Curve)
                counts['curves'] += 1
                counts['curve_lists_nonempty'] += sum(1 for values in stored if values)
                if computed != stored:
                    misses.append({'kind': 'curve', 'stored': stored, 'computed': computed})
    return counts, misses


def main():
    groups = {'committed': [], 'probe_outputs': sorted(WORK.glob('tmp/*/*.f3d'))}
    for path in sorted(ROOT.glob('re/Fusion/**/*.f3d')):
        if 'tmp' not in path.relative_to(ROOT).parts:
            groups['committed'].append(path)
    report = {'scope': 'Discontinuity lists of every converted Form body surface and exact boundary curve against the lowest jumping derivative order rule with slack 1e-10. Probe outputs live in the ignored Stencil tmp folder and are rebuilt by PrepareStencil and ProbeStencil', 'python': sys.version.split()[0], 'groups': {}}
    seen = set()
    for group, files in groups.items():
        entry = {'files': 0, 'totals': Counter(), 'mismatched_files': []}
        for path in files:
            data = path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            if digest in seen:
                continue
            seen.add(digest)
            try:
                counts, misses = census(path)
            except Exception:
                entry['totals']['unreadable'] += 1
                continue
            if not counts:
                continue
            entry['files'] += 1
            entry['totals'].update(counts)
            entry['totals']['mismatches'] += len(misses)
            if misses:
                entry['mismatched_files'].append({'file': str(path.relative_to(ROOT)), 'sha256': digest, 'misses': misses[:4]})
        entry['totals'] = dict(sorted(entry['totals'].items()))
        report['groups'][group] = entry
        print(group, json.dumps({key: value for key, value in entry.items() if key != 'mismatched_files'}), [item['file'] for item in entry['mismatched_files']])
    TARGET.write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
