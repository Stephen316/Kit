"""Create small modeling-feature cases with API descriptions for format research."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("models-" + uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point = adsk.core.Point3D.create
    value = adsk.core.ValueInput.createByString
    operation = adsk.fusion.FeatureOperations
    cases = ["new_body", "join", "cut", "intersect", "symmetric_full", "symmetric_half",
             "two_sided", "through_all", "revolve_partial", "revolve_full"]
    if isinstance(context, dict) and "cases" in context:
        cases = context["cases"]
    try:
        for case in cases:
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            try:
                design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
                design.designType = adsk.fusion.DesignTypes.ParametricDesignType
                root = design.rootComponent
                if case.startswith("revolve"):
                    sketch = root.sketches.add(root.xYConstructionPlane)
                    sketch.name = "RevolveProfile"
                    sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(1, 0, 0), point(2, 1.5, 0))
                    inputs = root.features.revolveFeatures.createInput(
                        sketch.profiles.item(0), root.yConstructionAxis, operation.NewBodyFeatureOperation)
                    inputs.setAngleExtent(False, value("360 deg" if case == "revolve_full" else "65 deg"))
                    feature = root.features.revolveFeatures.add(inputs)
                    feature.name = "ProbeRevolve"
                    probes = [feature]
                else:
                    probes = []
                    if case in ("join", "cut", "intersect", "through_all"):
                        base = root.sketches.add(root.xYConstructionPlane)
                        base.name = "BaseProfile"
                        base.sketchCurves.sketchCircles.addByCenterRadius(point(0, 0, 0), 2)
                        seed = root.features.extrudeFeatures.addSimple(base.profiles.item(0), value("30 mm"), operation.NewBodyFeatureOperation)
                        seed.name = "BaseExtrusion"
                        probes.append(seed)
                    sketch = root.sketches.add(root.xYConstructionPlane)
                    sketch.name = "ProbeProfile"
                    sketch.sketchCurves.sketchCircles.addByCenterRadius(point(0, 0, 0), 1)
                    op = {"join": operation.JoinFeatureOperation, "cut": operation.CutFeatureOperation,
                          "intersect": operation.IntersectFeatureOperation,
                          "through_all": operation.CutFeatureOperation}.get(case, operation.NewBodyFeatureOperation)
                    inputs = root.features.extrudeFeatures.createInput(sketch.profiles.item(0), op)
                    distance = lambda text: adsk.fusion.DistanceExtentDefinition.create(value(text))
                    if case.startswith("symmetric"):
                        inputs.setSymmetricExtent(value("24 mm"), case == "symmetric_full")
                    elif case == "two_sided":
                        inputs.setTwoSidesExtent(distance("11 mm"), distance("23 mm"))
                    elif case == "through_all":
                        inputs.setOneSideExtent(adsk.fusion.ThroughAllExtentDefinition.create(),
                                                adsk.fusion.ExtentDirections.PositiveExtentDirection)
                    else:
                        inputs.setOneSideExtent(distance("50 mm" if case == "join" else "17 mm"),
                                                adsk.fusion.ExtentDirections.PositiveExtentDirection)
                    feature = root.features.extrudeFeatures.add(inputs)
                    feature.name = "ProbeExtrusion"
                    probes.append(feature)
                design.computeAll()
                sample = {"file": case + ".f3d", "features": [], "parameters": []}
                for feature in probes:
                    sample["features"].append({
                        "name": feature.name, "kind": feature.objectType.split("::")[-1],
                        "operation": feature.operation, "extent_type": getattr(feature, "extentType", None),
                        "extent_one": (feature.extentDefinition if case.startswith("revolve")
                                       else feature.extentOne).objectType.split("::")[-1],
                        "is_solid": feature.isSolid,
                    })
                for index in range(root.modelParameters.count):
                    parameter = root.modelParameters.item(index)
                    sample["parameters"].append({
                        "name": parameter.name, "role": parameter.role, "value": parameter.value,
                        "expression": parameter.expression, "unit": parameter.unit,
                        "created_by": getattr(parameter.createdBy, "name", None),
                    })
                options = design.exportManager.createFusionArchiveExportOptions(str(output / sample["file"]))
                if not design.exportManager.execute(options):
                    raise RuntimeError("Model sample export failed")
                truth["samples"].append(sample)
                (output / "ground_truth.json").write_text(json.dumps(truth, indent=2))
                doc.close(False)
            except Exception:
                truth["errors"].append({"case": case, "error": traceback.format_exc()})
                (output / "ground_truth.json").write_text(json.dumps(truth, indent=2))
                doc.close(False)
        (output / "complete.txt").write_text("Model generation finished; consult per-case errors.\n")
    except Exception:
        (output / "error.txt").write_text(traceback.format_exc())
