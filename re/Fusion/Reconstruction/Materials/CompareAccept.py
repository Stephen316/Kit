import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
ACCEPT = ROOT / 're/Fusion/LocalOracle/MaterialFamilies/Accept'
LISTED = (
    'structural_Density', 'structural_Young_modulus', 'structural_Poisson_ratio', 'structural_Minimum_yield_stress',
    'structural_Minimum_tensile_strength', 'structural_Thermal_conductivity', 'structural_Specific_heat',
    'structural_Thermal_expansion_coefficient', 'thermal_Density', 'thermal_Thermal_conductivity', 'thermal_Specific_heat',
)


def same(left, right):
    if isinstance(left, float) and isinstance(right, float):
        return math.isclose(left, right, rel_tol=1e-9, abs_tol=1e-12)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(same(a, b) for a, b in zip(left, right))
    return left == right


def differ(reference, kit):
    rows = []
    for name in sorted(set(reference) | set(kit)):
        left, right = reference.get(name), kit.get(name)
        if left is None or right is None:
            rows.append([name, 'missing in kit' if right is None else 'extra in kit'])
        elif not same(left.get('value'), right.get('value')) or left.get('units') != right.get('units'):
            rows.append([name, left.get('value'), left.get('units'), right.get('value'), right.get('units')])
    return rows


def main():
    plans = json.loads((ACCEPT / 'Kit' / 'Plans.json').read_text())
    summary = {}
    for path in sorted((ACCEPT / 'Result').glob('*.json')):
        if path.stem == 'Status':
            continue
        kit = json.loads(path.read_text())
        reference = json.loads((ACCEPT / 'Reference' / path.name).read_text())
        properties = differ(reference['properties'], kit['properties'])
        looks = differ(reference['appearance_properties'], kit['appearance_properties'])
        listed = [row for row in properties if row[0] in LISTED]
        plan = plans[path.stem]
        summary[path.stem] = {
            'material': reference['material'],
            'held_out': True,
            'class': plan['class'],
            'type': plan['type'],
            'schemas_match_fusion': plan['kit_schemas'] == plan['fusion_schemas'] if plan['fusion_schemas'] else None,
            'kit_schemas': plan['kit_schemas'],
            'fusion_schemas': plan['fusion_schemas'],
            'kit_sha256': hashlib.sha256((ACCEPT / 'Kit' / (path.stem + '.f3d')).read_bytes()).hexdigest(),
            'properties_compared': len(reference['properties']),
            'appearance_compared': len(reference['appearance_properties']),
            'name_match': kit['material'] == reference['material'],
            'appearance_match': kit['appearance'] == reference['appearance'],
            'mass_match': same(kit['mass_kg'], reference['mass_kg']),
            'listed_match': not listed,
            'listed_present': sorted(name for name in LISTED if name in reference['properties']),
            'property_differences': properties,
            'appearance_differences': looks,
        }
        row = summary[path.stem]
        print(path.stem, reference['material'][:22].ljust(22), 'name', row['name_match'], 'look', row['appearance_match'], 'mass', row['mass_match'], 'listed', row['listed_match'], 'schemas', row['schemas_match_fusion'], 'diffs', len(properties), len(looks))
    (ACCEPT / 'Summary.json').write_text(json.dumps(summary, indent=1) + '\n')


if __name__ == '__main__':
    main()
