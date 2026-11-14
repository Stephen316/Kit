import hashlib
import json
from pathlib import Path
import traceback
import adsk.core
import adsk.fusion

folder=Path(__file__).resolve().parent/'TSpline'
app=adsk.core.Application.get()
original=app.activeDocument
document=None
form=None
editing=False
report=dict(fusion_version=app.version,scope='Native edge crease differential on owned T-spline controls',cases=[])

def observe(body,name):
    text=body.getTSMDescription();path=folder/(name+'.tsm');path.write_text(text)
    return dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),vertices=[list(v.geometry.asArray()) for v in body.vertices],edges=[dict(index=i,creased=e.isCreased,faces=len(e.faces),start=list(e.startVertex.geometry.asArray()),end=list(e.endVertex.geometry.asArray())) for i,e in enumerate(body.edges)])

try:
    for kind in ('Box','Plane'):
        document=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(folder/(kind+'.f3d'))))
        if document is None:raise RuntimeError('Control did not open')
        design=adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))
        form=design.rootComponent.features.formFeatures.item(0)
        if not form.startEdit():raise RuntimeError('Form edit failed')
        editing=True;body=form.tSplineBodies.item(0)
        case=dict(kind=kind,stages=dict(initial=observe(body,kind+'CreaseInitial')));report['cases'].append(case)
        candidates=[e for e in body.edges if len(e.faces)==2 and not e.isCreased]
        if not candidates:raise RuntimeError('No smooth interior edge')
        edge=candidates[0];case['selected']=dict(start=list(edge.startVertex.geometry.asArray()),end=list(edge.endVertex.geometry.asArray()))
        edge.isCreased=True
        if not edge.isCreased:raise RuntimeError('Crease assignment failed')
        case['stages']['creased']=observe(body,kind+'Creased')
        edge.isCreased=False
        if edge.isCreased:raise RuntimeError('Uncrease assignment failed')
        case['stages']['uncreased']=observe(body,kind+'Uncreased')
        if not form.finishEdit():raise RuntimeError('Form edit completion failed')
        editing=False
        if not design.computeAll() or form.healthState!=0:raise RuntimeError('Form recompute failed')
        case['status']='captured';document.close(False);document=None;form=None
    report['status']='captured'
except Exception:
    report['status']='failed';report['traceback']=traceback.format_exc();raise
finally:
    if editing and form is not None:form.finishEdit()
    if document is not None:document.close(False)
    if original is not None and original.isValid:original.activate()
    report['documents_after']=app.documents.count
    (folder/'CreaseCapture.json').write_text(json.dumps(report,indent=2)+'\n')
