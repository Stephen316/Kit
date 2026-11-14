import hashlib
import json
from math import isclose, pi
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion


root = Path(__file__).resolve().parent / "Brep"
source = root / "kit_cylinder_15r_11h.smt"
saved = root / "vendor_kit_cylinder.f3d"
app = adsk.core.Application.get()
original = app.activeDocument
doc = None
report = {"fusion_version": app.version, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "scope": "Independent generated SMT cylinder import, geometry inspection, native save and reopen; no parametric feature history is generated"}


def inspect(design):
    if design.rootComponent.bRepBodies.count != 1:
        raise RuntimeError("Expected one imported cylinder body")
    body = design.rootComponent.bRepBodies.item(0)
    box = body.boundingBox
    center = body.physicalProperties.centerOfMass
    observed = {"is_solid": body.isSolid, "faces": body.faces.count, "edges": body.edges.count, "vertices": body.vertices.count, "volume_cm3": body.volume, "center_cm": center.asArray(), "min_cm": box.minPoint.asArray(), "max_cm": box.maxPoint.asArray()}
    if not body.isSolid or (body.faces.count, body.edges.count, body.vertices.count) != (3, 2, 2):
        raise RuntimeError("Generated cylinder topology differs")
    if not isclose(body.volume, pi * 1.5 ** 2 * 1.1, rel_tol=1e-8):
        raise RuntimeError("Generated cylinder volume differs")
    for name, expected in (("center_cm", (2.0, -3.0, 1.05)), ("min_cm", (0.5, -4.5, 0.5)), ("max_cm", (3.5, -1.5, 1.6))):
        if not all(isclose(a, b, rel_tol=1e-8, abs_tol=1e-8) for a, b in zip(observed[name], expected)):
            raise RuntimeError("Generated cylinder spatial extent differs: " + name)
    return observed


try:
    doc = app.importManager.importToNewDocument(app.importManager.createSMTImportOptions(str(source)))
    if doc is None:
        raise RuntimeError("Generated SMT did not open")
    design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
    report["opened"] = inspect(design)
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
        raise RuntimeError("Native imported geometry export failed")
    doc.close(False)
    doc = None
    doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(saved)))
    design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
    report["reopened"] = inspect(design)
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
    report["documents_after"] = app.documents.count
    (root / "Acceptance.json").write_text(json.dumps(report, indent=2) + "\n")
