"""Two study-owned lofts with actual SketchArc guide and evaluator getter truth."""

import json
import math
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ("quarter_arc_centerline", "bowed_arc_rail")


def describe_arc(arc):
    geometry = arc.worldGeometry
    evaluator = geometry.evaluator
    ok, minimum, maximum = evaluator.getParameterExtents()
    if not ok:
        raise RuntimeError("Arc evaluator parameter extents unavailable")
    ok, length = evaluator.getLengthAtParameter(minimum, maximum)
    if not ok:
        raise RuntimeError("Arc evaluator length unavailable")
    samples = []
    for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
        parameter = minimum+fraction*(maximum-minimum)
        ok_point, point = evaluator.getPointAtParameter(parameter)
        ok_tangent, tangent = evaluator.getTangent(parameter)
        if not ok_point or not ok_tangent:
            raise RuntimeError("Arc evaluator point/tangent unavailable")
        samples.append({"parameter_fraction": fraction, "parameter": parameter,
                        "point_world_cm": point.asArray(), "tangent_world": tangent.asArray()})
    return {"entity_type": arc.objectType, "sketch_name": arc.parentSketch.name,
            "start_world_cm": arc.startSketchPoint.worldGeometry.asArray(),
            "end_world_cm": arc.endSketchPoint.worldGeometry.asArray(),
            "center_world_cm": geometry.center.asArray(), "radius_cm": geometry.radius,
            "normal_world": geometry.normal.asArray(), "reference_vector_world": geometry.referenceVector.asArray(),
            "start_angle_radians": geometry.startAngle, "end_angle_radians": geometry.endAngle,
            "geometry_start_world_cm": geometry.startPoint.asArray(), "geometry_end_world_cm": geometry.endPoint.asArray(),
            "sketch_geometry": {"center_cm": arc.geometry.center.asArray(), "normal": arc.geometry.normal.asArray(),
                                "reference_vector": arc.geometry.referenceVector.asArray(), "radius_cm": arc.geometry.radius,
                                "start_angle_radians": arc.geometry.startAngle, "end_angle_radians": arc.geometry.endAngle},
            "sketch_transform_matrix": arc.parentSketch.transform.asArray(),
            "evaluator": {"minimum_parameter": minimum, "maximum_parameter": maximum,
                          "length_cm": length, "samples": samples}}


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("loftcurvedguides-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": [],
             "scope": "Actual world SketchArc geometry, endpoint/evaluator getters and API-selected guide entities; creation order is not assumed to be native arc orientation"}
    point = adsk.core.Point3D.create
    for case in CASES:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sections = []
            if case == "quarter_arc_centerline":
                section_specs = ((root.xYConstructionPlane, (4, 0, 0), 0.5),
                                 (root.yZConstructionPlane, (0, 0, 4), 0.5))
                requested_points = ((4, 0, 0), (4/math.sqrt(2), 0, 4/math.sqrt(2)), (0, 0, 4))
            else:
                plane_input = root.constructionPlanes.createInput()
                if not plane_input.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(3)):
                    raise RuntimeError("Parallel end section plane rejected")
                end_plane = root.constructionPlanes.add(plane_input)
                section_specs = ((root.xYConstructionPlane, (0, 0, 0), 1.0), (end_plane, (0, 0, 3), 0.6))
                requested_points = ((1, 0, 0), (1.4, 0, 1.5), (0.6, 0, 3))
            for index, (plane, center, radius) in enumerate(section_specs):
                sketch = root.sketches.add(plane)
                sketch.name = "CurvedLoftSection"+str(index+1)
                circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(sketch.modelToSketchSpace(point(*center)), radius)
                sections.append((sketch, circle))
            path_sketch = root.sketches.add(root.xZConstructionPlane)
            path_sketch.name = "QuarterArcCenterline" if case == "quarter_arc_centerline" else "BowedArcRail"
            points = [path_sketch.modelToSketchSpace(point(*coordinates)) for coordinates in requested_points]
            arc = path_sketch.sketchCurves.sketchArcs.addByThreePoints(*points)
            if arc is None:
                raise RuntimeError("Three-point sketch arc creation failed")
            created_arc_truth = describe_arc(arc)
            inputs = root.features.loftFeatures.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            inputs.isSolid = True
            inputs.isClosed = False
            for sketch, _ in sections:
                inputs.loftSections.add(sketch.profiles.item(0))
            if case == "quarter_arc_centerline":
                guide = inputs.centerLineOrRails.addCenterLine(arc)
            else:
                guide = inputs.centerLineOrRails.addRail(arc)
            if guide is None:
                raise RuntimeError("SketchArc loft guide input rejected")
            feature = root.features.loftFeatures.add(inputs)
            feature.name = "ProbeCurvedGuideLoft"
            settings = {"result_body_count": feature.bodies.count,
                        "result_is_solid": [body.isSolid for body in feature.bodies],
                        "health_state": feature.healthState, "warning": feature.errorOrWarningMessage}
            feature.timelineObject.rollTo(True)
            settings.update(operation=feature.operation, is_solid=feature.isSolid, is_closed=feature.isClosed,
                            is_tangent_edges_merged=feature.isTangentEdgesMerged,
                            start_edge_alignment=feature.startLoftEdgeAlignment, end_edge_alignment=feature.endLoftEdgeAlignment,
                            section_count=feature.loftSections.count,
                            guide_count=feature.centerLineOrRails.count, is_centerline=feature.centerLineOrRails.isCenterLine)
            guide_truth = []
            for index in range(feature.centerLineOrRails.count):
                actual = feature.centerLineOrRails.item(index)
                entity = actual.entity
                item = {"index": index, "entity_type": entity.objectType, "is_centerline": actual.isCenterLine}
                selected_arc = adsk.fusion.SketchArc.cast(entity)
                if selected_arc:
                    item["arc"] = describe_arc(selected_arc)
                guide_truth.append(item)
            section_truth = []
            for index, (sketch, circle) in enumerate(sections):
                actual_section = feature.loftSections.item(index)
                entity = actual_section.entity
                geometry = circle.worldGeometry
                condition = actual_section.endCondition
                section_truth.append({"index": actual_section.index, "entity_type": entity.objectType,
                                      "sketch_name": sketch.name, "circle_center_world_cm": geometry.center.asArray(),
                                      "circle_normal_world": geometry.normal.asArray(), "circle_radius_cm": geometry.radius,
                                      "end_condition_type": condition.objectType if condition else None})
            design.timeline.moveToEnd()
            sample = {"file": case+".f3d", "requested_guide_three_points_world_cm": requested_points,
                      "created_arc": created_arc_truth, "settings": settings, "guides": guide_truth, "sections": section_truth,
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            options = design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))
            if not design.exportManager.execute(options):
                raise RuntimeError("Curved guide loft export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Curved guide loft captures finished; consult errors.\n")
