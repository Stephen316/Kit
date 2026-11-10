"""Generate isolated sketch cases for incremental format research."""

import json
import math
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def vector(value):
    return [value.x, value.y, value.z]


def describe(sketch):
    curves = []
    for i in range(sketch.sketchCurves.count):
        curve = sketch.sketchCurves.item(i)
        kind = curve.objectType.split("::")[-1]
        item = {"kind": kind, "construction": curve.isConstruction, "fixed": curve.isFixed}
        geometry = curve.geometry
        if kind == "SketchLine":
            item.update(start=vector(curve.startSketchPoint.geometry), end=vector(curve.endSketchPoint.geometry))
        elif kind in ("SketchCircle", "SketchArc"):
            item.update(center=vector(geometry.center), radius=geometry.radius)
            if kind == "SketchArc":
                item.update(start=vector(curve.startSketchPoint.geometry), end=vector(curve.endSketchPoint.geometry),
                            start_angle=geometry.startAngle, end_angle=geometry.endAngle)
        elif kind == "SketchEllipse":
            item.update(center=vector(geometry.center), major_radius=geometry.majorRadius,
                        minor_radius=geometry.minorRadius)
        curves.append(item)
    return {
        "name": sketch.name, "curves": curves,
        "constraints": [sketch.geometricConstraints.item(i).objectType.split("::")[-1]
                        for i in range(sketch.geometricConstraints.count)],
        "dimensions": [{"kind": sketch.sketchDimensions.item(i).objectType.split("::")[-1],
                        "parameter": sketch.sketchDimensions.item(i).parameter.name,
                        "value": sketch.sketchDimensions.item(i).parameter.value}
                       for i in range(sketch.sketchDimensions.count)],
    }


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("advanced-" + uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "coordinate_units": "cm", "sketches": [], "errors": []}
    try:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        point = adsk.core.Point3D.create
        names = ["Parallel", "Perpendicular", "Equal", "Collinear", "Concentric", "Tangent",
                 "MidPoint", "HorizontalPoints", "VerticalPoints", "Symmetry", "Primitives",
                 "ConstructionAndFixed", "LinearDimension", "DiameterDimension", "AngularDimension"]
        for name in names:
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.name = name
            lines, circles = sketch.sketchCurves.sketchLines, sketch.sketchCurves.sketchCircles
            constraints = sketch.geometricConstraints
            line = lambda a, b: lines.addByTwoPoints(point(*a), point(*b))
            circle = lambda c, r: circles.addByCenterRadius(point(*c), r)
            try:
                if name in ("Parallel", "Perpendicular", "Equal", "Collinear"):
                    first = line((1, 1, 0), (4, 1, 0))
                    second = line((6, 1, 0), (6, 4, 0)) if name == "Perpendicular" else line((6, 3, 0), (8, 3, 0))
                    getattr(constraints, "add" + name)(first, second)
                elif name == "Concentric":
                    constraints.addConcentric(circle((3, 3, 0), 1), circle((4, 3, 0), 2))
                elif name == "Tangent":
                    constraints.addTangent(line((1, 5, 0), (6, 5, 0)), circle((4, 4, 0), 1))
                elif name == "MidPoint":
                    segment = line((1, 5, 0), (5, 5, 0))
                    constraints.addMidPoint(sketch.sketchPoints.add(point(3, 5, 0)), segment)
                elif name in ("HorizontalPoints", "VerticalPoints"):
                    a = sketch.sketchPoints.add(point(1, 2, 0))
                    b = sketch.sketchPoints.add(point(4, 2, 0) if name == "HorizontalPoints" else point(1, 5, 0))
                    getattr(constraints, "add" + name)(a, b)
                elif name == "Symmetry":
                    a = sketch.sketchPoints.add(point(-2, 3, 0))
                    b = sketch.sketchPoints.add(point(2, 3, 0))
                    constraints.addSymmetry(a, b, line((0, 1, 0), (0, 5, 0)))
                elif name == "Primitives":
                    sketch.sketchCurves.sketchArcs.addByCenterStartSweep(point(2, 3, 0), point(3.5, 3, 0), 1.2)
                    sketch.sketchCurves.sketchEllipses.add(point(8, 3, 0), point(10.5, 3, 0), point(8, 4.25, 0))
                elif name == "ConstructionAndFixed":
                    line((0, 1, 0), (2, 3, 0)).isConstruction = True
                    circle((5, 3, 0), .75).isFixed = True
                elif name == "LinearDimension":
                    segment = line((1, 2, 0), (4, 2, 0))
                    sketch.sketchDimensions.addDistanceDimension(
                        segment.startSketchPoint, segment.endSketchPoint,
                        adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation, point(2, 1, 0))
                elif name == "DiameterDimension":
                    sketch.sketchDimensions.addDiameterDimension(circle((4, 3, 0), 1.75), point(7, 5, 0))
                elif name == "AngularDimension":
                    a = line((0, 0, 0), (4, 0, 0))
                    b = line((0, 0, 0), (2, 3, 0))
                    sketch.sketchDimensions.addAngularDimension(a, b, point(2, 1, 0))
                design.computeAll()
                truth["sketches"].append(describe(sketch))
            except Exception:
                truth["errors"].append({"sketch": name, "error": traceback.format_exc()})
        options = design.exportManager.createFusionArchiveExportOptions(str(output / "advanced.f3d"))
        if not design.exportManager.execute(options):
            raise RuntimeError("Could not export advanced sketch file")
        (output / "ground_truth.json").write_text(json.dumps(truth, indent=2))
        doc.close(False)
        (output / "complete.txt").write_text("Reference export finished; consult ground_truth.json for per-case errors.\n")
    except Exception:
        (output / "error.txt").write_text(traceback.format_exc())
