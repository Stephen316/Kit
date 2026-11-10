"""Four Loft guide probes with actual Path member/order/opposition getter truth."""

import json
import math
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ("centerline_connected_chain", "centerline_explicit_members", "rail_line_arc", "spline_centerline")


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("loftcompositeguides-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": [],
             "scope": "Actual API guide entity/Path member order, source geometry, opposed flags and evaluator samples; no native traversal mapping assumed"}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByReal
    cases = context.get("cases", CASES) if isinstance(context, dict) else CASES
    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        sample = {"case": case, "file": case+".f3d", "getter_errors": []}
        try:
            if case not in CASES:
                raise ValueError("Unknown composite guide case")
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent

            def read(field, getter):
                try:
                    return getter()
                except Exception:
                    sample["getter_errors"].append({"field": field, "error": traceback.format_exc()})
                    return None

            def geometry_truth(geometry, field):
                item = {"geometry_type": read(field+".type", lambda: geometry.objectType)}
                evaluator = geometry.evaluator
                ok, low, high = evaluator.getParameterExtents()
                if not ok:
                    raise RuntimeError("Guide evaluator extents unavailable")
                item["parameter_extents"] = [low, high]
                ok, length = evaluator.getLengthAtParameter(low, high)
                item["length_cm"] = length if ok else None
                item["samples"] = []
                for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
                    parameter = low+fraction*(high-low)
                    success, position = evaluator.getPointAtParameter(parameter)
                    tangent_ok, tangent = evaluator.getTangent(parameter)
                    item["samples"].append({"parameter_fraction": fraction, "parameter": parameter,
                                            "point_cm": position.asArray() if success else None,
                                            "tangent": tangent.asArray() if tangent_ok else None})
                arc = adsk.core.Arc3D.cast(geometry)
                nurbs = adsk.core.NurbsCurve3D.cast(geometry)
                if arc:
                    item.update(center_cm=arc.center.asArray(), radius_cm=arc.radius, normal=arc.normal.asArray(),
                                reference_axis=arc.referenceVector.asArray(), start_angle_radians=arc.startAngle, end_angle_radians=arc.endAngle)
                elif nurbs:
                    ok, controls, degree, knots, rational, weights, periodic = nurbs.getData()
                    item["nurbs"] = {"get_data_success": ok, "control_points_cm": [p.asArray() for p in controls],
                                     "degree": degree, "knots": list(knots), "is_rational": rational,
                                     "weights": list(weights), "is_periodic": periodic}
                return item

            def curve_truth(entity, field):
                item = {"entity_type": read(field+".type", lambda: entity.objectType),
                        "entity_token": read(field+".token", lambda: getattr(entity, "entityToken", None))}
                curve = adsk.fusion.SketchCurve.cast(entity)
                if curve:
                    item.update(sketch_name=curve.parentSketch.name, sketch_token=read(field+".sketch_token", lambda: curve.parentSketch.entityToken),
                                natural_world_geometry=geometry_truth(curve.worldGeometry, field+".world_geometry"))
                return item

            def path_truth(path, field):
                result = {"entity_type": path.objectType, "count": path.count, "is_closed": path.isClosed, "members": []}
                for index in range(path.count):
                    member = path.item(index)
                    result["members"].append({"index": index,
                                               "is_opposed_to_entity": read(field+".opposed", lambda: member.isOpposedToEntity),
                                               "source": curve_truth(member.entity, field+".source"+str(index)),
                                               "actual_path_geometry": geometry_truth(member.curve, field+".curve"+str(index))})
                return result

            def offset_plane(height):
                inputs = root.constructionPlanes.createInput()
                if not inputs.setByOffset(root.xYConstructionPlane, value(height)):
                    raise RuntimeError("Profile offset plane rejected")
                return root.constructionPlanes.add(inputs)

            path_sketch = root.sketches.add(root.xZConstructionPlane)
            path_sketch.name = "CompositeLoftGuide"
            source_curves = []
            if case == "spline_centerline":
                fit_points = adsk.core.ObjectCollection.create()
                for position in ((4, 0, -2), (4, 0, -1), (3.8, 0, 1), (2.2, 0, 3), (0, 0, 4)):
                    fit_points.add(path_sketch.modelToSketchSpace(point(*position)))
                spline = path_sketch.sketchCurves.sketchFittedSplines.add(fit_points)
                source_curves.append(spline)
                path = adsk.fusion.Path.create(spline, adsk.fusion.ChainedCurveOptions.noChainedCurves)
                sample["requested_path_mode"] = "Single fitted spline, no chained curves"
            else:
                if case == "rail_line_arc":
                    line_start, line_end, arc_end = (1, 0, 0), (1, 0, 1), (0.6, 0, 3)
                    half_angle = math.atan2(2, 4.8)/2
                    arc_middle = (-4.2+5.2*math.cos(half_angle), 0, 1+5.2*math.sin(half_angle))
                else:
                    line_start, line_end, arc_end = (4, 0, -2), (4, 0, 0), (0, 0, 4)
                    arc_middle = (4/math.sqrt(2), 0, 4/math.sqrt(2))
                line = path_sketch.sketchCurves.sketchLines.addByTwoPoints(
                    path_sketch.modelToSketchSpace(point(*line_start)), path_sketch.modelToSketchSpace(point(*line_end)))
                arc = path_sketch.sketchCurves.sketchArcs.addByThreePoints(
                    line.endSketchPoint, path_sketch.modelToSketchSpace(point(*arc_middle)),
                    path_sketch.modelToSketchSpace(point(*arc_end)))
                source_curves.extend((line, arc))
                sample["requested_source_points_world_cm"] = {"line_start": line_start, "line_end": line_end,
                                                               "arc_middle": arc_middle, "arc_end": arc_end}
                if case == "centerline_connected_chain":
                    path = adsk.fusion.Path.create(line, adsk.fusion.ChainedCurveOptions.connectedChainedCurves)
                    sample["requested_path_mode"] = "Seed line with connectedChainedCurves"
                else:
                    explicit = adsk.core.ObjectCollection.create()
                    explicit.add(line)
                    explicit.add(arc)
                    path = adsk.fusion.Path.create(explicit, adsk.fusion.ChainedCurveOptions.noChainedCurves)
                    sample["requested_path_mode"] = "Explicit ObjectCollection line then arc; chain option ignored for collection per SDK"
            if path is None:
                raise RuntimeError("Composite/spline Path creation failed")
            sample["source_curves_before_loft"] = [curve_truth(curve, "created_curve"+str(index)) for index, curve in enumerate(source_curves)]
            sample["input_path_before_loft"] = path_truth(path, "input_path")
            specs = []
            if case == "spline_centerline":
                for fraction in (0.0, 1.0):
                    inputs = root.constructionPlanes.createInput()
                    if not inputs.setByPath(path, adsk.fusion.PathDistanceTypes.ProportionalPathDistanceType, value(fraction)):
                        raise RuntimeError("Spline endpoint-normal profile plane rejected")
                    plane = root.constructionPlanes.add(inputs)
                    specs.append((plane, plane.geometry.origin, 0.4))
            elif case == "rail_line_arc":
                specs = [(root.xYConstructionPlane, point(0, 0, 0), 1.0), (offset_plane(3), point(0, 0, 3), 0.6)]
            else:
                specs = [(offset_plane(-2), point(4, 0, -2), 0.4), (root.yZConstructionPlane, point(0, 0, 4), 0.4)]
            sections = []
            for index, (plane, center, radius) in enumerate(specs):
                sketch = root.sketches.add(plane)
                sketch.name = "CompositeLoftSection"+str(index+1)
                circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(sketch.modelToSketchSpace(center), radius)
                sections.append((sketch, circle))
            inputs = root.features.loftFeatures.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            inputs.isSolid, inputs.isClosed = True, False
            for sketch, _ in sections:
                inputs.loftSections.add(sketch.profiles.item(0))
            guide = inputs.centerLineOrRails.addRail(path) if case == "rail_line_arc" else inputs.centerLineOrRails.addCenterLine(path)
            if guide is None:
                raise RuntimeError("Composite/spline Loft guide input rejected")
            feature = root.features.loftFeatures.add(inputs)
            feature.name = "ProbeCompositeGuideLoft"
            settings = {"result_body_count": feature.bodies.count, "result_is_solid": [body.isSolid for body in feature.bodies],
                        "health_state": read("health_state", lambda: feature.healthState), "warning": read("warning", lambda: feature.errorOrWarningMessage)}
            feature.timelineObject.rollTo(True)
            for key, getter in (("operation", lambda: feature.operation), ("is_solid", lambda: feature.isSolid),
                                ("is_closed", lambda: feature.isClosed), ("is_tangent_edges_merged", lambda: feature.isTangentEdgesMerged),
                                ("section_count", lambda: feature.loftSections.count), ("guide_count", lambda: feature.centerLineOrRails.count),
                                ("is_centerline", lambda: feature.centerLineOrRails.isCenterLine)):
                settings[key] = read("settings."+key, getter)
            settings["guides"] = []
            for index in range(feature.centerLineOrRails.count):
                actual = feature.centerLineOrRails.item(index)
                entity = actual.entity
                actual_path = adsk.fusion.Path.cast(entity)
                entry = {"index": index, "entity_type": entity.objectType, "is_centerline": actual.isCenterLine}
                entry["path"] = path_truth(actual_path, "actual_guide") if actual_path else None
                if not actual_path:
                    entry["curve"] = curve_truth(entity, "actual_guide")
                settings["guides"].append(entry)
            settings["sections"] = []
            for index, (sketch, circle) in enumerate(sections):
                section = feature.loftSections.item(index)
                condition = read("section.condition", lambda: section.endCondition)
                settings["sections"].append({"index": section.index, "entity_type": section.entity.objectType,
                    "sketch_name": sketch.name, "circle_center_world_cm": circle.worldGeometry.center.asArray(),
                    "circle_normal_world": circle.worldGeometry.normal.asArray(), "circle_radius_cm": circle.radius,
                    "end_condition_type": read("section.condition_type", lambda: condition.objectType) if condition else None})
            design.timeline.moveToEnd()
            sample["settings"] = settings
            sample["parameters"] = [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Composite/spline Loft guide export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc(), "partial_capture": sample})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Composite Loft guide captures finished; consult errors.\n")
