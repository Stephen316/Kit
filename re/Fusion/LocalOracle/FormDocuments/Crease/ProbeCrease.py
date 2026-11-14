import hashlib
import json
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

work = Path(__file__).resolve().parent
root = work.parents[4]
pointer = work / 'tmp' / 'Plan.txt'
app = adsk.core.Application.get()
opened = []


def clean(text):
    return text.replace(str(root), '<repo>').replace(str(Path.home()), '~')


def close(document):
    if document is not None and document.isValid:
        document.close(False)
    if document in opened:
        opened.remove(document)


def edge_rows(body):
    rows = []
    for index in range(body.edges.count):
        edge = body.edges.item(index)
        rows.append({'faces': edge.faces.count, 'length_cm': edge.length, 'tolerant': edge.isTolerant, 'tolerance_cm': edge.tolerance})
    return rows


def edit_vertex(form, move, row, tsm_target):
    if not form.startEdit():
        raise RuntimeError('Form edit did not start')
    body = form.tSplineBodies.item(0)
    near = move['near_cm']
    vertex = min(body.vertices, key=lambda item: sum((value - target) ** 2 for value, target in zip((item.geometry.x, item.geometry.y, item.geometry.z), near)))
    row['edited_vertex_cm'] = [vertex.geometry.x, vertex.geometry.y, vertex.geometry.z]
    if not vertex.move(adsk.core.Vector3D.create(*move['vector_cm'])):
        raise RuntimeError('Control point edit failed')
    try:
        tsm_target.write_text(body.getTSMDescription())
        row['edited_tsm_file'] = str(tsm_target.relative_to(root))
        row['edited_tsm_sha256'] = hashlib.sha256(tsm_target.read_bytes()).hexdigest()
    except Exception:
        row['edited_tsm_error'] = traceback.format_exc()
    if not form.finishEdit():
        raise RuntimeError('Form finish failed')


def run(cage, saved_folder):
    row = {'cage': cage['cage'], 'tsm_sha256': cage['tsm_sha256']}
    path = root / cage['tsm_file']
    if hashlib.sha256(path.read_bytes()).hexdigest() != cage['tsm_sha256']:
        raise RuntimeError('Prepared input changed')
    saved = saved_folder / (Path(cage['tsm_file']).stem + '.f3d')
    document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    opened.append(document)
    try:
        design = adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))
        form = design.rootComponent.features.formFeatures.add()
        if not form.startEdit():
            raise RuntimeError('Form edit did not start')
        if form.tSplineBodies.addByTSMFile(str(path)) is None:
            raise RuntimeError('TSM import failed')
        if not form.finishEdit():
            raise RuntimeError('Form finish failed')
        if 'edit_move' in cage:
            edit_vertex(form, cage['edit_move'], row, saved_folder / (Path(cage['tsm_file']).stem + '.edited.tsm'))
        bodies = design.rootComponent.bRepBodies
        row['bodies'] = [{'faces': body.faces.count, 'edges': body.edges.count, 'vertices': body.vertices.count, 'area_cm2': body.area, 'volume_cm3': body.volume if body.isSolid else None, 'solid': body.isSolid, 'edge_rows': edge_rows(body)} for body in bodies]
        forms = design.rootComponent.features.formFeatures
        row['form_health'] = [forms.item(index).healthState for index in range(forms.count)]
        if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
            raise RuntimeError('Native save failed')
        row['saved_file'] = str(saved.relative_to(root))
        row['saved_sha256'] = hashlib.sha256(saved.read_bytes()).hexdigest()
        row['status'] = 'completed'
    except Exception:
        row['status'] = 'error'
        row['traceback'] = traceback.format_exc()
    finally:
        close(document)
    return row


def probe(plan):
    preparation = json.loads((work / plan).read_text())
    target = work / preparation['report']
    saved_folder = work / 'tmp' / Path(plan).parent
    saved_folder.mkdir(parents=True, exist_ok=True)
    report = {'fusion_version': app.version, 'scope': preparation['scope'] + '. Fusion imports each TSM into a new Form, converts it and exports the archive to an ignored folder', 'documents_before': app.documents.count, 'cages': []}

    def checkpoint():
        target.write_text(clean(json.dumps(report, indent=1)) + '\n')

    try:
        for cage in preparation['cages']:
            report['cages'].append(run(cage, saved_folder))
            checkpoint()
        report['status'] = 'completed' if all(row['status'] == 'completed' for row in report['cages']) else 'errors'
    except Exception:
        report['status'] = 'failed'
        report['traceback'] = traceback.format_exc()
    finally:
        for document in list(opened):
            close(document)
        report['documents_after'] = app.documents.count
        checkpoint()


for plan in pointer.read_text().split():
    probe(plan)
