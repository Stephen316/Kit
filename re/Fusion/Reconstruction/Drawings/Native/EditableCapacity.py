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
variants = common.SCRATCH / 'Variants'
request = json.loads((variants / 'Capacity.json').read_text())
target = variants / 'Capacity.json.report.json'
report = {'fusion_version': app.version, 'documents_before': app.documents.count, 'stage': 'starting', 'deleted': []}
LIMIT_SECONDS = 2 * 3600


def eligible_projects():
    hub = app.data.activeHub
    rows = []
    for index in range(hub.dataProjects.count):
        project = hub.dataProjects.item(index)
        name = project.name
        if name == common.PROJECT or (name.startswith('Kit Fusion') and ('Acceptance' in name or 'Bundle' in name)):
            rows.append(project)
    return rows


def walk(folder, path, rows):
    for index in range(folder.dataFiles.count):
        item = folder.dataFiles.item(index)
        rows.append({'file': item, 'path': path, 'name': item.name, 'extension': item.fileExtension, 'modified': item.dateModified, 'read_only': common.safe(lambda: item.isReadOnly)})
    for index in range(folder.dataFolders.count):
        child = folder.dataFolders.item(index)
        walk(child, path + '/' + child.name, rows)


def inventory():
    rows = []
    for project in eligible_projects():
        walk(project.rootFolder, project.name, rows)
    return rows


def protected(row, now):
    if now - row['modified'] < LIMIT_SECONDS:
        return True
    if any(token in row['path'] for token in request.get('keep_paths', [])):
        return True
    open_names = {app.documents.item(index).name for index in range(app.documents.count)}
    return row['name'] in open_names


def summary(rows, now):
    editable = [row for row in rows if row['read_only'] is False]
    return {'files': len(rows), 'editable': len(editable), 'read_only': sum(1 for row in rows if row['read_only'] is True), 'editable_old': sum(1 for row in editable if not protected(row, now))}


def watched(rows):
    return [{'path': row['path'].split('/', 1)[-1], 'name': row['name'], 'extension': row['extension'], 'read_only': row['read_only']} for row in rows if any(token in row['path'] for token in request.get('watch_paths', []))]


def run():
    now = time.time()
    rows = inventory()
    report['before'] = summary(rows, now)
    report['watched_before'] = watched(rows)
    blocked = any(row['read_only'] is True and row['extension'] == 'f2d' for row in rows if any(token in row['path'] for token in request.get('watch_paths', [])))
    report['blocked'] = blocked
    wanted = max(0, report['before']['editable'] - request['editable_target']) if 'editable_target' in request else request.get('slots', 2)
    needed = wanted if blocked or request.get('force') else 0
    report['needed'] = needed
    tried = set()
    while sum(1 for row in report['deleted'] if row['result'] is True) < needed:
        rows = inventory()
        candidates = sorted((row for row in rows if row['read_only'] is False and not protected(row, time.time()) and (row['path'], row['name']) not in tried), key=lambda row: row['modified'])
        if not candidates:
            report['stopped'] = 'no eligible editable document remains'
            break
        victim = candidates[0]
        tried.add((victim['path'], victim['name']))
        entry = {'name': victim['name'], 'extension': victim['extension'], 'age_hours': round((time.time() - victim['modified']) / 3600, 2)}
        try:
            entry['result'] = bool(victim['file'].deleteMe())
        except Exception as error:
            entry['result'] = 'refused'
            entry['message'] = str(error).splitlines()[0]
        report['deleted'].append(entry)
        common.save_json(target, report)
    rows = inventory()
    report['after'] = summary(rows, time.time())
    report['watched_after'] = watched(rows)


try:
    run()
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    report['documents_after'] = app.documents.count
    report['stage'] = 'finished'
    common.save_json(target, report)
