import hashlib
import json
from math import isclose
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

root = Path(__file__).resolve().parents[3]
folder = Path(__file__).resolve().parent / "ReaderCoverage"
preparation = json.loads((folder / "Preparation.json").read_text())
app = adsk.core.Application.get()
original = app.activeDocument
document = None
report = {"fusion_version": app.version, "scope": "Native control comparison of Fusion-saved documents re-emitted by ReadDocument then EmitParsed after saved-class, matrix, primitive, entity-id, typed-fallback and directory qualification; components compare by name and their native enumeration order is recorded without comparison", "cases": []}


def checkpoint():
    (folder / "NativeAcceptance.json").write_text(json.dumps(report, indent=2) + "\n")


def parametric(design):
    return design.designType == adsk.fusion.DesignTypes.ParametricDesignType


def observe(design):
    components = []
    for component in design.allComponents:
        bodies = []
        for body in component.bRepBodies:
            box = body.boundingBox
            bodies.append({"name": body.name, "solid": body.isSolid, "visible": body.isVisible, "faces": body.faces.count, "edges": body.edges.count, "vertices": body.vertices.count, "volume_cm3": body.volume, "area_cm2": body.area, "bounds_cm": [box.minPoint.asArray(), box.maxPoint.asArray()]})
        sketches = [{"name": sketch.name, "curves": sketch.sketchCurves.count, "profiles": sketch.profiles.count, "dimensions": sketch.sketchDimensions.count} for sketch in component.sketches]
        components.append({"name": component.name, "bodies": bodies, "sketches": sketches, "meshes": component.meshBodies.count, "occurrences": component.occurrences.count, "planes": component.constructionPlanes.count, "axes": component.constructionAxes.count})
    state = {"design_type": design.designType, "root": design.rootComponent.name, "components": sorted(components, key=lambda item: json.dumps(item, sort_keys=True)), "occurrences": design.rootComponent.allOccurrences.count}
    if parametric(design):
        state["parameters"] = [{"name": p.name, "value": p.value, "expression": p.expression, "unit": p.unit} for p in design.allParameters]
        state["marker"] = design.timeline.markerPosition
        state["timeline"] = [{"name": item.name, "health": item.healthState, "message": item.errorOrWarningMessage, "group": item.isGroup, "suppressed": item.isSuppressed} for item in design.timeline]
    return state


def same(left, right, path="state"):
    if isinstance(left, float) and isinstance(right, (float, int)):
        if not isclose(left, right, rel_tol=1e-8, abs_tol=1e-9):
            raise RuntimeError(f"Native control mismatch at {path}: {left} != {right}")
    elif isinstance(left, dict) and isinstance(right, dict):
        if left.keys() != right.keys():
            raise RuntimeError(f"Native control keys differ at {path}")
        for key in left:
            same(left[key], right[key], path + "." + str(key))
    elif isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        if len(left) != len(right):
            raise RuntimeError(f"Native control lengths differ at {path}")
        for index, (a, b) in enumerate(zip(left, right)):
            same(a, b, path + "." + str(index))
    elif left != right:
        raise RuntimeError(f"Native control value differs at {path}: {left!r} != {right!r}")


def openDesign(path):
    opened = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(path)))
    if opened is None:
        raise RuntimeError("Archive did not open")
    design = adsk.fusion.Design.cast(opened.products.itemByProductType("DesignProductType"))
    if design is None:
        opened.close(False)
        raise RuntimeError("Archive has no design product")
    return opened, design


def order(design):
    return [component.name for component in design.allComponents]


def exercise(label, variant, source, expected):
    global document
    data = source.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected:
        raise RuntimeError("Prepared source changed")
    result = {"name": variant, "source_sha256": digest, "stages": {}, "component_order": {}}
    document, design = openDesign(source)
    result["stages"]["opened"] = observe(design)
    result["component_order"]["opened"] = order(design)
    if not design.computeAll():
        raise RuntimeError("Opened design did not rebuild")
    result["stages"]["rebuilt"] = observe(design)
    if parametric(design) and design.timeline.count:
        marker = design.timeline.markerPosition
        design.timeline.markerPosition = 0
        result["stages"]["rolled_back"] = observe(design)
        design.timeline.markerPosition = marker
        if not design.computeAll():
            raise RuntimeError("Restored marker did not rebuild")
        result["stages"]["restored"] = observe(design)
    saved = folder / ("vendor_" + label + variant + "Saved.f3d")
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
        raise RuntimeError("Native save failed")
    document.close(False)
    document = None
    document, design = openDesign(saved)
    if not design.computeAll():
        raise RuntimeError("Reopened design did not rebuild")
    result["stages"]["reopened"] = observe(design)
    result["component_order"]["reopened"] = order(design)
    result["saved"] = str(saved.relative_to(root))
    result["saved_sha256"] = hashlib.sha256(saved.read_bytes()).hexdigest()
    result["status"] = "accepted"
    document.close(False)
    document = None
    return result


try:
    for prepared in preparation["cases"]:
        label = prepared["label"]
        case = {"name": label, "covers": prepared["covers"], "source": prepared["source"], "output": prepared["output"], "output_sha256": prepared["output_sha256"], "variants": []}
        report["cases"].append(case)
        try:
            case["variants"].append(exercise(label, "Control", root / prepared["source"], prepared["source_sha256"]))
            checkpoint()
            case["variants"].append(exercise(label, "Reemitted", root / prepared["output"], prepared["output_sha256"]))
            same(case["variants"][0]["stages"], case["variants"][1]["stages"])
            case["status"] = "accepted"
        except Exception:
            case["status"] = "failed"
            case["traceback"] = traceback.format_exc()
            if document is not None:
                document.close(False)
                document = None
        checkpoint()
    report["status"] = "accepted" if all(case["status"] == "accepted" for case in report["cases"]) else "failed"
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
