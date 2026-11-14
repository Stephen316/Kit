import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.modules.pop('LinkCommon', None)
import adsk.core
from LinkCommon import acceptance_folder, private, pump, write

app = adsk.core.Application.get()
report = {'fusion_version': app.version, 'documents_before': app.documents.count, 'steps': []}
opened = []


def latest(folder, name):
    for index in range(folder.dataFiles.count):
        item = folder.dataFiles.item(index)
        if item.name == name:
            return item
    return None


def note(stage, **values):
    report['steps'].append({'stage': stage, **values})
    write(private / 'ProbeLinkSave.json', report)


def safe(call):
    try:
        return call()
    except Exception:
        return {'error': traceback.format_exc().splitlines()[-1]}


try:
    project, folder = acceptance_folder(app, subfolder='Accept2')
    data_file = latest(folder, 'KitLinkMovedR1')
    note('found', version=data_file.versionNumber, read_only=safe(lambda: data_file.isReadOnly))
    doc = app.documents.open(data_file, True)
    opened.append(doc)
    note('opened', modified=doc.isModified, saved=doc.isSaved, documents=app.documents.count)
    result = doc.updateAllReferences()
    pump(lambda: not any(doc.documentReferences.item(i).isOutOfDate for i in range(doc.documentReferences.count)), 180)
    note('updated', result=result, modified=doc.isModified, versions=[doc.documentReferences.item(i).version for i in range(doc.documentReferences.count)])
    saved = safe(lambda: doc.save('Kit link save probe'))
    note('save_called', result=saved, modified=doc.isModified, local_version=safe(lambda: doc.dataFile.versionNumber))
    grew = pump(lambda: (latest(folder, 'KitLinkMovedR1') or data_file).versionNumber >= 2, 420)
    note('after_wait', grew=grew, cloud_version=latest(folder, 'KitLinkMovedR1').versionNumber, modified=doc.isModified, saved=doc.isSaved)
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    for item in reversed(opened):
        try:
            if item.isValid:
                item.close(False)
        except Exception:
            report.setdefault('close_errors', []).append(traceback.format_exc())
    report['documents_after'] = app.documents.count
    write(private / 'ProbeLinkSave.json', report)
