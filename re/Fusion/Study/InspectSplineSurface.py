"""Read NURBS grids, seam curves and a few API evaluator points from an owned loft."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    base = Path(__file__).resolve().parent
    output = base/("surfacegrids-"+uuid.uuid4().hex[:12])
    output.mkdir()
    source = "moretools-380212ab6368/LoftThreeSections.f3d"
    truth = {"fusion_version": app.version, "source": source, "surfaces": [], "curves": [], "errors": []}
    doc = None
    try:
        doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(base/source)))
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        for body in design.rootComponent.bRepBodies:
            for face in body.faces:
                geometry = face.geometry
                if geometry.objectType.split("::")[-1] != "NurbsSurface":
                    continue
                ok, du, dv, nu, nv, controls, ku, kv, weights, pu, pv = geometry.getData()
                if not ok:
                    raise RuntimeError("NURBS surface getData failed")
                bounds = geometry.evaluator.parametricRange()
                low, high = bounds.minPoint, bounds.maxPoint
                params = [adsk.core.Point2D.create(low.x+(high.x-low.x)*u, low.y+(high.y-low.y)*v)
                          for u,v in ((.23, .31), (.63, .72), (.87, .46))]
                ok, points = geometry.evaluator.getPointsAtParameters(params)
                if not ok:
                    raise RuntimeError("Surface evaluator failed")
                item = {"body_name": body.name, "degree_u": du, "degree_v": dv, "control_count_u": nu,
                        "control_count_v": nv, "control_points_cm": [p.asArray() for p in controls],
                        "knots_u": ku, "knots_v": kv, "weights": weights, "properties_u": pu, "properties_v": pv,
                        "parameter_bounds": [low.asArray(), high.asArray()],
                        "evaluation_parameters": [p.asArray() for p in params],
                        "evaluation_points_cm": [p.asArray() for p in points]}
                ok, points = face.evaluator.getPointsAtParameters(params)
                if ok:
                    item["face_evaluation_points_cm"] = [p.asArray() for p in points]
                truth["surfaces"].append(item)
            for edge in body.edges:
                geometry = edge.geometry
                if geometry.objectType.split("::")[-1] != "NurbsCurve3D":
                    continue
                ok, controls, degree, knots, rational, weights, periodic = geometry.getData()
                if not ok:
                    raise RuntimeError("NURBS curve getData failed")
                ok, low, high = geometry.evaluator.getParameterExtents()
                if not ok:
                    raise RuntimeError("Curve parameter extents failed")
                params = [low+(high-low)*f for f in (.17, .51, .83)]
                ok, points = geometry.evaluator.getPointsAtParameters(params)
                if not ok:
                    raise RuntimeError("Curve evaluator failed")
                truth["curves"].append({"degree": degree, "control_points_cm": [p.asArray() for p in controls],
                                        "knots": knots, "rational": rational, "weights": weights, "periodic": periodic,
                                        "evaluation_parameters": params, "evaluation_points_cm": [p.asArray() for p in points]})
    except Exception:
        truth["errors"].append(traceback.format_exc())
    finally:
        if doc:
            doc.close(False)
        (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
        (output/"complete.txt").write_text("Spline surface evidence finished; consult errors.\n")
