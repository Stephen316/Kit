"""Four composite/spline body PathPattern captures with actual Path getter truth."""

import json
import math
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ("composite_identical", "composite_along", "spline_along", "composite_multiple")


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("pathpatterncomposites-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": [],
             "scope": "Actual PathPattern controls, input entity names/types, ordered Path members and opposed flags; no native traversal or instance association assumed"}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByReal
    cases = context.get("cases", CASES) if isinstance(context, dict) else CASES
    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        sample = {"case": case, "file": case+".f3d", "getter_errors": []}
        try:
            if case not in CASES:
                raise ValueError("Unknown composite PathPattern case")
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent

            def read(field, getter):
                try:
                    return getter()
                except Exception:
                    sample["getter_errors"].append({"field": field, "error": traceback.format_exc()})
                    return None

            def geometry_truth(geometry):
                evaluator = geometry.evaluator
                ok, low, high = evaluator.getParameterExtents()
                if not ok:
                    raise RuntimeError("Pattern path evaluator extents unavailable")
                ok_length, length = evaluator.getLengthAtParameter(low, high)
                item = {"geometry_type": geometry.objectType, "parameter_extents": [low, high],
                        "length_cm": length if ok_length else None, "samples": []}
                for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
                    parameter = low+fraction*(high-low)
                    success, position = evaluator.getPointAtParameter(parameter)
                    tangent_ok, tangent = evaluator.getTangent(parameter)
                    item["samples"].append({"parameter_fraction": fraction, "parameter": parameter,
                                            "point_cm": position.asArray() if success else None,
                                            "tangent": tangent.asArray() if tangent_ok else None})
                arc = adsk.core.Arc3D.cast(geometry)
                spline = adsk.core.NurbsCurve3D.cast(geometry)
                if arc:
                    item.update(center_cm=arc.center.asArray(), radius_cm=arc.radius, normal=arc.normal.asArray(),
                                reference_axis=arc.referenceVector.asArray(), start_angle_radians=arc.startAngle, end_angle_radians=arc.endAngle)
                elif spline:
                    success, controls, degree, knots, rational, weights, periodic = spline.getData()
                    item["nurbs"] = {"get_data_success": success, "control_points_cm": [p.asArray() for p in controls],
                                     "degree": degree, "knots": list(knots), "is_rational": rational,
                                     "weights": list(weights), "is_periodic": periodic}
                return item

            def source_truth(entity):
                item = {"entity_type": entity.objectType,
                        "entity_token": read("source.entity_token", lambda: getattr(entity, "entityToken", None))}
                curve = adsk.fusion.SketchCurve.cast(entity)
                if curve:
                    item.update(sketch_name=curve.parentSketch.name,
                                sketch_token=read("source.sketch_token", lambda: curve.parentSketch.entityToken),
                                natural_world_geometry=geometry_truth(curve.worldGeometry))
                return item

            def path_truth(path):
                if path is None:
                    return None
                item = {"entity_type": path.objectType, "count": path.count, "is_closed": path.isClosed, "members": []}
                for index in range(path.count):
                    member = path.item(index)
                    item["members"].append({"index": index, "is_opposed_to_entity": member.isOpposedToEntity,
                                             "source": source_truth(member.entity),
                                             "actual_path_geometry": geometry_truth(member.curve)})
                return item

            entities = adsk.core.ObjectCollection.create()
            for index in range(2 if case == "composite_multiple" else 1):
                sketch = root.sketches.add(root.xYConstructionPlane)
                sketch.name = "PatternSeedSketch"+str(index)
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0, index*1.2, 0), point(0.6, index*1.2+0.4, 0))
                seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value(0.5),
                                                             adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                seed.name = "PatternSeedFeature"+str(index)
                seed.bodies.item(0).name = "PatternSeedBody"+str(index)
                entities.add(seed.bodies.item(0))
            path_sketch = root.sketches.add(root.xYConstructionPlane)
            path_sketch.name = "CompositePatternPath"
            if case == "spline_along":
                fit_points = adsk.core.ObjectCollection.create()
                for position in ((0, 0, 0), (2, 0, 0), (4, 1, 0), (5, 3, 0), (6, 4, 0)):
                    fit_points.add(point(*position))
                source_curves = [path_sketch.sketchCurves.sketchFittedSplines.add(fit_points)]
                path = adsk.fusion.Path.create(source_curves[0], adsk.fusion.ChainedCurveOptions.noChainedCurves)
            else:
                line = path_sketch.sketchCurves.sketchLines.addByTwoPoints(point(0, 0, 0), point(3, 0, 0))
                arc = path_sketch.sketchCurves.sketchArcs.addByCenterStartSweep(point(3, 4, 0), line.endSketchPoint, math.pi/2)
                source_curves = [line, arc]
                collection = adsk.core.ObjectCollection.create()
                for curve in source_curves:
                    collection.add(curve)
                path = adsk.fusion.Path.create(collection, adsk.fusion.ChainedCurveOptions.noChainedCurves)
            if path is None:
                raise RuntimeError("Composite/spline pattern Path creation failed")
            sample["source_curves_before_pattern"] = [source_truth(curve) for curve in source_curves]
            sample["input_path_before_pattern"] = path_truth(path)
            extent = case != "composite_multiple"
            distance = 6.0 if extent else 1.5
            along = case in ("composite_along", "spline_along")
            mode = (adsk.fusion.PatternDistanceType.ExtentPatternDistanceType if extent
                    else adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
            inputs = root.features.pathPatternFeatures.createInput(entities, path, value(4), value(distance), mode)
            inputs.startPoint = 0.0
            inputs.isFlipDirection = False
            inputs.isSymmetric = False
            inputs.isOrientationAlongPath = along
            feature = root.features.pathPatternFeatures.add(inputs)
            feature.name = "ProbeCompositePathPattern"
            settings = {"health_state": read("health_state", lambda: feature.healthState),
                        "warning": read("warning", lambda: feature.errorOrWarningMessage)}
            feature.timelineObject.rollTo(True)
            actual_inputs = feature.inputEntities
            settings["inputs"] = [{"index": i, "entity_type": actual_inputs.item(i).objectType,
                                    "name": actual_inputs.item(i).name,
                                    "entity_token": read("input.token", lambda i=i: actual_inputs.item(i).entityToken)}
                                   for i in range(actual_inputs.count)]
            settings["path"] = path_truth(read("feature.path", lambda: feature.path))
            for field, getter in (("quantity", lambda: feature.quantity.value), ("distance_cm", lambda: feature.distance.value),
                                  ("start_fraction", lambda: feature.startPoint), ("is_flipped", lambda: feature.isFlipDirection),
                                  ("is_symmetric", lambda: feature.isSymmetric), ("orientation_along_path", lambda: feature.isOrientationAlongPath),
                                  ("distance_type", lambda: feature.patternDistanceType), ("pattern_entity_type", lambda: feature.patternEntityType),
                                  ("pattern_compute_option", lambda: feature.patternComputeOption)):
                settings[field] = read("settings."+field, getter)
            design.timeline.moveToEnd()
            settings["input_count"] = len(settings["inputs"])
            settings["result_body_count"] = root.bRepBodies.count
            settings["suppressed_element_ids"] = read("suppressed_element_ids", lambda: list(feature.suppressedElementsIds))
            sample["pattern_elements"] = []
            for index in range(feature.patternElements.count):
                element = feature.patternElements.item(index)
                sample["pattern_elements"].append({"collection_index": index, "id": element.id,
                                                   "is_suppressed": element.isSuppressed, "transform": element.transform.asArray()})
            sample["settings"] = settings
            sample["requested"] = {"quantity": 4, "distance_cm": distance, "distance_type": "Extent" if extent else "Spacing",
                                   "orientation_along_path": along, "start_fraction": 0.0, "is_flipped": False, "is_symmetric": False}
            sample["parameters"] = [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Composite PathPattern export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc(), "partial_capture": sample})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Composite PathPattern captures finished; consult errors.\n")
