"""Summarize the Fusion rounds that changed the sheet default fields of unknown meaning.

Reads Variants/PlanUnknowns.json, the EdgeRound reports Edges<tag>.json, the BisectRound reports Bisect<tag>.json
and the inspect reports InspectEx<label>.json, and writes GraftRoundUnknowns.json next to this script.

Each variant gets its edits, its digests and one outcome: opened (Fusion opened it with no message), damaged (Fusion
showed its "has been damaged" message on open) or stalled (the open did not finish and no message was found).
Only labels, field names, values, digests, counts and timings are kept. Document names and dialog text are not.

Run: python3.14 -I SummarizeUnknowns.py --tags Unknowns1 Unknowns2 ... Unknowns12 --damaged-by-hand Y1Zeros
"""

import argparse
import json
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
VARIANTS = Path(tempfile.gettempdir()) / 'KitFusionDrawings' / 'Variants'
DAMAGED = 'has been damaged'


def load(name):
    path = VARIANTS / name
    return json.loads(path.read_text()) if path.exists() else None


def edge_rows(tag):
    report = load('Edges' + tag + '.json') or {}
    for row in report.get('rows', []):
        result = row.get('result') or {}
        if result.get('ready'):
            yield row['label'], {'outcome': 'opened', 'round': tag, 'open_seconds': result.get('open_seconds'), 'views': result.get('open_curves'), 'boxes': result.get('open_boxes')}


def inspect_row(label):
    report = load('InspectEx' + label + '.json') or {}
    row = (report.get('uploads') or {}).get(label) or {}
    opened = row.get('opened') or {}
    sheets = opened.get('sheets') or [{}]
    return row, [view.get('curve_count') for view in sheets[0].get('views', [])]


def bisect_rows(tag):
    report = load('Bisect' + tag + '.json') or {}
    for row in report.get('rows', []):
        guard = row.get('guard') or {}
        result = row.get('result') or {}
        status = guard.get('status')
        if status == 'dialog' and DAMAGED in (guard.get('dialog') or ''):
            yield row['label'], {'outcome': 'damaged', 'round': tag, 'seconds_to_message': guard.get('age')}
        elif status == 'completed' and result.get('ready'):
            yield row['label'], {'outcome': 'opened', 'round': tag, 'open_seconds': result.get('open_seconds'), 'views': result.get('views'), 'dimensions': result.get('dimensions')}
        else:
            yield row['label'], {'outcome': 'stalled' if status == 'stalled' else str(status), 'round': tag, 'seconds': guard.get('age')}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tags', nargs='+', required=True)
    parser.add_argument('--damaged-by-hand', nargs='*', default=[], help='labels whose damage message was read and answered by hand')
    args = parser.parse_args()
    plan = load('PlanUnknowns.json')
    outcomes = {}
    for tag in args.tags:
        for label, row in [*edge_rows(tag), *bisect_rows(tag)]:
            outcomes.setdefault(label, []).append(row)
    for label in args.damaged_by_hand:
        row, views = inspect_row(label)
        outcomes.setdefault(label, []).append({'outcome': 'damaged', 'round': 'by hand', 'continue_pressed': True, 'open_seconds': row.get('open_seconds'), 'views_after_continue': views})
    grafts = {}
    for variant in plan['variants']:
        label = variant['label']
        grafts[label] = {
            'sha256': variant['sha256'],
            'dwg_sha256': variant['dwg_sha256'],
            'objects': variant['objects'],
            'edits': [{key: edit[key] for key in ('class', 'part', 'field', 'old', 'new')} for edit in variant['edits']],
            'runs': outcomes.get(label, []),
        }
    record = {
        'fusion_version': '2706.1.17',
        'route': 'object-level grafts on the A3 control (D0Plain base, BuildUnknowns.py); only the fields named in each edit change',
        'run': 'Native/EdgeRound.py and Native/BisectRound.py: upload, open, read the views; RunGuarded.mjs reads any message dialog',
        'base': plan['base'],
        'base_objects': plan['base_objects'],
        'grafts': grafts,
    }
    out = HERE / 'GraftRoundUnknowns.json'
    out.write_text(json.dumps(record, indent=1) + '\n')
    print(json.dumps({label: [run['outcome'] for run in graft['runs']] for label, graft in grafts.items()}))


if __name__ == '__main__':
    main()
