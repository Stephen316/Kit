import hashlib
import json
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion


root = Path(__file__).resolve().parent
output = root / "Features"
output.mkdir(exist_ok=True)
app = adsk.core.Application.get()
original = app.activeDocument
doc = None
report = {"operation": "controlled_circle_extrusion_capture", "fusion_version": app.version, "samples": []}


def capture(name, design):
    target = output / (name + ".f3d")
    if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(target))):
        raise RuntimeError("Archive export failed: " + name)
    entities = json.loads(app.executeTextCommand("PAsset.EntityIds"))
    properties = []
    for identity in entities:
        entry = {"identity": identity}
        if identity["entityId"] < 0:
            entry["skipped"] = "Named root entity; numeric property query unavailable"
            properties.append(entry)
            continue
        try:
            entry["properties"] = json.loads(app.executeTextCommand("PEntity.Properties " + str(identity["entityId"])))
        except Exception:
            entry["error"] = traceback.format_exc()
        properties.append(entry)
    (output / (name + ".entities.json")).write_text(json.dumps(properties, indent=2) + "\n")
    bodies = []
    for body in design.rootComponent.bRepBodies:
        box = body.boundingBox
        bodies.append({"name": body.name, "volume_cm3": body.volume, "faces": body.faces.count, "edges": body.edges.count, "vertices": body.vertices.count, "min_cm": box.minPoint.asArray(), "max_cm": box.maxPoint.asArray()})
    report["samples"].append({
        "file": target.name,
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "parameters": [{"name": p.name, "expression": p.expression, "value": p.value, "unit": p.unit} for p in design.allParameters],
        "timeline": [{"index": item.index, "name": item.name, "type": item.entity.objectType if item.entity else None} for item in design.timeline],
        "bodies": bodies,
        "property_count": len(properties),
        "property_error_count": sum("error" in entry for entry in properties),
    })
    (output / "Capture.json").write_text(json.dumps(report, indent=2) + "\n")


try:
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    depth = design.userParameters.add("depthLength", adsk.core.ValueInput.createByString("7 mm"), "mm", "extrusion depth control")
    sketch = design.rootComponent.sketches.add(design.rootComponent.xYConstructionPlane)
    sketch.name = "Radius10mm"
    sketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), 1.0)
    capture("circle_sketch", design)
    extrude = design.rootComponent.features.extrudeFeatures.addSimple(sketch.profiles.item(0), adsk.core.ValueInput.createByString("depthLength"), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extrude.name = "ControlledExtrusion"
    if not design.computeAll():
        raise RuntimeError("Initial extrusion rebuild failed")
    capture("extrude_07mm", design)
    depth.expression = "13 mm"
    if not design.computeAll():
        raise RuntimeError("Edited extrusion rebuild failed")
    capture("extrude_13mm", design)
    report["schema_command_result"] = app.executeTextCommand('Document.DumpAcitveDocSchema "' + str(output / "FeatureSchema.xml") + '"')
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
