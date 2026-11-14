import importlib
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
store = common.state()
report = {'fusion_version': app.version, 'documents_before': app.documents.count, 'stage': 'starting'}
owned = []
out = common.SCRATCH / 'Auto'


def checkpoint(stage):
    report['stage'] = stage
    common.save_json(out / 'CaptureAuto.json', report)


def save_version(doc, label):
    if not doc.save('Kit drawing control ' + label):
        raise RuntimeError('save did not start for ' + label)
    common.wait_until(lambda: doc.dataFile is not None and doc.dataFile.isComplete and not doc.isModified, 300, label + ' cloud save')
    return doc.dataFile.versionNumber


def existing(name):
    folder = store.get('folder')
    if folder is None:
        return None
    files = folder.dataFiles
    for index in range(files.count):
        if files.item(index).name == name:
            return files.item(index)
    return None


def create(source_file, label, autodim, reuse=None):
    if reuse is not None:
        started = time.time() - 2
        document = app.documents.open(reuse, True)
        owned.append(document)
        report[label + '_file'] = {'name': reuse.name, 'extension': reuse.fileExtension, 'version': reuse.versionNumber, 'reused': True}
        report[label] = common.drawing_info(document)
        common.capture_cache(label, started, report)
        return document, reuse, started
    manager = adsk.drawing.DrawingManager.get()
    entry = manager.createDrawingInput(source_file, adsk.drawing.DrawingCreationModes.AutomaticDrawingCreationMode)
    entry.standard = adsk.drawing.DrawingStandardTypes.ISODrawingStandardType
    entry.units = adsk.drawing.DrawingUnitTypes.MillimeterDrawingUnitType
    entry.sheetSize = adsk.drawing.SheetSizes.A3ISOSheetSize
    prefs = entry.automationPreferences
    glob = prefs.globalPreferences
    glob.isAutoDimensionEnabled = autodim
    glob.isAnimationSheetGenerated = False
    glob.isSubAssemblySheetGenerated = False
    component = prefs.componentPreferences.sheetViewPreferences
    component.isOrthogonalViewAdded = True
    component.isIsometricViewAdded = False
    report[label + '_prefs'] = {'main': glob.isMainAssemblySheetGenerated, 'component': glob.isComponentSheetGenerated, 'autodim': glob.isAutoDimensionEnabled}
    started = time.time() - 2
    drawing_file = manager.createDrawing(entry)
    if drawing_file is None:
        raise RuntimeError('createDrawing returned null for ' + label)
    common.wait_until(lambda: drawing_file.isComplete, 300, label + ' completion')
    report[label + '_file'] = {'name': drawing_file.name, 'extension': drawing_file.fileExtension, 'version': drawing_file.versionNumber}
    report[label + '_open_documents'] = [app.documents.item(index).name for index in range(app.documents.count)]
    document = None
    for index in range(app.documents.count):
        item = app.documents.item(index)
        if item.dataFile is not None and item.dataFile.name == drawing_file.name:
            document = item
    if document is None:
        document = app.documents.open(drawing_file, True)
    owned.append(document)
    report[label] = common.drawing_info(document)
    common.capture_cache(label, started, report)
    return document, drawing_file, started


def run():
    out.mkdir(parents=True, exist_ok=True)
    source_file = store.get('source_file')
    if source_file is None or not source_file.isValid:
        raise RuntimeError('Source data file unavailable in session state')
    report['source'] = {'name': source_file.name, 'version': source_file.versionNumber}
    document, drawing_file, started = create(source_file, 'A0Views', False, existing(source_file.name + ' Drawing'))
    store['auto_drawing_file'] = drawing_file
    checkpoint('captured_views')
    drawing = adsk.drawing.DrawingDocument.cast(document).drawing
    sheet = drawing.activeSheet
    view = sheet.views.item(0)
    curves = [view.viewCurves.item(index) for index in range(view.viewCurves.count)]
    straight = [curve for curve in curves if curve.startPoint is not None and curve.endPoint is not None and curve.centerPoint is None]
    longest = max(straight, key=lambda curve: abs(curve.endPoint.coordinate.x - curve.startPoint.coordinate.x) + abs(curve.endPoint.coordinate.y - curve.startPoint.coordinate.y))
    start, end = longest.startPoint.coordinate, longest.endPoint.coordinate
    place = adsk.drawing.DrawingPoint.create(adsk.core.Point2D.create((start.x + end.x) / 2, max(start.y, end.y) + 1.5))
    dimension = sheet.drawingDimensions.addLinearDimension(longest.startPoint, longest.endPoint, place, False)
    if dimension is None:
        raise RuntimeError('Linear dimension creation failed')
    report['dimension_curve'] = {'start': [start.x, start.y], 'end': [end.x, end.y]}
    report['A1Dimension_version'] = save_version(document, 'linear dimension')
    report['A1Dimension'] = common.drawing_info(document)
    common.capture_cache('A1Dimension', started, report)
    checkpoint('captured_dimension')
    common.close_owned(owned, report)
    create(source_file, 'A2AutoDim', True)
    checkpoint('captured_autodim')


try:
    run()
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    common.close_owned(owned, report)
    checkpoint(report['stage'])
