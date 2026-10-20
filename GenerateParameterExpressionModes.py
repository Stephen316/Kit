"""Capture actual dependency getters for bounded arithmetic and unsupported forms."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = {
    "product_sum": ("probeWidth * probeScale + 1 mm", "mm"),
    "parenthesized": ("(probeWidth + probeAllowance) / probeScale", "mm"),
    "repeated_reference": ("probeWidth + probeWidth + probeAllowance", "mm"),
    "unary_reference": ("-probeWidth + 20 mm", "mm"),
    "function_outside_subset": ("sqrt(probeScale)", ""),
    "text_name_literal": ("'probeWidth literal'", "Text"),
}


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("parameterexpressions-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    cases = context.get("cases", CASES) if isinstance(context, dict) else CASES
    value = adsk.core.ValueInput.createByString
    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            parameters = design.userParameters
            parameters.add("probeWidth", value("7.3 mm"), "mm", "")
            parameters.add("probeScale", value("2.5"), "", "")
            parameters.add("probeAllowance", value("1.2 mm"), "mm", "")
            expression, unit = CASES[case]
            parameters.add("probeResult", value(expression), unit, "")
            if not design.computeAll():
                raise RuntimeError("Expression computation failed")
            actual = []
            for parameter in parameters:
                item = {"name": parameter.name, "unit": parameter.unit, "expression": parameter.expression,
                        "value_type": int(parameter.valueType),
                        "dependency_names": [p.name for p in parameter.dependencyParameters],
                        "dependent_names": [p.name for p in parameter.dependentParameters]}
                item["text_value" if parameter.unit.lower() == "text" else "value"] = (
                    parameter.textValue if parameter.unit.lower() == "text" else parameter.value)
                actual.append(item)
            design.timeline.moveToEnd()
            sample = {"file": case+".f3d", "requested_expression": expression, "parameters": actual}
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Expression export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Parameter expression capture finished; consult errors.\n")
