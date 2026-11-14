import hashlib
import json
import lzma
from math import isclose
from pathlib import Path
import traceback
import adsk.core
import adsk.fusion

root=Path(__file__).resolve().parents[3];folder=Path(__file__).resolve().parent/'TSplineCodec'
preparation=json.loads((folder/'Preparation.json').read_text())
app=adsk.core.Application.get();original=app.activeDocument;document=None;form=None;editing=False
report=dict(fusion_version=app.version,scope='Complete typed TSM regeneration and source-free closed quad cage; native form import, cage edit, conversion, save and reopen',cases=[]);observations={}

def checkpoint():
    data=lzma.compress(json.dumps(observations,separators=(',',':'),allow_nan=False).encode());(folder/'NativeObservations.json.xz').write_bytes(data);report['observation_sha256']=hashlib.sha256(data).hexdigest();(folder/'NativeAcceptance.json').write_text(json.dumps(report,indent=2)+'\n')
def xyz(point):return list(point.asArray())
def key(point):return tuple(round(x,12) for x in point.asArray())
def digest(value):return hashlib.sha256(json.dumps(value,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def cage(body,label):
    raw=dict(control_points_cm=[xyz(v.geometry) for v in body.vertices],smooth_points_cm=[xyz(v.smoothGeometry) for v in body.vertices],edges=[dict(start=xyz(e.startVertex.geometry),end=xyz(e.endVertex.geometry),creased=e.isCreased) for e in body.edges],faces=[[xyz(v.geometry) for v in face.vertices] for face in body.faces]);observations[label]=raw
    points=sorted(key(v.geometry) for v in body.vertices);smooth=sorted(key(v.smoothGeometry) for v in body.vertices)
    edges=sorted((tuple(sorted((key(e.startVertex.geometry),key(e.endVertex.geometry)))),e.isCreased) for e in body.edges)
    faces=sorted(tuple(sorted(key(v.geometry) for v in face.vertices)) for face in body.faces)
    return dict(faces=body.faces.count,edges=body.edges.count,vertices=body.vertices.count,control_sha256=digest(points),smooth_sha256=digest(smooth),edge_crease_sha256=digest(edges),face_incidence_sha256=digest(faces))
def solved(design):
    return dict(timeline=[dict(name=f.name,health=f.healthState,message=f.errorOrWarningMessage) for f in design.timeline],bodies=[dict(solid=b.isSolid,faces=b.faces.count,edges=b.edges.count,vertices=b.vertices.count,area_cm2=b.area,volume_cm3=b.volume if b.isSolid else None,center_cm=xyz(b.physicalProperties.centerOfMass) if b.isSolid else None,bounds_cm=[xyz(b.boundingBox.minPoint),xyz(b.boundingBox.maxPoint)]) for b in design.rootComponent.bRepBodies])
def same(a,b,path='state'):
    if isinstance(a,float) and isinstance(b,(float,int)):
        if not isclose(a,b,rel_tol=1e-8,abs_tol=1e-8):raise RuntimeError(f'Native mismatch {path}: {a} != {b}')
    elif isinstance(a,dict) and isinstance(b,dict):
        if a.keys()!=b.keys():raise RuntimeError('Different fields at '+path)
        for k in a:same(a[k],b[k],path+'.'+str(k))
    elif isinstance(a,(list,tuple)) and isinstance(b,(list,tuple)):
        if len(a)!=len(b):raise RuntimeError('Different counts at '+path)
        for i,(x,y) in enumerate(zip(a,b)):same(x,y,path+'.'+str(i))
    elif a!=b:raise RuntimeError(f'Native mismatch {path}: {a!r} != {b!r}')
def finish(design):
    global editing
    if not form.finishEdit():raise RuntimeError('Form finish failed')
    editing=False
    if not design.computeAll() or form.healthState!=0:raise RuntimeError('Form conversion/rebuild failed')

try:
    for prepared in preparation['cases']:
        case=dict(name=prepared['name'],variants=[]);report['cases'].append(case)
        variants=[('NativePrimitive',None,None),('Authored',prepared['output_file'],prepared['output_sha256'])] if prepared.get('source_free') else [('Control',prepared['source_file'],prepared['source_sha256']),('Reemitted',prepared['output_file'],prepared['output_sha256'])]
        for label,relative,expected in variants:
            if relative is not None:
                source=root/relative
                if hashlib.sha256(source.read_bytes()).hexdigest()!=expected:raise RuntimeError('Prepared TSM changed')
            document=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType);design=adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'));form=design.rootComponent.features.formFeatures.add();form.name='Qualified Form'
            if not form.startEdit():raise RuntimeError('Form edit did not start')
            editing=True
            if relative is None:
                shape=form.tSplineBodies.createBoxInput(adsk.core.Point3D.create(0,0,0),adsk.core.Vector3D.create(1,0,0),adsk.core.Vector3D.create(0,1,0),1.7,2.3,3.1);shape.xFaceCount=1;shape.yFaceCount=1;shape.zFaceCount=1;body=form.tSplineBodies.addByShapeInput(shape)
            else:body=form.tSplineBodies.addByTSMFile(str(source))
            if body is None:raise RuntimeError('TSM import or native primitive creation failed')
            body.name='Qualified Cage';prefix=prepared['name']+label
            result=dict(variant=label,source_sha256=expected,stages={});case['variants'].append(result)
            result['stages']['initial_cage']=cage(body,prefix+'Initial');finish(design);result['stages']['initial_solved']=solved(design);checkpoint()
            if prepared.get('source_free') and result['stages']['initial_cage']['vertices']!=8:raise RuntimeError('Independent cage did not produce eight vertices')
            if not form.startEdit():raise RuntimeError('Form edit did not reopen')
            editing=True;body=form.tSplineBodies.item(0);vertex=min(body.vertices,key=lambda v:key(v.geometry));result['edited_control_point_cm']=xyz(vertex.geometry)
            if not vertex.move(adsk.core.Vector3D.create(.11,.07,.13)):raise RuntimeError('Control point edit failed')
            result['stages']['edited_cage']=cage(body,prefix+'Edited');finish(design);result['stages']['edited_solved']=solved(design)
            saved=folder/('vendor_'+prefix+'.f3d')
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):raise RuntimeError('TSM native save failed')
            document.close(False);document=None;form=None
            document=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(saved)))
            if document is None:raise RuntimeError('Saved TSM document did not open')
            design=adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'));form=design.rootComponent.features.formFeatures.item(0)
            if not design.computeAll() or not form.startEdit():raise RuntimeError('Saved TSM form did not rebuild/reopen')
            editing=True;result['stages']['reopened_cage']=cage(form.tSplineBodies.item(0),prefix+'Reopened');finish(design);result['stages']['reopened_solved']=solved(design)
            same(result['stages']['edited_cage'],result['stages']['reopened_cage'],'saved cage');same(result['stages']['edited_solved'],result['stages']['reopened_solved'],'saved solid')
            result['saved_sha256']=hashlib.sha256(saved.read_bytes()).hexdigest();result['status']='accepted';document.close(False);document=None;form=None;checkpoint()
        same(case['variants'][0]['stages'],case['variants'][1]['stages']);same(case['variants'][0]['edited_control_point_cm'],case['variants'][1]['edited_control_point_cm']);case['status']='accepted';checkpoint()
    report['status']='accepted'
except Exception:
    report['status']='failed';report['traceback']=traceback.format_exc();raise
finally:
    if editing and form is not None:form.finishEdit()
    if document is not None:document.close(False)
    if original is not None and original.isValid:original.activate()
    report['documents_after']=app.documents.count;checkpoint()
