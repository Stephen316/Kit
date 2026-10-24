"""Study-owned Thicken modes, input kinds and operation samples."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("thickenmodes-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    operations = adsk.fusion.FeatureOperations
    cases = [("positive", "1.5 mm", False, True, 0, operations.NewBodyFeatureOperation, False),
             ("negative", "-1.1 mm", False, False, 0, operations.NewBodyFeatureOperation, False),
             ("symmetric", "2 mm", True, False, 0, operations.NewBodyFeatureOperation, False),
             ("rounded", "1.5 mm", False, True, 1, operations.NewBodyFeatureOperation, False),
             ("body_input", "1.7 mm", False, False, 0, operations.NewBodyFeatureOperation, True),
             ("join", "1.5 mm", False, False, 0, operations.JoinFeatureOperation, False),
             ("cut", "-1.5 mm", False, True, 0, operations.CutFeatureOperation, False),
             ("intersect", "-5 mm", False, False, 0, operations.IntersectFeatureOperation, False)]
    if isinstance(context, dict) and "cases" in context:
        cases = [case for case in cases if case[0] in context["cases"]]

    def bounds(body):
        box = body.boundingBox
        return {"min_cm": box.minPoint.asArray(), "max_cm": box.maxPoint.asArray(),
                "volume_cm3": body.physicalProperties.volume}

    def entity_truth(entity):
        face = adsk.fusion.BRepFace.cast(entity)
        if face is not None:
            return {"kind": "Face", "body_name": face.body.name,
                    "geometry_type": face.geometry.objectType.split("::")[-1],
                    "point_on_face_cm": face.pointOnFace.asArray(), "area_cm2": face.area}
        body = adsk.fusion.BRepBody.cast(entity)
        if body is None:
            raise RuntimeError("Unexpected Thicken input type")
        return {"kind": "Body", "name": body.name, "face_count": body.faces.count, "bounds": bounds(body)}

    for case, distance, symmetric, chain, mode, operation, whole_body in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            needs_participant = case in ("join", "cut", "intersect")
            participant_evidence = None
            if needs_participant:
                participant_sketch = root.sketches.add(root.xYConstructionPlane)
                participant_sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0, -1.5, 0), point(1.5, 1.5, 0))
                participant = root.features.extrudeFeatures.addSimple(participant_sketch.profiles.item(0), value("20 mm"),
                                                                     operations.NewBodyFeatureOperation)
                participant.bodies.item(0).name = "ParticipantBody"
                participant_evidence = bounds(participant.bodies.item(0))
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.sketchCurves.sketchCircles.addByCenterRadius(point(0, 0, 0), 1.)
            seed_input = root.features.extrudeFeatures.createInput(sketch.profiles.item(0), operations.NewBodyFeatureOperation)
            seed_input.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(value("20 mm")),
                                       adsk.fusion.ExtentDirections.PositiveExtentDirection)
            seed_input.isSolid = False
            seed = root.features.extrudeFeatures.add(seed_input)
            seed.name = "SeedExtrusion"
            body = seed.bodies.item(0)
            body.name = "SeedBody"
            inputs = adsk.core.ObjectCollection.create()
            inputs.add(body if whole_body else seed.sideFaces.item(0))
            input_evidence = [entity_truth(inputs.item(i)) for i in range(inputs.count)]
            thicken_input = root.features.thickenFeatures.createInput(inputs, value(distance), symmetric, operation, chain)
            thicken_input.thickenType = mode
            feature = root.features.thickenFeatures.add(thicken_input)
            if feature is None:
                raise RuntimeError("Thicken add returned null")
            feature.name = "ProbeThicken"
            sample = {"file": case+".f3d", "requested": {"thickness_expression": distance, "is_symmetric": symmetric,
                      "is_chain_selection": chain, "thicken_type": mode, "operation": operation,
                      "input_entities": input_evidence},
                      "participant_body_before_thicken": participant_evidence,
                      "output_bodies": [{"name": feature.bodies.item(i).name, "bounds": bounds(feature.bodies.item(i))}
                                        for i in range(feature.bodies.count)],
                      "health_state": feature.healthState, "warning": feature.errorOrWarningMessage}
            feature.timelineObject.rollTo(True)
            sample["settings"] = {"thickness_cm": feature.thickness.value, "is_symmetric": feature.isSymmetric,
                                  "is_chain_selection": feature.isChainSelection, "thicken_type": feature.thickenType,
                                  "operation": feature.operation,
                                  "input_entities": [entity_truth(feature.inputFaces.item(i)) for i in range(feature.inputFaces.count)]}
            design.timeline.moveToEnd()
            sample["parameters"] = [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Thicken export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Thicken generation finished; consult errors.\n")
