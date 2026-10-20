"""Generate a small sequence that isolates basic sketch record changes."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def point_data(point):
    return [point.x, point.y, point.z]


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("sketches-" + uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "coordinate_units": "cm", "samples": []}
    try:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        sketch = design.rootComponent.sketches.add(design.rootComponent.xYConstructionPlane)
        sketch.name = "BasicSketch"
        point = adsk.core.Point3D.create
        first = sketch.sketchCurves.sketchLines.addByTwoPoints(point(1, 2, 0), point(4, 2, 0))
        second = sketch.sketchCurves.sketchLines.addByTwoPoints(point(6, 2, 0), point(6, 5, 0))
        circle = sketch.sketchCurves.sketchCircles.addByCenterRadius(point(9, 3, 0), 1.25)
        constraints = sketch.geometricConstraints
        stages = [
            ("baseline", None),
            ("horizontal", lambda: constraints.addHorizontal(first)),
            ("vertical", lambda: constraints.addVertical(second)),
            ("coincident", lambda: constraints.addCoincident(first.endSketchPoint, second.startSketchPoint)),
            ("radius", lambda: sketch.sketchDimensions.addRadialDimension(circle, point(11, 5, 0))),
        ]
        for name, action in stages:
            if action is not None and action() is None:
                raise RuntimeError("Could not create constraint for " + name)
            design.computeAll()
            sample = {
                "file": name + ".f3d", "sketch_name": sketch.name,
                "lines": [{"start": point_data(line.startSketchPoint.geometry),
                           "end": point_data(line.endSketchPoint.geometry)} for line in (first, second)],
                "circles": [{"center": point_data(circle.centerSketchPoint.geometry), "radius": circle.radius}],
                "constraint_types": [constraints.item(i).objectType for i in range(constraints.count)],
                "dimensions": [{"type": sketch.sketchDimensions.item(i).objectType,
                                "parameter_name": sketch.sketchDimensions.item(i).parameter.name,
                                "value": sketch.sketchDimensions.item(i).parameter.value}
                               for i in range(sketch.sketchDimensions.count)],
            }
            options = design.exportManager.createFusionArchiveExportOptions(str(output / sample["file"]))
            if not design.exportManager.execute(options):
                raise RuntimeError("Sketch sample export failed")
            truth["samples"].append(sample)
            (output / "ground_truth.json").write_text(json.dumps(truth, indent=2))
        doc.close(False)
        (output / "complete.txt").write_text("Five sketch snapshots generated.\n")
    except Exception:
        (output / "error.txt").write_text(traceback.format_exc())
