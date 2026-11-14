import collections
import json
import sys

KCAUSES = (
    'Unsupported Fusion journal qualified field',
    'Unsupported Fusion journal attribute family',
    'Unsupported Fusion journal entity kind',
)
KRECODED = ('.protein', '.smb', '.smbh')


def load(path):
    return {row['file']: row for row in json.load(open(path))['rows']}


def compare(base, head):
    before, after = load(base), load(head)
    report = {}
    report['regressions'] = sorted(name for name in before if before[name]['status'] == 'pass' and after[name]['status'] != 'pass')
    report['changed_passes'] = sorted(
        name for name in before
        if before[name]['status'] == 'pass' and after[name]['status'] == 'pass'
        and (before[name].get('differing') != after[name].get('differing') or before[name].get('emitted_sha256') != after[name].get('emitted_sha256'))
    )
    scope = sorted(name for name in before if before[name]['status'] != 'pass' and any(cause in before[name].get('error', '') for cause in KCAUSES))
    fixed = sorted(name for name in before if before[name]['status'] != 'pass' and after[name]['status'] == 'pass')
    report['scope'] = len(scope)
    report['fixed'] = fixed
    report['fixed_outside_scope'] = [name for name in fixed if name not in scope]
    report['fixed_unexpected_members'] = {name: [member for member in after[name].get('differing', []) if not member.endswith(KRECODED)] for name in fixed}
    report['fixed_unexpected_members'] = {name: members for name, members in report['fixed_unexpected_members'].items() if members}
    report['fixed_recoded_kinds'] = dict(collections.Counter(member.rsplit('.', 1)[-1] for name in fixed for member in after[name].get('differing', [])))
    report['fixed_model_equal'] = all(after[name].get('model_equal') for name in fixed)
    remaining = collections.defaultdict(list)
    for name in scope:
        if after[name]['status'] != 'pass':
            remaining[after[name]['status'] + ': ' + after[name].get('error', '')[:120]].append(name)
    report['remaining'] = dict(remaining)
    report['counts'] = {'before': dict(collections.Counter(row['status'] for row in before.values())), 'after': dict(collections.Counter(row['status'] for row in after.values()))}
    return report


if __name__ == '__main__':
    result = compare(sys.argv[1], sys.argv[2])
    text = json.dumps(result, indent=1)
    if len(sys.argv) > 3:
        open(sys.argv[3], 'w').write(text + '\n')
    print(text)
