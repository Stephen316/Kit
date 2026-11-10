"""Capture study-owned loft closure contrasts and ordered straight sketch rails."""

import json
import math
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


# Earlier cases remain available through context["cases"] for focused retries.
LEGACY_CASES = ("solid_two", "solid_three", "surface_two", "start_direction", "end_direction",
                "both_direction", "unmerged", "centerline")
CASES = ("closure_open_four", "closure_closed_four", "closure_closed_surface",
         "one_rail", "two_rails", "surface_one_rail")


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("loftguides-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    cases = context.get("cases", CASES) if isinstance(context, dict) else CASES
    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sketches = []
            if case.startswith("closure_"):
                for index in range(4):
                    angle = index*math.pi/2
                    plane = root.xZConstructionPlane
                    if index:
                        plane_input = root.constructionPlanes.createInput()
                        if not plane_input.setByAngle(root.zConstructionAxis, adsk.core.ValueInput.createByReal(angle), root.xZConstructionPlane):
                            raise RuntimeError("Radial section plane rejected")
                        plane = root.constructionPlanes.add(plane_input)
                    sketch = root.sketches.add(plane)
                    sketch.name = "LoftSection"+str(index+1)
                    center = sketch.modelToSketchSpace(point(4*math.cos(angle), 4*math.sin(angle), 0))
                    sketch.sketchCurves.sketchCircles.addByCenterRadius(center, .5)
                    sketches.append(sketch)
            else:
                for index, (height, radius) in enumerate(((0., 1.), (1.5, .85), (3., .6)) if case == "solid_three" else ((0., 1.), (3., .6))):
                    plane = root.xYConstructionPlane
                    if height:
                        plane_input = root.constructionPlanes.createInput()
                        plane_input.setByOffset(plane, adsk.core.ValueInput.createByReal(height))
                        plane = root.constructionPlanes.add(plane_input)
                    sketch = root.sketches.add(plane)
                    sketch.name = "LoftSection"+str(index+1)
                    sketch.sketchCurves.sketchCircles.addByCenterRadius(point(0, 0, 0), radius)
                    sketches.append(sketch)
            inputs = root.features.loftFeatures.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            sections = [inputs.loftSections.add(sketch.profiles.item(0)) for sketch in sketches]
            inputs.isSolid = case not in ("surface_two", "closure_closed_surface", "surface_one_rail")
            inputs.isClosed = case in ("closure_closed_four", "closure_closed_surface")
            inputs.isTangentEdgesMerged = case != "unmerged"
            if case in ("start_direction", "both_direction"):
                if not sections[0].setDirectionEndCondition(value("10 deg"), value("1.5")):
                    raise RuntimeError("Start direction condition rejected")
            if case in ("end_direction", "both_direction"):
                if not sections[-1].setDirectionEndCondition(value("-5 deg"), value("1.2")):
                    raise RuntimeError("End direction condition rejected")
            if case in ("one_rail", "two_rails", "surface_one_rail"):
                for rail_index, side in enumerate((1., -1.) if case == "two_rails" else (1.,)):
                    rail_sketch = root.sketches.add(root.xZConstructionPlane)
                    rail_sketch.name = "LoftRail"+str(rail_index+1)
                    line = rail_sketch.sketchCurves.sketchLines.addByTwoPoints(
                        rail_sketch.modelToSketchSpace(point(side, 0, 0)),
                        rail_sketch.modelToSketchSpace(point(.6*side, 0, 3)))
                    if inputs.centerLineOrRails.addRail(line) is None:
                        raise RuntimeError("Straight rail rejected")
            if case == "centerline":
                path_sketch = root.sketches.add(root.xZConstructionPlane)
                path_sketch.name = "LoftCenterLine"
                line = path_sketch.sketchCurves.sketchLines.addByTwoPoints(
                    path_sketch.modelToSketchSpace(point(0, 0, -.2)),
                    path_sketch.modelToSketchSpace(point(0, 0, 3.2)))
                if inputs.centerLineOrRails.addCenterLine(line) is None:
                    raise RuntimeError("Centerline rejected")
            feature = root.features.loftFeatures.add(inputs)
            feature.name = "ProbeLoft"
            settings = {"result_body_count": feature.bodies.count,
                        "result_is_solid": [body.isSolid for body in feature.bodies]}
            feature.timelineObject.rollTo(True)
            settings.update(operation=feature.operation, is_solid=feature.isSolid, is_closed=feature.isClosed,
                            is_tangent_edges_merged=feature.isTangentEdgesMerged,
                            start_edge_alignment=feature.startLoftEdgeAlignment, end_edge_alignment=feature.endLoftEdgeAlignment,
                            section_count=feature.loftSections.count,
                            guide_count=feature.centerLineOrRails.count, is_centerline=feature.centerLineOrRails.isCenterLine)
            settings["guides"] = []
            for index in range(feature.centerLineOrRails.count):
                guide = feature.centerLineOrRails.item(index)
                entity = guide.entity
                line = adsk.fusion.SketchLine.cast(entity)
                item = {"index": index, "entity_type": entity.objectType,
                        "edge_condition": guide.edgeCondition if adsk.fusion.BRepEdge.cast(entity) else None}
                if line:
                    item.update(sketch_name=line.parentSketch.name,
                                start_world_cm=line.startSketchPoint.worldGeometry.asArray(),
                                end_world_cm=line.endSketchPoint.worldGeometry.asArray())
                settings["guides"].append(item)
            settings["sections"] = []
            for index in range(feature.loftSections.count):
                section = feature.loftSections.item(index)
                entity = section.entity
                condition = section.endCondition if index in (0, feature.loftSections.count-1) and not feature.isClosed else None
                profile = adsk.fusion.Profile.cast(entity)
                item = {"index": section.index, "entity_type": entity.objectType,
                        "sketch_name": profile.parentSketch.name if profile else None,
                        "profile_loop_count": profile.profileLoops.count if profile else None,
                        "end_condition_type": condition.objectType if condition else None}
                direction = adsk.fusion.LoftDirectionEndCondition.cast(condition)
                if direction:
                    item.update(angle_radians=direction.angle.value, weight=direction.weight.value)
                settings["sections"].append(item)
            design.timeline.moveToEnd()
            sample = {"file": case+".f3d", "settings": settings,
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Loft export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Loft generation finished; consult errors.\n")
