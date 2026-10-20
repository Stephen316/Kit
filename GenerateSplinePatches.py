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
        for name, rational, nu, du in (("PolynomialPatch", False, 3, 2), ("RationalPatch", True, 3, 2),
                                       ("CubicRationalPatch", True, 4, 3), ("InteriorKnotRationalPatch", True, 4, 2)):
            case = {"name": name}
            truth["cases"].append(case)
            ku = [0.]*(du+1)+([.35] if nu == 4 and du == 2 else [])+[1.]*(du+1)
            kv = [0., 0., 0., 1., 1., 1.]
            controls = [adsk.core.Point3D.create(u*1.2, v*1.3,
                        [[0., .2, .1], [.15, 1.2, -.1], [.3, .1, .4], [.2, -.3, .5]][u][v])
                        for u in range(nu) for v in range(3)]
            weights = ([1., .9, 1., .8, .65, .8, 1.1, .85, 1.2, 1., .9, 1.][:nu*3] if rational else [])
            properties = 9 if rational else 1
            surface = adsk.core.NurbsSurface.create(du, 2, nu, 3, controls, ku, kv, weights, properties, properties)
            if not surface:
                raise RuntimeError("NURBS surface creation failed")
            case["input_surface"] = surface_data(surface)
            definition = adsk.fusion.BRepBodyDefinition.create()
            face = definition.lumpDefinitions.add().shellDefinitions.add().faceDefinitions.add(surface, False)
            loop = face.loopDefinitions.add()
            corners = [definition.createVertexDefinition(controls[i]) for i in (0, (nu-1)*3, nu*3-1, 2)]
            boundaries = ([u*3 for u in range(nu)], list(range((nu-1)*3, nu*3)),
                          [u*3+2 for u in reversed(range(nu))], [2, 1, 0])
            for i, indices in enumerate(boundaries):
                points = [controls[j] for j in indices]
                degree, knots = (du, ku) if i%2 == 0 else (2, kv)
                # Reversed controls require a reflected knot vector as well.
                if i >= 2:
                    knots = [1.-k for k in reversed(knots)]
                curve = (adsk.core.NurbsCurve3D.createRational(points, degree, knots, [weights[j] for j in indices], False)
                         if rational else adsk.core.NurbsCurve3D.createNonRational(points, degree, knots, False))
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
            case["curves"] = []
            for edge in body.edges:
                geometry = edge.geometry
                curve = {"kind": geometry.objectType.split("::")[-1]}
                if curve["kind"] == "NurbsCurve3D":
                    ok, points, degree, knots, is_rational, edge_weights, periodic = geometry.getData()
                    if not ok:
                        raise RuntimeError("Boundary NURBS getData failed")
                    curve.update(controls_cm=[p.asArray() for p in points], degree=degree, knots=knots,
                                 rational=is_rational, weights=edge_weights, periodic=periodic)
                ok, low, high = geometry.evaluator.getParameterExtents()
                if not ok:
                    raise RuntimeError("Boundary parameter extents failed")
                parameters = [low+(high-low)*fraction for fraction in (.17, .51, .83)]
                ok, points = geometry.evaluator.getPointsAtParameters(parameters)
                if not ok:
                    raise RuntimeError("Boundary evaluation failed")
                curve.update(parameter_domain=[low, high], evaluation_parameters=parameters,
                             evaluation_points_cm=[p.asArray() for p in points])
                case["curves"].append(curve)
        if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/"splinepatches.f3d"))):
            raise RuntimeError("Spline patch export failed")
    except Exception:
        truth["errors"].append(traceback.format_exc())
    finally:
        doc.close(False)
        (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
        (output/"complete.txt").write_text("Spline patch generation finished; consult errors.\n")
