"""Read UV trim evidence from the study-owned spline sheet archive."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    base = Path(__file__).resolve().parent
    output = base/("patchtrims-"+uuid.uuid4().hex[:12])
    output.mkdir()
    source = "splinepatches-900d152c2380/splinepatches.f3d"
    truth = {"fusion_version": app.version, "source": source, "curves": [], "errors": []}
    doc = None
    try:
        doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(base/source)))
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        for body in design.rootComponent.bRepBodies:
            for face in body.faces:
                for loop in face.loops:
                    for coedge in loop.coEdges:
                        geometry = coedge.geometry
                        item = {"body_name": body.name, "kind": geometry.objectType.split("::")[-1],
                                "is_opposed_to_edge": coedge.isOpposedToEdge, "is_param_reversed": coedge.isParamReversed}
                        if item["kind"] == "NurbsCurve2D":
                            ok, controls, degree, knots, rational, weights, periodic = geometry.getData()
                            if not ok:
                                raise RuntimeError("UV NURBS getData failed")
                            item.update(degree=degree, controls_uv=[p.asArray() for p in controls], knots=knots,
                                        rational=rational, weights=weights, periodic=periodic)
                        ok, low, high = coedge.evaluator.getParameterExtents()
                        if not ok:
                            raise RuntimeError("UV curve extents failed")
                        parameters = [low+(high-low)*fraction for fraction in (.19, .53, .82)]
                        ok, points = coedge.evaluator.getPointsAtParameters(parameters)
                        if not ok:
                            raise RuntimeError("UV curve evaluation failed")
                        item.update(parameter_domain=[low, high], evaluation_parameters=parameters,
                                    evaluation_points_uv=[p.asArray() for p in points])
                        ok, points = geometry.evaluator.getPointsAtParameters(parameters)
                        if not ok:
                            raise RuntimeError("Exposed UV spline geometry evaluation failed")
                        item["geometry_evaluation_points_uv"] = [p.asArray() for p in points]
                        truth["curves"].append(item)
    except Exception:
        truth["errors"].append(traceback.format_exc())
    finally:
        if doc:
            doc.close(False)
        (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
        (output/"complete.txt").write_text("Patch trim capture finished; consult errors.\n")
