"""Study-owned fixed-plane Draft modes and explicit input geometry evidence."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("draftmodes-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    cases = ("single", "negative", "flipped", "tangent_chain", "symmetric", "two_angles", "planar_face", "multiple_faces")
    if isinstance(context, dict) and "cases" in context:
        cases = [case for case in cases if case in context["cases"]]

    def face_truth(face):
        return {"body_name": face.body.name, "geometry_type": face.geometry.objectType.split("::")[-1],
                "point_on_face_cm": face.pointOnFace.asArray(), "area_cm2": face.area}

    def plane_truth(entity):
        face = adsk.fusion.BRepFace.cast(entity)
        geometry = adsk.core.Plane.cast(entity.geometry)
        if geometry is None:
            raise RuntimeError("Draft pull geometry is not planar")
        return {"kind": "Face" if face is not None else "ConstructionPlane",
                "name": entity.name if face is None else None,
                "body_name": face.body.name if face is not None else None,
                "origin_cm": geometry.origin.asArray(), "normal": geometry.normal.asArray()}

    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0, 0, 0), point(3, 2, 0))
            seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value("20 mm"),
                                                         adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            seed.name = "SeedExtrusion"
            seed.bodies.item(0).name = "SeedBody"
            pull_plane = root.xYConstructionPlane
            if case in ("symmetric", "two_angles"):
                plane_input = root.constructionPlanes.createInput()
                plane_input.setByOffset(root.xYConstructionPlane, value("10 mm"))
                pull_plane = root.constructionPlanes.add(plane_input)
                pull_plane.name = "MiddlePlane"
            elif case == "planar_face":
                pull_plane = seed.startFaces.item(0)
            faces = [seed.sideFaces.item(i) for i in range(seed.sideFaces.count)] if case == "multiple_faces" else [seed.sideFaces.item(0)]
            input_faces = [face_truth(face) for face in faces]
            requested_plane = plane_truth(pull_plane)
            inputs = root.features.draftFeatures.createInput(faces, pull_plane, case == "tangent_chain")
            inputs.isDirectionFlipped = case == "flipped"
            if case == "two_angles":
                success = inputs.setTwoAngles(value("5 deg"), value("2 deg"))
            else:
                success = inputs.setSingleAngle(case == "symmetric", value("-4 deg" if case == "negative" else "5 deg"))
            if not success:
                raise RuntimeError("Draft angle definition rejected")
            feature = root.features.draftFeatures.add(inputs)
            if feature is None:
                raise RuntimeError("Draft add returned null")
            feature.name = "ProbeDraft"
            sample = {"file": case+".f3d", "requested": {"input_faces": input_faces, "plane": requested_plane},
                      "health_state": feature.healthState, "warning": feature.errorOrWarningMessage}
            feature.timelineObject.rollTo(True)
            definition = feature.draftDefinition
            if definition.objectType.endswith("::AngleExtentDefinition"):
                angles = {"mode": "SingleAngle", "is_symmetric": definition.isSymmetric,
                          "angle_one_radians": definition.angle.value, "angle_two_radians": None}
            elif definition.objectType.endswith("::TwoSidesAngleExtentDefinition"):
                angles = {"mode": "TwoAngles", "is_symmetric": False,
                          "angle_one_radians": definition.angleOne.value, "angle_two_radians": definition.angleTwo.value}
            else:
                raise RuntimeError("Unobserved Draft definition: "+definition.objectType)
            sample["settings"] = {"draft_type": feature.draftType, "is_direction_flipped": feature.isDirectionFlipped,
                                  "is_tangent_chain": feature.isTangentChain, "angles": angles,
                                  "input_faces": [face_truth(face) for face in feature.inputFaces],
                                  "plane": plane_truth(feature.plane)}
            design.timeline.moveToEnd()
            sample["parameters"] = [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Draft export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Draft generation finished; consult errors.\n")
