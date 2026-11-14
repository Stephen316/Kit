import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SWEEP = ROOT / 're/Fusion/LocalOracle/MaterialFamilies/Sweep'


def main():
    decoded = json.loads(Path(sys.argv[1]).read_text())
    rows = []
    for key, value in sorted(decoded.items()):
        observed = json.loads((SWEEP / (key + '.json')).read_text())
        row = {'key': key, 'material': observed['material'], 'appearance': observed['appearance'], 'library_id': observed['material_id']}
        if 'error' in value:
            row['error'] = value['error']
            rows.append(row)
            continue
        assets = {asset['instance']: asset for asset in value['assets']}
        physical = [asset for asset in value['assets'] if asset['schema'] == 'PhysMatSchema']
        chosen = [asset for asset in physical if asset['definitions'].get('UIName') == observed['material_id']] or [asset for asset in physical if asset['properties'].get('physmat_Label') == observed['material']]
        if len(physical) == 1:
            chosen = physical
        if not chosen:
            chosen = [asset for asset in physical if asset['definitions'].get('UIName') != 'PrismMaterial-018']
        if len(chosen) != 1:
            row['error'] = 'physical asset not unique: %d' % len(chosen)
            rows.append(row)
            continue
        material = chosen[0]
        props = material['properties']
        row.update({key2: props.get(key2) for key2 in ('physmat_class', 'physmat_classification', 'physmat_Type', 'physmat_Label', 'physmat_Keywords', 'category', 'description', 'keyword')})
        links = props['physmat_aspects']['links']
        row['aspects_enabled'] = links['Enabled']
        row['aspects'] = []
        for target in links['Targets']:
            asset = assets.get(target)
            if asset is None:
                row['aspects'].append({'missing': target})
                continue
            aspect = {'schema': asset['schema'], 'role': asset['role'], 'name': asset['definitions'].get('UIName')}
            for field in ('structural_subclass', 'thermal_subclass', 'structural_Behavior', 'thermal_Behavior', 'category'):
                if field in asset['properties']:
                    aspect[field] = asset['properties'][field]
            row['aspects'].append(aspect)
        rows.append(row)
    Path(sys.argv[2]).write_text(json.dumps(rows, indent=1) + '\n')


if __name__ == '__main__':
    main()
