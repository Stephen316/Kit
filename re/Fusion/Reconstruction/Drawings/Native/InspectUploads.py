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

app = common.app
variants = common.SCRATCH / 'Variants'
target = variants / ('Inspect' + json.loads((variants / 'Selection.json').read_text()).get('tag', 'Uploads') + '.json')
report = {'fusion_version': app.version, 'documents_before': app.documents.count, 'uploads': {}, 'stage': 'starting'}
owned = []


def checkpoint(stage):
    report['stage'] = stage
    common.save_json(target, report)


def settle(seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        adsk.doEvents()


def poke(document):
    sheet = adsk.drawing.DrawingDocument.cast(document).drawing.activeSheet
    rows = []
    for index in range(sheet.views.count):
        view = sheet.views.item(index)
        scale = common.safe(lambda: view.scaleValue)
        step = {'before': view.viewCurves.count, 'scale': scale}
        step['set_half'] = common.safe(lambda: setattr(view, 'scaleValue', scale / 2) or True)
        settle(3)
        step['half'] = common.safe(lambda: view.viewCurves.count)
        step['set_back'] = common.safe(lambda: setattr(view, 'scaleValue', scale) or True)
        settle(3)
        step['after'] = common.safe(lambda: view.viewCurves.count)
        rows.append(step)
    return {'views': rows, 'info': common.drawing_info(document)}


def references(document):
    rows = []
    collection = common.safe(lambda: document.documentReferences, False)
    if not collection:
        return rows
    for index in range(collection.count):
        item = collection.item(index)
        rows.append({
            'name': common.safe(lambda: item.dataFile.name),
            'version': common.safe(lambda: item.version),
            'latest': common.safe(lambda: item.dataFile.latestVersionNumber),
            'out_of_date': common.safe(lambda: item.isOutOfDate),
        })
    return rows


def iterate(collection):
    return [collection.item(index) for index in range(collection.count)]


def export_dwg(document, label):
    folder = common.SCRATCH / 'Exports'
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (label + '.dwg')
    if path.exists():
        path.unlink()
    manager = adsk.drawing.DrawingDocument.cast(document).drawing.exportManager
    options = manager.createDWGExportOptions(str(path))
    options.format = adsk.drawing.DWGFormats.AutoCADDWGFormat
    started = time.monotonic()
    result = manager.execute(options)
    return {'result': result, 'seconds': round(time.monotonic() - started, 1), 'bytes': path.stat().st_size if path.exists() else 0, 'sha256': common.digest(path) if path.exists() else None}


def upload_folder(selection):
    begun = {'folder': selection['folder']} if 'folder' in selection else json.loads((variants / 'BeginUploads.json').read_text())
    report['folder'] = begun['folder']
    project, _ = common.ensure_project()
    folders = project.rootFolder.dataFolders
    for index in range(folders.count):
        if folders.item(index).name == begun['folder']:
            return folders.item(index)
    raise RuntimeError('Upload folder is unavailable')


def inspect(label, folder):
    files = [folder.dataFiles.item(index) for index in range(folder.dataFiles.count)]
    row = {'files': [{'name': item.name, 'extension': item.fileExtension, 'version': item.versionNumber, 'complete': item.isComplete} for item in files]}
    drawings = [item for item in files if item.fileExtension == 'f2d']
    designs = [item for item in files if item.fileExtension == 'f3d']
    if not drawings or not all(item.isComplete for item in files):
        row['ready'] = False
        return row
    row['ready'] = True
    started = time.time() - 2
    for design in designs:
        checkpoint(label + ' opening design')
        owned.append(app.documents.open(design, True))
        settle(4)
    checkpoint(label + ' opening drawing')
    opened_at = time.monotonic()
    try:
        document = app.documents.open(drawings[0], True)
    except Exception:
        row['open_error'] = traceback.format_exc().splitlines()[-1]
        row['open_seconds'] = round(time.monotonic() - opened_at, 1)
        return row
    row['open_seconds'] = round(time.monotonic() - opened_at, 1)
    owned.append(document)
    settle(10)
    row['opened'] = common.safe(lambda: common.drawing_info(document))
    row['dimension_types'] = common.safe(lambda: [int(sheet_dimension.type) for sheet_dimension in iterate(adsk.drawing.DrawingDocument.cast(document).drawing.activeSheet.drawingDimensions)])
    row['references'] = references(document)
    row['modified_after_open'] = common.safe(lambda: document.isModified)
    if selection.get('poke'):
        checkpoint(label + ' poking views')
        row['poked'] = common.safe(lambda: poke(document))
    if row['open_seconds'] > selection.get('slow_open_seconds', 480):
        row['slow_open'] = True
    elif selection.get('export_dwg'):
        checkpoint(label + ' exporting dwg')
        row['export'] = common.safe(lambda: export_dwg(document, label))
    row['captures'] = common.capture_cache('U' + label, started, report, ('_' + drawings[0].name + '.',))
    common.close_owned(owned, report)
    return row


try:
    selection = json.loads((variants / 'Selection.json').read_text())
    wanted = selection['labels']
    parent = upload_folder(selection)
    children = {parent.dataFolders.item(index).name.removeprefix(common.TOKEN + ' '): parent.dataFolders.item(index) for index in range(parent.dataFolders.count)}
    for label in wanted:
        if label not in children:
            report['uploads'][label] = {'missing_folder': True}
            continue
        report['uploads'][label] = common.safe(lambda: inspect(label, children[label]))
        checkpoint(label + ' inspected')
        if isinstance(report['uploads'][label], dict) and report['uploads'][label].get('slow_open'):
            report['stopped_after'] = label
            break
    report['status'] = 'inspected'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    common.close_owned(owned, report)
    checkpoint('finished')
