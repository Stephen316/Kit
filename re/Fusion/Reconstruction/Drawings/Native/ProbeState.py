import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
common = importlib.reload(importlib.import_module("DrawingCommon"))

import adsk.core

app = common.app
report = {
    "fusion_version": app.version,
    "offline": app.isOffLine,
    "documents": app.documents.count,
}
hub = common.safe(lambda: app.data.activeHub)
report["hub"] = hub if isinstance(hub, dict) else common.safe(lambda: hub.name)
report["projects"] = common.safe(
    lambda: [hub.dataProjects.item(index).name for index in range(hub.dataProjects.count)][:5]
)
common.save_json(common.SCRATCH / "Variants" / "ProbeState.json", report)
print(report)
