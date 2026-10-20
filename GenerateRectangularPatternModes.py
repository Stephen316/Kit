"""Rectangular body/feature input, compute, direction and suppression probes."""

import json
import traceback
import uuid
from pathlib import Path

import adsk.core
import adsk.fusion


CASES = ("body_one", "body_multiple_customaxis", "body_sketchlines", "body_negative",
         "feature_optimized", "feature_identical", "feature_adjust")


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("rectmodes-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    cases = CASES

    def describe_direction(entity):
        if entity is None:
            return None
        item = {"object_type": entity.objectType, "name": getattr(entity, "name", None)}
        line = adsk.fusion.SketchLine.cast(entity)
        if line:
            item.update(sketch_name=line.parentSketch.name, start_cm=line.startSketchPoint.geometry.asArray(),
                        end_cm=line.endSketchPoint.geometry.asArray())
        else:
            axis = adsk.fusion.ConstructionAxis.cast(entity)
            if axis:
                item.update(origin_cm=axis.geometry.origin.asArray(), direction=axis.geometry.direction.asArray())
        return item

    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            entities = adsk.core.ObjectCollection.create()
            is_feature = case.startswith("feature_")
            for index in range(2 if case == "body_multiple_customaxis" else 1):
                sketch = root.sketches.add(root.xYConstructionPlane)
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(1, index*2, 0), point(2, index*2+1, 0))
                seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value("10 mm"),
                                                             adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                seed.name = "SeedFeature"+str(index)
                seed.bodies.item(0).name = "SeedBody"+str(index)
                entities.add(seed if is_feature else seed.bodies.item(0))
            one, two = root.xConstructionAxis, root.yConstructionAxis
            if case in ("body_multiple_customaxis", "body_sketchlines"):
                directions = root.sketches.add(root.xYConstructionPlane)
                directions.name = "PatternDirections"
                first = directions.sketchCurves.sketchLines.addByTwoPoints(point(0, 0, 0), point(3, 4, 0))
                first.isConstruction = True
                if case == "body_multiple_customaxis":
                    axis_input = root.constructionAxes.createInput()
                    if not axis_input.setByEdge(first):
                        raise RuntimeError("Custom diagonal axis input rejected")
                    one = root.constructionAxes.add(axis_input)
                    one.name = "CustomDiagonalAxis"
                    two = root.zConstructionAxis
                else:
                    second = directions.sketchCurves.sketchLines.addByTwoPoints(point(0, 0, 0), point(-4, 3, 0))
                    second.isConstruction = True
                    one, two = first, second
            extent = case == "feature_adjust"
            distance_one = "-30 mm" if case == "body_negative" else "60 mm" if extent else "25 mm"
            inputs = root.features.rectangularPatternFeatures.createInput(entities, one, value("3"), value(distance_one), 0 if extent else 1)
            if case in ("body_one", "body_negative"):
                inputs.quantityTwo = value("1")
            elif not inputs.setDirectionTwo(two, value("2"), value("40 mm" if extent else "30 mm")):
                raise RuntimeError("Second rectangular pattern direction rejected")
            requested_compute = {"feature_optimized": 0, "feature_identical": 1, "feature_adjust": 2}.get(case)
            if requested_compute is not None:
                inputs.patternComputeOption = requested_compute
            feature = root.features.rectangularPatternFeatures.add(inputs)
            feature.name = "ProbeRectangularPattern"
            feature.timelineObject.rollTo(True)
            input_names = [feature.inputEntities.item(i).name for i in range(feature.inputEntities.count)]
            input_types = [feature.inputEntities.item(i).objectType for i in range(feature.inputEntities.count)]
            design.timeline.moveToEnd()
            if case == "body_suppressed_element":
                # The feature-wide setter is unimplemented in this Fusion build.
                # This separately documented setter is an optional single-case
                # probe; it is intentionally excluded from the default cases.
                feature.patternElements.item(1).isSuppressed = True
                feature.patternElements.item(4).isSuppressed = True
                design.computeAll()
            settings = {"quantity_one": feature.quantityOne.value, "quantity_two": feature.quantityTwo.value,
                        "distance_one_cm": feature.distanceOne.value, "distance_two_cm": feature.distanceTwo.value,
                        "distance_type": feature.patternDistanceType,
                        "symmetric_one": feature.isSymmetricInDirectionOne,
                        "symmetric_two": feature.isSymmetricInDirectionTwo,
                        "direction_one": feature.directionOne.asArray(), "direction_two": feature.directionTwo.asArray(),
                        "direction_one_entity": describe_direction(feature.directionOneEntity),
                        "direction_two_entity": describe_direction(feature.directionTwoEntity),
                        "pattern_entity_type": feature.patternEntityType,
                        "pattern_compute_option": feature.patternComputeOption,
                        "requested_compute_option": requested_compute,
                        "suppressed_element_ids": list(feature.suppressedElementsIds),
                        "input_names": input_names, "input_types": input_types, "input_count": len(input_names),
                        "result_body_count": root.bRepBodies.count,
                        "health_state": feature.healthState, "warning": feature.errorOrWarningMessage}
            sample = {"file": case+".f3d", "settings": settings,
                      "pattern_elements": [{"id": feature.patternElements.item(i).id,
                                            "is_suppressed": feature.patternElements.item(i).isSuppressed,
                                            "transform": feature.patternElements.item(i).transform.asArray()}
                                           for i in range(feature.patternElements.count)],
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Rectangular pattern export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Rectangular pattern exports finished; consult errors.\n")
