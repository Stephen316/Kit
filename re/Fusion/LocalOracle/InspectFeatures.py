import hashlib
import json
from pathlib import Path
import traceback

import adsk.core


output = Path(__file__).resolve().parent / "Features"
app = adsk.core.Application.get()
original = app.activeDocument
report = {"fusion_version": app.version, "samples": []}
try:
    for name in ("circle_sketch", "extrude_07mm", "extrude_13mm"):
        source = output / (name + ".f3d")
        doc = None
        properties = []
        try:
            doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
            entities = json.loads(app.executeTextCommand("PAsset.EntityIds"))
            for identity in entities:
                entry = {"identity": identity}
                if identity["entityId"] < 0:
                    entry["skipped"] = "Named root entity; numeric property query unavailable"
                else:
                    try:
                        entry["properties"] = json.loads(app.executeTextCommand("PEntity.Properties " + str(identity["entityId"])))
                    except Exception:
                        entry["error"] = traceback.format_exc()
                properties.append(entry)
            (output / (name + ".entities.json")).write_text(json.dumps(properties, indent=2) + "\n")
            report["samples"].append({"file": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "entity_count": len(entities), "property_count": sum("properties" in entry for entry in properties), "error_count": sum("error" in entry for entry in properties), "skipped_count": sum("skipped" in entry for entry in properties)})
        finally:
            if doc is not None:
                doc.close(False)
    report["status"] = "inspected"
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
    raise
finally:
    if original is not None and original.isValid:
        original.activate()
    (output / "GraphCapture.json").write_text(json.dumps(report, indent=2) + "\n")
