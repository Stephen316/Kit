"""Study-owned parametric construction planes and explicit API definition inputs."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("planedefinitions-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    cases = ("offset", "angle", "midplane", "three_points", "two_edges", "offset_through_point", "tangent", "tangent_at_point")
    if isinstance(context, dict) and "cases" in context:
        cases = [case for case in cases if case in context["cases"]]

    def entity_truth(entity):
        kind = entity.objectType.split("::")[-1]
        result = {"kind": kind}
        if kind in ("ConstructionPlane", "ConstructionAxis"):
            result["name"] = entity.name
            geometry = entity.geometry
            result["origin_cm"] = geometry.origin.asArray()
            result["normal" if kind == "ConstructionPlane" else "direction"] = (
                geometry.normal if kind == "ConstructionPlane" else geometry.direction).asArray()
        elif kind == "SketchPoint":
            result["world_position_cm"] = entity.worldGeometry.asArray()
            result["sketch_name"] = entity.parentSketch.name
        elif kind == "BRepFace":
            result.update(body_name=entity.body.name, geometry_type=entity.geometry.objectType.split("::")[-1],
                          point_on_face_cm=entity.pointOnFace.asArray(), area_cm2=entity.area)
        else:
            raise RuntimeError("Unexpected plane definition input: "+kind)
        return result

    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            inputs = root.constructionPlanes.createInput()
            role_names, scalar_names = [], []
            if case == "offset":
                success = inputs.setByOffset(root.xYConstructionPlane, value("12 mm"))
                role_names, scalar_names = ["planarEntity"], ["offset"]
            elif case == "angle":
                success = inputs.setByAngle(root.xConstructionAxis, value("35 deg"), root.xYConstructionPlane)
                role_names, scalar_names = ["linearEntity", "planarEntity"], ["angle"]
            elif case == "midplane":
                support_input = root.constructionPlanes.createInput()
                support_input.setByOffset(root.xYConstructionPlane, value("30 mm"))
                support = root.constructionPlanes.add(support_input)
                support.name = "SupportPlane"
                success = inputs.setByTwoPlanes(root.xYConstructionPlane, support)
                role_names = ["planarEntityOne", "planarEntityTwo"]
            elif case in ("three_points", "offset_through_point"):
                sketch = root.sketches.add(root.xYConstructionPlane)
                sketch.name = "SupportPoints"
                points = [sketch.sketchPoints.add(point(*p)) for p in ((1, 1, 0), (3, 1, 0), (1, 3, 0))]
                if case == "three_points":
                    success = inputs.setByThreePoints(*points)
                    role_names = ["pointEntityOne", "pointEntityTwo", "pointEntityThree"]
                else:
                    success = inputs.setByOffsetThroughPoint(root.yZConstructionPlane, points[1])
                    role_names = ["planarEntity", "point"]
            elif case == "two_edges":
                success = inputs.setByTwoEdges(root.xConstructionAxis, root.yConstructionAxis)
                role_names = ["linearEntityOne", "linearEntityTwo"]
            else:
                sketch = root.sketches.add(root.xYConstructionPlane)
                sketch.name = "CylinderProfile"
                sketch.sketchCurves.sketchCircles.addByCenterRadius(point(0, 0, 0), 1.)
                seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value("20 mm"),
                                                             adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                seed.name = "SeedExtrusion"
                seed.bodies.item(0).name = "CylinderBody"
                face = seed.sideFaces.item(0)
                if case == "tangent":
                    success = inputs.setByTangent(face, value("25 deg"), root.yZConstructionPlane)
                    role_names, scalar_names = ["tangentFace", "planarEntity"], ["angle"]
                else:
                    point_sketch = root.sketches.add(root.xYConstructionPlane)
                    point_sketch.name = "TangentPoint"
                    support_point = point_sketch.sketchPoints.add(point(1, 0, 0))
                    success = inputs.setByTangentAtPoint(face, support_point)
                    role_names = ["tangentFace", "pointEntity"]
            if not success:
                raise RuntimeError("Plane definition rejected")
            plane = root.constructionPlanes.add(inputs)
            if plane is None:
                raise RuntimeError("Plane add returned null")
            plane.name = "ProbePlane"
            definition = plane.definition
            sample = {"file": case+".f3d", "definition_type": definition.objectType.split("::")[-1],
                      "inputs": [{"role": role, "entity": entity_truth(getattr(definition, role))} for role in role_names],
                      "scalars": {name: getattr(definition, name).value for name in scalar_names},
                      "geometry": {"origin_cm": plane.geometry.origin.asArray(), "normal": plane.geometry.normal.asArray()},
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Plane definition export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Plane definition generation finished; consult errors.\n")
