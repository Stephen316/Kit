"""Study-owned split-face definitions with rolled-back input getter evidence."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("splitfacemodes-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    cases = ("plane", "plane_extended", "line", "line_extended", "along_vector", "closest_point", "multiple_faces")
    if isinstance(context, dict) and "cases" in context:
        cases = [case for case in cases if case in context["cases"]]
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString

    def entity_truth(entity):
        kind = entity.objectType.split("::")[-1]
        result = {"kind": kind}
        if kind in ("ConstructionPlane", "ConstructionAxis"):
            geometry = entity.geometry
            result.update(name=entity.name, origin_cm=geometry.origin.asArray())
            result["normal" if kind == "ConstructionPlane" else "direction"] = (
                geometry.normal if kind == "ConstructionPlane" else geometry.direction).asArray()
        elif kind == "SketchLine":
            geometry = entity.worldGeometry
            result.update(sketch_name=entity.parentSketch.name, start_cm=geometry.startPoint.asArray(), end_cm=geometry.endPoint.asArray())
        elif kind == "BRepFace":
            result.update(body_name=entity.body.name, geometry_type=entity.geometry.objectType.split("::")[-1],
                          area_cm2=entity.area, point_on_face_cm=entity.pointOnFace.asArray())
        else:
            raise RuntimeError("Unsupported captured split-face input: "+kind)
        return result

    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = None
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.name = "TargetProfile"
            sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0, 0, 0), point(3, 2, 0))
            seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value("10 mm"),
                                                         adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            seed.name = "TargetExtrusion"
            body = seed.bodies.item(0)
            body.name = "TargetBody"
            faces = adsk.core.ObjectCollection.create()
            faces.add(seed.endFaces.item(0))
            if case == "multiple_faces":
                faces.add(seed.startFaces.item(0))
            if case in ("plane", "plane_extended", "multiple_faces"):
                plane_input = root.constructionPlanes.createInput()
                plane_input.setByOffset(root.yZConstructionPlane, value("12 mm"))
                tool = root.constructionPlanes.add(plane_input)
                tool.name = "SplitToolPlane"
            else:
                support_plane = root.xYConstructionPlane
                if case in ("along_vector", "closest_point"):
                    plane_input = root.constructionPlanes.createInput()
                    plane_input.setByOffset(root.xYConstructionPlane, value("20 mm"))
                    support_plane = root.constructionPlanes.add(plane_input)
                    support_plane.name = "CurveSupportPlane"
                tool_sketch = root.sketches.add(support_plane)
                tool_sketch.name = "SplitToolSketch"
                tool = tool_sketch.sketchCurves.sketchLines.addByTwoPoints(point(1.2, -1, 0), point(1.2, 3, 0))
            extended = case.endswith("extended")
            inputs = root.features.splitFaceFeatures.createInput(faces, tool, extended)
            if case == "along_vector":
                if not inputs.setAlongVectorSplitType(root.zConstructionAxis):
                    raise RuntimeError("Along-vector input rejected")
            elif case == "closest_point":
                if not inputs.setClosestPointSplitType():
                    raise RuntimeError("Closest-point input rejected")
            before_faces = body.faces.count
            feature = root.features.splitFaceFeatures.add(inputs)
            if feature is None:
                raise RuntimeError("Split-face add returned null")
            feature.name = "ProbeSplitFace"
            after = {"body_count": root.bRepBodies.count, "face_count": body.faces.count,
                     "volume_cm3": body.volume}
            if not feature.timelineObject.rollTo(True):
                raise RuntimeError("Could not roll back to split-face input state")
            split_type = int(feature.splitType)
            sample = {"file": case+".f3d", "feature_type": feature.objectType, "split_type": split_type,
                      "is_splitting_tool_extended": feature.isSplittingToolExtended if split_type == 0 else None,
                      "faces_to_split": [entity_truth(face) for face in feature.facesToSplit],
                      "splitting_tools": [entity_truth(entity) for entity in feature.splittingTool],
                      "direction_entity": entity_truth(feature.directionEntity) if feature.directionEntity else None,
                      "before_face_count": before_faces, "result": after}
            design.timeline.moveToEnd()
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Split-face export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            if design:
                design.timeline.moveToEnd()
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Split-face modes finished; consult errors.\n")
