"""Capture study-owned Loft operation contrasts against an intersecting block."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ("new_body", "join", "cut", "intersect", "new_component")


def body_evidence(body):
    bounds = body.boundingBox
    return {"name": body.name, "entity_token": body.entityToken,
            "component_name": body.parentComponent.name, "is_solid": body.isSolid,
            "volume_cm3": body.volume,
            "bounding_box_min_cm": bounds.minPoint.asArray(),
            "bounding_box_max_cm": bounds.maxPoint.asArray()}


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("loftoperations-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": [],
             "token_scope": "Opaque API entity tokens retained as evidence; no native ID interpretation is assigned."}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    operations = adsk.fusion.FeatureOperations
    operation_values = {"new_body": operations.NewBodyFeatureOperation, "join": operations.JoinFeatureOperation,
                        "cut": operations.CutFeatureOperation, "intersect": operations.IntersectFeatureOperation,
                        "new_component": operations.NewComponentFeatureOperation}
    cases = context.get("cases", CASES) if isinstance(context, dict) else CASES
    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            seed_plane_input = root.constructionPlanes.createInput()
            seed_plane_input.setByOffset(root.xYConstructionPlane, value("-5 mm"))
            seed_sketch = root.sketches.add(root.constructionPlanes.add(seed_plane_input))
            seed_sketch.name = "BlockSection"
            seed_sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(-2, -2, 0), point(2, 2, 0))
            seed = root.features.extrudeFeatures.addSimple(seed_sketch.profiles.item(0), value("30 mm"),
                                                         operations.NewBodyFeatureOperation)
            seed.name = "StudyBlockExtrude"
            seed.bodies.item(0).name = "StudyBlock"
            seed_evidence = body_evidence(seed.bodies.item(0))
            sketches = []
            for index, (height_cm, radius_cm) in enumerate(((0., 1.), (3., .6))):
                plane = root.xYConstructionPlane
                if height_cm:
                    plane_input = root.constructionPlanes.createInput()
                    plane_input.setByOffset(plane, adsk.core.ValueInput.createByReal(height_cm))
                    plane = root.constructionPlanes.add(plane_input)
                sketch = root.sketches.add(plane)
                sketch.name = "LoftSection"+str(index+1)
                sketch.sketchCurves.sketchCircles.addByCenterRadius(point(0, 0, 0), radius_cm)
                sketches.append(sketch)
            inputs = root.features.loftFeatures.createInput(operation_values[case])
            for sketch in sketches:
                inputs.loftSections.add(sketch.profiles.item(0))
            feature = root.features.loftFeatures.add(inputs)
            feature.name = "ProbeLoftOperation"
            settings = {"requested_operation": operation_values[case],
                        "result_bodies": [body_evidence(body) for body in feature.bodies],
                        "root_body_count": root.bRepBodies.count,
                        "components": [{"name": component.name, "body_count": component.bRepBodies.count}
                                       for component in design.allComponents]}
            feature.timelineObject.rollTo(True)
            settings.update(operation=feature.operation, is_solid=feature.isSolid, is_closed=feature.isClosed,
                            is_tangent_edges_merged=feature.isTangentEdgesMerged,
                            feature_component_name=feature.parentComponent.name,
                            section_count=feature.loftSections.count,
                            guide_count=feature.centerLineOrRails.count,
                            is_centerline=feature.centerLineOrRails.isCenterLine)
            settings["sections"] = []
            for index in range(feature.loftSections.count):
                section = feature.loftSections.item(index)
                entity, condition = section.entity, section.endCondition
                profile = adsk.fusion.Profile.cast(entity)
                settings["sections"].append({"index": section.index, "entity_type": entity.objectType,
                    "profile_token": profile.entityToken if profile else None,
                    "sketch_name": profile.parentSketch.name if profile else None,
                    "profile_loop_count": profile.profileLoops.count if profile else None,
                    "end_condition_type": condition.objectType if condition else None})
            if settings["operation"] in (operations.CutFeatureOperation, operations.IntersectFeatureOperation):
                participants = feature.participantBodies
                settings["participant_bodies"] = [body_evidence(body) for body in participants] if participants else []
            else:
                settings["participant_bodies"] = None
            design.timeline.moveToEnd()
            sample = {"file": case+".f3d", "seed_before_loft": seed_evidence, "settings": settings,
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Loft operation export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Loft operation capture finished; consult errors.\n")
