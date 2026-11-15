import importlib
import json
import os
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
target = here / "Out" / "Designs" / ("Edit" + label + ".json")
report = {"fusion_version": app.version, "label": label, "stage": "starting"}
owned = []


def checkpoint(stage):
    report["stage"] = stage
    common.save_json(target, report)


def settle(seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        adsk.doEvents()


def run():
    project, _ = common.ensure_project()
    folder = project.rootFolder.dataFolders.add(
        "KitDesign " + time.strftime("%Y%m%d%H%M%S")
    )
    if folder is None:
        raise RuntimeError("could not create the upload folder")
    report["folder"] = folder.name
    checkpoint("uploading")
    future = folder.uploadFile(str(here / "Out" / "Designs" / plan["file"]))
    if future is None:
        raise RuntimeError("upload did not start")
    report["upload_state"] = int(future.uploadState)

    checkpoint("waiting for upload")
    deadline = time.monotonic() + 300
    uploaded = None
    while time.monotonic() < deadline:
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
            if common.safe(lambda item=item: item.isComplete)
            and common.safe(lambda item=item: item.fileExtension) == "f3d"
        ]
        if ready:
            uploaded = ready[0]
            break
        settle(3)
    if uploaded is None:
        raise RuntimeError("uploaded design never became complete")
    report["uploaded"] = {
        "name": common.safe(lambda: uploaded.name),
        "version": common.safe(lambda: uploaded.versionNumber),
        "read_only": common.safe(lambda: uploaded.isReadOnly),
    }

    checkpoint("opening design")
    document = app.documents.open(uploaded, True)
    owned.append(document)
    settle(12)
    design = adsk.fusion.Design.cast(
        document.products.itemByProductType("DesignProductType")
    )
    if design is None:
        raise RuntimeError("Fusion did not present a design product")

    parameter = design.userParameters.itemByName(plan["param"])
    bodies = design.rootComponent.bRepBodies
    volume = common.safe(lambda: bodies.item(0).volume)
    report["native"] = {
        "parameter": None
        if parameter is None
        else {
            "expression": common.safe(lambda: parameter.expression),
            "value_cm": common.safe(lambda: parameter.value),
        },
        "bodies": bodies.count,
        "volume_cm3": volume,
        "expected_cm3": plan["expected_volume_mm3"] / 1000.0,
        "features": design.rootComponent.features.count,
        "sketches": design.rootComponent.sketches.count,
    }
    if parameter is None:
        raise RuntimeError("authored parameter is missing in Fusion")
    if bodies.count != 1:
        raise RuntimeError("expected one authored body")
    if volume is None or abs(volume - plan["expected_volume_mm3"] / 1000.0) > 1e-6:
        raise RuntimeError("authored body volume does not match the spec")
    checkpoint("editing parameter")
    edited = 55.0
    parameter.expression = f"{edited} mm"
    settle(5)
    report["edit"] = {
        "requested_mm": edited,
        "expression": common.safe(lambda: parameter.expression),
    }
    if common.safe(lambda: parameter.expression) != f"{edited} mm":
        raise RuntimeError("Fusion did not apply the parameter edit")

    checkpoint("saving the design")
    name = common.TOKEN + " Saved " + label + " " + time.strftime("%H%M%S")
    report["save_as_started"] = common.safe(
        lambda: document.saveAs(name, folder, "Kit design acceptance", "")
    )
    deadline = time.monotonic() + int(os.environ.get("KIT_DESIGN_SAVE_SECONDS", "240"))
    saved = None
    while time.monotonic() < deadline:
        settle(2)
        try:
            files = [
                folder.dataFiles.item(index)
                for index in range(folder.dataFiles.count)
            ]
        except Exception:
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
        raise RuntimeError("the design save never produced a file")

    checkpoint("reopening the saved design")
    common.close_owned(owned, report)
    settle(6)
    reopened = app.documents.open(saved, True)
    owned.append(reopened)
    settle(12)
    design = adsk.fusion.Design.cast(
        reopened.products.itemByProductType("DesignProductType")
    )
    parameter = design.userParameters.itemByName(plan["param"])
    report["reopened"] = {
        "expression": common.safe(lambda: parameter.expression),
        "bodies": design.rootComponent.bRepBodies.count,
        "volume_cm3": common.safe(lambda: design.rootComponent.bRepBodies.item(0).volume),
        "expected_cm3": 3.141592653589793 * 12.5 * 12.5 * edited / 1000.0,
    }
    if report["reopened"]["expression"] != f"{edited} mm":
        raise RuntimeError("the edited parameter did not survive save and reopen")

    report["status"] = "accepted"


try:
    run()
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
finally:
    common.close_owned(owned, report)
    checkpoint("finished")
