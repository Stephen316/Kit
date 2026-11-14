import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.modules.pop('LinkCommon', None)
import adsk.core
import adsk.fusion
from LinkCommon import acceptance_folder, private, pump, write

out = private / 'schema'
out.mkdir(parents=True, exist_ok=True)
app = adsk.core.Application.get()
report = {'fusion_version': app.version, 'documents_before': app.documents.count}
opened = []


def command(text):
    try:
        return app.executeTextCommand(text)
    except Exception:
        return 'error: ' + traceback.format_exc().splitlines()[-1]


def entities(label):
    raw = command('PAsset.EntityIds')
    rows = []
    try:
        identities = json.loads(raw)
    except Exception:
        return {'raw': raw}
    for identity in identities:
        entry = {'identity': identity}
        if identity.get('entityId', -1) >= 0:
            text = command('PEntity.Properties ' + str(identity['entityId']))
            try:
                entry['properties'] = json.loads(text)
            except Exception:
                entry['raw'] = text
        rows.append(entry)
    (out / (label + '.entities.json')).write_text(json.dumps(rows, indent=1) + '\n')
    return {'count': len(rows)}


try:
    project, folder = acceptance_folder(app, subfolder='Run1')
    names = ['KitLinkRoot', 'KitLinkSub']
    files = {}
    for index in range(folder.dataFiles.count):
        item = folder.dataFiles.item(index)
        if item.name in names:
            files[item.name] = item
    report['found'] = sorted(files)
    for name in names:
        doc = app.documents.open(files[name], True)
        opened.append(doc)
        pump(lambda: app.activeDocument is not None and app.activeDocument == doc, 60)
        report[name] = {
            'open_count': app.documents.count,
            'schema': command('Document.DumpAcitveDocSchema "' + str(out / (name + '.Schema.xml')) + '"'),
            'segment': command('Segment.Save "' + str(out / (name + '.Segment.xml')) + '"'),
            'entities': entities(name),
        }
        doc.close(False)
        opened.remove(doc)
        write(private / 'LinkSchema.json', report)
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
    raise
finally:
    for item in reversed(opened):
        try:
            if item.isValid:
                item.close(False)
        except Exception:
            report.setdefault('close_errors', []).append(traceback.format_exc())
    report['documents_after'] = app.documents.count
    write(private / 'LinkSchema.json', report)
