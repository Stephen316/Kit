"""Research: where the fixed linear conversion map of a cage layout ends.

Reads the large single-grip moves of the creased cages from the probe and
reports, for each move, whether Fusion converted it, the body counts, any
refusal message, whether the converted body kept the layout of the base
cage, and the gap between the stencil prediction and the stored poles.
"""

import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(BASE))
from StencilCheck import compare, form_entities
from StencilFit import geometry
from convert.formats.Fusion.BrepCodec.Journal.Spline.Stencil.ConvertCage import ConvertCage
from convert.formats.Fusion.TSplineCodec.ReadTspline import ReadTspline

WORK = ROOT / 're/Fusion/LocalOracle/FormDocuments/Stencil'
TARGET = BASE / 'LimitProbe.json'


def main():
    probe = json.loads((WORK / 'Probe.json').read_text())
    preparation = json.loads((WORK / 'Preparation.json').read_text())
    report = {'scope': 'Large single-grip moves of the creased plane and creased box cages: Fusion conversion outcome, body counts and stencil prediction', 'python': sys.version.split()[0], 'cages': []}
    for cage in preparation['cages']:
        if cage['cage'] not in preparation.get('limits', []):
            continue
        done = {row['variant']: row for entry in probe['cages'] if entry['cage'] == cage['cage'] for row in entry['variants']}
        base = geometry(WORK / 'tmp' / cage['cage'] / 'Base.f3d') if done.get('Base', {}).get('status') == 'completed' else None
        rows = []
        for variant in cage['variants']:
            row = done.get(variant['variant'], {'status': 'not run'})
            entry = {'variant': variant['variant'], 'moves_cm': variant['moves'], 'status': row['status'], 'bodies': row.get('bodies'), 'form_health': row.get('form_health')}
            if row.get('traceback'):
                entry['messages'] = sorted(set(re.findall(r'ASM_[A-Z_]+|RuntimeError: [^\n]+', row['traceback'])))
            if row['status'] == 'completed' and base is not None:
                path = WORK / 'tmp' / cage['cage'] / (variant['variant'] + '.f3d')
                keys, _, layout = geometry(path)
                entry['layout_equal_base'] = keys == base[0] and layout == base[2]
                surface = ReadTspline((ROOT / variant['tsm_file']).read_bytes())
                if entry['layout_equal_base']:
                    check = compare(ConvertCage(surface), form_entities(path))
                    entry['stencil_gap_cm'] = max(check['surface_max'], check['curve_max'], check['point_max'])
                    entry['stencil_jumps_equal'] = check['jumps_equal']
                else:
                    entry['curves_points'] = [sum(1 for key in keys if key[0] == kind) for kind in ('s', 'c', 'p')]
                    entry['base_curves_points'] = [sum(1 for key in base[0] if key[0] == kind) for kind in ('s', 'c', 'p')]
            rows.append(entry)
        report['cages'].append({'cage': cage['cage'], 'grips': cage['grips'], 'variants': rows})
    TARGET.write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report, indent=1)[:5000])


if __name__ == '__main__':
    main()
