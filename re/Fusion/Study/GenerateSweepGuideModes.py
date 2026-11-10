"""Study-owned Sweep rails, guide surfaces, composite paths and closed paths."""

import json
import math
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ("rail_scale", "rail_stretch", "rail_no_scaling", "rail_full_extents",
         "composite_line_arc", "closed_circle", "guide_surface", "guide_surface_chain")


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("sweepguides-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    operation = adsk.fusion.FeatureOperations
    cases = [case for case in CASES if not isinstance(context, dict) or "cases" not in context or case in context["cases"]]

    def path_truth(path):
        if path is None:
            return None
        entities = []
        for index in range(path.count):
            item = path.item(index)
            source, curve = item.entity, item.curve
            evaluator = curve.evaluator
            ok, low, high = evaluator.getParameterExtents()
            ends = []
            if ok:
                for parameter in (low, high):
                    success, p = evaluator.getPointAtParameter(parameter)
                    ends.append(p.asArray() if success else None)
            entities.append({"source_kind": source.objectType.split("::")[-1] if source else None,
                             "source_sketch_name": source.parentSketch.name if adsk.fusion.SketchCurve.cast(source) else None,
                             "curve_kind": curve.objectType.split("::")[-1],
                             "is_opposed_to_entity": item.isOpposedToEntity,
                             "parameter_domain": [low, high] if ok else None, "curve_endpoints_cm": ends})
        return {"count": path.count, "is_closed": path.isClosed, "entities": entities}

    def face_truth(face):
        return {"body_name": face.body.name, "geometry_type": face.geometry.objectType.split("::")[-1],
                "point_on_face_cm": face.pointOnFace.asArray(), "area_cm2": face.area}

    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            section = root.sketches.add(root.yZConstructionPlane)
            section.name = "SweepSection"
            section.sketchCurves.sketchLines.addTwoPointRectangle(point(-.3, -.2, 0), point(.3, .2, 0))
            path_sketch = root.sketches.add(root.xYConstructionPlane)
            path_sketch.name = "SweepPath"
            if case == "composite_line_arc":
                curves = adsk.core.ObjectCollection.create()
                curves.add(path_sketch.sketchCurves.sketchLines.addByTwoPoints(point(0, 0, 0), point(3, 0, 0)))
                curves.add(path_sketch.sketchCurves.sketchArcs.addByCenterStartSweep(point(3, 4, 0), point(3, 0, 0), math.pi/2))
                path = adsk.fusion.Path.create(curves, adsk.fusion.ChainedCurveOptions.noChainedCurves)
            elif case == "closed_circle":
                circle = path_sketch.sketchCurves.sketchCircles.addByCenterRadius(point(0, 4, 0), 4.)
                path = adsk.fusion.Path.create(circle, adsk.fusion.ChainedCurveOptions.noChainedCurves)
            else:
                line = path_sketch.sketchCurves.sketchLines.addByTwoPoints(point(0, 0, 0), point(5, 0, 0))
                path = adsk.fusion.Path.create(line, adsk.fusion.ChainedCurveOptions.noChainedCurves)
            if path is None:
                raise RuntimeError("Sweep path creation failed")
            inputs = root.features.sweepFeatures.createInput(section.profiles.item(0), path, operation.NewBodyFeatureOperation)
            requested = {"path": path_truth(path)}
            if case.startswith("rail_"):
                rail_sketch = root.sketches.add(root.xYConstructionPlane)
                rail_sketch.name = "SweepRail"
                rail = rail_sketch.sketchCurves.sketchLines.addByTwoPoints(point(0, .3, 0), point(5, .6, 0))
                rail_path = adsk.fusion.Path.create(rail, adsk.fusion.ChainedCurveOptions.noChainedCurves)
                inputs.guideRail = rail_path
                inputs.profileScaling = {"rail_stretch": 1, "rail_no_scaling": 2}.get(case, 0)
                inputs.extent = 1 if case == "rail_full_extents" else 0
                requested.update(guide_rail=path_truth(rail_path), profile_scaling=inputs.profileScaling, extent=inputs.extent)
            elif case.startswith("guide_surface"):
                guide_sketch = root.sketches.add(root.xYConstructionPlane)
                guide_sketch.name = "GuideSurfaceProfile"
                guide_sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0, -2, 0), point(5, 2, 0))
                patch = root.features.patchFeatures.add(root.features.patchFeatures.createInput(guide_sketch.profiles.item(0), operation.NewBodyFeatureOperation))
                patch.bodies.item(0).name = "GuideSurfaceBody"
                inputs.guideSurfaces = [patch.bodies.item(0).faces.item(0)]
                inputs.isChainSelection = case == "guide_surface_chain"
                requested.update(guide_surfaces=[face_truth(patch.bodies.item(0).faces.item(0))],
                                 is_chain_selection=inputs.isChainSelection)
            feature = root.features.sweepFeatures.add(inputs)
            if feature is None:
                raise RuntimeError("Sweep add returned null")
            feature.name = "ProbeSweep"
            sample = {"file": case+".f3d", "requested": requested,
                      "health_state": feature.healthState, "warning": feature.errorOrWarningMessage,
                      "result_bodies": [{"name": b.name, "is_solid": b.isSolid} for b in feature.bodies]}
            feature.timelineObject.rollTo(True)
            # An inactive getter can throw even though add succeeded. Evidence
            # collection must retain that error without preventing local export.
            sample["getter_errors"] = []

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
                profile = feature.profile
                if not adsk.fusion.Profile.cast(profile):
                    raise RuntimeError("Sweep normalized profile outside observed sketch-profile input")
                return {"sketch_name": profile.parentSketch.name,
                        "loop_count": profile.profileLoops.count,
                        "loops": [{"is_outer": profile.profileLoops.item(i).isOuter,
                                   "curve_count": profile.profileLoops.item(i).profileCurves.count}
                                  for i in range(profile.profileLoops.count)]}

            has_rail, has_surface = case.startswith("rail_"), case.startswith("guide_surface")
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
                "guide_surfaces": getter("guideSurfaces", lambda: [face_truth(face) for face in (feature.guideSurfaces or [])]),
                "profile_scaling": getter("profileScaling", lambda: feature.profileScaling) if has_rail else None,
                "extent": getter("extent", lambda: feature.extent) if has_rail else None,
                "is_direction_flipped": getter("isDirectionFlipped", lambda: feature.isDirectionFlipped) if has_rail else None,
                "is_chain_selection": getter("isChainSelection", lambda: feature.isChainSelection) if has_surface else None,
                "profile": getter("profile", profile_truth)}
            sample["control_activity"] = {
                "orientation": "Guide modes do not expose the single-path orientation getter" if has_rail or has_surface else "Single-path orientation",
                "taper_and_twist": "Ignored by SDK when a rail or surface is specified" if has_rail or has_surface else "Single-path controls",
                "profile_scaling_and_extent": "Active with guide rail" if has_rail else "Inactive without guide rail",
                "direction_flip": "SDK applies only when a rail path extends both sides of the profile; these cases are one-sided",
                "surface_chain_selection": "Active with guide surfaces" if has_surface else "Inactive without guide surfaces"}
            design.timeline.moveToEnd()
            sample["parameters"] = [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Sweep guide/composite export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Sweep guide/composite generation finished; consult errors.\n")
