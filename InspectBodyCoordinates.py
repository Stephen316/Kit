"""API evidence for baked moved/scaled vertices and occurrence proxy coordinates."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


def run(context):
    app = adsk.core.Application.get()
    base = Path(__file__).resolve().parent
    output = base/("bodycoords-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    sources = ("namedbodies-3c7c11fc2924/namedbodies.f3d", "moretools-88a2cd6cad0b/MoveTranslate.f3d",
               "moretools-88a2cd6cad0b/MoveRotate.f3d", "bodymodes-df9b7113539f/scale_uniform.f3d",
               "bodymodes-df9b7113539f/scale_nonuniform.f3d")
    for source in sources:
        doc = None
        try:
            options = app.importManager.createFusionArchiveImportOptions(str(base/source))
            doc = app.importManager.importToNewDocument(options)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
            root = design.rootComponent
            sample = {"source": source, "placements": []}
            for body in root.bRepBodies:
                sample["placements"].append({"path": "", "name": body.name, "component_name": root.name,
                                             "world_vertex_positions_cm": [v.geometry.asArray() for v in body.vertices]})
            for occurrence in root.allOccurrences:
                for body in occurrence.bRepBodies:
                    sample["placements"].append({"path": occurrence.fullPathName, "name": body.name,
                                                 "component_name": occurrence.component.name,
                                                 "occurrence_transform": occurrence.transform2.asArray(),
                                                 "world_vertex_positions_cm": [v.geometry.asArray() for v in body.vertices]})
            truth["samples"].append(sample)
        except Exception:
            truth["errors"].append({"source": source, "error": traceback.format_exc()})
        finally:
            if doc:
                doc.close(False)
            (output/"ground_truth.json").write_text(json.dumps(truth, indent=2))
    (output/"complete.txt").write_text("Body coordinate evidence finished; consult errors.\n")
