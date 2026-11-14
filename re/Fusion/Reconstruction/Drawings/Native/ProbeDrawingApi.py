import json
import os
import tempfile
import traceback
from pathlib import Path

import adsk.core

out = Path(os.environ.get('KIT_DRAWING_OUT') or Path(tempfile.gettempdir()) / 'KitFusionDrawings') / 'Probe'
out.mkdir(parents=True, exist_ok=True)
app = adsk.core.Application.get()
report = {'fusion_version': app.version, 'documents_before': app.documents.count, 'offline': app.isOffLine}


def run():
    for name, command in (('list', 'TextCommands.List'), ('hidden', 'TextCommands.List /hidden')):
        try:
            text = app.executeTextCommand(command)
            (out / f'TextCommands.{name}.txt').write_text(text)
            report[f'text_{name}_chars'] = len(text)
        except Exception:
            report[f'text_{name}_error'] = traceback.format_exc()
    hub = app.data.activeHub
    report['hub_available'] = hub is not None
    if hub is not None:
        names = [hub.dataProjects.item(i).name for i in range(hub.dataProjects.count)]
        report['acceptance_project_exists'] = 'Kit Fusion Acceptance' in names
        report['project_count'] = len(names)
    try:
        import adsk.drawing
        manager = adsk.drawing.DrawingManager.get()
        report['drawing_manager'] = manager is not None
    except Exception:
        report['drawing_manager_error'] = traceback.format_exc()


try:
    run()
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    report['documents_after'] = app.documents.count
    (out / 'Probe.json').write_text(json.dumps(report, indent=2) + '\n')
