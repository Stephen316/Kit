"""Generate basic dress-up and body-tool records, retaining per-case errors."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("tools-" + uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    for case in ["Fillet", "Chamfer", "Shell", "Hole", "RectangularPattern", "Mirror", "Scale"]:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.name = "BoxProfile"
            sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(1, 1, 0), point(5, 4, 0))
            seed = root.features.extrudeFeatures.addSimple(
                sketch.profiles.item(0), value("20 mm"), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            seed.name = "BaseExtrusion"
            top = seed.endFaces.item(0)
            entities = adsk.core.ObjectCollection.create()
            if case in ("Fillet", "Chamfer"):
                entities.add(top.edges.item(0))
                if case == "Fillet":
                    inputs = root.features.filletFeatures.createInput()
                    inputs.edgeSetInputs.addConstantRadiusEdgeSet(entities, value("2 mm"), False)
                    feature = root.features.filletFeatures.add(inputs)
                else:
                    inputs = root.features.chamferFeatures.createInput2()
                    inputs.chamferEdgeSets.addEqualDistanceChamferEdgeSet(entities, value("1.5 mm"), False)
                    feature = root.features.chamferFeatures.add(inputs)
            elif case == "Shell":
                entities.add(top)
                inputs = root.features.shellFeatures.createInput(entities, False)
                inputs.insideThickness = value("2 mm")
                feature = root.features.shellFeatures.add(inputs)
            elif case == "Hole":
                inputs = root.features.holeFeatures.createSimpleInput(value("6 mm"))
                inputs.setPositionByPoint(top, point(3, 2, 2))
                inputs.setDistanceExtent(value("12 mm"))
                feature = root.features.holeFeatures.add(inputs)
            else:
                entities.add(root.bRepBodies.item(0))
                if case == "RectangularPattern":
                    inputs = root.features.rectangularPatternFeatures.createInput(
                        entities, root.xConstructionAxis, value("3"), value("60 mm"),
                        adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
                    feature = root.features.rectangularPatternFeatures.add(inputs)
                elif case == "Mirror":
                    inputs = root.features.mirrorFeatures.createInput(entities, root.yZConstructionPlane)
                    feature = root.features.mirrorFeatures.add(inputs)
                else:
                    inputs = root.features.scaleFeatures.createInput(entities, root.originConstructionPoint, value("1.25"))
                    feature = root.features.scaleFeatures.add(inputs)
            feature.name = "Probe" + case
            design.computeAll()
            sample = {"file": case + ".f3d", "feature": {"name": feature.name, "kind": feature.objectType.split("::")[-1]},
                      "parameters": []}
            for index in range(root.modelParameters.count):
                parameter = root.modelParameters.item(index)
                sample["parameters"].append({
                    "name": parameter.name, "role": parameter.role, "value": parameter.value,
                    "unit": parameter.unit, "expression": parameter.expression,
                    "created_by": getattr(parameter.createdBy, "name", None),
                })
            options = design.exportManager.createFusionArchiveExportOptions(str(output / sample["file"]))
            if not design.exportManager.execute(options):
                raise RuntimeError("Tool feature export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output / "ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output / "complete.txt").write_text("Tool feature export finished; consult per-case errors.\n")
