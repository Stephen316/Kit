# Create automatic drawings with orthogonal and isometric projected views under the ISO (first angle) and
# ASME (third angle) standards, from one existing saved design, and copy each new drawing from the local cache.
# The scripting API cannot place projected views, so the automatic mode is the only black-box source of them.
# The account is at its editable-document limit: the report records whether Fusion creates the file at all,
# whether it is read-only, and what it holds. Nothing is saved after creation.
# Request: $TMPDIR/KitFusionDrawings/Rules/CaptureAutoRules.request.json, for example
#   {"source": "KitDrw Wheel", "plans": ["AutoIsoA4", "AutoAsmeB"]}
# Report: $TMPDIR/KitFusionDrawings/Rules/CaptureAutoRules.json. Run it through Native/RunGuarded.mjs with
# --watch on that report and --stall 420.
import importlib
import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'Native'))
common = importlib.reload(importlib.import_module('DrawingCommon'))

import adsk.drawing

app = common.app
out = common.SCRATCH / 'Rules'
request = json.loads((out / 'CaptureAutoRules.request.json').read_text())
report = {'fusion_version': app.version, 'request': request, 'stage': 'starting', 'drawings': {}}
owned = []
Kinds = adsk.drawing

PLANS = {
    'AutoIsoA4': {'standard': Kinds.DrawingStandardTypes.ISODrawingStandardType, 'units': Kinds.DrawingUnitTypes.MillimeterDrawingUnitType, 'size': Kinds.SheetSizes.A4ISOSheetSize},
    'AutoIsoA2': {'standard': Kinds.DrawingStandardTypes.ISODrawingStandardType, 'units': Kinds.DrawingUnitTypes.MillimeterDrawingUnitType, 'size': Kinds.SheetSizes.A2ISOSheetSize},
    'AutoAsmeB': {'standard': Kinds.DrawingStandardTypes.ASMEDrawingStandardType, 'units': Kinds.DrawingUnitTypes.InchDrawingUnitType, 'size': Kinds.SheetSizes.BASMESheetSize},
    # Kit writes every drawing in millimetres, so this ASME control uses millimetre drawing units too.
    'AutoAsmeBmm': {'standard': Kinds.DrawingStandardTypes.ASMEDrawingStandardType, 'units': Kinds.DrawingUnitTypes.MillimeterDrawingUnitType, 'size': Kinds.SheetSizes.BASMESheetSize},
}


def checkpoint(stage):
    report['stage'] = stage
    common.save_json(out / 'CaptureAutoRules.json', report)


def find_file(name, extension):
    project, _created = common.ensure_project()
    pending = [project.rootFolder]
    while pending:
        folder = pending.pop()
        for index in range(folder.dataFiles.count):
            item = folder.dataFiles.item(index)
            if item.name == name and item.fileExtension == extension:
                return item
        pending.extend(folder.dataFolders.item(index) for index in range(folder.dataFolders.count))
    raise RuntimeError('File not found: ' + name + '.' + extension)


def sheet_rows(document):
    drawing = adsk.drawing.DrawingDocument.cast(document).drawing
    settings = drawing.documentSettings
    rows = []
    for index in range(drawing.sheets.count):
        sheet = drawing.sheets.item(index)
        views = [common.view_info(sheet.views.item(n)) for n in range(sheet.views.count)]
        for row in views:
            row['curves'] = row['curves'][:4]
        rows.append({'name': sheet.name, 'size': common.safe(lambda: int(sheet.sheetSize)), 'width': common.safe(lambda: sheet.width), 'height': common.safe(lambda: sheet.height), 'views': views})
    return {'standard': common.safe(lambda: int(settings.standard)), 'projection': common.safe(lambda: int(settings.projectionAngle)), 'sheets': rows}


def create(source_file, label, plan):
    row = report['drawings'].setdefault(label, {})
    manager = adsk.drawing.DrawingManager.get()
    entry = manager.createDrawingInput(source_file, adsk.drawing.DrawingCreationModes.AutomaticDrawingCreationMode)
    entry.standard = plan['standard']
    entry.units = plan['units']
    entry.sheetSize = plan['size']
    prefs = entry.automationPreferences
    glob = prefs.globalPreferences
    glob.isAutoDimensionEnabled = False
    glob.isAnimationSheetGenerated = False
    glob.isSubAssemblySheetGenerated = False
    component = prefs.componentPreferences.sheetViewPreferences
    component.isOrthogonalViewAdded = True
    component.isIsometricViewAdded = True
    started = time.time() - 2
    checkpoint('creating ' + label)
    drawing_file = manager.createDrawing(entry)
    if drawing_file is None:
        raise RuntimeError('createDrawing returned null')
    common.wait_until(lambda: drawing_file.isComplete, 300, label + ' completion')
    row['file'] = {'name': drawing_file.name, 'version': drawing_file.versionNumber, 'read_only': common.safe(lambda: drawing_file.isReadOnly)}
    document = None
    for index in range(app.documents.count):
        item = app.documents.item(index)
        if item.dataFile is not None and item.dataFile.name == drawing_file.name:
            document = item
    if document is None:
        checkpoint('opening drawing ' + label)
        document = app.documents.open(drawing_file, True)
    owned.append(document)
    time.sleep(3)
    common.capture_cache(label, started, report, tokens=(source_file.name,))
    checkpoint(label + ' captured')
    # Reading every view is slow, so it comes after the capture and only on request.
    if request.get('info'):
        row['info'] = sheet_rows(document)
        checkpoint(label + ' read')


def run():
    out.mkdir(parents=True, exist_ok=True)
    source_file = find_file(request['source'], 'f3d')
    report['source'] = {'name': source_file.name, 'version': source_file.versionNumber, 'read_only': common.safe(lambda: source_file.isReadOnly)}
    checkpoint('source found')
    for label in request['plans']:
        try:
            create(source_file, label, PLANS[label])
        except Exception:
            report['drawings'].setdefault(label, {})['error'] = traceback.format_exc()[-800:]
            checkpoint(label + ' failed')
        common.close_owned(owned, report)


try:
    run()
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    common.close_owned(owned, report)
    checkpoint(report['stage'])
