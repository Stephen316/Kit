import importlib
import os
import json
import sys
import time
import traceback
from pathlib import Path

NATIVE = Path(__file__).resolve().parents[1] / "Native"
sys.path.insert(0, str(NATIVE))
common = importlib.reload(importlib.import_module("DrawingCommon"))

import adsk.core
import adsk.drawing

app = common.app
variants = common.SCRATCH / "Variants"
request = json.loads((variants / "Selection.json").read_text())
label = request["labels"][0]
target = variants / f"IndependentAcceptance{label}.json"
report = {
    "fusion_version": app.version,
    "label": label,
    "documents_before": app.documents.count,
    "stage": "starting",
}
owned = []


def checkpoint(stage):
    report["stage"] = stage
    common.save_json(target, report)


def settle(seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        adsk.doEvents()


def open_drawing():
    project, _ = common.ensure_project()
    parent = next(
        project.rootFolder.dataFolders.item(index)
        for index in range(project.rootFolder.dataFolders.count)
        if project.rootFolder.dataFolders.item(index).name == request["folder"]
    )
    child = next(
        parent.dataFolders.item(index)
        for index in range(parent.dataFolders.count)
        if parent.dataFolders.item(index).name == common.TOKEN + " " + label
    )
    files = [child.dataFiles.item(index) for index in range(child.dataFiles.count)]
    report["read_only"] = {
        item.fileExtension: common.safe(lambda: item.isReadOnly) for item in files
    }
    return (
        child,
        next(item for item in files if item.fileExtension == "f2d"),
        [item for item in files if item.fileExtension == "f3d"],
    )


def save_and_reopen(document, folder, original_file):
    name = common.TOKEN + " Saved " + label + " " + time.strftime("%Y%m%d%H%M%S")
    checkpoint("saving edited drawing as")
    if not document.saveAs(name, folder, "Kit independent drawing acceptance", ""):
        raise RuntimeError("saveAs did not start")
    last = {}

    def saved():
        last["error"] = None
        try:
            item = document.dataFile
        except Exception as error:
            last["error"] = str(error)
            report["save_wait"] = dict(last)
            return False
        last["data_file"] = None if item is None else common.safe(lambda: item.name)
        last["complete"] = None if item is None else common.safe(lambda: item.isComplete)
        last["modified"] = common.safe(lambda: document.isModified)
        report["save_wait"] = dict(last)
        if item is None:
            return False
        if last["data_file"] != name or not last["complete"] or last["modified"]:
            return False
        return item

    try:
        saved_file = common.wait_until(
            saved, int(os.environ.get("KIT_ACCEPT_SAVE_SECONDS", "900")), "edited drawing cloud save"
        )
    except RuntimeError:
        checkpoint("edited drawing cloud save stalled")
        raise
    report["saved"] = {
        "name": saved_file.name,
        "version": saved_file.versionNumber,
        "read_only": common.safe(lambda: saved_file.isReadOnly),
        "original_version": original_file.versionNumber,
    }
    common.close_owned(owned, report)
    checkpoint("reopening drawing")
    reopened = app.documents.open(saved_file, True)
    owned.append(reopened)
    settle(10)
    sheet = adsk.drawing.DrawingDocument.cast(reopened).drawing.activeSheet
    report["reopened"] = {
        "drawing": common.drawing_info(reopened),
        "first_scale": common.safe(lambda: sheet.views.item(0).scaleValue)
        if sheet.views.count
        else None,
        "modified": common.safe(lambda: reopened.isModified),
    }


def run():
    folder, drawing_file, design_files = open_drawing()
    for design_file in design_files:
        checkpoint("opening referenced design")
        owned.append(app.documents.open(design_file, True))
        settle(6)
    checkpoint("opening drawing")
    document = app.documents.open(drawing_file, True)
    owned.append(document)
    settle(10)
    drawing = adsk.drawing.DrawingDocument.cast(document).drawing
    sheet = drawing.activeSheet
    info = None
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        try:
            candidate = common.drawing_info(document)
            if candidate["sheets"] and candidate["sheets"][0]["views"]:
                info = candidate
                break
        except Exception as Failure:
            report["info_error"] = str(Failure)
        settle(5)
    if info is None:
        raise RuntimeError("Fusion did not expose the drawing views")
    report["opened"] = info
    if not sheet.views.count:
        raise RuntimeError("The acceptance case requires at least one view")
    before = sheet.views.item(0).scaleValue
    edited = before / 2
    checkpoint("editing view scale")
    sheet.views.item(0).scaleValue = edited
    settle(5)
    report["edited"] = {
        "before": before,
        "requested": edited,
        "observed": sheet.views.item(0).scaleValue,
        "drawing": common.drawing_info(document),
        "modified": document.isModified,
    }
    if sheet.views.item(0).scaleValue != edited or not document.isModified:
        raise RuntimeError("Fusion did not apply the native drawing edit")
    save_and_reopen(document, folder, drawing_file)
    first_scale = report["reopened"]["first_scale"]
    if first_scale != edited:
        raise RuntimeError("The edited view scale did not survive save and reopen")
    report["status"] = "accepted"


try:
    run()
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
finally:
    common.close_owned(owned, report)
    checkpoint("finished")
