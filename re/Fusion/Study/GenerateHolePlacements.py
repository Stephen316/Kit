"""Reversed, sketch-point, multiple-point and center-edge hole definitions."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("holeplacements-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    for case in ("reversed_distance", "reversed_all", "sketch_point", "sketch_points", "center_edge"):
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sketch = root.sketches.add(root.xYConstructionPlane)
            if case == "center_edge":
                sketch.sketchCurves.sketchCircles.addByCenterRadius(point(3, 2, 0), 2)
            else:
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(1, 1, 0), point(5, 4, 0))
            seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value("20 mm"),
                                                         adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            top = seed.endFaces.item(0)
            inputs = root.features.holeFeatures.createSimpleInput(value("4.5 mm"))
            positions = [[3., 2., 2.]]
            if case.startswith("reversed"):
                positions = [[3., 2., 0.]]
                inputs.setPositionByPoint(root.xYConstructionPlane, point(*positions[0]))
                if case == "reversed_all":
                    inputs.setAllExtent(adsk.fusion.ExtentDirections.PositiveExtentDirection)
                else:
                    inputs.setDistanceExtent(value("11 mm"))
                inputs.isDefaultDirection = False
            else:
                if case.startswith("sketch_point"):
                    locations = root.sketches.add(top)
                    locations.name = "HoleLocations"
                    if case == "sketch_points":
                        positions = [[2., 1.5, 2.], [3., 2.5, 2.], [4., 3., 2.]]
                    points = adsk.core.ObjectCollection.create()
                    for position in positions:
                        points.add(locations.sketchPoints.add(locations.modelToSketchSpace(point(*position))))
                    if case == "sketch_points":
                        inputs.setPositionBySketchPoints(points)
                    else:
                        inputs.setPositionBySketchPoint(points.item(0))
                else:
                    inputs.setPositionAtCenter(top, top.edges.item(0))
                inputs.setDistanceExtent(value("11 mm"))
            feature = root.features.holeFeatures.add(inputs)
            feature.name = "ProbeHolePlacement"
            design.computeAll()
            sample = {"file": case+".f3d", "position_definition": feature.holePositionDefinition.objectType.split("::")[-1],
                      "input_positions_cm": positions, "position_cm": feature.position.asArray() if len(positions) == 1 else None,
                      "direction": feature.direction.asArray(), "is_default_direction": feature.isDefaultDirection,
                      "diameter_cm": feature.holeDiameter.value, "extent_kind": feature.extentDefinition.objectType.split("::")[-1],
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            options = design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))
            if not design.exportManager.execute(options):
                raise RuntimeError("Hole placement export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Hole placement exports finished; consult errors.\n")
