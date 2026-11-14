import hashlib
import json
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

folder = Path(__file__).resolve().parent
root = folder.parents[3]
work = folder / 'Saves'
work.mkdir(exist_ok=True)
app = adsk.core.Application.get()
report = {'fusion_version': app.version, 'scope': 'Repeated native saves of unchanged documents, to separate ACT record fields from stream slack', 'documents_before': app.documents.count, 'cases': []}
opened = []
target = folder / 'Probe.json'
source = root / 're/Fusion/LocalOracle/FormDocuments/Acceptance/ReemittedPlane.f3d'


def clean(text):
    return text.replace(str(root), '<repo>').replace(str(Path.home()), '~')


def checkpoint():
    target.write_text(clean(json.dumps(report, indent=2)) + '\n')


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


def save(document, name, row):
    design = design_of(document)
    path = work / (name + '.f3d')
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(path))):
        raise RuntimeError('Native save failed')
    row['saves'].append({'file': str(path.relative_to(root)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    return path


def run_case(name, opener):
    row = {'name': name, 'saves': []}
    report['cases'].append(row)
    document = None
    try:
        document = opener()
        first = save(document, name + 'First', row)
        save(document, name + 'Second', row)
        close(document)
        document = open_archive(first)
        save(document, name + 'Reopened', row)
        row['status'] = 'completed'
    except Exception:
        row['status'] = 'error'
        row['traceback'] = traceback.format_exc()
    finally:
        close(document)
        checkpoint()


def fresh():
    document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    opened.append(document)
    return document


try:
    report['source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    run_case('Fresh', fresh)
    run_case('Plane', lambda: open_archive(source))
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    for document in list(opened):
        close(document)
    report['documents_after'] = app.documents.count
    checkpoint()
