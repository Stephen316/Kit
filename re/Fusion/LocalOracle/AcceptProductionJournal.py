import hashlib
import json
from math import isclose
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

root = Path(__file__).resolve().parents[3]
folder = Path(__file__).resolve().parent / "JournalStates"
preparation = json.loads((folder / "ProductionPreparation.json").read_text())
app = adsk.core.Application.get()
original = app.activeDocument
document = None
report = {"fusion_version": app.version, "scope": "Native comparison of complete source-specific multi-state histories emitted by production ReadJournal, EmitJournal and PermuteJournal; source-specific non-history members preserved", "cases": []}


def checkpoint():
    (folder / "NativeProductionAcceptance.json").write_text(json.dumps(report, indent=2) + "\n")


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
    for label in ("OffsetCylinder", "Draft"):
        candidates = [item for item in preparation["outputs"] if item["label"] == label]
        if len(candidates) != 2 or {item["variant"] for item in candidates} != {"Production", "ProductionPermuted"}:
            raise RuntimeError("Missing production journal acceptance variants")
        prepared = candidates[0]
        case = {"name": label, "variants": []}
        report["cases"].append(case)
        for variant, source, expected in [("Control", Path(prepared["source"]), prepared["sourceArchiveSha256"]), *[(item["variant"], root / item["target"], item["targetArchiveSha256"]) for item in candidates]]:
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            if digest != expected:
                raise RuntimeError("Prepared source changed")
            result = {"name": variant, "source_sha256": digest, "stages": {}}
            case["variants"].append(result)
            document = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
            if document is None:
                raise RuntimeError("History archive did not open")
            design = adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))
            result["stages"]["opened"] = observe(design)
            checkpoint()
            if design.timeline.count != 3 or design.timeline.markerPosition != 3 or design.rootComponent.bRepBodies.count != 1:
                raise RuntimeError("Unexpected controlled feature layout")
            design.timeline.markerPosition = 2
            result["stages"]["prior_geometry"] = observe(design)
            if design.rootComponent.bRepBodies.count != 1 or not isclose(design.rootComponent.bRepBodies.item(0).volume, 2 * 3.141592653589793, rel_tol=1e-8):
                raise RuntimeError("Archived state did not restore the original cylinder")
            design.timeline.markerPosition = 1
            result["stages"]["sketch_only"] = observe(design)
            if design.rootComponent.bRepBodies.count:
                raise RuntimeError("Initial journal state retained a solid")
            if not design.timeline.moveToEnd() or not design.computeAll():
                raise RuntimeError("Restoring full feature history failed")
            result["stages"]["restored"] = observe(design)
            design.allParameters.itemByName("d1").expression = "23 mm"
            if not design.computeAll():
                raise RuntimeError("Height edit failed")
            result["stages"]["height_edited"] = observe(design)
            parameter = design.allParameters.itemByName("d3")
            if parameter is None:
                raise RuntimeError("Expected final-feature parameter d3 is absent")
            parameter.expression = "7 deg" if label == "Draft" else "3.5 mm"
            if not design.computeAll():
                raise RuntimeError("Final-feature edit failed")
            result["stages"]["feature_edited"] = observe(design)
            saved = folder / ("vendor_ProductionJournal" + label + variant + "Edited.f3d")
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
                raise RuntimeError("Native save failed")
            document.close(False)
            document = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(saved)))
            if document is None:
                raise RuntimeError("Native saved history did not reopen")
            design = adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))
            if not design.computeAll():
                raise RuntimeError("Native reopened history did not rebuild")
            result["stages"]["reopened"] = observe(design)
            result["saved_sha256"] = hashlib.sha256(saved.read_bytes()).hexdigest()
            result["status"] = "accepted"
            document.close(False)
            document = None
            checkpoint()
        for compared in case["variants"][1:]:
            same(case["variants"][0]["stages"], compared["stages"])
        case["status"] = "accepted"
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
