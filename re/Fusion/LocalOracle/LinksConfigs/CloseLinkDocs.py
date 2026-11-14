import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.modules.pop('LinkCommon', None)
import adsk.core
from LinkCommon import private

app = adsk.core.Application.get()
owned = ('KitLink', 'KitConfig', 'KitAuthored', 'KitAsm')


def is_owned(document):
    if document.name.startswith(owned):
        return True
    if not document.name.startswith('Untitled'):
        return False
    refs = document.documentReferences
    names = [refs.item(index).dataFile.name for index in range(refs.count) if refs.item(index).dataFile]
    return bool(names) and all(name.startswith(owned) for name in names)


report = {'fusion_version': app.version, 'documents_before': app.documents.count, 'open_names': [], 'closed': []}
try:
    for index in range(app.documents.count):
        report['open_names'].append(app.documents.item(index).name)
    documents = [app.documents.item(index) for index in range(app.documents.count)]
    documents.sort(key=lambda document: not document.name.startswith('Untitled'))
    for document in documents:
        if document.isValid and is_owned(document):
            document.close(False)
            report['closed'].append(document.name)
except Exception:
    report['traceback'] = traceback.format_exc()
finally:
    report['documents_after'] = app.documents.count
    (private / 'CloseLinkDocs.json').write_text(json.dumps(report, indent=2) + '\n')
