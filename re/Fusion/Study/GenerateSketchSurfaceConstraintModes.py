"""Journaled surface-constraint family probes using documented role getters.

All documents are newly created and locally exported, then closed(False). This
batch starts with XY entities satisfying relations to a perpendicular YZ plane
or planar patch face; actual entity dimensionality remains explicit API truth.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ("coincident_to_plane", "line_on_face", "line_parallel_to_plane", "perpendicular_to_plane")
METHODS = {
    "coincident_to_plane": ("addCoincidentToSurface", "point", "surface"),
    "line_on_face": ("addLineOnPlanarSurface", "line", "planarSurface"),
    "line_parallel_to_plane": ("addLineParallelToPlanarSurface", "line", "planarSurface"),
    "perpendicular_to_plane": ("addPerpendicularToSurface", "curve", "surface"),
}


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("sketchsurfaceconstraints-" + uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": [],
             "prepared_scope": "Surface constraint classes and explicit planar role selections; no generic3D spline or curved-surface support claimed",
             "identity_scope": "API tokens and face tempId retained as API evidence; native file IDs/classes require exported records, never coordinate matching",
             "sdk_methods": METHODS}
    selected = context.get("cases", CASES) if isinstance(context, dict) else CASES
    cases = [case for case in CASES if case in selected]
    point = adsk.core.Point3D.create

    def journal(phase, case=None, **fields):
        event = {"time_utc": datetime.now(timezone.utc).isoformat(), "phase": phase, "case": case,
                 "completed_samples": len(truth["samples"]), "error_count": len(truth["errors"]), **fields}
        with (output / "journal.jsonl").open("a") as stream:
            stream.write(json.dumps(event) + "\n")
        (output / "progress.json").write_text(json.dumps(event, indent=2))
        (output / "ground_truth.json").write_text(json.dumps(truth, indent=2))

    def observe(label, read, errors):
        try:
            return read()
        except Exception:
            errors.append({"getter": label, "error": traceback.format_exc()})
            return None

    def identity(entity):
        if entity is None:
            return None
        errors = []
        result = {"type": observe("objectType", lambda: entity.objectType, errors),
                  "entity_token": observe("entityToken", lambda: entity.entityToken, errors), "getter_errors": errors}
        if hasattr(entity, "name"):
            result["name"] = observe("name", lambda: entity.name, errors)
        return result

    def vertex_truth(vertex):
        errors = []
        return {"identity": identity(vertex), "getter_errors": errors,
                "sketch_cm": observe("geometry", lambda: vertex.geometry.asArray(), errors),
                "world_cm": observe("worldGeometry", lambda: vertex.worldGeometry.asArray(), errors)}

    def entity_truth(entity):
        if entity is None:
            return None
        errors = []
        result = {"identity": identity(entity), "getter_errors": errors}
        vertex, line = adsk.fusion.SketchPoint.cast(entity), adsk.fusion.SketchLine.cast(entity)
        if vertex or line:
            for key, field in (("is_reference", "isReference"), ("is_fixed", "isFixed"), ("is_2d", "is2D")):
                result[key] = observe(field, lambda field=field: getattr(entity, field), errors)
            result["parent_sketch"] = observe("parentSketch", lambda: identity(entity.parentSketch), errors)
            attached = observe("geometricConstraints", lambda: entity.geometricConstraints, errors)
            result["attached_constraints"] = observe("geometricConstraints.items",
                lambda: [identity(attached.item(i)) for i in range(attached.count)], errors) if attached is not None else None
        if vertex:
            result["point"] = vertex_truth(vertex)
        if line:
            result["start_point"] = observe("startSketchPoint", lambda: vertex_truth(line.startSketchPoint), errors)
            result["end_point"] = observe("endSketchPoint", lambda: vertex_truth(line.endSketchPoint), errors)
            result["is_construction"] = observe("isConstruction", lambda: line.isConstruction, errors)
        plane, face = adsk.fusion.ConstructionPlane.cast(entity), adsk.fusion.BRepFace.cast(entity)
        if plane or face:
            geometry = observe("geometry", lambda: entity.geometry, errors)
            result["surface_type"] = observe("geometry.objectType", lambda: geometry.objectType, errors) if geometry else None
            if geometry and adsk.core.Plane.cast(geometry):
                result["plane_origin_cm"] = observe("geometry.origin", lambda: geometry.origin.asArray(), errors)
                result["plane_normal"] = observe("geometry.normal", lambda: geometry.normal.asArray(), errors)
            if face:
                result["body"] = observe("body", lambda: identity(face.body), errors)
                result["temp_id"] = observe("tempId", lambda: face.tempId, errors)
                result["point_on_face_cm"] = observe("pointOnFace", lambda: face.pointOnFace.asArray(), errors)
                result["area_cm2"] = observe("area", lambda: face.area, errors)
        return result

    journal("batch_begin", selected_cases=cases)
    for case in cases:
        doc, design = None, None
        journal("case_begin", case)
        try:
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            journal("document_created", case)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            surface = root.yZConstructionPlane
            face_support = None
            if case == "line_on_face":
                support = root.sketches.add(root.yZConstructionPlane)
                support.name = "ConstraintFaceSupport"
                support.sketchCurves.sketchLines.addTwoPointRectangle(point(-2, -2, 0), point(3, 3, 0))
                patch = root.features.patchFeatures.add(root.features.patchFeatures.createInput(
                    support.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation))
                patch.name = "ConstraintTargetPatch"
                body = patch.bodies.item(0)
                body.name = "ConstraintTargetSheet"
                if body.faces.count != 1:
                    raise RuntimeError("Owned planar target patch does not have exactly one face")
                surface = body.faces.item(0)
                face_support = {"sketch": identity(support), "feature": identity(patch), "body": identity(body)}
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.name = "SurfaceConstraintProbe"
            if case == "coincident_to_plane":
                member = sketch.sketchPoints.add(point(0, 1., 0))
            else:
                first, last = ({"line_on_face": ((0, .7, 0), (0, 2.2, 0)),
                                "line_parallel_to_plane": ((.5, .7, 0), (.5, 2.2, 0)),
                                "perpendicular_to_plane": ((.5, 1., 0), (2.5, 1., 0))})[case]
                member = sketch.sketchCurves.sketchLines.addByTwoPoints(point(*first), point(*last))
            requested = {"method": METHODS[case][0], "member_before": entity_truth(member),
                         "surface_before": entity_truth(surface), "face_support": face_support,
                         "sketch": identity(sketch), "source_sketch_plane": entity_truth(root.xYConstructionPlane)}
            journal("constraint_add_begin", case, method=requested["method"])
            constraint = getattr(sketch.geometricConstraints, requested["method"])(member, surface)
            if constraint is None:
                raise RuntimeError("Surface constraint method returned None")
            journal("constraint_created", case)
            design.timeline.moveToEnd()
            errors = []
            settings = {"identity": identity(constraint), "getter_errors": errors,
                        "parent_sketch": observe("parentSketch", lambda: identity(constraint.parentSketch), errors)}
            for key, field in (("entity_role", METHODS[case][1]), ("surface_role", METHODS[case][2])):
                settings[key] = observe(field, lambda field=field: entity_truth(getattr(constraint, field)), errors)
            settings["member_after"] = entity_truth(member)
            settings["surface_after"] = entity_truth(surface)
            settings["constraints"] = observe("sketch.geometricConstraints", lambda: [
                identity(sketch.geometricConstraints.item(i)) for i in range(sketch.geometricConstraints.count)], errors)
            settings["sketch_to_component_matrix"] = observe("sketch.transform", lambda: sketch.transform.asArray(), errors)
            file = case + ".f3d"
            journal("export_begin", case, file=file)
            design.timeline.moveToEnd()
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output / file))):
                raise RuntimeError("Sketch surface constraint local export failed")
            truth["samples"].append({"file": file, "requested": requested, "settings": settings})
            journal("export_complete", case, file=file, size_bytes=(output / file).stat().st_size)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
            journal("case_error", case)
        finally:
            if design is not None:
                try:
                    design.timeline.moveToEnd()
                except Exception:
                    truth["errors"].append({"case": case, "cleanup": "timeline restore", "error": traceback.format_exc()})
            if doc is not None:
                try:
                    doc.close(False)
                    journal("owned_document_closed_without_save", case)
                except Exception:
                    truth["errors"].append({"case": case, "cleanup": "owned close(False)", "error": traceback.format_exc()})
            journal("case_finished", case)
    journal("batch_complete", selected_cases=cases)
    (output / "complete.txt").write_text("Sketch surface constraint probes finished; consult errors.\n")
