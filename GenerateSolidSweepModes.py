"""Study-owned solid tool Sweep orientation and explicit twist-axis contrasts."""

import json
import math
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ("solid_perpendicular", "solid_rigid", "solid_aligned", "solid_twist",
         "solid_twist_zero", "solid_twist_sixty")


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("solidsweeps-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": [],
             "scope": "Owned Cut sweeps using a convex asymmetric solid box tool and explicit target",
             "token_scope": "Opaque API entity tokens retained without native object ID interpretation"}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    operations = adsk.fusion.FeatureOperations
    orientations = adsk.fusion.SweepSolidOrientationTypes
    cases = [case for case in CASES if not isinstance(context, dict) or "cases" not in context or case in context["cases"]]

    def body_truth(body):
        if body is None:
            return None
        bounds = body.boundingBox
        return {"kind": body.objectType.split("::")[-1], "name": body.name,
                "entity_token": body.entityToken, "component_name": body.parentComponent.name,
                "is_solid": body.isSolid, "volume_cm3": body.volume,
                "face_count": body.faces.count, "edge_count": body.edges.count,
                "bounding_box_min_cm": bounds.minPoint.asArray(),
                "bounding_box_max_cm": bounds.maxPoint.asArray()}

    def axis_truth(axis):
        if axis is None:
            return None
        geometry = axis.geometry
        return {"kind": axis.objectType.split("::")[-1], "name": getattr(axis, "name", None),
                "entity_token": getattr(axis, "entityToken", None),
                "geometry_kind": geometry.objectType.split("::")[-1],
                "origin_cm": geometry.origin.asArray(), "direction": geometry.direction.asArray()}

    def path_truth(path):
        if path is None:
            return None
        entities = []
        for index in range(path.count):
            item = path.item(index)
            source = item.entity
            curve = adsk.fusion.SketchCurve.cast(source)
            line, arc = adsk.fusion.SketchLine.cast(source), adsk.fusion.SketchArc.cast(source)
            evidence = {"kind": source.objectType.split("::")[-1] if source else None,
                        "entity_token": getattr(source, "entityToken", None),
                        "sketch_name": curve.parentSketch.name if curve else None,
                        "is_opposed_to_entity": item.isOpposedToEntity}
            if line or arc:
                evidence.update(start_world_cm=source.startSketchPoint.worldGeometry.asArray(),
                                end_world_cm=source.endSketchPoint.worldGeometry.asArray())
            if arc:
                geometry = arc.worldGeometry
                evidence.update(center_world_cm=arc.centerSketchPoint.worldGeometry.asArray(),
                                radius_cm=geometry.radius, normal=geometry.normal.asArray())
            entities.append(evidence)
        return {"count": path.count, "is_closed": path.isClosed, "entities": entities}

    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = None
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            target_section = root.sketches.add(root.xYConstructionPlane)
            target_section.name = "SolidSweepTargetSection"
            target_section.sketchCurves.sketchLines.addTwoPointRectangle(point(-2, -2, 0), point(7, 6, 0))
            target_input = root.features.extrudeFeatures.createInput(target_section.profiles.item(0), operations.NewBodyFeatureOperation)
            target_input.setSymmetricExtent(value("20 mm"), True)
            target_extrude = root.features.extrudeFeatures.add(target_input)
            target_extrude.name = "SolidSweepTargetExtrude"
            target = target_extrude.bodies.item(0)
            target.name = "SolidSweepTarget"
            target_before = body_truth(target)
            tool_section = root.sketches.add(root.yZConstructionPlane)
            tool_section.name = "SolidSweepToolSection"
            tool_section.sketchCurves.sketchLines.addTwoPointRectangle(point(-.35, -.15, 0), point(.15, .25, 0))
            tool_input = root.features.extrudeFeatures.createInput(tool_section.profiles.item(0), operations.NewBodyFeatureOperation)
            tool_input.setSymmetricExtent(value("4 mm"), True)
            tool_extrude = root.features.extrudeFeatures.add(tool_input)
            tool_extrude.name = "SolidSweepToolExtrude"
            tool = tool_extrude.bodies.item(0)
            tool.name = "AsymmetricSolidSweepTool"
            tool_before = body_truth(tool)
            path_sketch = root.sketches.add(root.xYConstructionPlane)
            path_sketch.name = "SolidSweepPath"
            if case.startswith("solid_twist"):
                curve = path_sketch.sketchCurves.sketchLines.addByTwoPoints(point(0, 0, 0), point(5, 0, 0))
            else:
                curve = path_sketch.sketchCurves.sketchArcs.addByCenterStartSweep(point(0, 4, 0), point(0, 0, 0), math.pi/3)
            path = adsk.fusion.Path.create(curve, adsk.fusion.ChainedCurveOptions.noChainedCurves)
            if path is None:
                raise RuntimeError("Solid Sweep source path creation failed")
            inputs = root.features.sweepFeatures.createInputForSolid(tool, path, operations.CutFeatureOperation)
            if inputs is None:
                raise RuntimeError("createInputForSolid returned null")
            inputs.participantBodies = [target]
            requested = {"operation": operations.CutFeatureOperation, "solid_body": tool_before,
                         "path": path_truth(path), "participant_bodies": [target_before],
                         "solid_orientation": {"solid_rigid": orientations.RigidSolidOrientationType,
                                               "solid_aligned": orientations.AlignedSolidOrientationType}.get(case, orientations.PerpendicularSolidOrientationType)}
            if case == "solid_aligned":
                inputs.solidAlignedAxis = root.zConstructionAxis
                requested["solid_aligned_axis"] = axis_truth(root.zConstructionAxis)
            inputs.solidOrientation = requested["solid_orientation"]
            if case.startswith("solid_twist"):
                degrees = {"solid_twist_zero": 0, "solid_twist_sixty": 60}.get(case, 30)
                inputs.solidTwistAxis = root.xConstructionAxis
                inputs.twistAngle = value(str(degrees)+" deg")
                requested.update(solid_twist_axis=axis_truth(root.xConstructionAxis),
                                 twist_angle_radians=math.radians(degrees))
                # Only inspect the active ValueInput representation; reading
                # realValue on a string ValueInput can itself raise an error.
                requested["input_getter_errors"] = []
                try:
                    actual = inputs.twistAngle
                    evidence = None
                    if actual is not None:
                        evidence = {"kind": actual.objectType.split("::")[-1], "value_type": actual.valueType}
                        if actual.valueType == adsk.core.ValueTypes.StringValueType:
                            evidence["string_value"] = actual.stringValue
                        elif actual.valueType == adsk.core.ValueTypes.RealValueType:
                            evidence["real_value"] = actual.realValue
                    requested["actual_input_twist_angle"] = evidence
                except Exception:
                    requested["actual_input_twist_angle"] = None
                    requested["input_getter_errors"].append({"getter": "input.twistAngle", "error": traceback.format_exc()})
            feature = root.features.sweepFeatures.add(inputs)
            if feature is None:
                raise RuntimeError("Solid Sweep add returned null")
            feature.name = "ProbeSolidSweep"
            sample = {"file": case+".f3d", "requested": requested, "getter_errors": [],
                      "tool_before_sweep": tool_before, "target_before_sweep": target_before}

            def getter(name, read):
                try:
                    return read()
                except Exception:
                    sample["getter_errors"].append({"getter": name, "error": traceback.format_exc()})
                    return None

            def parameter_value(name):
                parameter = getattr(feature, name)
                return parameter.value if parameter else None

            sample["health_state"] = getter("healthState", lambda: feature.healthState)
            sample["warning"] = getter("errorOrWarningMessage", lambda: feature.errorOrWarningMessage)
            sample["result_bodies"] = getter("bodies", lambda: [body_truth(body) for body in feature.bodies])
            sample["root_bodies_after_sweep"] = getter("root.bRepBodies", lambda: [body_truth(body) for body in root.bRepBodies])
            feature.timelineObject.rollTo(True)
            sample["settings"] = {
                "operation": getter("operation", lambda: feature.operation),
                "solid_body": getter("solidBody", lambda: body_truth(feature.solidBody)),
                "solid_orientation": getter("solidOrientation", lambda: feature.solidOrientation),
                "solid_aligned_axis": getter("solidAlignedAxis", lambda: axis_truth(feature.solidAlignedAxis)),
                "solid_twist_axis": getter("solidTwistAxis", lambda: axis_truth(feature.solidTwistAxis)),
                "path": getter("path", lambda: path_truth(feature.path)),
                "profile_type": getter("profile", lambda: feature.profile.objectType if feature.profile else None),
                "guide_rail_type": getter("guideRail", lambda: feature.guideRail.objectType if feature.guideRail else None),
                "guide_surface_count": getter("guideSurfaces", lambda: len(feature.guideSurfaces or [])),
                "is_solid": getter("isSolid", lambda: feature.isSolid),
                "orientation": getter("orientation", lambda: feature.orientation),
                "distance_one": getter("distanceOne", lambda: parameter_value("distanceOne")),
                "distance_two": getter("distanceTwo", lambda: parameter_value("distanceTwo")),
                "taper_angle_radians": getter("taperAngle", lambda: parameter_value("taperAngle")),
                "twist_angle_radians": getter("twistAngle", lambda: parameter_value("twistAngle")),
                "participant_bodies": getter("participantBodies", lambda: [body_truth(body) for body in (feature.participantBodies or [])])}
            design.timeline.moveToEnd()
            sample["parameters"] = [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Solid Sweep local export failed")
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
    (output/"complete.txt").write_text("Solid Sweep generation finished; consult errors.\n")
