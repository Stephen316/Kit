import hashlib
import json
import lzma
from math import isclose
from pathlib import Path
import traceback

import adsk.core
import adsk.fusion

root = Path(__file__).resolve().parents[3]
folder = Path(__file__).resolve().parent / "ParaMesh"
preparation = json.loads((folder / "Preparation.json").read_text())
app = adsk.core.Application.get()
original = app.activeDocument
document = None
report = {"fusion_version": app.version, "scope": preparation["scope"], "cases": []}
observations = {}


def checkpoint():
    raw = json.dumps(observations, separators=(",", ":"), allow_nan=False).encode()
    encoded = lzma.compress(raw)
    (folder / "NativeObservations.json.xz").write_bytes(encoded)
    report["observation_sha256"] = hashlib.sha256(encoded).hexdigest()
    (folder / "NativeAcceptance.json").write_text(json.dumps(report, indent=2) + "\n")


def point(value):
    return [value.x, value.y, value.z]


def bounds(value):
    return [point(value.minPoint), point(value.maxPoint)]


def digest(values):
    normalized = [round(value, 12) if isinstance(value, float) else value for value in values]
    return hashlib.sha256(json.dumps(normalized, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def observe(design, key):
    result = {"marker": design.timeline.markerPosition, "parameters": [{"name": p.name, "expression": p.expression, "value": p.value, "unit": p.unit} for p in design.allParameters], "timeline": [{"name": item.name, "health": item.healthState, "message": item.errorOrWarningMessage, "group": item.isGroup} for item in design.timeline], "meshes": []}
    details = []
    for body in design.rootComponent.meshBodies:
        mesh = body.mesh
        group_ids = list(mesh.triangleFaceGroupTempIds)
        identities = list(dict.fromkeys(group_ids))
        partition = [identities.index(value) for value in group_ids]
        geometry = {"positions": list(mesh.nodeCoordinatesAsDouble), "normals": list(mesh.normalVectorsAsDouble), "corners": list(mesh.triangleNodeIndices), "groups": partition}
        details.append(geometry)
        groups = sorted([{"area_cm2": group.area, "bounds_cm": bounds(group.boundingBox), "centroid_cm": point(group.centroid), "planar": group.isPlanar} for group in body.faceGroups], key=lambda item: (item["centroid_cm"], item["area_cm2"]))
        result["meshes"].append({"name": body.name, "vertices": mesh.nodeCount, "triangles": mesh.triangleCount, "quads": mesh.quadCount, "polygons": mesh.polygonCount, "closed": body.isClosed, "oriented": body.isOriented, "area_cm2": body.area, "volume_cm3": body.volume, "bounds_cm": bounds(body.boundingBox), "face_groups": groups, "geometry_sha256": {name: digest(values) for name, values in geometry.items()}})
    observations[key] = details
    return result


def same(left, right, path="state"):
    if isinstance(left, float) and isinstance(right, (float, int)):
        if not isclose(left, right, rel_tol=1e-8, abs_tol=1e-8):
            raise RuntimeError(f"Native control mismatch at {path}: {left} != {right}")
    elif isinstance(left, dict) and isinstance(right, dict):
        if left.keys() != right.keys():
            raise RuntimeError("Native observation fields differ")
        for key in left:
            same(left[key], right[key], path + "." + str(key))
    elif isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            raise RuntimeError(f"Native lengths differ at {path}: {len(left)} != {len(right)}")
        for index, (a, b) in enumerate(zip(left, right)):
            same(a, b, path + "." + str(index))
    elif left != right:
        raise RuntimeError(f"Native control differs at {path}: {left!r} != {right!r}")


try:
    for prepared in preparation["cases"]:
        case = {"name": prepared["name"], "variants": []}
        report["cases"].append(case)
        for label, relative, expected in [("Control", prepared["source_file"], prepared["source_sha256"]), ("Reemitted", prepared["output_file"], prepared["output_sha256"])]:
            source = root / relative
            if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
                raise RuntimeError("Prepared mesh archive changed")
            result = {"name": label, "source_sha256": expected, "stages": {}}
            case["variants"].append(result)
            checkpoint()
            document = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(source)))
            if document is None:
                raise RuntimeError("Mesh archive did not open")
            design = adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))
            prefix = prepared["name"] + label
            result["stages"]["opened"] = observe(design, prefix + "Opened")
            checkpoint()
            expected_count = 4 if prepared["name"] == "PreparedMesh00" else 3
            if design.timeline.count != expected_count or design.rootComponent.meshBodies.count != 1:
                raise RuntimeError("Unexpected native mesh control layout")
            feature = design.timeline.item(expected_count - 1).entity
            if not feature.timelineObject.rollTo(True):
                raise RuntimeError("Mesh feature rollback failed")
            result["stages"]["rolled_back"] = observe(design, prefix + "RolledBack")
            if not design.timeline.moveToEnd() or not design.computeAll():
                raise RuntimeError("Mesh restoration/rebuild failed")
            result["stages"]["rebuilt"] = observe(design, prefix + "Rebuilt")
            if prepared["name"] == "PreparedMesh00":
                if not feature.timelineObject.rollTo(True):
                    raise RuntimeError("Mesh selection edit rollback failed")
                body = adsk.fusion.MeshBody.cast(feature.mesh)
                if body is None or body.faceGroups.count != 8:
                    raise RuntimeError("Expected eight input face groups")
                feature.inputFaceGroups = list(body.faceGroups)
            else:
                feature.thickness.expression = "1.5 mm"
            if not design.timeline.moveToEnd() or not design.computeAll():
                raise RuntimeError("Mesh feature edit failed")
            result["stages"]["edited"] = observe(design, prefix + "Edited")
            if prepared["name"] == "PreparedMesh00" and design.rootComponent.meshBodies.item(0).faceGroups.count != 1:
                raise RuntimeError("Combining all face groups did not produce one group")
            checkpoint()
            saved = folder / ("vendor_" + prefix + "Edited.f3d")
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(saved))):
                raise RuntimeError("Mesh native save failed")
            document.close(False)
            document = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(saved)))
            if document is None:
                raise RuntimeError("Saved mesh document did not reopen")
            design = adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType"))
            if not design.computeAll():
                raise RuntimeError("Saved mesh document did not rebuild")
            result["stages"]["reopened"] = observe(design, prefix + "Reopened")
            same(result["stages"]["edited"], result["stages"]["reopened"], "saved state")
            result["saved_sha256"] = hashlib.sha256(saved.read_bytes()).hexdigest()
            result["status"] = "accepted"
            document.close(False)
            document = None
            checkpoint()
        same(case["variants"][0]["stages"], case["variants"][1]["stages"])
        case["status"] = "accepted"
    report["status"] = "accepted"
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
    raise
finally:
    if document is not None:
        document.close(False)
    if original is not None and original.isValid:
        original.activate()
    report["documents_after"] = app.documents.count
    checkpoint()
