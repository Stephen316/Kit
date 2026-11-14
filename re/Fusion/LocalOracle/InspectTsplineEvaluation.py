import hashlib
import json
from pathlib import Path
import traceback
import adsk.core
import adsk.fusion

folder=Path(__file__).resolve().parent/'TSplineCodec'/'Evaluation'
folder.mkdir(exist_ok=True)
app=adsk.core.Application.get();original=app.activeDocument;document=None;form=None;editing=False
report=dict(fusion_version=app.version,scope='Native primitive, unchanged native TSM import, and independently authored TSM surface evaluation',cases=[],comparisons=[])
manager=adsk.fusion.TemporaryBRepManager.get();solids={}

def checkpoint():
    (folder/'Capture.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
def point(v):return list(v.asArray())
def properties(body):
    result=dict(faces=body.faces.count,edges=body.edges.count,vertices=body.vertices.count,solid=body.isSolid,bounds_cm=[point(body.boundingBox.minPoint),point(body.boundingBox.maxPoint)],default_area_cm2=body.area,default_volume_cm3=body.volume)
    for name,accuracy in [('low',adsk.fusion.CalculationAccuracy.LowCalculationAccuracy),('very_high',adsk.fusion.CalculationAccuracy.VeryHighCalculationAccuracy)]:
        value=body.getPhysicalProperties(accuracy);result[name]=dict(accuracy=value.accuracy,area_cm2=value.area,volume_cm3=value.volume,center_cm=point(value.centerOfMass))
    return result

def sample(body):
    points=[]
    for face in body.faces:
        evaluator=face.evaluator;domain=evaluator.parametricRange()
        for u in (.1,.3,.5,.7,.9):
            for v in (.1,.3,.5,.7,.9):
                parameter=adsk.core.Point2D.create(domain.minPoint.x+u*(domain.maxPoint.x-domain.minPoint.x),domain.minPoint.y+v*(domain.maxPoint.y-domain.minPoint.y))
                ok,p=evaluator.getPointAtParameter(parameter)
                if ok and face.isPointOnFace(p):points.append(p)
    return points

def distance(source,target):
    distances=[];failed=0
    for p in sample(source):
        candidates=[]
        for face in target.faces:
            evaluator=face.evaluator;ok,uv=evaluator.getParameterAtPoint(p)
            if not ok:continue
            ok,nearest=evaluator.getPointAtParameter(uv)
            if ok and face.isPointOnFace(nearest):candidates.append(p.distanceTo(nearest))
        if candidates:distances.append(min(candidates))
        else:failed+=1
    return dict(samples=len(distances),failed=failed,max_distance_cm=max(distances) if distances else None,mean_distance_cm=sum(distances)/len(distances) if distances else None)

try:
    for name in ('NativePrimitive','NativeDescriptionImported','AuthoredImported'):
        document=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType);design=adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'));form=design.rootComponent.features.formFeatures.add()
        if not form.startEdit():raise RuntimeError('Form edit did not start')
        editing=True
        if name=='NativePrimitive':
            shape=form.tSplineBodies.createBoxInput(adsk.core.Point3D.create(0,0,0),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),1.7,2.3,3.1);shape.xFaceCount=1;shape.yFaceCount=1;shape.zFaceCount=1;body=form.tSplineBodies.addByShapeInput(shape)
        else:
            source=folder/'NativePrimitiveInitial.tsm' if name=='NativeDescriptionImported' else folder.parent/'AuthoredClosedCage.tsm'
            body=form.tSplineBodies.addByTSMFile(str(source))
        if body is None:raise RuntimeError('TSpline creation failed')
        case=dict(name=name,stages={});report['cases'].append(case)
        for stage in ('Initial','Edited'):
            if stage=='Edited':
                if not form.startEdit():raise RuntimeError('Form edit did not reopen')
                editing=True;body=form.tSplineBodies.item(0);vertex=min(body.vertices,key=lambda v:tuple(round(x,12) for x in v.geometry.asArray()))
                if not vertex.move(adsk.core.Vector3D.create(.11,.07,.13)):raise RuntimeError('Control point edit failed')
            description=body.getTSMDescription();path=folder/(name+stage+'.tsm');path.write_text(description)
            if not form.finishEdit():raise RuntimeError('Form edit did not finish')
            editing=False
            if not design.computeAll() or form.healthState!=0:raise RuntimeError('Native solve failed')
            solved=design.rootComponent.bRepBodies.item(0);case['stages'][stage]=dict(tsm_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),properties=properties(solved));solids[(name,stage)]=manager.copy(solved);checkpoint()
        document.close(False);document=None;form=None
    for stage in ('Initial','Edited'):
        for left,right in [('NativePrimitive','NativeDescriptionImported'),('NativePrimitive','AuthoredImported'),('NativeDescriptionImported','AuthoredImported')]:
            report['comparisons'].append(dict(stage=stage,left=left,right=right,left_to_right=distance(solids[(left,stage)],solids[(right,stage)]),right_to_left=distance(solids[(right,stage)],solids[(left,stage)])));checkpoint()
    report['status']='captured'
except Exception:
    report['status']='failed';report['traceback']=traceback.format_exc();raise
finally:
    if editing and form is not None:form.finishEdit()
    if document is not None:document.close(False)
    if original is not None and original.isValid:original.activate()
    report['documents_after']=app.documents.count;checkpoint()
