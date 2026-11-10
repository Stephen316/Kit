"""Study-owned Boundary Fill controls/cells; always finish or cancel input transactions."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("boundaryfills-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    operations = adsk.fusion.FeatureOperations
    cases = [("new_middle", operations.NewBodyFeatureOperation, [1], False, False),
             ("new_first", operations.NewBodyFeatureOperation, [0], False, False),
             ("new_two", operations.NewBodyFeatureOperation, [0, 2], False, False),
             ("new_middle_remove", operations.NewBodyFeatureOperation, [1], True, False),
             ("join_middle", operations.JoinFeatureOperation, [1], False, False),
             ("cut_middle", operations.CutFeatureOperation, [1], False, False),
             ("intersect_middle", operations.IntersectFeatureOperation, [1], False, False),
             ("component_middle", operations.NewComponentFeatureOperation, [1], False, False),
             ("plane_first", operations.NewBodyFeatureOperation, [0], False, True)]

    def snapshot(body):
        bounds = body.boundingBox
        return {"min_cm": bounds.minPoint.asArray(), "max_cm": bounds.maxPoint.asArray(),
                "volume_cm3": body.physicalProperties.volume}

    for case, operation, choices, remove, plane_tool in cases:
        doc, pending = None, None
        try:
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent

            def box(x0, x1, name):
                sketch = root.sketches.add(root.xYConstructionPlane)
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(x0, 0, 0), point(x1, 2, 0))
                extrude = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value("20 mm"),
                                                                operations.NewBodyFeatureOperation)
                body = extrude.bodies.item(0)
                body.name = name
                return body

            tools = adsk.core.ObjectCollection.create()
            tools.add(box(0, 3, "ToolA"))
            if plane_tool:
                plane_input = root.constructionPlanes.createInput()
                plane_input.setByOffset(root.yZConstructionPlane, value("12 mm"))
                plane = root.constructionPlanes.add(plane_input)
                plane.name = "ToolPlane"
                tools.add(plane)
            else:
                tools.add(box(2, 5, "ToolB"))
            pending = root.features.boundaryFillFeatures.createInput(tools, operation)
            if pending is None:
                raise RuntimeError("Boundary Fill input creation failed")
            pending.isRemoveTools = remove
            tool_names = [tools.item(i).name for i in range(tools.count)]
            cells = pending.bRepCells
            if max(choices) >= cells.count:
                raise RuntimeError("Expected cell choices unavailable: "+str(cells.count))
            cell_truth = []
            for index in range(cells.count):
                cell = cells.item(index)
                cell.isSelected = index in choices
                cell_truth.append({"index": index, "selected": cell.isSelected,
                                   "source_tools": [cell.sourceTools.item(j).name for j in range(cell.sourceTools.count)],
                                   "geometry": snapshot(cell.cellBody)})
            feature = root.features.boundaryFillFeatures.add(pending)
            if feature is None:
                raise RuntimeError("Boundary Fill add returned null")
            pending = None
            feature.name = "ProbeBoundaryFill"
            sample = {"file": case+".f3d", "operation": feature.operation,
                      "cells_before_add": cell_truth,
                      "requested_choices": choices, "tool_names": tool_names,
                      "output_bodies": [{"name": feature.bodies.item(i).name,
                                         "geometry": snapshot(feature.bodies.item(i))} for i in range(feature.bodies.count)],
                      "health_state": feature.healthState, "warning": feature.errorOrWarningMessage}
            feature.timelineObject.rollTo(True)
            sample["is_remove_tools"] = feature.isRemoveTools
            design.timeline.moveToEnd()
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Boundary Fill archive export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            if pending is not None:
                try:
                    pending.cancel()
                except Exception:
                    truth["errors"].append({"case": case, "cancel_error": traceback.format_exc()})
            if doc is not None:
                doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Boundary Fill generation finished; consult errors.\n")
