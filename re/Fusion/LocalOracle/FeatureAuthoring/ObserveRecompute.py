import hashlib
import json
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion


root = Path(__file__).resolve().parent
folder = root / "Recompute"
preparation = json.loads((folder / globals().get("PREPARATION", "Preparation.json")).read_text())
controls = {c["name"]: c for c in json.loads((root / "Controls" / "Capture.json").read_text())["controls"]}
app = adsk.core.Application.get()
report = {"fusion_version": app.version, "documents_before": app.documents.count, "scope": "Native observation of same-source controls whose BRep journal was truncated before later features; measures what Fusion shows on open and after computeAll", "cases": []}


def checkpoint():
    (folder / globals().get("OUTPUT", "Observation.json")).write_text(json.dumps(report, indent=2).replace(str(Path(__file__).resolve().parents[4]) + "/", "").replace(str(Path.home()), "~") + "\n")


def observe(design):
    comp = design.rootComponent
    return {
        "timeline": [{"name": i.name, "health": i.healthState, "message": i.errorOrWarningMessage, "rolled_back": i.isRolledBack} for i in design.timeline],
        "bodies": [{"name": b.name, "volume_cm3": b.volume, "area_cm2": b.area, "faces": b.faces.count, "edges": b.edges.count, "vertices": b.vertices.count, "min_cm": b.boundingBox.minPoint.asArray(), "max_cm": b.boundingBox.maxPoint.asArray()} for b in comp.bRepBodies],
    }


def signature(observed):
    return sorted((round(b["volume_cm3"], 6), b["faces"], b["edges"], b["vertices"]) for b in observed["bodies"])


try:
    for entry in preparation["cases"]:
        source = folder / entry["target"]
        case = {"name": entry["name"], "control": entry["source"][:-4], "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
        report["cases"].append(case)
        doc = None
        try:
            doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            try:
                case["opened"] = observe(design)
            except Exception:
                case["opened_error"] = traceback.format_exc().splitlines()[-1]
                case["opened"] = {"timeline": [], "bodies": []}
            expected = signature(controls[case["control"]]["observed"])
            case["expected_signature"] = expected
            case["opened_matches_control"] = signature(case["opened"]) == expected
            case["compute_all"] = design.computeAll()
            case["recomputed"] = observe(design)
            case["recomputed_matches_control"] = signature(case["recomputed"]) == expected
            markers = []
            for position in range(design.timeline.count + 1):
                design.timeline.markerPosition = position
                markers.append({"position": position, "bodies": signature(observe(design))})
            design.timeline.moveToEnd()
            case["markers"] = markers
            case["final"] = signature(observe(design))
            case["status"] = "observed"
        except Exception:
            case["status"] = "failed"
            case["traceback"] = traceback.format_exc()
        finally:
            if doc is not None:
                doc.close(False)
            checkpoint()
    report["status"] = "observed"
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
finally:
    report["documents_after"] = app.documents.count
    checkpoint()
