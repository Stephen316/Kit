"""Offline behavioral check of actual dispatcher AST with in-memory resources.

No dispatcher module import, CoreGraphics load, process command, UI operation,
permission query or keyboard event is executed. Only the actual dispatch
function body runs against traceable in-memory boundary objects.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path,PurePosixPath
import subprocess
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parent
SOURCE='dispatch_fusion_script.py'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dispatch_code():
    source=(ROOT/SOURCE).read_text();tree=ast.parse(source)
    functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    assert 'dispatch' in functions and 'read_session_lock_state' in functions
    assignments={t.id:n.value for n in tree.body if isinstance(n,ast.Assign) for t in n.targets if isinstance(t,ast.Name)}
    prepare=ast.literal_eval(assignments['PREPARE'])
    # Existing target-field verification remains the sole modeled UI boundary.
    for fragment in ('set value of text field 1 of mainWindow to commandText',
        'value of text field 1 of mainWindow is commandText',
        'value of attribute "AXFocused" of text field 1 of mainWindow is true',
        'value of radio button "Txt" of mainWindow is 1',
        'if frontBefore is not frontAfter then',
        'if fieldReady is not true then error',
        'return (frontBefore as text) & "|" & (targetPid as text)'):
        assert fragment in prepare,('Target-field validation changed',fragment)
    isolated=ast.Module(body=[functions['dispatch']],type_ignores=[])
    return compile(isolated,SOURCE,'exec'),prepare


def run_case(code,prepare,case,lock_state,*,active_hold=False,field_valid=True):
    trace=[];memory={
        '/owned/study/GenerateOwnedProbe.py':b'owned generator bytes',
        '/owned/study/dispatch_fusion_script.py':b'not executed module bytes',
        '/owned/study/fusion-live-capture-hold.json':json.dumps({'active':active_hold}).encode()}
    class MemPath:
        def __init__(self,value):self.path=PurePosixPath(str(value))
        def __str__(self):return str(self.path)
        def __eq__(self,other):return isinstance(other,MemPath) and self.path==other.path
        def __truediv__(self,value):return MemPath(self.path/str(value))
        @property
        def parent(self):return MemPath(self.path.parent)
        @property
        def name(self):return self.path.name
        @property
        def suffix(self):return self.path.suffix
        def resolve(self,strict=False):
            if strict and str(self) not in memory:raise FileNotFoundError(str(self))
            return self
        def with_name(self,name):return MemPath(self.path.with_name(name))
        def exists(self):return str(self) in memory
        def is_file(self):return str(self) in memory
        def read_bytes(self):return memory[str(self)]
        def read_text(self):return self.read_bytes().decode()
    class Call:
        def __init__(self,fn):self.fn=fn
        def __call__(self,*args):return self.fn(*args)
    next_event=[100]
    def preflight():trace.append(dict(action='event_permission_preflight'));return True
    def create(context,key,down):
        assert context is None and key==36 and type(down) is bool
        next_event[0]+=1;event=next_event[0]
        trace.append(dict(action='create_target_return_event',event=event,down=down));return event
    def flags(event,value):assert value==0;trace.append(dict(action='set_event_flags',event=event))
    def post(pid,event):trace.append(dict(action='post_to_pid',pid=pid,event=event))
    def release(event):trace.append(dict(action='release_event',event=event))
    cg=SimpleNamespace(CGPreflightPostEventAccess=Call(preflight),CGEventCreateKeyboardEvent=Call(create),
        CGEventSetFlags=Call(flags),CGEventPostToPid=Call(post))
    cf=SimpleNamespace(CFRelease=Call(release))
    def load(name):
        trace.append(dict(action='load_native_library',name=name))
        if name=='/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics':return cg
        if name=='/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation':return cf
        raise AssertionError('Unexpected native library boundary')
    def session(cg_arg=None,cf_arg=None):
        assert cg_arg is cg and cf_arg is cf
        trace.append(dict(action='read_session_lock_state',value=lock_state));return lock_state
    def run(args,**kwargs):
        assert args==['/usr/bin/osascript','-','Python.RunScript "/owned/study/GenerateOwnedProbe.py"']
        assert kwargs==dict(input=prepare,text=True,capture_output=True,check=True,timeout=20)
        trace.append(dict(action='verified_target_field_prepare',accepted=field_valid))
        if not field_valid:raise subprocess.CalledProcessError(1,args,stderr='Fusion text command field could not be verified; no event posted')
        return SimpleNamespace(stdout='111|4242\n')
    namespace=dict(Path=MemPath,__file__='/owned/study/dispatch_fusion_script.py',json=json,hashlib=hashlib,
        ctypes=SimpleNamespace(CDLL=load,c_bool=object,c_void_p=object,c_ushort=object,c_uint64=object,c_int=object),
        subprocess=SimpleNamespace(run=run,CalledProcessError=subprocess.CalledProcessError),
        PREPARE=prepare,read_session_lock_state=session)
    exec(code,namespace)
    result=None;error=None
    try:result=namespace['dispatch'](MemPath('/owned/study/GenerateOwnedProbe.py'))
    except RuntimeError as failure:error=dict(type=type(failure).__name__,message=str(failure))
    actions=[r['action'] for r in trace]
    if active_hold:
        assert error and 'suspend' in error['message'].lower()
        assert not trace,'Active hold reached native/session/UI boundary'
    elif lock_state is True:
        assert error and 'lock' in error['message'].lower()
        assert actions==['load_native_library','load_native_library','read_session_lock_state']
    else:
        assert actions[:4]==['load_native_library','load_native_library','read_session_lock_state','event_permission_preflight']
        assert actions.count('verified_target_field_prepare')==1
        created=[r['event'] for r in trace if r['action']=='create_target_return_event']
        released=[r['event'] for r in trace if r['action']=='release_event']
        assert len(created)==2 and released==created
        posted=[r for r in trace if r['action']=='post_to_pid']
        if field_valid:
            assert error is None and result['target_pid']==4242 and result['global_keyboard_events'] is False
            assert [r['event'] for r in posted]==created and {r['pid'] for r in posted}=={4242}
            assert actions.index('verified_target_field_prepare')<actions.index('post_to_pid')
        else:
            assert result is None and error and 'preparation failed before Return' in error['message']
            assert not posted
    return dict(case=case,modeled_session_lock_state=lock_state,active_hold=active_hold,modeled_field_valid=field_valid,
        result=result,error=error,boundary_trace=trace,passed=True)


def validate():
    code,prepare=dispatch_code()
    cases=[run_case(code,prepare,'Active hold blocks before native loading',True,active_hold=True),
        run_case(code,prepare,'Explicit locked session blocks before event permission/event/UI',True),
        run_case(code,prepare,'Unlocked session retains exact verified-target preparation',False),
        run_case(code,prepare,'Unknown session state retains verified-target preparation',None),
        run_case(code,prepare,'Unknown session state cannot bypass failed target-field verification',None,field_valid=False)]
    return dict(scope='Actual dispatcher AST control flow under modeled session/native/UI boundaries; no native lock-state or live dispatch verification',
        summary=dict(behavioral_scenarios=len(cases),passed=len(cases),active_hold_pre_native_blocks=1,locked_pre_event_UI_blocks=1,
            unlocked_verified_target_fallthrough=1,unknown_verified_target_fallthrough=1,unknown_failed_field_blocks=1,
            actual_native_library_loads=0,actual_UI_calls=0,actual_keyboard_events=0,actual_process_commands=0),
        cases=cases,source_sha256={p:sha(ROOT/p) for p in ('validate_fusion_capture_preflight.py',SOURCE)},
        limitations=['Session state is stubbed True/False/None; this does not test macOS session querying or prove a live native fix',
            'Only the isolated actual dispatch function AST executes; imports, CLI and read_session_lock_state native implementation are not executed',
            'Verified command-field AppleScript is checked structurally and passed unchanged to the in-memory boundary; no accessibility action runs',
            'Unknown state is retained as unknown and never relabeled unlocked; existing verified-target preparation still controls posting',
            'No Fusion capture, foreground/focus change, permission request, event posting, live API, main decoder or Git mutation'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',default='fusion-capture-preflight-validation.json');a=p.parse_args()
    result=validate();Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['summary'],sort_keys=True))
if __name__=='__main__':main()
