import builtins
import json
import runpy
import sys
import traceback
from pathlib import Path

here = Path(__file__).resolve().parent
sys.path.insert(0, str(here))
sys.modules.pop('LinkCommon', None)
import adsk.core
from LinkCommon import acceptance_folder, private, pump, write

author = private / 'author'
plan = json.loads((author / 'Then.json').read_text())
upload = json.loads((author / 'Upload.json').read_text())
app = adsk.core.Application.get()
out_path = private / 'UploadThen.json'
report = {'fusion_version': app.version, 'run': upload['run'], 'next': plan['next'], 'documents_before': app.documents.count}


def find_file(folder, name):
    for index in range(folder.dataFiles.count):
        item = folder.dataFiles.item(index)
        if item.name == name:
            return item
    return None


def upload_states(names):
    futures = getattr(getattr(builtins, '_kit_asm_upload', None), 'futures', {}) or {}
    return {name: int(futures[name].uploadState) for name in names if name in futures}


try:
    if plan['next'] not in ('ProbeAsmTargets.py', 'AcceptAsmRoot.py'):
        raise RuntimeError('Unknown next stage')
    runpy.run_path(str(here / 'BeginAsmUpload.py'), run_name='__kit_upload__')
    begin = json.loads((private / 'BeginAsmUpload.json').read_text())
    report['begin_status'] = begin.get('status')
    (author / ('BeginAsmUpload.' + plan['stage'] + '.json')).write_text(json.dumps(begin, indent=2) + '\n')
    if begin.get('status') != 'started':
        raise RuntimeError('Upload did not start')
    names = [entry['name'] for entry in upload['files']]
    finished = int(adsk.core.UploadStates.UploadFinished)
    report['uploads_finished'] = pump(lambda: all(state == finished for state in upload_states(names).values()), 900)
    report['upload_states'] = upload_states(names)
    project, folder = acceptance_folder(app, subfolder=upload['run'])
    report['files_listed'] = pump(lambda: all(find_file(acceptance_folder(app, subfolder=upload['run'])[1], name) is not None for name in names), 300)
    write(out_path, report)
    if report['uploads_finished'] and report['files_listed']:
        runpy.run_path(str(here / plan['next']), run_name='__kit_next__')
        report['next_ran'] = True
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    report['documents_after'] = app.documents.count
    write(out_path, report)
