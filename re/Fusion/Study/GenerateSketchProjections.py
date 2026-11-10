"""Capture study-owned sketch projection/inclusion links and detached controls."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ("linked_line", "unlinked_line", "broken_line", "linked_circle", "linked_point", "included_line", "body_edge")


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("sketchprojections-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString

    def entity_summary(entity):
        result = {"type": entity.objectType, "is_reference": entity.isReference, "is_2d": entity.is2D,
                  "is_fixed": entity.isFixed}
        reference = entity.referencedEntity if entity.isReference else None
        result["referenced_type"] = reference.objectType if reference else None
        parent = getattr(reference, "parentSketch", None) if reference else None
        result["referenced_sketch_name"] = parent.name if parent else None
        line, circle, vertex = (adsk.fusion.SketchLine.cast(entity), adsk.fusion.SketchCircle.cast(entity),
                                adsk.fusion.SketchPoint.cast(entity))
        if line:
            result.update(start_world_cm=line.startSketchPoint.worldGeometry.asArray(),
                          end_world_cm=line.endSketchPoint.worldGeometry.asArray())
        elif circle:
            result.update(center_world_cm=circle.centerSketchPoint.worldGeometry.asArray(), radius_cm=circle.radius)
        elif vertex:
            result["position_world_cm"] = vertex.worldGeometry.asArray()
        return result

    cases = context.get("cases", CASES) if isinstance(context, dict) else CASES
    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            if case == "body_edge":
                seed = root.sketches.add(root.xYConstructionPlane)
                seed.name = "SeedSection"
                seed.sketchCurves.sketchLines.addTwoPointRectangle(point(-1, -1, 0), point(1, 1, 0))
                extrude = root.features.extrudeFeatures.addSimple(seed.profiles.item(0), value("20 mm"),
                           adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                source = extrude.endFaces.item(0).edges.item(0)
            else:
                plane_input = root.constructionPlanes.createInput()
                plane_input.setByOffset(root.xYConstructionPlane, value("10 mm"))
                source_sketch = root.sketches.add(root.constructionPlanes.add(plane_input))
                source_sketch.name = "ProjectionSource"
                if case == "linked_circle":
                    source = source_sketch.sketchCurves.sketchCircles.addByCenterRadius(point(.8, 1.2, 0), .6)
                elif case == "linked_point":
                    source = source_sketch.sketchPoints.add(point(.8, 1.2, 0))
                else:
                    source = source_sketch.sketchCurves.sketchLines.addByTwoPoints(point(.5, .7, 0), point(2., 1.3, 0))
            target = root.sketches.add(root.xYConstructionPlane)
            target.name = "ProjectionTarget"
            if case == "included_line":
                included = target.include(source)
                projected = [included.item(i) for i in range(included.count)]
            else:
                projected = target.project2([source], case != "unlinked_line")
            if case == "broken_line":
                for entity in projected:
                    entity.isReference = False
            sample = {"file": case+".f3d", "settings": {"source_type": source.objectType,
                      "source_sketch_name": getattr(getattr(source, "parentSketch", None), "name", None),
                      "target_sketch_name": target.name, "method": "include" if case == "included_line" else "project2",
                      "requested_is_linked": case not in ("unlinked_line", "broken_line"),
                      "broken_after_projection": case == "broken_line", "output_count": len(projected),
                      "outputs": [entity_summary(entity) for entity in projected]}}
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample["file"]))):
                raise RuntimeError("Sketch projection export failed")
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"case": case, "error": traceback.format_exc()})
        finally:
            doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Sketch projection generation finished; consult errors.\n")
