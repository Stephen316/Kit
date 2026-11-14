"""Research: print the crease edges of a measured round, one line per edge."""

import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent


def main():
    for name in sys.argv[1:]:
        data = json.loads((BASE / 'tmp' / (name + 'Angles.json')).read_text())
        for cage in data['cages']:
            if cage['status'] != 'completed':
                print(cage['cage'], cage['status'])
                continue
            interior = [row for row in cage['edges'] if 'spans' in row and (row['max_abs_deg'] < 45.0 or row['convexity'] != 'unknown')]
            print('%-22s faces %d edges %d' % (cage['cage'], cage['faces'], len(cage['edges'])))
            for row in interior:
                spans = ' '.join('[%.3g,%.3g] %s%.4f..%.4f' % (span['range'][0], span['range'][1], ''.join('+' if sign else '-' for sign in span['signs']) or '0', span['min_abs_deg'], span['max_abs_deg']) for span in row['spans'])
                print('   e%-3d %-8s bounds %-28s mid %s | %s' % (row['edge'], row['convexity'], row['bounds'], [round(value, 3) for value in row['mid_cm']], spans))


if __name__ == '__main__':
    main()
