"""Capture actual dependency getters for unary function expression syntax."""

from pathlib import Path
import json
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = {
    'sqrt_sum': ('sqrt(probeScale + 1)', ''),
    'abs_difference': ('abs(probeAllowance - probeWidth)', 'mm'),
    'nested_sqrt': ('sqrt(probeScale * sqrt(probeScale))', ''),
    'nested_unary_abs': ('-abs(-probeWidth) + 20 mm', 'mm'),
}


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/('parameterfunctions-'+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {'fusion_version': app.version, 'samples': [], 'errors': []}
    cases = context.get('cases', CASES) if isinstance(context, dict) else CASES
    value = adsk.core.ValueInput.createByString
    for case in cases:
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            parameters = design.userParameters
            parameters.add('probeWidth', value('7.3 mm'), 'mm', '')
            parameters.add('probeScale', value('2.5'), '', '')
            parameters.add('probeAllowance', value('1.2 mm'), 'mm', '')
            expression, unit = CASES[case]
            parameters.add('probeResult', value(expression), unit, '')
            if not design.computeAll():
                raise RuntimeError('Expression computation failed')
            actual = []
            for parameter in parameters:
                actual.append({'name': parameter.name, 'unit': parameter.unit,
                               'expression': parameter.expression, 'value': parameter.value,
                               'dependency_names': [p.name for p in parameter.dependencyParameters],
                               'dependent_names': [p.name for p in parameter.dependentParameters]})
            design.timeline.moveToEnd()
            sample = {'file': case+'.f3d', 'requested_expression': expression, 'parameters': actual}
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample['file']))):
                raise RuntimeError('Function expression export failed')
            truth['samples'].append(sample)
        except Exception:
            truth['errors'].append({'case': case, 'error': traceback.format_exc()})
        finally:
            doc.close(False)
            (output/'ground_truth.json').write_text(json.dumps(truth, indent=2)+'\n')
    (output/'complete.txt').write_text('Parameter function capture finished; consult errors.\n')
