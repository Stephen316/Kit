import json
import os
from pathlib import Path
import traceback

import adsk.core

out = Path(os.environ.get('KIT_MATERIAL_PROBE', str(Path(__file__).resolve().parent / 'LibraryProbe.json')))
app = adsk.core.Application.get()
report = {'fusion_version': app.version, 'libraries': []}


def plain(item):
    if item is None or type(item) in (str, bool, int, float):
        return item
    if isinstance(item, (list, tuple)):
        return [plain(child) for child in item]
    if isinstance(item, adsk.core.Color):
        return [item.red, item.green, item.blue, item.opacity]
    return item.objectType


def rows(items):
    result = []
    for item in items:
        row = {'id': item.id, 'name': item.name, 'type': item.objectType.split('::')[-1]}
        try:
            if getattr(item, 'hasMultipleValues', False):
                row['values'] = plain(item.values)
            elif hasattr(item, 'value'):
                row['value'] = plain(item.value)
            if hasattr(item, 'units'):
                row['units'] = item.units
            if hasattr(item, 'hasConnectedTexture'):
                row['texture'] = item.hasConnectedTexture
            if hasattr(item, 'choices'):
                row['choices'] = plain(item.choices)
        except Exception:
            row['error'] = traceback.format_exc().splitlines()[-1]
        result.append(row)
    return result


try:
    for library in app.materialLibraries:
        entry = {'name': library.name, 'native': library.isNative, 'materials': [], 'appearances': []}
        for material in library.materials:
            entry['materials'].append({'name': material.name, 'id': material.id, 'appearance': material.appearance.name if material.appearance else None, 'appearance_id': material.appearance.id if material.appearance else None, 'properties': rows(material.materialProperties)})
        for appearance in library.appearances:
            entry['appearances'].append({'name': appearance.name, 'id': appearance.id, 'properties': rows(appearance.appearanceProperties)})
        report['libraries'].append(entry)
    report['status'] = 'completed'
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
finally:
    out.write_text(json.dumps(report, indent=1) + '\n')
