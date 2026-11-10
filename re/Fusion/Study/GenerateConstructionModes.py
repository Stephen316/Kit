"""Study-owned axis/point definition modes with actual API support getters."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("constructionmodes-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    cases = ("axis_two_points", "axis_perpendicular_at_point", "axis_normal_to_face", "axis_circular_face",
             "axis_edge", "point_edge_plane", "point_two_edges", "point_center")
    if isinstance(context, dict) and "cases" in context:
        cases = [case for case in cases if case in context["cases"]]
    roles = {"ConstructionAxisTwoPointDefinition": ("pointEntityOne", "pointEntityTwo"),
             "ConstructionAxisPerpendicularAtPointDefinition": ("face", "point"),
             "ConstructionAxisNormalToFaceAtPointDefinition": ("face", "pointEntity"),
             "ConstructionAxisCircularFaceDefinition": ("circularFace",),
             "ConstructionAxisEdgeDefinition": ("edgeEntity",),
             "ConstructionPointEdgePlaneDefinition": ("edge", "plane"),
             "ConstructionPointTwoEdgesDefinition": ("edgeOne", "edgeTwo"),
             "ConstructionPointCenterDefinition": ("circularEntity",)}

    def entity_truth(entity):
        kind = entity.objectType.split("::")[-1]
        result = {"kind": kind}
        if kind == "Point3D":
            result["position_cm"] = entity.asArray()
        elif kind in ("ConstructionPlane", "ConstructionAxis"):
            result["name"] = entity.name
            geometry = entity.geometry
            result["origin_cm"] = geometry.origin.asArray()
            result["normal" if kind == "ConstructionPlane" else "direction"] = (
                geometry.normal if kind == "ConstructionPlane" else geometry.direction).asArray()
        elif kind == "SketchPoint":
            result.update(world_position_cm=entity.worldGeometry.asArray(), sketch_name=entity.parentSketch.name)
        elif kind in ("SketchLine", "SketchCircle"):
            geometry = entity.worldGeometry
            result["sketch_name"] = entity.parentSketch.name
            if kind == "SketchLine":
                result.update(start_cm=geometry.startPoint.asArray(), end_cm=geometry.endPoint.asArray())
            else:
                result.update(center_cm=geometry.center.asArray(), radius_cm=geometry.radius)
        elif kind == "BRepFace":
            geometry = entity.geometry
            geometry_type = geometry.objectType.split("::")[-1]
            result.update(body_name=entity.body.name, geometry_type=geometry_type,
                          point_on_face_cm=entity.pointOnFace.asArray(), area_cm2=entity.area)
            if geometry_type == "Plane":
                result.update(origin_cm=geometry.origin.asArray(), normal=geometry.normal.asArray())
            elif geometry_type == "Cylinder":
                result.update(origin_cm=geometry.origin.asArray(), axis=geometry.axis.asArray(), radius_cm=geometry.radius)
        else:
            raise RuntimeError("Unobserved construction support entity: "+kind)
        return result

    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.name = "SupportSketch"
            is_axis = case.startswith("axis_")
            inputs = root.constructionAxes.createInput() if is_axis else root.constructionPoints.createInput()
            if case == "axis_two_points":
                first = sketch.sketchPoints.add(point(1, 2, 0))
                second = sketch.sketchPoints.add(point(4, 6, 0))
                method = "setByTwoPoints"
                success = inputs.setByTwoPoints(first, second)
            elif case in ("axis_perpendicular_at_point", "axis_normal_to_face", "axis_circular_face"):
                circular = case == "axis_circular_face"
                if circular:
                    sketch.sketchCurves.sketchCircles.addByCenterRadius(point(0, 0, 0), 1.)
                else:
                    sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0, 0, 0), point(3, 2, 0))
                seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value("20 mm"),
                                                             adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                seed.name = "SeedExtrusion"
                seed.bodies.item(0).name = "SupportBody"
                if circular:
                    method = "setByCircularFace"
                    success = inputs.setByCircularFace(seed.sideFaces.item(0))
                else:
                    face = seed.endFaces.item(0)
                    on_face = case == "axis_perpendicular_at_point"
                    support_sketch = root.sketches.add(face if on_face else root.xYConstructionPlane)
                    support_sketch.name = "AxisPoint"
                    support_point = support_sketch.sketchPoints.add(point(0, 0, 0) if on_face else point(.5, .7, 0))
                    if on_face:
                        method = "setByPerpendicularAtPoint"
                        success = inputs.setByPerpendicularAtPoint(face, support_point)
                    else:
                        method = "setByNormalToFaceAtPoint"
                        success = inputs.setByNormalToFaceAtPoint(face, support_point)
            elif case == "axis_edge":
                edge = sketch.sketchCurves.sketchLines.addByTwoPoints(point(0, 0, 0), point(3, 4, 0))
                method = "setByEdge"
                success = inputs.setByEdge(edge)
            elif case == "point_edge_plane":
                plane_input = root.constructionPlanes.createInput()
                plane_input.setByOffset(root.xYConstructionPlane, value("13 mm"))
                plane = root.constructionPlanes.add(plane_input)
                plane.name = "PointSupportPlane"
                method = "setByEdgePlane"
                success = inputs.setByEdgePlane(root.zConstructionAxis, plane)
            elif case == "point_two_edges":
                first = sketch.sketchCurves.sketchLines.addByTwoPoints(point(0, 2, 0), point(3, 2, 0))
                second = sketch.sketchCurves.sketchLines.addByTwoPoints(point(1, 0, 0), point(1, 4, 0))
                method = "setByTwoEdges"
                success = inputs.setByTwoEdges(first, second)
            else:
                circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(point(1.2, -.5, 0), .8)
                method = "setByCenter"
                success = inputs.setByCenter(circle)
            if not success:
                raise RuntimeError("Construction definition rejected")
            entity = root.constructionAxes.add(inputs) if is_axis else root.constructionPoints.add(inputs)
            if entity is None:
                raise RuntimeError("Construction add returned null")
            entity.name = "ProbeAxis" if is_axis else "ProbePoint"
            definition = entity.definition
            definition_type = definition.objectType.split("::")[-1]
            if definition_type not in roles:
                raise RuntimeError("Unobserved definition type: "+definition_type)
            geometry = entity.geometry
            sample = {"file": case+".f3d", "requested_method": method, "name": entity.name,
                      "definition_type": definition_type,
                      "support_inputs": [{"role": role, "entity": entity_truth(getattr(definition, role))}
                                         for role in roles[definition_type]],
                      "geometry": ({"origin_cm": geometry.origin.asArray(), "direction": geometry.direction.asArray()}
                                   if is_axis else {"position_cm": geometry.asArray()}),
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Construction modes export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Construction modes generation finished; consult errors.\n")
