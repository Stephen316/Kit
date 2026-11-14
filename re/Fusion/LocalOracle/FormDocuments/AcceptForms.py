import hashlib
import json
from math import isclose
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

folder = Path(__file__).resolve().parent
root = folder.parents[3]
work = folder / 'Acceptance'
preparation = json.loads((work / 'Preparation.json').read_text())
app = adsk.core.Application.get()
original = app.activeDocument
report = {'fusion_version': app.version, 'scope': 'Production Form document re-emission; native open, form health, cage edit, conversion, save and reopen', 'documents_before': app.documents.count, 'cases': []}
opened = []
target = work / 'NativeAcceptance.json'


def clean(text):
    return text.replace(str(root), '<repo>').replace(str(Path.home()), '~')


def checkpoint():
    target.write_text(clean(json.dumps(report, indent=2)) + '\n')


def xyz(point):
    return list(point.asArray())


def key(point):
    return tuple(round(value, 9) for value in point.asArray())


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':')).encode()).hexdigest()


def cage(body):
    points = sorted(key(vertex.geometry) for vertex in body.vertices)
    edges = sorted((tuple(sorted((key(edge.startVertex.geometry), key(edge.endVertex.geometry)))), edge.isCreased) for edge in body.edges)
    faces = sorted(tuple(sorted(key(vertex.geometry) for vertex in face.vertices)) for face in body.faces)
    return {'faces': body.faces.count, 'edges': body.edges.count, 'vertices': body.vertices.count, 'control_sha256': digest(points), 'edge_crease_sha256': digest(edges), 'face_incidence_sha256': digest(faces)}


def solved(design):
    bodies = []
    for body in design.rootComponent.bRepBodies:
        row = {'solid': body.isSolid, 'faces': body.faces.count, 'edges': body.edges.count, 'vertices': body.vertices.count, 'area_cm2': body.area, 'bounds_cm': [xyz(body.boundingBox.minPoint), xyz(body.boundingBox.maxPoint)]}
        row['volume_cm3'] = body.volume if body.isSolid else None
        bodies.append(row)
    timeline = [{'name': item.name, 'health': item.healthState, 'message': item.errorOrWarningMessage} for item in design.timeline]
    forms = design.rootComponent.features.formFeatures
    return {'timeline': timeline, 'bodies': bodies, 'forms': forms.count, 'form_health': [forms.item(index).healthState for index in range(forms.count)]}


def compare(a, b, path, problems):
    if isinstance(a, float) and isinstance(b, (float, int)):
        if not isclose(a, b, rel_tol=1e-7, abs_tol=1e-7):
            problems.append('%s: %r != %r' % (path, a, b))
    elif isinstance(a, dict) and isinstance(b, dict):
        if a.keys() != b.keys():
            problems.append('%s: fields differ' % path)
            return
        for name in a:
            compare(a[name], b[name], path + '.' + name, problems)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            problems.append('%s: counts %d != %d' % (path, len(a), len(b)))
            return
        for index, (left, right) in enumerate(zip(a, b)):
            compare(left, right, '%s.%d' % (path, index), problems)
    elif a != b:
        problems.append('%s: %r != %r' % (path, a, b))


def close(document):
    if document is not None and document.isValid:
        document.close(False)
    if document in opened:
        opened.remove(document)


def design_of(document):
    return adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))


def open_archive(path):
    document = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(path)))
    if document is None:
        raise RuntimeError('Archive did not open')
    opened.append(document)
    return document


def from_tsm(path):
    document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    opened.append(document)
    design = design_of(document)
    form = design.rootComponent.features.formFeatures.add()
    form.name = 'Qualified Form'
    if not form.startEdit():
        raise RuntimeError('Form edit did not start')
    body = form.tSplineBodies.addByTSMFile(str(path))
    if body is None:
        raise RuntimeError('TSM import failed')
    body.name = 'Qualified Cage'
    if not form.finishEdit():
        raise RuntimeError('Form finish failed')
    return document


def exercise(document, label, stages):
    design = design_of(document)
    stages['loaded'] = solved(design)
    stages['compute_all'] = design.computeAll()
    stages['solved'] = solved(design)
    form = design.rootComponent.features.formFeatures.item(0)
    if not form.startEdit():
        raise RuntimeError('Form edit did not start')
    body = form.tSplineBodies.item(0)
    stages['cage'] = cage(body)
    vertex = min(body.vertices, key=lambda item: key(item.geometry))
    stages['edited_point_cm'] = xyz(vertex.geometry)
    if not vertex.move(adsk.core.Vector3D.create(.11, .07, .13)):
        raise RuntimeError('Control point edit failed')
    stages['edited_cage'] = cage(body)
    if not form.finishEdit():
        raise RuntimeError('Form finish failed')
    stages['edited_compute'] = design.computeAll()
    stages['edited'] = solved(design)
    saved = work / 'Saved' / (label + '.f3d')
    saved.parent.mkdir(exist_ok=True)
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
        raise RuntimeError('Native save failed')
    stages['saved_sha256'] = hashlib.sha256(saved.read_bytes()).hexdigest()
    close(document)
    again = open_archive(saved)
    design = design_of(again)
    stages['reopened_compute'] = design.computeAll()
    stages['reopened'] = solved(design)
    form = design.rootComponent.features.formFeatures.item(0)
    if not form.startEdit():
        raise RuntimeError('Reopened form edit did not start')
    stages['reopened_cage'] = cage(form.tSplineBodies.item(0))
    form.finishEdit()
    close(again)
    problems = []
    compare(stages['edited'], stages['reopened'], 'saved', problems)
    compare(stages['edited_cage'], stages['reopened_cage'], 'saved_cage', problems)
    stages['save_reopen_problems'] = problems


def run_variant(case, label, kind, relative, expected):
    row = {'variant': label, 'file': relative, 'stages': {}}
    case['variants'].append(row)
    document = None
    try:
        path = root / relative
        row['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        if expected is not None and row['sha256'] != expected:
            raise RuntimeError('Prepared input changed')
        document = from_tsm(path) if kind == 'tsm' else open_archive(path)
        exercise(document, case['name'] + label, row['stages'])
        row['status'] = 'completed'
    except Exception:
        row['status'] = 'error'
        row['traceback'] = traceback.format_exc()
    finally:
        close(document)
        checkpoint()
    return row


try:
    for prepared in preparation['cases']:
        case = {'name': prepared['name'], 'kind': prepared['kind'], 'variants': []}
        report['cases'].append(case)
        if prepared['kind'] == 'reemitted':
            first = run_variant(case, 'Control', 'archive', prepared['control_file'], prepared['control_sha256'])
            second = run_variant(case, 'Reemitted', 'archive', prepared['file'], prepared['sha256'])
        else:
            first = run_variant(case, 'NativeFromTsm', 'tsm', prepared['tsm_file'], prepared['tsm_sha256'])
            second = run_variant(case, 'Authored', 'archive', prepared['file'], prepared['sha256'])
        problems = []
        if first['status'] == second['status'] == 'completed':
            for stage in ('solved', 'cage', 'edited_point_cm', 'edited', 'reopened', 'reopened_cage'):
                compare(first['stages'][stage], second['stages'][stage], stage, problems)
            problems += first['stages']['save_reopen_problems'] + second['stages']['save_reopen_problems']
            healthy = all(value == 0 for value in second['stages']['solved']['form_health'] + second['stages']['edited']['form_health'])
            case['status'] = 'accepted' if not problems and healthy and second['stages']['solved']['forms'] == 1 else 'mismatch'
        else:
            case['status'] = 'error'
        case['problems'] = problems
        checkpoint()
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    for document in list(opened):
        close(document)
    if original is not None and original.isValid:
        original.activate()
    report['documents_after'] = app.documents.count
    checkpoint()
