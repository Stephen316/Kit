"""Generate a compact spline/conic corpus and API geometry truth."""

import json
import math
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def geometry_data(curve):
    geometry = curve.geometry
    result = {"kind": curve.objectType.split("::")[-1], "geometry_kind": geometry.objectType.split("::")[-1],
              "is_fixed": curve.isFixed, "is_construction": curve.isConstruction}
    if isinstance(geometry, adsk.core.NurbsCurve3D):
        ok, points, degree, knots, rational, weights, periodic = geometry.getData()
        if not ok:
            raise RuntimeError("NURBS API geometry unavailable")
        result.update(control_points_cm=[p.asArray() for p in points], degree=degree, knots=knots,
                      is_rational=rational, weights=weights, is_periodic=periodic)
        ok, start, end = geometry.evaluator.getParameterExtents()
        parameters = [start + (end-start)*i/4 for i in range(5)]
        ok, points = geometry.evaluator.getPointsAtParameters(parameters)
        result.update(evaluation_parameters=parameters, evaluation_points_cm=[p.asArray() for p in points])
    else:
        result["geometry_data"] = [v.asArray() if hasattr(v, "asArray") else v for v in geometry.getData()]
    if hasattr(curve, "fitPoints"):
        result["fit_points_cm"] = [p.geometry.asArray() for p in curve.fitPoints]
    return result


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("splines-" + uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, vector = adsk.core.Point3D.create, adsk.core.Vector3D.create
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    try:
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        for case in ("FittedOpen", "FittedClosed", "ControlCubic", "ControlQuintic",
                     "FixedRational", "FixedNonRational", "EllipticalArc", "Conic"):
            try:
                sketch = root.sketches.add(root.xYConstructionPlane)
                sketch.name = "Probe" + case
                coords = [(0.7, 1.1, 0), (1.6, 3.2, 0), (3.8, -1.3, 0), (5.1, 2.4, 0)]
                if case.startswith("Fitted"):
                    points = adsk.core.ObjectCollection.create()
                    for p in coords:
                        points.add(point(*p))
                    curve = sketch.sketchCurves.sketchFittedSplines.add(points)
                    if case == "FittedClosed":
                        curve.isClosed = True
                elif case.startswith("Control"):
                    degree = 3 if case == "ControlCubic" else 5
                    if degree == 5:
                        coords += [(6.7, 4.1, 0), (8.4, 0.8, 0)]
                    curve = sketch.sketchCurves.sketchControlPointSplines.add([point(*p) for p in coords], degree)
                elif case.startswith("Fixed"):
                    points = [point(*p) for p in coords]
                    knots = [0., 0., 0., 0., 1., 1., 1., 1.]
                    if case == "FixedRational":
                        geometry = adsk.core.NurbsCurve3D.createRational(points, 3, knots, [1., 0.5, 2., 1.], False)
                    else:
                        geometry = adsk.core.NurbsCurve3D.createNonRational(points, 3, knots, False)
                    curve = sketch.sketchCurves.sketchFixedSplines.addByNurbsCurve(geometry)
                elif case == "EllipticalArc":
                    curve = sketch.sketchCurves.sketchEllipticalArcs.addByAngle(
                        point(1.3, -0.6, 0), vector(2.4, 1.8, 0), vector(-0.9, 1.2, 0), 0.4, 2.2)
                else:
                    curve = sketch.sketchCurves.sketchConicCurves.add(
                        point(0.7, 1.1, 0), point(5.1, 2.4, 0), point(2.6, 4.2, 0), 0.65)
                truth["samples"].append({"name": sketch.name, "primary_curve": geometry_data(curve),
                                         "all_curves": [geometry_data(c) for c in sketch.sketchCurves]})
            except Exception:
                truth["errors"].append({"case": case, "error": traceback.format_exc()})
        options = design.exportManager.createFusionArchiveExportOptions(str(output / "splines.f3d"))
        if not design.exportManager.execute(options):
            raise RuntimeError("Spline export failed")
    except Exception:
        truth["errors"].append({"case": "export", "error": traceback.format_exc()})
    finally:
        doc.close(False)
        (output / "ground_truth.json").write_text(json.dumps(truth, indent=2))
        (output / "complete.txt").write_text("Spline export finished; consult errors.\n")
