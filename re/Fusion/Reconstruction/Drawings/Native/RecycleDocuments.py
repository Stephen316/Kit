import collections
import importlib
import json
import re
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
common = importlib.reload(importlib.import_module('DrawingCommon'))

import adsk.core

app = common.app
variants = common.SCRATCH / 'Variants'
request = json.loads((variants / 'Recycle.json').read_text())
target = variants / ('Recycle' + request['tag'] + '.json')
report = {'fusion_version': app.version, 'documents_before': app.documents.count, 'stage': 'starting', 'tag': request['tag']}
PROTECTED = ('KitLink', 'KitCfg')


def scrub(text):
    return re.sub(r'urn:\S+|[0-9a-fA-F-]{20,}', '<id>', text)[:160]


def walk(folder, path, rows, failures):
    try:
        count = folder.dataFiles.count
    except Exception as error:
        failures['folder files'] += 1
        report.setdefault('list_errors', []).append(scrub(str(error).splitlines()[0]))
        count = 0
    for index in range(count):
        try:
            item = folder.dataFiles.item(index)
            rows.append({'file': item, 'path': path, 'name': item.name, 'extension': item.fileExtension, 'read_only': common.safe(lambda: item.isReadOnly)})
        except Exception as error:
            failures['file'] += 1
            report.setdefault('list_errors', []).append(scrub(str(error).splitlines()[0]))
    for index in range(folder.dataFolders.count):
        child = folder.dataFolders.item(index)
        walk(child, path + '/' + child.name, rows, failures)


def inventory():
    project, _ = common.ensure_project()
    rows = []
    failures = collections.Counter()
    walk(project.rootFolder, '', rows, failures)
    return rows, failures


def counts(rows):
    mine = [row for row in rows if row['name'].startswith(common.TOKEN)]
    return {
        'files': len(rows),
        'editable': sum(1 for row in rows if row['read_only'] is False),
        'read_only': sum(1 for row in rows if row['read_only'] is True),
        'kitdrw_files': len(mine),
        'kitdrw_editable': sum(1 for row in mine if row['read_only'] is False),
    }


def eligible(row, open_names):
    if not row['name'].startswith(common.TOKEN) or any(token in row['name'] for token in PROTECTED):
        return False
    if row['name'] in open_names:
        return False
    keep = request.get('keep_folders', [])
    return not any(('/' + token) in row['path'] for token in keep)


def run():
    rows, failures = inventory()
    report['before'] = counts(rows)
    report['list_failures_before'] = dict(failures)
    open_names = {app.documents.item(index).name for index in range(app.documents.count)}
    victims = [row for row in rows if eligible(row, open_names)]
    victims.sort(key=lambda row: (row['extension'] != 'f2d', row['path'], row['name']))
    deleted = collections.Counter()
    refused = collections.Counter()
    messages = collections.Counter()
    for row in victims:
        label = row['name'] + '.' + row['extension']
        try:
            if row['file'].deleteMe():
                deleted[label] += 1
            else:
                refused[label] += 1
                messages['returned false'] += 1
        except Exception as error:
            refused[label] += 1
            messages[scrub(str(error).splitlines()[0])] += 1
        report['deleted'] = dict(deleted)
        report['refused'] = dict(refused)
        common.save_json(target, report)
    report['refusal_messages'] = dict(messages)
    report['deleted_count'] = sum(deleted.values())
    report['refused_count'] = sum(refused.values())
    rows, failures = inventory()
    report['after'] = counts(rows)
    report['list_failures_after'] = dict(failures)


try:
    run()
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = scrub(traceback.format_exc())
finally:
    report['documents_after'] = app.documents.count
    report['stage'] = 'finished'
    common.save_json(target, report)
