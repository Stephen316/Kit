"""Generate additional modeling tools with numeric settings and API truth."""

import json
import math
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("moretools-" + uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, vector, value = adsk.core.Point3D.create, adsk.core.Vector3D.create, adsk.core.ValueInput.createByString
    operation = adsk.fusion.FeatureOperations
    cases = ("Sweep", "Loft", "CircularPattern", "CircularPatternSymmetric", "CombineJoin", "CombineCut",
             "CombineIntersect", "Draft", "SplitBody", "MoveTranslate", "MoveRotate", "Thicken")
    if isinstance(context, dict) and "cases" in context:
        cases = context["cases"]
    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            settings = {}

            def profile(name, plane, center=(0, 0, 0), radius=1.):
                sketch = root.sketches.add(plane)
                sketch.name = name
                sketch.sketchCurves.sketchCircles.addByCenterRadius(point(*center), radius)
                return sketch

            if case.startswith("Sweep"):
                sketch = profile("SweepSection", root.yZConstructionPlane, radius=0.6)
                path_sketch = root.sketches.add(root.xYConstructionPlane)
                path_sketch.name = "SweepPath"
                line = path_sketch.sketchCurves.sketchLines.addByTwoPoints(point(0, 0, 0), point(5, 0, 0))
                inputs = root.features.sweepFeatures.createInput(sketch.profiles.item(0), root.features.createPath(line), operation.NewBodyFeatureOperation)
                inputs.taperAngle, inputs.twistAngle = value("3 deg"), value("15 deg")
                if case == "SweepPartial":
                    inputs.distanceOne = value("0.6")
                feature = root.features.sweepFeatures.add(inputs)
            elif case.startswith("Loft"):
                first = profile("LoftSectionOne", root.xYConstructionPlane, radius=1.)
                plane_input = root.constructionPlanes.createInput()
                plane_input.setByOffset(root.xYConstructionPlane, value("30 mm"))
                plane = root.constructionPlanes.add(plane_input)
                plane.name = "LoftEndPlane"
                second = profile("LoftSectionTwo", plane, center=(0.5, 0, 0), radius=0.6)
                inputs = root.features.loftFeatures.createInput(operation.NewBodyFeatureOperation)
                inputs.loftSections.add(first.profiles.item(0))
                inputs.loftSections.add(second.profiles.item(0))
                if case == "LoftThreeSections":
                    extra_input = root.constructionPlanes.createInput()
                    extra_input.setByOffset(root.xYConstructionPlane, value("60 mm"))
                    third = profile("LoftSectionThree", root.constructionPlanes.add(extra_input), center=(1, 0, 0), radius=0.4)
                    inputs.loftSections.add(third.profiles.item(0))
                feature = root.features.loftFeatures.add(inputs)
                settings["section_count"] = 3 if case == "LoftThreeSections" else 2
            else:
                sketch = profile("SeedProfile", root.xYConstructionPlane,
                                 center=(3, 0, 0) if case.startswith("Circular") else (0, 0, 0))
                inputs = root.features.extrudeFeatures.createInput(sketch.profiles.item(0), operation.NewBodyFeatureOperation)
                inputs.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(value("20 mm")), adsk.fusion.ExtentDirections.PositiveExtentDirection)
                inputs.isSolid = case != "Thicken"
                seed = root.features.extrudeFeatures.add(inputs)
                seed.name = "SeedExtrusion"
                body = root.bRepBodies.item(0)
                entities = adsk.core.ObjectCollection.create()
                entities.add(body)
                if case.startswith("Circular"):
                    inputs = root.features.circularPatternFeatures.createInput(entities, root.zConstructionAxis)
                    symmetric = case != "CircularPattern"
                    inputs.quantity = value("6" if case == "CircularPatternSymmetric" else "4")
                    inputs.totalAngle = value("180 deg" if case == "CircularPatternSymmetric" else "270 deg")
                    inputs.isSymmetric = symmetric
                    feature = root.features.circularPatternFeatures.add(inputs)
                    settings.update(quantity=feature.quantity.value, total_angle_radians=feature.totalAngle.value,
                                    is_symmetric=feature.isSymmetric, axis_name=feature.axis.name)
                elif case.startswith("Combine"):
                    other = profile("ToolProfile", root.xYConstructionPlane, center=(1.2, 0, 0))
                    tool = root.features.extrudeFeatures.addSimple(other.profiles.item(0), value("20 mm"), operation.NewBodyFeatureOperation)
                    tool.name = "ToolExtrusion"
                    collection = adsk.core.ObjectCollection.create()
                    collection.add(tool.bodies.item(0))
                    inputs = root.features.combineFeatures.createInput(body, collection)
                    inputs.operation = (operation.JoinFeatureOperation if case == "CombineJoin" else
                                        operation.CutFeatureOperation if case.startswith("CombineCut") else operation.IntersectFeatureOperation)
                    inputs.isKeepToolBodies = not case.endswith("NoKeep")
                    feature = root.features.combineFeatures.add(inputs)
                    settings.update(operation=feature.operation, keep_tool_bodies=feature.isKeepToolBodies)
                elif case == "Draft":
                    inputs = root.features.draftFeatures.createInput([seed.sideFaces.item(0)], root.xYConstructionPlane, False)
                    inputs.setSingleAngle(False, value("5 deg"))
                    feature = root.features.draftFeatures.add(inputs)
                elif case == "SplitBody":
                    inputs = root.features.splitBodyFeatures.createInput(body, root.yZConstructionPlane, True)
                    feature = root.features.splitBodyFeatures.add(inputs)
                    settings["splitting_plane"] = "YZ"
                elif case.startswith("Move"):
                    transform = adsk.core.Matrix3D.create()
                    if case == "MoveRotate":
                        transform.setToRotation(math.radians(35), vector(0, 0, 1), point(0, 0, 0))
                    transform.translation = vector(1.7, -0.8, 2.3)
                    inputs = root.features.moveFeatures.createInput2(entities)
                    inputs.defineAsFreeMove(transform)
                    feature = root.features.moveFeatures.add(inputs)
                    settings["transform"] = transform.asArray()
                else:
                    faces = adsk.core.ObjectCollection.create()
                    for face in seed.sideFaces:
                        faces.add(face)
                    inputs = root.features.thickenFeatures.createInput(faces, value("1.5 mm"), False, operation.NewBodyFeatureOperation)
                    feature = root.features.thickenFeatures.add(inputs)
            feature.name = "Probe" + case
            design.computeAll()
            sample = {"file": case+".f3d", "name": feature.name, "kind": feature.objectType.split("::")[-1],
                      "settings": settings, "body_count": root.bRepBodies.count,
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value,
                                      "unit": p.unit, "created_by": getattr(p.createdBy, "name", None)}
                                     for p in root.modelParameters]}
            options = design.exportManager.createFusionArchiveExportOptions(str(output / sample["file"]))
            if not design.exportManager.execute(options):
                raise RuntimeError("Additional tool export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output / "ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output / "complete.txt").write_text("Additional tool export finished; consult errors.\n")
