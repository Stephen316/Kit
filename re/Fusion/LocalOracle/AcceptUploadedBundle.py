import builtins
import json
from math import isclose
from pathlib import Path
import time
import traceback

import adsk
import adsk.core
import adsk.fusion

root = Path(__file__).resolve().parent / 'Bundles'
state = builtins._kit_bundle_acceptance
app = adsk.core.Application.get()
original = app.activeDocument
doc = None
report = json.loads((root / 'NativeBundleAcceptance.json').read_text())


def checkpoint(stage):
    report['stage'] = stage
    (root / 'NativeBundleAcceptance.json').write_text(json.dumps(report, indent=2) + '\n')


def observe(design):
    return {'timeline_count': design.timeline.count, 'root_occurrences': design.rootComponent.occurrences.count, 'all_occurrences': design.rootComponent.allOccurrences.count, 'components': design.allComponents.count, 'parameters': design.allParameters.count, 'body_count': sum(c.bRepBodies.count for c in design.allComponents), 'warnings_or_errors': [{'index': item.index, 'name': item.name, 'health': int(item.healthState), 'message': item.errorOrWarningMessage} for item in design.timeline if item.healthState in (adsk.fusion.FeatureHealthStates.WarningFeatureHealthState, adsk.fusion.FeatureHealthStates.ErrorFeatureHealthState)]}


def require_contents(value):
    for key in ('timeline_count', 'root_occurrences', 'all_occurrences', 'components', 'body_count'):
        if value[key] != report['opened'][key]:
            raise RuntimeError('Native assembly contents changed: ' + key)
    if value['warnings_or_errors']:
        raise RuntimeError('Native assembly contains feature warnings or errors')


try:
    doc = app.documents.open(state.root_file, False)
    if doc is None:
        raise RuntimeError('Could not reopen uploaded root')
    design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    report['health_enum'] = {name: int(getattr(adsk.fusion.FeatureHealthStates, name)) for name in dir(adsk.fusion.FeatureHealthStates) if name.endswith('FeatureHealthState')}
    checkpoint('rebuilding')
    if not design.computeAll():
        raise RuntimeError('Assembly rebuild failed')
    report['rebuilt'] = observe(design)
    require_contents(report['rebuilt'])
    checkpoint('rebuilt')
    parameter = design.userParameters.add('kitBundleAcceptance', adsk.core.ValueInput.createByString('2 mm'), 'mm', 'Kit reconstructed F3Z envelope native acceptance')
    if parameter is None:
        raise RuntimeError('Native parameter creation failed')
    parameter.expression = '4 mm'
    if not design.computeAll() or not isclose(parameter.value, 0.4):
        raise RuntimeError('Native parameter edit failed')
    report['edited'] = observe(design)
    report['edited']['acceptance_parameter_cm'] = parameter.value
    require_contents(report['edited'])
    checkpoint('saving')
    if not doc.save('Kit F3Z codec native acceptance: rebuild and parameter edit'):
        raise RuntimeError('Cloud save did not start')
    deadline = time.monotonic() + 90
    while (doc.isModified or not doc.dataFile.isComplete) and time.monotonic() < deadline:
        adsk.doEvents()
        time.sleep(0.1)
    if doc.isModified or not doc.dataFile.isComplete:
        raise RuntimeError('Cloud save did not complete within acceptance deadline')
    saved_file = doc.dataFile
    report['saved_version'] = saved_file.versionNumber
    doc.close(False)
    doc = None
    checkpoint('reopening')
    doc = app.documents.open(saved_file, False)
    if doc is None:
        raise RuntimeError('Saved assembly did not reopen')
    design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    if not design.computeAll():
        raise RuntimeError('Saved assembly rebuild failed')
    parameter = design.userParameters.itemByName('kitBundleAcceptance')
    if parameter is None or not isclose(parameter.value, 0.4):
        raise RuntimeError('Saved parameter edit did not persist')
    report['reopened'] = observe(design)
    report['reopened']['acceptance_parameter_cm'] = parameter.value
    require_contents(report['reopened'])
    children = saved_file.childReferences
    report['reopened_children'] = [children.item(i).name for i in range(children.count)]
    if set(report['reopened_children']) != set(report['root_children']):
        raise RuntimeError('Saved assembly references changed')
    report['status'] = 'accepted'
    checkpoint('reopened')
except Exception:
    report['status'] = 'failed'
    report['traceback'] = traceback.format_exc()
    raise
finally:
    if doc is not None:
        doc.close(False)
    if original is not None and original.isValid:
        original.activate()
    report['documents_after'] = app.documents.count
    (root / 'NativeBundleAcceptance.json').write_text(json.dumps(report, indent=2) + '\n')
