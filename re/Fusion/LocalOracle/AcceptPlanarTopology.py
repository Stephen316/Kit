import hashlib
import json
from math import isclose, sqrt
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

root=Path(__file__).resolve().parents[3]
folder=Path(__file__).resolve().parent/'PlanarTopology'
prepared=json.loads((folder/'ProductionPreparation.json').read_text())
app=adsk.core.Application.get()
original=app.activeDocument
document=None
report=dict(fusion_version=app.version,scope='Production complete source-specific planar histories and source-free standalone convex polyhedra; nonidentity transform verified separately; source other archive members retained',documents_before=app.documents.count,histories=[],authored=[])


def checkpoint():
    (folder/'NativeAcceptance.json').write_text(json.dumps(report,indent=2)+'\n')


def compare(left,right,path='state'):
    if isinstance(left,float) and isinstance(right,(float,int)):
        if not isclose(left,right,rel_tol=1e-8,abs_tol=1e-8):raise RuntimeError(f'Mismatch at {path}: {left} != {right}')
    elif isinstance(left,dict) and isinstance(right,dict):
        if left.keys()!=right.keys():raise RuntimeError('Different keys at '+path)
        for key in left:compare(left[key],right[key],path+'.'+str(key))
    elif isinstance(left,(tuple,list)) and isinstance(right,(tuple,list)):
        if len(left)!=len(right):raise RuntimeError('Different counts at '+path)
        for index,(first,second) in enumerate(zip(left,right)):compare(first,second,path+'.'+str(index))
    elif left!=right:raise RuntimeError(f'Mismatch at {path}: {left!r} != {right!r}')


def body_info(body):
    bounds=body.boundingBox
    return dict(name=body.name,is_solid=body.isSolid,faces=body.faces.count,edges=body.edges.count,vertices=body.vertices.count,volume_cm3=body.volume,center_cm=body.physicalProperties.centerOfMass.asArray(),min_cm=bounds.minPoint.asArray(),max_cm=bounds.maxPoint.asArray())


def observe(design):
    return dict(marker=design.timeline.markerPosition,parameters=[dict(name=value.name,value=value.value,expression=value.expression,unit=value.unit) for value in design.allParameters],timeline=[dict(name=value.name,health=value.healthState,message=value.errorOrWarningMessage) for value in design.timeline],bodies=[body_info(body) for body in design.rootComponent.bRepBodies],mesh_bodies=design.rootComponent.meshBodies.count)


def open_archive(path):
    global document
    document=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(path)))
    if document is None:raise RuntimeError('Fusion archive did not open')
    return adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))


def save_reopen(design,path):
    global document
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(path))):raise RuntimeError('Native archive save failed')
    document.close(False);document=None
    return open_archive(path)


def check_shape(observed,expected,center=True):
    for key,value in expected.items():
        if key=='center_cm' and not center:continue
        compare(observed[key],value,key)


try:
    for label in ('Tetrahedron','TriangularPipe'):
        entries=[item for item in prepared['histories'] if item['label']==label]
        if len(entries)!=2:raise RuntimeError('Missing reconstructed/permuted history pair')
        case=dict(label=label,variants=[]);report['histories'].append(case)
        source=entries[0]
        variants=[('Control',source['source'],source['sourceSha256']),*[(item['variant'],item['target'],item['targetSha256']) for item in entries]]
        for variant,path,digest in variants:
            path=root/Path(path)
            if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise RuntimeError('Prepared history artifact changed')
            result=dict(variant=variant,source_sha256=digest,stages={});case['variants'].append(result)
            design=open_archive(path);result['stages']['opened']=observe(design);checkpoint()
            if design.rootComponent.bRepBodies.count!=1:raise RuntimeError('Expected one native planar solid')
            expected=dict(is_solid=True,faces=4 if label=='Tetrahedron' else 5,edges=6 if label=='Tetrahedron' else 9,vertices=4 if label=='Tetrahedron' else 6,volume_cm3=4.0 if label=='Tetrahedron' else 1.2470765814495919)
            check_shape(result['stages']['opened']['bodies'][0],expected)
            for marker in reversed(range(design.timeline.count)):
                design.timeline.markerPosition=marker
                result['stages']['rollback_'+str(marker)]=observe(design)
            if not design.timeline.moveToEnd() or not design.computeAll():raise RuntimeError('Native full history restore/rebuild failed')
            result['stages']['restored']=observe(design)
            if label=='TriangularPipe':
                parameter=design.allParameters.itemByName('d3')
                if parameter is None or parameter.unit!='mm':raise RuntimeError('Expected pipe section parameter d3 is absent')
                parameter.expression='8 mm'
                if not design.computeAll():raise RuntimeError('Pipe section edit failed')
                expected['volume_cm3']=1.2470765814495919*(8.0/6.0)**2
                result['stages']['section_edited']=observe(design)
                check_shape(result['stages']['section_edited']['bodies'][0],expected)
            else:
                if design.allParameters.count!=0:raise RuntimeError('Unexpected tetrahedron source parameters')
                result['edit_scope']='Native mesh-to-BRep source has zero parameters; all conversion features are preserved and rollback/rebuild is compared'
            saved=folder/('vendor_Planar'+label+variant+'.f3d')
            design=save_reopen(design,saved)
            if not design.computeAll():raise RuntimeError('Reopened planar history failed to rebuild')
            result['stages']['reopened']=observe(design);result['saved_sha256']=hashlib.sha256(saved.read_bytes()).hexdigest();result['status']='accepted'
            document.close(False);document=None;checkpoint()
        for variant in case['variants'][1:]:compare(case['variants'][0]['stages'],variant['stages'])
        case['status']='accepted'
    expected_shapes={
        'IndependentTetrahedron':dict(is_solid=True,faces=4,edges=6,vertices=4,volume_cm3=17*23*31/6000,center_cm=(.425,.575,.775),min_cm=(0.,0.,0.),max_cm=(1.7,2.3,3.1)),
        'IndependentTriangularPrism':dict(is_solid=True,faces=5,edges=9,vertices=6,volume_cm3=19*13*37/2000,center_cm=(1.9/3,1.3/3,1.85),min_cm=(0.,0.,0.),max_cm=(1.9,1.3,3.7)),
        'PlacedTetrahedron':dict(is_solid=True,faces=4,edges=6,vertices=4,volume_cm3=17*23*31/6000*1.25**3,center_cm=(.38125,-.16875,1.46875),min_cm=(-1.775,-.7,.5),max_cm=(1.1,1.425,4.375)),
    }
    if {item['label'] for item in prepared['authored']}!=set(expected_shapes):raise RuntimeError('Unexpected independent shape set')
    for item in prepared['authored']:
        source=root/Path(item['target']);label=item['label'];expected=expected_shapes[label]
        if hashlib.sha256(source.read_bytes()).hexdigest()!=item['sha256']:raise RuntimeError('Prepared standalone artifact changed')
        result=dict(label=label,source_sha256=item['sha256'],expected=expected);report['authored'].append(result)
        bodies=adsk.fusion.TemporaryBRepManager.get().createFromFile(str(source))
        if bodies is None or bodies.count!=1:raise RuntimeError('Authored SMB did not import one body')
        result['temporary']=body_info(bodies.item(0));check_shape(result['temporary'],expected,center=False)
        document=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design=adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'));design.designType=adsk.fusion.DesignTypes.DirectDesignType
        added=design.rootComponent.bRepBodies.add(bodies.item(0))
        if added is None:raise RuntimeError('Temporary body could not be persisted')
        result['persisted']=body_info(added);check_shape(result['persisted'],expected);checkpoint()
        saved=folder/('vendor_'+label+'.f3d');design=save_reopen(design,saved)
        if design.rootComponent.bRepBodies.count!=1:raise RuntimeError('Reopened standalone body count changed')
        result['reopened']=body_info(design.rootComponent.bRepBodies.item(0));check_shape(result['reopened'],expected)
        result['saved_sha256']=hashlib.sha256(saved.read_bytes()).hexdigest();result['status']='accepted'
        document.close(False);document=None;checkpoint()
    report['status']='accepted'
except Exception:
    report['status']='failed';report['traceback']=traceback.format_exc();raise
finally:
    if document is not None:document.close(False)
    if original is not None and original.isValid:original.activate()
    report['documents_after']=app.documents.count;checkpoint()
