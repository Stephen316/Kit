import hashlib
import json
from math import isclose
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion


root = Path(__file__).resolve().parent / "PrismSnapshot"
app = adsk.core.Application.get()
original = app.activeDocument
doc = None
report = {
    "fusion_version": app.version,
    "scope": "Complete planar cuboid/profile/sketch snapshots reconstructed from typed semantics; each archive preserves its own source non-snapshot members",
    "cases": [],
}


def checkpoint():
    (root / "NativeAcceptance.json").write_text(json.dumps(report, indent=2) + "\n")


def observe(design):
    return {
        "parameters": [{"name": p.name, "value": p.value, "expression": p.expression} for p in design.allParameters],
        "timeline": [{"name": item.name, "health": item.healthState, "message": item.errorOrWarningMessage} for item in design.timeline],
        "bodies": [{
            "volume_cm3": body.volume,
            "min_cm": [body.boundingBox.minPoint.x, body.boundingBox.minPoint.y, body.boundingBox.minPoint.z],
            "max_cm": [body.boundingBox.maxPoint.x, body.boundingBox.maxPoint.y, body.boundingBox.maxPoint.z],
            "faces": body.faces.count,
            "edges": body.edges.count,
            "vertices": body.vertices.count,
        } for body in design.rootComponent.bRepBodies],
    }


def require_geometry(design, width, depth, height):
    if design.timeline.count != 2 or design.rootComponent.bRepBodies.count != 1:
        raise RuntimeError("Timeline or body count changed")
    if any(item.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState or item.errorOrWarningMessage for item in design.timeline):
        raise RuntimeError("Timeline contains a warning or error")
    sketch = design.rootComponent.sketches.item(0)
    if sketch.profiles.count != 1 or sketch.sketchCurves.sketchLines.count != 4:
        raise RuntimeError("Planar profile or sketch selection structure differs")
    body = design.rootComponent.bRepBodies.item(0)
    bounds = body.boundingBox
    actual = (bounds.minPoint.x, bounds.minPoint.y, bounds.minPoint.z, bounds.maxPoint.x, bounds.maxPoint.y, bounds.maxPoint.z)
    expected = (0.0, 0.0, 0.0, width, depth, height)
    if not all(isclose(a, b, rel_tol=1e-9, abs_tol=1e-9) for a, b in zip(actual, expected)):
        raise RuntimeError("Cuboid bounds differ")
    if not isclose(body.volume, width * depth * height, rel_tol=1e-9):
        raise RuntimeError("Cuboid volume differs")
    if (body.faces.count, body.edges.count, body.vertices.count) != (6, 12, 8):
        raise RuntimeError("Cuboid topology counts differ")


try:
    preparation = json.loads((root / "Preparation.json").read_text())
    for source_case in preparation["cases"]:
        name = source_case["name"]
        width = source_case["geometry_mm"]["Width"] / 10
        depth = source_case["geometry_mm"]["Depth"] / 10
        height = source_case["geometry_mm"]["Height"] / 10
        edited_height = source_case["edited_height_mm"] / 10
        source = root / (name + "Snapshot.f3d")
        saved = root / ("vendor_" + name + "Edited.f3d")
        case = {"name": name, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "stage": "importing"}
        if case["source_sha256"] != source_case["output_sha256"]:
            raise RuntimeError("Prepared snapshot source digest changed")
        report["cases"].append(case)
        checkpoint()
        doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
        if doc is None:
            raise RuntimeError("Kit-written cuboid history did not open")
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        case["opened"] = observe(design)
        case["stage"] = "opened"
        checkpoint()
        require_geometry(design, width, depth, height)
        design.timeline.markerPosition = 1
        case["rolled_back"] = observe(design)
        case["stage"] = "rolled_back"
        checkpoint()
        if design.rootComponent.bRepBodies.count != 0 or design.rootComponent.sketches.count != 1:
            raise RuntimeError("Rollback did not restore the sketch-only state")
        if not design.timeline.moveToEnd():
            raise RuntimeError("Could not restore the end of the timeline")
        case["restored"] = observe(design)
        require_geometry(design, width, depth, height)
        if not design.computeAll():
            raise RuntimeError("Kit-written cuboid history rebuild failed")
        case["rebuilt"] = observe(design)
        case["stage"] = "rebuilt"
        checkpoint()
        require_geometry(design, width, depth, height)
        extent = adsk.fusion.DistanceExtentDefinition.cast(design.rootComponent.features.extrudeFeatures.item(0).extentOne)
        if extent is None:
            raise RuntimeError("Extrusion is not a distance extent")
        design.allParameters.itemByName(source_case["height_parameter"]).expression = str(source_case["edited_height_mm"]) + " mm"
        if not design.computeAll():
            raise RuntimeError("Subsequent vendor parameter edit failed")
        case["edited"] = observe(design)
        case["stage"] = "edited"
        checkpoint()
        require_geometry(design, width, depth, edited_height)
        if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
            raise RuntimeError("Vendor export failed")
        doc.close(False)
        doc = None
        doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(saved)))
        if doc is None:
            raise RuntimeError("Saved cuboid history did not reopen")
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        if not design.computeAll():
            raise RuntimeError("Reopened cuboid history rebuild failed")
        case["reopened"] = observe(design)
        case["stage"] = "reopened"
        checkpoint()
        require_geometry(design, width, depth, edited_height)
        case["saved_sha256"] = hashlib.sha256(saved.read_bytes()).hexdigest()
        case["status"] = "accepted"
        doc.close(False)
        doc = None
        checkpoint()
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
    checkpoint()
