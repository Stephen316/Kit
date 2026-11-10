"""Study-owned tapped holes and their automatically attached thread features."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("tappedholes-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    query = adsk.fusion.ThreadDataQuery.create(False)
    family = query.defaultMetricThreadType
    for case in ("cosmetic_full", "cosmetic_partial", "modeled_full"):
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0, 0, 0), point(4, 3, 0))
            seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value("20 mm"),
                                                         adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            inputs = root.features.holeFeatures.createSimpleInput(value("6 mm"))
            inputs.setPositionByPoint(seed.endFaces.item(0), point(2, 1.5, 2))
            inputs.setDistanceExtent(value("12 mm"))
            ok, designation, thread_class = query.recommendThreadData(1.2, True, family)
            if not ok or not inputs.setToTappedHole(adsk.fusion.ThreadInfo.create(False, True, family, designation, thread_class, True)):
                raise RuntimeError("Tapped hole definition failed")
            inputs.isModeled = case == "modeled_full"
            if case == "cosmetic_partial" and not inputs.setLengthAndOffset(value("7 mm"), value("1 mm")):
                raise RuntimeError("Tapped hole partial extent rejected")
            hole = root.features.holeFeatures.add(inputs)
            hole.name = "ProbeTappedHole"
            thread = hole.thread
            if thread is None:
                raise RuntimeError("Tapped hole did not expose its attached thread")
            info = thread.threadInfo
            sample = {"file": case+".f3d", "settings": {"tap_type": hole.holeTapType,
                      "hole_diameter_cm": hole.holeDiameter.value, "position_cm": hole.position.asArray(),
                      "thread_name": thread.name, "thread_hole_name": thread.hole.name,
                      "is_modeled": thread.isModeled, "is_full_length": thread.isFullLength,
                      "thread_length_cm": thread.threadLength.value if thread.threadLength else None,
                      "thread_offset_cm": thread.threadOffset.value if thread.threadOffset else None,
                      "thread_designation": info.threadDesignation, "thread_class": info.threadClass,
                      "is_internal": info.isInternal},
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Tapped hole export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Tapped hole generation finished; consult errors.\n")
