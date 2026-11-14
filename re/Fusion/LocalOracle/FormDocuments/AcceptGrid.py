import hashlib
import json
from math import isclose
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

folder = Path(__file__).resolve().parent
root = folder.parents[3]
work = folder / 'Grid'
saved_folder = work / 'Saved'
preparation = json.loads((work / 'Preparation.json').read_text())
app = adsk.core.Application.get()
report = {
    'fusion_version': app.version,
    'scope': 'Kit-converted plane Form documents against Fusion conversion of the same Kit TSM; plane primitives of other sizes; converted-surface cache variants',
    'tolerance_cm': 1e-8,
    'documents_before': app.documents.count,
    'cases': [],
    'primitives': [],
    'cache': [],
}
opened = []
target = work / 'NativeAcceptance.json'
grid = [index / 6 for index in range(7)]
PRIMITIVES = ((1, 1, 2.0, 1.5), (3, 2, 3.0, 2.0), (4, 4, 2.5, 2.5), (2, 5, 1.7, 4.1))
CACHE = ('PlaneControl', 'PlaneSurfShifted', 'BoxControl', 'BoxSurfShifted')


def clean(text):
    return text.replace(str(root), '<repo>').replace(str(Path.home()), '~')


def checkpoint():
    target.write_text(clean(json.dumps(report, indent=1)) + '\n')


def xyz(point):
    return list(point.asArray())


def key(point):
    return tuple(round(value, 9) for value in point.asArray())


def nurbs(face):
    geometry = face.geometry
    row = {'surface_type': geometry.surfaceType}
    if geometry.surfaceType == adsk.core.SurfaceTypes.NurbsSurfaceType:
        data = adsk.core.NurbsSurface.cast(geometry).getData()
        row.update({'degree': [data[1], data[2]], 'counts': [data[3], data[4]], 'poles_cm': [xyz(point) for point in data[5]], 'knots_u': list(data[6]), 'knots_v': list(data[7]), 'weights': list(data[8])})
    return row


def face_row(face):
    box = face.evaluator.parametricRange()
    row = {'area_cm2': face.area, 'range': [box.minPoint.x, box.maxPoint.x, box.minPoint.y, box.maxPoint.y]}
    row.update(nurbs(face))
    params = [adsk.core.Point2D.create(box.minPoint.x + (box.maxPoint.x - box.minPoint.x) * s, box.minPoint.y + (box.maxPoint.y - box.minPoint.y) * t) for s in grid for t in grid]
    ok, points = face.evaluator.getPointsAtParameters(params)
    row['grid_cm'] = [xyz(point) for point in points] if ok else None
    return row


def edge_row(edge):
    ok, start, end = edge.evaluator.getParameterExtents()
    row = {'length_cm': edge.length, 'curve_type': edge.geometry.curveType, 'range': [start, end] if ok else None}
    if ok:
        ok, points = edge.evaluator.getPointsAtParameters([start + (end - start) * s for s in grid])
        row['points_cm'] = [xyz(point) for point in points] if ok else None
    return row


def solved(design):
    bodies = []
    for body in design.rootComponent.bRepBodies:
        edges = sorted((edge_row(edge) for edge in body.edges), key=lambda row: [round(value, 6) for value in row['points_cm'][3]])
        bodies.append({'solid': body.isSolid, 'faces': body.faces.count, 'edges': body.edges.count, 'vertices': body.vertices.count, 'area_cm2': body.area, 'volume_cm3': body.volume if body.isSolid else None, 'face_rows': [face_row(face) for face in body.faces], 'edge_rows': edges, 'vertex_cm': sorted(xyz(vertex.geometry) for vertex in body.vertices)})
    forms = design.rootComponent.features.formFeatures
    timeline = [{'name': item.name, 'health': item.healthState, 'message': item.errorOrWarningMessage} for item in design.timeline]
    return {'timeline': timeline, 'form_health': [forms.item(index).healthState for index in range(forms.count)], 'bodies': bodies}


def same(left, right, path, problems):
    if isinstance(left, bool) or isinstance(right, bool) or isinstance(left, str):
        if left != right:
            problems.append(f'{path}: {left!r} != {right!r}')
    elif isinstance(left, (int, float)) and isinstance(right, (int, float)):
        if not isclose(left, right, rel_tol=1e-8, abs_tol=1e-8):
            problems.append(f'{path}: {left!r} != {right!r}')
    elif isinstance(left, dict) and isinstance(right, dict):
        if left.keys() != right.keys():
            problems.append(f'{path}: different fields')
        for name in left.keys() & right.keys():
            same(left[name], right[name], path + '.' + name, problems)
    elif isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            problems.append(f'{path}: {len(left)} != {len(right)} items')
        for index, (first, second) in enumerate(zip(left, right)):
            same(first, second, f'{path}[{index}]', problems)
    elif left != right:
        problems.append(f'{path}: {left!r} != {right!r}')


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


def new_form():
    document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    opened.append(document)
    design = design_of(document)
    form = design.rootComponent.features.formFeatures.add()
    if not form.startEdit():
        raise RuntimeError('Form edit did not start')
    return document, design, form


def from_tsm(path):
    document, design, form = new_form()
    if form.tSplineBodies.addByTSMFile(str(path)) is None:
        raise RuntimeError('TSM import failed')
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
    stages['cage_tsm_sha256'] = hashlib.sha256(body.getTSMDescription().encode()).hexdigest()
    vertex = min(body.vertices, key=lambda item: key(item.geometry))
    stages['edited_vertex_cm'] = xyz(vertex.geometry)
    if not vertex.move(adsk.core.Vector3D.create(.11, .07, .13)):
        raise RuntimeError('Control point edit failed')
    if not form.finishEdit():
        raise RuntimeError('Form finish failed')
    stages['edited_compute'] = design.computeAll()
    stages['edited'] = solved(design)
    saved = saved_folder / (label + '.f3d')
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
        raise RuntimeError('Native save failed')
    stages['saved_file'] = str(saved.relative_to(root))
    stages['saved_sha256'] = hashlib.sha256(saved.read_bytes()).hexdigest()
    close(document)
    again = open_archive(saved)
    stages['reopened'] = solved(design_of(again))
    close(again)


def run_case(prepared):
    case = {'case': prepared['case'], 'oracle': {}, 'kit': {}}
    report['cases'].append(case)
    for name, field in (('tsm_file', 'tsm_sha256'), ('document_file', 'document_sha256')):
        if hashlib.sha256((root / prepared[name]).read_bytes()).hexdigest() != prepared[field]:
            raise RuntimeError('Prepared input changed')
    exercise(from_tsm(root / prepared['tsm_file']), 'Oracle' + prepared['case'], case['oracle'])
    exercise(open_archive(root / prepared['document_file']), 'Kit' + prepared['case'], case['kit'])
    problems = []
    oracle, kit = case['oracle'], case['kit']
    for left, right in (('loaded', 'solved'), ('solved', 'solved'), ('edited', 'edited'), ('reopened', 'reopened')):
        for field in ('bodies', 'form_health'):
            same(kit[left][field], oracle[right][field], f'kit.{left}~oracle.{right}.{field}', problems)
    same(kit['reopened']['bodies'], kit['edited']['bodies'], 'kit.reopened~kit.edited', problems)
    same([item['health'] for item in kit['solved']['timeline']], [0] * len(kit['solved']['timeline']), 'kit.timeline_health', problems)
    for name in ('cage_tsm_sha256', 'edited_vertex_cm'):
        same(kit[name], oracle[name], name, problems)
    case['problems'] = problems[:40]
    case['problem_count'] = len(problems)
    case['status'] = 'accepted' if not problems else 'different'


def run_primitive(spec):
    count_x, count_y, size_x, size_y = spec
    row = {'faces': [count_x, count_y], 'size_cm': [size_x, size_y]}
    report['primitives'].append(row)
    document, design, form = new_form()
    shape = form.tSplineBodies.createPlaneInput(adsk.core.Point3D.create(0, 0, 0), adsk.core.Vector3D.create(1, 0, 0), adsk.core.Vector3D.create(0, 1, 0), size_x, size_y)
    shape.xFaceCount = count_x
    shape.yFaceCount = count_y
    if form.tSplineBodies.addByShapeInput(shape) is None:
        raise RuntimeError('Plane primitive failed')
    if not form.finishEdit():
        raise RuntimeError('Form finish failed')
    row['compute_all'] = design.computeAll()
    row['solved'] = solved(design)
    saved = work / 'Primitives' / f'Plane{count_x}x{count_y}.f3d'
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
        raise RuntimeError('Native save failed')
    row['saved_file'] = str(saved.relative_to(root))
    row['saved_sha256'] = hashlib.sha256(saved.read_bytes()).hexdigest()
    row['status'] = 'completed'
    close(document)


def run_cache(name):
    row = {'variant': name, 'file': f're/Fusion/LocalOracle/FormDocuments/Cache/{name}.f3d'}
    report['cache'].append(row)
    document = open_archive(root / row['file'])
    design = design_of(document)
    row['loaded'] = solved(design)
    row['compute_all'] = design.computeAll()
    row['solved'] = solved(design)
    row['status'] = 'completed'
    close(document)


def guarded(action, value, rows):
    try:
        action(value)
    except Exception:
        rows[-1]['status'] = 'error'
        rows[-1]['traceback'] = traceback.format_exc()
    finally:
        for document in list(opened):
            close(document)
        checkpoint()


try:
    saved_folder.mkdir(exist_ok=True)
    (work / 'Primitives').mkdir(exist_ok=True)
    for prepared in preparation['rows']:
        guarded(run_case, prepared, report['cases'])
    for spec in PRIMITIVES:
        guarded(run_primitive, spec, report['primitives'])
    for name in CACHE:
        guarded(run_cache, name, report['cache'])
    accepted = all(case.get('status') == 'accepted' for case in report['cases'])
    report['status'] = 'accepted' if accepted else 'different'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    for document in list(opened):
        close(document)
    report['documents_after'] = app.documents.count
    checkpoint()
