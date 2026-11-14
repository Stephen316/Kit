import hashlib
import json
from math import isclose, pi
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion


root = Path(__file__).resolve().parent / "Features"
source = root / "kit_full_brep_19mm.f3d"
saved = root / "vendor_full_brep23mm.f3d"
app = adsk.core.Application.get()
original = app.activeDocument
doc = None
report = {"fusion_version": app.version, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "scope": "Same-source typed Design with both independently generated snapshot and solved BRep/history members, OGS graphics caches omitted; require healthy timeline and correct initial19mm geometry, roll back to sketch-only state and restore, then edit/rebuild/save/reopen; no independent full document generation"}


def observe(design):
    return {
        "parameters": [{"name": p.name, "value": p.value, "expression": p.expression} for p in design.allParameters],
        "timeline": [{"name": item.name, "type": item.entity.objectType if item.entity else None, "health": item.healthState, "message": item.errorOrWarningMessage} for item in design.timeline],
        "bodies": [{"volume_cm3": body.volume, "height_cm": body.boundingBox.maxPoint.z - body.boundingBox.minPoint.z, "faces": body.faces.count, "edges": body.edges.count, "vertices": body.vertices.count} for body in design.rootComponent.bRepBodies],
    }


def require_geometry(design, depth):
    if design.timeline.count != 2 or design.rootComponent.bRepBodies.count != 1:
        raise RuntimeError("Timeline or body count changed")
    if [item.name for item in design.timeline] != ["Radius10mm", "Kit ControlledExtrusion"]:
        raise RuntimeError("Rewritten feature names differ")
    if any(item.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState or item.errorOrWarningMessage for item in design.timeline):
        raise RuntimeError("Timeline contains a warning or error")
    body = design.rootComponent.bRepBodies.item(0)
    if not isclose(body.volume, pi * depth, rel_tol=1e-9) or not isclose(body.boundingBox.maxPoint.z, depth, rel_tol=1e-9):
        raise RuntimeError("Rebuilt extrusion geometry differs")


try:
    doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
    if doc is None:
        raise RuntimeError("Kit-written feature archive did not open")
    design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
    report["opened"] = observe(design)
    require_geometry(design, 1.9)
    design.timeline.markerPosition = 1
    report["rolled_back"] = observe(design)
    if design.rootComponent.bRepBodies.count != 0 or design.rootComponent.sketches.count != 1:
        raise RuntimeError("Rollback did not restore the sketch-only state")
    if not design.timeline.moveToEnd():
        raise RuntimeError("Could not restore the end of the native timeline")
    report["restored"] = observe(design)
    require_geometry(design, 1.9)
    if not design.computeAll():
        raise RuntimeError("Kit-written feature rebuild failed")
    report["rebuilt"] = observe(design)
    require_geometry(design, 1.9)
    design.userParameters.itemByName("depthLength").expression = "23 mm"
    if not design.computeAll():
        raise RuntimeError("Subsequent vendor parameter edit failed")
    report["edited"] = observe(design)
    require_geometry(design, 2.3)
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
        raise RuntimeError("Vendor export failed")
    doc.close(False)
    doc = None
    doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(saved)))
    design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
    if not design.computeAll():
        raise RuntimeError("Reopened feature rebuild failed")
    report["reopened"] = observe(design)
    require_geometry(design, 2.3)
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
    (root / "FullBrepAcceptance.json").write_text(json.dumps(report, indent=2) + "\n")
