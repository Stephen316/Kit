import bisect
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
WORK = ROOT / 're/Fusion/LocalOracle/FormDocuments/Stencil/tmp'
TARGET = BASE / 'StencilFields.json'
DENOMINATOR = 10 ** 5
QUADRATIC = 5000
SLACK = 1e-14


def rational(value):
    fraction = Fraction(value).limit_denominator(DENOMINATOR)
    return abs(float(fraction) - value) <= SLACK


def quadratic_finder(root):
    pairs = sorted(((q * root) % 1.0, q) for q in range(-QUADRATIC, QUADRATIC + 1))
    keys = [item[0] for item in pairs]

    def find(value):
        for scale in range(1, QUADRATIC + 1):
            target = (scale * value) % 1.0
            spot = bisect.bisect_left(keys, target)
            for index in (spot - 1, spot, spot + 1):
                if 0 <= index < len(keys):
                    distance = abs(keys[index] - target)
                    if min(distance, 1.0 - distance) <= SLACK * scale:
                        return scale, pairs[index][1]
        return None
    return find


def main():
    report = {'scope': 'Arithmetic of the stencil coefficients: rational with denominator up to 1e5 within 1e-14, or in Q(sqrt d) with integer parts up to 5000 within 1e-14 per unit of denominator', 'python': sys.version.split()[0], 'cages': []}
    for name in sys.argv[1:]:
        table = json.loads((WORK / (name + 'Table.json')).read_text())
        values = sorted({round(float(text), 15) for row in table['rows'] for _, text in row})
        odd = [value for value in values if not rational(value)]
        row = {'cage': name, 'distinct_coefficients': len(values), 'rational': len(values) - len(odd), 'not_rational': len(odd)}
        sample = odd[:: max(1, len(odd) // 40)][:40]
        for root_value in (2, 3, 5):
            finder = quadratic_finder(math.sqrt(root_value))
            hits = [value for value in sample if finder(value) is not None]
            row['sample_in_q_sqrt_%d' % root_value] = '%d of %d' % (len(hits), len(sample))
        row['sample_values'] = sample[:8]
        report['cages'].append(row)
        print(json.dumps(row))
    TARGET.write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
