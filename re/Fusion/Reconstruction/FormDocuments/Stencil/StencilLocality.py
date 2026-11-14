import json
import sys
from fractions import Fraction
from itertools import combinations
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
WORK = ROOT / 're/Fusion/LocalOracle/FormDocuments/Stencil/tmp'
TARGET = BASE / 'StencilLocality.json'
NAMES = ('Box', 'Box3', 'CreasedBox', 'Valence5', 'Valence6', 'Valence8')


def irrational_values(name):
    table = json.loads((WORK / (name + 'Table.json')).read_text())
    found = set()
    for row in table['rows']:
        for _, text in row:
            value = float(text)
            fraction = Fraction(value).limit_denominator(10 ** 5)
            if abs(float(fraction) - value) > 1e-14:
                found.add(round(value, 12))
    return found


def main():
    values = {name: irrational_values(name) for name in NAMES}
    report = {'scope': 'Shared non-rational stencil coefficients between cage layouts, rounded to 1e-12. Equal values would indicate a local cap rule that transfers between layouts', 'python': sys.version.split()[0], 'non_rational_counts': {name: len(found) for name, found in values.items()}, 'shared': []}
    for left, right in combinations(NAMES, 2):
        shared = values[left] & values[right]
        report['shared'].append({'pair': [left, right], 'shared': len(shared), 'examples': sorted(shared)[:4]})
    TARGET.write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
