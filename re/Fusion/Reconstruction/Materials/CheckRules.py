import collections
import json
import sys
from pathlib import Path

COPIES = {
    'structural_Young_modulus': ('_1', '_2', '_X', '_Y', '_Z'),
    'structural_Poisson_ratio': ('_12', '_23', '_X', '_Y', '_Z'),
    'structural_Shear_modulus': ('_12', '_X', '_Y', '_Z'),
    'structural_Thermal_conductivity': ('_X', '_Y', '_Z'),
    'structural_Thermal_expansion_coefficient': ('_1', '_2', '_X', '_Y', '_Z'),
    'thermal_Thermal_conductivity': ('_X', '_Y', '_Z'),
}
PAIRS = (('thermal_Density', 'structural_Density'), ('thermal_Thermal_conductivity', 'structural_Thermal_conductivity'), ('thermal_Specific_heat', 'structural_Specific_heat'))


def magnitude(value):
    return value['Magnitude'] if isinstance(value, dict) and 'Magnitude' in value else value


def close(left, right):
    return abs(left - right) <= 1e-9 * max(1.0, abs(left), abs(right))


def main():
    decoded = json.loads(Path(sys.argv[1]).read_text())
    tally = collections.defaultdict(collections.Counter)
    misses = collections.defaultdict(list)
    units = collections.defaultdict(set)
    for key, control in sorted(decoded.items()):
        assets = {asset['instance']: asset for asset in control['assets']}
        for asset in assets.values():
            props = asset['properties']
            schema = asset['schema']
            for name, value in props.items():
                if isinstance(value, dict) and 'UnitCode' in value:
                    units[value['UnitCode']].add(name)
            for main, suffixes in COPIES.items():
                if main not in props:
                    continue
                behavior = props.get('structural_Behavior' if main.startswith('structural') else 'thermal_Behavior')
                for suffix in suffixes:
                    if main + suffix not in props:
                        continue
                    same = close(magnitude(props[main + suffix]), magnitude(props[main]))
                    tally['copy %s behavior=%s' % (main, behavior)][same] += 1
                    if not same and len(misses['copy ' + main]) < 3:
                        misses['copy ' + main].append((key, suffix, behavior))
            if 'appearance' in asset['role'] and 'interior_model' in props:
                tally['interior_model ' + schema][props['interior_model']] += 1
            if 'structural_Young_modulus' in props and props.get('structural_Behavior') == 0:
                young = magnitude(props['structural_Young_modulus'])
                poisson = magnitude(props['structural_Poisson_ratio'])
                shear = magnitude(props['structural_Shear_modulus'])
                same = close(shear, young / (2 * (1 + poisson)))
                tally['shear = E/(2(1+nu))'][same] += 1
                if not same and len(misses['shear']) < 6:
                    misses['shear'].append((key, young, poisson, shear))
        for physical in [asset for asset in assets.values() if asset['schema'] == 'PhysMatSchema']:
            linked = [assets[target] for target in physical['properties']['physmat_aspects']['links']['Targets'] if target in assets]
            merged = {}
            for asset in linked:
                merged.update(asset['properties'])
            for left, right in PAIRS:
                if left in merged and right in merged:
                    same = close(magnitude(merged[left]), magnitude(merged[right]))
                    tally['pair %s=%s' % (left, right)][same] += 1
                    if not same and len(misses['pair ' + left]) < 4:
                        misses['pair ' + left].append((key, magnitude(merged[left]), magnitude(merged[right])))
    for name, counts in sorted(tally.items()):
        print(name, dict(counts))
    for name, rows in sorted(misses.items()):
        print('MISS', name, rows)
    print('UNITS', {code: sorted(names)[:3] for code, names in sorted(units.items())})


if __name__ == '__main__':
    main()
