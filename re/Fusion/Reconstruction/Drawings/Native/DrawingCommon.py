import builtins
import hashlib
import json
import os
import shutil
import tempfile
import time
import traceback
from pathlib import Path

import adsk
import adsk.core
import adsk.drawing
import adsk.fusion

SCRATCH = Path(os.environ.get('KIT_DRAWING_OUT') or Path(tempfile.gettempdir()) / 'KitFusionDrawings')
PROJECT = 'Kit Fusion Acceptance'
TOKEN = 'KitDrw'
CACHE = Path.home() / 'Library/Application Support/Autodesk/Autodesk Fusion 360'
app = adsk.core.Application.get()


def state():
    if not hasattr(builtins, '_kit_drawing_state'):
        builtins._kit_drawing_state = {}
    return builtins._kit_drawing_state


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def wait_until(predicate, seconds, label):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            if predicate():
                return True
        except Exception:
            pass
        adsk.doEvents()
    raise RuntimeError('Timed out waiting for ' + label)


def ensure_project():
    hub = app.data.activeHub
    if hub is None or app.isOffLine:
        raise RuntimeError('No online active hub')
    for index in range(hub.dataProjects.count):
        item = hub.dataProjects.item(index)
        if item.name == PROJECT:
            return item, False
    project = hub.dataProjects.add(PROJECT, 'Isolated Kit Fusion native acceptance experiments', '')
    if project is None:
        raise RuntimeError('Acceptance project creation failed')
    return project, True


def token_files(since, tokens=(TOKEN,)):
    found = []
    for base, _dirs, files in os.walk(CACHE):
        for name in files:
            if any(token in name for token in tokens):
                path = Path(base) / name
                stat = path.stat()
                if stat.st_mtime >= since:
                    found.append(path)
    return sorted(found)


def capture_cache(label, since, report, tokens=(TOKEN,)):
    target = SCRATCH / 'Captures' / label
    target.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in token_files(since, tokens):
        copy = target / path.name
        shutil.copyfile(path, copy)
        rows.append({'cache_relative': str(path.relative_to(CACHE)).split('/', 1)[-1], 'bytes': copy.stat().st_size, 'sha256': digest(copy)})
    report.setdefault('captures', {})[label] = rows
    return rows


def save_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, default=str) + '\n')


def safe(getter, default=None):
    try:
        return getter()
    except Exception as error:
        return {'error': str(error)} if default is None else default


def view_info(view):
    curves = view.viewCurves
    rows = []
    for index in range(curves.count):
        curve = curves.item(index)
        row = {'type': safe(lambda: int(curve.type))}
        for name in ('startPoint', 'endPoint', 'centerPoint'):
            point = safe(lambda: getattr(curve, name), False)
            if point:
                coordinate = point.coordinate
                row[name] = [round(coordinate.x, 6), round(coordinate.y, 6)]
        rows.append(row)
    return {'type': safe(lambda: int(view.type)), 'orientation': safe(lambda: int(view.orientation)), 'scale': safe(lambda: view.scaleValue), 'style': safe(lambda: int(view.style)), 'curve_count': curves.count, 'curves': rows}


def drawing_info(document):
    drawing = adsk.drawing.DrawingDocument.cast(document).drawing
    sheets = []
    active = drawing.activeSheet
    for sheet in [active]:
        views = [view_info(sheet.views.item(index)) for index in range(sheet.views.count)]
        title = safe(lambda: sheet.titleBlock.name if sheet.titleBlock else None)
        sheets.append({'name': sheet.name, 'size': safe(lambda: int(sheet.sheetSize)), 'width': safe(lambda: sheet.width), 'height': safe(lambda: sheet.height), 'views': views, 'dimensions': safe(lambda: sheet.drawingDimensions.count), 'title_block': title})
    return {'title_blocks': safe(lambda: drawing.titleBlocks.count), 'sheets': sheets}


def close_owned(documents, report):
    for document in reversed(documents):
        try:
            if document is not None and document.isValid:
                document.close(False)
        except Exception:
            report.setdefault('close_errors', []).append(traceback.format_exc())
    documents.clear()
    for index in reversed(range(app.documents.count)):
        item = app.documents.item(index)
        try:
            if TOKEN in item.name:
                item.close(False)
        except Exception:
            report.setdefault('close_errors', []).append(traceback.format_exc())
    report['documents_after'] = app.documents.count
