"""Read-only Fusion script execution evidence; creates no design documents."""
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback
import uuid


def run(context):
    source=Path(__file__).resolve()
    output=source.parent/('apiexecution-'+uuid.uuid4().hex[:12])
    output.mkdir()
    executed=source.read_bytes()
    (output/'executed-generator-source.txt').write_bytes(executed)
    truth={'status':'entered_run','pid':os.getpid(),
        'executed_generator_sha256':hashlib.sha256(executed).hexdigest(),
        'errors':[], 'documents_created':0,
        'scope':'Read-only API/runtime and exact study-script stack filenames; no document access beyond collection count, no UI mutation or process restart.'}
    def save():
        (output/'ground_truth.json').write_text(json.dumps(truth,indent=2)+'\n')
    save()
    try:
        import adsk.core
        import adsk.fusion
        app=adsk.core.Application.get()
        truth.update(fusion_version=app.version,document_count=app.documents.count,
            fusion_module_file=getattr(adsk.fusion,'__file__',None),
            study_directory_on_sys_path=str(source.parent) in sys.path)
        sdk=Path(adsk.fusion.__file__)
        truth['fusion_module_sha256']=hashlib.sha256(sdk.read_bytes()).hexdigest()
        stacks=[]
        for thread_id,frame in sys._current_frames().items():
            study_frames=[]
            while frame is not None:
                filename=Path(frame.f_code.co_filename)
                if filename.parent==source.parent and filename!=source:
                    study_frames.append({'file':filename.name,'function':frame.f_code.co_name,'line':frame.f_lineno})
                frame=frame.f_back
            if study_frames:stacks.append({'thread_id':thread_id,'study_frames':study_frames})
        truth['other_current_study_script_frames']=stacks
        truth['status']='complete'
    except Exception:
        truth['errors'].append(traceback.format_exc())
        truth['status']='error'
    finally:
        save()
        (output/'complete.txt').write_text('terminal read-only runtime probe; inspect actual errors and frames\n')
