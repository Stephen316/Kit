"""Export controlled ambiguous-profile choices with API loop/curve truth."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def curve_truth(curve):
    geometry = curve.geometry
    item = {"kind": curve.objectType.split("::")[-1], "entity_token": curve.entityToken}
    if isinstance(geometry, adsk.core.Circle3D):
        item.update(center_cm=geometry.center.asArray(), radius_cm=geometry.radius)
    return item


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("profiles-" + uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    for case in ("disjoint_left", "disjoint_right", "concentric_disk", "concentric_annulus"):
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.name = "MultipleProfiles"
            sketch.sketchCurves.sketchCircles.addByCenterRadius(point(0, 0, 0), 1)
            sketch.sketchCurves.sketchCircles.addByCenterRadius(
                point(4, 0, 0) if case.startswith("disjoint") else point(0, 0, 0),
                1 if case.startswith("disjoint") else 2)
            candidates = list(sketch.profiles)
            if case.startswith("disjoint"):
                candidates.sort(key=lambda p: p.areaProperties().centroid.x)
                selected = candidates[0 if case.endswith("left") else -1]
            else:
                candidates.sort(key=lambda p: p.areaProperties().area)
                selected = candidates[0 if case.endswith("disk") else -1]
            loops = [{"is_outer": loop.isOuter, "curves": [curve_truth(c.sketchEntity) for c in loop.profileCurves]}
                     for loop in selected.profileLoops]
            feature = root.features.extrudeFeatures.addSimple(
                selected, value("17 mm"), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            feature.name = "SelectedRegionExtrusion"
            sample = {"file": case+".f3d", "sketch_name": sketch.name, "feature_name": feature.name,
                      "available_profile_count": sketch.profiles.count, "selected_profile_area_cm2": selected.areaProperties().area,
                      "selected_loops": loops, "all_sketch_curves": [curve_truth(c) for c in sketch.sketchCurves]}
            options = design.exportManager.createFusionArchiveExportOptions(str(output / sample["file"]))
            if not design.exportManager.execute(options):
                raise RuntimeError("Profile export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output / "ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output / "complete.txt").write_text("Profile export finished; consult errors.\n")
