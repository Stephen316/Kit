"""Locate the step that stopped Fusion during the TwoTexts bounds acceptance.

Runs the acceptance steps on the native two_texts.f3d control one at a time
and appends a synced log line before and after each step, so the last start
line without a matching done line names the failing step if Fusion stops.
Run only through RunLocked.mjs with a short timeout.
"""

import json
import os
from pathlib import Path
import shutil
import tempfile
import traceback

import adsk.core
import adsk.fusion

root = Path(__file__).resolve().parents[3]
folder = Path(__file__).resolve().parent / 'ComplexGeometry' / 'Bounds'
log = folder / 'CrashProbe.jsonl'
source = root / 're/Fusion/Study/embosstext-cd769aa41cdf/two_texts.f3d'
app = adsk.core.Application.get()
document = None
vendor = Path(tempfile.mkdtemp(prefix='kit-probe-'))


def note(**fields):
    with open(log, 'a') as handle:
        handle.write(json.dumps(fields, default=str) + '\n')
        handle.flush()
        os.fsync(handle.fileno())


def step(name, action):
    note(step=name, phase='start')
    value = action()
    note(step=name, phase='done', value=value)
    return value


def kind(entity):
    return 'None' if entity.geometry is None else entity.geometry.objectType


def bodies(design):
    return [body for component in design.allComponents for body in component.bRepBodies]


def light(design):
    return dict(marker=design.timeline.markerPosition, timeline=[(item.name, item.healthState) for item in design.timeline], bodies=[(body.name, body.isValid, body.faces.count, body.edges.count) for body in bodies(design)])


def open_archive(path):
    global document
    document = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(path)))
    return adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))


def close():
    global document
    if document is not None and document.isValid:
        document.close(False)
    document = None


def measures(design):
    for index, body in enumerate(bodies(design)):
        step(f'body{index}.mass', lambda: dict(area=body.area, volume=body.volume if body.isSolid else None, low=body.boundingBox.minPoint.asArray(), high=body.boundingBox.maxPoint.asArray()))
        step(f'body{index}.kinds', lambda: dict(faces=sorted(set(kind(face) for face in body.faces)), edges=sorted(set(kind(edge) for edge in body.edges))))
        step(f'body{index}.faceboxes', lambda: sum(face.area for face in body.faces if kind(face) == 'adsk::core::NurbsSurface' and face.boundingBox is not None))
        for number, edge in enumerate(body.edges):
            if kind(edge) == 'adsk::core::NurbsCurve3D':
                step(f'body{index}.edge{number}.length', lambda: edge.length)


try:
    log.write_text('')
    note(step='begin', fusion_version=app.version, documents_before=app.documents.count)
    design = step('import', lambda: open_archive(source))
    step('opened', lambda: light(design))
    step('parameterkinds', lambda: [(value.name, value.objectType, value.unit, value.expression) for value in design.allParameters])
    step('parameterfields', lambda: sorted({name for value in design.allParameters for name in dir(value) if 'text' in name.lower() or 'type' in name.lower()}))
    measures(design)
    for marker in reversed(range(design.timeline.count)):
        def roll(position=marker):
            design.timeline.markerPosition = position
            return light(design)
        step(f'rollback{marker}', roll)
        measures(design)
    step('restore', lambda: design.timeline.moveToEnd() and design.computeAll())
    step('rebuilt', lambda: light(design))
    target = vendor / 'probe.f3d'
    step('export', lambda: design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(target))))
    step('close', lambda: close() is None)
    step('reopen', lambda: open_archive(target) is not None)
    design = adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))
    step('recompute', lambda: design.computeAll())
    step('reopened', lambda: light(design))
    note(step='end', status='completed')
except Exception:
    note(step='end', status='failed', traceback=traceback.format_exc())
    raise
finally:
    close()
    shutil.rmtree(vendor, ignore_errors=True)
    note(step='finally', documents_after=app.documents.count)
