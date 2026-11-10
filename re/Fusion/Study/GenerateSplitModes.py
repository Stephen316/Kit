"""Local planar split tools, extension flags and multiple target bodies."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("splits-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    for case in ("yz_extend", "yz_no_extend", "xz_extend", "offset_plane", "multiple_bodies"):
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sketches = []
            for index in range(2 if case == "multiple_bodies" else 1):
                sketch = root.sketches.add(root.xYConstructionPlane)
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(-2+6*index, -1, 0), point(2+6*index, 1, 0))
                root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value("20 mm"),
                                                       adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                sketches.append(sketch)
            tool = root.xZConstructionPlane if case in ("xz_extend", "multiple_bodies") else root.yZConstructionPlane
            if case == "offset_plane":
                plane_input = root.constructionPlanes.createInput()
                plane_input.setByOffset(root.xYConstructionPlane, value("10 mm"))
                tool = root.constructionPlanes.add(plane_input)
                tool.name = "SplitPlane"
            bodies = adsk.core.ObjectCollection.create()
            for body in root.bRepBodies:
                bodies.add(body)
            settings = {"input_body_count": bodies.count, "tool_name": tool.name,
                        "tool_origin_cm": tool.geometry.origin.asArray(), "tool_normal": tool.geometry.normal.asArray(),
                        "tool_evidence": "Actual API input construction plane"}
            inputs = root.features.splitBodyFeatures.createInput(bodies, tool, case != "yz_no_extend")
            feature = root.features.splitBodyFeatures.add(inputs)
            feature.name = "ProbeSplit"
            design.computeAll()
            settings.update(is_tool_extended=feature.isSplittingToolExtended, result_body_count=root.bRepBodies.count)
            sample = {"file": case+".f3d", "settings": settings}
            options = design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))
            if not design.exportManager.execute(options):
                raise RuntimeError("Split export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Split exports finished; consult errors.\n")
