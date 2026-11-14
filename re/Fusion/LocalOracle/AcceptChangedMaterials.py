import hashlib
import json
from math import isclose, pi
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

root = Path(__file__).resolve().parent / 'Features'
source = root / 'kit_changed_materials_19mm.f3d'
baseline = root / 'kit_full_brep_19mm.f3d'
saved = root / 'vendor_changed_materials23mm.f3d'
app = adsk.core.Application.get()
original = app.activeDocument
doc = None
report = {'fusion_version': app.version, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'scope': 'Same-source material semantics fully reserialized into new nested package with zeroed unused allocation bytes; explicitly changed density6300 and color RGBA51/102/153/255, parameter rebuild, save and reopen'}


def value(item):
    if item is None or type(item) in (str, bool, int, float):
        return item
    if isinstance(item, (list, tuple)):
        return [value(child) for child in item]
    if isinstance(item, adsk.core.Color):
        return [item.red, item.green, item.blue, item.opacity]
    raise RuntimeError('Unsupported native material value ' + item.objectType)


def properties(items):
    rows = []
    for item in items:
        row = {'id': item.id, 'type': item.objectType}
        if hasattr(item, 'hasMultipleValues') and item.hasMultipleValues:
            row['values'] = value(item.values)
        elif hasattr(item, 'value'):
            row['value'] = value(item.value)
        else:
            raise RuntimeError('Unsupported native property ' + item.objectType)
        if hasattr(item, 'hasConnectedTexture'):
            row['has_texture'] = item.hasConnectedTexture
        rows.append(row)
    return sorted(rows, key=lambda row: row['id'])


def observe(design):
    return {'materials': sorted([{'id': item.id, 'name': item.name, 'appearance': item.appearance.id, 'properties': properties(item.materialProperties)} for item in design.materials], key=lambda row: row['id']), 'appearances': sorted([{'id': item.id, 'name': item.name, 'properties': properties(item.appearanceProperties)} for item in design.appearances], key=lambda row: row['id']), 'body_materials': [body.material.id for body in design.rootComponent.bRepBodies]}


try:
    doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(baseline)))
    design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    report['baseline'] = observe(design)
    doc.close(False)
    doc = None
    doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
    if doc is None:
        raise RuntimeError('Reconstructed materials archive did not open')
    design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    report['expected'] = json.loads(json.dumps(report['baseline']))
    for material in report['expected']['materials']:
        for field in material['properties']:
            if field['id'] in ('structural_Density', 'thermal_Density'):
                field['value'] = 6300.0
    for appearance in report['expected']['appearances']:
        for field in appearance['properties']:
            if field['id'] == 'metal_f0':
                field['value'] = [51, 102, 153, 255]
    report['opened'] = observe(design)
    if report['opened'] != report['expected']:
        raise RuntimeError('Native material properties differ')
    if not isclose(design.rootComponent.bRepBodies.item(0).volume, pi * 1.9, rel_tol=1e-9):
        raise RuntimeError('Initial geometry differs')
    design.userParameters.itemByName('depthLength').expression = '23 mm'
    if not design.computeAll() or not isclose(design.rootComponent.bRepBodies.item(0).volume, pi * 2.3, rel_tol=1e-9):
        raise RuntimeError('Parameter rebuild failed')
    if any(item.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState for item in design.timeline):
        raise RuntimeError('Timeline unhealthy')
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
        raise RuntimeError('Vendor save failed')
    doc.close(False)
    doc = None
    doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(saved)))
    design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    report['reopened'] = observe(design)
    if report['reopened'] != report['expected']:
        raise RuntimeError('Reopened material properties differ')
    if not design.computeAll() or not isclose(design.rootComponent.bRepBodies.item(0).volume, pi * 2.3, rel_tol=1e-9):
        raise RuntimeError('Reopened parameter rebuild failed')
    report['saved_sha256'] = hashlib.sha256(saved.read_bytes()).hexdigest()
    report['status'] = 'accepted'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
    raise
finally:
    if doc is not None:
        doc.close(False)
    if original is not None and original.isValid:
        original.activate()
    report['documents_after'] = app.documents.count
    (root / 'ChangedMaterialAcceptance.json').write_text(json.dumps(report, indent=2) + '\n')
