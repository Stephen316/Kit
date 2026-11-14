import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.modules.pop('LinkCommon', None)
import adsk.core
from LinkCommon import acceptance_folder, design_of, export_f3d, private, pump, write

author = private / 'author'
plan = json.loads((author / 'Accept.json').read_text())
app = adsk.core.Application.get()
report = {'fusion_version': app.version, 'run': plan['run'], 'documents_before': app.documents.count, 'exports': []}
before = [app.documents.item(index) for index in range(app.documents.count)]
out_path = private / 'ReexportAsmRoot.json'


def find_file(folder, name):
    for index in range(folder.dataFiles.count):
        item = folder.dataFiles.item(index)
        if item.name == name:
            return item
    return None


def close_new():
    for doc in [app.documents.item(index) for index in range(app.documents.count)]:
        if doc.isValid and not any(doc == old for old in before):
            doc.close(False)


try:
    project, folder = acceptance_folder(app, subfolder=plan['run'])
    root_file = find_file(folder, plan['root'])
    report['root_version'] = root_file.versionNumber
    doc = app.documents.open(root_file, True)
    refs = doc.documentReferences
    pump(lambda: all(refs.item(index).dataFile is not None for index in range(refs.count)), 180)
    design = design_of(doc)
    for label in ('First', 'Second'):
        report['exports'].append({label: export_f3d(design, author / ('Reexport' + label + 'KitAsmRoot.f3d'))})
    doc.close(False)
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    try:
        close_new()
    except Exception:
        report.setdefault('close_errors', []).append(traceback.format_exc())
    report['documents_after'] = app.documents.count
    write(out_path, report)
