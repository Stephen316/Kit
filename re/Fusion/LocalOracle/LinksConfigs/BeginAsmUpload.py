import builtins
import json
import sys
import traceback
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.modules.pop('LinkCommon', None)
import adsk.core
from LinkCommon import acceptance_folder, digest, private, write

author = private / 'author'
plan = json.loads((author / 'Upload.json').read_text())
app = adsk.core.Application.get()
report = {'fusion_version': app.version, 'run': plan['run'], 'documents_before': app.documents.count, 'uploads': []}
try:
    project, folder = acceptance_folder(app, subfolder=plan['run'])
    report['folder'] = folder.name
    present = {folder.dataFiles.item(index).name for index in range(folder.dataFiles.count)}
    futures = dict(getattr(getattr(builtins, '_kit_asm_upload', None), 'futures', {}) or {})
    for entry in plan['files']:
        source = author / (entry['name'] + '.f3d')
        row = {'name': entry['name'], 'file_sha256': digest(source), 'planned_sha256': entry['sha256']}
        report['uploads'].append(row)
        if row['file_sha256'] != entry['sha256']:
            raise RuntimeError('Planned file changed: ' + entry['name'])
        if entry['name'] in present:
            row['state'] = 'already_present'
            continue
        future = folder.uploadFile(str(source))
        if future is None:
            raise RuntimeError('Upload returned no future: ' + entry['name'])
        futures[entry['name']] = future
        row['upload_state'] = int(future.uploadState)
    builtins._kit_asm_upload = types.SimpleNamespace(futures=futures)
    report['status'] = 'started'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    report['documents_after'] = app.documents.count
    write(private / 'BeginAsmUpload.json', report)
