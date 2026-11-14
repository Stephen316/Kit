"""Research: summarise Fusion's ridge crease edges across the crease probe rounds.

Reads <Round>Angles.json written by MeasureCrease.py and keeps, for every
cage, the converted edges that lie on the ridge crease. Each piece records
Fusion's stored convexity, its bounds on the shared curve and the signed
dihedral range measured on it. The output is CreaseSummary.json.
"""

import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROUNDS = ('Pilot', 'RoundOne', 'RoundTwo', 'RoundThree', 'RoundFour', 'RoundFive', 'RoundSix', 'RoundEight', 'RoundTen', 'RoundEleven')


def on_ridge(row, scale):
    if 'spans' not in row:
        return False
    return all(abs(point[0] - scale) <= 1e-6 * scale and abs(point[2] - scale) <= 1e-6 * scale for point in (row['start_cm'], row['mid_cm'], row['end_cm']))


def piece(row):
    return {
        'convexity': row['convexity'],
        'bounds': row['bounds'] or row['curve_range'],
        'max_abs_deg': row['max_abs_deg'],
        'signed_range_deg': [row['min_signed_deg'], row['max_signed_deg']],
        'start_deg': row['spans'][0]['start_deg'],
        'end_deg': row['spans'][-1]['end_deg'],
    }


def main():
    rows = []
    for name in ROUNDS:
        path = BASE / 'tmp' / (name + 'Angles.json')
        if not path.exists():
            continue
        for cage in json.loads(path.read_text())['cages']:
            entry = {'round': name, 'cage': cage['cage'], 'fold_deg_per_row': cage['design']['fold_deg_per_row'], 'scale': cage['design']['scale'], 'loose_edges': len(cage['design']['loose_edges']), 'status': cage['status']}
            if cage['status'] == 'completed':
                scale = cage['design']['scale']
                ridge = [piece(row) for row in cage['edges'] if on_ridge(row, scale)]
                ridge.sort(key=lambda item: item['bounds'][0])
                entry['faces'] = cage['faces']
                entry['edges'] = len(cage['edges'])
                entry['ridge'] = ridge
                entry['other_inner_edges'] = sorted({row['convexity'] + (' <=1deg' if row['max_abs_deg'] <= 1.0 else ' >1deg') for row in cage['edges'] if 'spans' in row and not on_ridge(row, scale)})
            rows.append(entry)
    report = {'scope': 'Fusion 2706.1.17 ridge crease edges of the crease probe cages: stored convexity and split bounds against the measured signed dihedral angle', 'python': sys.version.split()[0], 'cages': rows}
    (BASE / 'CreaseSummary.json').write_text(json.dumps(report, indent=1) + '\n')
    print(len(rows), 'cages summarised')


if __name__ == '__main__':
    main()
