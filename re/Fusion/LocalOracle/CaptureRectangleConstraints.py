import hashlib
import json
from math import isclose
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion


root = Path(__file__).resolve().parent / "RectangleConstraints"
root.mkdir(exist_ok=True)
app = adsk.core.Application.get()
original = app.activeDocument
doc = None
report = {"fusion_version": app.version, "scope": "Native controlled differential capture of rectangular orientation constraints, fixed anchor and driving dimensions; not Kit writer acceptance", "captures": []}


def capture(name, design, sketch):
    path = root / (name + ".f3d")
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(path))):
        raise RuntimeError("Native dimensional sketch export failed")
    report["captures"].append({
        "name": name,
        "file": path.name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
        "parameters": [{"name": p.name, "expression": p.expression, "value": p.value} for p in design.allParameters],
        "constraints": [value.objectType for value in sketch.geometricConstraints],
        "dimensions": [{"type": value.objectType, "parameter": value.parameter.name, "value": value.parameter.value, "expression": value.parameter.expression} for value in sketch.sketchDimensions],
        "lines": [{"start_cm": line.startSketchPoint.geometry.asArray(), "end_cm": line.endSketchPoint.geometry.asArray()} for line in sketch.sketchCurves.sketchLines],
        "profiles": sketch.profiles.count,
        "fully_constrained": sketch.isFullyConstrained,
        "points": [{"xyz_cm": point.geometry.asArray(), "fixed": point.isFixed} for point in sketch.sketchPoints],
    })
    (root / "Capture.json").write_text(json.dumps(report, indent=2) + "\n")


try:
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    sketch = design.rootComponent.sketches.add(design.rootComponent.xYConstructionPlane)
    sketch.name = "ControlledConstrainedRectangle"
    lines = sketch.sketchCurves.sketchLines.addTwoPointRectangle(adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(1.7, 2.3, 0))
    horizontal = next(line for line in lines if isclose(line.startSketchPoint.geometry.y, 0, abs_tol=1e-8) and isclose(line.endSketchPoint.geometry.y, 0, abs_tol=1e-8))
    vertical = next(line for line in lines if isclose(line.startSketchPoint.geometry.x, 0, abs_tol=1e-8) and isclose(line.endSketchPoint.geometry.x, 0, abs_tol=1e-8))
    width = design.userParameters.add("controlledWidth", adsk.core.ValueInput.createByString("17 mm"), "mm", "Controlled width input")
    depth = design.userParameters.add("controlledDepth", adsk.core.ValueInput.createByString("23 mm"), "mm", "Controlled depth input")
    capture("Baseline", design, sketch)
    for index, line in enumerate(lines):
        start = line.startSketchPoint.geometry
        end = line.endSketchPoint.geometry
        if isclose(start.y, end.y, abs_tol=1e-8):
            sketch.geometricConstraints.addHorizontal(line)
        else:
            sketch.geometricConstraints.addVertical(line)
        capture("Orientation" + str(index + 1), design, sketch)
    anchor = next(point for point in sketch.sketchPoints if isclose(point.geometry.x, 0, abs_tol=1e-8) and isclose(point.geometry.y, 0, abs_tol=1e-8) and any(point == line.startSketchPoint or point == line.endSketchPoint for line in lines))
    anchor.isFixed = True
    capture("FixedAnchor", design, sketch)
    dimension = sketch.sketchDimensions.addDistanceDimension(horizontal.startSketchPoint, horizontal.endSketchPoint, adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, adsk.core.Point3D.create(0.85, -0.5, 0))
    if dimension is None:
        raise RuntimeError("Horizontal dimension creation failed")
    dimension.parameter.expression = "controlledWidth"
    capture("WidthDimension", design, sketch)
    dimension = sketch.sketchDimensions.addDistanceDimension(vertical.startSketchPoint, vertical.endSketchPoint, adsk.fusion.DimensionOrientations.VerticalDimensionOrientation, adsk.core.Point3D.create(-0.5, 1.15, 0))
    if dimension is None:
        raise RuntimeError("Vertical dimension creation failed")
    dimension.parameter.expression = "controlledDepth"
    capture("WidthDepthDimensions", design, sketch)
    width.expression = "19 mm"
    depth.expression = "29 mm"
    if not design.computeAll():
        raise RuntimeError("Native dimensional sketch did not rebuild")
    capture("EditedDimensions", design, sketch)
    corners = {(round(point.geometry.x, 8), round(point.geometry.y, 8)) for line in lines for point in (line.startSketchPoint, line.endSketchPoint)}
    if corners != {(0, 0), (1.9, 0), (1.9, 2.9), (0, 2.9)} or not sketch.isFullyConstrained:
        raise RuntimeError("Anchored dimension edits did not preserve a fully constrained rectangle")
    report["status"] = "captured"
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
    (root / "Capture.json").write_text(json.dumps(report, indent=2) + "\n")
