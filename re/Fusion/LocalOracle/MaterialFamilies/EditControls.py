import json
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

here = Path(__file__).resolve().parent
out = here / 'Edits'
out.mkdir(exist_ok=True)
app = adsk.core.Application.get()
original = app.activeDocument
report = {'fusion_version': app.version, 'controls': [], 'documents_before': app.documents.count}
CASES = (
    ('base', 'ABS Plastic', None, None, None),
    ('young', 'ABS Plastic', 'material', 'structural_Young_modulus', 3456789.0),
    ('poisson', 'ABS Plastic', 'material', 'structural_Poisson_ratio', 0.321),
    ('conduct', 'ABS Plastic', 'material', 'structural_Thermal_conductivity', 0.4321),
    ('expand', 'ABS Plastic', 'material', 'structural_Thermal_expansion_coefficient', 87.654),
    ('thermk', 'ABS Plastic', 'material', 'thermal_Thermal_conductivity', 0.2345),
    ('density', 'ABS Plastic', 'material', 'structural_Density', 1111.0),
    ('albedo', 'ABS Plastic', 'appearance', 'opaque_albedo', (12, 34, 56, 255)),
    ('rough', 'ABS Plastic', 'appearance', 'surface_roughness', 0.4321),
    ('gasbase', 'Air', None, None, None),
    ('gasexp', 'Air', 'material', 'structural_Thermal_expansion_coefficient', 0.00345),
)


def plain(item):
    if item is None or type(item) in (str, bool, int, float):
        return item
    if isinstance(item, (list, tuple)):
        return [plain(child) for child in item]
    if isinstance(item, adsk.core.Color):
        return [item.red, item.green, item.blue, item.opacity]
    return item.objectType


def values(items):
    result = {}
    for item in items:
        try:
            result[item.id] = plain(item.values) if getattr(item, 'hasMultipleValues', False) else plain(item.value)
        except Exception:
            result[item.id] = 'error'
    return result


def control(name, source, target, field, value):
    library = app.materialLibraries.itemByName('Fusion Material Library')
    material = library.materials.itemByName(source)
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    try:
        design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        sketch = root.sketches.add(root.xYConstructionPlane)
        sketch.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(1, 2, 0))
        body = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), adsk.core.ValueInput.createByString('30 mm'), adsk.fusion.FeatureOperations.NewBodyFeatureOperation).bodies.item(0)
        copy = design.materials.addByCopy(material, 'Kit Edit ' + name)
        body.material = copy
        if target == 'material':
            prop = copy.materialProperties.itemById(field)
            prop.value = value
        elif target == 'appearance':
            appearance = design.appearances.addByCopy(copy.appearance, 'Kit Look ' + name)
            prop = appearance.appearanceProperties.itemById(field)
            prop.value = adsk.core.Color.create(*value) if isinstance(value, tuple) else value
            body.appearance = appearance
        used = body.material
        row = {'name': name, 'material': used.name, 'appearance': body.appearance.name, 'field': field, 'set': value, 'properties': values(used.materialProperties), 'appearance_properties': values(body.appearance.appearanceProperties)}
        if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(out / (name + '.f3d')))):
            raise RuntimeError('export failed')
        report['controls'].append(row)
    finally:
        doc.close(False)


try:
    for case in CASES:
        try:
            control(*case)
        except Exception:
            report['controls'].append({'name': case[0], 'error': traceback.format_exc().splitlines()[-1]})
finally:
    if original is not None and original.isValid:
        original.activate()
    report['documents_after'] = app.documents.count
    (out / 'EditControls.json').write_text(json.dumps(report, indent=1) + '\n')
