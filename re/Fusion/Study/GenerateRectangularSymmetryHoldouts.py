"""Six symmetry holdouts: extent, signed spacing, oblique axes and input types."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = (("extent_one", 5, 2, True, False, "Extent", "60 mm", "40 mm", "Bodies", 1, False),
         ("extent_both", 4, 4, True, True, "Extent", "60 mm", "90 mm", "Bodies", 1, False),
         ("negative_spacing", 4, 3, True, True, "Spacing", "-25 mm", "-30 mm", "Bodies", 1, False),
         ("oblique_axes", 5, 4, True, True, "Spacing", "25 mm", "30 mm", "Bodies", 1, True),
         ("feature_input", 4, 3, True, True, "Spacing", "25 mm", "30 mm", "Features", 1, False),
         ("multiple_bodies", 3, 4, True, True, "Spacing", "25 mm", "30 mm", "Bodies", 2, False))


def body_box(body):
    """Actual API bounding-box getters, independent of element transforms."""
    bounds = body.boundingBox
    minimum, maximum = bounds.minPoint.asArray(), bounds.maxPoint.asArray()
    return {"name": body.name, "min_cm": minimum, "max_cm": maximum,
            "center_cm": [(a+b)/2 for a, b in zip(minimum, maximum)]}


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("rectsymholdouts-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": [],
             "scope": "Actual pattern getters and independent seed/result body bounding-box getters; explicit axes, no inferred ID associations"}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    for case, one_count, two_count, one_sym, two_sym, mode, one_distance, two_distance, input_kind, body_count, oblique in CASES:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            entities = adsk.core.ObjectCollection.create()
            seed_boxes = []
            for index in range(body_count):
                sketch = root.sketches.add(root.xYConstructionPlane)
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(1, index*2, 0), point(2, index*2+1, 0))
                seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value("10 mm"),
                                                             adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                seed.name = "SeedFeature"+str(index)
                body = seed.bodies.item(0)
                body.name = "SeedBody"+str(index)
                seed_boxes.append(body_box(body))
                entities.add(seed if input_kind == "Features" else body)
            one_axis, two_axis = root.xConstructionAxis, root.yConstructionAxis
            if oblique:
                directions = root.sketches.add(root.xYConstructionPlane)
                directions.name = "ObliquePatternDirections"
                axes = []
                for index, endpoint in enumerate(((3, 4, 0), (-2, 5, 0))):
                    line = directions.sketchCurves.sketchLines.addByTwoPoints(point(0, 0, 0), point(*endpoint))
                    line.isConstruction = True
                    axis_input = root.constructionAxes.createInput()
                    if not axis_input.setByEdge(line):
                        raise RuntimeError("Explicit oblique axis creation rejected")
                    axis = root.constructionAxes.add(axis_input)
                    axis.name = "ObliqueAxis"+str(index+1)
                    axes.append(axis)
                one_axis, two_axis = axes
            distance_type = (adsk.fusion.PatternDistanceType.ExtentPatternDistanceType if mode == "Extent"
                             else adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
            inputs = root.features.rectangularPatternFeatures.createInput(
                entities, one_axis, value(str(one_count)), value(one_distance), distance_type)
            if not inputs.setDirectionTwo(two_axis, value(str(two_count)), value(two_distance)):
                raise RuntimeError("Explicit second pattern direction rejected")
            inputs.isSymmetricInDirectionOne, inputs.isSymmetricInDirectionTwo = one_sym, two_sym
            if input_kind == "Features":
                inputs.patternComputeOption = adsk.fusion.PatternComputeOptions.IdenticalPatternCompute
            feature = root.features.rectangularPatternFeatures.add(inputs)
            feature.name = "ProbeRectangularSymmetryHoldout"
            feature.timelineObject.rollTo(True)
            actual_inputs = feature.inputEntities
            input_names = [actual_inputs.item(i).name for i in range(actual_inputs.count)]
            input_types = [actual_inputs.item(i).objectType for i in range(actual_inputs.count)]
            axis_truth = []
            for axis in (feature.directionOneEntity, feature.directionTwoEntity):
                geometry = axis.geometry
                axis_truth.append({"name": axis.name, "object_type": axis.objectType,
                                   "origin_cm": geometry.origin.asArray(), "direction": geometry.direction.asArray()})
            design.timeline.moveToEnd()
            settings = {"quantity_one": feature.quantityOne.value, "quantity_two": feature.quantityTwo.value,
                        "distance_one_cm": feature.distanceOne.value, "distance_two_cm": feature.distanceTwo.value,
                        "distance_type": feature.patternDistanceType,
                        "symmetric_one": feature.isSymmetricInDirectionOne, "symmetric_two": feature.isSymmetricInDirectionTwo,
                        "direction_one": feature.directionOne.asArray(), "direction_two": feature.directionTwo.asArray(),
                        "direction_one_entity": axis_truth[0], "direction_two_entity": axis_truth[1],
                        "input_names": input_names, "input_types": input_types, "input_count": len(input_names),
                        "pattern_entity_type": feature.patternEntityType, "pattern_compute_option": feature.patternComputeOption,
                        "suppressed_element_ids": list(feature.suppressedElementsIds),
                        "result_body_count": root.bRepBodies.count,
                        "health_state": feature.healthState, "warning": feature.errorOrWarningMessage}
            elements = []
            for index in range(feature.patternElements.count):
                element = feature.patternElements.item(index)
                elements.append({"collection_index": index, "id": element.id,
                                 "is_suppressed": element.isSuppressed, "transform": element.transform.asArray()})
            sample = {"file": case+".f3d", "requested": {"quantity_one": one_count, "quantity_two": two_count,
                       "symmetric_one": one_sym, "symmetric_two": two_sym, "distance_type": mode,
                       "distance_one_expression": one_distance, "distance_two_expression": two_distance,
                       "input_kind": input_kind, "oblique_axes": oblique},
                      "settings": settings, "pattern_elements": elements, "seed_body_boxes": seed_boxes,
                      "result_body_boxes": [body_box(root.bRepBodies.item(i)) for i in range(root.bRepBodies.count)],
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            options = design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))
            if not design.exportManager.execute(options):
                raise RuntimeError("Rectangular symmetry holdout export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Rectangular symmetry holdouts finished; consult errors.\n")
