import hashlib
import json
from pathlib import Path
import time
import traceback

import adsk.core
import adsk.fusion

folder = Path(__file__).resolve().parent
root = folder.parents[3]
work = folder / 'Stencil'
preparation = json.loads((work / 'Preparation.json').read_text())
target = work / 'Probe.json'
app = adsk.core.Application.get()
previous = json.loads(target.read_text()) if (work / 'Probe.json').exists() else {'cages': []}
earlier = {(cage['cage'], row['variant']): row for cage in previous['cages'] for row in cage['variants']}
report = {'fusion_version': app.version, 'scope': 'Fusion conversion of each prepared stencil variant: TSM import into a new Form, conversion, save to the ignored tmp folder', 'documents_before': app.documents.count, 'api': {}, 'cages': []}
opened = []
budget = time.time() + 600


def clean(text):
    return text.replace(str(root), '<repo>').replace(str(Path.home()), '~')


def checkpoint():
    target.write_text(clean(json.dumps(report, indent=1)) + '\n')


def close(document):
    if document is not None and document.isValid:
        document.close(False)
    if document in opened:
        opened.remove(document)


def new_form():
    document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    opened.append(document)
    design = adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))
    form = design.rootComponent.features.formFeatures.add()
    if not form.startEdit():
        raise RuntimeError('Form edit did not start')
    return document, design, form


def describe_api():
    document, design, form = new_form()
    bodies = form.tSplineBodies
    for name in dir(type(bodies)):
        if name.startswith(('create', 'add')):
            report['api'][name] = getattr(type(bodies), name).__doc__
    form.finishEdit()
    close(document)


def run_variant(cage, variant):
    row = {'variant': variant['variant'], 'tsm_sha256': variant['tsm_sha256']}
    path = root / variant['tsm_file']
    if hashlib.sha256(path.read_bytes()).hexdigest() != variant['tsm_sha256']:
        raise RuntimeError('Prepared input changed')
    saved = path.with_suffix('.f3d')
    prior = earlier.get((cage, variant['variant']))
    if prior is not None and prior['status'] == 'completed' and prior.get('tsm_sha256', variant['tsm_sha256']) == variant['tsm_sha256'] and saved.exists() and saved.stat().st_mtime > path.stat().st_mtime and hashlib.sha256(saved.read_bytes()).hexdigest() == prior['saved_sha256']:
        prior = dict(prior)
        prior['tsm_sha256'] = variant['tsm_sha256']
        return prior
    if time.time() > budget:
        row['status'] = 'pending'
        return row
    document, design, form = new_form()
    try:
        if form.tSplineBodies.addByTSMFile(str(path)) is None:
            raise RuntimeError('TSM import failed')
        if not form.finishEdit():
            raise RuntimeError('Form finish failed')
        bodies = design.rootComponent.bRepBodies
        row['bodies'] = [{'faces': body.faces.count, 'edges': body.edges.count, 'vertices': body.vertices.count, 'area_cm2': body.area, 'solid': body.isSolid} for body in bodies]
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
    describe_api()
    checkpoint()
    for cage in preparation['cages']:
        entry = {'cage': cage['cage'], 'variants': []}
        report['cages'].append(entry)
        for variant in cage['variants']:
            entry['variants'].append(run_variant(cage['cage'], variant))
        checkpoint()
    states = {row['status'] for cage in report['cages'] for row in cage['variants']}
    report['status'] = 'completed' if states == {'completed'} else 'partial' if states == {'completed', 'pending'} else 'errors'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    for document in list(opened):
        close(document)
    report['documents_after'] = app.documents.count
    checkpoint()
