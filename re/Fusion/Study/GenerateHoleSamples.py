"""Controlled single-position hole modes, end conditions and numeric settings."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("holes-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    for case in ("simple", "counterbore", "countersink", "through_all", "to_bottom", "flat_tip"):
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.name = "BlockProfile"
            sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(1, 1, 0), point(5, 4, 0))
            seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value("20 mm"),
                                                          adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            seed.name = "BlockExtrusion"
            if case == "counterbore":
                inputs = root.features.holeFeatures.createCounterboreInput(value("6 mm"), value("12 mm"), value("3 mm"))
            elif case == "countersink":
                inputs = root.features.holeFeatures.createCountersinkInput(value("6 mm"), value("12 mm"), value("82 deg"))
            else:
                inputs = root.features.holeFeatures.createSimpleInput(value("6 mm"))
            inputs.setPositionByPoint(seed.endFaces.item(0), point(3, 2, 2))
            if case == "through_all":
                inputs.setAllExtent(adsk.fusion.ExtentDirections.PositiveExtentDirection)
            elif case == "to_bottom":
                inputs.setOneSideToExtent(seed.startFaces.item(0), False)
            else:
                inputs.setDistanceExtent(value("12 mm"))
            if case == "flat_tip":
                inputs.tipAngle = value("180 deg")
            feature = root.features.holeFeatures.add(inputs)
            feature.name = "ProbeHole"
            design.computeAll()
            sample = {"file": case+".f3d", "name": feature.name, "hole_type": feature.holeType,
                      "position_cm": feature.position.asArray(), "direction": feature.direction.asArray(),
                      "is_default_direction": feature.isDefaultDirection,
                      "extent_kind": feature.extentDefinition.objectType.split("::")[-1],
                      "settings": {"diameter": feature.holeDiameter.value, "tip_angle": feature.tipAngle.value},
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value, "unit": p.unit,
                                      "created_by": getattr(p.createdBy, "name", None)} for p in root.modelParameters]}
            if case == "counterbore":
                sample["settings"].update(counterbore_diameter=feature.counterboreDiameter.value,
                                          counterbore_depth=feature.counterboreDepth.value)
            elif case == "countersink":
                sample["settings"].update(countersink_diameter=feature.countersinkDiameter.value,
                                          countersink_angle=feature.countersinkAngle.value)
            options = design.exportManager.createFusionArchiveExportOptions(str(output / sample["file"]))
            if not design.exportManager.execute(options):
                raise RuntimeError("Hole sample export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output / "ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output / "complete.txt").write_text("Hole export finished; consult errors.\n")
