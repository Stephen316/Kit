import builtins
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.modules.pop('LinkCommon', None)
import adsk.core
from LinkCommon import acceptance_folder, private, write

app = adsk.core.Application.get()
report = {'fusion_version': app.version, 'documents_before': app.documents.count, 'open_names': [app.documents.item(index).name for index in range(app.documents.count)]}
try:
    state = getattr(builtins, '_kit_link_upload', None)
    report['futures'] = None if state is None else {name: int(future.uploadState) for name, future in state.futures.items()}
    project, folder = acceptance_folder(app, subfolder='Accept2')
    rows = []
    for index in range(folder.dataFiles.count):
        item = folder.dataFiles.item(index)
        rows.append({'name': item.name, 'extension': item.fileExtension, 'version': item.versionNumber, 'complete': item.isComplete})
    report['files'] = rows
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    report['documents_after'] = app.documents.count
    write(private / 'InspectLinkUpload.json', report)
