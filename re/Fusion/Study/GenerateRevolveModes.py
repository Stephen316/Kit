"""Controlled revolve modes, operations and solid/surface settings."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CASES = ("positive", "negative", "symmetric", "two_sided", "join", "cut", "intersect", "surface", "axis_x")


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("revolvemodes-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    ops = adsk.fusion.FeatureOperations
    for case in CASES:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            if case in ("join", "cut", "intersect"):
                base = root.sketches.add(root.xYConstructionPlane)
                base.sketchCurves.sketchLines.addTwoPointRectangle(point(1, 0, 0), point(4, 3, 0))
                inputs = root.features.revolveFeatures.createInput(base.profiles.item(0), root.yConstructionAxis,
                                                                  ops.NewBodyFeatureOperation)
                inputs.setAngleExtent(False, value("360 deg"))
                root.features.revolveFeatures.add(inputs)
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.name = "ProbeRevolveProfile"
            if case in ("join", "cut", "intersect"):
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(2, 1, 0), point(5, 2, 0))
            else:
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(1, 1, 0), point(3, 4, 0))
            operation = {"join": ops.JoinFeatureOperation, "cut": ops.CutFeatureOperation,
                         "intersect": ops.IntersectFeatureOperation}.get(case, ops.NewBodyFeatureOperation)
            axis = root.xConstructionAxis if case == "axis_x" else root.yConstructionAxis
            inputs = root.features.revolveFeatures.createInput(sketch.profiles.item(0), axis, operation)
            if case == "two_sided":
                inputs.setTwoSideAngleExtent(value("60 deg"), value("25 deg"))
            else:
                inputs.setAngleExtent(case == "symmetric", value("-75 deg" if case == "negative" else "65 deg"))
            inputs.isSolid = case != "surface"
            inputs.isProjectAxis = case == "project_axis"
            feature = root.features.revolveFeatures.add(inputs)
            feature.name = "ProbeRevolve"
            design.computeAll()
            definition = feature.extentDefinition
            settings = {"operation": feature.operation, "is_solid": feature.isSolid,
                        "is_project_axis": feature.isProjectAxis, "axis_name": axis.name,
                        "axis_direction": axis.geometry.direction.asArray(),
                        "extent_kind": definition.objectType.split("::")[-1]}
            for attr in ("angle", "angleOne", "angleTwo"):
                if hasattr(definition, attr):
                    settings[attr] = getattr(definition, attr).value
            if hasattr(definition, "isSymmetric"):
                settings["is_symmetric"] = definition.isSymmetric
            sample = {"file": case+".f3d", "settings": settings,
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            options = design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))
            if not design.exportManager.execute(options):
                raise RuntimeError("Revolve export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Revolve exports finished; consult errors.\n")
