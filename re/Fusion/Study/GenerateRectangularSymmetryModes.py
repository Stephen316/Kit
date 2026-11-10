"""Four rectangular body patterns with explicit axes and symmetry getter truth."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = (("symmetric_one", 5, 2, True, False),
         ("symmetric_two", 3, 4, False, True),
         ("symmetric_both_odd", 5, 3, True, True),
         ("symmetric_both_even", 4, 4, True, True))


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("rectsymmetry-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": [],
             "scope": "Modeling body patterns, explicit component X/Y axes, spacing distances; actual getter matrices, no assumed instance ordering"}
    point = adsk.core.Point3D.create
    value = adsk.core.ValueInput.createByString
    for case, quantity_one, quantity_two, symmetric_one, symmetric_two in CASES:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(1, 0, 0), point(2, 1, 0))
            seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value("10 mm"),
                                                         adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            seed.name = "SeedFeature"
            seed.bodies.item(0).name = "SeedBody"
            entities = adsk.core.ObjectCollection.create()
            entities.add(seed.bodies.item(0))
            inputs = root.features.rectangularPatternFeatures.createInput(
                entities, root.xConstructionAxis, value(str(quantity_one)), value("25 mm"),
                adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
            if not inputs.setDirectionTwo(root.yConstructionAxis, value(str(quantity_two)), value("30 mm")):
                raise RuntimeError("Explicit second pattern direction rejected")
            inputs.isSymmetricInDirectionOne = symmetric_one
            inputs.isSymmetricInDirectionTwo = symmetric_two
            feature = root.features.rectangularPatternFeatures.add(inputs)
            feature.name = "ProbeRectangularSymmetry"
            feature.timelineObject.rollTo(True)
            direction_names = (feature.directionOneEntity.name, feature.directionTwoEntity.name)
            input_names = [feature.inputEntities.item(i).name for i in range(feature.inputEntities.count)]
            design.timeline.moveToEnd()
            settings = {"quantity_one": feature.quantityOne.value, "quantity_two": feature.quantityTwo.value,
                        "distance_one_cm": feature.distanceOne.value, "distance_two_cm": feature.distanceTwo.value,
                        "distance_type": feature.patternDistanceType,
                        "symmetric_one": feature.isSymmetricInDirectionOne,
                        "symmetric_two": feature.isSymmetricInDirectionTwo,
                        "direction_one": feature.directionOne.asArray(), "direction_two": feature.directionTwo.asArray(),
                        "direction_one_entity_name": direction_names[0],
                        "direction_two_entity_name": direction_names[1],
                        "input_names": input_names, "input_count": len(input_names),
                        "pattern_entity_type": feature.patternEntityType,
                        "pattern_compute_option": feature.patternComputeOption,
                        "suppressed_element_ids": list(feature.suppressedElementsIds),
                        "result_body_count": root.bRepBodies.count,
                        "health_state": feature.healthState, "warning": feature.errorOrWarningMessage}
            elements = []
            for index in range(feature.patternElements.count):
                element = feature.patternElements.item(index)
                elements.append({"collection_index": index, "id": element.id,
                                 "is_suppressed": element.isSuppressed,
                                 "transform": element.transform.asArray()})
            sample = {"file": case+".f3d", "requested": {"quantity_one": quantity_one, "quantity_two": quantity_two,
                       "symmetric_one": symmetric_one, "symmetric_two": symmetric_two},
                      "settings": settings, "pattern_elements": elements,
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            options = design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))
            if not design.exportManager.execute(options):
                raise RuntimeError("Rectangular symmetry export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Rectangular symmetry exports finished; consult errors.\n")
