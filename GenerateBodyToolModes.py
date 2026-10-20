"""Controlled scale, mirror and shell modes with local API reference values."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CASES = ("scale_uniform", "scale_nonuniform", "mirror_xy", "mirror_xz", "mirror_yz",
         "shell_inside", "shell_outside", "shell_both", "shell_rounded")


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("bodymodes-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    for case in CASES:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(1, 1, 0), point(5, 4, 0))
            seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value("20 mm"),
                                                         adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            seed.name = "SeedExtrusion"
            entities = adsk.core.ObjectCollection.create()
            settings = {}
            if case.startswith("scale"):
                entities.add(root.bRepBodies.item(0))
                inputs = root.features.scaleFeatures.createInput(entities, root.originConstructionPoint,
                                                                 value("0.65" if case == "scale_holdout" else "1.75"))
                if case == "scale_nonuniform":
                    if not inputs.setToNonUniform(value("1.2"), value("0.8"), value("1.6")):
                        raise RuntimeError("Nonuniform scale rejected")
                feature = root.features.scaleFeatures.add(inputs)
                # ScaleFeature.point requires an edit rollback even just to read it.
                # Record the actual input construction point without changing history.
                settings = {"is_uniform": feature.isUniform, "point_cm": root.originConstructionPoint.geometry.asArray(),
                            "point_evidence": "API input: root.originConstructionPoint"}
                if feature.isUniform:
                    settings["factor"] = feature.scaleFactor.value
                else:
                    settings["factors"] = [feature.xScale.value, feature.yScale.value, feature.zScale.value]
            elif case.startswith("mirror"):
                entities.add(root.bRepBodies.item(0))
                plane = {"mirror_xy": root.xYConstructionPlane, "mirror_xy_combine": root.xYConstructionPlane,
                         "mirror_xz": root.xZConstructionPlane,
                         "mirror_yz": root.yZConstructionPlane}[case]
                inputs = root.features.mirrorFeatures.createInput(entities, plane)
                inputs.isCombine = case == "mirror_xy_combine"
                feature = root.features.mirrorFeatures.add(inputs)
                geometry = feature.mirrorPlane.geometry
                settings = {"is_combine": feature.isCombine, "plane_name": feature.mirrorPlane.name,
                            "plane_origin_cm": geometry.origin.asArray(), "plane_normal": geometry.normal.asArray()}
            else:
                entities.add(seed.endFaces.item(0))
                inputs = root.features.shellFeatures.createInput(entities, case == "shell_tangent")
                inputs.insideThickness = value("1.5 mm" if case != "shell_outside" else "0 mm")
                inputs.outsideThickness = value("0.75 mm" if case in ("shell_outside", "shell_both") else "0 mm")
                if case == "shell_rounded":
                    inputs.shellType = adsk.fusion.ShellTypes.RoundedOffsetShellType
                feature = root.features.shellFeatures.add(inputs)
                settings = {"inside_cm": feature.insideThickness.value if feature.insideThickness else None,
                            "outside_cm": feature.outsideThickness.value if feature.outsideThickness else None,
                            "shell_type": feature.shellType, "is_tangent_chain": feature.isTangentChain}
            feature.name = "ProbeBodyTool"
            design.computeAll()
            sample = {"file": case+".f3d", "kind": feature.objectType.split("::")[-1], "settings": settings,
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            options = design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))
            if not design.exportManager.execute(options):
                raise RuntimeError("Body tool export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Body tool exports finished; consult errors.\n")
