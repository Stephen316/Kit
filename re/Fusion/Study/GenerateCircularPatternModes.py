"""Local circular body/feature pattern controls, suppression and compute probes."""

import json
import traceback
import uuid
from pathlib import Path

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("circularmodes-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    cases = ("body_full", "body_negative", "body_symmetric", "body_suppressed",
             "multiple_customaxis", "feature_optimized", "feature_identical", "feature_adjust")
    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            entities = adsk.core.ObjectCollection.create()
            is_feature = case.startswith("feature_")
            for index in range(2 if case == "multiple_customaxis" else 1):
                sketch = root.sketches.add(root.xYConstructionPlane)
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(3, index*2, 0), point(4, index*2+1, 0))
                seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value("10 mm"),
                                                             adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                seed.name = "SeedFeature"+str(index)
                seed.bodies.item(0).name = "SeedBody"+str(index)
                entities.add(seed if is_feature else seed.bodies.item(0))
            axis = root.zConstructionAxis
            if case == "multiple_customaxis":
                plane_input = root.constructionPlanes.createInput()
                plane_input.setByOffset(root.yZConstructionPlane, value("10 mm"))
                plane = root.constructionPlanes.add(plane_input)
                axis_input = root.constructionAxes.createInput()
                if not axis_input.setByTwoPlanes(plane, root.xZConstructionPlane):
                    raise RuntimeError("Custom pattern axis input rejected")
                axis = root.constructionAxes.add(axis_input)
                axis.name = "OffsetZAxis"
            inputs = root.features.circularPatternFeatures.createInput(entities, axis)
            inputs.quantity = value("5" if case == "body_symmetric" else "4")
            inputs.totalAngle = value("-210 deg" if case == "body_negative" else
                                      "180 deg" if case == "body_symmetric" else "360 deg")
            inputs.isSymmetric = case == "body_symmetric"
            requested_compute = {"feature_optimized": 0, "feature_identical": 1, "feature_adjust": 2}.get(case)
            if requested_compute is not None:
                inputs.patternComputeOption = requested_compute
            feature = root.features.circularPatternFeatures.add(inputs)
            feature.name = "ProbeCircularPattern"
            feature.timelineObject.rollTo(True)
            if case == "body_suppressed":
                feature.suppressedElementsIds = [1]
            input_names = [feature.inputEntities.item(i).name for i in range(feature.inputEntities.count)]
            input_types = [feature.inputEntities.item(i).objectType for i in range(feature.inputEntities.count)]
            design.timeline.moveToEnd()
            settings = {"quantity": feature.quantity.value, "total_angle_radians": feature.totalAngle.value,
                        "is_symmetric": feature.isSymmetric,
                        "suppressed_element_ids": list(feature.suppressedElementsIds),
                        "pattern_entity_type": feature.patternEntityType,
                        "pattern_compute_option": feature.patternComputeOption,
                        "requested_compute_option": requested_compute,
                        "input_names": input_names, "input_types": input_types,
                        "input_count": len(input_names), "result_body_count": root.bRepBodies.count,
                        "axis_name": axis.name, "axis_origin_cm": axis.geometry.origin.asArray(),
                        "axis_direction": axis.geometry.direction.asArray(),
                        "health_state": feature.healthState, "warning": feature.errorOrWarningMessage}
            elements = [{"id": feature.patternElements.item(i).id,
                         "is_suppressed": feature.patternElements.item(i).isSuppressed,
                         "transform": feature.patternElements.item(i).transform.asArray()}
                        for i in range(feature.patternElements.count)]
            sample = {"file": case+".f3d", "settings": settings, "pattern_elements": elements,
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Circular pattern export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Circular pattern exports finished; consult errors.\n")
