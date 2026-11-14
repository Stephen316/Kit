import collections
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[4]
sys.path.insert(0, str(BASE))
from StencilFit import WORK, geometry

CAGES = ('Valence7', 'Mixed56', 'Mixed78')


def counts(layout):
    return collections.Counter(json.dumps(item[2:]) for item in layout if item[0] in ('surface', 'curve'))


def main():
    probe = json.loads((WORK / 'Probe.json').read_text())
    preparation = {cage['cage']: cage for cage in json.loads((WORK / 'Preparation.json').read_text())['cages']}
    report = {'scope': 'BRep layout of the Fusion conversion under single-grip, paired and random grip moves of the valence-7 prism and two mixed-valence band cages. A layout change means that face grouping or edge splitting depends on grip positions, so a table keyed by cage topology cannot convert the cage', 'python': sys.version.split()[0], 'cages': []}
    for cage in probe['cages']:
        if cage['cage'] not in CAGES:
            continue
        folder = WORK / 'tmp' / cage['cage']
        _, _, base = geometry(folder / 'Base.f3d')
        moves = {row['variant']: row['moves'] for row in preparation[cage['cage']]['variants']}
        changed = []
        for row in cage['variants']:
            if row['status'] != 'completed':
                continue
            _, _, layout = geometry(folder / (row['variant'] + '.f3d'))
            if layout != base:
                body = row['bodies'][0]
                changed.append({'variant': row['variant'], 'moved_grips': len(moves[row['variant']]), 'faces_edges_vertices': [body['faces'], body['edges'], body['vertices']], 'patterns_only_in_base': sum((counts(base) - counts(layout)).values()), 'patterns_only_in_variant': sum((counts(layout) - counts(base)).values())})
        first = cage['variants'][0]['bodies'][0]
        valences = preparation[cage['cage']]
        report['cages'].append({'cage': cage['cage'], 'grips': valences['grips'], 'variants': len(cage['variants']), 'base_faces_edges_vertices': [first['faces'], first['edges'], first['vertices']], 'layout_changes': changed})
        print(cage['cage'], len(changed))
    (BASE / 'LayoutDrift.json').write_text(json.dumps(report, indent=1) + '\n')


if __name__ == '__main__':
    main()
