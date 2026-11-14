import hashlib
import json
from math import isclose
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion


root = Path(__file__).resolve().parent / "Frustums"
inputs = json.loads((root / "Preparation.json").read_text())["cases"]
app = adsk.core.Application.get()
original = app.activeDocument
doc = None
report = {"fusion_version": app.version, "scope": "Independent production SMT/SMB analytic frusta; standalone geometry only, no parametric feature history", "cases": []}


def checkpoint():
    (root / "NativeAcceptance.json").write_text(json.dumps(report, indent=2) + "\n")


def observe(design, expected):
    if design.rootComponent.bRepBodies.count != 1:
        raise RuntimeError("Expected one imported frustum body")
    body = design.rootComponent.bRepBodies.item(0)
    props = body.physicalProperties
    value = {"solid": body.isSolid, "faces": body.faces.count, "edges": body.edges.count, "vertices": body.vertices.count, "volume_cm3": body.volume, "area_cm2": props.area, "center_cm": props.centerOfMass.asArray(), "min_cm": body.boundingBox.minPoint.asArray(), "max_cm": body.boundingBox.maxPoint.asArray()}
    if not value["solid"] or (value["faces"], value["edges"], value["vertices"]) != (3, 2, 2):
        raise RuntimeError("Frustum topology differs")
    for key in ("volume_cm3", "area_cm2"):
        if not isclose(value[key], expected[key], rel_tol=1e-7, abs_tol=1e-8):
            raise RuntimeError("Frustum measurement differs: " + key)
    for key in ("center_cm", "min_cm", "max_cm"):
        if not all(isclose(a, b, rel_tol=1e-7, abs_tol=1e-8) for a, b in zip(value[key], expected[key])):
            raise RuntimeError("Frustum spatial measurement differs: " + key)
    return value


try:
    for entry in inputs:
        source = root / entry["file"]
        if hashlib.sha256(source.read_bytes()).hexdigest() != entry["sha256"]:
            raise RuntimeError("Frustum artifact digest changed")
        case = {"name": entry["name"], "format": entry["format"], "source_sha256": entry["sha256"], "stage": "importing"}
        report["cases"].append(case)
        checkpoint()
        if entry["format"] == "smt":
            doc = app.importManager.importToNewDocument(app.importManager.createSMTImportOptions(str(source)))
            if doc is None:
                raise RuntimeError("Independent frustum SMT did not open")
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        else:
            bodies = adsk.fusion.TemporaryBRepManager.get().createFromFile(str(source))
            if bodies is None or bodies.count != 1:
                raise RuntimeError("Independent frustum SMB did not import")
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.DirectDesignType
            if design.rootComponent.bRepBodies.add(bodies.item(0)) is None:
                raise RuntimeError("Could not add frustum to a native document")
        case["opened"] = observe(design, entry["expected"])
        case["stage"] = "opened"
        checkpoint()
        saved = root / ("vendor_" + entry["name"] + "_" + entry["format"] + ".f3d")
        if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
            raise RuntimeError("Native frustum export failed")
        doc.close(False)
        doc = None
        doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(saved)))
        if doc is None:
            raise RuntimeError("Native frustum save did not reopen")
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        case["reopened"] = observe(design, entry["expected"])
        case["saved_sha256"] = hashlib.sha256(saved.read_bytes()).hexdigest()
        case["stage"] = "reopened"
        case["status"] = "accepted"
        doc.close(False)
        doc = None
        checkpoint()
    report["status"] = "accepted"
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
    raise
finally:
    if doc is not None:
        doc.close(False)
    if original is not None and original.isValid:
        original.activate()
    report["documents_after"] = app.documents.count
    checkpoint()
