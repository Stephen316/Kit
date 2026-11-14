import hashlib
import json
from math import hypot, isclose, pi, radians, tan
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

folder = Path(__file__).resolve().parent / "PublicAdapter"
preparation = json.loads((folder / "Preparation.json").read_text())
app = adsk.core.Application.get()
original = app.activeDocument
document = None
report = {"fusion_version": app.version, "scope": "Complete public writer→strict reader→neutral JSON→writer artifacts, independently authored with no carrier; native load, edits, rollback/rebuild and save/reopen", "cases": []}


def checkpoint():
    (folder / "NativeAcceptance.json").write_text(json.dumps(report, indent=2) + "\n")


def observe(design):
    sketches = []
    for sketch in design.rootComponent.sketches:
        sketches.append({"name": sketch.name, "fully_constrained": sketch.isFullyConstrained, "profiles": sketch.profiles.count, "dimensions": [{"name": dim.parameter.name, "expression": dim.parameter.expression, "value": dim.parameter.value} for dim in sketch.sketchDimensions], "circles": [{"center_cm": curve.centerSketchPoint.geometry.asArray(), "radius_cm": curve.radius} for curve in sketch.sketchCurves.sketchCircles], "lines": [{"start_cm": curve.startSketchPoint.geometry.asArray(), "end_cm": curve.endSketchPoint.geometry.asArray()} for curve in sketch.sketchCurves.sketchLines]})
    bodies = []
    for body in design.rootComponent.bRepBodies:
        color = adsk.core.ColorProperty.cast(body.appearance.appearanceProperties.itemById("metal_f0")).value
        props = body.physicalProperties
        bodies.append({"name": body.name, "volume_cm3": body.volume, "area_cm2": props.area, "mass_kg": props.mass, "density_kg_per_cm3": props.density, "center_cm": props.centerOfMass.asArray(), "min_cm": body.boundingBox.minPoint.asArray(), "max_cm": body.boundingBox.maxPoint.asArray(), "material": body.material.name, "color_rgba": [color.red, color.green, color.blue, color.opacity], "faces": body.faces.count, "edges": body.edges.count, "vertices": body.vertices.count})
    return {"parameters": [{"name": p.name, "value": p.value, "expression": p.expression} for p in design.allParameters], "timeline": [{"name": item.name, "health": item.healthState, "message": item.errorOrWarningMessage} for item in design.timeline], "sketches": sketches, "bodies": bodies}


def require(design, kind, height, width, depth, radius, angle):
    solid = kind in ("extrusion", "cuboid", "frustum")
    count = 0 if kind == "parameter" else 2 if solid else 1
    if design.timeline.count != count or design.rootComponent.bRepBodies.count != int(solid) or design.rootComponent.sketches.count != int(kind != "parameter"):
        raise RuntimeError("Public profile document structure differs")
    if any(item.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState or item.errorOrWarningMessage for item in design.timeline):
        raise RuntimeError("Public profile has an unhealthy feature")
    if not isclose(design.userParameters.itemByName("publicHeight").value, height, rel_tol=1e-9):
        raise RuntimeError("Public height parameter differs")
    if kind != "parameter":
        sketch = design.rootComponent.sketches.item(0)
        if sketch.profiles.count != 1:
            raise RuntimeError("Public profile is not closed")
        if kind in ("rectangle", "cuboid"):
            if not sketch.isFullyConstrained or sketch.geometricConstraints.count != 4 or sketch.sketchDimensions.count != 2:
                raise RuntimeError("Public rectangle is not fully constrained")
            points = [point for line in sketch.sketchCurves.sketchLines for point in (line.startSketchPoint, line.endSketchPoint)]
            actual = {(round(p.geometry.x, 8), round(p.geometry.y, 8), round(p.geometry.z, 8)) for p in points}
            if actual != {(0, 0, 0), (width, 0, 0), (width, depth, 0), (0, depth, 0)}:
                raise RuntimeError("Public rectangle corners differ")
        elif sketch.sketchCurves.sketchCircles.count != 1 or not isclose(sketch.sketchCurves.sketchCircles.item(0).radius, radius, rel_tol=1e-9):
            raise RuntimeError("Public circle radius differs")
    if not solid:
        return
    if kind == "cuboid":
        volume = width * depth * height
        area = 2 * (width * depth + width * height + depth * height)
        center = (width / 2, depth / 2, height / 2)
        bounds = (0, 0, 0, width, depth, height)
        topology = (6, 12, 8)
    else:
        upper = radius + height * tan(radians(angle))
        quadratic = radius * radius + radius * upper + upper * upper
        volume = pi * height * quadratic / 3
        area = pi * (radius * radius + upper * upper + (radius + upper) * hypot(height, upper - radius))
        center = (0, 0, height * (radius * radius + 2 * radius * upper + 3 * upper * upper) / (4 * quadratic))
        extent = max(radius, upper)
        bounds = (-extent, -extent, 0, extent, extent, height)
        topology = (3, 2, 2)
    body = design.rootComponent.bRepBodies.item(0)
    props = body.physicalProperties
    pairs = [(body.volume, volume), (props.area, area), (props.density, 0.00287), (props.mass, volume * 0.00287), *zip(props.centerOfMass.asArray(), center), *zip((*body.boundingBox.minPoint.asArray(), *body.boundingBox.maxPoint.asArray()), bounds)]
    if not all(isclose(a, b, rel_tol=1e-8, abs_tol=1e-8) for a, b in pairs) or (body.faces.count, body.edges.count, body.vertices.count) != topology or body.material.name != "Public Material":
        raise RuntimeError("Public solid geometry, mass or material differs")
    color = adsk.core.ColorProperty.cast(body.appearance.appearanceProperties.itemById("metal_f0")).value
    if (color.red, color.green, color.blue, color.opacity) != (51, 102, 153, 255):
        raise RuntimeError("Public appearance color differs")


try:
    for prepared in preparation:
        kind = prepared["kind"]
        source = Path(prepared["reemit"])
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if digest != prepared["reemitSha256"] or digest != prepared["sha256"]:
            raise RuntimeError("Public re-emission digest differs")
        case = {"kind": kind, "source_sha256": digest, "stages": {}}
        report["cases"].append(case)
        document = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
        if document is None:
            raise RuntimeError("Public adapter archive did not open")
        design = adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))
        height, width, depth, radius, angle = 1.7, 1.9, 2.3, 1.2, 5 if kind == "frustum" else 0
        case["stages"]["opened"] = observe(design)
        checkpoint()
        require(design, kind, height, width, depth, radius, angle)
        if kind in ("extrusion", "cuboid", "frustum"):
            design.timeline.markerPosition = 1
            case["stages"]["rollback"] = observe(design)
            if design.rootComponent.bRepBodies.count:
                raise RuntimeError("Public solid rollback retained geometry")
            if not design.timeline.moveToEnd():
                raise RuntimeError("Public solid restoration failed")
        if not design.computeAll():
            raise RuntimeError("Public profile rebuild failed")
        case["stages"]["rebuilt"] = observe(design)
        require(design, kind, height, width, depth, radius, angle)
        design.userParameters.itemByName("publicHeight").expression = "21 mm"
        height = 2.1
        if kind in ("rectangle", "cuboid"):
            design.userParameters.itemByName("rectangleWidth").expression = "22 mm"
            design.userParameters.itemByName("rectangleDepth").expression = "29 mm"
            width, depth = 2.2, 2.9
        elif kind == "circle":
            design.rootComponent.sketches.item(0).sketchCurves.sketchCircles.item(0).radius = 1.4
            radius = 1.4
        elif kind == "frustum":
            design.allParameters.itemByName("d3").expression = "-3 deg"
            angle = -3
        if not design.computeAll():
            raise RuntimeError("Public profile edit failed")
        case["stages"]["edited"] = observe(design)
        require(design, kind, height, width, depth, radius, angle)
        saved = folder / ("vendor_" + kind + "Edited.f3d")
        if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
            raise RuntimeError("Public profile native save failed")
        document.close(False)
        document = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(saved)))
        if document is None:
            raise RuntimeError("Public profile saved file did not reopen")
        design = adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))
        if not design.computeAll():
            raise RuntimeError("Public profile saved file did not rebuild")
        case["stages"]["reopened"] = observe(design)
        require(design, kind, height, width, depth, radius, angle)
        case["saved_sha256"] = hashlib.sha256(saved.read_bytes()).hexdigest()
        case["status"] = "accepted"
        document.close(False)
        document = None
        checkpoint()
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
