"""Generate a local assembly with nested and repeated component instances."""

import json
import math
from pathlib import Path
import runpy
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent / ("assembly-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "components": [], "occurrences": [], "errors": []}
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    point, vector = adsk.core.Point3D.create, adsk.core.Vector3D.create
    try:
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent

        def matrix(translation, axis, angle):
            result = adsk.core.Matrix3D.create()
            result.setToRotation(math.radians(angle), vector(*axis), point(0, 0, 0))
            result.translation = vector(*translation)
            return result

        def model(component, label, plane, center, radius, depth):
            sketch = component.sketches.add(plane)
            sketch.name = label+"Profile"
            sketch.sketchCurves.sketchCircles.addByCenterRadius(point(*center), radius)
            feature = component.features.extrudeFeatures.addSimple(sketch.profiles.item(0),
                adsk.core.ValueInput.createByString(depth), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            feature.name = label+"Extrusion"
            truth["components"].append({"name": component.name, "sketch_name": sketch.name,
                                         "feature_name": feature.name, "sketch_local_probe_cm": center,
                                         "sketch_transform": sketch.transform.asArray(), "body_count": component.bRepBodies.count})

        first = root.occurrences.addNewComponent(matrix([10, 2, -1], [0, 0, 1], 30))
        comp_a = first.component
        comp_a.name = "ComponentA"
        model(comp_a, "A", comp_a.xYConstructionPlane, [0.7, 1.2, 0], 0.4, "12 mm")
        nested = comp_a.occurrences.addNewComponent(matrix([1, 5, 0.7], [1, 0, 0], 20))
        comp_b = nested.component
        comp_b.name = "ComponentB"
        model(comp_b, "B", comp_b.xYConstructionPlane, [-0.8, 0.5, 0], 0.3, "8 mm")
        root.occurrences.addExistingComponent(comp_a, matrix([-6, 3, 2], [0, 0, 1], -15))
        third = root.occurrences.addNewComponent(matrix([0, -4, 3], [0, 1, 0], 35))
        comp_c = third.component
        comp_c.name = "ComponentC"
        model(comp_c, "C", comp_c.yZConstructionPlane, [2, 1, 0], 0.5, "10 mm")
        design.computeAll()
        local_probes = {c["name"]: c["sketch_local_probe_cm"] for c in truth["components"]}
        for occurrence in root.allOccurrences:
            native = occurrence.nativeObject or occurrence
            sketch = occurrence.component.sketches.item(0)
            proxy = sketch.createForAssemblyContext(occurrence)
            truth["occurrences"].append({
                "name": occurrence.name, "path": occurrence.fullPathName, "component_name": occurrence.component.name,
                "transform2": occurrence.transform2.asArray(), "native_transform2": native.transform2.asArray(),
                "sketch_probe_world_cm": proxy.sketchToModelSpace(point(*local_probes[occurrence.component.name])).asArray(),
            })
        helper = runpy.run_path(str(Path(__file__).with_name("GenerateTimelineSamples.py")))
        truth["timeline"] = [helper["timeline_item"](design.timeline.item(i)) for i in range(design.timeline.count)]
        options = design.exportManager.createFusionArchiveExportOptions(str(output / "assembly.f3d"))
        if not design.exportManager.execute(options):
            raise RuntimeError("Assembly export failed")
    except Exception:
        truth["errors"].append(traceback.format_exc())
    finally:
        doc.close(False)
        (output / "ground_truth.json").write_text(json.dumps(truth, indent=2))
        (output / "complete.txt").write_text("Assembly export finished; consult errors.\n")
