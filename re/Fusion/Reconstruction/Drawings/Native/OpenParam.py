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
plan = json.loads((here / "Out" / "Designs" / "ParamPlan.json").read_text())
label = plan["label"]
target = here / "Out" / "Designs" / ("Param" + label + ".json")
report = {"fusion_version": app.version, "label": label, "stage": "starting"}
owned = []


def checkpoint(stage):
    report["stage"] = stage
    common.save_json(target, report)


def settle(seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        adsk.doEvents()


def open_file(folder, name):
    deadline = time.monotonic() + 300
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
            if common.safe(lambda item=item: item.name) == name
            and common.safe(lambda item=item: item.isComplete)
        ]
        if ready:
            return ready[0]
        settle(3)
    raise RuntimeError("uploaded design never became complete: " + name)


def describe(document):
    report["products"] = [
        common.safe(lambda index=index: document.products.item(index).productType)
        for index in range(common.safe(lambda: document.products.count) or 0)
    ]
    design = adsk.fusion.Design.cast(
        document.products.itemByProductType("DesignProductType")
    )
    if design is None:
        raise RuntimeError("Fusion did not present a design product")
    parameters = {}
    for index in range(design.allParameters.count):
        item = design.allParameters.item(index)
        parameters[common.safe(lambda item=item: item.name)] = {
            "expression": common.safe(lambda item=item: item.expression),
            "value_cm": common.safe(lambda item=item: item.value),
        }
    root = design.rootComponent
    bodies = root.bRepBodies
    volumes = []
    for index in range(bodies.count):
        volumes.append(common.safe(lambda index=index: bodies.item(index).volume))
    for index in range(root.allOccurrences.count):
        occurrence = root.allOccurrences.item(index)
        child = occurrence.bRepBodies
        for inner in range(child.count):
            volumes.append(common.safe(lambda inner=inner, child=child: child.item(inner).volume))
    return {
        "parameters": parameters,
        "bodies": len(volumes),
        "volumes_cm3": volumes,
        "features": root.features.count,
    }


def run():
    project, _ = common.ensure_project()
    folder = project.rootFolder.dataFolders.add(
        "KitParam " + time.strftime("%Y%m%d%H%M%S")
    )
    if folder is None:
        raise RuntimeError("could not create the upload folder")
    report["folder"] = folder.name
    for role, name in (("control", plan["control"]), ("edited", plan["file"])):
        checkpoint("uploading " + role)
        if folder.uploadFile(str(here / "Out" / "Designs" / name)) is None:
            raise RuntimeError("upload did not start for " + role)
        uploaded = open_file(folder, Path(name).stem)
        checkpoint("opening " + role)
        document = app.documents.open(uploaded, True)
        owned.append(document)
        settle(30)
        report[role] = describe(document)
        if role == "edited":
            design = adsk.fusion.Design.cast(
                document.products.itemByProductType("DesignProductType")
            )
            report["recompute"] = common.safe(lambda: design.computeAll())
            settle(20)
            report["after_recompute"] = describe(document)
        common.close_owned(owned, report)
        settle(6)
    expected = plan["after_formula"]
    observed = report["edited"]["parameters"].get(plan["param"], {}).get("expression")
    report["expected_expression"] = expected
    report["observed_expression"] = observed
    if observed != expected:
        raise RuntimeError("Fusion did not report the edited parameter")
    after = report.get("after_recompute") or report["edited"]
    if report["control"]["bodies"] and (
        after["volumes_cm3"] == report["control"]["volumes_cm3"]
    ):
        raise RuntimeError("the body volume did not change with the parameter")
    report["status"] = "accepted"


try:
    run()
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
finally:
    common.close_owned(owned, report)
    checkpoint("finished")
