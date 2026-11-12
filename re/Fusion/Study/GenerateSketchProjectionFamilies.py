"""Owned primitive intersections, spatial inclusion and planar surface projection."""

import json
import math
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ("intersect_line", "intersect_circle", "intersect_plane", "include_arc",
         "surface_closest_line", "surface_vector_line")


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("projectionfamilies-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": [],
             "sdk_methods": {"IntersectWithSketchPlane": "Sketch.intersectWithSketchPlane",
                             "Include3DGeometry": "Sketch.include (no include3DGeometry method in this SDK)",
                             "ProjectToSurface": "Sketch.projectToSurface"},
             "token_scope": "Opaque API tokens retained without native object ID interpretation"}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    cases = [case for case in CASES if not isinstance(context, dict) or "cases" not in context or case in context["cases"]]

    def identity(entity):
        if entity is None:
            return None
        parent = getattr(entity, "parentSketch", None)
        body = getattr(entity, "body", None)
        return {"kind": entity.objectType.split("::")[-1], "name": getattr(entity, "name", None),
                "entity_token": getattr(entity, "entityToken", None),
                "sketch_name": parent.name if parent else None, "body_name": body.name if body else None}

    def entity_truth(entity):
        result = {"getter_errors": []}

        def getter(name, read):
            try:
                return read()
            except Exception:
                result["getter_errors"].append({"getter": name, "error": traceback.format_exc()})
                return None

        result["identity"] = getter("identity", lambda: identity(entity))
        sketch_entity = adsk.fusion.SketchEntity.cast(entity)
        if sketch_entity:
            result["is_reference"] = getter("isReference", lambda: sketch_entity.isReference)
            result["is_2d"] = getter("is2D", lambda: sketch_entity.is2D)
            result["is_fixed"] = getter("isFixed", lambda: sketch_entity.isFixed)
            result["referenced_entity"] = getter("referencedEntity", lambda: identity(sketch_entity.referencedEntity)) if result["is_reference"] else None
        line, circle, arc, vertex = (adsk.fusion.SketchLine.cast(entity), adsk.fusion.SketchCircle.cast(entity),
                                     adsk.fusion.SketchArc.cast(entity), adsk.fusion.SketchPoint.cast(entity))
        curve = adsk.fusion.SketchCurve.cast(entity)
        if curve:
            result["is_construction"] = getter("isConstruction", lambda: curve.isConstruction)
            result["world_geometry_type"] = getter("worldGeometry", lambda: curve.worldGeometry.objectType.split("::")[-1])
        if line or arc:
            result["start_world_cm"] = getter("startSketchPoint.worldGeometry", lambda: entity.startSketchPoint.worldGeometry.asArray())
            result["end_world_cm"] = getter("endSketchPoint.worldGeometry", lambda: entity.endSketchPoint.worldGeometry.asArray())
        if circle or arc:
            result["center_world_cm"] = getter("centerSketchPoint.worldGeometry", lambda: entity.centerSketchPoint.worldGeometry.asArray())
            result["radius_cm"] = getter("worldGeometry.radius", lambda: entity.worldGeometry.radius)
            result["normal_world"] = getter("worldGeometry.normal", lambda: entity.worldGeometry.normal.asArray())
        if vertex:
            result["position_world_cm"] = getter("worldGeometry", lambda: vertex.worldGeometry.asArray())
        plane = adsk.fusion.ConstructionPlane.cast(entity)
        if plane:
            result["origin_world_cm"] = getter("geometry.origin", lambda: plane.geometry.origin.asArray())
            result["normal_world"] = getter("geometry.normal", lambda: plane.geometry.normal.asArray())
        face = adsk.fusion.BRepFace.cast(entity)
        if face:
            result["surface_geometry_type"] = getter("geometry", lambda: face.geometry.objectType.split("::")[-1])
            result["point_on_face_world_cm"] = getter("pointOnFace", lambda: face.pointOnFace.asArray())
            result["area_cm2"] = getter("area", lambda: face.area)
        return result

    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = None
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            face, direction = None, None
            if case == "intersect_plane":
                source = root.yZConstructionPlane
            else:
                source_sketch = root.sketches.add(root.xYConstructionPlane if case.startswith("surface_") else root.xZConstructionPlane)
                source_sketch.name = "ProjectionFamilySource"
                local = source_sketch.modelToSketchSpace
                if case == "intersect_circle":
                    source = source_sketch.sketchCurves.sketchCircles.addByCenterRadius(local(point(1, 0, 0)), 1.)
                elif case == "include_arc":
                    source = source_sketch.sketchCurves.sketchArcs.addByCenterStartSweep(local(point(1, 0, 1)), local(point(0, 0, 1)), math.pi/2)
                else:
                    first, last = ((point(.5, .7, 0), point(2, 1.3, 0)) if case.startswith("surface_") else (point(1, 0, -1), point(1, 0, 1)))
                    source = source_sketch.sketchCurves.sketchLines.addByTwoPoints(local(first), local(last))
            if case.startswith("surface_"):
                plane_input = root.constructionPlanes.createInput()
                plane_input.setByOffset(root.xYConstructionPlane, value("10 mm"))
                face_sketch = root.sketches.add(root.constructionPlanes.add(plane_input))
                face_sketch.name = "ProjectionSurfaceSection"
                face_sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(-2, -2, 0), point(3, 3, 0))
                patch = root.features.patchFeatures.add(root.features.patchFeatures.createInput(
                    face_sketch.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation))
                patch.name = "ProjectionFamilySurfacePatch"
                patch.bodies.item(0).name = "ProjectionFamilySurface"
                face = patch.bodies.item(0).faces.item(0)
                if case == "surface_vector_line":
                    direction_sketch = root.sketches.add(root.xZConstructionPlane)
                    direction_sketch.name = "ProjectionFamilyDirection"
                    direction = direction_sketch.sketchCurves.sketchLines.addByTwoPoints(
                        direction_sketch.modelToSketchSpace(point(0, 0, 0)), direction_sketch.modelToSketchSpace(point(0, 0, 2)))
            target = root.sketches.add(root.xYConstructionPlane)
            target.name = "ProjectionFamilyTarget"
            requested = {"source": entity_truth(source), "target_plane": entity_truth(root.xYConstructionPlane),
                         "target_sketch_name": target.name, "face": entity_truth(face) if face else None,
                         "direction": entity_truth(direction) if direction else None}
            if case.startswith("intersect_"):
                method = "intersectWithSketchPlane"
                projected = list(target.intersectWithSketchPlane([source]))
            elif case == "include_arc":
                method = "include"
                result = target.include(source)
                projected = [result.item(i) for i in range(result.count)]
            else:
                method = "projectToSurface"
                project_type = (adsk.fusion.SurfaceProjectTypes.AlongVectorSurfaceProjectType if direction else
                                adsk.fusion.SurfaceProjectTypes.ClosestPointSurfaceProjectType)
                requested["surface_project_type"] = project_type
                projected = list(target.projectToSurface([face], [source], project_type, direction))
            sample = {"file": case+".f3d", "requested": requested,
                      "settings": {"method": method, "output_count": len(projected),
                                   "outputs": [entity_truth(entity) for entity in projected]}}
            design.timeline.moveToEnd()
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Sketch projection-family local export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            if design is not None:
                try:
                    design.timeline.moveToEnd()
                except Exception:
                    truth["errors"].append({"case": case, "cleanup": "timeline restore", "error": traceback.format_exc()})
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Sketch projection-family generation finished; consult errors.\n")
