import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from Sweep import documents


def index(label):
    report = json.loads((BASE / f'Sweep-{label}.json').read_text())
    return {name: item for row in report['rows'] for name, item in documents(row)}


def state(item):
    material = item.get('material', {})
    native = material.get('native', {})
    graph = material.get('graph', {})
    return {
        'read': item['read'],
        'model': item.get('model'),
        'round': item.get('round'),
        'native': (native.get('status'), native.get('digest')),
        'graph': (graph.get('status'), graph.get('digest')),
    }


def main():
    before, after = index(sys.argv[1]), index(sys.argv[2])
    changes = {'fixed': [], 'broken': [], 'model': [], 'round': [], 'native': [], 'graph': [], 'missing': []}
    for name in sorted(set(before) | set(after)):
        if name not in before or name not in after:
            changes['missing'].append(name)
            continue
        old, new = state(before[name]), state(after[name])
        if old['read'] != 'pass' and new['read'] == 'pass':
            changes['fixed'].append(name)
            continue
        if old['read'] == 'pass' and new['read'] != 'pass':
            changes['broken'].append(name)
            continue
        if old['read'] != 'pass':
            continue
        for key in ('model', 'round', 'native', 'graph'):
            if old[key] != new[key]:
                changes[key].append(name)
    print(json.dumps({key: len(value) for key, value in changes.items()}))
    for key, value in changes.items():
        for name in value[:int(sys.argv[3]) if len(sys.argv) > 3 else 5]:
            print(key, name)


if __name__ == '__main__':
    main()
