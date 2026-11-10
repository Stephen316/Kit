"""Run in Fusion to generate independent decoder validation files."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("holdouts-" + uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": []}
    cases = [
        ("independent_depth", [(17.375, 6.25, 0, False)], False, False),
        ("expression_depth", [(19.25, 12, 0, False)], True, True),
        ("two_extrusions", [(43.125, 4, 0, False), (5.875, 3, 0, True)], False, True),
        ("drafted_extrusion", [(21.25, 10, 5, False)], False, False),
    ]
    try:
        for filename, specs, use_expression, extra_sketch in cases:
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            if use_expression:
                design.userParameters.add("probeDepth", adsk.core.ValueInput.createByString("9.125 mm"), "mm", "")
            if extra_sketch:
                spare = root.sketches.add(root.xZConstructionPlane)
                spare.name = "UnrelatedSketch"
                spare.sketchCurves.sketchLines.addByTwoPoints(
                    adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(2, 1, 0)
                )
            sample = {"file": filename + ".f3d", "extrusions": []}
            for index, (depth, radius, draft, reverse) in enumerate(specs):
                sketch = root.sketches.add(root.xYConstructionPlane)
                sketch.name = "IndependentProfile" + str(index)
                sketch.sketchCurves.sketchCircles.addByCenterRadius(
                    adsk.core.Point3D.create(index * 5, 0, 0), radius / 10
                )
                expression = "probeDepth * 2 + 1 mm" if use_expression else f"{depth} mm"
                extent = adsk.fusion.DistanceExtentDefinition.create(adsk.core.ValueInput.createByString(expression))
                inputs = root.features.extrudeFeatures.createInput(
                    sketch.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation
                )
                direction = (adsk.fusion.ExtentDirections.NegativeExtentDirection if reverse
                             else adsk.fusion.ExtentDirections.PositiveExtentDirection)
                if not inputs.setOneSideExtent(extent, direction, adsk.core.ValueInput.createByString(f"{draft} deg")):
                    raise RuntimeError("Could not define holdout extrusion")
                feature = root.features.extrudeFeatures.add(inputs)
                feature.name = "BlindProbe_" + str(index)
                parameter = adsk.fusion.DistanceExtentDefinition.cast(feature.extentOne).distance
                sample["extrusions"].append({
                    "name": feature.name, "depth_mm": depth, "radius_mm": radius,
                    "draft_degrees": draft, "reverse": reverse,
                    "parameter_name": parameter.name, "api_depth_cm": parameter.value,
                    "expression": parameter.expression,
                })
            if not design.computeAll() or root.bRepBodies.count != len(specs):
                raise RuntimeError("Holdout geometry did not rebuild as expected")
            options = design.exportManager.createFusionArchiveExportOptions(str(output / sample["file"]))
            if not design.exportManager.execute(options):
                raise RuntimeError("Holdout export failed")
            truth["samples"].append(sample)
            (output / "ground_truth.json").write_text(json.dumps(truth, indent=2))
            doc.close(False)
        (output / "complete.txt").write_text("All four holdout files generated successfully.\n")
    except Exception:
        (output / "error.txt").write_text(traceback.format_exc())
