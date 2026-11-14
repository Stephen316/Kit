import hashlib
import json
from math import isclose
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion


root = Path(__file__).resolve().parent
output = root / "Rewritten"
source = output / "edited_parameters.f3d"
saved = output / "vendor_rebuilt.f3d"
report = {"scope": "same-source user-parameter edit, expression rebuild and reopen", "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
app = adsk.core.Application.get()
original = app.activeDocument
doc = None


def read_values(design):
    return [{"name": p.name, "value_cm": p.value, "expression": p.expression, "comment": p.comment} for p in design.userParameters]


try:
    report["fusion_version"] = app.version
    doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
    if doc is None:
        raise RuntimeError("Kit-written archive did not open")
    design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
    report["opened"] = read_values(design)
    beta = design.userParameters.itemByName("betaLength")
    gamma = design.userParameters.itemByName("gammaLength")
    if not isclose(beta.value, 3.1) or not isclose(gamma.value, 4.7):
        raise RuntimeError("Kit-written values differ after vendor load")
    if not design.computeAll():
        raise RuntimeError("Initial rebuild failed")
    gamma.expression = "2 * betaLength"
    beta.expression = "37 mm"
    if not design.computeAll() or not isclose(gamma.value, 7.4):
        raise RuntimeError("Dependent expression did not rebuild")
    report["rebuilt"] = read_values(design)
    report["timeline_count"] = design.timeline.count
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
        raise RuntimeError("Vendor re-export failed")
    doc.close(False)
    doc = None
    doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(saved)))
    design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
    report["reopened"] = read_values(design)
    if not design.computeAll() or not isclose(design.userParameters.itemByName("gammaLength").value, 7.4):
        raise RuntimeError("Reopened dependency did not retain its value")
    report["saved_sha256"] = hashlib.sha256(saved.read_bytes()).hexdigest()
    report["status"] = "accepted"
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
    raise
finally:
    if doc is not None:
        doc.close(False)
    if original is not None and original.isValid:
        original.activate()
    (output / "Acceptance.json").write_text(json.dumps(report, indent=2) + "\n")
