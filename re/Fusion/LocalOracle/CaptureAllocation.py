import hashlib
import json
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion


output = Path(__file__).resolve().parent / "Allocation"
output.mkdir(exist_ok=True)
report = {"operation": "controlled_parameter_allocation_capture", "samples": []}
app = adsk.core.Application.get()
original = app.activeDocument
doc = None


def capture(name, design):
    target = output / (name + ".f3d")
    options = design.exportManager.createFusionArchiveExportOptions(str(target))
    if not design.exportManager.execute(options):
        raise RuntimeError("Fusion archive export failed: " + name)
    report["samples"].append({
        "file": target.name,
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "parameters": [
            {"name": p.name, "expression": p.expression, "value": p.value, "unit": p.unit}
            for p in design.allParameters
        ],
        "timeline_count": design.timeline.count,
    })
    (output / "Capture.json").write_text(json.dumps(report, indent=2) + "\n")


try:
    report["fusion_version"] = app.version
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    capture("empty", design)
    alpha = design.userParameters.add("alphaLength", adsk.core.ValueInput.createByString("7.3 mm"), "mm", "first allocation")
    design.userParameters.add("betaLength", adsk.core.ValueInput.createByString("19 mm"), "mm", "survives deletion")
    capture("two_parameters", design)
    if not alpha.deleteMe():
        raise RuntimeError("Parameter deletion failed")
    capture("deleted_first", design)
    design.userParameters.add("gammaLength", adsk.core.ValueInput.createByString("23 mm"), "mm", "after deletion")
    capture("added_third", design)
    schema = output / "ParameterSchema.xml"
    report["schema_command_result"] = app.executeTextCommand('Document.DumpAcitveDocSchema "' + str(schema) + '"')
    report["schema_exists"] = schema.exists()
    report["status"] = "captured"
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
    raise
finally:
    if doc is not None:
        doc.close(False)
    if original is not None and original.isValid:
        original.activate()
    (output / "Capture.json").write_text(json.dumps(report, indent=2) + "\n")
