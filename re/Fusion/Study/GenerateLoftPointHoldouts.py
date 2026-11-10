"""Point-Loft holdouts using documented parametric point definitions."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ("tangent_start_weight1", "construction_sharp_end", "construction_sharp_start", "vertex_construction_sharp_end",
         "tangent_start_weight2")


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("loftpointholdouts-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": [],
             "token_scope": "Opaque API tokens retained as evidence; token equality does not establish decoded native identity"}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByReal
    for case in CASES:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        sample = {"case": case, "file": case+".f3d", "getter_errors": []}
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent

            def read(field, getter):
                try:
                    return getter()
                except Exception:
                    sample["getter_errors"].append({"field": field, "error": traceback.format_exc()})
                    return None

            def describe(entity, field, include_definition=True):
                item = {"entity_type": read(field+".entity_type", lambda: entity.objectType),
                        "entity_token": read(field+".entity_token", lambda: getattr(entity, "entityToken", None))}
                sketch_point = adsk.fusion.SketchPoint.cast(entity)
                construction = adsk.fusion.ConstructionPoint.cast(entity)
                vertex = adsk.fusion.BRepVertex.cast(entity)
                profile = adsk.fusion.Profile.cast(entity)
                plane = adsk.fusion.ConstructionPlane.cast(entity)
                if sketch_point:
                    item.update(sketch_name=read(field+".sketch_name", lambda: sketch_point.parentSketch.name),
                                sketch_token=read(field+".sketch_token", lambda: sketch_point.parentSketch.entityToken),
                                sketch_point_cm=read(field+".sketch_point_cm", lambda: sketch_point.geometry.asArray()),
                                world_point_cm=read(field+".world_point_cm", lambda: sketch_point.worldGeometry.asArray()))
                elif construction:
                    item.update(name=read(field+".name", lambda: construction.name),
                                world_point_cm=read(field+".world_point_cm", lambda: construction.geometry.asArray()),
                                is_parametric=read(field+".is_parametric", lambda: construction.isParametric),
                                component_name=read(field+".component_name", lambda: construction.component.name))
                    if include_definition:
                        definition = read(field+".definition", lambda: construction.definition)
                        if definition:
                            kind = read(field+".definition.type", lambda: definition.objectType)
                            entry = {"entity_type": kind, "sources": {}}
                            properties = {"adsk::fusion::ConstructionPointThreePlanesDefinition": ("planeOne", "planeTwo", "planeThree"),
                                          "adsk::fusion::ConstructionPointPointDefinition": ("pointEntity",)}.get(kind, ())
                            for role in properties:
                                source = read(field+".definition."+role, lambda role=role: getattr(definition, role))
                                entry["sources"][role] = describe(source, field+".definition."+role, False) if source else None
                            item["definition"] = entry
                elif vertex:
                    item.update(world_point_cm=read(field+".world_point_cm", lambda: vertex.geometry.asArray()),
                                body_name=read(field+".body_name", lambda: vertex.body.name),
                                body_token=read(field+".body_token", lambda: vertex.body.entityToken))
                elif profile:
                    sketch = profile.parentSketch
                    item.update(sketch_name=read(field+".sketch_name", lambda: sketch.name),
                                sketch_token=read(field+".sketch_token", lambda: sketch.entityToken),
                                profile_loop_count=read(field+".profile_loop_count", lambda: profile.profileLoops.count))
                    circles = []
                    for index in range(sketch.sketchCurves.sketchCircles.count):
                        circle = sketch.sketchCurves.sketchCircles.item(index)
                        circles.append({"entity_token": read(field+".circle.token", lambda: circle.entityToken),
                                        "center_world_cm": read(field+".circle.center", lambda: circle.worldGeometry.center.asArray()),
                                        "normal_world": read(field+".circle.normal", lambda: circle.worldGeometry.normal.asArray()),
                                        "radius_cm": read(field+".circle.radius", lambda: circle.radius)})
                    item["sketch_circles"] = circles
                elif plane:
                    item.update(name=read(field+".name", lambda: plane.name),
                                origin_world_cm=read(field+".origin", lambda: plane.geometry.origin.asArray()),
                                normal_world=read(field+".normal", lambda: plane.geometry.normal.asArray()))
                return item

            def offset_plane(height, name):
                inputs = root.constructionPlanes.createInput()
                if not inputs.setByOffset(root.xYConstructionPlane, value(height)):
                    raise RuntimeError("Section offset plane input rejected")
                plane = root.constructionPlanes.add(inputs)
                plane.name = name
                return plane

            is_start = case.startswith("tangent_start_") or case == "construction_sharp_start"
            profile_height = 3 if is_start else 0
            point_height = 0 if is_start else 3
            profile_plane = offset_plane(profile_height, "PointLoftProfilePlane") if profile_height else root.xYConstructionPlane
            profile_sketch = root.sketches.add(profile_plane)
            profile_sketch.name = "HoldoutLoftProfile"
            profile_sketch.sketchCurves.sketchCircles.addByCenterRadius(point(0, 0, 0), 1.0)
            profile = profile_sketch.profiles.item(0)
            if case.startswith("tangent_start_"):
                point_sketch = root.sketches.add(root.xYConstructionPlane)
                point_sketch.name = "HoldoutLoftPoint"
                selected_point = point_sketch.sketchPoints.add(point(0, 0, 0))
                sample["requested_point_source"] = "SketchPoint"
            else:
                point_input = root.constructionPoints.createInput()
                if case == "vertex_construction_sharp_end":
                    support = root.sketches.add(root.xYConstructionPlane)
                    support.name = "VertexSupportSketch"
                    support.sketchCurves.sketchLines.addTwoPointRectangle(point(0, 0, 0), point(1, 1, 0))
                    seed = root.features.extrudeFeatures.addSimple(support.profiles.item(0), value(3),
                                                                 adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                    seed.name = "PointSupportExtrude"
                    body = seed.bodies.item(0)
                    body.name = "PointSupportBody"
                    candidates = [body.vertices.item(i) for i in range(body.vertices.count)]
                    matching = [v for v in candidates if v.geometry.distanceTo(point(0, 0, 3)) < 1e-9]
                    if len(matching) != 1:
                        raise RuntimeError("Study support vertex is missing or ambiguous")
                    vertex = matching[0]
                    sample["requested_point_source"] = "ConstructionPointInput.setByPoint(BRepVertex)"
                    sample["vertex_before_construction"] = describe(vertex, "support_vertex")
                    accepted = point_input.setByPoint(vertex)
                else:
                    endpoint_plane = offset_plane(point_height, "PointEndpointPlane") if point_height else root.xYConstructionPlane
                    sample["requested_point_source"] = "ConstructionPointInput.setByThreePlanes"
                    accepted = point_input.setByThreePlanes(endpoint_plane, root.xZConstructionPlane, root.yZConstructionPlane)
                if not accepted:
                    raise RuntimeError("Parametric construction point input rejected")
                selected_point = root.constructionPoints.add(point_input)
                selected_point.name = "HoldoutLoftConstructionPoint"
            sources = [selected_point, profile] if is_start else [profile, selected_point]
            sample["source_entities_before_loft"] = [describe(entity, "source"+str(index)) for index, entity in enumerate(sources)]
            inputs = root.features.loftFeatures.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            inputs.isSolid, inputs.isClosed = True, False
            sections = [inputs.loftSections.add(entity) for entity in sources]
            point_index = 0 if is_start else 1
            tangent = case.startswith("tangent_start_")
            tangent_weight = 2.0 if case == "tangent_start_weight2" else 1.0
            sample["requested_condition"] = {"type": "PointTangent" if tangent else "PointSharp", "section_index": point_index,
                                             "weight": tangent_weight if tangent else None}
            accepted = (sections[point_index].setPointTangentEndCondition(value(tangent_weight)) if tangent
                        else sections[point_index].setPointSharpEndCondition())
            if not accepted:
                raise RuntimeError("Point Loft end-condition input rejected")
            feature = root.features.loftFeatures.add(inputs)
            feature.name = "ProbeLoftPointHoldout"
            settings = {"result_body_count": feature.bodies.count, "root_body_count": root.bRepBodies.count,
                        "result_is_solid": [body.isSolid for body in feature.bodies],
                        "health_state": read("health_state", lambda: feature.healthState),
                        "warning": read("warning", lambda: feature.errorOrWarningMessage)}
            feature.timelineObject.rollTo(True)
            for field, getter in (("operation", lambda: feature.operation), ("is_solid", lambda: feature.isSolid),
                                  ("is_closed", lambda: feature.isClosed), ("is_tangent_edges_merged", lambda: feature.isTangentEdgesMerged),
                                  ("section_count", lambda: feature.loftSections.count), ("guide_count", lambda: feature.centerLineOrRails.count),
                                  ("is_centerline", lambda: feature.centerLineOrRails.isCenterLine)):
                settings[field] = read("settings."+field, getter)
            settings["sections"] = []
            for index in range(feature.loftSections.count):
                section = feature.loftSections.item(index)
                entry = describe(section.entity, "section"+str(index))
                entry["index"] = section.index
                condition = read("section.condition", lambda: section.endCondition)
                entry["end_condition_type"] = read("section.condition_type", lambda: condition.objectType) if condition else None
                point_tangent = adsk.fusion.LoftPointTangentEndCondition.cast(condition) if condition else None
                if point_tangent:
                    entry["weight"] = read("section.weight", lambda: point_tangent.weight.value)
                settings["sections"].append(entry)
            design.timeline.moveToEnd()
            sample["settings"] = settings
            sample["parameters"] = [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Point Loft holdout export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc(), "partial_capture": sample})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Point Loft holdouts finished; consult errors.\n")
