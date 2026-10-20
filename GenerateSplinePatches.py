"""Create study-owned bounded NURBS sheets with explicit control grids."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def surface_data(surface):
    ok, du, dv, nu, nv, points, ku, kv, weights, pu, pv = surface.getData()
    if not ok:
        raise RuntimeError("NURBS surface getData failed")
    parameters = [adsk.core.Point2D.create(u, v) for u, v in ((.23, .31), (.63, .72), (.87, .46))]
    ok, samples = surface.evaluator.getPointsAtParameters(parameters)
    if not ok:
        raise RuntimeError("NURBS surface evaluator failed")
    return {"degree_u": du, "degree_v": dv, "control_count_u": nu, "control_count_v": nv,
            "controls_cm": [p.asArray() for p in points], "knots_u": ku, "knots_v": kv,
            "weights": weights, "properties_u": pu, "properties_v": pv,
            "evaluation_uv": [p.asArray() for p in parameters],
            "evaluation_points_cm": [p.asArray() for p in samples]}


def run(context):
    app = adsk.core.Application.get()
    base = Path(__file__).resolve().parent
    output = base/("splinepatches-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "cases": [], "errors": []}
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    try:
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        knots = [0., 0., 0., 1., 1., 1.]
        for rational in (False, True):
            case = {"name": "RationalPatch" if rational else "PolynomialPatch"}
            truth["cases"].append(case)
            controls = [adsk.core.Point3D.create(u*1.2, v*1.3, [[0., .2, .1], [.15, 1.2, -.1], [.3, .1, .4]][u][v])
                        for u in range(3) for v in range(3)]
            weights = [1., .9, 1., .8, .65, .8, 1., .9, 1.] if rational else []
            properties = 9 if rational else 1
            surface = adsk.core.NurbsSurface.create(2, 2, 3, 3, controls, knots, knots, weights, properties, properties)
            if not surface:
                raise RuntimeError("NURBS surface creation failed")
            case["input_surface"] = surface_data(surface)
            definition = adsk.fusion.BRepBodyDefinition.create()
            face = definition.lumpDefinitions.add().shellDefinitions.add().faceDefinitions.add(surface, False)
            loop = face.loopDefinitions.add()
            corners = [definition.createVertexDefinition(controls[i]) for i in (0, 6, 8, 2)]
            for i, indices in enumerate(((0, 3, 6), (6, 7, 8), (8, 5, 2), (2, 1, 0))):
                points = [controls[j] for j in indices]
                curve = (adsk.core.NurbsCurve3D.createRational(points, 2, knots, [weights[j] for j in indices], False)
                         if rational else adsk.core.NurbsCurve3D.createNonRational(points, 2, knots, False))
                edge = definition.createEdgeDefinitionByCurve(corners[i], corners[(i+1)%4], curve)
                loop.bRepCoEdgeDefinitions.add(edge, False)
            temporary = definition.createBody()
            case["body_creation_info"] = definition.outcomeInfo
            if not temporary:
                raise RuntimeError("BRep definition failed: "+str(definition.outcomeInfo))
            feature = root.features.baseFeatures.add()
            feature.name = case["name"]
            feature.startEdit()
            try:
                body = root.bRepBodies.add(temporary, feature)
                body.name = case["name"]
            finally:
                feature.finishEdit()
            body = feature.bodies.item(0)
            case.update(face_count=body.faces.count, edge_count=body.edges.count, vertex_count=body.vertices.count,
                        stored_surface=surface_data(body.faces.item(0).geometry))
        if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/"splinepatches.f3d"))):
            raise RuntimeError("Spline patch export failed")
    except Exception:
        truth["errors"].append(traceback.format_exc())
    finally:
        doc.close(False)
        (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
        (output/"complete.txt").write_text("Spline patch generation finished; consult errors.\n")
