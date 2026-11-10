"""Controlled extension, untrim, ruled-surface and planar trim examples."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CASES = ("extend_natural", "extend_tangent", "extend_perpendicular", "extend_perpendicular_negative",
         "extend_aligned", "extend_two_edges", "untrim_internal", "untrim_external", "untrim_all", "untrim_manual",
         "ruled_tangent", "ruled_normal", "ruled_direction", "ruled_mitered", "trim_positive", "trim_negative")


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("surfacebounds-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    for case in CASES:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        pending_trim = None
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sketch = root.sketches.add(root.xYConstructionPlane)
            if case.startswith("untrim"):
                sketch.sketchCurves.sketchCircles.addByCenterRadius(point(0, 0, 0), 2.)
                sketch.sketchCurves.sketchCircles.addByCenterRadius(point(0, 0, 0), .5)
                profile = next(p for p in sketch.profiles if p.profileLoops.count == 2)
            else:
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(-2, -1, 0), point(2, 1, 0))
                profile = sketch.profiles.item(0)
            if case == "ruled_alternate":
                seed = root.features.extrudeFeatures.addSimple(profile, value("10 mm"), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            else:
                seed = root.features.patchFeatures.add(root.features.patchFeatures.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation))
            body = seed.bodies.item(0)
            settings = {}
            if case.startswith("extend"):
                edges = adsk.core.ObjectCollection.create()
                edges.add(body.edges.item(0))
                if case == "extend_two_edges":
                    edges.add(body.edges.item(1))
                kind = (2 if "perpendicular" in case else 1 if case == "extend_tangent" else 0)
                inputs = root.features.extendFeatures.createInput(edges, value("-3 mm" if case.endswith("negative") else "4 mm"), kind,
                                                                  case == "extend_aligned")
                inputs.extendAlignment = 1 if case == "extend_aligned" else 0
                settings["input_edge_count"] = edges.count
                feature = root.features.extendFeatures.add(inputs)
                if case == "extend_no_chain":
                    feature.timelineObject.rollTo(True)
                    edit_edges = adsk.core.ObjectCollection.create()
                    edit_edges.add(seed.bodies.item(0).edges.item(0))
                    feature.setInputEntities(edit_edges, False)
                    design.timeline.moveToEnd()
                settings.update(distance_cm=feature.distance.value, extend_type=feature.extendType,
                                is_chaining_enabled=feature.isChainingEnabled, alignment=feature.extendAlignment)
            elif case.startswith("untrim"):
                face = body.faces.item(0)
                if case == "untrim_manual":
                    loops = [loop for loop in face.loops if not loop.isOuter]
                    inputs = root.features.untrimFeatures.createInputFromLoops(loops)
                else:
                    kind = {"untrim_all": 0, "untrim_external": 1, "untrim_internal": 2}[case]
                    inputs = root.features.untrimFeatures.createInputFromFaces([face], kind, value("3 mm") if kind != 2 else None)
                feature = root.features.untrimFeatures.add(inputs)
                settings.update(loop_type=feature.untrimLoopType,
                                extension_distance_cm=feature.extensionDistance.value if feature.extensionDistance else None)
            elif case.startswith("ruled"):
                edge = seed.endFaces.item(0).edges.item(0) if case == "ruled_alternate" else body.edges.item(0)
                profile = root.createBRepEdgeProfile(edge, False)
                kind = {"ruled_tangent": 0, "ruled_mitered": 0, "ruled_normal": 1, "ruled_direction": 2, "ruled_alternate": 0}[case]
                direction = root.zConstructionAxis if kind == 2 else None
                inputs = root.features.ruledSurfaceFeatures.createInput(profile, value("5 mm"), value("15 deg"), kind, direction)
                inputs.operation = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
                inputs.cornerType = 1 if case == "ruled_mitered" else 0
                inputs.alternateFace = case == "ruled_alternate"
                feature = root.features.ruledSurfaceFeatures.add(inputs)
                if case == "ruled_alternate":
                    feature.timelineObject.rollTo(True)
                    feature.alternateFace = True
                    design.timeline.moveToEnd()
                settings.update(distance_cm=feature.distance.value, angle_radians=feature.angle.value,
                                ruled_type=feature.ruledSurfaceType, corner_type=feature.cornerType,
                                alternate_face=feature.alternateFace, operation_input="NewBody")
                if direction:
                    settings["direction_axis"] = direction.geometry.direction.asArray()
            else:
                pending_trim = root.features.trimFeatures.createInput(root.xZConstructionPlane)
                cells = pending_trim.bRepCells
                settings["cells"] = []
                for index in range(cells.count):
                    cell = cells.item(index)
                    bounds = cell.cellBody.boundingBox
                    center = [(a+b)/2 for a,b in zip(bounds.minPoint.asArray(), bounds.maxPoint.asArray())]
                    cell.isSelected = center[1] > 0 if case == "trim_positive" else center[1] < 0
                    settings["cells"].append({"index": index, "bounding_box_center_cm": center, "is_removed": cell.isSelected})
                if not any(c["is_removed"] for c in settings["cells"]):
                    raise RuntimeError("Trim did not produce a selectable half-sheet cell")
                feature = root.features.trimFeatures.add(pending_trim)
                pending_trim = None
                settings.update(tool_plane_origin_cm=root.xZConstructionPlane.geometry.origin.asArray(),
                                tool_plane_normal=root.xZConstructionPlane.geometry.normal.asArray())
            feature.name = "ProbeSurfaceBoundary"
            design.computeAll()
            settings["result_body_count"] = root.bRepBodies.count
            sample = {"file": case+".f3d", "kind": feature.objectType.split("::")[-1], "settings": settings,
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Surface boundary export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            try:
                if pending_trim:
                    pending_trim.cancel()
            finally:
                doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Surface boundary generation finished; consult errors.\n")
