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
out = common.SCRATCH / 'Manual'


def checkpoint(stage):
    report['stage'] = stage
    common.save_json(out / 'CaptureManual.json', report)


def build_source():
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    owned.append(doc)
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    root = design.rootComponent
    params = design.userParameters
    params.add('kitWidth', adsk.core.ValueInput.createByString('40 mm'), 'mm', 'Plate width')
    params.add('kitDepth', adsk.core.ValueInput.createByString('20 mm'), 'mm', 'Plate depth')
    sketch = root.sketches.add(root.xYConstructionPlane)
    lines = sketch.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(4, 2, 0))
    sketch.geometricConstraints.addCoincident(lines.item(0).startSketchPoint, sketch.originPoint)
    dims = sketch.sketchDimensions
    width = dims.addDistanceDimension(lines.item(0).startSketchPoint, lines.item(0).endSketchPoint, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.core.Point3D.create(2, -0.6, 0))
    width.parameter.expression = 'kitWidth'
    depth = dims.addDistanceDimension(lines.item(1).startSketchPoint, lines.item(1).endSketchPoint, adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, adsk.core.Point3D.create(4.6, 1, 0))
    depth.parameter.expression = 'kitDepth'
    sketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(1, 1, 0), 0.4)
    profile = max((sketch.profiles.item(index) for index in range(sketch.profiles.count)), key=lambda item: item.profileLoops.count)
    root.features.extrudeFeatures.addSimple(profile, adsk.core.ValueInput.createByString('10 mm'), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    report['source'] = {'bodies': root.bRepBodies.count, 'faces': root.bRepBodies.item(0).faces.count, 'edges': root.bRepBodies.item(0).edges.count, 'volume_cm3': root.bRepBodies.item(0).volume}
    path = out / 'Source.f3d'
    options = design.exportManager.createFusionArchiveExportOptions(str(path), root)
    if not design.exportManager.execute(options):
        raise RuntimeError('Source archive export failed')
    report['source']['archive'] = {'bytes': path.stat().st_size, 'sha256': common.digest(path)}
    return doc


def save_new(doc, name, folder, label):
    if not doc.saveAs(name, folder, 'Kit drawing control ' + label, ''):
        raise RuntimeError('saveAs did not start for ' + label)
    common.wait_until(lambda: doc.dataFile is not None and doc.dataFile.isComplete and not doc.isModified, 240, label + ' cloud save')
    return doc.dataFile


def save_version(doc, label):
    if not doc.save('Kit drawing control ' + label):
        raise RuntimeError('save did not start for ' + label)
    common.wait_until(lambda: doc.dataFile is not None and doc.dataFile.isComplete and not doc.isModified, 240, label + ' cloud save')
    return doc.dataFile.versionNumber


def run():
    out.mkdir(parents=True, exist_ok=True)
    started = time.time() - 2
    project, created = common.ensure_project()
    report['project_created'] = created
    stamp = time.strftime('%Y%m%d%H%M%S')
    folder = project.rootFolder.dataFolders.add('Drawings ' + stamp)
    if folder is None:
        raise RuntimeError('Folder creation failed')
    store['folder'] = folder
    report['folder_name'] = 'Drawings ' + stamp
    checkpoint('folder_created')
    source = build_source()
    checkpoint('source_built')
    source_file = save_new(source, common.TOKEN + ' Source ' + stamp, folder, 'source')
    store['source_file'] = source_file
    report['source']['version'] = source_file.versionNumber
    report['source']['name'] = source_file.name
    checkpoint('source_saved')
    manager = adsk.drawing.DrawingManager.get()
    entry = manager.createDrawingInput(source_file, adsk.drawing.DrawingCreationModes.ManualDrawingCreationMode)
    entry.standard = adsk.drawing.DrawingStandardTypes.ISODrawingStandardType
    entry.units = adsk.drawing.DrawingUnitTypes.MillimeterDrawingUnitType
    entry.sheetSize = adsk.drawing.SheetSizes.A3ISOSheetSize
    checkpoint('creating_drawing')
    drawing_file = manager.createDrawing(entry)
    if drawing_file is None:
        raise RuntimeError('createDrawing returned null')
    store['manual_drawing_file'] = drawing_file
    report['drawing_file'] = {'name': drawing_file.name, 'extension': drawing_file.fileExtension, 'version': drawing_file.versionNumber}
    report['documents_after_create'] = [app.documents.item(index).name for index in range(app.documents.count)]
    checkpoint('drawing_created')
    common.wait_until(lambda: drawing_file.isComplete, 240, 'drawing cloud completion')
    drawing_doc = None
    for index in range(app.documents.count):
        item = app.documents.item(index)
        if item.dataFile is not None and item.dataFile.name == drawing_file.name:
            drawing_doc = item
    if drawing_doc is None:
        drawing_doc = app.documents.open(drawing_file, True)
    owned.append(drawing_doc)
    report['drawing_doc_type'] = drawing_doc.objectType
    report['V0Empty'] = common.drawing_info(drawing_doc)
    common.capture_cache('V0Empty', started, report)
    checkpoint('captured_empty')
    drawing = adsk.drawing.DrawingDocument.cast(drawing_doc).drawing
    sheet = drawing.activeSheet
    entry = sheet.views.createBaseViewInput()
    entry.placementPoint = adsk.drawing.DrawingPoint.create(adsk.core.Point2D.create(12, 18))
    entry.viewParameters.orientation = adsk.drawing.ViewOrientationTypes.FrontViewOrientationType
    entry.viewParameters.scaleValue = 1.0
    view = sheet.views.add(entry)
    if view is None:
        raise RuntimeError('Base view creation failed')
    report['V1Base_version'] = save_version(drawing_doc, 'base view')
    report['V1Base'] = common.drawing_info(drawing_doc)
    common.capture_cache('V1Base', started, report)
    checkpoint('captured_base')
    curves = [view.viewCurves.item(index) for index in range(view.viewCurves.count)]
    straight = [curve for curve in curves if curve.startPoint is not None and curve.endPoint is not None and curve.centerPoint is None]
    longest = max(straight, key=lambda curve: abs(curve.endPoint.coordinate.x - curve.startPoint.coordinate.x) + abs(curve.endPoint.coordinate.y - curve.startPoint.coordinate.y))
    start, end = longest.startPoint.coordinate, longest.endPoint.coordinate
    place = adsk.drawing.DrawingPoint.create(adsk.core.Point2D.create((start.x + end.x) / 2, max(start.y, end.y) + 1.5))
    dimension = sheet.drawingDimensions.addLinearDimension(longest.startPoint, longest.endPoint, place, False)
    if dimension is None:
        raise RuntimeError('Linear dimension creation failed')
    report['dimension_curve'] = {'start': [start.x, start.y], 'end': [end.x, end.y]}
    report['V2Dimension_version'] = save_version(drawing_doc, 'linear dimension')
    report['V2Dimension'] = common.drawing_info(drawing_doc)
    common.capture_cache('V2Dimension', started, report)
    checkpoint('captured_dimension')


try:
    run()
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    common.close_owned(owned, report)
    checkpoint(report['stage'])
