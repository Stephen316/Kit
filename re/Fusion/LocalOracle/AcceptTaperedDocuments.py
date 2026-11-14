import hashlib
import json
from math import hypot, isclose, pi, radians, tan
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion


root = Path(__file__).resolve().parent / "TaperedAuthoring"
preparation = json.loads((root / "Preparation.json").read_text())
app = adsk.core.Application.get()
original = app.activeDocument
doc = None
report = {
    "fusion_version": app.version,
    "scope": "Complete independently authored circular frustum documents and materials generated from dimensions; native geometry, mass, inertia, rollback, height and taper edits, rebuild, save and reopen",
    "cases": [],
}


def checkpoint():
    (root / "NativeAcceptance.json").write_text(json.dumps(report, indent=2) + "\n")


def observe(design):
    return {
        "parameters": [{"name": p.name, "value": p.value, "expression": p.expression} for p in design.allParameters],
        "timeline": [{"name": item.name, "health": item.healthState, "message": item.errorOrWarningMessage} for item in design.timeline],
        "bodies": [{"volume_cm3": b.volume, "area_cm2": b.physicalProperties.area, "min_cm": b.boundingBox.minPoint.asArray(), "max_cm": b.boundingBox.maxPoint.asArray(), "center_cm": b.physicalProperties.centerOfMass.asArray(), "mass_kg": b.physicalProperties.mass, "density_kg_per_cm3": b.physicalProperties.density, "material_name": b.material.name, "inertia_kg_cm2": b.physicalProperties.getXYZMomentsOfInertia(), "faces": b.faces.count, "edges": b.edges.count, "vertices": b.vertices.count} for b in design.rootComponent.bRepBodies],
    }


def require_geometry(design, lower, height, angle):
    if design.timeline.count != 2 or design.rootComponent.bRepBodies.count != 1 or design.rootComponent.sketches.count != 1:
        raise RuntimeError("Tapered extrusion feature or body count differs")
    if any(item.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState or item.errorOrWarningMessage for item in design.timeline):
        raise RuntimeError("Timeline contains a warning or error")
    upper = lower + height * tan(radians(angle))
    radius = max(lower, upper)
    sum_value = lower * lower + lower * upper + upper * upper
    expected_volume = pi * height * sum_value / 3
    expected_area = pi * (lower * lower + upper * upper + (lower + upper) * hypot(height, upper - lower))
    expected_center = height * (lower * lower + 2 * lower * upper + 3 * upper * upper) / (4 * sum_value)
    body = design.rootComponent.bRepBodies.item(0)
    actual = (*body.boundingBox.minPoint.asArray(), *body.boundingBox.maxPoint.asArray())
    expected = (-radius, -radius, 0, radius, radius, height)
    if not all(isclose(a, b, rel_tol=1e-8, abs_tol=1e-8) for a, b in zip(actual, expected)):
        raise RuntimeError(f"Tapered bounds differ: {actual} versus {expected}")
    if not isclose(body.volume, expected_volume, rel_tol=1e-8):
        raise RuntimeError("Tapered volume differs")
    if not isclose(body.physicalProperties.area, expected_area, rel_tol=1e-8):
        raise RuntimeError("Tapered surface area differs")
    if not all(isclose(a, b, rel_tol=1e-8, abs_tol=1e-8) for a, b in zip(body.physicalProperties.centerOfMass.asArray(), (0, 0, expected_center))):
        raise RuntimeError("Tapered mass center differs")
    if (body.faces.count, body.edges.count, body.vertices.count) != (3, 2, 2):
        raise RuntimeError("Tapered topology differs")
    density = 0.00287
    if body.material.name != "Independent frustum material" or not isclose(body.physicalProperties.density, density, rel_tol=1e-8) or not isclose(body.physicalProperties.mass, expected_volume * density, rel_tol=1e-8):
        raise RuntimeError("Independent tapered material mass differs")
    delta = upper - lower
    izz = pi * height * (lower**4 + lower**3 * upper + lower**2 * upper**2 + lower * upper**3 + upper**4) / 10
    ixx = izz / 2 + pi * height**3 * (lower**2 / 3 + lower * delta / 2 + delta**2 / 5)
    inertia = body.physicalProperties.getXYZMomentsOfInertia()
    if not inertia[0] or not all(isclose(a, b, rel_tol=1e-7, abs_tol=1e-8) for a, b in zip(inertia[1:], (ixx * density, ixx * density, izz * density, 0, 0, 0))):
        raise RuntimeError(f"Independent tapered inertia differs: {inertia}")


try:
    for source_case in preparation["cases"]:
        name = source_case["name"]
        source = root / (name + ".f3d")
        height = source_case["specification"]["LengthMm"] / 10
        lower = source_case["specification"]["RadiusMm"] / 10
        angle = source_case["specification"]["TaperDegrees"]
        case = {"name": name, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "stage": "importing"}
        report["cases"].append(case)
        checkpoint()
        if case["source_sha256"] != source_case["sha256"]:
            raise RuntimeError("Prepared source digest changed")
        doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
        if doc is None:
            raise RuntimeError("Typed tapered history did not open")
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        case["opened"] = observe(design)
        case["stage"] = "opened"
        checkpoint()
        require_geometry(design, lower, height, angle)
        design.timeline.markerPosition = 1
        case["rolled_back"] = observe(design)
        case["stage"] = "rolled_back"
        checkpoint()
        if design.rootComponent.bRepBodies.count != 0:
            raise RuntimeError("Rollback retained a solid")
        if not design.timeline.moveToEnd():
            raise RuntimeError("Timeline restoration failed")
        require_geometry(design, lower, height, angle)
        if not design.computeAll():
            raise RuntimeError("Complete tapered history rebuild failed")
        case["rebuilt"] = observe(design)
        require_geometry(design, lower, height, angle)
        design.userParameters.itemByName(source_case["parameters"]["height"]).expression = "27 mm"
        if not design.computeAll():
            raise RuntimeError("Height edit failed")
        case["height_edited"] = observe(design)
        case["stage"] = "height_edited"
        checkpoint()
        require_geometry(design, lower, 2.7, angle)
        design.allParameters.itemByName(source_case["parameters"]["taperAngle"]).expression = "-3 deg"
        if not design.computeAll():
            raise RuntimeError("Taper edit failed")
        case["taper_edited"] = observe(design)
        case["stage"] = "taper_edited"
        checkpoint()
        require_geometry(design, lower, 2.7, -3)
        saved = root / ("vendor_" + name + "27mmMinus3deg.f3d")
        if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
            raise RuntimeError("Tapered history export failed")
        doc.close(False)
        doc = None
        doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(saved)))
        if doc is None:
            raise RuntimeError("Saved tapered history did not reopen")
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        if not design.computeAll():
            raise RuntimeError("Reopened tapered history rebuild failed")
        case["reopened"] = observe(design)
        case["stage"] = "reopened"
        checkpoint()
        require_geometry(design, lower, 2.7, -3)
        case["saved_sha256"] = hashlib.sha256(saved.read_bytes()).hexdigest()
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
