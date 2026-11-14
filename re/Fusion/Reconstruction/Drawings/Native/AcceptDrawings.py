import importlib
import json
import runpy
import sys
import time
import traceback
from pathlib import Path

base = Path(__file__).resolve().parent
sys.path.insert(0, str(base))
common = importlib.reload(importlib.import_module('DrawingCommon'))

import adsk
import adsk.core

variants = common.SCRATCH / 'Variants'
request = json.loads((variants / 'Accept.json').read_text())
report = {'fusion_version': common.app.version, 'request': request, 'steps': []}
target = variants / ('Accept' + request['tag'] + '.json')


def step(name, script, config_name=None, config=None):
    if config_name:
        common.save_json(variants / config_name, config)
    row = {'name': name, 'started': time.strftime('%H:%M:%S')}
    report['steps'].append(row)
    common.save_json(target, report)
    try:
        runpy.run_path(str(base / script), run_name='__kit_fusion_oracle__')
        row['status'] = 'returned'
    except Exception:
        row['status'] = 'raised'
        row['traceback'] = traceback.format_exc()
    row['finished'] = time.strftime('%H:%M:%S')
    row['documents_after'] = common.app.documents.count
    common.save_json(target, report)


def wait_complete(folder_name, labels, seconds):
    project, _ = common.ensure_project()
    folders = project.rootFolder.dataFolders
    parent = next(folders.item(index) for index in range(folders.count) if folders.item(index).name == folder_name)
    deadline = time.monotonic() + seconds
    states = {}
    while time.monotonic() < deadline:
        children = {parent.dataFolders.item(index).name: parent.dataFolders.item(index) for index in range(parent.dataFolders.count)}
        for label in labels:
            child = children.get(common.TOKEN + ' ' + label)
            files = [child.dataFiles.item(index) for index in range(child.dataFiles.count)] if child else []
            states[label] = {'files': len(files), 'complete': bool(files) and all(item.isComplete for item in files), 'drawing': any(item.fileExtension == 'f2d' for item in files)}
        if all(value['complete'] and value['drawing'] for value in states.values()):
            break
        deadline_left = deadline - time.monotonic()
        pause = time.monotonic() + min(5, max(deadline_left, 0))
        while time.monotonic() < pause:
            adsk.doEvents()
    report.setdefault('upload_waits', []).append({'states': states, 'seconds': round(seconds - max(deadline - time.monotonic(), 0), 1)})
    common.save_json(target, report)


def refuse_quarantined():
    """Refuse the whole request before touching Fusion when it names a variant known or suspected to crash the drawing engine."""
    path = variants / 'Quarantine.json'
    if not path.exists():
        return
    quarantined = json.loads(path.read_text())['labels']
    named = set(request.get('upload', []))
    for item in request['plan']:
        named.update(item.get('labels', []))
        named.update([item['label']] if 'label' in item else [])
    hits = sorted(named & set(quarantined))
    if hits:
        raise RuntimeError('Quarantined variants requested: ' + ', '.join(hits))


try:
    refuse_quarantined()
    for item in request.get('before', []):
        if item['kind'] == 'capacity':
            step('capacity', 'EditableCapacity.py', 'Capacity.json', item['config'])
        elif item['kind'] == 'recycle':
            step('recycle ' + item['config']['tag'], 'RecycleDocuments.py', 'Recycle.json', item['config'])
    uploads = request.get('upload', [])
    folder = request.get('folder')
    if uploads:
        step('upload', 'BeginUploads.py', 'Selection.json', {'labels': uploads, 'tag': request['tag']})
        folder = json.loads((variants / 'BeginUploads.json').read_text())['folder']
        report['folder'] = folder
        wait_complete(folder, uploads, request.get('upload_seconds', 600))
    for item in request['plan']:
        if item['kind'] == 'upload':
            step('upload ' + ' '.join(item['labels']), 'BeginUploads.py', 'Selection.json', {'labels': item['labels'], 'tag': request['tag']})
            folder = json.loads((variants / 'BeginUploads.json').read_text())['folder']
            report.setdefault('folders', []).append(folder)
            wait_complete(folder, item['labels'], request.get('upload_seconds', 600))
            continue
        where = report['folders'][item['folder_index']] if 'folder_index' in item else item.get('folder', folder)
        if item['kind'] == 'inspect':
            step('inspect ' + item['tag'], 'InspectUploads.py', 'Selection.json', {'labels': item['labels'], 'tag': item['tag'], 'folder': where, 'export_dwg': item.get('export_dwg', False)})
        elif item['kind'] == 'edit':
            step('edit ' + item['label'], 'EditAcceptance.py', 'Edit.json', {'folder': where, 'label': item['label'], 'expression': item['expression'], 'require_editable': item.get('require_editable', False)})
        elif item['kind'] == 'recycle':
            step('recycle ' + item['config']['tag'], 'RecycleDocuments.py', 'Recycle.json', item['config'])
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    report['documents_after'] = common.app.documents.count
    common.save_json(target, report)
