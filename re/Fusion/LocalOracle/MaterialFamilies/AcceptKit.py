import json
import time
import traceback
from pathlib import Path

import adsk.core
import adsk.fusion

here = Path(__file__).resolve().parent
source = here / 'Accept' / 'Kit'
out = here / 'Accept' / 'Result'
out.mkdir(parents=True, exist_ok=True)
budget = 600
app = adsk.core.Application.get()
original = app.activeDocument
started = time.time()
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


def accept(path):
    doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(path)))
    if doc is None:
        raise RuntimeError('Kit document did not open')
    try:
        design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
        if not design.computeAll():
            raise RuntimeError('Kit document did not compute')
        observed = observe(design, path.stem)
        observed['design_materials'] = [design.materials.item(index).name for index in range(design.materials.count)]
        (out / (path.stem + '.json')).write_text(json.dumps(observed, indent=1) + '\n')
    finally:
        doc.close(False)


try:
    for path in sorted(source.glob('*.f3d')):
        if time.time() - started > budget:
            break
        try:
            accept(path)
            status['done'].append(path.stem)
        except Exception:
            status['failed'].append({'key': path.stem, 'error': traceback.format_exc().splitlines()[-1]})
finally:
    if original is not None and original.isValid:
        original.activate()
    status['documents_after'] = app.documents.count
    (out / 'Status.json').write_text(json.dumps(status, indent=1) + '\n')
