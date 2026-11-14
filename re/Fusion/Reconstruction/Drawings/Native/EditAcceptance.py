import importlib
import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
common = importlib.reload(importlib.import_module('DrawingCommon'))

import adsk.core
import adsk.drawing
import adsk.fusion

app = common.app
variants = common.SCRATCH / 'Variants'
request = json.loads((variants / 'Edit.json').read_text())
target = variants / ('Edit' + request['label'] + '.json')
report = {'fusion_version': app.version, 'documents_before': app.documents.count, 'label': request['label'], 'stage': 'starting'}
owned = []


def checkpoint(stage):
    report['stage'] = stage
    common.save_json(target, report)


def settle(seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        adsk.doEvents()


def references(document):
    collection = document.documentReferences
    return [{'name': common.safe(lambda: collection.item(index).dataFile.name), 'version': common.safe(lambda: collection.item(index).version), 'out_of_date': common.safe(lambda: collection.item(index).isOutOfDate)} for index in range(collection.count)]


def files():
    project, _ = common.ensure_project()
    folders = project.rootFolder.dataFolders
    parent = next(folders.item(index) for index in range(folders.count) if folders.item(index).name == request['folder'])
    child = next(parent.dataFolders.item(index) for index in range(parent.dataFolders.count) if parent.dataFolders.item(index).name == common.TOKEN + ' ' + request['label'])
    rows = [child.dataFiles.item(index) for index in range(child.dataFiles.count)]
    report.setdefault('read_only', []).append({item.fileExtension: common.safe(lambda: item.isReadOnly) for item in rows})
    return next(item for item in rows if item.fileExtension == 'f3d'), next(item for item in rows if item.fileExtension == 'f2d')


def saved(document, comment, label):
    before = common.safe(lambda: document.dataFile.versionNumber)
    report.setdefault('save_requests', []).append({'label': label, 'modified': document.isModified, 'version_before': before, 'active': app.activeDocument == document})
    if not document.save(comment):
        raise RuntimeError('save did not start for ' + label)
    deadline = time.monotonic() + request.get('save_seconds', 300)
    while time.monotonic() < deadline:
        settle(1)
        if not document.isModified and document.dataFile is not None and document.dataFile.isComplete and document.dataFile.versionNumber != before:
            return document.dataFile.versionNumber
    raise RuntimeError('Timed out waiting for ' + label + ' cloud save')


def edit_design(design_file):
    document = app.documents.open(design_file, True)
    owned.append(document)
    settle(4)
    design = adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))
    parameter = design.userParameters.itemByName('kitWidth')
    body = design.rootComponent.bRepBodies.item(0)
    report['design_before'] = {'version': design_file.versionNumber, 'expression': parameter.expression, 'volume_cm3': body.volume}
    parameter.expression = request['expression']
    settle(2)
    report['design_after'] = {'expression': parameter.expression, 'volume_cm3': design.rootComponent.bRepBodies.item(0).volume}
    report['design_after']['version'] = saved(document, 'Kit drawing edit ' + request['expression'], 'design')
    return document


def run():
    design_file, drawing_file = files()
    if request.get('require_editable') and any(value is not False for value in report['read_only'][0].values()):
        raise RuntimeError('Uploaded files are read-only, so the edit was not attempted')
    if request.get('expression'):
        checkpoint('editing design')
        edit_design(design_file)
    else:
        owned.append(app.documents.open(design_file, True))
        settle(4)
    checkpoint('opening drawing')
    drawing_doc = adsk.drawing.DrawingDocument.cast(app.documents.open(drawing_file, True))
    owned.append(drawing_doc)
    settle(10)
    report['drawing_before'] = common.drawing_info(drawing_doc)
    report['references_before'] = references(drawing_doc)
    checkpoint('updating references')
    report['update_result'] = drawing_doc.updateAllReferences()
    settle(request.get('update_seconds', 15))
    drawing_doc.activate()
    settle(2)
    report['drawing_after'] = common.drawing_info(drawing_doc)
    report['references_after'] = references(drawing_doc)
    if report['read_only'][0].get('f2d') is True:
        raise RuntimeError('Drawing file is read-only, so the save was not attempted')
    started = time.time() - 2
    checkpoint('saving drawing')
    report['drawing_version'] = saved(drawing_doc, 'Kit drawing after reference update', 'drawing')
    report['captures_saved'] = common.capture_cache('E' + request['label'], started, report, ('_' + drawing_file.name + '.',))
    common.close_owned(owned, report)
    checkpoint('reopening')
    design_file, drawing_file = files()
    owned.append(app.documents.open(design_file, True))
    settle(4)
    reopened = app.documents.open(drawing_file, True)
    owned.append(reopened)
    settle(10)
    report['reopened'] = {'version': drawing_file.versionNumber, 'drawing': common.drawing_info(reopened), 'references': references(reopened), 'modified': reopened.isModified}


try:
    run()
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    common.close_owned(owned, report)
    checkpoint('finished')
