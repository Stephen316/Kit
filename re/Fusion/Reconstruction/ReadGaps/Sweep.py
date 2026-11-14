import collections
import concurrent.futures
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
PYTHON = '/opt/homebrew/bin/python3.14'
SUFFIXES = {'.f3d', '.f3z', '.f2d'}


def tracked():
    output = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, capture_output=True, check=True).stdout
    names = [name.decode() for name in output.split(b'\0') if name]
    return sorted(name for name in names if Path(name).suffix.lower() in SUFFIXES)


def run(name, deep, timeout):
    command = [PYTHON, '-I', str(BASE / 'SweepOne.py'), name] + (['deep'] if deep else [])
    try:
        done = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=timeout, text=True)
    except subprocess.TimeoutExpired:
        return {'file': name, 'read': 'fail', 'class': 'Timeout', 'message': f'over {timeout} s'}
    lines = done.stdout.strip().splitlines()
    if done.returncode or not lines:
        tail = done.stderr.strip().splitlines()[-1:] or ['no output']
        return {'file': name, 'read': 'fail', 'class': 'Crash', 'message': tail[0][:200], 'code': done.returncode}
    return json.loads(lines[-1])


def documents(row):
    if row.get('kind') == 'bundle' and row.get('read') == 'pass':
        for child in row['members']:
            if child['kind'] != 'other':
                yield f"{row['file']} member {child['member']}", child
    else:
        yield row['file'], row


def cause(item):
    return f"{item.get('class')}: {item.get('message')}"


def summary(rows):
    files = collections.Counter(row.get('read') for row in rows)
    kinds = collections.Counter()
    reads = collections.Counter()
    rounds = collections.Counter()
    native = collections.Counter()
    graph = collections.Counter()
    causes = collections.Counter()
    natives = collections.Counter()
    graphs = collections.Counter()
    for name, item in (pair for row in rows for pair in documents(row)):
        kinds[item.get('kind', 'design')] += 1
        reads[item['read']] += 1
        if item['read'] != 'pass':
            causes[cause(item)] += 1
            continue
        if 'round' in item:
            rounds[item['round']] += 1
        if 'material' in item:
            first = item['material']['native']
            second = item['material']['graph']
            native[first['status']] += 1
            graph[second['status']] += 1
            if first['status'] == 'fail':
                natives[cause(first)] += 1
            if second['status'] == 'fail':
                graphs[cause(second)] += 1
    return {
        'files': len(rows),
        'file_reads': dict(files),
        'documents': dict(kinds),
        'document_reads': dict(reads),
        'round_trips': dict(rounds),
        'native_material': dict(native),
        'graph_material': dict(graph),
        'read_causes': dict(causes.most_common()),
        'native_causes': dict(natives.most_common()),
        'graph_causes': dict(graphs.most_common()),
    }


def write(path, report):
    head = {key: value for key, value in report.items() if key != 'rows'}
    lines = [json.dumps(row, separators=(',', ':')) for row in report['rows']]
    text = json.dumps(head, indent=1)[:-2] + ',\n "rows": [\n' + ',\n'.join(lines) + '\n ]\n}\n'
    json.loads(text)
    path.write_text(text)


def main():
    label = sys.argv[1]
    deep = 'deep' in sys.argv[2:]
    timeout = 900
    names = tracked()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        rows = list(pool.map(lambda name: run(name, deep, timeout), names))
    report = {'label': label, 'python': PYTHON, 'deep': deep, 'summary': summary(rows), 'rows': rows}
    write(BASE / f'Sweep-{label}.json', report)
    print(json.dumps(report['summary'], indent=1)[:4000])


if __name__ == '__main__':
    main()
