import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from Scope import CAUSES


# compares a base and a head Census.py report: fixed files with their former cause, regressions, new differing members
def main():
    base = json.loads(Path(sys.argv[1]).read_text())
    head = json.loads(Path(sys.argv[2]).read_text())
    before = {row['file']: row for row in base['rows']}
    after = {row['file']: row for row in head['rows']}
    passing = [name for name in before if before[name]['status'] == 'pass']
    fixed = sorted(name for name in before if before[name]['status'] != 'pass' and after[name]['status'] == 'pass')
    in_scope = sorted(name for name in before if any(cause in before[name].get('error', '') for cause in CAUSES))
    report = {
        'scope': 'Census.py all on the base commit and on this branch, compared file by file',
        'base_counts': base['counts'],
        'head_counts': head['counts'],
        'regressions': [name for name in passing if after[name]['status'] != 'pass'],
        'new_differing_members': {
            name: sorted(set(after[name].get('differing', [])) - set(before[name].get('differing', [])))
            for name in passing
            if after[name]['status'] == 'pass' and set(after[name].get('differing', [])) - set(before[name].get('differing', []))
        },
        'changed_output_of_passing_files': [name for name in passing if after[name].get('emitted_sha256') != before[name].get('emitted_sha256')],
        'fixed': [
            {'file': name, 'former_error': before[name].get('error'), 'differing_kinds': sorted({member.rsplit('.', 1)[-1] for member in after[name]['differing']})}
            for name in fixed
        ],
        'in_scope_remaining': [
            {'file': name, 'former_error': before[name].get('error'), 'error': after[name].get('error'), 'where': after[name].get('where')}
            for name in in_scope
            if after[name]['status'] != 'pass'
        ],
    }
    Path(__file__).with_name('CensusDelta.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'fixed'}, indent=1))
    print(len(report['fixed']), 'fixed')


if __name__ == '__main__':
    main()
