"""Five BRep-edge Pipe contrasts using documented Path and PipeFeatureInput APIs.

Only actual API getters constitute ground truth. Native optional-selector presence
is inspected offline after export; it is not inferred from the source geometry.
"""

import json
import math
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ("line_full", "line_partial", "line_offset_negative_partial",
         "circle_full", "circle_partial_two_sided")


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("pipeedgecontrasts-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": [],
             "scope": "Actual BRep Path closure, member geometry and Pipe fractions; native selectors and topology links require separate offline inspection",
             "sdk_basis": {"PipeFeatureInput.distanceOne": "Open fraction 0..1; closed fraction <=1-distanceTwo",
                           "PipeFeatureInput.distanceTwo": "Set distanceOne first; ignored/null for open path",
                           "PipeFeature.path": "Start follows first curve; getter captured with timeline immediately before Pipe"}}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByReal
    cases = context.get("cases", CASES) if isinstance(context, dict) else CASES
    for case in cases:
        sample = {"case": case, "file": case+".f3d", "getter_errors": []}
        doc = design = None
        try:
            (output/"progress.json").write_text(json.dumps({"case": case, "phase": "creating_document"})+"\n")
            if case not in CASES:
                raise ValueError("Unknown edge contrast case")
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
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
                    raise RuntimeError("Edge evaluator parameter extents unavailable")
                length_ok, length = evaluator.getLengthAtParameter(low, high)
                result = {"parameter_extents": [low, high], "length_cm": length if length_ok else None, "samples": []}
                for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
                    parameter = low+fraction*(high-low)
                    point_ok, position = evaluator.getPointAtParameter(parameter)
                    tangent_ok, tangent = evaluator.getTangent(parameter)
                    result["samples"].append({"parameter_fraction": fraction, "parameter": parameter,
                                               "point_cm": position.asArray() if point_ok else None,
                                               "tangent": tangent.asArray() if tangent_ok else None})
                return result

            def geometry_truth(geometry):
                result = {"geometry_type": geometry.objectType, **evaluator_truth(geometry.evaluator)}
                line = adsk.core.Line3D.cast(geometry)
                circle = adsk.core.Circle3D.cast(geometry)
                if line:
                    result.update(start_point_cm=line.startPoint.asArray(), end_point_cm=line.endPoint.asArray())
                if circle:
                    result.update(center_cm=circle.center.asArray(), radius_cm=circle.radius,
                                  normal=circle.normal.asArray())
                return result

            def vertex_truth(vertex, field):
                if vertex is None:
                    return None
                return {"entity_type": vertex.objectType, "point_cm": vertex.geometry.asArray(),
                        "entity_token": read(field+".token", lambda: vertex.entityToken)}

            def edge_truth(edge):
                return {"entity_type": edge.objectType, "entity_token": read("source.token", lambda: edge.entityToken),
                        "body_name": edge.body.name, "body_token": read("source.body_token", lambda: edge.body.entityToken),
                        "natural_geometry": geometry_truth(edge.geometry),
                        "trimmed_edge_evaluator": evaluator_truth(edge.evaluator),
                        "is_param_reversed": read("source.isParamReversed", lambda: edge.isParamReversed),
                        "start_vertex": read("source.start_vertex", lambda: vertex_truth(edge.startVertex, "start_vertex")),
                        "end_vertex": read("source.end_vertex", lambda: vertex_truth(edge.endVertex, "end_vertex"))}

            def path_truth(path):
                if path is None:
                    return None
                return {"entity_type": path.objectType, "count": path.count, "is_closed": path.isClosed,
                        "members": [{"index": i, "is_opposed_to_entity": path.item(i).isOpposedToEntity,
                                     "source": edge_truth(path.item(i).entity),
                                     "actual_path_geometry": geometry_truth(path.item(i).curve)} for i in range(path.count)]}

            closed = case.startswith("circle_")
            offset = case == "line_offset_negative_partial"
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.name = "PipeEdgeSupportSketch"
            if closed:
                sketch.sketchCurves.sketchCircles.addByCenterRadius(point(0, 0, 0), 2)
            else:
                low = (2, -1, 0) if offset else (0, 0, 0)
                high = (3, 0, 0) if offset else (1, 1, 0)
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(*low), point(*high))
            distance = -3 if offset else 3
            seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value(distance),
                                                         adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            seed.name = "PipeEdgeSupportExtrude"
            body = seed.bodies.item(0)
            body.name = "PipePathSupportBody"
            matches = []
            for index in range(body.edges.count):
                edge = body.edges.item(index)
                if closed:
                    geometry = adsk.core.Circle3D.cast(edge.geometry)
                    selected = geometry and geometry.center.distanceTo(point(0, 0, 3)) < 1e-9 and abs(geometry.radius-2) < 1e-9
                else:
                    a, b = point(*low), point(low[0], low[1], distance)
                    endpoints = [edge.startVertex.geometry, edge.endVertex.geometry] if edge.startVertex and edge.endVertex else []
                    selected = (any(p.distanceTo(a) < 1e-9 for p in endpoints)
                                and any(p.distanceTo(b) < 1e-9 for p in endpoints))
                if selected:
                    matches.append(edge)
            if len(matches) != 1:
                raise RuntimeError("Controlled support edge missing or ambiguous: "+str(len(matches)))
            source = matches[0]
            path = adsk.fusion.Path.create(source, adsk.fusion.ChainedCurveOptions.noChainedCurves)
            if path is None:
                raise RuntimeError("Explicit BRep-edge Path creation failed")
            sample["requested"] = {"source": "Top circular edge" if closed else "Vertical support edge at selected rectangle corner",
                                   "support_extrude_cm": distance, "fixture_selection_only": True,
                                   "distance_one": 0.35 if closed and case.endswith("two_sided") else (0.4 if "partial" in case else 1.0),
                                   "distance_two": 0.2 if case.endswith("two_sided") else None}
            sample["source_before_pipe"] = edge_truth(source)
            sample["input_path_before_pipe"] = path_truth(path)
            inputs = root.features.pipeFeatures.createInput(path, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            inputs.sectionType = adsk.fusion.PipeSectionTypes.CircularPipeSectionType
            inputs.sectionSize = value(0.4)
            inputs.distanceOne = value(sample["requested"]["distance_one"])
            if sample["requested"]["distance_two"] is not None:
                inputs.distanceTwo = value(sample["requested"]["distance_two"])
            feature = root.features.pipeFeatures.add(inputs)
            feature.name = "ProbePipeEdgeContrast"
            settings = {"result_body_count": feature.bodies.count, "root_body_count": root.bRepBodies.count,
                        "result_is_solid": [b.isSolid for b in feature.bodies],
                        "result_bounding_boxes_cm": [{"min": b.boundingBox.minPoint.asArray(), "max": b.boundingBox.maxPoint.asArray()} for b in feature.bodies],
                        "health_state": read("health_state", lambda: feature.healthState),
                        "warning": read("warning", lambda: feature.errorOrWarningMessage)}
            feature.timelineObject.rollTo(True)
            settings["path"] = read("feature.path", lambda: path_truth(feature.path))
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
                raise RuntimeError("Pipe edge contrast export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc(), "partial_capture": sample})
        finally:
            if design is not None:
                try:
                    design.timeline.moveToEnd()
                except Exception:
                    sample["getter_errors"].append({"field": "finally.restore_timeline", "error": traceback.format_exc()})
            if doc is not None:
                doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Pipe BRep-edge contrasts finished; consult errors.\n")
