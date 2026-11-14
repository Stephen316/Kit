import json
from pathlib import Path
import adsk.core
import adsk.fusion

app = adsk.core.Application.get()
report = {"documents_before": app.documents.count, "scope": "Close the empty unmodified Untitled document left by the failed binary-as-text import"}
if app.documents.count != 1:
    raise RuntimeError("Unexpected native document inventory")
doc = app.documents.item(0)
design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
if doc.name != "Untitled" or doc.isSaved or doc.isModified or design.rootComponent.bRepBodies.count != 0:
    raise RuntimeError("Failed-import document no longer matches its recorded empty state")
doc.close(False)
report["documents_after"] = app.documents.count
Path(__file__).resolve().parent.joinpath("Brep/FailedImportCleanup.json").write_text(json.dumps(report, indent=2) + "\n")
