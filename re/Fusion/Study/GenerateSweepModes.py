"""Capture study-owned single-path sweep controls and selection ground truth."""

import json
import math
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ("line_perpendicular", "arc_perpendicular", "arc_parallel", "arc_partial",
         "line_taper", "line_twist", "line_surface", "line_cut")


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("sweeps-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    operation = adsk.fusion.FeatureOperations
    for case in CASES:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            if case == "line_cut":
                base = root.sketches.add(root.xYConstructionPlane)
                base.sketchCurves.sketchLines.addTwoPointRectangle(point(-1, -1, 0), point(6, 1, 0))
                seed_input = root.features.extrudeFeatures.createInput(base.profiles.item(0), operation.NewBodyFeatureOperation)
                seed_input.setSymmetricExtent(value("20 mm"), True)
                root.features.extrudeFeatures.add(seed_input)
            section = root.sketches.add(root.yZConstructionPlane)
            section.name = "SweepSection"
            section.sketchCurves.sketchLines.addTwoPointRectangle(point(-.3, -.2, 0), point(.3, .2, 0))
            path_sketch = root.sketches.add(root.xYConstructionPlane)
            path_sketch.name = "SweepPath"
            if case.startswith("arc"):
                curve = path_sketch.sketchCurves.sketchArcs.addByCenterStartSweep(point(0, 4, 0), point(0, 0, 0), math.pi/3)
            else:
                curve = path_sketch.sketchCurves.sketchLines.addByTwoPoints(point(0, 0, 0), point(5, 0, 0))
            path = root.features.createPath(curve)
            inputs = root.features.sweepFeatures.createInput(section.profiles.item(0), path,
                       operation.CutFeatureOperation if case == "line_cut" else operation.NewBodyFeatureOperation)
            inputs.orientation = (adsk.fusion.SweepOrientationTypes.ParallelOrientationType if case == "arc_parallel"
                                  else adsk.fusion.SweepOrientationTypes.PerpendicularOrientationType)
            if case == "arc_partial":
                inputs.distanceOne = value("0.65")
            if case == "line_taper":
                inputs.taperAngle = value("2 deg")
            if case == "line_twist":
                inputs.twistAngle = value("30 deg")
            inputs.isSolid = case != "line_surface"
            feature = root.features.sweepFeatures.add(inputs)
            feature.name = "ProbeSweep"
            settings = {"result_body_count": feature.bodies.count,
                        "result_is_solid": [body.isSolid for body in feature.bodies]}
            # Selection getters require the marker before this feature in the local SDK.
            feature.timelineObject.rollTo(True)
            source_path = feature.path
            profile = feature.profile
            settings.update(operation=feature.operation, orientation=feature.orientation, is_solid=feature.isSolid,
                            distance_one=feature.distanceOne.value if feature.distanceOne else None,
                            distance_two=feature.distanceTwo.value if feature.distanceTwo else None,
                            taper_angle_radians=feature.taperAngle.value if feature.taperAngle else None,
                            twist_angle_radians=feature.twistAngle.value if feature.twistAngle else None,
                            profile_type=profile.objectType if profile else None,
                            profile_sketch_name=profile.parentSketch.name if adsk.fusion.Profile.cast(profile) else None,
                            profile_loop_count=profile.profileLoops.count if adsk.fusion.Profile.cast(profile) else None,
                            path_entity_count=source_path.count,
                            path_entity_types=[source_path.item(i).entity.objectType for i in range(source_path.count)],
                            guide_rail_present=feature.guideRail is not None,
                            guide_surface_count=len(feature.guideSurfaces))
            design.timeline.moveToEnd()
            sample = {"file": case+".f3d", "settings": settings,
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Sweep export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Sweep generation finished; consult errors.\n")
