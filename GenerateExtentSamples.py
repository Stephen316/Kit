"""Controlled extrusion end/start conditions with API truth and local exports."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def describe_extent(extent):
    if extent is None:
        return None
    result = {"kind": extent.objectType.split("::")[-1]}
    for name in ("distance", "offset", "isPositiveDirection", "isChained"):
        if hasattr(extent, name):
            item = getattr(extent, name)
            result[name] = item.value if hasattr(item, "value") else item
    if hasattr(extent, "entity"):
        result["entity_name"] = getattr(extent.entity, "name", None)
    return result


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("extents-" + uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    distance = lambda text: adsk.fusion.DistanceExtentDefinition.create(value(text))
    operation, directions = adsk.fusion.FeatureOperations, adsk.fusion.ExtentDirections
    cases = ("distance_positive", "distance_negative", "offset_positive", "offset_negative",
             "to_plane", "to_plane_offset", "from_plane", "through_positive", "through_negative",
             "two_sided_mixed", "taper")
    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            cut = case.startswith("through") or case == "two_sided_mixed"
            if cut:
                seed_sketch = root.sketches.add(root.xYConstructionPlane)
                seed_sketch.name = "SeedProfile"
                seed_sketch.sketchCurves.sketchCircles.addByCenterRadius(point(0, 0, 0), 2)
                seed_input = root.features.extrudeFeatures.createInput(seed_sketch.profiles.item(0), operation.NewBodyFeatureOperation)
                seed_input.setSymmetricExtent(value("60 mm"), True)
                root.features.extrudeFeatures.add(seed_input).name = "SeedExtrusion"
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.name = "ProbeProfile"
            sketch.sketchCurves.sketchCircles.addByCenterRadius(point(0, 0, 0), 1)
            inputs = root.features.extrudeFeatures.createInput(
                sketch.profiles.item(0), operation.CutFeatureOperation if cut else operation.NewBodyFeatureOperation)
            direction = directions.NegativeExtentDirection if case in ("distance_negative", "through_negative") else directions.PositiveExtentDirection
            if case.startswith("to_plane") or case == "from_plane":
                plane_input = root.constructionPlanes.createInput()
                plane_input.setByOffset(root.xYConstructionPlane, value("30 mm"))
                plane = root.constructionPlanes.add(plane_input)
                plane.name = "TargetPlane"
            if case.startswith("through"):
                inputs.setOneSideExtent(adsk.fusion.ThroughAllExtentDefinition.create(), direction)
            elif case == "two_sided_mixed":
                inputs.setTwoSidesExtent(distance("11 mm"), adsk.fusion.ThroughAllExtentDefinition.create())
            elif case.startswith("to_plane"):
                extent = adsk.fusion.ToEntityExtentDefinition.create(
                    plane, False, value("4 mm" if case == "to_plane_offset" else "0 mm"))
                inputs.setOneSideExtent(extent, direction)
            else:
                inputs.setOneSideExtent(distance("17 mm"), direction, value("7 deg" if case == "taper" else "0 deg"))
            if case.startswith("offset"):
                inputs.startExtent = adsk.fusion.OffsetStartDefinition.create(
                    value("7 mm" if case == "offset_positive" else "-9 mm"))
            elif case == "from_plane":
                inputs.startExtent = adsk.fusion.FromEntityStartDefinition.create(plane, value("5 mm"))
            feature = root.features.extrudeFeatures.add(inputs)
            feature.name = "ProbeExtrusion"
            design.computeAll()
            bbox = root.bRepBodies.item(0).boundingBox
            sample = {"file": case+".f3d", "name": feature.name,
                      "extent_one": describe_extent(feature.extentOne),
                      "extent_two": describe_extent(feature.extentTwo) if feature.hasTwoExtents else None,
                      "start": describe_extent(feature.startExtent),
                      "taper_one": feature.taperAngleOne.value,
                      "body_bounds_cm": [bbox.minPoint.asArray(), bbox.maxPoint.asArray()],
                      "parameters": [{"name": p.name, "role": p.role, "value": p.value,
                                      "unit": p.unit, "created_by": getattr(p.createdBy, "name", None)}
                                     for p in root.modelParameters]}
            options = design.exportManager.createFusionArchiveExportOptions(str(output / sample["file"]))
            if not design.exportManager.execute(options):
                raise RuntimeError("Extent export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output / "ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output / "complete.txt").write_text("Extent export finished; consult errors.\n")
