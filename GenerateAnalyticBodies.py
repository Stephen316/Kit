"""Revolved sphere, torus and cone with API surface evidence."""

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
    base = Path(__file__).resolve().parent
    surface_evidence = runpy.run_path(str(base/"CaptureSurfaceEvidence.py"))["surface_evidence"]
    output = base/("analytic-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "bodies": [], "errors": []}
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
    try:
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        for case in ("Sphere", "Torus", "Cone"):
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.name = case+"Profile"
            if case == "Sphere":
                arc = sketch.sketchCurves.sketchArcs.addByCenterStartSweep(point(0, 0, 0), point(0, 2, 0), math.pi)
                sketch.sketchCurves.sketchLines.addByTwoPoints(arc.endSketchPoint, arc.startSketchPoint)
            elif case == "Torus":
                sketch.sketchCurves.sketchCircles.addByCenterRadius(point(4, 0, 0), .75)
            else:
                lines = sketch.sketchCurves.sketchLines
                a = lines.addByTwoPoints(point(0, 0, 0), point(2, 0, 0))
                b = lines.addByTwoPoints(a.endSketchPoint, point(0, 3, 0))
                lines.addByTwoPoints(b.endSketchPoint, a.startSketchPoint)
            inputs = root.features.revolveFeatures.createInput(sketch.profiles.item(0), root.yConstructionAxis,
                                                               adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            inputs.setAngleExtent(False, value("360 deg"))
            feature = root.features.revolveFeatures.add(inputs)
            feature.name = case+"Revolve"
            body = feature.bodies.item(0)
            body.name = case
            truth["bodies"].append({"name": body.name, "face_count": body.faces.count,
                                    "edge_count": body.edges.count, "vertex_count": body.vertices.count,
                                    "vertex_positions_cm": [v.geometry.asArray() for v in body.vertices],
                                    "surfaces": [surface_evidence(f.geometry) for f in body.faces]})
        options = design.exportManager.createFusionArchiveExportOptions(str(output/"analytic.f3d"))
        if not design.exportManager.execute(options):
            raise RuntimeError("Analytic body export failed")
    except Exception:
        truth["errors"].append(traceback.format_exc())
    finally:
        doc.close(False)
        (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
        (output/"complete.txt").write_text("Analytic body export finished; consult errors.\n")
