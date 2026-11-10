"""Compare rectangular pattern distances, axes and symmetric direction flags."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("patterns-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    for case in ("one_spacing", "one_extent", "two_spacing", "two_extent", "symmetric_one", "symmetric_two"):
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(1, 1, 0), point(5, 4, 0))
            root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value("20 mm"),
                                                   adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            entities = adsk.core.ObjectCollection.create()
            entities.add(root.bRepBodies.item(0))
            distance_type = (adsk.fusion.PatternDistanceType.ExtentPatternDistanceType if case.endswith("extent")
                             else adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
            inputs = root.features.rectangularPatternFeatures.createInput(entities, root.xConstructionAxis,
                                                                          value("3"), value("60 mm"), distance_type)
            if case.startswith("one"):
                inputs.quantityTwo = value("1")
            else:
                if not inputs.setDirectionTwo(root.yConstructionAxis, value("4"), value("50 mm")):
                    raise RuntimeError("Second pattern direction rejected")
            inputs.isSymmetricInDirectionOne = case == "symmetric_one"
            inputs.isSymmetricInDirectionTwo = case == "symmetric_two"
            feature = root.features.rectangularPatternFeatures.add(inputs)
            feature.name = "ProbePattern"
            design.computeAll()
            settings = {"quantity_one": feature.quantityOne.value, "quantity_two": feature.quantityTwo.value,
                        "distance_one_cm": feature.distanceOne.value, "distance_two_cm": feature.distanceTwo.value,
                        "distance_type": feature.patternDistanceType,
                        "symmetric_one": feature.isSymmetricInDirectionOne,
                        "symmetric_two": feature.isSymmetricInDirectionTwo,
                        "direction_one": feature.directionOne.asArray(), "direction_two": feature.directionTwo.asArray(),
                        "direction_one_entity": feature.directionOneEntity.name,
                        "direction_two_entity": feature.directionTwoEntity.name if feature.directionTwoEntity else None}
            sample = {"file": case+".f3d", "settings": settings,
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            options = design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))
            if not design.exportManager.execute(options):
                raise RuntimeError("Pattern export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Pattern exports finished; consult errors.\n")
