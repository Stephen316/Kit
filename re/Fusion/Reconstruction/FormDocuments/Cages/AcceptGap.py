"""Research: numeric gaps of a Form acceptance report.

For each case of a NativeAcceptance.json written by AcceptStencil.py or
AcceptCageDocs.py, compares the Kit stages with the oracle stages field by
field. Vertex lists are matched as point sets, so ties that differ only in
the last bit no longer reorder them. Solid and volume flags are reported
separately from the geometric gap.
"""

import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
PAIRS = (('loaded', 'solved'), ('solved', 'solved'), ('edited', 'edited'), ('reopened', 'reopened'))
FLAGS = ('solid', 'volume_cm3')


def numbers(left, right, path, found):
    if isinstance(left, dict) and isinstance(right, dict):
        if left.keys() != right.keys():
            found['structure'].append(path + ': fields')
        for name in left.keys() & right.keys():
            if name in FLAGS:
                if left[name] != right[name] and not (isinstance(left[name], float) and isinstance(right[name], float) and abs(left[name] - right[name]) <= 1e-8 * max(1.0, abs(right[name]))):
                    found['flags'].append(f'{path}.{name}: {left[name]!r} != {right[name]!r}')
            elif name == 'vertex_cm':
                found['gap'] = max(found['gap'], point_sets(left[name], right[name], path, found))
            else:
                numbers(left[name], right[name], path + '.' + name, found)
    elif isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            found['structure'].append(f'{path}: {len(left)} != {len(right)} items')
            return
        for index, (first, second) in enumerate(zip(left, right)):
            numbers(first, second, f'{path}[{index}]', found)
    elif isinstance(left, bool) or isinstance(right, bool) or isinstance(left, str) or left is None or right is None:
        if left != right:
            found['structure'].append(f'{path}: {left!r} != {right!r}')
    elif isinstance(left, (int, float)) and isinstance(right, (int, float)):
        found['gap'] = max(found['gap'], abs(left - right))


def point_sets(left, right, path, found):
    if len(left) != len(right):
        found['structure'].append(path + '.vertex_cm: counts')
        return 0.0
    remaining = list(right)
    worst = 0.0
    for point in left:
        best = min(range(len(remaining)), key=lambda index: max(abs(a - b) for a, b in zip(point, remaining[index])))
        worst = max(worst, max(abs(a - b) for a, b in zip(point, remaining.pop(best))))
    return worst


def main():
    work = ROOT / sys.argv[1]
    source = work / 'NativeAcceptance.json'
    report = json.loads(source.read_text())
    result = {'scope': 'Numeric gaps between the Kit and oracle stages of ' + str(source.relative_to(ROOT)) + ', with vertex lists matched as point sets', 'python': sys.version.split()[0], 'acceptance_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'acceptance_status': report.get('status'), 'documents_after': report.get('documents_after'), 'cases': []}
    for case in report['cases']:
        row = {'case': case['case'], 'status': case.get('status'), 'stages': {}}
        kit, oracle = case.get('kit', {}), case.get('oracle', {})
        for left, right in PAIRS:
            if left not in kit or right not in oracle:
                row['stages'][left] = 'missing'
                continue
            found = {'gap': 0.0, 'flags': [], 'structure': []}
            numbers(kit[left]['bodies'], oracle[right]['bodies'], 'bodies', found)
            found['form_health'] = [kit[left]['form_health'], oracle[right]['form_health']]
            found['timeline_health'] = [item['health'] for item in kit[left]['timeline']]
            row['stages'][left] = found
        found = {'gap': 0.0, 'flags': [], 'structure': []}
        if 'reopened' in kit and 'edited' in kit:
            numbers(kit['reopened']['bodies'], kit['edited']['bodies'], 'bodies', found)
        row['kit_reopened_vs_edited'] = found
        row['cage_tsm_equal'] = kit.get('cage_tsm_sha256') == oracle.get('cage_tsm_sha256')
        row['areas_cm2'] = {stage: [body['area_cm2'] for body in kit[stage]['bodies']] for stage in ('loaded', 'edited') if stage in kit}
        row['volumes_cm3'] = {stage: [body['volume_cm3'] for body in kit[stage]['bodies']] for stage in ('loaded', 'edited') if stage in kit}
        result['cases'].append(row)
    target = BASE / (work.name + 'Gap.json')
    target.write_text(json.dumps(result, indent=1) + '\n')
    for row in result['cases']:
        print(row['case'], {stage: (value['gap'], len(value['flags']), value['structure'][:2]) if isinstance(value, dict) else value for stage, value in row['stages'].items()}, row['kit_reopened_vs_edited']['gap'], row['cage_tsm_equal'])


if __name__ == '__main__':
    main()
