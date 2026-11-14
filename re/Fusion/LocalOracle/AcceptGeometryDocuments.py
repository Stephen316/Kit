import hashlib
import json
import lzma
from math import isclose
from pathlib import Path
import traceback
import adsk.core
import adsk.fusion

root=Path(__file__).resolve().parents[3]
folder=Path(__file__).resolve().parent/'DocumentGeometry'
preparation=json.loads((folder/'Preparation.json').read_text())
app=adsk.core.Application.get();original=app.activeDocument;document=None
report=dict(fusion_version=app.version,scope='Complete typed mesh-conversion and planar geometry archives; source/control native lifecycle comparison',cases=[])
observations={}

def checkpoint():
    encoded=lzma.compress(json.dumps(observations,separators=(',',':'),allow_nan=False).encode());(folder/'NativeObservations.json.xz').write_bytes(encoded)
    report['observations_sha256']=hashlib.sha256(encoded).hexdigest();(folder/'NativeAcceptance.json').write_text(json.dumps(report,indent=2)+'\n')

def xyz(value):return list(value.asArray())
def bounds(value):return [xyz(value.minPoint),xyz(value.maxPoint)]
def digest(values):return hashlib.sha256(json.dumps(values,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def observe(design,key):
    result=dict(marker=design.timeline.markerPosition,parameters=[dict(name=p.name,expression=p.expression,value=p.value,unit=p.unit) for p in design.allParameters],timeline=[dict(name=t.name,health=t.healthState,message=t.errorOrWarningMessage) for t in design.timeline],bodies=[],meshes=[])
    for b in design.rootComponent.bRepBodies:
        result['bodies'].append(dict(name=b.name,solid=b.isSolid,faces=b.faces.count,edges=b.edges.count,vertices=b.vertices.count,area_cm2=b.area,volume_cm3=b.volume if b.isSolid else None,center_cm=xyz(b.physicalProperties.centerOfMass) if b.isSolid else None,bounds_cm=bounds(b.boundingBox),points_cm=sorted(xyz(v.geometry) for v in b.vertices),surface_types=sorted(f.geometry.objectType for f in b.faces)))
    details=[]
    for b in design.rootComponent.meshBodies:
        mesh=b.mesh;groups=list(mesh.triangleFaceGroupTempIds);ids=list(dict.fromkeys(groups));partition=[ids.index(g) for g in groups]
        data=dict(positions=[round(x,12) for x in mesh.nodeCoordinatesAsDouble],normals=[round(x,12) for x in mesh.normalVectorsAsDouble],corners=list(mesh.triangleNodeIndices),groups=partition);details.append(data)
        result['meshes'].append(dict(name=b.name,vertices=mesh.nodeCount,triangles=mesh.triangleCount,closed=b.isClosed,area_cm2=b.area,volume_cm3=b.volume,bounds_cm=bounds(b.boundingBox),face_groups=b.faceGroups.count,geometry_sha256=digest(data)))
    observations[key]=details
    return result

def same(a,b,path='state'):
    if isinstance(a,float) and isinstance(b,(float,int)):
        if not isclose(a,b,rel_tol=1e-8,abs_tol=1e-8):raise RuntimeError(f'Native mismatch {path}: {a} != {b}')
    elif isinstance(a,dict) and isinstance(b,dict):
        if a.keys()!=b.keys():raise RuntimeError('Different keys at '+path)
        for k in a:same(a[k],b[k],path+'.'+str(k))
    elif isinstance(a,(list,tuple)) and isinstance(b,(list,tuple)):
        if len(a)!=len(b):raise RuntimeError('Different lengths at '+path)
        for i,(x,y) in enumerate(zip(a,b)):same(x,y,path+'.'+str(i))
    elif a!=b:raise RuntimeError(f'Native mismatch {path}: {a!r} != {b!r}')

def open_file(path):
    global document
    document=app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(path)))
    if document is None:raise RuntimeError('Archive did not open')
    return adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))

try:
    if preparation['status']!='prepared':raise RuntimeError('Incomplete candidate preparation')
    for prepared in preparation['cases']:
        if prepared['label'].startswith('Native'):continue
        case=dict(label=prepared['label'],variants=[]);report['cases'].append(case)
        for variant,relative,expected in [('Control',prepared['source'],prepared['sourceSha256']),('Reemitted',prepared['target'],prepared['targetSha256'])]:
            source=root/relative
            if hashlib.sha256(source.read_bytes()).hexdigest()!=expected:raise RuntimeError('Candidate bytes changed')
            result=dict(variant=variant,source_sha256=expected,stages={});case['variants'].append(result)
            design=open_file(source);prefix=prepared['label']+variant
            result['stages']['opened']=observe(design,prefix+'Opened');checkpoint()
            for marker in reversed(range(design.timeline.count)):
                design.timeline.markerPosition=marker;result['stages']['rollback_'+str(marker)]=observe(design,prefix+'Rollback'+str(marker))
            if design.timeline.count and not design.timeline.moveToEnd():raise RuntimeError('History restore failed')
            if not design.computeAll():raise RuntimeError('Native document rebuild failed')
            result['stages']['rebuilt']=observe(design,prefix+'Rebuilt')
            edit=prepared.get('parameterEdit')
            if edit:
                parameter=design.allParameters.itemByName(edit['name'])
                if parameter is None:raise RuntimeError('Expected native parameter absent')
                if parameter.expression!=edit['previous']:raise RuntimeError('Unexpected initial native expression')
                parameter.expression=edit['expression']
                if not design.computeAll():raise RuntimeError('Native parameter edit failed')
                result['stages']['edited']=observe(design,prefix+'Edited')
            else:result['edit_scope']='No driving parameter edit is invented for these native mesh conversion controls; complete feature rollback and rebuild are compared'
            saved=folder/('vendor_'+prefix+'.f3d')
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):raise RuntimeError('Native save failed')
            document.close(False);document=None;design=open_file(saved)
            if not design.computeAll():raise RuntimeError('Saved native document rebuild failed')
            result['stages']['reopened']=observe(design,prefix+'Reopened')
            same(result['stages']['edited' if edit else 'rebuilt'],result['stages']['reopened'],'saved state')
            result['saved_sha256']=hashlib.sha256(saved.read_bytes()).hexdigest();result['status']='accepted'
            document.close(False);document=None;checkpoint()
        same(case['variants'][0]['stages'],case['variants'][1]['stages']);case['status']='accepted';checkpoint()
    report['status']='accepted'
except Exception:
    report['status']='failed';report['traceback']=traceback.format_exc();raise
finally:
    if document is not None:document.close(False)
    if original is not None and original.isValid:original.activate()
    report['documents_after']=app.documents.count;checkpoint()
