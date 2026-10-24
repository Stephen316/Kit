"""Study-owned Sweep Boolean operations, two-sided extents and active rail flip."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ("join", "intersect", "two_sided", "rail_flip_false", "rail_flip_true", "guided_cut")


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("sweepoperations-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": [],
             "sdk_rules": ["distanceTwo ignored for guide rails and one-sided paths",
                           "isDirectionFlipped applies to guide-rail paths extending both sides of profile",
                           "orientation/taper/twist inactive with guides"],
             "token_scope": "Opaque API entity tokens; no native object ID interpretation assigned"}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    operations = adsk.fusion.FeatureOperations
    cases = [case for case in CASES if not isinstance(context, dict) or "cases" not in context or case in context["cases"]]

    def body_truth(body):
        bounds = body.boundingBox
        return {"name": body.name, "entity_token": body.entityToken,
                "component_name": body.parentComponent.name, "is_solid": body.isSolid,
                "volume_cm3": body.volume,
                "bounding_box_min_cm": bounds.minPoint.asArray(),
                "bounding_box_max_cm": bounds.maxPoint.asArray()}

    def path_truth(path):
        if path is None:
            return None
        entities = []
        for index in range(path.count):
            item = path.item(index)
            source = item.entity
            curve = adsk.fusion.SketchCurve.cast(source)
            line = adsk.fusion.SketchLine.cast(source)
            entities.append({"source_kind": source.objectType.split("::")[-1] if source else None,
                             "source_sketch_name": curve.parentSketch.name if curve else None,
                             "is_opposed_to_entity": item.isOpposedToEntity,
                             "source_line_start_world_cm": line.startSketchPoint.worldGeometry.asArray() if line else None,
                             "source_line_end_world_cm": line.endSketchPoint.worldGeometry.asArray() if line else None})
        return {"count": path.count, "is_closed": path.isClosed, "entities": entities}

    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = None
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            is_rail = case.startswith("rail_flip_") or case == "guided_cut"
            two_sided = case == "two_sided" or case.startswith("rail_flip_")
            operation = {"join": operations.JoinFeatureOperation, "intersect": operations.IntersectFeatureOperation,
                         "guided_cut": operations.CutFeatureOperation}.get(case, operations.NewBodyFeatureOperation)
            target, seed_evidence = None, None
            if case in ("join", "intersect", "guided_cut"):
                seed_sketch = root.sketches.add(root.xYConstructionPlane)
                seed_sketch.name = "SweepTargetSection"
                seed_sketch.sketchCurves.sketchLines.addTwoPointRectangle(
                    point(-1, -1, 0), point(6 if case == "guided_cut" else 2, 1, 0))
                seed_input = root.features.extrudeFeatures.createInput(seed_sketch.profiles.item(0), operations.NewBodyFeatureOperation)
                seed_input.setSymmetricExtent(value("20 mm"), True)
                seed = root.features.extrudeFeatures.add(seed_input)
                seed.name = "StudySweepTargetExtrude"
                target = seed.bodies.item(0)
                target.name = "StudySweepTarget"
                seed_evidence = body_truth(target)
            section = root.sketches.add(root.yZConstructionPlane)
            section.name = "SweepSection"
            section.sketchCurves.sketchLines.addTwoPointRectangle(point(-.3, -.2, 0), point(.3, .2, 0))
            path_sketch = root.sketches.add(root.xYConstructionPlane)
            path_sketch.name = "SweepPath"
            line = path_sketch.sketchCurves.sketchLines.addByTwoPoints(point(-3 if two_sided else 0, 0, 0), point(5, 0, 0))
            path = adsk.fusion.Path.create(line, adsk.fusion.ChainedCurveOptions.noChainedCurves)
            inputs = root.features.sweepFeatures.createInput(section.profiles.item(0), path, operation)
            requested = {"operation": operation, "path": path_truth(path),
                         "profile_plane": "YZ at x=0; path extends from x=-3 to x=5" if two_sided else "YZ at x=0; path extends to x=5",
                         "two_sided_path": two_sided}
            if two_sided:
                inputs.distanceOne = value("0.6")
                requested["distance_one"] = .6
                if not is_rail:
                    inputs.distanceTwo = value("0.4")
                    requested["distance_two"] = .4
            if is_rail:
                rail_sketch = root.sketches.add(root.xYConstructionPlane)
                rail_sketch.name = "SweepRail"
                # Both lines meet the profile at x=0; rail y=.3 there.
                rail = rail_sketch.sketchCurves.sketchLines.addByTwoPoints(
                    point(-3 if two_sided else 0, .15 if two_sided else .3, 0), point(5, .55 if two_sided else .6, 0))
                rail_path = adsk.fusion.Path.create(rail, adsk.fusion.ChainedCurveOptions.noChainedCurves)
                inputs.guideRail = rail_path
                inputs.profileScaling = adsk.fusion.SweepProfileScalingOptions.SweepProfileScaleOption
                inputs.extent = adsk.fusion.SweepExtentTypes.PerpendicularToPathExtentType
                requested.update(guide_rail=path_truth(rail_path), profile_scaling=inputs.profileScaling, extent=inputs.extent)
                if two_sided:
                    requested["is_direction_flipped"] = case == "rail_flip_true"
                    inputs.isDirectionFlipped = requested["is_direction_flipped"]
            if case in ("intersect", "guided_cut"):
                inputs.participantBodies = [target]
                requested["participant_bodies"] = [seed_evidence]
            feature = root.features.sweepFeatures.add(inputs)
            if feature is None:
                raise RuntimeError("Sweep add returned null")
            feature.name = "ProbeSweepOperation"
            sample = {"file": case+".f3d", "requested": requested,
                      "seed_before_sweep": seed_evidence, "getter_errors": []}

            def getter(name, read):
                try:
                    return read()
                except Exception:
                    sample["getter_errors"].append({"getter": name, "error": traceback.format_exc()})
                    return None

            def parameter_value(name):
                parameter = getattr(feature, name)
                return parameter.value if parameter else None

            def profile_truth():
                profile = adsk.fusion.Profile.cast(feature.profile)
                if profile is None:
                    raise RuntimeError("Sweep profile is outside captured sketch-profile input")
                return {"sketch_name": profile.parentSketch.name,
                        "loop_count": profile.profileLoops.count,
                        "loops": [{"is_outer": profile.profileLoops.item(i).isOuter,
                                   "curve_count": profile.profileLoops.item(i).profileCurves.count}
                                  for i in range(profile.profileLoops.count)]}

            sample["result_bodies"] = getter("bodies", lambda: [body_truth(body) for body in feature.bodies])
            sample["health_state"] = getter("healthState", lambda: feature.healthState)
            sample["warning"] = getter("errorOrWarningMessage", lambda: feature.errorOrWarningMessage)
            feature.timelineObject.rollTo(True)
            sample["settings"] = {
                "operation": getter("operation", lambda: feature.operation),
                "orientation": getter("orientation", lambda: feature.orientation),
                "is_solid": getter("isSolid", lambda: feature.isSolid),
                "distance_one": getter("distanceOne", lambda: parameter_value("distanceOne")),
                "distance_two": getter("distanceTwo", lambda: parameter_value("distanceTwo")),
                "taper_angle_radians": getter("taperAngle", lambda: parameter_value("taperAngle")),
                "twist_angle_radians": getter("twistAngle", lambda: parameter_value("twistAngle")),
                "path": getter("path", lambda: path_truth(feature.path)),
                "guide_rail": getter("guideRail", lambda: path_truth(feature.guideRail)),
                "guide_surface_count": getter("guideSurfaces", lambda: len(feature.guideSurfaces or [])),
                "profile_scaling": getter("profileScaling", lambda: feature.profileScaling) if is_rail else None,
                "extent": getter("extent", lambda: feature.extent) if is_rail else None,
                "is_direction_flipped": getter("isDirectionFlipped", lambda: feature.isDirectionFlipped) if is_rail else None,
                "profile": getter("profile", profile_truth),
                "participant_bodies": getter("participantBodies", lambda: [body_truth(body) for body in (feature.participantBodies or [])]) if case in ("intersect", "guided_cut") else None}
            design.timeline.moveToEnd()
            sample["parameters"] = [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Sweep operation/side export failed")
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
    (output/"complete.txt").write_text("Sweep operation/side generation finished; consult errors.\n")
