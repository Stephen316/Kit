"""Read/set componentColor only in a fresh import of an owned study archive."""
import hashlib
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

SOURCE = 'parameteridentity-8fc83529b236/01_literal.f3d'


def run(context):
    app = adsk.core.Application.get(); root = Path(__file__).resolve().parent
    output = root/('componentcolorcontrast-'+uuid.uuid4().hex[:12]); output.mkdir()
    report = {'fusion_version': app.version, 'source_archive': SOURCE,
              'source_sha256': hashlib.sha256((root/SOURCE).read_bytes()).hexdigest(),
              'scope': 'Actual root componentColor getters and one controlled setter in an owned new import; no global component-color display setting is changed',
              'requested_color': {'red': 17, 'green': 83, 'blue': 201, 'opacity': 255},
              'status': 'starting', 'errors': []}
    document = None
    def save():
        (output/'ground_truth.json').write_text(json.dumps(report, indent=2)+'\n')
    def color_truth(color):
        return {'red': color.red, 'green': color.green, 'blue': color.blue, 'opacity': color.opacity}
    save()
    try:
        report['status'] = 'importing'; save()
        document = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(root/SOURCE)))
        if document is None: raise RuntimeError('Owned archive import did not return a new document')
        design = adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))
        component = design.rootComponent
        report['actual_color_before'] = color_truth(component.componentColor)
        report['status'] = 'setting_owned_component_color'; save()
        component.componentColor = adsk.core.Color.create(17, 83, 201, 255)
        report['actual_color_after'] = color_truth(component.componentColor)
        report['computeAll_returned'] = design.computeAll()
        report['parameters_after'] = [{'name': p.name, 'expression': p.expression, 'value_cm': p.value,
                                       'dependency_names': [x.name for x in p.dependencyParameters]} for p in design.userParameters]
        filename = 'known_component_color.f3d'; target = output/filename
        report['status'] = 'exporting'; save()
        if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(target))):
            raise RuntimeError('Owned component-color export failed')
        report['file'] = filename; report['sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
        report['status'] = 'exported'
    except Exception:
        report['status'] = 'error'; report['errors'].append(traceback.format_exc())
    finally:
        if document is not None:
            try: report['close_owned_document_result'] = document.close(False)
            except Exception: report['errors'].append(traceback.format_exc()); report['status'] = 'error'
        save()
        (output/'complete.txt').write_text('Owned component color contrast finished; inspect status/errors.\n')
