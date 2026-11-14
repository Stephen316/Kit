# Build Fusion-saved control drawings that the drawing rules were not fitted on.
# It makes one source design with a slanted edge and a hole, then saves drawings on ISO A4, ISO A2 and
# ASME B sheets with base views in several orientations, horizontal, vertical, aligned, radial and
# diameter dimensions, and a copied second sheet. Each saved version is copied from the local cache.
# Run it through re/Fusion/Reconstruction/Drawings/Native/RunGuarded.mjs or RunLocked.mjs.
import importlib
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'Native'))
common = importlib.reload(importlib.import_module('DrawingCommon'))

import adsk.core
import adsk.drawing
import adsk.fusion

app = common.app
report = {'fusion_version': app.version, 'documents_before': app.documents.count, 'stage': 'starting', 'drawings': {}}
owned = []
out = common.SCRATCH / 'Rules'
Orient = adsk.drawing.ViewOrientationTypes
Sizes = adsk.drawing.SheetSizes
Standards = adsk.drawing.DrawingStandardTypes
Units = adsk.drawing.DrawingUnitTypes

PLANS = [
    {
        'label': 'RuleA4',
        'size': Sizes.A4ISOSheetSize,
        'standard': Standards.ISODrawingStandardType,
        'units': Units.MillimeterDrawingUnitType,
        'views': [(Orient.FrontViewOrientationType, 7.0, 13.0, 1.0), (Orient.LeftViewOrientationType, 17.0, 13.0, 1.0), (Orient.IsoTopRightViewOrientationType, 22.0, 6.0, 1.0)],
        'dimensions': True,
        'copy_sheet': True,
    },
    {
        'label': 'RuleA2',
        'size': Sizes.A2ISOSheetSize,
        'standard': Standards.ISODrawingStandardType,
        'units': Units.MillimeterDrawingUnitType,
        'views': [(Orient.BackViewOrientationType, 15.0, 30.0, 2.0), (Orient.BottomViewOrientationType, 35.0, 30.0, 2.0), (Orient.IsoBottomLeftViewOrientationType, 30.0, 12.0, 2.0)],
        'dimensions': True,
        'copy_sheet': False,
    },
    {
        'label': 'RuleAsmeB',
        'size': Sizes.BASMESheetSize,
        'standard': Standards.ASMEDrawingStandardType,
        'units': Units.InchDrawingUnitType,
        'views': [(Orient.FrontViewOrientationType, 10.0, 18.0, 1.0), (Orient.TopViewOrientationType, 10.0, 8.0, 1.0), (Orient.RightViewOrientationType, 22.0, 18.0, 1.0)],
        'dimensions': True,
        'copy_sheet': False,
    },
]


def checkpoint(stage):
    report['stage'] = stage
    common.save_json(out / 'CaptureRules.json', report)


def build_source():
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    owned.append(doc)
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    root = design.rootComponent
    sketch = root.sketches.add(root.xYConstructionPlane)
    corners = [(0, 0), (5, 0), (5, 1.5), (3.5, 3), (0, 3)]
    points = [adsk.core.Point3D.create(x, y, 0) for x, y in corners]
    lines = sketch.sketchCurves.sketchLines
    for index in range(len(points)):
        lines.addByTwoPoints(points[index], points[(index + 1) % len(points)])
    sketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(1.5, 1.5, 0), 0.6)
    profile = max((sketch.profiles.item(index) for index in range(sketch.profiles.count)), key=lambda item: item.profileLoops.count)
    root.features.extrudeFeatures.addSimple(profile, adsk.core.ValueInput.createByString('12 mm'), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    body = root.bRepBodies.item(0)
    report['source'] = {'bodies': root.bRepBodies.count, 'faces': body.faces.count, 'edges': body.edges.count, 'volume_cm3': body.volume}
    return doc


def save_new(doc, name, folder, label):
    if not doc.saveAs(name, folder, 'Kit drawing rule control ' + label, ''):
        raise RuntimeError('saveAs did not start for ' + label)
    common.wait_until(lambda: doc.dataFile is not None and doc.dataFile.isComplete and not doc.isModified, 300, label + ' cloud save')
    return doc.dataFile


def save_version(doc, label):
    if not doc.save('Kit drawing rule control ' + label):
        raise RuntimeError('save did not start for ' + label)
    common.wait_until(lambda: doc.dataFile is not None and doc.dataFile.isComplete and not doc.isModified, 300, label + ' cloud save')
    return doc.dataFile.versionNumber


def point_of(curve, name):
    value = getattr(curve, name, None)
    return value if value is not None else None


def curves_of(view):
    return [view.viewCurves.item(index) for index in range(view.viewCurves.count)]


def straight(curve):
    return curve.startPoint is not None and curve.endPoint is not None and curve.centerPoint is None


def add_dimensions(sheet, view, row):
    made = row.setdefault('dimension_results', [])
    curves = curves_of(view)
    lines = [curve for curve in curves if straight(curve)]
    circles = [curve for curve in curves if curve.centerPoint is not None and curve.startPoint is None]
    arcs = [curve for curve in curves if curve.centerPoint is not None]

    def coords(point):
        value = point.coordinate
        return value.x, value.y

    def flat(curve):
        (x0, y0), (x1, y1) = coords(curve.startPoint), coords(curve.endPoint)
        return abs(y1 - y0) < 1e-6 and abs(x1 - x0) > 1e-6

    def tall(curve):
        (x0, y0), (x1, y1) = coords(curve.startPoint), coords(curve.endPoint)
        return abs(x1 - x0) < 1e-6 and abs(y1 - y0) > 1e-6

    def run(kind, action):
        try:
            result = action()
            made.append({'kind': kind, 'created': result is not None})
        except Exception:
            made.append({'kind': kind, 'error': traceback.format_exc()[-600:]})

    horizontal = max((c for c in lines if flat(c)), key=lambda c: abs(coords(c.endPoint)[0] - coords(c.startPoint)[0]), default=None)
    vertical = max((c for c in lines if tall(c)), key=lambda c: abs(coords(c.endPoint)[1] - coords(c.startPoint)[1]), default=None)
    slanted = [c for c in lines if not flat(c) and not tall(c)]
    if horizontal is not None:
        (x0, y0), (x1, y1) = coords(horizontal.startPoint), coords(horizontal.endPoint)
        place = adsk.drawing.DrawingPoint.create(adsk.core.Point2D.create((x0 + x1) / 2, max(y0, y1) + 1.2))
        run('horizontal', lambda: sheet.drawingDimensions.addLinearDimension(horizontal.startPoint, horizontal.endPoint, place, False))
    if vertical is not None:
        (x0, y0), (x1, y1) = coords(vertical.startPoint), coords(vertical.endPoint)
        place = adsk.drawing.DrawingPoint.create(adsk.core.Point2D.create(max(x0, x1) + 1.2, (y0 + y1) / 2))
        run('vertical', lambda: sheet.drawingDimensions.addLinearDimension(vertical.startPoint, vertical.endPoint, place, False))
    if slanted:
        edge = slanted[0]
        (x0, y0), (x1, y1) = coords(edge.startPoint), coords(edge.endPoint)
        place = adsk.drawing.DrawingPoint.create(adsk.core.Point2D.create((x0 + x1) / 2 + 0.8, (y0 + y1) / 2 + 0.8))
        run('aligned', lambda: sheet.drawingDimensions.addLinearDimension(edge.startPoint, edge.endPoint, place, True))
    round_curves = circles or arcs
    if round_curves:
        circle = round_curves[0]
        cx, cy = coords(circle.centerPoint)
        run('radial', lambda: sheet.drawingDimensions.addRadialDimension(circle, adsk.drawing.DrawingPoint.create(adsk.core.Point2D.create(cx + 1.5, cy + 1.0))))
        run('diameter', lambda: sheet.drawingDimensions.addDiameterDimension(circle, adsk.drawing.DrawingPoint.create(adsk.core.Point2D.create(cx - 1.5, cy - 1.2))))
    row['curve_kinds'] = {'lines': len(lines), 'circles': len(circles), 'arcs': len(arcs), 'slanted': len(slanted)}


def sheets_info(document):
    drawing = adsk.drawing.DrawingDocument.cast(document).drawing
    rows = []
    sheets = common.safe(lambda: drawing.sheets, None)
    count = common.safe(lambda: sheets.count, 0) if sheets is not None and not isinstance(sheets, dict) else 0
    for index in range(count):
        sheet = sheets.item(index)
        dims = []
        for number in range(sheet.drawingDimensions.count):
            item = sheet.drawingDimensions.item(number)
            dims.append({'type': common.safe(lambda: item.objectType), 'value': common.safe(lambda: item.value), 'text': common.safe(lambda: item.text)})
        rows.append({'name': sheet.name, 'size': common.safe(lambda: int(sheet.sheetSize)), 'width': common.safe(lambda: sheet.width), 'height': common.safe(lambda: sheet.height), 'views': [common.view_info(sheet.views.item(n)) for n in range(sheet.views.count)], 'dimensions': dims})
    return {'sheet_count': count, 'sheets': rows}


def make_drawing(plan, source_file, started):
    row = report['drawings'].setdefault(plan['label'], {})
    manager = adsk.drawing.DrawingManager.get()
    entry = manager.createDrawingInput(source_file, adsk.drawing.DrawingCreationModes.ManualDrawingCreationMode)
    entry.standard = plan['standard']
    entry.units = plan['units']
    entry.sheetSize = plan['size']
    checkpoint('creating ' + plan['label'])
    drawing_file = manager.createDrawing(entry)
    if drawing_file is None:
        raise RuntimeError('createDrawing returned null')
    common.wait_until(lambda: drawing_file.isComplete, 300, plan['label'] + ' drawing completion')
    row['drawing_name'] = drawing_file.name
    document = None
    for index in range(app.documents.count):
        item = app.documents.item(index)
        if item.dataFile is not None and item.dataFile.name == drawing_file.name:
            document = item
    if document is None:
        document = app.documents.open(drawing_file, True)
    owned.append(document)
    drawing = adsk.drawing.DrawingDocument.cast(document).drawing
    sheet = drawing.activeSheet
    views = []
    for orientation, x_cm, y_cm, scale in plan['views']:
        try:
            entry = sheet.views.createBaseViewInput()
            entry.placementPoint = adsk.drawing.DrawingPoint.create(adsk.core.Point2D.create(x_cm, y_cm))
            entry.viewParameters.orientation = orientation
            entry.viewParameters.scaleValue = scale
            view = sheet.views.add(entry)
            views.append(view)
            row.setdefault('view_results', []).append({'orientation': int(orientation), 'created': view is not None})
        except Exception:
            row.setdefault('view_results', []).append({'orientation': int(orientation), 'error': traceback.format_exc()[-600:]})
    checkpoint(plan['label'] + ' views added')
    if plan['dimensions'] and views and views[0] is not None:
        add_dimensions(sheet, views[0], row)
    checkpoint(plan['label'] + ' dimensions added')
    if plan['copy_sheet']:
        try:
            copied = sheet.copy('Kit Copied Sheet', False)
            row['copied_sheet'] = copied is not None
            if copied is None:
                common.wait_until(lambda: drawing.sheets.count > 1, 120, 'copied sheet')
                row['copied_sheet_late'] = drawing.sheets.count
        except Exception:
            row['copy_error'] = traceback.format_exc()[-600:]
    row['version'] = save_version(document, plan['label'])
    row['info'] = sheets_info(document)
    common.capture_cache(plan['label'], started, report)
    checkpoint(plan['label'] + ' captured')


def run():
    out.mkdir(parents=True, exist_ok=True)
    started = time.time() - 2
    project, created = common.ensure_project()
    report['project_created'] = created
    stamp = time.strftime('%Y%m%d%H%M%S')
    folder = project.rootFolder.dataFolders.add('Rules ' + stamp)
    if folder is None:
        raise RuntimeError('Folder creation failed')
    report['folder_name'] = 'Rules ' + stamp
    source = build_source()
    checkpoint('source_built')
    source_file = save_new(source, common.TOKEN + ' Rule Source ' + stamp, folder, 'source')
    report['source']['name'] = source_file.name
    checkpoint('source_saved')
    wanted = [item for item in sys.argv[1:] if item.startswith('Rule')]
    for plan in PLANS:
        if wanted and plan['label'] not in wanted:
            continue
        try:
            make_drawing(plan, source_file, started)
        except Exception:
            report['drawings'].setdefault(plan['label'], {})['error'] = traceback.format_exc()
            checkpoint(plan['label'] + ' failed')
        common.close_owned(owned[1:], report)
        del owned[1:]


try:
    run()
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    common.close_owned(owned, report)
    checkpoint(report['stage'])
