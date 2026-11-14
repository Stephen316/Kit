# Capture Fusion-saved drawing controls without creating cloud documents.
# The account is at its editable-document limit, so this script opens one existing editable KitDrw drawing,
# adds sheets in other sizes and orientations, places base views in other orientations and adds horizontal,
# vertical, aligned, radial and diameter dimensions. With "save": true in the request it saves one new
# version of that drawing and copies the local cache; otherwise it only reports and closes without saving.
# Request: $TMPDIR/KitFusionDrawings/Rules/CaptureEdit.request.json, for example
#   {"drawing": "KitDrw Wheel Drawing", "save": false, "plans": ["RuleA4P", "RuleA2"]}
# "existing_info": false and "after_info": false skip the slow per-view reads before and after the edit.
# Report: $TMPDIR/KitFusionDrawings/Rules/CaptureEdit.json. Run it through Native/RunGuarded.mjs with
# --watch on that report and --stall 420, because a valid drawing open can take more than 6 minutes.
import importlib
import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'Native'))
common = importlib.reload(importlib.import_module('DrawingCommon'))

import adsk.core
import adsk.drawing

app = common.app
out = common.SCRATCH / 'Rules'
request = json.loads((out / 'CaptureEdit.request.json').read_text())
report = {'fusion_version': app.version, 'request': request, 'stage': 'starting', 'sheets': {}}
owned = []
Orient = adsk.drawing.ViewOrientationTypes
Sizes = adsk.drawing.SheetSizes
Turns = adsk.drawing.SheetOrientationTypes
Styles = adsk.drawing.DrawingViewStyleTypes
Tangents = adsk.drawing.TangentEdgeDisplayTypes

PLANS = {
    'RuleA4P': {'size': Sizes.A4ISOSheetSize, 'turn': Turns.PortraitSheetOrientationType, 'views': [(Orient.LeftViewOrientationType, 0.35, 0.62), (Orient.IsoTopRightViewOrientationType, 0.7, 0.3)]},
    'RuleA2': {'size': Sizes.A2ISOSheetSize, 'turn': Turns.LandscapeSheetOrientationType, 'views': [(Orient.BackViewOrientationType, 0.3, 0.6), (Orient.BottomViewOrientationType, 0.6, 0.6), (Orient.IsoBottomLeftViewOrientationType, 0.6, 0.3)]},
    'RuleA1': {'size': Sizes.A1ISOSheetSize, 'turn': Turns.LandscapeSheetOrientationType, 'views': [(Orient.RightViewOrientationType, 0.3, 0.6), (Orient.TopViewOrientationType, 0.6, 0.6)]},
    'RuleAsmeB': {'size': Sizes.BASMESheetSize, 'turn': Turns.LandscapeSheetOrientationType, 'views': [(Orient.FrontViewOrientationType, 0.3, 0.6), (Orient.IsoTopLeftViewOrientationType, 0.65, 0.4)]},
    'RuleA4L': {'size': Sizes.A4ISOSheetSize, 'turn': Turns.LandscapeSheetOrientationType, 'views': [(Orient.FrontViewOrientationType, 0.4, 0.55)]},
    # Adds a base view to the drawing's first sheet, to tell a view's age from the sheet it sits on.
    'FirstFront': {'sheet': 'first', 'views': [(Orient.FrontViewOrientationType, 0.85, 0.72)]},
    # One base view per display option, each changing one option from the documented defaults, to map the
    # view record's shape fields to the options.
    'StyleGrid': {'size': Sizes.A1ISOSheetSize, 'turn': Turns.LandscapeSheetOrientationType, 'dimensions': False, 'views': [
        (Orient.FrontViewOrientationType, 0.15, 0.75, {'style': Styles.VisibleEdgesDrawingViewStyleType}),
        (Orient.FrontViewOrientationType, 0.38, 0.75, {'style': Styles.VisibleAndHiddenEdgesDrawingViewStyleType}),
        (Orient.FrontViewOrientationType, 0.61, 0.75, {'style': Styles.ShadedVisibleEdgesDrawingViewStyleType}),
        (Orient.FrontViewOrientationType, 0.84, 0.75, {'style': Styles.ShadedAndHiddenEdgesDrawingViewStyleType}),
        (Orient.FrontViewOrientationType, 0.15, 0.4, {'style': Styles.VisibleEdgesDrawingViewStyleType, 'tangent': Tangents.OffTangentEdgeDisplayType}),
        (Orient.FrontViewOrientationType, 0.38, 0.4, {'style': Styles.VisibleEdgesDrawingViewStyleType, 'tangent': Tangents.FullLengthTangentEdgeDisplayType}),
        (Orient.FrontViewOrientationType, 0.61, 0.4, {'style': Styles.VisibleEdgesDrawingViewStyleType, 'threads': True}),
        (Orient.FrontViewOrientationType, 0.84, 0.4, {'style': Styles.VisibleEdgesDrawingViewStyleType, 'interference': True}),
    ]},
    # Base views created with a style are all saved as visible and hidden edges (StyleGrid), so these set the style
    # after creation: visible, visible and hidden, shaded and hidden, shaded visible.
    'StyleSet': {'size': Sizes.A1ISOSheetSize, 'turn': Turns.LandscapeSheetOrientationType, 'dimensions': False, 'views': [
        (Orient.FrontViewOrientationType, 0.2, 0.7, {'after_style': Styles.VisibleEdgesDrawingViewStyleType}),
        (Orient.FrontViewOrientationType, 0.7, 0.7, {'after_style': Styles.VisibleAndHiddenEdgesDrawingViewStyleType}),
        (Orient.FrontViewOrientationType, 0.2, 0.3, {'after_style': Styles.ShadedAndHiddenEdgesDrawingViewStyleType}),
        (Orient.FrontViewOrientationType, 0.7, 0.3, {'after_style': Styles.ShadedVisibleEdgesDrawingViewStyleType}),
    ]},
    # FitGrid's input scales were ignored (every view took the sheet's scale), so these set the scale after creation.
    'FitSet': {'size': Sizes.A1ISOSheetSize, 'turn': Turns.LandscapeSheetOrientationType, 'views': [
        (Orient.FrontViewOrientationType, 0.18, 0.72, {'after_scale': 3.0}),
        (Orient.FrontViewOrientationType, 0.5, 0.72, {'after_scale': 4.0}),
        (Orient.FrontViewOrientationType, 0.82, 0.72, {'after_scale': 4.5}),
        (Orient.FrontViewOrientationType, 0.18, 0.3, {'after_scale': 4.53}),
        (Orient.FrontViewOrientationType, 0.5, 0.3, {'after_scale': 4.56}),
        (Orient.FrontViewOrientationType, 0.82, 0.3, {'after_scale': 4.6}),
    ]},
    # FitSet kept arrows inside from 10.607 mm and text inside from 14.142 mm, so these scales put the 3.54 mm
    # chamfer's aligned dimension on both sides of each candidate limit: arrows 9.8 or 10.5 mm, text 11.875 or 12.575 mm.
    'FitSteps': {'size': Sizes.A1ISOSheetSize, 'turn': Turns.LandscapeSheetOrientationType, 'views': [
        (Orient.FrontViewOrientationType, fx, fy, {'after_scale': value}) for (fx, fy), value in zip(
            [(fx, fy) for fy in (0.8, 0.5, 0.2) for fx in (0.18, 0.5, 0.82)],
            (2.75, 2.8, 2.95, 2.99, 3.33, 3.39, 3.54, 3.58, 3.9))
    ]},
    # StyleSet tied the hidden-edge style to ViewLongB and shading to flag bit 0. These set one other display option
    # each after creation, all on the visible-edge style, to find the flag bits 0x400, 0x800 and 0x2000.
    'ToggleSet': {'size': Sizes.A1ISOSheetSize, 'turn': Turns.LandscapeSheetOrientationType, 'dimensions': False, 'views': [
        (Orient.FrontViewOrientationType, fx, fy, {'after': {'style': Styles.VisibleEdgesDrawingViewStyleType, **change}})
        for (fx, fy), change in zip(
            [(fx, fy) for fy in (0.75, 0.3) for fx in (0.15, 0.38, 0.61, 0.84)],
            ({}, {'tangentEdgesType': Tangents.OffTangentEdgeDisplayType},
             {'tangentEdgesType': Tangents.FullLengthTangentEdgeDisplayType},
             {'style': Styles.VisibleAndHiddenEdgesDrawingViewStyleType},
             {'isShowThreadEdges': True}, {'isShowThreadEdges': False},
             {'isShowInterferenceEdges': True}, {'isShowInterferenceEdges': False}))
    ]},
    # Small scales put the 10 mm vertical edge's dimension (text 4.672 mm wide) where its text may fit between the
    # extension lines while its arrows do not.
    'FitShort': {'size': Sizes.A1ISOSheetSize, 'turn': Turns.LandscapeSheetOrientationType, 'views': [
        (Orient.FrontViewOrientationType, fx, fy, {'after_scale': value}) for (fx, fy), value in zip(
            [(fx, fy) for fy in (0.75, 0.3) for fx in (0.18, 0.5, 0.82)],
            (0.6, 0.75, 0.85, 0.95, 1.1, 1.3))
    ]},
    # Front views at scales that put the 3.54 mm chamfer's aligned dimension just below and just above two 3.5 mm
    # arrows plus its text (16.075 mm on the sheet), to find when Fusion moves arrows and text outside.
    'FitGrid': {'size': Sizes.A1ISOSheetSize, 'turn': Turns.LandscapeSheetOrientationType, 'views': [
        (Orient.FrontViewOrientationType, 0.18, 0.72, {'scale': 3.0}),
        (Orient.FrontViewOrientationType, 0.5, 0.72, {'scale': 4.0}),
        (Orient.FrontViewOrientationType, 0.82, 0.72, {'scale': 4.5}),
        (Orient.FrontViewOrientationType, 0.18, 0.3, {'scale': 4.53}),
        (Orient.FrontViewOrientationType, 0.5, 0.3, {'scale': 4.56}),
        (Orient.FrontViewOrientationType, 0.82, 0.3, {'scale': 4.6}),
    ]},
}


def checkpoint(stage):
    report['stage'] = stage
    common.save_json(out / 'CaptureEdit.json', report)


def find_file(name):
    project, _created = common.ensure_project()
    pending = [project.rootFolder]
    while pending:
        folder = pending.pop()
        for index in range(folder.dataFiles.count):
            item = folder.dataFiles.item(index)
            if item.name == name:
                return item
        pending.extend(folder.dataFolders.item(index) for index in range(folder.dataFolders.count))
    raise RuntimeError('Drawing not found: ' + name)


def coords(point):
    value = point.coordinate
    return value.x, value.y


def at(x_cm, y_cm):
    return adsk.drawing.DrawingPoint.create(adsk.core.Point2D.create(x_cm, y_cm))


def add_dimensions(sheet, view, made):
    curves = [view.viewCurves.item(index) for index in range(view.viewCurves.count)]
    lines = [c for c in curves if c.startPoint is not None and c.endPoint is not None and c.centerPoint is None]
    rounds = [c for c in curves if c.centerPoint is not None]

    def run(kind, action, detail):
        try:
            result = action()
            made.append({'kind': kind, 'created': result is not None, **detail})
        except Exception:
            made.append({'kind': kind, 'error': traceback.format_exc()[-400:], **detail})

    def span(curve):
        (x0, y0), (x1, y1) = coords(curve.startPoint), coords(curve.endPoint)
        return x0, y0, x1, y1

    flats = [c for c in lines if abs(span(c)[3] - span(c)[1]) < 1e-6]
    talls = [c for c in lines if abs(span(c)[2] - span(c)[0]) < 1e-6]
    slants = [c for c in lines if c not in flats and c not in talls and abs(span(c)[2] - span(c)[0]) > 0.2 and abs(span(c)[3] - span(c)[1]) > 0.2]
    if flats:
        edge = max(flats, key=lambda c: abs(span(c)[2] - span(c)[0]))
        x0, y0, x1, y1 = span(edge)
        place = ((x0 + x1) / 2, max(y0, y1) + 1.2)
        run('horizontal', lambda: sheet.drawingDimensions.addLinearDimension(edge.startPoint, edge.endPoint, at(*place), False), {'first': [x0, y0], 'second': [x1, y1], 'place': place})
    if talls:
        edge = max(talls, key=lambda c: abs(span(c)[3] - span(c)[1]))
        x0, y0, x1, y1 = span(edge)
        place = (max(x0, x1) + 1.2, (y0 + y1) / 2)
        run('vertical', lambda: sheet.drawingDimensions.addLinearDimension(edge.startPoint, edge.endPoint, at(*place), False), {'first': [x0, y0], 'second': [x1, y1], 'place': place})
    if slants:
        edge = max(slants, key=lambda c: (span(c)[2] - span(c)[0]) ** 2 + (span(c)[3] - span(c)[1]) ** 2)
        x0, y0, x1, y1 = span(edge)
        place = ((x0 + x1) / 2 + 0.8, (y0 + y1) / 2 + 0.8)
        run('aligned', lambda: sheet.drawingDimensions.addLinearDimension(edge.startPoint, edge.endPoint, at(*place), True), {'first': [x0, y0], 'second': [x1, y1], 'place': place})
    if rounds:
        circle = max(rounds, key=lambda c: common.safe(lambda: c.radius, 0) or 0)
        cx, cy = coords(circle.centerPoint)
        radius = common.safe(lambda: circle.radius, None)
        run('radial', lambda: sheet.drawingDimensions.addRadialDimension(circle, at(cx + 1.5, cy + 1.0)), {'center': [cx, cy], 'radius': radius, 'place': [cx + 1.5, cy + 1.0]})
        run('diameter', lambda: sheet.drawingDimensions.addDiameterDimension(circle, at(cx - 1.5, cy - 1.2)), {'center': [cx, cy], 'radius': radius, 'place': [cx - 1.5, cy - 1.2]})
    return {'lines': len(lines), 'rounds': len(rounds), 'flats': len(flats), 'talls': len(talls), 'slants': len(slants)}


def sheet_info(sheet):
    dims = []
    for number in range(sheet.drawingDimensions.count):
        item = sheet.drawingDimensions.item(number)
        dims.append({'type': common.safe(lambda: int(item.type)), 'object': common.safe(lambda: item.objectType)})
    views = [common.view_info(sheet.views.item(n)) for n in range(sheet.views.count)]
    for row in views:
        row['curves'] = row['curves'][:6]
    return {'name': sheet.name, 'size': common.safe(lambda: int(sheet.sheetSize)), 'orientation': common.safe(lambda: int(sheet.orientation)), 'width': common.safe(lambda: sheet.width), 'height': common.safe(lambda: sheet.height), 'views': views, 'dimensions': dims}


def set_options(params, options):
    if 'style' in options:
        params.style = options['style']
    if 'tangent' in options:
        params.tangentEdgesType = options['tangent']
    if 'threads' in options:
        params.isShowThreadEdges = options['threads']
    if 'interference' in options:
        params.isShowInterferenceEdges = options['interference']
    if 'scale' in options:
        params.scaleValue = options['scale']


def read_options(view):
    if view is None:
        return None
    return {'style': common.safe(lambda: int(view.style)), 'handle_note': 'view record handle comes from the save'}


def new_sheet(drawing, label, plan):
    entry = drawing.sheets.createInput()
    entry.name = 'Kit ' + label
    sheet = drawing.sheets.add(entry)
    if sheet is None:
        raise RuntimeError('Sheet add returned null')
    sheet.sheetSize = plan['size']
    sheet.orientation = plan['turn']
    return sheet


def add_sheet(drawing, label, plan, scale):
    row = report['sheets'].setdefault(label, {})
    if plan.get('sheet') == 'first':
        sheet = drawing.sheets.item(0)
    else:
        sheet = new_sheet(drawing, label, plan)
    row['size_after_set'] = [common.safe(lambda: sheet.width), common.safe(lambda: sheet.height)]
    width, height = sheet.width, sheet.height
    made = []
    for orientation, fx, fy, *extra in plan['views']:
        options = extra[0] if extra else {}
        try:
            entry = sheet.views.createBaseViewInput()
            entry.placementPoint = at(width * fx, height * fy)
            entry.viewParameters.orientation = orientation
            entry.viewParameters.scaleValue = scale
            set_options(entry.viewParameters, options)
            view = sheet.views.add(entry)
            made.append(view)
            restyle = None
            if 'after_style' in options and view is not None:
                try:
                    view.style = options['after_style']
                    restyle = 'set'
                except Exception:
                    restyle = traceback.format_exc()[-300:]
            row.setdefault('restyle', []).append(restyle)
            if 'after' in options and view is not None:
                applied = {}
                for name, value in options['after'].items():
                    try:
                        setattr(view, name, value)
                        applied[name] = ['set', str(common.safe(lambda: getattr(view, name)))]
                    except Exception:
                        applied[name] = traceback.format_exc()[-200:]
                row.setdefault('applied', []).append(applied)
            if 'after_scale' in options and view is not None:
                tried = {}
                for name in ('scaleValue', 'scale'):
                    try:
                        setattr(view, name, options['after_scale'])
                        tried[name] = 'set'
                        break
                    except Exception:
                        tried[name] = traceback.format_exc()[-200:]
                tried['read'] = [common.safe(lambda: view.scaleValue), str(common.safe(lambda: view.scale))]
                row.setdefault('rescale', []).append(tried)
            row.setdefault('view_results', []).append({'orientation': int(orientation), 'created': view is not None, 'place_cm': [width * fx, height * fy], 'asked': {key: (value if isinstance(value, (bool, float)) else ({k: (v if isinstance(v, (bool, float)) else int(v)) for k, v in value.items()} if isinstance(value, dict) else int(value))) for key, value in options.items()}, 'options': read_options(view)})
        except Exception:
            row.setdefault('view_results', []).append({'orientation': int(orientation), 'error': traceback.format_exc()[-400:]})
    dims = row.setdefault('dimension_results', [])
    for view in made:
        if view is not None and plan.get('dimensions', True):
            row.setdefault('curve_kinds', []).append(add_dimensions(sheet, view, dims))
    checkpoint(label + ' built')


def run():
    out.mkdir(parents=True, exist_ok=True)
    started = time.time() - 2
    data_file = find_file(request['drawing'])
    report['drawing'] = {'name': data_file.name, 'version_before': data_file.versionNumber, 'read_only': common.safe(lambda: data_file.isReadOnly)}
    if request.get('save') and data_file.isReadOnly:
        raise RuntimeError('The drawing is read-only, so a save would never finish')
    checkpoint('opening drawing ' + data_file.name)
    document = app.documents.open(data_file, True)
    if document is None:
        raise RuntimeError('Open returned null')
    owned.append(document)
    drawing = adsk.drawing.DrawingDocument.cast(document).drawing
    settings = drawing.documentSettings
    report['settings'] = {'standard': common.safe(lambda: int(settings.standard)), 'projection': common.safe(lambda: int(settings.projectionAngle)), 'units': common.safe(lambda: int(settings.units))}
    first = drawing.sheets.item(0)
    if request.get('existing_info', True):
        report['existing'] = [sheet_info(drawing.sheets.item(n)) for n in range(drawing.sheets.count)]
    scale = request.get('scale') or common.safe(lambda: first.views.item(0).scaleValue, 1.0) or 1.0
    report['scale'] = scale
    checkpoint('opened')
    for label in request['plans']:
        try:
            add_sheet(drawing, label, PLANS[label], scale)
        except Exception:
            report['sheets'].setdefault(label, {})['error'] = traceback.format_exc()[-800:]
            checkpoint(label + ' failed')
    if request.get('save'):
        if not document.save('Kit drawing rule controls ' + ' '.join(request['plans'])):
            raise RuntimeError('save did not start')
        common.wait_until(lambda: document.dataFile.isComplete and not document.isModified, 600, 'drawing version save')
        report['drawing']['version_after'] = document.dataFile.versionNumber
        checkpoint('saved')
        time.sleep(3)
        common.capture_cache('Edit' + str(document.dataFile.versionNumber), started, report)
    # Sheet details last: reading every view of every sheet can take minutes, and the save must not wait for it.
    report['after'] = []
    for number in range(drawing.sheets.count if request.get('after_info', True) else 0):
        report['after'].append(sheet_info(drawing.sheets.item(number)))
        checkpoint('sheet info ' + str(number))
    checkpoint('done')


try:
    run()
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    common.close_owned(owned, report)
    checkpoint(report['stage'])
