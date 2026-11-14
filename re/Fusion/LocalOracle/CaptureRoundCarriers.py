import hashlib
import json
from pathlib import Path
import traceback
import adsk.core
import adsk.fusion

folder=Path(__file__).resolve().parent/'RoundCarriers';folder.mkdir(exist_ok=True)
app=adsk.core.Application.get();original=app.activeDocument;document=None
manager=adsk.fusion.TemporaryBRepManager.get()
report=dict(fusion_version=app.version,scope='Owned analytic sphere/torus carrier capture; no independent codec acceptance',cases=[])
try:
    for label,center,radius,minor,axis in [('Sphere',(1.1,-.7,.5),1.7,None,None),('Torus',(1.1,-.7,.5),2.3,.7,(0.,0.,1.)),('TiltedTorus',(1.1,-.7,.5),2.3,.7,(0.,.6,.8))]:
        point=adsk.core.Point3D.create(*center)
        body=manager.createSphere(point,radius) if minor is None else manager.createTorus(point,adsk.core.Vector3D.create(*axis),radius,minor)
        if body is None:raise RuntimeError('Native round primitive construction failed')
        smt=folder/(label+'.smt')
        if not manager.exportToFile([body],str(smt)):raise RuntimeError('Native SMT export failed')
        document=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design=adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'));design.designType=adsk.fusion.DesignTypes.DirectDesignType
        owned=design.rootComponent.bRepBodies.add(body);owned.name='Owned '+label
        if owned is None:raise RuntimeError('Native body ownership failed')
        source=folder/(label+'.f3d')
        if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(source))):raise RuntimeError('Native F3D export failed')
        box=owned.boundingBox
        report['cases'].append(dict(label=label,input=dict(center_cm=center,major_or_sphere_radius_cm=radius,minor_radius_cm=minor,axis=axis),faces=owned.faces.count,edges=owned.edges.count,vertices=owned.vertices.count,volume_cm3=owned.volume,area_cm2=owned.area,center_cm=list(owned.physicalProperties.centerOfMass.asArray()),bounds_cm=[list(box.minPoint.asArray()),list(box.maxPoint.asArray())],smt=dict(file=smt.name,sha256=hashlib.sha256(smt.read_bytes()).hexdigest()),archive=dict(file=source.name,sha256=hashlib.sha256(source.read_bytes()).hexdigest())))
        document.close(False);document=None
    report['status']='captured'
except Exception:
    report['status']='failed';report['traceback']=traceback.format_exc();raise
finally:
    if document is not None:document.close(False)
    if original is not None and original.isValid:original.activate()
    report['documents_after']=app.documents.count
    (folder/'Capture.json').write_text(json.dumps(report,indent=2)+'\n')
