import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.modules.pop('LinkCommon', None)
import adsk.core
from LinkCommon import private

app = adsk.core.Application.get()
report = {'fusion_version': app.version, 'documents_before': app.documents.count, 'open_names': [app.documents.item(index).name for index in range(app.documents.count)]}
report['documents_after'] = app.documents.count
(private / 'NoteState.json').write_text(json.dumps(report, indent=2) + '\n')
