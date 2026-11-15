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
target = here / "Out" / "Designs" / ("Import" + label + ".json")
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
        "expected_cm3": plan["expected_volume_mm3"] / 1000.0,
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
    report["modified_after_import"] = common.safe(lambda: document.isModified)

    checkpoint("saving the imported design")
    name = common.TOKEN + " Imported " + label + " " + time.strftime("%H%M%S")
    project, _ = common.ensure_project()
    folder = project.rootFolder.dataFolders.add(
        "KitImport " + time.strftime("%Y%m%d%H%M%S")
    )
    if folder is None:
        raise RuntimeError("could not create the save folder")
    report["folder"] = folder.name
    report["save_as_started"] = common.safe(
        lambda: document.saveAs(name, folder, "Kit imported design", "")
    )
    deadline = time.monotonic() + 300
    saved = None
    while time.monotonic() < deadline:
        settle(2)
        try:
            files = [
                folder.dataFiles.item(index)
                for index in range(folder.dataFiles.count)
            ]
        except Exception as Failure:
            report["poll_error"] = str(Failure)
            files = []
        ready = [
            item
            for item in files
            if common.safe(lambda item=item: item.name) == name
            and common.safe(lambda item=item: item.isComplete)
        ]
        if ready:
            saved = ready[0]
            break
    report["saved"] = None if saved is None else {
        "name": common.safe(lambda: saved.name),
        "version": common.safe(lambda: saved.versionNumber),
    }
    if saved is None:
        raise RuntimeError("the imported design never saved")

    checkpoint("reopening the saved design")
    common.close_owned(owned, report)
    settle(6)
    reopened = app.documents.open(saved, True)
    owned.append(reopened)
    settle(15)
    report["reopened"] = describe(reopened)
    if report["reopened"]["expression"] != report["imported"]["expression"]:
        raise RuntimeError("the parameter did not survive save and reopen")
    report["status"] = "accepted"


try:
    run()
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
finally:
    common.close_owned(owned, report)
    checkpoint("finished")
