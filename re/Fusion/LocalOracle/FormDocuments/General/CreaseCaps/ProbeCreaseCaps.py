import hashlib
import json
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

folder = Path(__file__).resolve().parent
root = folder.parents[5]
work = folder
pointer = work / 'tmp' / 'Plan.txt'
plan = pointer.read_text().strip() if pointer.exists() else 'Preparation.json'
preparation = json.loads((work / plan).read_text())
target = work / preparation.get('report', 'Probe.json')
saved_folder = work / 'tmp'
saved_folder.mkdir(parents=True, exist_ok=True)
app = adsk.core.Application.get()
report = {'fusion_version': app.version, 'scope': preparation['scope'] + '. Fusion imports each TSM into a new Form, converts it and exports the archive to an ignored folder', 'documents_before': app.documents.count, 'cages': []}
opened = []


def clean(text):
    return text.replace(str(root), '<repo>').replace(str(Path.home()), '~')


def checkpoint():
    target.write_text(clean(json.dumps(report, indent=1)) + '\n')


def close(document):
    if document is not None and document.isValid:
        document.close(False)
    if document in opened:
        opened.remove(document)


def run(cage):
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
        bodies = design.rootComponent.bRepBodies
        row['bodies'] = [{'faces': body.faces.count, 'edges': body.edges.count, 'vertices': body.vertices.count, 'area_cm2': body.area, 'volume_cm3': body.volume if body.isSolid else None, 'solid': body.isSolid} for body in bodies]
        forms = design.rootComponent.features.formFeatures
        row['form_health'] = [forms.item(index).healthState for index in range(forms.count)]
        if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
            raise RuntimeError('Native save failed')
        row['saved_sha256'] = hashlib.sha256(saved.read_bytes()).hexdigest()
        row['status'] = 'completed'
    except Exception:
        row['status'] = 'error'
        row['traceback'] = traceback.format_exc()
    finally:
        close(document)
    return row


try:
    for cage in preparation['cages']:
        report['cages'].append(run(cage))
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
