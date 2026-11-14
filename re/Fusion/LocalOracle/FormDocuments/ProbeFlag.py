import hashlib
import json
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

folder = Path(__file__).resolve().parent
root = folder.parents[3]
work = folder / 'Flag'
preparation = json.loads((work / 'Preparation.json').read_text())
app = adsk.core.Application.get()
report = {'fusion_version': app.version, 'scope': preparation['scope'], 'documents_before': app.documents.count, 'rows': []}
opened = []
target = work / 'Probe.json'


def clean(text):
    return text.replace(str(root), '<repo>').replace(str(Path.home()), '~')


def checkpoint():
    target.write_text(clean(json.dumps(report, indent=1)) + '\n')


def solved(design):
    bodies = []
    for body in design.rootComponent.bRepBodies:
        faces = []
        for face in body.faces:
            data = adsk.core.NurbsSurface.cast(face.geometry).getData()
            faces.append({'area_cm2': face.area, 'counts': [data[3], data[4]], 'poles_cm': [list(point.asArray()) for point in data[5]]})
        bodies.append({'faces': body.faces.count, 'edges': body.edges.count, 'area_cm2': body.area, 'face_rows': faces, 'vertex_cm': sorted(list(vertex.geometry.asArray()) for vertex in body.vertices)})
    forms = design.rootComponent.features.formFeatures
    timeline = [{'name': item.name, 'health': item.healthState, 'message': item.errorOrWarningMessage} for item in design.timeline]
    return {'timeline': timeline, 'form_health': [forms.item(index).healthState for index in range(forms.count)], 'bodies': bodies}


def close(document):
    if document is not None and document.isValid:
        document.close(False)
    if document in opened:
        opened.remove(document)


try:
    for prepared in preparation['rows']:
        row = {'variant': prepared['variant'], 'file': prepared['file']}
        report['rows'].append(row)
        try:
            if hashlib.sha256((root / prepared['file']).read_bytes()).hexdigest() != prepared['sha256']:
                raise RuntimeError('Prepared input changed')
            document = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(root / prepared['file'])))
            if document is None:
                raise RuntimeError('Archive did not open')
            opened.append(document)
            design = adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))
            row['loaded'] = solved(design)
            row['compute_all'] = design.computeAll()
            row['solved'] = solved(design)
            form = design.rootComponent.features.formFeatures.item(0)
            if not form.startEdit():
                raise RuntimeError('Form edit did not start')
            if not form.finishEdit():
                raise RuntimeError('Form finish failed')
            row['empty_edit_compute'] = design.computeAll()
            row['empty_edit'] = solved(design)
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
