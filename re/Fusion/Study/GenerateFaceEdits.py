"""Controlled offset-face, replace-face and healed delete-face examples."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("faceedits-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    for case in ("offset_positive", "offset_negative", "offset_two_faces", "offset_cylinder",
                 "replace_plane", "replace_plane_tangent", "delete_hole_face"):
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sketch = root.sketches.add(root.xYConstructionPlane)
            if case == "offset_cylinder":
                sketch.sketchCurves.sketchCircles.addByCenterRadius(point(2, 2, 0), 1.)
            else:
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0, 0, 0), point(4, 3, 0))
            seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value("20 mm"),
                                                         adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            seed.name = "FaceEditSeed"
            body = seed.bodies.item(0)
            settings = {}
            if case.startswith("offset"):
                faces = [seed.endFaces.item(0)]
                if case == "offset_cylinder":
                    faces = [f for f in body.faces if f.geometry.objectType.endswith("Cylinder")]
                elif case == "offset_two_faces":
                    faces.append(next(f for f in body.faces if abs(f.centroid.x-4.) < 1e-8))
                settings["input_face_count"] = len(faces)
                distance = "-2 mm" if case == "offset_negative" else "2.5 mm"
                feature = root.features.offsetFacesFeatures.add(root.features.offsetFacesFeatures.createInput(faces, value(distance)))
                settings["distance_cm"] = feature.distance.value
            elif case.startswith("replace"):
                plane_input = root.constructionPlanes.createInput()
                plane_input.setByOffset(root.xYConstructionPlane, value("30 mm"))
                plane = root.constructionPlanes.add(plane_input)
                plane.name = "ReplacementPlane"
                faces = adsk.core.ObjectCollection.create()
                faces.add(seed.endFaces.item(0))
                tangent = case == "replace_plane_tangent"
                settings.update(input_face_count=1, is_tangent_chain=tangent,
                                target_plane_origin_cm=plane.geometry.origin.asArray(),
                                target_plane_normal=plane.geometry.normal.asArray())
                feature = root.features.replaceFaceFeatures.add(root.features.replaceFaceFeatures.createInput(faces, tangent, plane))
            else:
                hole = root.sketches.add(root.xYConstructionPlane)
                hole.sketchCurves.sketchCircles.addByCenterRadius(point(2, 1.5, 0), .5)
                root.features.extrudeFeatures.addSimple(hole.profiles.item(0), value("20 mm"),
                                                       adsk.fusion.FeatureOperations.CutFeatureOperation)
                faces = adsk.core.ObjectCollection.create()
                for face in body.faces:
                    if face.geometry.objectType.endswith("Cylinder"):
                        faces.add(face)
                settings["input_face_count"] = faces.count
                feature = root.features.deleteFaceFeatures.add(faces)
            feature.name = "ProbeFaceEdit"
            design.computeAll()
            settings.update(result_body_count=root.bRepBodies.count,
                            result_face_count=root.bRepBodies.item(0).faces.count)
            sample = {"file": case+".f3d", "kind": feature.objectType.split("::")[-1], "settings": settings,
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Face edit export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Face edit generation finished; consult errors.\n")
