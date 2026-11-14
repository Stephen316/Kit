import hashlib
import importlib
import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
common = importlib.reload(importlib.import_module('DrawingCommon'))

import adsk.core

app = common.app
store = common.state()
variants = common.SCRATCH / 'Variants'
PLAN_FILES = ('Plan.json', 'Plan2.json', 'Plan3.json', 'Plan4.json', 'Plan5.json', 'Plan6.json', 'Plan7.json', 'Plan8.json', 'Plan9.json', 'Plan10.json', 'Plan11.json', 'PlanFresh.json', 'PlanAuthored.json', 'PlanBisect.json', 'PlanGrafts.json', 'PlanTransplant.json', 'PlanContainer.json', 'PlanDims.json', 'PlanAsme.json', 'PlanChildren.json', 'PlanEdges.json', 'PlanUnknowns.json')
report = {'fusion_version': app.version, 'documents_before': app.documents.count, 'stage': 'starting', 'uploads': {}}


def run():
    rows = {}
    for name in PLAN_FILES:
        if (variants / name).exists():
            for row in json.loads((variants / name).read_text())['variants']:
                rows[row['label']] = row
    wanted = json.loads((variants / 'Selection.json').read_text())['labels']
    missing = [label for label in wanted if label not in rows]
    if missing:
        raise RuntimeError('No plan row for ' + ', '.join(missing))
    project, created = common.ensure_project()
    report['project_created'] = created
    stamp = time.strftime('%Y%m%d%H%M%S')
    folder = project.rootFolder.dataFolders.add('KitDrw Uploads ' + stamp)
    if folder is None:
        raise RuntimeError('Upload folder creation failed')
    report['folder'] = folder.name
    uploads = store.setdefault('uploads', {})
    for label in wanted:
        row = rows[label]
        path = variants / row['file']
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise RuntimeError('Variant changed after planning: ' + row['label'])
        child = folder.dataFolders.add('KitDrw ' + row['label'])
        future = child.uploadFile(str(path))
        if future is None:
            raise RuntimeError('Upload did not start for ' + row['label'])
        uploads[row['label']] = {'future': future, 'folder': child, 'sha256': row['sha256'], 'started': time.time()}
        report['uploads'][row['label']] = {'sha256': row['sha256'], 'state': int(future.uploadState)}
    report['stage'] = 'uploads_started'


try:
    run()
    report['status'] = 'started'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    report['documents_after'] = app.documents.count
    common.save_json(variants / 'BeginUploads.json', report)
