import json
import time
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

here = Path(__file__).resolve().parent
out = here / 'Sweep'
out.mkdir(exist_ok=True)
budget = 480
app = adsk.core.Application.get()
original = app.activeDocument
started = time.time()
rows = json.loads((here / 'SweepList.json').read_text())
status = {'fusion_version': app.version, 'done': 0, 'failed': [], 'documents_before': app.documents.count}


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
            if getattr(item, 'hasMultipleValues', False):
                result[item.id] = plain(item.values)
            elif hasattr(item, 'value'):
                result[item.id] = plain(item.value)
        except Exception:
            result[item.id] = 'error'
    return result


def control(row):
    library = app.materialLibraries.itemByName(row['library'])
    material = library.materials.itemById(row['id'])
    if material is None or material.name != row['material']:
        raise RuntimeError('Library material moved')
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    try:
        design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        sketch = root.sketches.add(root.xYConstructionPlane)
        sketch.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(1, 2, 0))
        extrude = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), adsk.core.ValueInput.createByString('30 mm'), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        body = extrude.bodies.item(0)
        body.name = 'KitMatBody'
        body.material = material
        physical = body.getPhysicalProperties(adsk.fusion.CalculationAccuracy.VeryHighCalculationAccuracy)
        used = body.material
        appearance = body.appearance
        observed = {'key': row['key'], 'library': row['library'], 'material': used.name, 'material_id': used.id, 'appearance': appearance.name if appearance else None, 'appearance_id': appearance.id if appearance else None, 'mass_kg': physical.mass, 'volume_cm3': physical.volume, 'density_kg_cm3': physical.density, 'properties': values(used.materialProperties), 'appearance_properties': values(appearance.appearanceProperties) if appearance else None}
        target = out / (row['key'] + '.f3d')
        if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(target))):
            raise RuntimeError('Archive export failed')
        (out / (row['key'] + '.json')).write_text(json.dumps(observed, indent=1) + '\n')
    finally:
        doc.close(False)


try:
    for row in rows:
        if time.time() - started > budget:
            break
        if (out / (row['key'] + '.json')).exists():
            continue
        try:
            control(row)
            status['done'] += 1
        except Exception:
            status['failed'].append({'key': row['key'], 'error': traceback.format_exc().splitlines()[-1]})
    status['remaining'] = sum(1 for row in rows if not (out / (row['key'] + '.json')).exists())
finally:
    if original is not None and original.isValid:
        original.activate()
    status['documents_after'] = app.documents.count
    (here / 'SweepStatus.json').write_text(json.dumps(status, indent=1) + '\n')
