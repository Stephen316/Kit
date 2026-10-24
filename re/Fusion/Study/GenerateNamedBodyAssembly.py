"""Interleaved root/component body creation, custom names and API ownership."""

from collections import Counter
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/("namedbodies-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "bodies": [], "errors": []}
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    try:
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        matrix = adsk.core.Matrix3D.create()
        matrix.translation = adsk.core.Vector3D.create(10, 0, 0)
        comp_a = root.occurrences.addNewComponent(matrix).component
        comp_a.name = "Module A"
        matrix = adsk.core.Matrix3D.create()
        matrix.translation = adsk.core.Vector3D.create(0, 12, 0)
        comp_b = root.occurrences.addNewComponent(matrix).component
        comp_b.name = "Module B"
        cases = ((root, "Root block", (1, 1, 4, 3), "16 mm"),
                 (comp_a, "Child bracket", (-1, 0, 1, 1), "10 mm"),
                 (root, "Guide pin Ø12", None, "24 mm"),
                 (comp_b, "Child spacer", (2, -2, 4, -1), "30 mm"))
        for component, name, rectangle, depth in cases:
            sketch = component.sketches.add(component.xYConstructionPlane)
            if rectangle:
                a, b, c, d = rectangle
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(a, b, 0), point(c, d, 0))
            else:
                sketch.sketchCurves.sketchCircles.addByCenterRadius(point(8, 2, 0), .6)
            feature = component.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value(depth),
                                                                 adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            body = feature.bodies.item(0)
            body.name = name
            truth["bodies"].append({"name": body.name, "component_name": component.name,
                                    "face_count": body.faces.count, "edge_count": body.edges.count,
                                    "vertex_count": body.vertices.count,
                                    "vertex_positions_cm": [v.geometry.asArray() for v in body.vertices],
                                    "surface_types": dict(Counter(f.geometry.objectType.split("::")[-1] for f in body.faces))})
        options = design.exportManager.createFusionArchiveExportOptions(str(output/"namedbodies.f3d"))
        if not design.exportManager.execute(options):
            raise RuntimeError("Named body export failed")
    except Exception:
        truth["errors"].append(traceback.format_exc())
    finally:
        doc.close(False)
        (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
        (output/"complete.txt").write_text("Named-body assembly export finished; consult errors.\n")
