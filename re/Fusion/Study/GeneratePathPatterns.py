"""Local body path-pattern controls, arc orientation and suppression evidence."""

import json
import math
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("pathpatterns-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    cases = ("spacing", "extent", "start_offset", "flipped", "symmetric", "arc_identical", "arc_along", "multiple_bodies", "suppressed_instance")
    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            entities = adsk.core.ObjectCollection.create()
            for index in range(2 if case == "multiple_bodies" else 1):
                sketch = root.sketches.add(root.xYConstructionPlane)
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0, index*2, 0), point(1, index*2+1, 0))
                seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value("10 mm"),
                                                             adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                entities.add(seed.bodies.item(0))
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.name = "PatternPath"
            if case.startswith("arc"):
                curve = sketch.sketchCurves.sketchArcs.addByCenterStartSweep(point(0, 0, 0), point(4, 0, 0), math.pi/2)
            else:
                curve = sketch.sketchCurves.sketchLines.addByTwoPoints(point(0, 0, 0), point(6, 0, 0))
            path = root.features.createPath(curve, False)
            extent = case == "extent" or case.startswith("arc") or case == "symmetric"
            distance = "20 mm" if case == "symmetric" else "45 mm" if extent else "10 mm" if case in ("flipped", "start_offset") else "15 mm"
            inputs = root.features.pathPatternFeatures.createInput(entities, path, value("3" if case == "symmetric" else "4"),
                                                                  value(distance), 0 if extent else 1)
            inputs.startPoint = {"start_offset": .25, "flipped": .75, "symmetric": .5}.get(case, 0.)
            inputs.isFlipDirection = case == "flipped"
            inputs.isSymmetric = case == "symmetric"
            inputs.isOrientationAlongPath = case == "arc_along"
            feature = root.features.pathPatternFeatures.add(inputs)
            feature.name = "ProbePathPattern"
            if case == "suppressed_instance":
                feature.timelineObject.rollTo(True)
                feature.suppressedElementsIds = [1]
                design.timeline.moveToEnd()
            settings = {"quantity": feature.quantity.value, "distance_cm": feature.distance.value,
                        "start_fraction": feature.startPoint, "is_flipped": feature.isFlipDirection,
                        "is_symmetric": feature.isSymmetric, "orientation_along_path": feature.isOrientationAlongPath,
                        "distance_type": feature.patternDistanceType, "input_body_count": entities.count,
                        "suppressed_element_ids": list(feature.suppressedElementsIds),
                        "path_geometry_kind": "Arc" if case.startswith("arc") else "Line",
                        "result_body_count": root.bRepBodies.count}
            sample = {"file": case+".f3d", "settings": settings,
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Path pattern export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Path pattern exports finished; consult errors.\n")
