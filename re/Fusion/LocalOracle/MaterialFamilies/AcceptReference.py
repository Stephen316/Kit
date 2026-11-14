import json
import time
import traceback
from pathlib import Path

import adsk.core
import adsk.fusion

here = Path(__file__).resolve().parent
out = here / 'Accept' / 'Reference'
out.mkdir(parents=True, exist_ok=True)
budget = 600
app = adsk.core.Application.get()
original = app.activeDocument
started = time.time()
cases = json.loads((here / 'AcceptList.json').read_text())['cases']
status = {'fusion_version': app.version, 'done': [], 'failed': [], 'documents_before': app.documents.count}


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
        row = {'type': item.objectType.split('::')[-1]}
        try:
            row['value'] = plain(item.values) if getattr(item, 'hasMultipleValues', False) else plain(item.value)
        except Exception:
            row['value'] = 'error'
        try:
            row['units'] = item.units
        except Exception:
            pass
        result[item.id] = row
    return result


def observe(design, key):
    bodies = design.rootComponent.bRepBodies
    if bodies.count != 1:
        raise RuntimeError('Expected one body')
    body = bodies.item(0)
    physical = body.getPhysicalProperties(adsk.fusion.CalculationAccuracy.VeryHighCalculationAccuracy)
    used = body.material
    appearance = body.appearance
    return {'key': key, 'material': used.name, 'material_id': used.id, 'appearance': appearance.name, 'appearance_id': appearance.id, 'mass_kg': physical.mass, 'volume_cm3': physical.volume, 'density_kg_cm3': physical.density, 'properties': values(used.materialProperties), 'appearance_properties': values(appearance.appearanceProperties)}


def reference(case):
    library = app.materialLibraries.itemByName(case['library'])
    material = library.materials.itemById(case['id'])
    if material is None or material.name != case['material']:
        raise RuntimeError('Library material moved')
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    try:
        design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        sketch = root.sketches.add(root.xYConstructionPlane)
        sketch.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(1, 2, 0))
        body = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), adsk.core.ValueInput.createByString('30 mm'), adsk.fusion.FeatureOperations.NewBodyFeatureOperation).bodies.item(0)
        if 'copy' in case:
            copy = design.materials.addByCopy(material, case['copy'])
            body.material = copy
            for field, value in case['edits'].items():
                copy.materialProperties.itemById(field).value = value
        else:
            body.material = material
        observed = observe(design, case['key'])
        (out / (case['key'] + '.json')).write_text(json.dumps(observed, indent=1) + '\n')
    finally:
        doc.close(False)


try:
    for case in cases:
        if time.time() - started > budget:
            break
        try:
            reference(case)
            status['done'].append(case['key'])
        except Exception:
            status['failed'].append({'key': case['key'], 'error': traceback.format_exc().splitlines()[-1]})
finally:
    if original is not None and original.isValid:
        original.activate()
    status['documents_after'] = app.documents.count
    (out / 'Status.json').write_text(json.dumps(status, indent=1) + '\n')
