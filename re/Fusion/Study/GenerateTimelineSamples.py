"""Export one owned design through controlled timeline state changes."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def timeline_item(item):
    result = {"name": item.name}
    for native, name in (("index", "index"), ("isSuppressed", "is_suppressed"),
                         ("isRolledBack", "is_rolled_back"), ("isGroup", "is_group")):
        try:
            result[name] = getattr(item, native)
        except RuntimeError as error:
            result[name] = None
            result.setdefault("unavailable_api_properties", {})[name] = str(error)
    if item.entity:
        result["entity_kind"] = item.entity.objectType.split("::")[-1]
    if item.isGroup:
        result["is_collapsed"] = item.isCollapsed
        result["children"] = [timeline_item(item.item(i)) for i in range(item.count)]
    return result


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("timeline-" + uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    try:
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        items = []
        for index, label in enumerate("ABC"):
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.name = "Profile"+label
            sketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(index*4, 0, 0), 1.)
            feature = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0),
                adsk.core.ValueInput.createByString(str((index+1)*10)+" mm"),
                adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            feature.name = "Extrusion"+label
            items.extend([sketch, feature])

        def export(case):
            sample = {"file": case+".f3d", "marker_position": design.timeline.markerPosition,
                      "timeline_count": design.timeline.count, "body_count": root.bRepBodies.count,
                      "timeline": [timeline_item(design.timeline.item(i)) for i in range(design.timeline.count)],
                      "created_entities": [timeline_item(item.timelineObject) for item in items]}
            options = design.exportManager.createFusionArchiveExportOptions(str(output / sample["file"]))
            if not design.exportManager.execute(options):
                raise RuntimeError("Timeline export failed: "+case)
            truth["samples"].append(sample)
            (output / "ground_truth.json").write_text(json.dumps(truth, indent=2))

        export("baseline")
        items[3].timelineObject.isSuppressed = True
        export("suppressed_b")
        items[3].timelineObject.isSuppressed = False
        if not items[3].timelineObject.reorder(items[5].timelineObject.index):
            raise RuntimeError("Independent feature B could not move before feature C")
        design.timeline.moveToEnd()
        export("reordered_b")
        group = design.timeline.timelineGroups.add(2, 3)
        group.name = "ProfileGroup"
        group.isCollapsed = True
        export("grouped")
        design.timeline.markerPosition = 2
        export("rolled_back")
    except Exception:
        truth["errors"].append(traceback.format_exc())
    finally:
        doc.close(False)
        (output / "ground_truth.json").write_text(json.dumps(truth, indent=2))
        (output / "complete.txt").write_text("Timeline export finished; consult errors.\n")
