import hashlib
import json
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

folder = Path(__file__).resolve().parent
root = folder.parents[3]
preparation = json.loads((folder / 'Stale' / 'Preparation.json').read_text())
app = adsk.core.Application.get()
original = app.activeDocument
report = {'fusion_version': app.version, 'scope': 'Native response to stale or omitted Form BRep caches and disagreeing TSM copies', 'documents_before': app.documents.count, 'cases': []}
target = folder / 'Stale' / 'Probe.json'


def checkpoint():
    target.write_text(json.dumps(report, indent=2) + '\n')


def xyz(point):
    return list(point.asArray())


def bodies(design):
    rows = []
    for body in design.rootComponent.bRepBodies:
        row = {'name': body.name, 'solid': body.isSolid, 'faces': body.faces.count, 'edges': body.edges.count, 'vertices': body.vertices.count, 'area_cm2': body.area, 'bounds_cm': [xyz(body.boundingBox.minPoint), xyz(body.boundingBox.maxPoint)]}
        if body.isSolid:
            row['volume_cm3'] = body.volume
        rows.append(row)
    return rows


def features(design):
    return [{'name': item.name, 'health': item.healthState, 'message': item.errorOrWarningMessage} for item in design.timeline]


def cage(form):
    rows = []
    for body in form.tSplineBodies:
        points = sorted(tuple(round(value, 9) for value in vertex.geometry.asArray()) for vertex in body.vertices)
        rows.append({'vertices': body.vertices.count, 'faces': body.faces.count, 'lowest_points': points[:3], 'points_sha256': hashlib.sha256(json.dumps(points).encode()).hexdigest()})
    return rows


def observe(document, form_stage):
    design = adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))
    state = {'bodies_loaded': bodies(design), 'timeline_loaded': features(design)}
    state['compute_all'] = design.computeAll()
    state['bodies_computed'] = bodies(design)
    state['timeline_computed'] = features(design)
    forms = design.rootComponent.features.formFeatures
    state['forms'] = forms.count
    if forms.count and form_stage:
        form = forms.item(0)
        state['form_health'] = form.healthState
        if form.startEdit():
            state['cage'] = cage(form)
            state['finish'] = form.finishEdit()
            state['compute_after_edit'] = design.computeAll()
            state['bodies_after_edit'] = bodies(design)
            state['timeline_after_edit'] = features(design)
        else:
            state['edit_started'] = False
    return state


try:
    controls = {}
    for case in preparation['cases']:
        controls.setdefault(case['kind'], case['source'])
    entries = [(kind, 'Control', source) for kind, source in controls.items()] + [(case['kind'], case['variant'], case['file']) for case in preparation['cases']]
    for kind, label, relative in entries:
        row = {'kind': kind, 'variant': label, 'file': relative, 'sha256': hashlib.sha256((root / relative).read_bytes()).hexdigest()}
        report['cases'].append(row)
        document = None
        try:
            document = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(root / relative)))
            row['opened'] = document is not None
            if document is not None:
                row['state'] = observe(document, True)
        except Exception:
            row['error'] = traceback.format_exc()
        finally:
            if document is not None and document.isValid:
                document.close(False)
        checkpoint()
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    while app.documents.count > report['documents_before']:
        latest = app.documents.item(app.documents.count - 1)
        if latest == original:
            break
        latest.close(False)
    if original is not None and original.isValid:
        original.activate()
    report['documents_after'] = app.documents.count
    checkpoint()
