import json
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion


root = Path(__file__).resolve().parent
output = root / "Inspection"
output.mkdir(exist_ok=True)
report = {}
app = adsk.core.Application.get()
original = app.activeDocument
doc = None
try:
    options = app.importManager.createFusionArchiveImportOptions(str(root / "Allocation/added_third.f3d"))
    doc = app.importManager.importToNewDocument(options)
    if doc is None:
        raise RuntimeError("Archive import did not create a document")
    design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
    report["fusion_version"] = app.version
    report["compute_all"] = design.computeAll()
    report["parameters"] = [{"name": p.name, "value": p.value, "expression": p.expression} for p in design.allParameters]
    report["entity_ids"] = app.executeTextCommand("PAsset.EntityIds")
    report["segment_save"] = app.executeTextCommand('Segment.Save "' + str(output / "Design.xml") + '"')
    report["status"] = "inspected"
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
    raise
finally:
    if doc is not None:
        doc.close(False)
    if original is not None and original.isValid:
        original.activate()
    (output / "Inspection.json").write_text(json.dumps(report, indent=2) + "\n")
