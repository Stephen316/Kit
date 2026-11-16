import importlib
import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
common = importlib.reload(importlib.import_module("DrawingCommon"))

import adsk.core
import adsk.fusion

app = common.app
here = Path(__file__).resolve().parent
plan = json.loads((here / "Out" / "Designs" / "DesignPlan.json").read_text())
label = plan["label"]
target = here / "Out" / "Designs" / ("Export" + label + ".json")
exported = here / "Out" / "Designs" / ("FusionExport" + label + ".f3d")
report = {"fusion_version": app.version, "label": label, "stage": "starting"}
owned = []


def checkpoint(stage):
    report["stage"] = stage
    common.save_json(target, report)


def settle(seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        adsk.doEvents()


def describe(document):
    design = adsk.fusion.Design.cast(
        document.products.itemByProductType("DesignProductType")
    )
    if design is None:
        raise RuntimeError("Fusion did not present a design product")
    parameter = design.allParameters.itemByName(plan["param"])
    bodies = design.rootComponent.bRepBodies
    return {
        "expression": common.safe(lambda: parameter.expression),
        "bodies": bodies.count,
        "volume_cm3": common.safe(lambda: bodies.item(0).volume),
    }


def run():
    source = here / "Out" / "Designs" / plan["file"]
    checkpoint("importing")
    options = app.importManager.createFusionArchiveImportOptions(str(source))
    if options is None:
        raise RuntimeError("import options were not created")
    document = app.importManager.importToNewDocument(options)
    if document is None:
        raise RuntimeError("import did not produce a document")
    owned.append(document)
    settle(20)
    report["imported"] = describe(document)

    checkpoint("exporting")
    if exported.exists():
        exported.unlink()
    design = adsk.fusion.Design.cast(
        document.products.itemByProductType("DesignProductType")
    )
    if design is None:
        raise RuntimeError("Fusion did not present a design product")
    export_options = design.exportManager.createFusionArchiveExportOptions(
        str(exported)
    )
    if export_options is None:
        raise RuntimeError("export options were not created")
    report["export_started"] = common.safe(
        lambda: design.exportManager.execute(export_options)
    )
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        settle(2)
        if exported.exists() and exported.stat().st_size > 0:
            break
    if not exported.exists():
        raise RuntimeError("Fusion did not write the exported archive")
    report["exported_bytes"] = exported.stat().st_size
    report["exported_path"] = str(exported)

    checkpoint("reopening the export")
    common.close_owned(owned, report)
    settle(6)
    reopen_options = app.importManager.createFusionArchiveImportOptions(
        str(exported)
    )
    if reopen_options is None:
        raise RuntimeError("reopen options were not created")
    reopened = app.importManager.importToNewDocument(reopen_options)
    if reopened is None:
        raise RuntimeError("the export did not reopen")
    owned.append(reopened)
    settle(20)
    report["reopened"] = describe(reopened)

    before = report["imported"]
    after = report["reopened"]
    if after["expression"] != before["expression"]:
        raise RuntimeError("the parameter did not survive the export")
    if after["bodies"] != before["bodies"]:
        raise RuntimeError("the body count did not survive the export")
    if after["volume_cm3"] != before["volume_cm3"]:
        raise RuntimeError("the body volume did not survive the export")
    report["status"] = "accepted"


try:
    run()
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
finally:
    common.close_owned(owned, report)
    checkpoint("finished")
