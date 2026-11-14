import hashlib
import json
from math import isclose
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

root = Path(__file__).resolve().parents[3]
source = root / 're/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d'
out = root / 're/Fusion/LocalOracle/PrismHistory'
out.mkdir(exist_ok=True)
app = adsk.core.Application.get()
original = app.activeDocument
doc = None
report = {'fusion_version': app.version, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'scope': 'Native baseline capture of supplied ordinary rectangular extrusion; no Kit geometry replacement'}
try:
    doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
    if doc is None:
        raise RuntimeError('Native rectangular control did not open')
    design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    body = design.rootComponent.bRepBodies.item(0)
    report['opened'] = {'timeline': [{'name': i.name, 'health': int(i.healthState), 'message': i.errorOrWarningMessage} for i in design.timeline], 'parameters': [{'name': p.name, 'expression': p.expression, 'value': p.value} for p in design.allParameters], 'geometry': {'volume_cm3': body.volume, 'min_cm': body.boundingBox.minPoint.asArray(), 'max_cm': body.boundingBox.maxPoint.asArray(), 'faces': body.faces.count, 'edges': body.edges.count, 'vertices': body.vertices.count}, 'extrusion_extent_type': design.rootComponent.features.extrudeFeatures.item(0).extentOne.objectType}
    if not isclose(body.volume, 30.0) or (body.faces.count, body.edges.count, body.vertices.count) != (6, 12, 8):
        raise RuntimeError('Native rectangular control geometry differs')
    if any(i.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState for i in design.timeline):
        raise RuntimeError('Native rectangular control contains unhealthy features')
    design.timeline.markerPosition = 1
    report['rollback_body_count'] = design.rootComponent.bRepBodies.count
    if report['rollback_body_count'] != 0 or not design.timeline.moveToEnd() or not design.computeAll():
        raise RuntimeError('Native rectangular control rollback or rebuild failed')
    report['rebuilt_volume_cm3'] = design.rootComponent.bRepBodies.item(0).volume
    report['status'] = 'captured'
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
    (out / 'NativeSource.json').write_text(json.dumps(report, indent=2) + '\n')
