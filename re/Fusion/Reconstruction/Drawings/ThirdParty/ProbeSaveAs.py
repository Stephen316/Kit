import importlib
import json
import os
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Native"))
common = importlib.reload(importlib.import_module("DrawingCommon"))

import adsk.core
import adsk.drawing

app = common.app
variants = common.SCRATCH / "Variants"
selection = json.loads((variants / "Selection.json").read_text())
labels = selection["labels"]
target = variants / ("ProbeSaveAs" + selection.get("tag", "Round") + ".json")
report = {"fusion_version": app.version, "labels": labels, "stage": "starting", "rows": {}}
owned = []


def checkpoint(stage):
    report["stage"] = stage
    common.save_json(target, report)


def settle(seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        adsk.doEvents()


def project_folders():
    project, _ = common.ensure_project()
    folders = project.rootFolder.dataFolders
    return [folders.item(index) for index in range(folders.count)]


def find_child(label):
    want = common.TOKEN + " " + label
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        for folder in project_folders():
            children = [
                folder.dataFolders.item(index)
                for index in range(folder.dataFolders.count)
            ]
            for child in children:
                if common.safe(lambda: child.name) == want:
                    return folder, child
        settle(3)
    raise RuntimeError("no upload folder for " + label)


def files_of(child):
    return [
        child.dataFiles.item(index) for index in range(child.dataFiles.count)
    ]


def find_file(folder, name):
    for candidate in folder.dataFiles:
        if common.safe(lambda: candidate.name) == name:
            return candidate
    for child in [
        folder.dataFolders.item(index)
        for index in range(folder.dataFolders.count)
    ]:
        for candidate in child.dataFiles:
            if common.safe(lambda: candidate.name) == name:
                return candidate
    return None


def read_scale(document):
    deadline = time.monotonic() + 150
    while time.monotonic() < deadline:
        try:
            sheet = common.drawing_info(document)["sheets"][0]
            if sheet["views"]:
                return {
                    "sheet": sheet["name"],
                    "views": len(sheet["views"]),
                    "scale": sheet["views"][0]["scale"],
                }
        except Exception as Failure:
            report["info_error"] = str(Failure)
        settle(5)
    return {"error": "views never appeared"}


def cycle(label):
    row = {"label": label}
    report["rows"][label] = row
    folder, child = find_child(label)
    row["folder"] = common.safe(lambda: child.name)
    files = files_of(child)
    row["read_only"] = {
        item.fileExtension: common.safe(lambda item=item: item.isReadOnly)
        for item in files
    }
    design_file = next(item for item in files if item.fileExtension == "f3d")
    drawing_file = next(item for item in files if item.fileExtension == "f2d")
    checkpoint("opening design " + label)
    owned.append(app.documents.open(design_file, True))
    settle(6)
    checkpoint("opening drawing " + label)
    document = app.documents.open(drawing_file, True)
    owned.append(document)
    settle(12)
    row["opened"] = read_scale(document)
    if "error" in row["opened"]:
        return row
    before = row["opened"]["scale"]
    checkpoint("editing " + label)
    sheet = adsk.drawing.DrawingDocument.cast(document).drawing.activeSheet
    sheet.views.item(0).scaleValue = before / 2
    settle(6)
    row["edited"] = {
        "before": before,
        "observed": common.safe(lambda: sheet.views.item(0).scaleValue),
        "modified": common.safe(lambda: document.isModified),
    }
    name = common.TOKEN + " Saved " + label + " " + time.strftime("%H%M%S")
    row["save_name"] = name
    checkpoint("saving " + label)
    row["save_as_started"] = common.safe(
        lambda: document.saveAs(name, folder, "Kit drawing acceptance", "")
    )
    row["save_as_error"] = common.safe(lambda: None)
    deadline = time.monotonic() + int(os.environ.get("KIT_SAVE_AS_SECONDS", "300"))
    saved_file = None
    while time.monotonic() < deadline:
        settle(2)
        candidate = find_file(folder, name)
        if candidate is not None and common.safe(lambda: candidate.isComplete):
            saved_file = candidate
            break
    row["saved_appeared"] = saved_file is not None
    if saved_file is None:
        return row
    row["saved"] = {
        "name": common.safe(lambda: saved_file.name),
        "version": common.safe(lambda: saved_file.versionNumber),
    }
    checkpoint("closing " + label)
    common.close_owned(owned, row)
    settle(6)
    checkpoint("reopening " + label)
    design_file = find_file(folder, design_file.name) or design_file
    owned.append(app.documents.open(design_file, True))
    settle(6)
    reopened = app.documents.open(saved_file, True)
    owned.append(reopened)
    settle(12)
    row["reopened"] = read_scale(reopened)
    row["survived"] = (
        row["reopened"].get("scale") == row["edited"]["observed"]
        if "scale" in row["reopened"]
        else False
    )
    common.close_owned(owned, row)
    settle(4)
    return row


def run():
    for label in labels:
        try:
            cycle(label)
        except Exception:
            report["rows"][label] = {"error": traceback.format_exc()}
    report["status"] = "done"


try:
    run()
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
finally:
    common.close_owned(owned, report)
    checkpoint("finished")
