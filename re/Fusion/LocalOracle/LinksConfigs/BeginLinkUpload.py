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

run_name = 'Accept2'
accept = private / 'accept'
prepared = json.loads((accept / 'Prepare.json').read_text())
app = adsk.core.Application.get()
report = {'fusion_version': app.version, 'run': run_name, 'documents_before': app.documents.count, 'uploads': []}
try:
    project, folder = acceptance_folder(app, subfolder=run_name)
    report['folder'] = folder.name
    present = {folder.dataFiles.item(index).name for index in range(folder.dataFiles.count)}
    futures = {}
    for entry in prepared['outputs']:
        source = accept / (entry['name'] + '.f3d')
        row = {'name': entry['name'], 'file_sha256': digest(source), 'prepared_sha256': entry['output_sha256']}
        report['uploads'].append(row)
        if row['file_sha256'] != entry['output_sha256']:
            raise RuntimeError('Prepared file changed: ' + entry['name'])
        if entry['name'] in present:
            row['state'] = 'already_present'
            continue
        future = folder.uploadFile(str(source))
        if future is None:
            raise RuntimeError('Upload returned no future: ' + entry['name'])
        futures[entry['name']] = future
        row['upload_state'] = int(future.uploadState)
    builtins._kit_link_upload = types.SimpleNamespace(futures=futures)
    report['status'] = 'started'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    report['documents_after'] = app.documents.count
    write(private / 'BeginLinkUpload.json', report)
