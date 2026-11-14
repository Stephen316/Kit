import hashlib
import json
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion


root = Path(__file__).resolve().parents[3]
folder = Path(__file__).resolve().parent / "RolledHistory"
folder.mkdir(exist_ok=True)
source = root / "re/Fusion/Study/timeline-5867579925b5/rolled_back.f3d"
app = adsk.core.Application.get()
original = app.activeDocument
document = None
report = {"fusion_version": app.version, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
try:
    document = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
    if document is None:
        raise RuntimeError("Rolled history control did not open")
    design = adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))
    report["marker"] = design.timeline.markerPosition
    report["timeline"] = [{"index": i.index, "name": i.name, "health": i.healthState, "message": i.errorOrWarningMessage, "type": None if i.entity is None else i.entity.objectType} for i in design.timeline]
    report["parameters"] = [{"name": p.name, "value": p.value, "expression": p.expression, "unit": p.unit} for p in design.allParameters]
    report["bodies"] = [{"name": b.name, "faces": b.faces.count, "edges": b.edges.count, "vertices": b.vertices.count, "volume_cm3": b.volume, "bounds_cm": [[b.boundingBox.minPoint.x, b.boundingBox.minPoint.y, b.boundingBox.minPoint.z],[b.boundingBox.maxPoint.x, b.boundingBox.maxPoint.y, b.boundingBox.maxPoint.z]]} for b in design.rootComponent.bRepBodies]
    report["status"] = "captured"
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
    raise
finally:
    if document is not None:
        document.close(False)
    if original is not None and original.isValid:
        original.activate()
    report["documents_after"] = app.documents.count
    (folder / "ControlObservation.json").write_text(json.dumps(report, indent=2) + "\n")
