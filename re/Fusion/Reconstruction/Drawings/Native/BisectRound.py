"""Upload a set of variants and open each one in its own guarded Fusion run.

Usage: BisectRound.py <round tag> <label> [<label> ...] [--folder <upload folder>] [--stall S]

Each Fusion step runs through RunGuarded.mjs, so the oracle lock is held only while one step drives Fusion,
and a stalled open restarts Fusion under that lock before the next variant opens. The round summary goes to
Variants/Bisect<tag>.json.
"""

import argparse
import json
import subprocess
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VARIANTS = Path(tempfile.gettempdir()) / 'KitFusionDrawings' / 'Variants'
RUNNER = HERE / 'RunGuarded.mjs'


def guarded(script, *extra, timeout=1800):
    started = time.monotonic()
    done = subprocess.run(['node', str(RUNNER), str(HERE / script), '--timeout', str(timeout), *extra], capture_output=True, text=True)
    lines = [line for line in done.stdout.splitlines() if line.startswith('{')]
    outcome = json.loads(lines[-1]) if lines else {'status': 'no output', 'stderr': done.stderr[-400:]}
    outcome['wall_seconds'] = round(time.monotonic() - started, 1)
    return outcome


def write(name, value):
    (VARIANTS / name).write_text(json.dumps(value, indent=1) + '\n')


def upload(tag, labels):
    write('Accept.json', {'tag': tag, 'upload_seconds': 600, 'plan': [{'kind': 'upload', 'labels': labels}]})
    outcome = guarded('AcceptDrawings.py', '--events', str(VARIANTS / ('Events' + tag + '.json')), '--label', 'upload ' + tag)
    report = json.loads((VARIANTS / ('Accept' + tag + '.json')).read_text())
    return outcome, report.get('folders', [None])[0], report.get('upload_waits')


def summary(row):
    if not isinstance(row, dict):
        return {'raw': str(row)[:300]}
    keep = {key: row[key] for key in ('ready', 'open_seconds', 'open_error', 'modified_after_open', 'missing_folder') if key in row}
    opened = row.get('opened')
    if isinstance(opened, dict) and opened.get('sheets'):
        sheet = opened['sheets'][0]
        keep['views'] = [view.get('curve_count') for view in sheet.get('views', [])]
        keep['dimensions'] = sheet.get('dimensions')
        keep['sheet_mm'] = [sheet.get('width'), sheet.get('height')]
    return keep


def inspect(tag, label, folder, stall, poke=False):
    name = 'Bx' + label
    path = VARIANTS / ('Inspect' + name + '.json')
    if path.exists():
        path.unlink()
    write('Selection.json', {'labels': [label], 'tag': name, 'folder': folder, 'export_dwg': False, 'poke': poke})
    outcome = guarded('InspectUploads.py', '--watch', str(path), '--stall', str(stall), '--events', str(VARIANTS / ('Events' + tag + '.json')), '--label', label)
    report = json.loads(path.read_text()) if path.exists() else {}
    row = report.get('uploads', {}).get(label)
    return {'label': label, 'guard': {key: outcome.get(key) for key in ('status', 'stage', 'age', 'dialog', 'windows', 'wall_seconds')}, 'restart': (outcome.get('restart') or {}).get('seconds'), 'result': summary(row) if row is not None else None, 'stage': report.get('stage')}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('tag')
    parser.add_argument('labels', nargs='+')
    parser.add_argument('--folder')
    parser.add_argument('--stall', type=int, default=60)
    parser.add_argument('--poke', action='store_true', help='after open, halve and restore each view scale and count curves')
    args = parser.parse_args()
    target = VARIANTS / ('Bisect' + args.tag + '.json')
    round_report = {'tag': args.tag, 'labels': args.labels, 'started': time.strftime('%H:%M:%S'), 'rows': []}
    folder = args.folder
    if folder is None:
        outcome, folder, waits = upload(args.tag, args.labels)
        round_report['upload'] = {'status': outcome.get('status'), 'wall_seconds': outcome.get('wall_seconds'), 'waits': waits}
    round_report['folder'] = folder
    target.write_text(json.dumps(round_report, indent=1) + '\n')
    for label in args.labels:
        row = inspect(args.tag, label, folder, args.stall, args.poke)
        round_report['rows'].append(row)
        target.write_text(json.dumps(round_report, indent=1) + '\n')
        print(json.dumps(row), flush=True)
    round_report['finished'] = time.strftime('%H:%M:%S')
    target.write_text(json.dumps(round_report, indent=1) + '\n')


if __name__ == '__main__':
    main()
