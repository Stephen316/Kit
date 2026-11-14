"""Open journal-swap variants and record what Fusion shows. Run through RunLocked.mjs."""

import hashlib
import json
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion


root = Path(__file__).resolve().parent
folder = root / globals().get("FOLDER", "Variants")
manifest = json.loads((folder / "Manifest.json").read_text())
app = adsk.core.Application.get()
original = app.activeDocument
OWN = {"Fillet", "Chamfer", "Shell", "FilletShell", "MultiFeature", "Untitled"} | set(manifest)
report = {"fusion_version": app.version, "documents_before": app.documents.count, "scope": "Native open of Kit journal-swap variants; diagnostic evidence only", "leftovers_closed": [], "cases": []}


def checkpoint():
    (folder / "Observation.json").write_text(json.dumps(report, indent=2).replace(str(Path(__file__).resolve().parents[4]) + "/", "").replace(str(Path.home()), "~") + "\n")


def close_leftovers(before):
    for doc in list(app.documents):
        if doc not in before and doc.isValid:
            report["leftovers_closed"].append(doc.name)
            doc.close(False)


def observe(design):
    bodies = []
    for b in design.rootComponent.bRepBodies:
        entry = {"name": b.name}
        try:
            entry.update({"volume_cm3": b.volume, "area_cm2": b.area, "faces": b.faces.count, "edges": b.edges.count, "vertices": b.vertices.count})
        except Exception:
            entry["error"] = traceback.format_exc().splitlines()[-1]
        bodies.append(entry)
    timeline = [{"name": i.name, "health": i.healthState, "message": i.errorOrWarningMessage} for i in design.timeline]
    return {"timeline": timeline, "bodies": bodies}


for doc in list(app.documents):
    if doc.isValid and doc.name.split(" ")[0] in OWN:
        report["leftovers_closed"].append(doc.name)
        doc.close(False)
report["documents_after_cleanup"] = app.documents.count
try:
    for name, entry in manifest.items():
        source = folder / entry["file"]
        case = {"name": name, "purpose": entry.get("purpose"), "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
        report["cases"].append(case)
        before = list(app.documents)
        try:
            doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            case["opened"] = observe(design)
            markers = []
            for position in range(design.timeline.count + 1):
                design.timeline.markerPosition = position
                markers.append(observe(design)["bodies"])
            design.timeline.moveToEnd()
            case["markers"] = markers
            case["computed"] = design.computeAll()
            case["recomputed"] = observe(design)
            case["status"] = "opened"
        except Exception:
            case["status"] = "failed"
            case["error"] = traceback.format_exc().splitlines()[-1]
        finally:
            close_leftovers(before)
            checkpoint()
    report["status"] = "observed"
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
finally:
    if original is not None and original.isValid:
        original.activate()
    report["documents_after"] = app.documents.count
    checkpoint()
