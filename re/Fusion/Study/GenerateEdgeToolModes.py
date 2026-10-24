"""Controlled fillet/chamfer edge-set modes; exports owned local documents."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CASES = ("fillet_constant", "fillet_tangent", "fillet_setback", "fillet_multiple",
         "fillet_variable", "fillet_chord", "fillet_asymmetric", "chamfer_equal", "chamfer_tangent",
         "chamfer_two", "chamfer_two_flipped", "chamfer_angle", "chamfer_angle_flipped")


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("edgemodes-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    for case in CASES:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(1, 1, 0), point(5, 4, 0))
            seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value("20 mm"),
                                                         adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            edges = adsk.core.ObjectCollection.create()
            top = seed.endFaces.item(0)
            edges.add(top.edges.item(0))
            if case.startswith("fillet"):
                inputs = root.features.filletFeatures.createInput()
                inputs.isRollingBallCorner = case != "fillet_setback"
                if case == "fillet_variable":
                    inputs.edgeSetInputs.addVariableRadiusEdgeSet(edges, value("1 mm"), value("3 mm"), False)
                elif case == "fillet_chord":
                    inputs.edgeSetInputs.addChordLengthEdgeSet(edges, value("2 mm"), False)
                elif case == "fillet_asymmetric":
                    inputs.edgeSetInputs.addAsymmetricRadiusEdgeSet(edges, value("2 mm"), value("1 mm"), False)
                else:
                    edge_input = inputs.edgeSetInputs.addConstantRadiusEdgeSet(edges, value("2 mm"), case == "fillet_tangent")
                    if case == "fillet_curvature":
                        edge_input.continuity = adsk.fusion.SurfaceContinuityTypes.CurvatureSurfaceContinuityType
                        edge_input.tangencyWeight = value("0.75")
                    if case == "fillet_multiple":
                        other = adsk.core.ObjectCollection.create()
                        other.add(top.edges.item(2))
                        inputs.edgeSetInputs.addConstantRadiusEdgeSet(other, value("3 mm"), False)
                feature = root.features.filletFeatures.add(inputs)
                settings = {"rolling_ball_corner": feature.isRollingBallCorner, "feature_type": feature.filletFeatureType}
                sets = feature.edgeSets
            else:
                inputs = root.features.chamferFeatures.createInput2()
                flipped = case.endswith("flipped")
                if case.startswith("chamfer_two"):
                    inputs.chamferEdgeSets.addTwoDistancesChamferEdgeSet(edges, value("1.5 mm"), value("2.5 mm"), flipped, False)
                elif case.startswith("chamfer_angle"):
                    inputs.chamferEdgeSets.addDistanceAndAngleChamferEdgeSet(edges, value("1.5 mm"), value("35 deg"), flipped, False)
                else:
                    inputs.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges, value("1.5 mm"), case == "chamfer_tangent")
                    if case == "chamfer_multiple":
                        other = adsk.core.ObjectCollection.create()
                        other.add(top.edges.item(2))
                        inputs.chamferEdgeSets.addTwoDistancesChamferEdgeSet(other, value("2 mm"), value("3 mm"), False, False)
                feature = root.features.chamferFeatures.add(inputs)
                settings = {}
                sets = feature.edgeSets
            feature.name = "ProbeEdgeTool"
            design.computeAll()
            settings["edge_sets"] = []
            for edge_set in sets:
                item = {"kind": edge_set.objectType.split("::")[-1], "tangent_chain": edge_set.isTangentChain}
                for key in ("radius", "startRadius", "endRadius", "chordLength", "offsetOne", "offsetTwo",
                            "distance", "distanceOne", "distanceTwo", "angle", "tangencyWeight"):
                    if hasattr(edge_set, key):
                        parameter = getattr(edge_set, key)
                        if parameter:
                            item[key] = {"name": parameter.name, "value": parameter.value, "role": parameter.role}
                for key in ("continuity", "isFlipped"):
                    if hasattr(edge_set, key):
                        item[key] = getattr(edge_set, key)
                settings["edge_sets"].append(item)
            sample = {"file": case+".f3d", "settings": settings,
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            options = design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))
            if not design.exportManager.execute(options):
                raise RuntimeError("Edge tool export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Edge tool exports finished; consult errors.\n")
