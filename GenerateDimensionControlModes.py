"""Paired driving/reference dimensions with real annotation getter readback."""

import json
import traceback
import uuid
from pathlib import Path

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("dimcontrols-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": [],
             "sdk_scope": "Installed SketchDimension exposes textPosition/isDriving setters; tangent side selection is supplied only at creation, without per-side getters/setters."}
    point = adsk.core.Point3D.create
    positions = {"radius": ((4.1, 5.2, 0), (4.6, 5.7, 0)),
                 "diameter": ((3.7, 5.3, 0), (4.3, 5.9, 0)),
                 "angle": ((2.5, 1.8, 0), (2.8, 2.2, 0)),
                 "tangent": ((3.1, 4.3, 0), (3.4, 4.8, 0))}
    for kind in ("radius", "diameter", "angle", "tangent"):
        for driving in (True, False):
            case = kind+("_driving" if driving else "_reference")
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            try:
                design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
                design.designType = adsk.fusion.DesignTypes.ParametricDesignType
                root = design.rootComponent
                sketch = root.sketches.add(root.xYConstructionPlane)
                sketch.name = "ProbeDimension"
                curves, dimensions = sketch.sketchCurves, sketch.sketchDimensions
                requested, final = positions[kind]
                geometry = []
                if kind in ("radius", "diameter"):
                    circle = curves.sketchCircles.addByCenterRadius(point(1.2, 2.3, 0) if kind == "radius" else point(-1.3, 2.6, 0),
                                                                  1.4 if kind == "radius" else .85)
                    method = dimensions.addRadialDimension if kind == "radius" else dimensions.addDiameterDimension
                    dimension = method(circle, point(*requested), driving)
                    geometry.append(circle)
                elif kind == "angle":
                    first = curves.sketchLines.addByTwoPoints(point(.4, .6, 0), point(4.4, .6, 0))
                    second = curves.sketchLines.addByTwoPoints(point(.4, .6, 0), point(2.4, 3.6, 0))
                    dimension = dimensions.addAngularDimension(first, second, point(*requested), driving)
                    geometry.extend((first, second))
                else:
                    first = curves.sketchCircles.addByCenterRadius(point(.8, 1.2, 0), .6)
                    second = curves.sketchCircles.addByCenterRadius(point(5.2, 1.2, 0), .9)
                    dimension = dimensions.addTangentDistanceDimension(first, False, second, False, point(*requested), driving)
                    geometry.extend((first, second))
                if dimension is None:
                    raise RuntimeError("Dimension creation rejected")
                before = dimension.textPosition.asArray()
                dimension.textPosition = point(*final)
                design.computeAll()
                parameter = dimension.parameter
                entities = []
                for curve in geometry:
                    item = {"kind": curve.objectType.split("::")[-1]}
                    if adsk.fusion.SketchCircle.cast(curve):
                        item.update(center_cm=curve.centerSketchPoint.geometry.asArray(), radius_cm=curve.radius)
                    else:
                        item.update(start_cm=curve.startSketchPoint.geometry.asArray(), end_cm=curve.endSketchPoint.geometry.asArray())
                    entities.append(item)
                sample = {"file": case+".f3d", "kind": kind, "sketch_name": sketch.name,
                          "dimension": {"object_type": dimension.objectType, "is_driving": dimension.isDriving,
                                        "value": dimension.value,
                                        "requested_creation_text_position_cm": list(requested),
                                        "creation_text_position_getter_cm": before,
                                        "requested_updated_text_position_cm": list(final),
                                        "updated_text_position_getter_cm": dimension.textPosition.asArray(),
                                        "parameter_name": parameter.name, "parameter_value": parameter.value,
                                        "parameter_expression": parameter.expression,
                                        "parameter_role": getattr(parameter, "role", None),
                                        "parameter_unit": parameter.unit, "parameter_object_type": parameter.objectType},
                          "geometry": entities}
                if kind == "tangent":
                    sample["requested_tangent_sides"] = {"entity_one_closest_to_two": False, "entity_two_closest_to_one": False}
                    sample["tangent_side_scope"] = "Creation arguments only; no per-side getter or setter in installed SDK. No independent tangent-side contrast in this paired driving probe."
                if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                    raise RuntimeError("Dimension control export failed")
                truth["samples"].append(sample)
            except Exception:
                truth["errors"].append({"case": case, "error": traceback.format_exc()})
            finally:
                doc.close(False)
                (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Dimension control exports finished; consult errors.\n")
