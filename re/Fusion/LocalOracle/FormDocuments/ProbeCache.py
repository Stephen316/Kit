import hashlib
import json
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

folder = Path(__file__).resolve().parent
root = folder.parents[3]
work = folder / 'Cache'
preparation = json.loads((work / 'Preparation.json').read_text())
app = adsk.core.Application.get()
report = {'fusion_version': app.version, 'scope': 'Converted Form surface cache authority: open, measure, edit, convert, save and reopen each prepared variant', 'documents_before': app.documents.count, 'rows': []}
opened = []
target = work / 'Probe.json'
grid = [index / 6 for index in range(7)]


def clean(text):
    return text.replace(str(root), '<repo>').replace(str(Path.home()), '~')


def checkpoint():
    target.write_text(clean(json.dumps(report, indent=1)) + '\n')


def xyz(point):
    return list(point.asArray())


def digest(values):
    return hashlib.sha256(json.dumps([round(value, 9) for value in values]).encode()).hexdigest()


def nurbs_data(face):
    geometry = face.geometry
    row = {'surface_type': geometry.surfaceType}
    if geometry.surfaceType == adsk.core.SurfaceTypes.NurbsSurfaceType:
        data = adsk.core.NurbsSurface.cast(geometry).getData()
        row.update({'degree': [data[1], data[2]], 'poles': [data[3], data[4]], 'knots_u': list(data[6]), 'knots_v': list(data[7]), 'pole_sha256': digest([value for point in data[5] for value in point.asArray()]), 'rational': len(data[8]) > 0})
    return row


def face_row(face):
    evaluator = face.evaluator
    ok, box = evaluator.getParameterExtents()
    row = {'area_cm2': face.area, 'extents': [box.minPoint.x, box.maxPoint.x, box.minPoint.y, box.maxPoint.y] if ok else None}
    row.update(nurbs_data(face))
    if ok:
        params = [adsk.core.Point2D.create(box.minPoint.x + (box.maxPoint.x - box.minPoint.x) * s, box.minPoint.y + (box.maxPoint.y - box.minPoint.y) * t) for s in grid for t in grid]
        ok, points = evaluator.getPointsAtParameters(params)
        row['grid_cm'] = [xyz(point) for point in points] if ok else None
    return row


def edge_row(edge):
    evaluator = edge.evaluator
    ok, start, end = evaluator.getParameterExtents()
    row = {'length_cm': edge.length, 'curve_type': edge.geometry.curveType}
    if ok:
        ok, points = evaluator.getPointsAtParameters([start + (end - start) * s for s in grid])
        row['points_cm'] = [xyz(point) for point in points] if ok else None
    return row


def solved(design):
    bodies = []
    for body in design.rootComponent.bRepBodies:
        bodies.append({
            'solid': body.isSolid,
            'faces': body.faces.count,
            'edges': body.edges.count,
            'vertices': body.vertices.count,
            'area_cm2': body.area,
            'volume_cm3': body.volume if body.isSolid else None,
            'face_rows': [face_row(face) for face in body.faces],
            'edge_rows': [edge_row(edge) for edge in body.edges],
            'vertex_cm': [xyz(vertex.geometry) for vertex in body.vertices],
        })
    forms = design.rootComponent.features.formFeatures
    timeline = [{'name': item.name, 'health': item.healthState, 'message': item.errorOrWarningMessage} for item in design.timeline]
    return {'timeline': timeline, 'forms': forms.count, 'form_health': [forms.item(index).healthState for index in range(forms.count)], 'bodies': bodies}


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


def key(point):
    return tuple(round(value, 9) for value in point.asArray())


def exercise(row):
    document = open_archive(root / row['file'])
    design = design_of(document)
    stages = row['stages']
    stages['loaded'] = solved(design)
    stages['compute_all'] = design.computeAll()
    stages['solved'] = solved(design)
    form = design.rootComponent.features.formFeatures.item(0)
    if not form.startEdit():
        raise RuntimeError('Form edit did not start')
    body = form.tSplineBodies.item(0)
    vertex = min(body.vertices, key=lambda item: key(item.geometry))
    if not vertex.move(adsk.core.Vector3D.create(.11, .07, .13)):
        raise RuntimeError('Control point edit failed')
    if not form.finishEdit():
        raise RuntimeError('Form finish failed')
    stages['edited_compute'] = design.computeAll()
    stages['edited'] = solved(design)
    saved = work / 'Saved' / (row['case'] + row['variant'] + '.f3d')
    saved.parent.mkdir(exist_ok=True)
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
        raise RuntimeError('Native save failed')
    stages['saved_sha256'] = hashlib.sha256(saved.read_bytes()).hexdigest()
    close(document)
    again = open_archive(saved)
    stages['reopened'] = solved(design_of(again))
    close(again)


try:
    for prepared in preparation['rows']:
        row = {'case': prepared['case'], 'variant': prepared['variant'], 'file': prepared['file'], 'stages': {}}
        report['rows'].append(row)
        try:
            data = (root / prepared['file']).read_bytes()
            if hashlib.sha256(data).hexdigest() != prepared['sha256']:
                raise RuntimeError('Prepared input changed')
            exercise(row)
            row['status'] = 'completed'
        except Exception:
            row['status'] = 'error'
            row['traceback'] = traceback.format_exc()
        finally:
            for document in list(opened):
                close(document)
            checkpoint()
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    for document in list(opened):
        close(document)
    report['documents_after'] = app.documents.count
    checkpoint()
