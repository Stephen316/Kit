# List the drawing API members that matter for rule captures and say which properties are writable.
# The report goes to $TMPDIR/KitFusionDrawings/Rules/ProbeApi.json and stays out of the repository.
import importlib
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'Native'))
common = importlib.reload(importlib.import_module('DrawingCommon'))

import adsk.drawing

app = common.app
out = common.SCRATCH / 'Rules'
report = {'fusion_version': app.version, 'classes': {}}
NAMES = ['DocumentSettings', 'DrawingStandardsSettings', 'SheetInput', 'Views', 'View', 'ViewParameters', 'DWGExportOptions', 'DrawingExportOptions', 'CreateDrawingInput', 'ViewSettings', 'SheetBorder', 'TitleBlock', 'TitleBlocks', 'CustomSheetSize']
ENUMS = ['SheetCreationTypes', 'SheetOrientationTypes', 'ProjectionAngleTypes', 'ViewTypes', 'DWGFormats', 'SheetSizes', 'DrawingStandardTypes', 'TitleBlockSourceTypes']


def members(kind):
    rows = {}
    for name in dir(kind):
        if name.startswith('_') or name in ('this', 'thisown'):
            continue
        value = getattr(kind, name, None)
        if isinstance(value, property):
            rows[name] = 'property rw' if value.fset is not None else 'property ro'
        elif callable(value):
            rows[name] = 'method'
    return rows


try:
    for name in NAMES:
        kind = getattr(adsk.drawing, name, None)
        report['classes'][name] = members(kind) if kind is not None else None
    report['enums'] = {name: {key: int(getattr(getattr(adsk.drawing, name), key)) for key in dir(getattr(adsk.drawing, name)) if not key.startswith('_') and isinstance(getattr(getattr(adsk.drawing, name), key), int)} for name in ENUMS}
    report['module'] = sorted(name for name in dir(adsk.drawing) if not name.startswith('_'))
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    common.save_json(out / 'ProbeApi.json', report)
