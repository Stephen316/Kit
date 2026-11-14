import json
import sys


def rows(path):
    data = json.load(open(path))
    return data['counts'], {row['file']: row for row in data['rows']}


def differing(row):
    found = set(row.get('differing') or ())
    for child in row.get('children') or ():
        found |= {child['member'] + '!' + name for name in child.get('differing') or ()}
    return found


if __name__ == '__main__':
    before_counts, before = rows(sys.argv[1])
    after_counts, after = rows(sys.argv[2])
    print('before', before_counts, 'after', after_counts)
    for name in sorted(set(before) | set(after)):
        old, new = before.get(name, {}), after.get(name, {})
        if old.get('status') != new.get('status'):
            print('status', name, old.get('status'), '->', new.get('status'), new.get('error', '')[:120])
        elif old.get('status') == 'pass' and differing(old) != differing(new):
            print('members', name, sorted(differing(new) - differing(old)), sorted(differing(old) - differing(new)))
        elif old.get('error') != new.get('error'):
            print('error', name, old.get('error', '')[:80], '->', new.get('error', '')[:120])
