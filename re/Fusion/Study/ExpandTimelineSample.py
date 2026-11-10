"""Import an owned local reference archive and vary only its group expansion."""

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
    output = base / ("timeline-expanded-"+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {"fusion_version": app.version, "samples": [], "errors": []}
    doc = None
    try:
        helpers = runpy.run_path(str(base / "GenerateTimelineSamples.py"))
        source = base / "timeline-5867579925b5/grouped.f3d"
        options = app.importManager.createFusionArchiveImportOptions(str(source))
        doc = app.importManager.importToNewDocument(options)
        design = adsk.fusion.Design.cast(doc.products.itemByProductType("DesignProductType"))
        group = design.timeline.timelineGroups.item(0)
        group.isCollapsed = False
        design.timeline.moveToEnd()
        truth["source"] = str(source)
        sample = {"file": "expanded.f3d", "group_name": group.name, "group_is_collapsed": group.isCollapsed,
                  "marker_position": design.timeline.markerPosition, "timeline_count": design.timeline.count,
                  "timeline": [helpers["timeline_item"](design.timeline.item(i)) for i in range(design.timeline.count)]}
        options = design.exportManager.createFusionArchiveExportOptions(str(output / sample["file"]))
        if not design.exportManager.execute(options):
            raise RuntimeError("Expanded timeline export failed")
        truth["samples"].append(sample)
    except Exception:
        truth["errors"].append(traceback.format_exc())
    finally:
        if doc:
            doc.close(False)
        (output / "ground_truth.json").write_text(json.dumps(truth, indent=2))
        (output / "complete.txt").write_text("Expanded timeline export finished; consult errors.\n")
