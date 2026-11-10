"""Export a small sketch-placement corpus with independent API coordinates."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("placement-" + uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    try:
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        planes = [("XY", root.xYConstructionPlane), ("XZ", root.xZConstructionPlane),
                  ("YZ", root.yZConstructionPlane)]
        inputs = root.constructionPlanes.createInput()
        inputs.setByOffset(root.xYConstructionPlane, value("17 mm"))
        offset = root.constructionPlanes.add(inputs)
        offset.name = "Offset17mm"
        planes.append(("OffsetXY", offset))
        inputs = root.constructionPlanes.createInput()
        inputs.setByAngle(root.xConstructionAxis, value("30 deg"), root.xYConstructionPlane)
        angled = root.constructionPlanes.add(inputs)
        angled.name = "Angle30deg"
        planes.append(("AngledXY", angled))
        inputs = root.constructionPlanes.createInput()
        inputs.setByOffset(angled, value("-23 mm"))
        compound = root.constructionPlanes.add(inputs)
        compound.name = "AngledOffsetMinus23mm"
        planes.append(("AngledOffset", compound))
        for name, plane in planes:
            sketch = root.sketches.add(plane)
            sketch.name = "Placement" + name
            sketch.sketchCurves.sketchLines.addByTwoPoints(point(1.2, -0.7, 0), point(3.4, 2.1, 0))
            sketch.sketchCurves.sketchCircles.addByCenterRadius(point(-2, 1.3, 0), 0.6)
            local = [[0, 0, 0], [1.2, -0.7, 0], [3.4, 2.1, 0], [-2, 1.3, 0]]
            truth["samples"].append({
                "name": sketch.name, "plane_name": plane.name,
                "api_model_to_sketch_transform": sketch.transform.asArray(),
                "plane_transform": plane.transform.asArray(),
                "local_points_cm": local,
                "model_points_cm": [sketch.sketchToModelSpace(point(*p)).asArray() for p in local],
            })
        truth["parameters"] = [{"name": p.name, "role": p.role, "value": p.value,
                                 "unit": p.unit, "created_by": getattr(p.createdBy, "name", None)}
                                for p in root.modelParameters]
        options = design.exportManager.createFusionArchiveExportOptions(str(output / "placement.f3d"))
        if not design.exportManager.execute(options):
            raise RuntimeError("Placement export failed")
    except Exception:
        truth["errors"].append(traceback.format_exc())
    finally:
        doc.close(False)
        (output / "ground_truth.json").write_text(json.dumps(truth, indent=2))
        (output / "complete.txt").write_text("Placement export finished; consult errors.\n")
