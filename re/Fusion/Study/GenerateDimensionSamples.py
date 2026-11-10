"""Small dimension variants and spline constraints with API truth."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("dimensions-" + uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point = adsk.core.Point3D.create
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    try:
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        cases = ("Aligned", "Horizontal", "Vertical", "DrivenAligned", "Offset", "EllipseMajor", "EllipseMinor",
                 "Concentric", "TangentDistance", "LinearDiameter", "Smooth", "ControlPolygon")
        for case in cases:
            try:
                sketch = root.sketches.add(root.xYConstructionPlane)
                sketch.name = "Dimension" + case
                curves, dimensions, dimension = sketch.sketchCurves, sketch.sketchDimensions, None
                if case in ("Aligned", "Horizontal", "Vertical", "DrivenAligned"):
                    line = curves.sketchLines.addByTwoPoints(point(0.7, 1.1, 0), point(4.2, 3.6, 0))
                    orientation = {"Aligned": adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
                                   "DrivenAligned": adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
                                   "Horizontal": adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
                                   "Vertical": adsk.fusion.DimensionOrientations.VerticalDimensionOrientation}[case]
                    dimension = dimensions.addDistanceDimension(line.startSketchPoint, line.endSketchPoint,
                                                                 orientation, point(2, 5, 0), case != "DrivenAligned")
                elif case == "Offset":
                    first = curves.sketchLines.addByTwoPoints(point(1, 1, 0), point(4, 1, 0))
                    second = curves.sketchLines.addByTwoPoints(point(1, 3, 0), point(4, 3, 0))
                    dimension = dimensions.addOffsetDimension(first, second, point(5, 2, 0))
                elif case.startswith("Ellipse"):
                    ellipse = curves.sketchEllipses.add(point(1, 1, 0), point(4, 1, 0), point(1, 2.5, 0))
                    method = dimensions.addEllipseMajorRadiusDimension if case == "EllipseMajor" else dimensions.addEllipseMinorRadiusDimension
                    dimension = method(ellipse, point(5, 4, 0))
                elif case in ("Concentric", "TangentDistance"):
                    first = curves.sketchCircles.addByCenterRadius(point(0.7, 1.1, 0), 1 if case == "Concentric" else 0.5)
                    second = curves.sketchCircles.addByCenterRadius(
                        point(0.7, 1.1, 0) if case == "Concentric" else point(5, 1.1, 0),
                        2.8 if case == "Concentric" else 0.9)
                    dimension = (dimensions.addConcentricCircleDimension(first, second, point(3, 4, 0)) if case == "Concentric"
                                 else dimensions.addTangentDistanceDimension(first, False, second, False, point(3, 4, 0)))
                elif case == "LinearDiameter":
                    line = curves.sketchLines.addByTwoPoints(point(0, -2, 0), point(0, 5, 0))
                    line.isConstruction = True
                    other = sketch.sketchPoints.add(point(3, 2, 0))
                    dimension = dimensions.addLinearDiameterDimension(line, other, point(4, 2, 0))
                elif case == "Smooth":
                    pts = adsk.core.ObjectCollection.create()
                    for p in ((0.7, 1.1, 0), (1.6, 3.2, 0), (3.8, -1.3, 0), (5.1, 2.4, 0)):
                        pts.add(point(*p))
                    first = curves.sketchFittedSplines.add(pts)
                    pts = adsk.core.ObjectCollection.create()
                    pts.add(first.endSketchPoint)
                    for p in ((6, 4, 0), (7, 3, 0), (8, 5, 0)):
                        pts.add(point(*p))
                    second = curves.sketchFittedSplines.add(pts)
                    sketch.geometricConstraints.addSmooth(first, second)
                else:
                    curves.sketchControlPointSplines.add([point(*p) for p in
                        ((0.7, 1.1, 0), (1.6, 3.2, 0), (3.8, -1.3, 0), (5.1, 2.4, 0))], 3)
                sample = {"name": sketch.name, "geometric_constraints": [c.objectType.split("::")[-1] for c in sketch.geometricConstraints]}
                if dimension:
                    parameter = dimension.parameter
                    sample["dimension"] = {"kind": dimension.objectType.split("::")[-1], "is_driving": dimension.isDriving,
                                           "parameter_name": parameter.name, "parameter_value": parameter.value,
                                           "parameter_role": getattr(parameter, "role", None), "parameter_unit": parameter.unit,
                                           "parameter_object_type": parameter.objectType}
                truth["samples"].append(sample)
            except Exception:
                truth["errors"].append({"case": case, "error": traceback.format_exc()})
        options = design.exportManager.createFusionArchiveExportOptions(str(output / "dimensions.f3d"))
        if not design.exportManager.execute(options):
            raise RuntimeError("Dimension export failed")
    except Exception:
        truth["errors"].append({"case": "export", "error": traceback.format_exc()})
    finally:
        doc.close(False)
        (output / "ground_truth.json").write_text(json.dumps(truth, indent=2))
        (output / "complete.txt").write_text("Dimension export finished; consult errors.\n")
