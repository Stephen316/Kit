import json
import sys
from pathlib import Path


def assets(control, label):
    rows = {}
    for asset in control['assets']:
        name = asset['definitions'].get('UIName', '')
        if label in name or asset['properties'].get('physmat_Label') == label:
            rows[asset['schema']] = asset['properties']
    return rows


def linked(control, label):
    physical = [asset for asset in control['assets'] if asset['schema'] == 'PhysMatSchema' and asset['definitions'].get('UIName') == label]
    if len(physical) != 1:
        return {'error': len(physical)}
    table = {asset['instance']: asset for asset in control['assets']}
    rows = {'PhysMatSchema': physical[0]['properties']}
    for target in physical[0]['properties']['physmat_aspects']['links']['Targets']:
        rows[table[target]['schema'] + ':' + table[target]['role']] = table[target]['properties']
    return rows


def main():
    decoded = json.loads(Path(sys.argv[1]).read_text())
    pairs = [(name, 'base') for name in ('young', 'poisson', 'conduct', 'expand', 'density')] + [('gasexp', 'gasbase')]
    for name, base in pairs:
        left = linked(decoded[base], 'Kit Edit ' + base)
        right = linked(decoded[name], 'Kit Edit ' + name)
        changes = []
        for schema in sorted(set(left) | set(right)):
            before, after = left.get(schema, {}), right.get(schema, {})
            for field in sorted(set(before) | set(after)):
                if field in ('physmat_aspects', 'AssetLibID') or 'error' in (schema,):
                    continue
                if before.get(field) != after.get(field):
                    changes.append((schema.split(':')[0], field, str(before.get(field))[:50], str(after.get(field))[:50]))
        print(name, len(left), len(right))
        for row in changes:
            print('   ', row)


if __name__ == '__main__':
    main()
