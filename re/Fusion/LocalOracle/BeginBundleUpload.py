import builtins
import hashlib
import json
from pathlib import Path
import traceback
import types

import adsk.core

root = Path(__file__).resolve().parent / 'Bundles'
source = root / 'kit_production_example1.f3z'
app = adsk.core.Application.get()
report = {'fusion_version': app.version, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'scope': 'Production reconstruction of the F3Z JSON and ZIP envelope; its nine complete source document members are preserved', 'stage': 'starting'}
try:
    if report['source_sha256'] != '33a42876f25ecc72844cf37af3ab35cb17ed6bfe621ff4e21ce4b3a62c6afe54':
        raise RuntimeError('Acceptance artifact changed')
    inventory = json.loads((root / 'ProjectInventory.json').read_text())
    hub = app.data.activeHub
    if hub is None or hub.id != inventory['active_hub_id'] or app.isOffLine:
        raise RuntimeError('Selected online acceptance hub is unavailable')
    name = 'Kit Fusion Codec Acceptance 2026-11-12 33a42876'
    if any(hub.dataProjects.item(i).name == name for i in range(hub.dataProjects.count)):
        raise RuntimeError('Acceptance project already exists; refusing duplicate upload')
    project = hub.dataProjects.add(name, 'Native acceptance of independently reconstructed Kit Fusion bundle envelope', '')
    if project is None:
        raise RuntimeError('Could not create isolated acceptance project')
    report['project_name'] = name
    report['stage'] = 'project_created'
    (root / 'UploadStatus.json').write_text(json.dumps(report, indent=2) + '\n')
    future = project.rootFolder.uploadFile(str(source))
    if future is None:
        raise RuntimeError('Upload did not return a future')
    builtins._kit_bundle_acceptance = types.SimpleNamespace(future=future, project=project, report=report, data_file=None)
    report['stage'] = 'upload_started'
    report['upload_state'] = int(future.uploadState)
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
    raise
finally:
    (root / 'UploadStatus.json').write_text(json.dumps(report, indent=2) + '\n')
