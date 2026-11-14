import collections
import json
import sys


def load(path):
    return {row['file']: row for row in json.load(open(path))['rows']}


def kinds(row):
    names = set(row.get('differing', []))
    for child in row.get('children', []):
        names.update(child.get('differing', []))
    return sorted(name.rsplit('.', 1)[-1] if '.' in name.rsplit('/', 1)[-1] else name.rsplit('/', 1)[-1] for name in names)


before, after = load(sys.argv[1]), load(sys.argv[2])
moves = collections.Counter()
for name in sorted(set(before) | set(after)):
    left, right = before.get(name, {}), after.get(name, {})
    moves[(left.get('status'), right.get('status'))] += 1
    if left.get('status') == 'pass' and right.get('status') != 'pass':
        print('REGRESSION', name, right.get('error'))
    elif left.get('status') == right.get('status') == 'pass' and set(left.get('differing', [])) != set(right.get('differing', [])):
        print('DIFFERING CHANGED', name, left.get('differing'), right.get('differing'))
    elif left.get('status') != 'pass' and right.get('status') == 'pass':
        print('FIXED', name, kinds(right))
    elif left.get('status') != 'pass' and left.get('error') != right.get('error'):
        print('MOVED', name, left.get('error'), '->', right.get('error'))
print(dict(moves))
