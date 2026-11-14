import hashlib
import json
from math import isclose
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

folder = Path(__file__).resolve().parent / "RolledHistory"
preparation = json.loads((folder / "Preparation.json").read_text())
app = adsk.core.Application.get()
original = app.activeDocument
document = None
report = {"fusion_version": app.version, "scope": "Native source/control comparison for complete reconstructed rolled-back history, preserving other source members", "cases": []}


def checkpoint():
    (folder / "NativeAcceptance.json").write_text(json.dumps(report, indent=2) + "\n")


def observe(design):
    return {"marker": design.timeline.markerPosition, "parameters": [{"name": p.name, "value": p.value, "expression": p.expression, "unit": p.unit} for p in design.allParameters], "timeline": [{"name": item.name, "health": item.healthState, "message": item.errorOrWarningMessage, "group": item.isGroup} for item in design.timeline], "bodies": [{"name": body.name, "faces": body.faces.count, "edges": body.edges.count, "vertices": body.vertices.count, "volume_cm3": body.volume, "area_cm2": body.area, "bounds_cm": [[body.boundingBox.minPoint.x, body.boundingBox.minPoint.y, body.boundingBox.minPoint.z], [body.boundingBox.maxPoint.x, body.boundingBox.maxPoint.y, body.boundingBox.maxPoint.z]]} for body in design.rootComponent.bRepBodies]}


def same(left, right, path="state"):
    if isinstance(left, float) and isinstance(right, (float, int)):
        if not isclose(left, right, rel_tol=1e-8, abs_tol=1e-9):
            raise RuntimeError(f"Native control mismatch at {path}: {left} != {right}")
    elif isinstance(left, dict) and isinstance(right, dict):
        if left.keys() != right.keys():
            raise RuntimeError(f"Native control keys differ at {path}")
        for key in left:
            same(left[key], right[key], path + "." + str(key))
    elif isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            raise RuntimeError(f"Native control lengths differ at {path}")
        for index, (a, b) in enumerate(zip(left, right)):
            same(a, b, path + "." + str(index))
    elif left != right:
        raise RuntimeError(f"Native control value differs at {path}: {left!r} != {right!r}")


try:
    for name, source in [("Control", Path(preparation["source"])), ("Reemitted", Path(preparation["output"]))]:
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        expected = preparation["source_sha256" if name == "Control" else "output_sha256"]
        if digest != expected:
            raise RuntimeError("Prepared history source changed")
        case = {"name": name, "source_sha256": digest, "stages": {}}
        report["cases"].append(case)
        document = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
        if document is None:
            raise RuntimeError("History archive did not open")
        design = adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))
        case["stages"]["opened"] = observe(design)
        if design.timeline.markerPosition != 2 or design.rootComponent.bRepBodies.count != 1:
            raise RuntimeError("Rolled-back source marker was not preserved")
        checkpoint()
        design.timeline.markerPosition = 1
        case["stages"]["rollback"] = observe(design)
        if design.rootComponent.bRepBodies.count:
            raise RuntimeError("Rollback did not return to the sketch")
        design.timeline.markerPosition = 2
        if not design.computeAll():
            raise RuntimeError("Rebuilding rolled-back state failed")
        case["stages"]["restored"] = observe(design)
        if not design.timeline.moveToEnd() or not design.computeAll():
            raise RuntimeError("Restoring future features failed")
        case["stages"]["end"] = observe(design)
        design.allParameters.itemByName("d1").expression = "13 mm"
        if not design.computeAll():
            raise RuntimeError("History parameter edit failed")
        case["stages"]["edited"] = observe(design)
        saved = folder / ("vendor_" + name + "Edited.f3d")
        if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
            raise RuntimeError("Native save failed")
        document.close(False)
        document = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(saved)))
        if document is None:
            raise RuntimeError("Native saved history did not reopen")
        design = adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))
        if not design.computeAll():
            raise RuntimeError("Native reopened history did not rebuild")
        case["stages"]["reopened"] = observe(design)
        case["saved_sha256"] = hashlib.sha256(saved.read_bytes()).hexdigest()
        case["status"] = "accepted"
        document.close(False)
        document = None
        checkpoint()
    same(report["cases"][0]["stages"], report["cases"][1]["stages"])
    report["status"] = "accepted"
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
    checkpoint()
