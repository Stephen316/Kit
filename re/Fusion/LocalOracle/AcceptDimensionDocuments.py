import hashlib
import json
from math import isclose
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion


root = Path(__file__).resolve().parent / "DimensionAuthoring"
preparation = json.loads((root / "Preparation.json").read_text())
app = adsk.core.Application.get()
original = app.activeDocument
doc = None
report = {"fusion_version": app.version, "scope": "Independent complete constrained rectangle/cuboid documents: native constraint and dimension semantics, anchored width/depth edits, solid height edit, rollback/rebuild/save/reopen", "cases": []}


def checkpoint():
    (root / "NativeAcceptance.json").write_text(json.dumps(report, indent=2) + "\n")


def observe(design):
    sketch = design.rootComponent.sketches.item(0)
    return {
        "parameters": [{"name": p.name, "expression": p.expression, "value": p.value} for p in design.allParameters],
        "timeline": [{"name": item.name, "health": item.healthState, "message": item.errorOrWarningMessage} for item in design.timeline],
        "sketch": {"name": sketch.name, "fully_constrained": sketch.isFullyConstrained, "profiles": sketch.profiles.count, "constraints": [x.objectType for x in sketch.geometricConstraints], "dimensions": [{"type": x.objectType, "parameter": x.parameter.name, "expression": x.parameter.expression, "value": x.parameter.value} for x in sketch.sketchDimensions], "lines": [{"start_cm": line.startSketchPoint.geometry.asArray(), "end_cm": line.endSketchPoint.geometry.asArray()} for line in sketch.sketchCurves.sketchLines]},
        "bodies": [{"volume_cm3": b.volume, "min_cm": b.boundingBox.minPoint.asArray(), "max_cm": b.boundingBox.maxPoint.asArray(), "center_cm": b.physicalProperties.centerOfMass.asArray(), "mass_kg": b.physicalProperties.mass, "density_kg_per_cm3": b.physicalProperties.density, "material": b.material.name, "faces": b.faces.count, "edges": b.edges.count, "vertices": b.vertices.count} for b in design.rootComponent.bRepBodies],
    }


def require(design, width, depth, height, solid):
    if design.timeline.count != (2 if solid else 1) or design.rootComponent.sketches.count != 1 or design.rootComponent.bRepBodies.count != int(solid):
        raise RuntimeError("Constrained document structure differs")
    if any(x.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState or x.errorOrWarningMessage for x in design.timeline):
        raise RuntimeError("Constrained timeline contains a warning or error")
    sketch = design.rootComponent.sketches.item(0)
    if not sketch.isFullyConstrained or sketch.profiles.count != 1 or sketch.sketchCurves.sketchLines.count != 4 or sketch.sketchDimensions.count != 2 or sketch.geometricConstraints.count != 4:
        raise RuntimeError("Independent sketch constraints or dimensions differ")
    points = [point for line in sketch.sketchCurves.sketchLines for point in (line.startSketchPoint, line.endSketchPoint)]
    actual = {(round(p.geometry.x, 8), round(p.geometry.y, 8), round(p.geometry.z, 8)) for p in points}
    expected = {(0, 0, 0), (width, 0, 0), (width, depth, 0), (0, depth, 0)}
    if actual != expected:
        raise RuntimeError(f"Anchored corners differ: {actual} versus {expected}")
    if not any(p.isFixed and all(isclose(v, 0, abs_tol=1e-8) for v in p.geometry.asArray()) for p in points):
        raise RuntimeError("Rectangle lacks its fixed anchor")
    if {x.parameter.expression for x in sketch.sketchDimensions} != {"boxWidth", "boxDepth"}:
        raise RuntimeError("Sketch dimensions are not driven by expected user parameters")
    if solid:
        body = design.rootComponent.bRepBodies.item(0)
        if (body.faces.count, body.edges.count, body.vertices.count) != (6, 12, 8):
            raise RuntimeError("Constrained cuboid topology differs")
        bounds = (*body.boundingBox.minPoint.asArray(), *body.boundingBox.maxPoint.asArray())
        if not all(isclose(a, b, rel_tol=1e-8, abs_tol=1e-8) for a, b in zip(bounds, (0, 0, 0, width, depth, height))):
            raise RuntimeError("Constrained cuboid bounds differ")
        if not isclose(body.volume, width * depth * height, rel_tol=1e-8):
            raise RuntimeError("Constrained cuboid volume differs")
        props = body.physicalProperties
        if not all(isclose(a, b, rel_tol=1e-8, abs_tol=1e-8) for a, b in zip(props.centerOfMass.asArray(), (width / 2, depth / 2, height / 2))):
            raise RuntimeError("Constrained cuboid mass center differs")
        if body.material.name != "Dimension driven material" or not isclose(props.density, 0.00287, rel_tol=1e-8) or not isclose(props.mass, width * depth * height * 0.00287, rel_tol=1e-8):
            raise RuntimeError("Constrained cuboid material or mass differs")


try:
    for source_case in preparation["cases"]:
        solid = source_case["profile"] == "cuboid"
        name = "DimensionedCuboid" if solid else "DimensionedRectangle"
        source = root / (name + ".f3d")
        case = {"name": name, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "stage": "importing"}
        report["cases"].append(case)
        checkpoint()
        if case["source_sha256"] != source_case["sha256"]:
            raise RuntimeError("Dimensioned source digest changed")
        doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
        if doc is None:
            raise RuntimeError("Independent dimensioned document did not open")
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        case["opened"] = observe(design)
        case["stage"] = "opened"
        checkpoint()
        require(design, 1.7, 2.3, 3.1, solid)
        if solid:
            design.timeline.markerPosition = 1
            case["rolled_back"] = observe(design)
            if design.rootComponent.bRepBodies.count != 0 or not design.rootComponent.sketches.item(0).isFullyConstrained:
                raise RuntimeError("Rollback did not preserve the constrained sketch")
            if not design.timeline.moveToEnd():
                raise RuntimeError("Constrained timeline restoration failed")
        if not design.computeAll():
            raise RuntimeError("Constrained document rebuild failed")
        require(design, 1.7, 2.3, 3.1, solid)
        case["rebuilt"] = observe(design)
        design.userParameters.itemByName("boxWidth").expression = "19 mm"
        if not design.computeAll():
            raise RuntimeError("Width edit failed")
        case["width_edited"] = observe(design)
        case["stage"] = "width_edited"
        checkpoint()
        require(design, 1.9, 2.3, 3.1, solid)
        design.userParameters.itemByName("boxDepth").expression = "29 mm"
        if not design.computeAll():
            raise RuntimeError("Depth edit failed")
        case["depth_edited"] = observe(design)
        case["stage"] = "depth_edited"
        checkpoint()
        require(design, 1.9, 2.9, 3.1, solid)
        design.userParameters.itemByName("boxHeight").expression = "37 mm"
        if not design.computeAll():
            raise RuntimeError("Height edit failed")
        case["height_edited"] = observe(design)
        case["stage"] = "height_edited"
        checkpoint()
        require(design, 1.9, 2.9, 3.7, solid)
        saved = root / ("vendor_" + name + "Edited.f3d")
        if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
            raise RuntimeError("Dimensioned document export failed")
        doc.close(False)
        doc = None
        doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(saved)))
        if doc is None:
            raise RuntimeError("Saved dimensioned document did not reopen")
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        if not design.computeAll():
            raise RuntimeError("Reopened dimensioned document rebuild failed")
        case["reopened"] = observe(design)
        case["stage"] = "reopened"
        checkpoint()
        require(design, 1.9, 2.9, 3.7, solid)
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
