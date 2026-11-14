import json
from pathlib import Path
import traceback

import adsk.core


output = Path(__file__).resolve().parent / "Bundles"
output.mkdir(exist_ok=True)
app = adsk.core.Application.get()
report = {
    "operation": "read_only_bundle_upload_destination_inventory",
    "cloud_mutations": [],
    "document_mutations": [],
    "hubs": [],
}


def describe_project(project):
    folder = project.rootFolder
    return {"id": project.id, "name": project.name,
            "root_folder": {"id": folder.id, "name": folder.name} if folder else None}


try:
    report["fusion_version"] = app.version
    report["is_offline"] = app.isOffLine
    report["documents_before"] = app.documents.count
    data = app.data
    active_hub = data.activeHub
    active_project = None
    try:
        active_project = data.activeProject
    except RuntimeError as error:
        report["active_project_error"] = {"type": type(error).__name__, "message": str(error)}
    report["active_hub_id"] = active_hub.id if active_hub else None
    report["active_project_id"] = active_project.id if active_project else None
    report["api"] = {
        "uploadFile_present": callable(getattr(adsk.core.DataFolder, "uploadFile", None)),
        "project_add_present": callable(getattr(adsk.core.DataProjects, "add", None)),
        "uploadFile_contract": adsk.core.DataFolder.uploadFile.__doc__,
        "project_add_contract": adsk.core.DataProjects.add.__doc__,
        "future_state_contract": adsk.core.DataFileFuture.uploadState.__doc__,
        "future_result_contract": adsk.core.DataFileFuture.dataFile.__doc__,
    }
    hubs = data.dataHubs
    report["hub_count"] = hubs.count
    if hubs.count > 100:
        raise RuntimeError("Hub inventory exceeds bounded read-only scope")
    for index in range(hubs.count):
        hub = hubs.item(index)
        projects = hub.dataProjects
        entry = {"id": hub.id, "name": hub.name, "hub_type": int(hub.hubType),
                 "is_active": active_hub is not None and hub.id == active_hub.id,
                 "project_count": projects.count, "projects": []}
        report["hubs"].append(entry)
        if projects.count > 1000:
            raise RuntimeError("Project inventory exceeds bounded read-only scope")
        entry["projects"] = [describe_project(projects.item(position))
                             for position in range(projects.count)]
    report["status"] = "inspected"
except Exception:
    report["status"] = "failed"
    report["traceback"] = traceback.format_exc()
    raise
finally:
    report["documents_after"] = app.documents.count
    (output / "ProjectInventory.json").write_text(json.dumps(report, indent=2) + "\n")
