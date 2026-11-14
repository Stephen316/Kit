import hashlib
import json
from math import isclose
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion


root = Path(__file__).resolve().parent / "RectangleAuthoring"
app = adsk.core.Application.get()
original = app.activeDocument
doc = None
report = {"fusion_version": app.version, "scope": "Independent complete rectangle and cuboid documents emitted only by production Kit codecs, without source archives, donor geometry, research runtime imports or CAD runtime in the writer", "cases": []}


def checkpoint():
    (root / "NativeAcceptance.json").write_text(json.dumps(report, indent=2) + "\n")


def observe(design):
    sketch = design.rootComponent.sketches.item(0)
    return {
        "parameters": [{"name": p.name, "expression": p.expression, "value": p.value} for p in design.allParameters],
        "timeline": [{"name": item.name, "health": item.healthState, "message": item.errorOrWarningMessage} for item in design.timeline],
        "sketch": {"name": sketch.name, "lines": [{"start_cm": line.startSketchPoint.geometry.asArray(), "end_cm": line.endSketchPoint.geometry.asArray()} for line in sketch.sketchCurves.sketchLines], "points": sketch.sketchPoints.count, "profiles": sketch.profiles.count, "dimensions": sketch.sketchDimensions.count, "constraints": sketch.geometricConstraints.count},
        "bodies": [{"volume_cm3": b.volume, "min_cm": b.boundingBox.minPoint.asArray(), "max_cm": b.boundingBox.maxPoint.asArray(), "center_cm": b.physicalProperties.centerOfMass.asArray(), "mass_kg": b.physicalProperties.mass, "density_kg_per_cm3": b.physicalProperties.density, "faces": b.faces.count, "edges": b.edges.count, "vertices": b.vertices.count} for b in design.rootComponent.bRepBodies],
    }


def require_sketch(design):
    if design.rootComponent.sketches.count != 1:
        raise RuntimeError("Expected one rectangle sketch")
    sketch = design.rootComponent.sketches.item(0)
    if sketch.name != "Authored Rectangle" or sketch.sketchCurves.sketchLines.count != 4 or sketch.profiles.count != 1:
        raise RuntimeError("Rectangle profile or names differ")
    actual = {(round(p.geometry.x, 8), round(p.geometry.y, 8), round(p.geometry.z, 8)) for line in sketch.sketchCurves.sketchLines for p in (line.startSketchPoint, line.endSketchPoint)}
    if actual != {(0.0, 0.0, 0.0), (1.7, 0.0, 0.0), (1.7, 2.3, 0.0), (0.0, 2.3, 0.0)}:
        raise RuntimeError("Rectangle corners differ")
    if any(item.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState or item.errorOrWarningMessage for item in design.timeline):
        raise RuntimeError("Timeline contains a warning or error")


def require_body(design, height, authored):
    require_sketch(design)
    if design.timeline.count != 2 or design.rootComponent.bRepBodies.count != 1:
        raise RuntimeError("Cuboid feature or body count differs")
    body = design.rootComponent.bRepBodies.item(0)
    bounds = body.boundingBox
    actual = (*bounds.minPoint.asArray(), *bounds.maxPoint.asArray())
    if not all(isclose(a, b, rel_tol=1e-9, abs_tol=1e-9) for a, b in zip(actual, (0, 0, 0, 1.7, 2.3, height))):
        raise RuntimeError("Cuboid bounds differ")
    if not isclose(body.volume, 1.7 * 2.3 * height, rel_tol=1e-9):
        raise RuntimeError("Cuboid volume differs")
    if (body.faces.count, body.edges.count, body.vertices.count) != (6, 12, 8):
        raise RuntimeError("Cuboid topology differs")
    props = body.physicalProperties
    if props.density <= 0 or props.mass <= 0 or body.material is None:
        raise RuntimeError("Cuboid lacks a valid positive-density material")
    if not all(isclose(a, b, rel_tol=1e-8, abs_tol=1e-8) for a, b in zip(props.centerOfMass.asArray(), (0.85, 1.15, height / 2))):
        raise RuntimeError("Cuboid mass center differs")
    if not isclose(props.mass, body.volume * props.density, rel_tol=1e-8):
        raise RuntimeError("Cuboid mass and density disagree")
    if authored and (not isclose(props.density, 0.001, rel_tol=1e-8) or body.material.name != "Kit Generic Material"):
        raise RuntimeError("Independently authored material values differ")


try:
    for name in ("ProductionRectangle", "ProductionCuboid"):
        source = root / (name + ".f3d")
        case = {"name": name, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "stage": "importing"}
        report["cases"].append(case)
        checkpoint()
        doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
        if doc is None:
            raise RuntimeError("Independently authored rectangle document did not open")
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        case["opened"] = observe(design)
        case["stage"] = "opened"
        checkpoint()
        require_sketch(design)
        if name == "ProductionRectangle":
            if design.timeline.count != 1 or design.rootComponent.bRepBodies.count != 0:
                raise RuntimeError("Sketch-only document has unexpected features")
            if not design.computeAll():
                raise RuntimeError("Rectangle sketch rebuild failed")
            require_sketch(design)
            sketch_saved = root / "vendor_rectangle_sketch.f3d"
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(sketch_saved))):
                raise RuntimeError("Rectangle sketch export failed")
            case["sketch_saved_sha256"] = hashlib.sha256(sketch_saved.read_bytes()).hexdigest()
            doc.close(False)
            doc = None
            doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(sketch_saved)))
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            if not design.computeAll():
                raise RuntimeError("Reopened rectangle sketch failed to rebuild")
            require_sketch(design)
            case["sketch_reopened"] = observe(design)
            extrudes = design.rootComponent.features.extrudeFeatures
            feature_input = extrudes.createInput(design.rootComponent.sketches.item(0).profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            distance = adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString("authoredLength"))
            if not feature_input.setOneSideExtent(distance, adsk.fusion.ExtentDirections.PositiveExtentDirection):
                raise RuntimeError("Native extrusion extent setup failed")
            feature = extrudes.add(feature_input)
            feature.name = "Authored Cuboid Extrusion"
            if not design.computeAll():
                raise RuntimeError("Native extrusion of authored rectangle failed")
            case["native_extrusion"] = observe(design)
        require_body(design, 3.1, name == "ProductionCuboid")
        design.timeline.markerPosition = 1
        case["rolled_back"] = observe(design)
        case["stage"] = "rolled_back"
        checkpoint()
        if design.rootComponent.bRepBodies.count != 0:
            raise RuntimeError("Rollback retained a solid")
        if not design.timeline.moveToEnd():
            raise RuntimeError("Timeline restoration failed")
        require_body(design, 3.1, name == "ProductionCuboid")
        if not design.computeAll():
            raise RuntimeError("Complete cuboid rebuild failed")
        case["rebuilt"] = observe(design)
        require_body(design, 3.1, name == "ProductionCuboid")
        design.userParameters.itemByName("authoredLength").expression = "37 mm"
        if not design.computeAll():
            raise RuntimeError("Height parameter edit failed")
        case["edited"] = observe(design)
        case["stage"] = "edited"
        checkpoint()
        require_body(design, 3.7, name == "ProductionCuboid")
        saved = root / ("vendor_" + name + "37mm.f3d")
        if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
            raise RuntimeError("Complete cuboid export failed")
        doc.close(False)
        doc = None
        doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(saved)))
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        if not design.computeAll():
            raise RuntimeError("Reopened cuboid failed to rebuild")
        case["reopened"] = observe(design)
        case["stage"] = "reopened"
        checkpoint()
        require_body(design, 3.7, name == "ProductionCuboid")
        case["saved_sha256"] = hashlib.sha256(saved.read_bytes()).hexdigest()
        case["status"] = "accepted"
        doc.close(False)
        doc = None
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
