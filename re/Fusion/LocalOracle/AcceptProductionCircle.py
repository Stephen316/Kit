import hashlib
import json
from math import isclose, pi
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

root = Path(__file__).resolve().parent
source = root / 'Authored/ProductionCircle.f3d'
output = root / 'Authored'
output.mkdir(exist_ok=True)
saved = output / 'vendor_production_circle.f3d'
feature_saved = output / 'vendor_production_circle_extrusion.f3d'
app = adsk.core.Application.get()
original = app.activeDocument
doc = None
report = {'fusion_version': app.version, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'scope': 'Production Kit-authored complete F3D with semantic circle sketch, no source archive or template'}


def checkpoint(stage):
    report['stage'] = stage
    (output / 'ProductionCircleAcceptance.json').write_text(json.dumps(report, indent=2) + '\n')


def observe(design):
    sketch = design.rootComponent.sketches.item(0)
    return {'design_type': int(design.designType), 'timeline_count': design.timeline.count, 'body_count': design.rootComponent.bRepBodies.count, 'sketch_count': design.rootComponent.sketches.count, 'sketch_name': sketch.name, 'circle_count': sketch.sketchCurves.sketchCircles.count, 'radius_cm': sketch.sketchCurves.sketchCircles.item(0).radius, 'profiles': sketch.profiles.count, 'health': int(sketch.healthState), 'error': sketch.errorOrWarningMessage}


try:
    checkpoint('importing')
    doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
    if doc is None:
        raise RuntimeError('Independently authored circle did not open')
    checkpoint('opened')
    design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    report['opened'] = observe(design)
    checkpoint('observed')
    if report['opened']['timeline_count'] != 1 or not isclose(report['opened']['radius_cm'], 1.25, rel_tol=1e-9):
        raise RuntimeError('Authored circle is incorrect')
    if not design.computeAll():
        raise RuntimeError('Authored circle failed to compute')
    report['computed'] = observe(design)
    checkpoint('computed')
    sketch = design.rootComponent.sketches.item(0)
    sketch.sketchCurves.sketchCircles.item(0).radius = 1.8
    if not design.computeAll():
        raise RuntimeError('Authored circle edit failed to compute')
    report['edited'] = observe(design)
    if not isclose(report['edited']['radius_cm'], 1.8, rel_tol=1e-9) or report['edited']['health'] != 0:
        raise RuntimeError('Authored circle edit is incorrect')
    checkpoint('edited')
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
        raise RuntimeError('Native circle export failed')
    doc.close(False)
    doc = None
    doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(saved)))
    design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    if not design.computeAll():
        raise RuntimeError('Reopened authored circle failed to compute')
    report['reopened'] = observe(design)
    if not isclose(report['reopened']['radius_cm'], 1.8, rel_tol=1e-9) or report['reopened']['profiles'] != 1:
        raise RuntimeError('Authored circle did not survive save')
    checkpoint('reopened')
    sketch = design.rootComponent.sketches.item(0)
    extrudes = design.rootComponent.features.extrudeFeatures
    feature_input = extrudes.createInput(sketch.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    distance = adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('authoredLength'))
    feature_input.setOneSideExtent(distance, adsk.fusion.ExtentDirections.PositiveExtentDirection)
    feature = extrudes.add(feature_input)
    if not design.computeAll() or feature.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:
        raise RuntimeError('Native extrusion failed on independently authored circle')
    body = design.rootComponent.bRepBodies.item(0)
    report['native_extrusion'] = {'timeline_count': design.timeline.count, 'volume_cm3': body.volume, 'faces': body.faces.count, 'health': int(feature.healthState)}
    if not isclose(body.volume, pi * 1.8 ** 2 * 1.725, rel_tol=1e-9):
        raise RuntimeError('Native extrusion used incorrect profile or parameter')
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(feature_saved))):
        raise RuntimeError('Native extrusion export failed')
    report['saved_sha256'] = hashlib.sha256(saved.read_bytes()).hexdigest()
    report['native_feature_sha256'] = hashlib.sha256(feature_saved.read_bytes()).hexdigest()
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
    checkpoint('finished')
