import hashlib
import json
from math import isclose, pi
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

root = Path(__file__).resolve().parent
source = root.parent / 'Reconstruction/ContainerAuthoring/FreshParameter/AuthoredParameter.f3d'
output = root / 'Authored'
output.mkdir(exist_ok=True)
saved = output / 'vendor_fresh_parameter.f3d'
feature_saved = output / 'vendor_fresh_extrusion.f3d'
app = adsk.core.Application.get()
original = app.activeDocument
doc = None
report = {'fusion_version': app.version, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'scope': 'Independently authored complete F3D parameter document, no source archive or template; native read/edit/save/reopen and subsequent native feature creation'}


def observe(design):
    return {'design_type': int(design.designType), 'root_name': design.rootComponent.name, 'default_units': design.unitsManager.defaultLengthUnits, 'user_parameters': [{'name': item.name, 'value': item.value, 'expression': item.expression, 'unit': item.unit, 'comment': item.comment} for item in design.userParameters], 'timeline_count': design.timeline.count, 'body_count': design.rootComponent.bRepBodies.count, 'sketch_count': design.rootComponent.sketches.count}


try:
    doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
    if doc is None:
        raise RuntimeError('Independently authored F3D did not open')
    design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    report['opened'] = observe(design)
    parameter = design.userParameters.itemByName('authoredLength')
    if parameter is None or not isclose(parameter.value, 1.725, rel_tol=1e-9):
        raise RuntimeError('Authored parameter was not restored')
    if parameter.comment != 'Independently authored semantic parameter':
        raise RuntimeError('Authored parameter comment differs')
    parameter.expression = '31.5 mm'
    if not design.computeAll() or not isclose(parameter.value, 3.15, rel_tol=1e-9):
        raise RuntimeError('Authored parameter edit failed')
    report['edited'] = observe(design)
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
        raise RuntimeError('Native parameter export failed')
    doc.close(False)
    doc = None
    doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(saved)))
    design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    report['reopened'] = observe(design)
    if not design.computeAll() or not isclose(design.userParameters.itemByName('authoredLength').value, 3.15, rel_tol=1e-9):
        raise RuntimeError('Authored parameter did not survive native save')
    sketch = design.rootComponent.sketches.add(design.rootComponent.xYConstructionPlane)
    sketch.name = 'Native On Authored Document'
    sketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 2.0)
    extrudes = design.rootComponent.features.extrudeFeatures
    feature_input = extrudes.createInput(sketch.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    distance = adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString('authoredLength'))
    feature_input.setOneSideExtent(distance, adsk.fusion.ExtentDirections.PositiveExtentDirection)
    feature = extrudes.add(feature_input)
    if not design.computeAll() or feature.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:
        raise RuntimeError('Native feature creation failed on authored document')
    body = design.rootComponent.bRepBodies.item(0)
    report['native_feature'] = {'document': observe(design), 'volume_cm3': body.volume, 'faces': body.faces.count, 'health': int(feature.healthState)}
    if not isclose(body.volume, pi * 4 * 3.15, rel_tol=1e-9):
        raise RuntimeError('Native feature used the wrong authored parameter')
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(feature_saved))):
        raise RuntimeError('Native feature export failed')
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
    (output / 'ParameterAcceptance.json').write_text(json.dumps(report, indent=2) + '\n')
