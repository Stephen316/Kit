"""Upload view edge grafts, open each one, read its curves, update its views and export its DWG.

Usage: python3 EdgeRound.py <round tag> <label> [<label> ...] [--folder <upload folder>] [--timeout S]

Every Fusion step runs through re/Fusion/LocalOracle/RunLocked.mjs, so the agents that share Fusion take turns.
The open counts are the curves Fusion projects from the stored edges. The poke halves and restores each view
scale, which makes Fusion find the edges itself; the export after the poke keeps Fusion's own edge lists.
The round summary goes to Variants/Edges<tag>.json and each export to Exports/<label>.dwg.
"""

import argparse
import json
import subprocess
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VARIANTS = Path(tempfile.gettempdir()) / 'KitFusionDrawings' / 'Variants'
RUNNER = HERE.parents[2] / 'LocalOracle' / 'RunLocked.mjs'


def locked(script, timeout):
    started = time.monotonic()
    done = subprocess.run(['node', str(RUNNER), str(HERE / script), '--timeout', str(timeout)], capture_output=True, text=True)
    lines = [line for line in done.stdout.splitlines() if line.startswith('{')]
    outcome = json.loads(lines[-1]) if lines else {'status': 'no output', 'stderr': done.stderr[-400:]}
    outcome['wall_seconds'] = round(time.monotonic() - started, 1)
    return outcome


def write(name, value):
    (VARIANTS / name).write_text(json.dumps(value, indent=1) + '\n')


def boxes(views):
    rows = []
    for view in views:
        points = [point for curve in view.get('curves', []) for key in ('startPoint', 'endPoint', 'centerPoint') if (point := curve.get(key))]
        xs, ys = [p[0] for p in points], [p[1] for p in points]
        rows.append([round(min(xs), 4), round(min(ys), 4), round(max(xs), 4), round(max(ys), 4)] if points else None)
    return rows


def summary(row):
    keep = {key: row[key] for key in ('ready', 'open_seconds', 'open_error', 'modified_after_open') if key in row}
    opened = row.get('opened')
    if isinstance(opened, dict) and opened.get('sheets'):
        views = opened['sheets'][0].get('views', [])
        keep['open_curves'] = [view.get('curve_count') for view in views]
        keep['open_styles'] = [view.get('style') for view in views]
        keep['open_boxes'] = boxes(views)
    poked = row.get('poked')
    if isinstance(poked, dict) and poked.get('info'):
        views = poked['info']['sheets'][0].get('views', [])
        keep['update_curves'] = [view.get('curve_count') for view in views]
        keep['update_boxes'] = boxes(views)
    export = row.get('export')
    if isinstance(export, dict):
        keep['export'] = {key: export.get(key) for key in ('result', 'bytes', 'sha256')}
    return keep


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('tag')
    parser.add_argument('labels', nargs='+')
    parser.add_argument('--folder')
    parser.add_argument('--timeout', type=int, default=900)
    args = parser.parse_args()
    target = VARIANTS / ('Edges' + args.tag + '.json')
    report = {'tag': args.tag, 'labels': args.labels, 'started': time.strftime('%H:%M:%S'), 'rows': []}
    folder = args.folder
    if folder is None:
        write('Accept.json', {'tag': args.tag, 'upload_seconds': 600, 'plan': [{'kind': 'upload', 'labels': args.labels}]})
        report['upload'] = locked('AcceptDrawings.py', args.timeout)
        accepted = json.loads((VARIANTS / ('Accept' + args.tag + '.json')).read_text())
        folder = json.loads((VARIANTS / 'BeginUploads.json').read_text()).get('folder')
        report['upload_waits'] = accepted.get('upload_waits')
    report['folder'] = folder
    target.write_text(json.dumps(report, indent=1) + '\n')
    for label in args.labels:
        name = 'Ex' + label
        path = VARIANTS / ('Inspect' + name + '.json')
        if path.exists():
            path.unlink()
        write('Selection.json', {'labels': [label], 'tag': name, 'folder': folder, 'export_dwg': True, 'poke': True})
        outcome = locked('InspectUploads.py', args.timeout)
        inspected = json.loads(path.read_text()) if path.exists() else {}
        row = inspected.get('uploads', {}).get(label)
        report['rows'].append({'label': label, 'run': outcome.get('status'), 'wall_seconds': outcome.get('wall_seconds'),
                               'stage': inspected.get('stage'), 'result': summary(row) if isinstance(row, dict) else row})
        target.write_text(json.dumps(report, indent=1) + '\n')
        print(json.dumps(report['rows'][-1])[:600], flush=True)
    report['finished'] = time.strftime('%H:%M:%S')
    target.write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
