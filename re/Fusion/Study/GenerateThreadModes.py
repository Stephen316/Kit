"""Controlled local thread modes using Fusion's installed metric thread data."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CASES = ("cosmetic_full", "modeled_full", "partial_high", "partial_low", "left_handed", "internal")


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("threadmodes-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    query = adsk.fusion.ThreadDataQuery.create(False)
    family = query.defaultMetricThreadType
    for case in CASES:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.sketchCurves.sketchCircles.addByCenterRadius(point(0, 0, 0), .6)
            internal = case == "internal"
            if internal:
                sketch.sketchCurves.sketchCircles.addByCenterRadius(point(0, 0, 0), 1.2)
            profile = next(p for p in sketch.profiles if p.profileLoops.count == (2 if internal else 1))
            seed = root.features.extrudeFeatures.addSimple(profile, value("20 mm"),
                                                         adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            face = next(f for f in seed.bodies.item(0).faces if f.geometry.objectType.endswith("Cylinder")
                        and abs(f.geometry.radius-.6) < 1e-9)
            ok, designation, thread_class = query.recommendThreadData(1.2, internal, family)
            if not ok:
                raise RuntimeError("Installed metric thread recommendation failed")
            info = adsk.fusion.ThreadInfo.create(False, internal, family, designation, thread_class, case != "left_handed")
            inputs = root.features.threadFeatures.createInput(face, info)
            inputs.isModeled = case == "modeled_full"
            if case.startswith("partial"):
                inputs.isFullLength = False
                inputs.threadLength = value("7 mm")
                inputs.threadOffset = value("2 mm")
                inputs.threadLocation = (adsk.fusion.ThreadLocations.LowEndThreadLocation if case == "partial_low" else
                                         adsk.fusion.ThreadLocations.HighEndThreadLocation)
            feature = root.features.threadFeatures.add(inputs)
            feature.name = "ProbeThread"
            if case == "left_handed":
                # This build did not retain the ThreadInfo.create handedness input.
                # Set the actual feature in its documented edit position instead.
                feature.timelineObject.rollTo(True)
                feature.isRightHanded = False
                design.timeline.moveToEnd()
            info = feature.threadInfo
            settings = {"thread_type": info.threadType, "thread_size": info.threadSize,
                        "thread_designation": info.threadDesignation, "thread_class": info.threadClass,
                        "is_internal": info.isInternal, "is_right_handed": feature.isRightHanded,
                        "info_is_right_handed": info.isRightHanded,
                        "is_modeled": feature.isModeled, "is_full_length": feature.isFullLength,
                        "stored_length_cm": feature.threadLength.value if feature.threadLength else None,
                        "stored_offset_cm": feature.threadOffset.value if feature.threadOffset else None,
                        "thread_location": feature.threadLocation, "pitch_cm": info.threadPitch,
                        "major_diameter_cm": info.majorDiameter, "minor_diameter_cm": info.minorDiameter,
                        "pitch_diameter_cm": info.pitchDiameter, "thread_angle_degrees": info.threadAngle}
            sample = {"file": case+".f3d", "settings": settings,
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Thread export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Thread exports finished; consult errors.\n")
