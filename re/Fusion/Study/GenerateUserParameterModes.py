"""Capture study-owned user-parameter variants and actual API getter truth."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("userparameters-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    cases = ("length_mm", "length_in", "angle", "unitless", "comment", "favorite", "dependency_chain", "text")
    if isinstance(context, dict) and "cases" in context:
        cases = [case for case in cases if case in context["cases"]]

    def parameter_truth(parameter):
        is_text = parameter.unit.lower() == "text"
        result = {"name": parameter.name, "object_type": parameter.objectType,
                  "unit": parameter.unit, "expression": parameter.expression,
                  "comment": parameter.comment, "is_favorite": parameter.isFavorite,
                  "value_type": int(parameter.valueType),
                  "dependency_names": [p.name for p in parameter.dependencyParameters],
                  "dependent_names": [p.name for p in parameter.dependentParameters]}
        result["text_value" if is_text else "value"] = parameter.textValue if is_text else parameter.value
        return result

    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            parameters = design.userParameters
            value = adsk.core.ValueInput.createByString
            if case in ("length_mm", "comment", "favorite", "dependency_chain"):
                first = parameters.add("probeWidth", value("7.3 mm"), "mm", "Width Ø support" if case == "comment" else "")
                first.isFavorite = case == "favorite"
                if case == "dependency_chain":
                    parameters.add("probeScale", value("2.5"), "", "")
                    parameters.add("probeResult", value("probeWidth * probeScale + 1 mm"), "mm", "")
            elif case == "length_in":
                parameters.add("probeInches", value("1.125 in"), "in", "")
            elif case == "angle":
                parameters.add("probeAngle", value("31 deg"), "deg", "")
            elif case == "unitless":
                parameters.add("probeCount", value("7"), "", "")
            elif case == "text":
                parameters.add("probeLabel", value("'Steel Ø'"), "Text", "Material label")
            if not design.computeAll():
                raise RuntimeError("User parameter computation failed")
            sample = {"file": case+".f3d", "user_parameters": [parameter_truth(p) for p in parameters]}
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("User parameter export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("User parameter generation finished; consult errors.\n")
