import builtins
import json
from pathlib import Path
import traceback
import zipfile

import adsk.core
import adsk.fusion

root = Path(__file__).resolve().parent / 'Bundles'
state = builtins._kit_bundle_acceptance
app = adsk.core.Application.get()
original = app.activeDocument
doc = None
report = dict(state.report)
try:
    with zipfile.ZipFile(root / 'kit_production_example1.f3z') as archive:
        graph = json.loads(archive.read('DesignDescription.json'))['designDescription']['designGraphs'][0]
    expected = {item['displayName'] for item in graph['designObjects']}
    root_name = next(item['displayName'] for item in graph['designObjects'] if item['id'] in graph['rootIds'])
    files = state.project.rootFolder.dataFiles
    report['uploaded_documents'] = [{'name': files.item(i).name, 'complete': files.item(i).isComplete} for i in range(files.count)]
    if {entry['name'] for entry in report['uploaded_documents']} != expected or not all(entry['complete'] for entry in report['uploaded_documents']):
        raise RuntimeError('Uploaded document set is incomplete')
    state.root_file = next(files.item(i) for i in range(files.count) if files.item(i).name == root_name)
    children = state.root_file.childReferences
    report['root_name'] = root_name
    report['root_children'] = [children.item(i).name for i in range(children.count)]
    if set(report['root_children']) != expected - {root_name}:
        raise RuntimeError('Native root references differ from the bundle graph')
    report['stage'] = 'opening_root'
    (root / 'NativeBundleAcceptance.json').write_text(json.dumps(report, indent=2) + '\n')
    doc = app.documents.open(state.root_file, False)
    if doc is None:
        raise RuntimeError('Uploaded root did not open')
    design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    report['opened'] = {'timeline_count': design.timeline.count, 'root_occurrences': design.rootComponent.occurrences.count, 'all_occurrences': design.rootComponent.allOccurrences.count, 'components': design.allComponents.count, 'parameters': design.allParameters.count, 'body_count': sum(c.bRepBodies.count for c in design.allComponents), 'external_occurrences': [{'name': o.name, 'referenced_name': o.component.parentDesign.parentDocument.dataFile.name if o.component.parentDesign.parentDocument.dataFile else None} for o in design.rootComponent.occurrences if o.isReferencedComponent], 'unhealthy_features': [{'index': i.index, 'name': i.name, 'health': int(i.healthState), 'message': i.errorOrWarningMessage} for i in design.timeline if i.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState]}
    report['stage'] = 'opened_root'
    report['status'] = 'native_bundle_opened'
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
