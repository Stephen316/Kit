import hashlib
import json
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

folder = Path(__file__).resolve().parent / "TSpline"
folder.mkdir(exist_ok=True)
app = adsk.core.Application.get()
original = app.activeDocument
document = None
form = None
editing = False
report = {"fusion_version": app.version, "scope": "Owned native T-spline shape and vertex-edit format controls; no product codec claim", "cases": []}


def checkpoint():
    (folder / "Capture.json").write_text(json.dumps(report, indent=2) + "\n")


def coordinates(point):
    return [point.x, point.y, point.z]


def record(body):
    return {"name": body.name, "faces": body.faces.count, "edges": body.edges.count, "vertices": body.vertices.count, "control_points_cm": [coordinates(vertex.geometry) for vertex in body.vertices], "smooth_points_cm": [coordinates(vertex.smoothGeometry) for vertex in body.vertices], "bounds_cm": [coordinates(body.boundingBox.minPoint), coordinates(body.boundingBox.maxPoint)]}


def save_description(body, name):
    text = body.getTSMDescription()
    path = folder / (name + ".tsm")
    path.write_text(text)
    return {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}


try:
    for kind in ("Plane", "Box", "SymmetricBox"):
        case = {"kind": kind, "stages": {}}
        report["cases"].append(case)
        document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))
        form = design.rootComponent.features.formFeatures.add()
        form.name = "Owned " + kind
        if not form.startEdit():
            raise RuntimeError("Form edit did not start")
        editing = True
        bodies = form.tSplineBodies
        origin = adsk.core.Point3D.create(-0.7, 1.3, 0.5)
        x_axis = adsk.core.Vector3D.create(1, 0, 0)
        y_axis = adsk.core.Vector3D.create(0, 1, 0)
        if kind == "Plane":
            shape = bodies.createPlaneInput(origin, x_axis, y_axis, 1.7, 2.3)
            shape.xFaceCount = 2
            shape.yFaceCount = 3
        else:
            shape = bodies.createBoxInput(origin, x_axis, y_axis, 1.7, 2.3, 3.1)
            shape.xFaceCount = 2
            shape.yFaceCount = 2
            shape.zFaceCount = 2
            if kind == "SymmetricBox":
                shape.isXSymmetric = True
        body = bodies.addByShapeInput(shape)
        if body is None:
            raise RuntimeError("T-spline primitive was not created")
        body.name = "Owned " + kind + " Cage"
        case["stages"]["initial"] = record(body)
        case["initial_tsm"] = save_description(body, kind)
        if not form.finishEdit():
            raise RuntimeError("Form edit did not finish")
        editing = False
        if not design.computeAll() or form.healthState != 0:
            raise RuntimeError("Native T-spline form did not rebuild healthily")
        source = folder / (kind + ".f3d")
        if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(source))):
            raise RuntimeError("Native T-spline archive export failed")
        case["archive"] = {"file": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
        checkpoint()
        if not form.startEdit():
            raise RuntimeError("Form did not reopen for vertex edit")
        editing = True
        body = form.tSplineBodies.item(0)
        if not body.vertices.item(0).move(adsk.core.Vector3D.create(0.0, 0.0, 0.2)):
            raise RuntimeError("Native T-spline control vertex did not move")
        case["stages"]["vertex_edited"] = record(body)
        case["edited_tsm"] = save_description(body, kind + "Edited")
        if not form.finishEdit():
            raise RuntimeError("Edited form did not finish")
        editing = False
        if not design.computeAll() or form.healthState != 0:
            raise RuntimeError("Edited T-spline form did not rebuild healthily")
        edited = folder / (kind + "Edited.f3d")
        if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(edited))):
            raise RuntimeError("Edited T-spline archive export failed")
        case["edited_archive"] = {"file": edited.name, "sha256": hashlib.sha256(edited.read_bytes()).hexdigest()}
        case["status"] = "captured"
        document.close(False)
        document = None
        form = None
        checkpoint()
    report["status"] = "captured"
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
    raise
finally:
    if editing and form is not None:
        form.finishEdit()
    if document is not None:
        document.close(False)
    if original is not None and original.isValid:
        original.activate()
    report["documents_after"] = app.documents.count
    checkpoint()
