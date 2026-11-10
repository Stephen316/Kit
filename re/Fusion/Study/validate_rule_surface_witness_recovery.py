"""Actual recovery source executed with synthetic lifetime-tracked SDK wrappers."""
import argparse
import ast
import gc
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import weakref

ROOT=Path(__file__).resolve().parent
SOURCE='GenerateRecoverRuleSurfaceWitness.py'
SCENARIOS=('known_pre_add_success','wrong_phase','added_witness','different_document',
           'input_face_mismatch','concrete_equality_NotImplemented','broken_recovery_alias',
           'different_recovery_root','different_source_body','close_false')


def validate():
    text=(ROOT/SOURCE).read_text();tree=ast.parse(text)
    # Importing the real SDK or calling a live application is deliberately absent.
    body=[n for n in tree.body if isinstance(n,(ast.Assign,ast.FunctionDef))]
    code=compile(ast.fix_missing_locations(ast.Module(body=body,type_ignores=[])),SOURCE+' [synthetic SDK]','exec')
    results=[]
    for scenario in SCENARIOS:
        events=[];live=weakref.WeakValueDictionary();state=dict(open=True,closes=0,forbidden_calls=0)
        class Native:
            def __init__(self,kind,identity=1):self.kind=kind;self.identity=identity;live[id(self)]=self
            @property
            def isValid(self):return state['open']
            def __del__(self):events.append(dict(event='native_wrapper_released',kind=self.kind,document_open=state['open']))
        class Document(Native):
            def __init__(self,identity=1):super().__init__('Document',identity)
            def __eq__(self,other):return isinstance(other,Document) and self.identity==other.identity
            @property
            def products(self):return SimpleNamespace(itemByProductType=lambda _:Design())
            def close(self,save):
                assert save is False
                state['closes']+=1
                remaining=[o.kind for o in list(live.values()) if not isinstance(o,Document)]
                assert remaining==[],('Native wrappers survive close boundary',remaining)
                events.append(dict(event='close',save=save))
                if scenario=='close_false':return False
                state['open']=False;return True
        class Design(Native):
            def __init__(self):super().__init__('Design')
            @staticmethod
            def cast(value):return value
            def __eq__(self,other):return isinstance(other,Design) and self.identity==other.identity
            @property
            def parentDocument(self):return state['document']
            @property
            def rootComponent(self):return Component()
            def findEntityByToken(self,token):return [Face(10)]
            def computeAll(self):state['forbidden_calls']+=1;raise AssertionError('Recovery must not recompute')
        class Face(Native):
            def __init__(self,identity):super().__init__('BRepFace',identity)
            @property
            def body(self):return Body()
            def __eq__(self,other):
                if scenario=='concrete_equality_NotImplemented':return NotImplemented
                return isinstance(other,Face) and self.identity==other.identity
        class Body(Native):
            def __init__(self,identity=1):super().__init__('BRepBody',identity)
            def __eq__(self,other):return isinstance(other,Body) and self.identity==other.identity
            @property
            def parentComponent(self):return Component()
        class Component(Native):
            def __init__(self):super().__init__('Component')
            def __eq__(self,other):return isinstance(other,Component) and self.identity==other.identity
            @property
            def parentDesign(self):return Design()
            @property
            def features(self):return Features()
        class Features(Native):
            def __init__(self):super().__init__('Features')
            count=1
            def item(self,index):return SimpleNamespace(name='RuleFillet')
            @property
            def offsetFeatures(self):return Offsets()
        class Offsets(Native):
            def __init__(self):super().__init__('OffsetFeatures')
            def __eq__(self,other):return False
            @property
            def count(self):return int(scenario=='added_witness')
            def add(self,*args):state['forbidden_calls']+=1;raise AssertionError('Recovery must not add')
        class Collection(Native):
            def __init__(self,identity=10):super().__init__('ObjectCollection');self.face=identity
            count=1
            def item(self,index):return Face(self.face)
        class Inputs(Native):
            def __init__(self):super().__init__('OffsetFeatureInput')
            @property
            def entities(self):return Collection(11 if scenario=='input_face_mismatch' else 10)
            @property
            def distance(self):return Value()
            isChainSelection=False;operation=0
        class Value(Native):
            def __init__(self):super().__init__('ValueInput')
            realValue=0.
        class Base:
            def __eq__(self,other):raise AssertionError('Abstract Base equality must not be called')
        fusion=SimpleNamespace(FusionDocument=Document,Design=Design,BRepFace=Face,
            OffsetFeatureInput=Inputs,OffsetFeatures=Offsets,Component=Component,BRepBody=Body,FeatureOperations=SimpleNamespace(NewBodyFeatureOperation=0))
        fake=SimpleNamespace(core=SimpleNamespace(Base=Base,Document=Document),fusion=fusion)
        with tempfile.TemporaryDirectory(prefix='rule-recovery-test-') as folder:
            folder=Path(folder);source=folder/SOURCE;source.write_text(text)
            for artifact in ('rulefilletsurfaces-9dd46198ca8a','recoverrulesurfacewitness-b0a35766ba60',
                             'inspectrulewitnessquarantine-151086054fb5','inspectrulewitnessquarantine-2a852f50f1a0'):
                shutil.copytree(ROOT/artifact,folder/artifact)
            env=dict(__file__=str(source),adsk=fake,Path=Path,json=json,hashlib=hashlib,uuid=__import__('uuid'),
                datetime=__import__('datetime').datetime,timezone=__import__('datetime').timezone,
                gc=SimpleNamespace(collect=lambda:(events.append(dict(event='gc',document_open=state['open'])),gc.collect())[1]))
            exec(code,env)
            doc=Document();state['document']=doc
            handles={k:None for k in env['HANDLE_KEYS']}
            handles.update(design=Design(),root=Component(),offsets=Offsets(),source_face=Face(10),
                source_body=Body(2 if scenario=='different_source_body' else 1),entities=Collection(),distance=Value(),inputs=Inputs(),
                input_entities=Collection(),input_face=Face(10),input_distance=Value())
            setattr(fusion,env['WITNESS'],[dict(phase='other' if scenario=='wrong_phase' else 'create_witness',
                document=Document(2) if scenario=='different_document' else doc,native_handles=handles)])
            setattr(fusion,env['DOCUMENTS'],[doc])
            rows=getattr(fusion,env['WITNESS']);entry=rows[0]
            recovery_root=Component();recovery_root.identity=2 if scenario=='different_recovery_root' else 1
            recovery_handles=dict(design=Design(),root=recovery_root,offsets=Offsets(),resolved=None,input_faces=None,
                quarantine_rows=rows,quarantine_entry=entry,
                native_handles=dict(handles) if scenario=='broken_recovery_alias' else handles)
            setattr(fusion,env['RECOVERY'],[dict(phase='release_known_handles',document=doc,native_handles=recovery_handles)])
            handles=rows=entry=recovery_handles=recovery_root=None
            env['run'](None)
            output,=[p for p in folder.glob('recoverrulesurfacewitness-*') if p.name!=env['V1_CAPTURE']];report=json.loads((output/'recovery.json').read_text())
            success=scenario=='known_pre_add_success'
            assert report['status']==('RecoveredClosed' if success else 'HaltedRetained'),(scenario,report)
            assert state['closes']==(1 if success or scenario=='close_false' else 0)
            assert state['forbidden_calls']==0
            if success:
                assert not getattr(fusion,env['WITNESS']) and not getattr(fusion,env['DOCUMENTS']) and not getattr(fusion,env['RECOVERY'])
                released=[e for e in events if e['event']=='native_wrapper_released' and e['kind']!='Document']
                assert released and all(e['document_open'] for e in released)
                beforeclose=events[:next(i for i,e in enumerate(events) if e['event']=='close')]
                assert len([e for e in beforeclose if e['event']=='gc' and e['document_open']])==2
                assert report['release']['concrete_source_face_equality'] is True
                assert report['release']['concrete_input_face_equality'] is True
            else:
                assert state['open'] and getattr(fusion,env['DOCUMENTS'])
                assert getattr(fusion,env['RECOVERY'])
            results.append(dict(scenario=scenario,status=report['status'],close_calls=state['closes'],
                native_wrapper_release_before_close_verified=success,uncertain_state_retained=not success,
                abstract_Base_equality_calls=0,feature_timeline_compute_export_calls=state['forbidden_calls']))
            # Test-only teardown keeps the synthetic document open; never native.
            state['open']=True
            setattr(fusion,env['WITNESS'],[]);setattr(fusion,env['DOCUMENTS'],[]);setattr(fusion,env['RECOVERY'],[])
            gc.collect()
    return dict(scope='Offline v2 actual-source resource lifetime checks with synthetic SDK wrappers; recovery is prepared/unexecuted and native cleanup success is not claimed',
        saved_failure_evidence=env['saved_evidence'](ROOT),source_sha256={SOURCE:hashlib.sha256((ROOT/SOURCE).read_bytes()).hexdigest(),
            Path(__file__).name:hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        scenarios=results,summary=dict(synthetic_scenarios=len(results),live_API_calls=0,native_recovery_verified=False),
        limitations=['Synthetic wrappers prove orchestration and failure gates only, not native destructor safety.',
            'Concrete equality NotImplemented is rejected without truth conversion.',
            'No feature add/cancel, timeline movement, recompute/export or unrelated-document operations are allowed.'])


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'rule-surface-witness-recovery-v2-validation.json');args=parser.parse_args()
    result=validate();args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary']))
