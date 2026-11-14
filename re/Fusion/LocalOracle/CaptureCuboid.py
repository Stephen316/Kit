import hashlib
import json
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

root = Path(__file__).resolve().parent / 'Brep'
app = adsk.core.Application.get()
original = app.activeDocument
doc = None
report = {'fusion_version': app.version, 'scope': 'Controlled native rectangular cuboid capture for semantic topology evidence', 'dimensions_mm': {'width': 12, 'depth': 18, 'height': 24, 'base': [20, -30, 5]}, 'exports': []}
try:
    shape = adsk.core.OrientedBoundingBox3D.create(adsk.core.Point3D.create(2.6, -2.1, 1.7), adsk.core.Vector3D.create(1, 0, 0), adsk.core.Vector3D.create(0, 1, 0), 1.2, 1.8, 2.4)
    temporary = adsk.fusion.TemporaryBRepManager.get().createBox(shape)
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    design.designType = adsk.fusion.DesignTypes.DirectDesignType
    body = design.rootComponent.bRepBodies.add(temporary)
    if body is None:
        raise RuntimeError('Controlled cuboid could not be added')
    body.name = 'ControlledCuboid'
    for extension, create in (('smt', design.exportManager.createSMTExportOptions), ('f3d', design.exportManager.createFusionArchiveExportOptions)):
        target = root / ('native_cuboid_12_18_24.' + extension)
        options = create(str(target), design.rootComponent) if extension == 'smt' else create(str(target))
        if not design.exportManager.execute(options):
            raise RuntimeError('Controlled cuboid export failed')
        report['exports'].append({'file': target.name, 'bytes': target.stat().st_size, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
    report['geometry'] = {'solid': body.isSolid, 'faces': body.faces.count, 'edges': body.edges.count, 'vertices': body.vertices.count, 'volume_cm3': body.volume, 'center_cm': body.physicalProperties.centerOfMass.asArray(), 'minimum_cm': body.boundingBox.minPoint.asArray(), 'maximum_cm': body.boundingBox.maxPoint.asArray()}
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
    (root / 'CuboidCapture.json').write_text(json.dumps(report, indent=2) + '\n')
