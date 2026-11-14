import hashlib
import json
from pathlib import Path
import traceback
import adsk.core
import adsk.fusion

folder=Path(__file__).resolve().parent/'RoundCarriers'
app=adsk.core.Application.get();original=app.activeDocument;document=None
report=dict(fusion_version=app.version,scope='Owned explicit placement control after observed native axis-aligned torus origin discrepancy')
try:
    manager=adsk.fusion.TemporaryBRepManager.get()
    body=manager.createTorus(adsk.core.Point3D.create(0,0,0),adsk.core.Vector3D.create(0,0,1),2.3,.7)
    if body is None:raise RuntimeError('Origin torus creation failed')
    matrix=adsk.core.Matrix3D.create();matrix.translation=adsk.core.Vector3D.create(1.1,-.7,.5)
    if not manager.transform(body,matrix):raise RuntimeError('Explicit torus translation failed')
    smt=folder/'PlacedTorus.smt'
    if not manager.exportToFile([body],str(smt)):raise RuntimeError('Placed torus SMT export failed')
    document=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design=adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'));design.designType=adsk.fusion.DesignTypes.DirectDesignType
    owned=design.rootComponent.bRepBodies.add(body)
    if owned is None:raise RuntimeError('Placed torus ownership failed')
    owned.name='Owned Explicitly Placed Torus'
    source=folder/'PlacedTorus.f3d'
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(source))):raise RuntimeError('Placed torus F3D export failed')
    report.update(center_cm=list(owned.physicalProperties.centerOfMass.asArray()),volume_cm3=owned.volume,faces=owned.faces.count,edges=owned.edges.count,vertices=owned.vertices.count,smt_sha256=hashlib.sha256(smt.read_bytes()).hexdigest(),archive_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),status='captured')
except Exception:
    report['status']='failed';report['traceback']=traceback.format_exc();raise
finally:
    if document is not None:document.close(False)
    if original is not None and original.isValid:original.activate()
    report['documents_after']=app.documents.count
    (folder/'PlacementCapture.json').write_text(json.dumps(report,indent=2)+'\n')
