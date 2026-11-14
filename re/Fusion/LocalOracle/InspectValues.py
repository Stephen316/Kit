import json
from pathlib import Path
import traceback

import adsk.core


root = Path(__file__).resolve().parent
app = adsk.core.Application.get()
original = app.activeDocument
doc = None
report = {}
try:
    doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(root / "Allocation/added_third.f3d")))
    for command in (
        "PEntity.Properties 203",
        'PEntity.Properties {"segId":11,"entityId":203,"rootId":""}',
        "Entity.Dump 203",
    ):
        try:
            report[command] = app.executeTextCommand(command)
        except Exception:
            report[command] = traceback.format_exc()
except Exception:
    report["traceback"] = traceback.format_exc()
finally:
    if doc is not None:
        doc.close(False)
    if original is not None and original.isValid:
        original.activate()
    (root / "Inspection/Values.json").write_text(json.dumps(report, indent=2) + "\n")
