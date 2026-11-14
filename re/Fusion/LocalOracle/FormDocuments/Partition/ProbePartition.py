import hashlib
import json
from pathlib import Path
import time
import traceback

import adsk.core
import adsk.fusion

work = Path(__file__).resolve().parent
root = work.parents[4]
round_name = (work / 'tmp' / 'Plan.txt').read_text().strip()
plan = json.loads((work / round_name / 'Preparation.json').read_text())
target = work / round_name / 'Probe.json'
app = adsk.core.Application.get()
previous = json.loads(target.read_text()) if target.exists() else {'variants': []}
earlier = {row['variant']: row for row in previous['variants']}
report = {'fusion_version': app.version, 'scope': 'Fusion conversion of each prepared partition variant: TSM import into a new Form, conversion, save to the ignored tmp folder', 'round': round_name, 'documents_before': app.documents.count, 'variants': []}
opened = []
budget = time.time() + 500


def clean(text):
    return text.replace(str(root), '<repo>').replace(str(Path.home()), '~')


def checkpoint():
    target.write_text(clean(json.dumps(report, indent=1)) + '\n')


def close(document):
    if document is not None and document.isValid:
        document.close(False)
    if document in opened:
        opened.remove(document)


def run_variant(variant):
    row = {'variant': variant['variant'], 'tsm_sha256': variant['tsm_sha256']}
    path = root / variant['tsm_file']
    if hashlib.sha256(path.read_bytes()).hexdigest() != variant['tsm_sha256']:
        raise RuntimeError('Prepared input changed')
    saved = path.with_suffix('.f3d')
    prior = earlier.get(variant['variant'])
    if prior is not None and prior['status'] == 'completed' and prior['tsm_sha256'] == variant['tsm_sha256'] and saved.exists() and hashlib.sha256(saved.read_bytes()).hexdigest() == prior['saved_sha256']:
        return prior
    if time.time() > budget:
        row['status'] = 'pending'
        return row
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
        row['bodies'] = [{'faces': body.faces.count, 'edges': body.edges.count, 'vertices': body.vertices.count} for body in bodies]
        if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
            raise RuntimeError('Native save failed')
        row['saved_sha256'] = hashlib.sha256(saved.read_bytes()).hexdigest()
        row['status'] = 'completed'
    except Exception:
        row['status'] = 'error'
        row['traceback'] = clean(traceback.format_exc())
    finally:
        close(document)
    return row


try:
    for variant in plan['variants']:
        report['variants'].append(run_variant(variant))
        checkpoint()
    states = {row['status'] for row in report['variants']}
    report['status'] = 'completed' if states == {'completed'} else 'partial' if states <= {'completed', 'pending'} else 'errors'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = clean(traceback.format_exc())
finally:
    for document in list(opened):
        close(document)
    report['documents_after'] = app.documents.count
    checkpoint()
