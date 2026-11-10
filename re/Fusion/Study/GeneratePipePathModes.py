"""Composite, spline and explicit BRep-edge Pipe path getter captures."""

import json
import math
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ("composite_circular", "composite_square_hollow_partial", "spline_circular", "brep_edge_circular")


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("pipepaths-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": [],
             "scope": "Actual Pipe dimensions/conditions and Path source/member geometry; API tokens/opposed flags are evidence without native topology/traversal assumptions"}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByReal
    cases = context.get("cases", CASES) if isinstance(context, dict) else CASES
    for case in cases:
        sample = {"case": case, "file": case+".f3d", "getter_errors": []}
        doc = None
        try:
            (output/"progress.json").write_text(json.dumps({"case":case,"phase":"creating_document"})+"\n")
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            if case not in CASES:
                raise ValueError("Unknown Pipe path case")
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent

            def read(field, getter):
                try:
                    return getter()
                except Exception:
                    sample["getter_errors"].append({"field": field, "error": traceback.format_exc()})
                    return None

            def evaluator_truth(evaluator):
                ok, low, high = evaluator.getParameterExtents()
                if not ok:
                    raise RuntimeError("Pipe path evaluator extents unavailable")
                ok_length, length = evaluator.getLengthAtParameter(low, high)
                item = {"parameter_extents": [low, high], "length_cm": length if ok_length else None, "samples": []}
                for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
                    parameter = low+fraction*(high-low)
                    success, position = evaluator.getPointAtParameter(parameter)
                    tangent_ok, tangent = evaluator.getTangent(parameter)
                    item["samples"].append({"parameter_fraction": fraction, "parameter": parameter,
                                            "point_cm": position.asArray() if success else None,
                                            "tangent": tangent.asArray() if tangent_ok else None})
                return item

            def geometry_truth(geometry):
                item = {"geometry_type": geometry.objectType, **evaluator_truth(geometry.evaluator)}
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
                        "entity_token": read("source.token", lambda: getattr(entity, "entityToken", None))}
                curve = adsk.fusion.SketchCurve.cast(entity)
                edge = adsk.fusion.BRepEdge.cast(entity)
                if curve:
                    item.update(sketch_name=curve.parentSketch.name,
                                sketch_token=read("source.sketch_token", lambda: curve.parentSketch.entityToken),
                                natural_world_geometry=geometry_truth(curve.worldGeometry))
                elif edge:
                    item.update(body_name=edge.body.name, body_token=read("source.body_token", lambda: edge.body.entityToken),
                                natural_geometry=geometry_truth(edge.geometry), trimmed_edge_evaluator=evaluator_truth(edge.evaluator),
                                start_vertex_point_cm=read("source.start_vertex", lambda: edge.startVertex.geometry.asArray() if edge.startVertex else None),
                                end_vertex_point_cm=read("source.end_vertex", lambda: edge.endVertex.geometry.asArray() if edge.endVertex else None))
                return item

            def path_truth(path):
                if path is None:
                    return None
                item = {"entity_type": path.objectType, "count": path.count, "is_closed": path.isClosed, "members": []}
                for index in range(path.count):
                    member = path.item(index)
                    item["members"].append({"index": index, "is_opposed_to_entity": member.isOpposedToEntity,
                                             "source": source_truth(member.entity), "actual_path_geometry": geometry_truth(member.curve)})
                return item

            if case == "brep_edge_circular":
                sketch = root.sketches.add(root.xYConstructionPlane)
                sketch.name = "PipeEdgeSupportSketch"
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0, 0, 0), point(1, 1, 0))
                seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value(3),
                                                             adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                seed.name = "PipeEdgeSupportExtrude"
                body = seed.bodies.item(0)
                body.name = "PipePathSupportBody"
                matches = []
                for index in range(body.edges.count):
                    edge = body.edges.item(index)
                    if edge.startVertex and edge.endVertex:
                        endpoints = [edge.startVertex.geometry, edge.endVertex.geometry]
                        if (any(p.distanceTo(point(0, 0, 0)) < 1e-9 for p in endpoints)
                                and any(p.distanceTo(point(0, 0, 3)) < 1e-9 for p in endpoints)):
                            matches.append(edge)
                if len(matches) != 1:
                    raise RuntimeError("Study vertical BRep edge missing or ambiguous")
                source_curves = matches
                path = adsk.fusion.Path.create(matches[0], adsk.fusion.ChainedCurveOptions.noChainedCurves)
                sample["requested_source"] = "Explicit support-body BRepEdge with endpoints(0,0,0)/(0,0,3); selection rule is fixture construction, not native topology mapping"
            else:
                sketch = root.sketches.add(root.xYConstructionPlane)
                sketch.name = "PipePathSketch"
                if case == "spline_circular":
                    fit_points = adsk.core.ObjectCollection.create()
                    for position in ((0, 0, 0), (2, 0, 0), (4, 1, 0), (5, 3, 0), (6, 4, 0)):
                        fit_points.add(point(*position))
                    source_curves = [sketch.sketchCurves.sketchFittedSplines.add(fit_points)]
                    path = adsk.fusion.Path.create(source_curves[0], adsk.fusion.ChainedCurveOptions.noChainedCurves)
                else:
                    line = sketch.sketchCurves.sketchLines.addByTwoPoints(point(0, 0, 0), point(3, 0, 0))
                    arc = sketch.sketchCurves.sketchArcs.addByCenterStartSweep(point(3, 4, 0), line.endSketchPoint, math.pi/2)
                    source_curves = [line, arc]
                    collection = adsk.core.ObjectCollection.create()
                    collection.add(line)
                    collection.add(arc)
                    path = adsk.fusion.Path.create(collection, adsk.fusion.ChainedCurveOptions.noChainedCurves)
            if path is None:
                raise RuntimeError("Pipe Path creation failed")
            sample["source_entities_before_pipe"] = [source_truth(entity) for entity in source_curves]
            sample["input_path_before_pipe"] = path_truth(path)
            inputs = root.features.pipeFeatures.createInput(path, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            hollow = case == "composite_square_hollow_partial"
            inputs.sectionType = adsk.fusion.PipeSectionTypes.SquarePipeSectionType if hollow else adsk.fusion.PipeSectionTypes.CircularPipeSectionType
            inputs.sectionSize = value(0.6 if hollow else 0.4)
            if hollow:
                inputs.sectionThickness = value(0.1)
                inputs.distanceOne = value(0.75)
            feature = root.features.pipeFeatures.add(inputs)
            feature.name = "ProbePipePath"
            settings = {"result_body_count": feature.bodies.count, "root_body_count": root.bRepBodies.count,
                        "result_is_solid": [body.isSolid for body in feature.bodies],
                        "health_state": read("health_state", lambda: feature.healthState), "warning": read("warning", lambda: feature.errorOrWarningMessage)}
            feature.timelineObject.rollTo(True)
            settings["path"] = path_truth(read("feature.path", lambda: feature.path))
            for field, getter in (("operation", lambda: feature.operation), ("section_type", lambda: feature.sectionType),
                                  ("section_size_cm", lambda: feature.sectionSize.value), ("is_hollow", lambda: feature.isHollow),
                                  ("section_thickness_cm", lambda: feature.sectionThickness.value if feature.sectionThickness else None),
                                  ("distance_one", lambda: feature.distanceOne.value if feature.distanceOne else None),
                                  ("distance_two", lambda: feature.distanceTwo.value if feature.distanceTwo else None)):
                settings[field] = read("settings."+field, getter)
            design.timeline.moveToEnd()
            sample["settings"] = settings
            sample["parameters"] = [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Pipe path export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc(), "partial_capture": sample})
        finally:
            if doc is not None:
                doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Pipe path captures finished; consult errors.\n")
