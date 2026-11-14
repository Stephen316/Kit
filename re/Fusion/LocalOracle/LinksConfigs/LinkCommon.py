import hashlib
import json
from pathlib import Path
import time

import adsk.core
import adsk.fusion

here = Path(__file__).resolve().parent
private = here / 'tmp'
private.mkdir(exist_ok=True)
project_name = 'Kit Fusion Acceptance'
folder_name = 'Kit LinksConfigs'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def acceptance_folder(app, create=False, subfolder=None):
    hub = app.data.activeHub
    if hub is None or app.isOffLine:
        raise RuntimeError('Online active hub is unavailable')
    project = None
    for index in range(hub.dataProjects.count):
        item = hub.dataProjects.item(index)
        if item.name == project_name:
            project = item
            break
    if project is None:
        if not create:
            raise RuntimeError('Acceptance project is absent')
        project = hub.dataProjects.add(project_name, 'Kit Fusion native codec acceptance experiments', '')
        if project is None:
            raise RuntimeError('Acceptance project could not be created')
    folder = project.rootFolder.dataFolders.itemByName(folder_name)
    if folder is None:
        if not create:
            raise RuntimeError('Acceptance folder is absent')
        folder = project.rootFolder.dataFolders.add(folder_name)
    if subfolder is not None:
        child = folder.dataFolders.itemByName(subfolder)
        if child is None:
            child = folder.dataFolders.add(subfolder)
        folder = child
    return project, folder


def pump(predicate, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return True
        adsk.doEvents()
    return predicate()


def design_of(doc):
    return adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))


def export_f3d(design, target):
    target = Path(target)
    if target.exists():
        target.unlink()
    options = design.exportManager.createFusionArchiveExportOptions(str(target))
    if not design.exportManager.execute(options):
        raise RuntimeError('Fusion archive export failed: ' + target.name)
    produced = [item for item in target.parent.glob(target.stem + '.*') if item.suffix in ('.f3d', '.f3z')]
    return [{'file': item.name, 'bytes': item.stat().st_size, 'sha256': digest(item)} for item in produced]


def matrix(rotation_deg=0.0, axis=(0, 0, 1), translation=(0.0, 0.0, 0.0)):
    value = adsk.core.Matrix3D.create()
    if rotation_deg:
        value.setToRotation(rotation_deg * 3.141592653589793 / 180.0, adsk.core.Vector3D.create(*axis), adsk.core.Point3D.create(0, 0, 0))
    value.translation = adsk.core.Vector3D.create(*translation)
    return value


def write(path, report):
    Path(path).write_text(json.dumps(report, indent=2, default=str) + '\n')
