import hashlib
import json
import math
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

root=Path(__file__).resolve().parents[3]
folder=Path(__file__).resolve().parent/'RoundBodies'
app=adsk.core.Application.get()
original=app.activeDocument
document=None
report=dict(fusion_version=app.version,scope='Typed positive sphere/ring-torus carrier reconstruction, trimmed history preservation, and source-free untrimmed primitive authoring',standalone=[],geometry=[],histories=[])


def checkpoint():
    (folder/'NativeAcceptance.json').write_text(json.dumps(report,indent=2)+'\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare(first,second,trail='state'):
    if isinstance(first,float) and isinstance(second,(float,int)):
        if not math.isclose(first,second,rel_tol=1e-8,abs_tol=1e-8):raise RuntimeError(f'{trail}: {first} != {second}')
    elif isinstance(first,dict) and isinstance(second,dict):
        if first.keys()!=second.keys():raise RuntimeError('Different fields at '+trail)
        for key in first:compare(first[key],second[key],trail+'.'+str(key))
    elif isinstance(first,(list,tuple)) and isinstance(second,(list,tuple)):
        if len(first)!=len(second):raise RuntimeError('Different counts at '+trail)
        for index,(left,right) in enumerate(zip(first,second)):compare(left,right,trail+'.'+str(index))
    elif first!=second:raise RuntimeError(f'{trail}: {first!r} != {second!r}')


def body_info(body):
    bounds=body.boundingBox
    return dict(solid=body.isSolid,faces=body.faces.count,edges=body.edges.count,vertices=body.vertices.count,volumeCm3=body.volume if body.isSolid else None,areaCm2=body.area,centerCm=body.physicalProperties.centerOfMass.asArray() if body.isSolid else None,boundsCm=[bounds.minPoint.asArray(),bounds.maxPoint.asArray()],surfaceTypes=[face.geometry.objectType for face in body.faces])


def observe(design):
    return dict(marker=design.timeline.markerPosition,parameters=[dict(name=value.name,value=value.value,expression=value.expression,unit=value.unit) for value in design.allParameters],timeline=[dict(name=value.name,health=value.healthState,message=value.errorOrWarningMessage) for value in design.timeline],bodies=[body_info(body) for body in design.rootComponent.bRepBodies])


def open_archive(path):
    global document
    document=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(path)))
    if document is None:raise RuntimeError('Native archive import failed')
    return adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))


def close_document():
    global document
    if document is not None:document.close(False)
    document=None


def save_reopen(design,label):
    path=folder/('vendor_'+label+'.f3d')
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(path))):raise RuntimeError('Native archive export failed')
    close_document()
    return open_archive(path),digest(path)


def import_body(path):
    global document
    bodies=adsk.fusion.TemporaryBRepManager.get().createFromFile(str(path))
    if bodies is None or bodies.count!=1:raise RuntimeError('SMB did not import exactly one body')
    temporary=body_info(bodies.item(0))
    document=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design=adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))
    design.designType=adsk.fusion.DesignTypes.DirectDesignType
    added=design.rootComponent.bRepBodies.add(bodies.item(0))
    if added is None:raise RuntimeError('Temporary body could not be persisted')
    return design,temporary,body_info(added)


def check_expected(actual,expected):
    if not actual['solid']:raise RuntimeError('Expected a solid analytic body')
    for key,value in expected.items():compare(actual[key],value,key)


def accept_standalone():
    prepared=json.loads((folder/'PreparationStandalone.json').read_text())
    for item in prepared['standalone']:
        path=root/item['target']
        if digest(path)!=item['targetSha256']:raise RuntimeError('Authored geometry digest changed')
        result=dict(label=item['label'],source_sha256=item['targetSha256'],expected=item['expected']);report['standalone'].append(result)
        design,result['temporary'],result['persisted']=import_body(path)
        check_expected(result['persisted'],item['expected'])
        expected_type='adsk::core::Sphere' if item['label']=='AuthoredSphere' else 'adsk::core::Torus'
        compare(result['persisted']['surfaceTypes'],[expected_type])
        design,result['saved_sha256']=save_reopen(design,item['label'])
        result['reopened']=body_info(design.rootComponent.bRepBodies.item(0))
        check_expected(result['reopened'],item['expected']);compare(result['persisted'],result['reopened'])
        result['status']='accepted';close_document();checkpoint()


def accept_geometry():
    prepared=json.loads((folder/'PreparationGeometry.json').read_text())
    for item in prepared['geometry']:
        source=root/item['source'];target=root/item['target']
        if digest(source)!=item['sourceSha256'] or digest(target)!=item['targetSha256']:raise RuntimeError('Controlled geometry digest changed')
        result=dict(label=item['label'],source_sha256=item['sourceSha256'],target_sha256=item['targetSha256']);report['geometry'].append(result)
        design=open_archive(source)
        if design.rootComponent.bRepBodies.count!=1:raise RuntimeError('Expected one native source primitive')
        result['control']=body_info(design.rootComponent.bRepBodies.item(0));close_document()
        design,result['temporary'],result['persisted']=import_body(target)
        compare(result['control'],result['persisted'])
        design,result['saved_sha256']=save_reopen(design,'Decoded'+item['label'])
        result['reopened']=body_info(design.rootComponent.bRepBodies.item(0));compare(result['control'],result['reopened'])
        result['status']='accepted';close_document();checkpoint()


def accept_histories():
    prepared=json.loads((folder/'PreparationHistories.json').read_text())
    for item in prepared['histories']:
        result=dict(label=item['label'],variants=[]);report['histories'].append(result)
        for variant,path,sha in (('Control',item['source'],item['sourceSha256']),('Reemitted',item['target'],item['targetSha256'])):
            path=root/path
            if digest(path)!=sha:raise RuntimeError('Prepared history archive changed')
            entry=dict(variant=variant,source_sha256=sha,stages={});result['variants'].append(entry)
            design=open_archive(path);entry['stages']['opened']=observe(design);checkpoint()
            for marker in reversed(range(design.timeline.count)):
                design.timeline.markerPosition=marker;entry['stages']['rollback_'+str(marker)]=observe(design)
            if not design.timeline.moveToEnd() or not design.computeAll():raise RuntimeError('History restore/rebuild failed')
            entry['stages']['rebuilt']=observe(design)
            edits={'PartialClosed':('d3',0.6,'8 mm'),'CompositeCircular':('d3',0.4,'6 mm'),'RoundFillets':('d7',0.1,'0.8 mm')}
            name,prior,expression=edits[item['label']]
            parameter=design.allParameters.itemByName(name)
            if parameter is None or parameter.unit!='mm':raise RuntimeError('Expected semantic driving parameter is absent')
            compare(parameter.value,prior,'driving parameter before edit')
            parameter.expression=expression
            if not design.computeAll():raise RuntimeError('Driving parameter edit failed to rebuild')
            entry['stages']['edited']=observe(design)
            if entry['stages']['edited']['bodies']==entry['stages']['rebuilt']['bodies']:raise RuntimeError('Driving parameter edit did not alter geometry')
            entry['edit_scope']=dict(parameter=name,expression=expression,evidence='re/Fusion/Reconstruction/RoundBodies/DesignInputs.json.xz')
            design,entry['saved_sha256']=save_reopen(design,item['label']+variant)
            if not design.computeAll():raise RuntimeError('Reopened history failed to rebuild')
            entry['stages']['reopened']=observe(design)
            close_document();entry['status']='accepted';checkpoint()
        compare(result['variants'][0]['stages'],result['variants'][1]['stages'])
        result['status']='accepted'


try:
    accept_standalone();accept_geometry();accept_histories()
    report['status']='accepted'
except Exception:
    report['status']='failed';report['traceback']=traceback.format_exc();raise
finally:
    close_document()
    if original is not None and original.isValid:original.activate()
    report['documents_after']=app.documents.count;checkpoint()
