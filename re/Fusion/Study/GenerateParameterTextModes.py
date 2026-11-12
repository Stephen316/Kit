"""Capture multiline parameter strings and model-parameter favorites."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ("user_multiline_comment", "text_multiline_value", "model_favorite_false",
         "model_favorite_true", "model_multiline_comment")


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("parametertexts-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    cases = context.get("cases", CASES) if isinstance(context, dict) else CASES
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            multiline = "First Ø line\nSecond\tcolumn\r\nThird line"
            if case.startswith("user_"):
                parameter = design.userParameters.add("probeWidth", value("7.3 mm"), "mm", multiline)
            elif case == "text_multiline_value":
                parameter = design.userParameters.add("probeLabel", value("'Initial'"), "Text", "")
                parameter.textValue = multiline
            else:
                root = design.rootComponent
                sketch = root.sketches.add(root.xYConstructionPlane)
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0, 0, 0), point(2, 1, 0))
                feature = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value("7.3 mm"),
                                                               adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                feature.name = "ProbeExtrude"
                parameter = next(p for p in root.modelParameters if p.role == "AlongDistance"
                                 and p.createdBy and p.createdBy.name == feature.name)
                parameter.isFavorite = case == "model_favorite_true"
                if case == "model_multiline_comment":
                    parameter.comment = multiline
            actual = {"name": parameter.name, "object_type": parameter.objectType,
                      "unit": parameter.unit, "expression": parameter.expression,
                      "comment": parameter.comment, "is_favorite": parameter.isFavorite,
                      "value_type": int(parameter.valueType)}
            if adsk.fusion.ModelParameter.cast(parameter):
                actual.update(role=parameter.role, created_by=parameter.createdBy.name)
            if parameter.unit.lower() == "text":
                actual["text_value"] = parameter.textValue
            else:
                actual["value"] = parameter.value
            design.timeline.moveToEnd()
            sample = {"file": case+".f3d", "parameter": actual,
                      "requested_multiline": multiline if "multiline" in case else None}
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Parameter text export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Parameter text capture finished; consult errors.\n")
