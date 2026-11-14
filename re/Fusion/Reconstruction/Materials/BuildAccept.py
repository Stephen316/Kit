import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'src'))

from convert.adapters.Fusion.State.EncodeState import EncodeState
from convert.formats.Fusion.DocumentCodec.EmitDocument import EmitDocument
from convert.formats.Fusion.DocumentCodec.Materials.Model.DirectionValue import DirectionValue
from convert.formats.Fusion.DocumentCodec.Materials.Model.FinishSpec import FinishSpec
from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import MaterialSpec
from convert.formats.Fusion.DocumentCodec.Materials.Model.MechanicSpec import MechanicSpec
from convert.formats.Fusion.DocumentCodec.Materials.Model.ThermalSpec import ThermalSpec
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue

FAMILIES = ROOT / 're/Fusion/LocalOracle/MaterialFamilies'
VOCABULARY = ROOT / 'src/convert/formats/Fusion/DocumentCodec/Materials/Vocabulary/MaterialSchemas.json'
TO_SI = {
    'Kilopascal': 1e3, 'Pascal': 1.0, 'KilogramPerCubicMeter': 1.0, 'WattPerMeterKelvin': 1.0,
    'JoulePerGramCelsius': 1e3, 'JoulePerGram': 1e3, 'MicrometerPerMeterCelsius': 1e-6, 'InvCelsius': 1.0,
    'Unitless': 1.0, 'Centipoise': 1e-3, 'OhmMeter': 1.0, 'NanogramPerPascalSecondSquareMeter': 1e-12,
    'MilliMeter': 1.0,
}
MECHANIC = {
    'YoungModulus': ['structural_Young_modulus'], 'PoissonRatio': ['structural_Poisson_ratio'],
    'ShearModulus': ['structural_Shear_modulus'], 'YieldStrength': ['structural_Minimum_yield_stress'],
    'TensileStrength': ['structural_Minimum_tensile_strength'], 'Conductivity': ['structural_Thermal_conductivity'],
    'SpecificHeat': ['structural_Specific_heat'], 'Expansion': ['structural_Thermal_expansion_coefficient'],
    'Damping': ['structural_Damping_coefficient'], 'AverageModulus': ['structural_wood_Average_modulus'],
    'Bending': ['structural_wood_Bending'], 'CompressAlong': ['structural_wood_compression_parallel'],
    'CompressAcross': ['structural_wood_compression_perpendicular'], 'ShearAlong': ['structural_wood_shear_parallel'],
    'TensionAlong': ['structural_wood_tension_parallel'], 'TensionAcross': ['structural_wood_tension_perpendicular'],
}
DIRECTIONS = ('1', '2', '12', '23', 'X', 'Y', 'Z')
THERMAL = {
    'Density': ['thermal_Density'], 'Conductivity': ['thermal_Thermal_conductivity'],
    'SpecificHeat': ['thermal_Specific_heat'], 'Emissivity': ['thermal_Emissivity'],
    'Resistivity': ['thermal_Electrical_resistivity'], 'Permeability': ['thermal_Permeability'],
    'Porosity': ['thermal_Porosity'], 'Reflectivity': ['thermal_Reflectivity'],
    'Compressibility': ['thermal_Compressibility'], 'Viscosity': ['thermal_Gas_viscosity', 'thermal_Liquid_viscosity'],
    'VaporPressure': ['thermal_Vapor_pressure'], 'Vaporization': ['thermal_Specific_heat_of_vaporization'],
}
FINISH = {
    'Roughness': ['surface_roughness'], 'Anisotropy': ['surface_anisotropy'], 'Rotation': ['surface_rotation'],
    'Reflectance': ['opaque_f0', 'layered_f0'], 'ScatterDistance': ['opaque_mfp'], 'Refraction': ['transparent_ior'],
    'ColorDepth': ['transparent_distance'], 'LayerFraction': ['layered_fraction'], 'LayerRoughness': ['layered_roughness'],
}
FINISH_COLORS = {'Tint': ['surface_albedo'], 'ScatterColor': ['opaque_mfp_modifier'], 'LayerColor': ['layered_bottom_f0']}
MAIN_COLORS = ['metal_f0', 'opaque_albedo', 'transparent_color', 'layered_diffuse']
CLASSES = ('Plastic', 'Metal', 'Wood', 'Gas', 'Liquid', 'Generic')


def choices(field):
    found = {}

    def walk(node):
        if isinstance(node, dict):
            attributes = dict(node.get('Attributes', []))
            if node.get('TagName') == 'Choice' and attributes.get('id') == field:
                for child in node.get('Children', []):
                    entry = dict(child['Attributes'])
                    found[entry['id']] = (entry['label'], int(entry['val']))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(json.loads(VOCABULARY.read_text()))
    return found


def pick(rows, names):
    present = [name for name in names if name in rows]
    if len(present) > 1:
        raise ValueError('Two places for one value')
    return rows[present[0]] if present else None


def number(rows, names):
    row = pick(rows, names)
    return None if row is None else row['value'] * TO_SI[row.get('units', 'Unitless')]


def color(value):
    return ColorValue(*(channel / 255 for channel in value))


def spec(observed):
    rows = observed['properties']
    looks = observed['appearance_properties']
    label = choices('physmat_Type')[rows['physmat_Type']['value']][0]
    steps = []
    for key, names in MECHANIC.items():
        for direction in DIRECTIONS:
            copy = names[0] + '_' + direction
            if names[0] in rows and copy in rows and rows[copy]['value'] != rows[names[0]]['value']:
                steps.append(DirectionValue(key, direction, number(rows, [copy])))
    behavior = pick(rows, ['structural_Behavior'])
    mechanics = MechanicSpec(
        **{key: number(rows, names) for key, names in MECHANIC.items()},
        Behavior=None if behavior is None else choices('structural_Behavior')[behavior['value']][0],
        Directional=tuple(steps),
    )
    thermal = None
    if any(name.startswith('thermal_') for name in rows):
        flag = pick(rows, ['thermal_Transmits_light'])
        thermal = ThermalSpec(**{key: number(rows, names) for key, names in THERMAL.items()}, TransmitsLight=None if flag is None else flag['value'])
    spaces = {row['value'] for name, row in looks.items() if name.endswith('_colorspace')}
    if len(spaces) > 1:
        raise ValueError('Mixed colorspaces')
    space_ids = choices('surface_albedo_colorspace')
    translucent = pick(looks, ['opaque_translucency'])
    finish = FinishSpec(
        NameValue=observed['appearance'],
        Metallic='metal_f0' in looks,
        ColorSpace=space_ids[spaces.pop()][1] if spaces else None,
        Translucent=None if translucent is None else translucent['value'],
        **{key: number(looks, names) for key, names in FINISH.items()},
        **{key: (None if pick(looks, names) is None else color(pick(looks, names)['value'])) for key, names in FINISH_COLORS.items()},
    )
    return MaterialSpec(
        observed['material'],
        number(rows, ['structural_Density']),
        color(pick(looks, MAIN_COLORS)['value']),
        label if label in CLASSES else 'Generic',
        mechanics,
        thermal,
        finish,
        label,
    )


def schemas(package, label=None):
    assets = {asset.InstanceId: asset for asset in package.Assets}
    physical = [asset for asset in package.Assets if asset.SchemaName == 'PhysMatSchema']
    if label is not None:
        physical = [asset for asset in physical if dict((entry.FieldName, entry.Value) for entry in asset.Definitions).get('UIName') != 'PrismMaterial-018']
    if len(physical) != 1:
        raise ValueError('Physical asset not unique')
    links = {entry.FieldName: entry for entry in physical[0].Properties}['physmat_aspects'].Connections
    return sorted(assets[target].SchemaName for target in links.Targets)


def main():
    reference = FAMILIES / 'Accept' / 'Reference'
    target = FAMILIES / 'Accept' / 'Kit'
    target.mkdir(parents=True, exist_ok=True)
    plans = {}
    for path in sorted(reference.glob('*.json')):
        if path.stem == 'Status':
            continue
        observed = json.loads(path.read_text())
        material = spec(observed)
        document = DocumentSpec('Kit ' + path.stem, 'bodyHeight', 30.0, ProfileKind='cuboid', WidthMm=10.0, DepthMm=20.0, Material=material)
        payload = EmitDocument(document)
        (target / (path.stem + '.f3d')).write_bytes(payload)
        kit = schemas(ReadDocument(payload).Materials[0].Package)
        sweep = FAMILIES / 'Sweep' / (('M319' if path.stem == 'W01' else path.stem) + '.f3d')
        fusion = None
        if sweep.exists():
            model = ReadDocument(sweep.read_bytes())
            fusion = schemas([entry for entry in model.Materials if any(asset.SchemaName == 'PhysMatSchema' for asset in entry.Package.Assets)][0].Package, 'library')
        plans[path.stem] = {'class': material.ClassName, 'type': material.TypeName, 'kit_schemas': kit, 'fusion_schemas': fusion, 'input': EncodeState(material)}
        print(path.stem, material.ClassName, material.TypeName, 'same' if kit == fusion else ('DIFF', kit, fusion))
    (target / 'Plans.json').write_text(json.dumps(plans, indent=1) + '\n')


if __name__ == '__main__':
    main()
