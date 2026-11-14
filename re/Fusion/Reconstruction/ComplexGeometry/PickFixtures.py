"""Pick the smallest byte-exact corpus member for every complex type, for tests."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ENTITIES = ('spline-surface', 'intcurve-curve', 'pcurve', 'tcoedge-coedge', 'tedge-edge', 'tvertex-vertex')


def main():
    inventory = json.loads((HERE / 'Inventory.json').read_text())
    verify = json.loads((HERE / 'VerifyComplex.json').read_text())
    exact = {item['sha256'] for item in verify['members'] if item.get('exact')}
    members_per_path = {}
    for item in inventory:
        members_per_path.setdefault((item['path'], item['member'][-5:].endswith('smbh')), []).append(item)
    picks = {}
    for item in inventory:
        if item['sha256'] not in exact:
            continue
        kind = 'smbh' if item['member'].endswith('.smbh') else 'smb'
        if len(members_per_path[(item['path'], kind == 'smbh')]) != 1:
            continue
        size = (ROOT / item['path']).stat().st_size
        keys = [f'{kind}:{name}' for name in item['subtypes']]
        keys += [f'{kind}:{name.split(":", 1)[1]}' for name in item['names'] if name.split(':', 1)[1] in ENTITIES]
        for key in keys:
            if key not in picks or size < picks[key][0]:
                picks[key] = (size, item['path'])
    for key in sorted(picks):
        print(f'{key:45} {picks[key][0]:>8} {picks[key][1]}')


if __name__ == '__main__':
    main()
