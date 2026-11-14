import hashlib
import json
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion


root = Path(__file__).resolve().parent
output = root / "RectangleAuthoring"
app = adsk.core.Application.get()
original = app.activeDocument
docs = []
report = {"fusion_version": app.version, "scope": "Native diagnosis of authored-body material and mass properties; assignment uses a native control only for evidence, not production writer input", "cases": []}


def observe(body):
    props = body.physicalProperties
    result = {"body_volume_cm3": body.volume, "volume_cm3": props.volume, "area_cm2": props.area, "mass_kg": props.mass, "density_kg_per_cm3": props.density, "center_cm": props.centerOfMass.asArray(), "moments_kg_cm2": props.getXYZMomentsOfInertia()}
    try:
        material = body.material
        result["material"] = None if material is None else {"id": material.id, "name": material.name}
    except Exception as error:
        result["material_error"] = str(error)
    return result


try:
    control = root.parents[0] / "Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d"
    native_doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(control)))
    docs.append(native_doc)
    native_design = adsk.fusion.Design.cast(native_doc.products.itemByProductType("DesignProductType"))
    native_body = native_design.rootComponent.bRepBodies.item(0)
    report["control"] = observe(native_body)
    native_material = native_body.material
    for relative in ("RectangleAuthoring/Initial/ProductionCuboid.f3d", "Authored/ProductionExtrusion.f3d"):
        source = root / relative
        doc = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
        docs.append(doc)
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        body = design.rootComponent.bRepBodies.item(0)
        case = {"source": relative, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "opened": observe(body)}
        report["cases"].append(case)
        material = design.materials.addByCopy(native_material, "Kit Density Control")
        if material is None:
            raise RuntimeError("Native material copy failed")
        body.material = material
        case["assigned"] = observe(body)
        if not design.computeAll():
            raise RuntimeError("Native material assignment rebuild failed")
        case["rebuilt"] = observe(body)
        saved = output / ("mass_probe_" + source.name)
        if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
            raise RuntimeError("Native mass probe export failed")
        case["saved"] = saved.name
        case["saved_sha256"] = hashlib.sha256(saved.read_bytes()).hexdigest()
        doc.close(False)
        docs.pop()
    report["status"] = "captured"
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
    raise
finally:
    for doc in reversed(docs):
        if doc is not None and doc.isValid:
            doc.close(False)
    if original is not None and original.isValid:
        original.activate()
    report["documents_after"] = app.documents.count
    (output / "MassProbe.json").write_text(json.dumps(report, indent=2) + "\n")
