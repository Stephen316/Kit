"""Read API topology evidence by importing only this study's owned archives."""

from collections import Counter
import json
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
    output = base/("breptruth-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    for source in ("holes-926347c1eaa8/simple.f3d", "tools-fda3948848f4/Fillet.f3d",
                   "splits-efce4ef164c9/multiple_bodies.f3d"):
        doc = None
        try:
            options = app.importManager.createFusionArchiveImportOptions(str(base/source))
            doc = app.importManager.importToNewDocument(options)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            sample = {"source": source, "evidence": "Completed geometry read after local archive import", "bodies": []}
            for body in design.rootComponent.bRepBodies:
                sample["bodies"].append({
                    "name": body.name, "revision_id": body.revisionId, "is_solid": body.isSolid,
                    "lump_count": body.lumps.count, "shell_count": body.shells.count,
                    "face_count": body.faces.count, "edge_count": body.edges.count, "vertex_count": body.vertices.count,
                    "bounding_box_cm": [body.boundingBox.minPoint.asArray(), body.boundingBox.maxPoint.asArray()],
                    "vertex_positions_cm": [v.geometry.asArray() for v in body.vertices],
                    "surface_types": dict(Counter(f.geometry.objectType.split("::")[-1] for f in body.faces)),
                    "surfaces": [surface_evidence(f.geometry) for f in body.faces],
                    "faces": [{"temp_id": f.tempId, "surface_type": f.geometry.objectType.split("::")[-1],
                               "edge_count": f.edges.count, "loop_count": f.loops.count} for f in body.faces],
                })
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"source": source, "error": traceback.format_exc()})
        finally:
            if doc:
                doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("BRep API inspection finished; consult errors.\n")
