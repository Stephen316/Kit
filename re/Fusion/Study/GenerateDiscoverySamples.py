"""Generate two feature families unknown to the label list for discovery work."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("discovery-" + uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    try:
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        planes = []
        for base, expression, name in ((root.xYConstructionPlane, "17 mm", "PlaneXY17"),
                                       (root.xZConstructionPlane, "-23 mm", "PlaneXZMinus23"),
                                       (root.yZConstructionPlane, "31 mm", "PlaneYZ31")):
            inputs = root.constructionPlanes.createInput()
            inputs.setByOffset(base, adsk.core.ValueInput.createByString(expression))
            plane = root.constructionPlanes.add(inputs)
            plane.name = name
            planes.append(plane)
            truth["samples"].append({"kind": "ConstructionPlane", "name": name, "transform": plane.transform.asArray()})
        inputs = root.constructionAxes.createInput()
        inputs.setByTwoPlanes(planes[0], planes[2])
        axis = root.constructionAxes.add(inputs)
        axis.name = "IntersectionAxis"
        truth["samples"].append({"kind": "ConstructionAxis", "name": axis.name,
                                 "origin_cm": axis.geometry.origin.asArray(), "direction": axis.geometry.direction.asArray()})
        inputs = root.constructionPoints.createInput()
        inputs.setByThreePlanes(*planes)
        point = root.constructionPoints.add(inputs)
        point.name = "IntersectionPoint"
        truth["samples"].append({"kind": "ConstructionPoint", "name": point.name, "position_cm": point.geometry.asArray()})
        options = design.exportManager.createFusionArchiveExportOptions(str(output / "discovery.f3d"))
        if not design.exportManager.execute(options):
            raise RuntimeError("Discovery export failed")
    except Exception:
        truth["errors"].append(traceback.format_exc())
    finally:
        doc.close(False)
        (output / "ground_truth.json").write_text(json.dumps(truth, indent=2))
        (output / "complete.txt").write_text("Discovery export finished; consult errors.\n")
