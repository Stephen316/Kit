# Count editable and read-only cloud documents per project and list the open documents.
# The report goes to $TMPDIR/KitFusionDrawings/Rules/ProbeCapacity.json and stays out of the repository.
import importlib
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'Native'))
common = importlib.reload(importlib.import_module('DrawingCommon'))

app = common.app
out = common.SCRATCH / 'Rules'
report = {'fusion_version': app.version, 'stage': 'starting', 'projects': []}


def walk(folder, rows, depth=0):
    for index in range(folder.dataFiles.count):
        item = folder.dataFiles.item(index)
        rows.append({'name': item.name, 'extension': item.fileExtension, 'modified': item.dateModified, 'read_only': common.safe(lambda: item.isReadOnly)})
    if depth < 6:
        for index in range(folder.dataFolders.count):
            walk(folder.dataFolders.item(index), rows, depth + 1)


try:
    hub = app.data.activeHub
    now = time.time()
    for index in range(hub.dataProjects.count):
        project = hub.dataProjects.item(index)
        rows = []
        walk(project.rootFolder, rows)
        editable = [row for row in rows if row['read_only'] is False]
        report['projects'].append({
            'name': project.name,
            'files': len(rows),
            'editable': len(editable),
            'editable_older_7_days': sum(1 for row in editable if now - row['modified'] > 7 * 86400),
            'oldest_days': round(max((now - row['modified'] for row in rows), default=0) / 86400, 2),
            'editable_names': sorted(row['name'] + '.' + row['extension'] for row in editable)[:40],
        })
    report['open_documents'] = [app.documents.item(index).name for index in range(app.documents.count)]
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    common.save_json(out / 'ProbeCapacity.json', report)
