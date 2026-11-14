import hashlib
import json
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

folder = Path(__file__).resolve().parent
root = folder.parents[3]
work = folder / 'Sourceless' / 'Variants'
plan = json.loads((work / 'Variants.json').read_text())
app = adsk.core.Application.get()
report = {
    'fusion_version': app.version,
    'scope': 'Body count and solidity of one-field Form document variants before and after computeAll',
    'documents_before': app.documents.count,
    'cases': [],
}
opened = []
target = work / 'ProbeVariants.json'


def clean(text):
    return text.replace(str(root), '<repo>').replace(str(Path.home()), '~')


def checkpoint():
    target.write_text(clean(json.dumps(report, indent=1)) + '\n')


def bodies(design):
    rows = []
    for body in design.rootComponent.bRepBodies:
        rows.append({'solid': body.isSolid, 'faces': body.faces.count, 'area_cm2': body.area, 'volume_cm3': body.volume if body.isSolid else None})
    timeline = [item.healthState for item in design.timeline]
    forms = design.rootComponent.features.formFeatures
    return {'bodies': rows, 'timeline_health': timeline, 'form_health': [forms.item(index).healthState for index in range(forms.count)]}


def close(document):
    if document is not None and document.isValid:
        document.close(False)
    if document in opened:
        opened.remove(document)


def run(row):
    case = {'case': row['case']}
    report['cases'].append(case)
    path = root / row['document_file']
    if hashlib.sha256(path.read_bytes()).hexdigest() != row['document_sha256']:
        raise RuntimeError('Variant changed')
    document = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(path)))
    opened.append(document)
    design = adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))
    case['loaded'] = bodies(design)
    case['compute_all'] = design.computeAll()
    case['solved'] = bodies(design)
    close(document)


try:
    for row in plan['rows']:
        try:
            run(row)
        except Exception:
            report['cases'][-1]['traceback'] = traceback.format_exc()
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
