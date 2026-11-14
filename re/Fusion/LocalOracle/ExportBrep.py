import hashlib
import json
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion


root = Path(__file__).resolve().parent
output = root / "Brep"
output.mkdir(exist_ok=True)
source = root / "Features/extrude_07mm.f3d"
app = adsk.core.Application.get()
original = app.activeDocument
doc = None
report = {"fusion_version": app.version, "source": "Features/extrude_07mm.f3d", "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "exports": []}
try:
    doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
    if doc is None:
        raise RuntimeError("Native control import failed")
    design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
    for extension, create in (("smt", design.exportManager.createSMTExportOptions), ("sat", design.exportManager.createSATExportOptions)):
        target = output / ("cylinder_07mm." + extension)
        if not design.exportManager.execute(create(str(target), design.rootComponent)):
            raise RuntimeError("Native geometry export failed: " + extension)
        report["exports"].append({"file": target.name, "bytes": target.stat().st_size, "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
    body = design.rootComponent.bRepBodies.item(0)
    report["geometry"] = {"volume_cm3": body.volume, "faces": body.faces.count, "edges": body.edges.count, "vertices": body.vertices.count, "minimum_cm": body.boundingBox.minPoint.asArray(), "maximum_cm": body.boundingBox.maxPoint.asArray()}
    report["status"] = "exported"
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
    raise
finally:
    if doc is not None:
        doc.close(False)
    if original is not None and original.isValid:
        original.activate()
    report["documents_after"] = app.documents.count
    (output / "Export.json").write_text(json.dumps(report, indent=2) + "\n")
