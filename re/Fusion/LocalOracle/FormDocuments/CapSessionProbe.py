import json
import os
from pathlib import Path

import adsk.core

folder = Path(__file__).resolve().parent
root = folder.parents[3]
app = adsk.core.Application.get()
report = {
    'fusion_version': app.version,
    'oracle_process_id': os.getpid(),
    'documents_open': app.documents.count,
    'document_names': [app.documents.item(index).name for index in range(app.documents.count)],
}
target = root / 're/Fusion/LocalOracle/FormDocuments/General/CapAccept/SessionProbe.json'
target.write_text(json.dumps(report, indent=1) + '\n')
