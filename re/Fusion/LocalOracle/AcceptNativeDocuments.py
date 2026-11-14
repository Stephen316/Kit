import hashlib
import json
from math import isclose
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

root = Path(__file__).resolve().parents[3]
folder = Path(__file__).resolve().parent / "NativeDocuments"
preparation = json.loads((folder / "Preparation.json").read_text())
app = adsk.core.Application.get()
original = app.activeDocument
document = None
report = {"fusion_version": app.version, "scope": "Complete native ReadDocument→EmitParsed reconstruction: entity graphs, history, snapshots, materials, configurations and graphics; original preview image parts retained", "cases": []}


def checkpoint():
    (folder / "NativeAcceptance.json").write_text(json.dumps(report, indent=2) + "\n")


def observe(design):
    bodies = []
    for body in design.rootComponent.bRepBodies:
        props = body.physicalProperties
        colors = []
        for prop in body.appearance.appearanceProperties:
            color_prop = adsk.core.ColorProperty.cast(prop)
            if color_prop is not None and color_prop.value is not None:
                color = color_prop.value
                colors.append({"id": prop.id, "rgba": [color.red, color.green, color.blue, color.opacity]})
        bodies.append({"name": body.name, "volume_cm3": body.volume, "area_cm2": props.area, "mass_kg": props.mass, "density_kg_per_cm3": props.density, "center_cm": props.centerOfMass.asArray(), "inertia_kg_cm2": props.getXYZMomentsOfInertia(), "bounds_cm": [body.boundingBox.minPoint.asArray(), body.boundingBox.maxPoint.asArray()], "material": body.material.name, "appearance": body.appearance.name, "colors": sorted(colors, key=lambda item: item["id"]), "faces": body.faces.count, "edges": body.edges.count, "vertices": body.vertices.count})
    return {"marker": design.timeline.markerPosition, "parameters": [{"name": p.name, "value": p.value, "expression": p.expression} for p in design.allParameters], "timeline": [{"name": item.name, "health": item.healthState, "message": item.errorOrWarningMessage} for item in design.timeline], "sketches": [{"name": sketch.name, "profiles": sketch.profiles.count, "lines": sketch.sketchCurves.sketchLines.count, "dimensions": sketch.sketchDimensions.count, "fully_constrained": sketch.isFullyConstrained} for sketch in design.rootComponent.sketches], "bodies": bodies}


def require(design, width, depth, height):
    if design.timeline.count != 2 or design.rootComponent.bRepBodies.count != 1 or design.rootComponent.sketches.count != 1:
        raise RuntimeError("Complete native document structure differs")
    if any(item.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState or item.errorOrWarningMessage for item in design.timeline):
        raise RuntimeError("Complete native document has an unhealthy feature")
    body = design.rootComponent.bRepBodies.item(0)
    if (body.faces.count, body.edges.count, body.vertices.count) != (6, 12, 8):
        raise RuntimeError("Native cuboid topology differs")
    if not isclose(body.volume, width * depth * height, rel_tol=1e-8):
        raise RuntimeError("Native cuboid volume differs")
    if not all(isclose(a, b, rel_tol=1e-8, abs_tol=1e-8) for a, b in zip((*body.boundingBox.minPoint.asArray(), *body.boundingBox.maxPoint.asArray()), (0, 0, 0, width, depth, height))):
        raise RuntimeError("Native cuboid bounds differ")


def same(left, right, path="state"):
    if isinstance(left, float) and isinstance(right, (float, int)):
        if not isclose(left, right, rel_tol=1e-8, abs_tol=1e-8):
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


try:
    for prepared in preparation["cases"]:
        name = prepared["name"]
        width, depth, height = [prepared["geometry_mm"][key] / 10 for key in ("Width", "Depth", "Height")]
        edited = prepared["edited_height_mm"] / 10
        case = {"name": name, "variants": []}
        report["cases"].append(case)
        for variant, source, expected in [("Control", root / prepared["source"], prepared["source_sha256"]), ("Reemitted", root / prepared["output_file"], prepared["output_sha256"])]:
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            if digest != expected:
                raise RuntimeError("Prepared complete document changed")
            result = {"name": variant, "source_sha256": digest, "stages": {}}
            case["variants"].append(result)
            document = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
            if document is None:
                raise RuntimeError("Complete native document did not open")
            design = adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))
            result["stages"]["opened"] = observe(design)
            checkpoint()
            require(design, width, depth, height)
            design.timeline.markerPosition = 1
            result["stages"]["rollback"] = observe(design)
            if design.rootComponent.bRepBodies.count:
                raise RuntimeError("Complete document rollback retained a solid")
            if not design.timeline.moveToEnd() or not design.computeAll():
                raise RuntimeError("Complete document restoration failed")
            result["stages"]["rebuilt"] = observe(design)
            require(design, width, depth, height)
            design.allParameters.itemByName(prepared["height_parameter"]).expression = str(prepared["edited_height_mm"]) + " mm"
            if not design.computeAll():
                raise RuntimeError("Complete document height edit failed")
            result["stages"]["edited"] = observe(design)
            require(design, width, depth, edited)
            saved = folder / ("vendor_" + name + variant + "Edited.f3d")
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
                raise RuntimeError("Complete document save failed")
            document.close(False)
            document = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(saved)))
            if document is None:
                raise RuntimeError("Complete document saved file did not reopen")
            design = adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))
            if not design.computeAll():
                raise RuntimeError("Complete document saved file did not rebuild")
            result["stages"]["reopened"] = observe(design)
            require(design, width, depth, edited)
            result["saved_sha256"] = hashlib.sha256(saved.read_bytes()).hexdigest()
            result["status"] = "accepted"
            document.close(False)
            document = None
            checkpoint()
        same(case["variants"][0]["stages"], case["variants"][1]["stages"])
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
