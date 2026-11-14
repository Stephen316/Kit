import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FAMILIES = ('loft_spl_sur', 'cl_loft_spl_sur', 'sweep_sur', 'srf_srf_v_bl_spl_sur', 'VBL_SURF', 'exact_spl_sur', 'g2_blend_spl_sur')


def main():
    inventory = json.loads((HERE / 'Inventory.json').read_text())
    verify = json.loads((HERE / 'VerifyComplex.json').read_text())
    exact = {item['sha256'] for item in verify['members'] if item.get('exact')}
    rows = []
    for item in inventory:
        if not item['member'].endswith('.smbh') or item['sha256'] not in exact:
            continue
        kinds = sorted({name.split(':')[1] for name in item['subtypes'] if name.split(':')[1] in FAMILIES})
        if kinds:
            size = (ROOT / item['path']).stat().st_size
            rows.append((kinds, size, item['path'], sum(item['names'].values())))
    for family in FAMILIES:
        print('==', family)
        for kinds, size, path, records in sorted((row for row in rows if family in row[0]), key=lambda row: row[1])[:8]:
            print(f'  {size:>8} {records:>6} {path} {kinds}')


if __name__ == '__main__':
    main()
