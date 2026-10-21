"""Offline teardown behavior using actual generator AST and fake native wrappers.

Synthetic resources are not Fusion, and no native crash repair is proved here.
No adsk import, API/UI call, or native archive is created by these fixtures.
"""
import argparse
import ast
import gc
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace as NS
import traceback
import weakref
import zipfile

SOURCE='GenerateSurfaceTrimToolContrasts.py'


class Collection:
    def __init__(self,values=()):self.values=list(values)
    @property
    def count(self):return len(self.values)
    def item(self,i):return self.values[i]


class MemoryPath:
    def __init__(self,name,files):self.name=name;self.files=files
    def __truediv__(self,name):return MemoryPath(self.name+'/'+name,self.files)
    def __str__(self):return self.name
    def is_file(self):return self.name in self.files
    def stat(self):return NS(st_size=len(self.files[self.name]))
    def read_bytes(self):return self.files[self.name]
    def write_text(self,text):self.files[self.name]=text.encode();return len(text)


def fixture(source,scenario):
    events=[];violations=[];references=[];files={};documents=[]
    def event(name,**fields):events.append(dict(event=name,**fields))
    class Native:
        objectType='fake::Native';isValid=True
        def __init__(self,kind,doc):self.kind=kind;self.doc=doc;references.append((kind,weakref.ref(self)));event('acquire',kind=kind)
        def __del__(self):
            if self.doc.closed:violations.append('Native '+self.kind+' released after document close')
            if self.kind=='TrimFeature' and self.doc.position!='BeforeTrim':violations.append('TrimFeature released outside before-feature edit position')
            event('release',kind=self.kind,document_open=not self.doc.closed,position=self.doc.position)
    class Body:
        objectType='fake::Body';isValid=True;isSolid=False;area=1.;volume=0.;isVisible=True;isTemporary=False
        def __init__(self,lo=(-2,-1,0),hi=(2,1,0)):
            self.boundingBox=NS(minPoint=NS(x=lo[0],y=lo[1],z=lo[2]),maxPoint=NS(x=hi[0],y=hi[1],z=hi[2]));self.faces=Collection();self.vertices=Collection();self.parentComponent=None
    class Face:
        objectType='fake::Face';isValid=True;tempId=0;area=1.;isParamReversed=False
        def __init__(self,body):self.body=body;self.geometry=None;self.edges=Collection();self.loops=Collection()
    class Cell(Native):
        def __init__(self,doc,lo,hi):super().__init__('Cell',doc);self.cellBody=Body(lo,hi);self.isSelected=False;self.sourceTools=Collection()
    class Cells(Native,Collection):
        def __init__(self,doc):
            Native.__init__(self,'CellCollection',doc);Collection.__init__(self,[Cell(doc,(-2,-1,0),(2,0,0)),Cell(doc,(-2,0,0),(2,1,0)),Cell(doc,(-3,0,-1),(3,0,1))])
    class Input(Native):
        def __init__(self,doc,tool):super().__init__('TrimInput',doc);self.trimTool=tool;self.targetBaseFeature=None;self.bRepCells=Cells(doc)
        def cancel(self):
            event('cancel',document_open=not self.doc.closed)
            if scenario=='cancel_raises':raise RuntimeError('Synthetic cancel failure')
            return scenario!='cancel_false'
    class Feature(Native):
        healthState=0;errorOrWarningMessage='';isParametric=True;isSuppressed=False;parentComponent=None;name='FakeTrim'
        def __init__(self,doc,pending):
            super().__init__('TrimFeature',doc);self.retained_input=pending;self.bodies=Collection();self.timelineObject=NS(index=4,rollTo=self.roll);self.trimTool=pending.trimTool;self.bRepCells=pending.bRepCells
        def roll(self,before):
            event('roll_before',requested=before)
            if scenario=='roll_false':return False
            self.doc.position='BeforeTrim';return True
    class TrimFeatures:
        def __init__(self,doc):self.doc=doc;self.count=0
        def createInput(self,tool):
            event('create_input')
            if scenario=='create_raises':raise RuntimeError('Synthetic uncertain createInput failure')
            return Input(self.doc,tool)
        def add(self,pending):
            event('add')
            if scenario.startswith('cancel_') or scenario=='selection_error_cancel_success':raise RuntimeError('Synthetic add failure')
            self.count+=1;return Feature(self.doc,pending)
    class Timeline:
        count=5
        def __init__(self,doc):self.doc=doc
        @property
        def markerPosition(self):return 4 if self.doc.position=='BeforeTrim' else 5
        def moveToEnd(self):
            if any(kind=='TrimFeature' and ref() is not None for kind,ref in references):violations.append('Timeline moved to end while Trim wrapper still alive')
            self.doc.position='End';event('move_to_end')
    class Design:
        def __init__(self,doc):
            self.doc=doc;self.timeline=Timeline(doc);self.calls=0;self.rootComponent=NS(xYConstructionPlane='XY',xZConstructionPlane='XZ',bRepBodies=Collection(),modelParameters=Collection(),features=NS(trimFeatures=TrimFeatures(doc)))
            self.exportManager=NS(createFusionArchiveExportOptions=lambda p:p,execute=self.export)
        def computeAll(self):
            self.calls+=1;event('compute',call=self.calls)
            if scenario=='snapshot_exception' and self.calls==1:
                frame_probe=Native('ExceptionFrameProbe',self.doc)
                raise RuntimeError('Synthetic capture error carrying a native local in its traceback frame')
            return not(scenario=='final_compute_false' and self.calls==2)
        def export(self,path):event('export');files[path]=b'SYNTHETIC MEMORY ONLY - NOT A FUSION ARCHIVE';return True
    class Doc:
        def __init__(self):self.closed=False;self.position='End';self.design=Design(self);self.products=NS(itemByProductType=lambda name:self.design);documents.append(self);event('document_create')
        def close(self,save):
            alive=[kind for kind,ref in references if ref() is not None]
            if alive:violations.append('Close with live critical native wrappers: '+','.join(alive))
            event('document_close',save=save,alive_critical=alive);self.closed=True;return True
    def patch(root,plane,corners,name):
        body=Body();body.name=name+'_Body';face=Face(body);body.faces=Collection([face]);root.bRepBodies.values.append(body)
        return NS(name=name,bodies=Collection([body])),body,NS(name=name,transform=NS(asArray=lambda:[1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.]))
    fusion=NS(Design=NS(cast=lambda d:d),DesignTypes=NS(ParametricDesignType=1),BRepFace=NS(cast=lambda v:v if isinstance(v,Face) else None),BRepBody=NS(cast=lambda v:v if isinstance(v,Body) else None),SketchLine=NS(cast=lambda v:None))
    truth=dict(samples=[],errors=[])
    def journal(phase,case=None,**fields):event('journal',phase=phase,**fields)
    def collect():event('gc',open_document_count=sum(not d.closed for d in documents));return gc.collect()
    env=dict(adsk=NS(core=NS(DocumentTypes=NS(FusionDesignDocumentType=1)),fusion=fusion),app=NS(documents=NS(add=lambda kind:Doc())),
        cases=('sheet_face','sheet_face'),truth=truth,output=MemoryPath('MEMORY_ONLY',files),gc=NS(collect=collect),json=json,traceback=traceback,hashlib=hashlib,
        HALTED_NATIVE_ATTRIBUTE='_codex_FusionFileStudy_surface_trim_halted_native_handles',journal=journal,persist=lambda:json.dumps(truth),patch=patch)
    tree=ast.parse(source);run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
    helpers=[n for n in run.body if isinstance(n,ast.FunctionDef) and n.name not in ('patch','journal','persist')]
    exec(compile(ast.fix_missing_locations(ast.Module(body=helpers,type_ignores=[])),'<actual Trim helper AST>','exec'),env)
    # Execute the actual outer case loop/final status, preserving its native-scope boundaries.
    loop_index=next(i for i,n in enumerate(run.body) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='case')
    driver=ast.FunctionDef(name='_fixture_driver',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=run.body[loop_index:],decorator_list=[])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[driver],type_ignores=[])),'<actual Trim orchestration AST>','exec'),env)
    env['_fixture_driver']();gc.collect();json.dumps(truth)
    quarantine=getattr(fusion,env['HALTED_NATIVE_ATTRIBUTE'],[])
    unsafe=scenario in ('cancel_false','cancel_raises','create_raises','roll_false')
    if unsafe:
        assert len(documents)==1 and not documents[0].closed and quarantine
        assert not any(e['event'] in ('export','document_close') for e in events)
        assert truth['terminal_status']=='HaltedUnfinishedTransaction'
        for entry in quarantine:
            assert all(not isinstance(v,(BaseException,type(traceback))) and not callable(v) for v in entry['handles'].values())
        # The actual top-of-run guard also blocks a subsequent invocation sharing the module anchor.
        initial_guard=run.body[0]
        try:exec(compile(ast.fix_missing_locations(ast.Module(body=[initial_guard],type_ignores=[])),'<actual quarantine guard>','exec'),env)
        except RuntimeError:pass
        else:raise AssertionError('Quarantined module did not block another invocation')
    else:
        assert len(documents)==2 and all(d.closed for d in documents) and not quarantine
        assert not violations,violations
        assert all(ref() is None for _,ref in references),'Exception/native wrapper retained after clean case teardown'
        if scenario=='selection_error_cancel_success':assert any(e['event']=='cancel' for e in events)
        if scenario=='snapshot_exception':assert any(e['event']=='release' and e['kind']=='ExceptionFrameProbe' and e['document_open'] for e in events)
        if scenario=='final_compute_false':assert not any(e['event']=='export' for e in events)
    assert not violations,violations
    return dict(scenario=scenario,outcome='PassedSyntheticBehavior',document_count=len(documents),closed_document_count=sum(d.closed for d in documents),
        quarantined_document_count=len(quarantine),terminal_status=truth['terminal_status'],events=events,
        simulated_native_wrapper_release_after_close=False,actual_native_execution=False,
        artifact_scope='All export/complete bytes are synthetic in-memory fixture data; no filesystem native archive, Fusion API, UI or dispatcher used')


def validate(root,native_evidence=None):
    source=(root/SOURCE).read_text();investigation=json.loads((root/'fusion-trim-crash-investigation.json').read_text());cer=[]
    for item in investigation['local_native_crash_evidence']:
        path=Path(item['local_crash_archive']);raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==item['archive_sha256']
        with zipfile.ZipFile(path) as archive:text=archive.read('crashLog.txt')
        assert hashlib.sha256(text).hexdigest()==item['crash_text_sha256']
        decoded=text.decode('utf-8','replace');assert '_wrap_delete_TrimFeature' in decoded and 'TrimFeatureInputD2Ev' in decoded and 'commitTransaction' in decoded
        cer.append(dict(archive_sha256=item['archive_sha256'],crash_text_sha256=item['crash_text_sha256'],reported_modified_utc=item['archive_modified_utc'],relevant_trim_feature_input_transaction_destructors_present=True))
    scenarios=('success','selection_error_cancel_success','snapshot_exception','cancel_false','cancel_raises','create_raises','roll_false','final_compute_false')
    results=[fixture(source,s) for s in scenarios]
    native=dict(status='NotProvided',native_fix_verified=False,scope='Synthetic teardown tests cannot establish native Fusion crash repair')
    if native_evidence is not None:
        native=dict(status='RootProvidedEvidence',evidence_path=str(native_evidence),evidence_sha256=hashlib.sha256(native_evidence.read_bytes()).hexdigest(),evidence=json.loads(native_evidence.read_text()),
            scope='Actual execution evidence supplied by root; preserve its scope and distinguish it from synthetic tests. This validator performs no live process/API/UI check.')
    return dict(scope='Offline actual-generator resource-order behavior with fake native wrappers, plus verified historical CER artifacts; separate actual validation only when root supplies evidence',
        synthetic_scenario_count=len(results),synthetic_scenarios=results,historical_CER_evidence=cer,native_validation=native,
        source_sha256={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in (SOURCE,'GenerateSurfaceTrimLifecycleValidation.py','validate_trim_lifecycle.py','fusion-trim-crash-investigation.json')},
        limitations=['Mocks check Python ownership/destruction ordering, not Autodesk native resource graphs or crash absence',
            'Failure-only strong quarantine intentionally retains named native handles while the owned document remains open; no traceback/frame objects retained',
            'CER correlation supports retained-wrapper cleanup as a leading hypothesis, not a complete Autodesk root cause',
            'No live Fusion API/UI execution or synthetic native archives written by this validator'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--native-evidence',type=Path);parser.add_argument('--output',default='trim-lifecycle-validation.json');args=parser.parse_args()
    result=validate(Path(__file__).resolve().parent,args.native_evidence);Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(synthetic_scenario_count=result['synthetic_scenario_count'],native_validation=result['native_validation']['status'])))

if __name__=='__main__':main()
