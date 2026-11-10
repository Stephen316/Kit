"""Prepared same-document, equal-value native parameter identity contrasts.

Four local exports change only result.expression in one owned document. All
requested expressions have five characters and evaluate to10mm. Actual API
getters, failures and export progress are retained; native IDs require later
inspection of real exports. This file does not run until Fusion calls run().
"""

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


STAGES = (
    ('literal', '10 mm', ()),
    ('alpha_reference', 'alpha', ('alpha',)),
    ('bravo_reference', 'bravo', ('bravo',)),
    ('literal_return', '10 mm', ()),
)
PARAMETER_NAMES = ('alpha', 'bravo', 'result')
OUTPUT_PREFIX = 'parameteridentity-'


def run(context):
    app = adsk.core.Application.get()
    batch_id = uuid.uuid4().hex[:12]
    output = Path(__file__).resolve().parent / (OUTPUT_PREFIX + batch_id)
    output.mkdir()  # Fresh generated basename; never overwrite earlier captures.
    truth = {
        'batch_id': batch_id, 'fusion_version': app.version,
        'samples': [], 'errors': [], 'stage_plan': [
            {'case': case, 'expression': expression,
             'expected_dependency_names': list(dependencies),
             'requested_character_count': len(expression),
             'requested_utf16le_bytes': len(expression.encode('utf-16le')),
             'expected_internal_value_cm': 1.0}
            for case, expression, dependencies in STAGES],
        'execution_scope': 'One newly created owned parametric document; three user parameters created once; only result.expression changes between four independent local exports.',
        'identity_scope': 'Same API handles are retained without deletion, rename or recreation. Native object-ID equality is pending offline inspection of actual archives. Entity tokens are opaque evidence, not interpreted as native IDs.',
        'evidence_scope': 'API dependencies are actual getter results, not inferred from requested expressions. Expected controls and actual getter snapshots remain separate.',
    }
    doc, design, active_case = None, None, None
    terminal_status = 'failed'

    def persist():
        (output / 'ground_truth.json').write_text(json.dumps(truth, indent=2)+'\n')

    def journal(phase, case=None, **fields):
        event = {'time_utc': datetime.now(timezone.utc).isoformat(),
                 'batch_id': batch_id, 'phase': phase, 'case': case,
                 'completed_sample_count': len(truth['samples']),
                 'error_count': len(truth['errors']), **fields}
        with (output / 'journal.jsonl').open('a') as stream:
            stream.write(json.dumps(event)+'\n')
        (output / 'progress.json').write_text(json.dumps(event, indent=2)+'\n')
        persist()

    def observe(label, getter, errors):
        try:
            return getter()
        except Exception:
            errors.append({'getter': label, 'error': traceback.format_exc()})
            return None

    def parameter_truth(parameter):
        errors = []
        result = {'getter_errors': errors}
        for key, getter in (
            ('name', lambda: parameter.name),
            ('object_type', lambda: parameter.objectType),
            ('entity_token', lambda: parameter.entityToken),
            ('is_valid', lambda: parameter.isValid),
            ('expression', lambda: parameter.expression),
            ('unit', lambda: parameter.unit),
            ('value_type', lambda: int(parameter.valueType)),
            ('value_cm', lambda: parameter.value),
            ('dependency_names', lambda: [p.name for p in parameter.dependencyParameters]),
            ('dependent_names', lambda: [p.name for p in parameter.dependentParameters]),
        ):
            result[key] = observe(key, getter, errors)
        expression = result['expression']
        result['actual_expression_character_count'] = len(expression) if isinstance(expression, str) else None
        result['actual_expression_utf16le_bytes'] = len(expression.encode('utf-16le')) if isinstance(expression, str) else None
        return result

    journal('batch_begin', planned_sample_count=len(STAGES), output_directory=str(output))
    try:
        journal('document_create_begin')
        doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        journal('document_created')
        design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
        if design is None:
            raise RuntimeError('Owned document has no Fusion Design product')
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        parameters = design.userParameters
        handles = {}
        for name in PARAMETER_NAMES:
            parameter = parameters.add(name, adsk.core.ValueInput.createByString('10 mm'), 'mm', '')
            if parameter is None:
                raise RuntimeError('Parameter creation returned null: '+name)
            handles[name] = parameter
            journal('parameter_created', parameter_name=name)
        result = handles['result']
        # No stage selection: all four states must retain the same owned document.
        for index, (case, expression, expected_dependencies) in enumerate(STAGES):
            active_case = case
            sample = {'file': str(index+1).zfill(2)+'_'+case+'.f3d',
                      'case': case, 'stage_index': index, 'getter_errors': [],
                      'requested_result_expression': expression,
                      'expected_result_dependency_names': list(expected_dependencies),
                      'expected_internal_value_cm': 1.0,
                      'requested_expression_character_count': len(expression),
                      'requested_expression_utf16le_bytes': len(expression.encode('utf-16le'))}
            truth['active_sample'] = sample
            journal('stage_begin', case, stage_index=index)
            result.expression = expression
            journal('expression_assigned', case)
            if not design.computeAll():
                raise RuntimeError('computeAll returned false for '+case)
            journal('computed', case)
            design.timeline.moveToEnd()
            sample['timeline_count'] = observe('timeline.count', lambda: design.timeline.count, sample['getter_errors'])
            sample['marker_position'] = observe('timeline.markerPosition', lambda: design.timeline.markerPosition, sample['getter_errors'])
            sample['user_parameter_count'] = observe('userParameters.count', lambda: parameters.count, sample['getter_errors'])
            # Snapshot the original owned handles, with each API property guarded.
            sample['parameters'] = [parameter_truth(handles[name]) for name in PARAMETER_NAMES]
            actual_result = sample['parameters'][2]
            value = actual_result['value_cm']
            dependencies = actual_result['dependency_names']
            sample['observed_controls'] = {
                'expression_matches_request': actual_result['expression'] == expression if actual_result['expression'] is not None else None,
                'expression_character_count_is_five': actual_result['actual_expression_character_count'] == 5 if actual_result['expression'] is not None else None,
                'expression_utf16le_bytes_is_ten': actual_result['actual_expression_utf16le_bytes'] == 10 if actual_result['expression'] is not None else None,
                'all_cached_values_one_cm': all(p['value_cm'] is not None and math.isclose(p['value_cm'], 1.0, abs_tol=1e-10) for p in sample['parameters']) if all(p['value_cm'] is not None for p in sample['parameters']) else None,
                'result_value_one_cm': math.isclose(value, 1.0, abs_tol=1e-10) if value is not None else None,
                'result_dependency_names_match_prediction': sorted(dependencies) == sorted(expected_dependencies) if dependencies is not None else None,
                'all_original_handles_valid': all(p['is_valid'] for p in sample['parameters']) if all(p['is_valid'] is not None for p in sample['parameters']) else None,
            }
            journal('api_snapshot_complete', case, observed_controls=sample['observed_controls'])
            # Export this state before changing the next expression.
            destination = output / sample['file']
            journal('export_begin', case, file=sample['file'])
            options = design.exportManager.createFusionArchiveExportOptions(str(destination))
            succeeded = design.exportManager.execute(options)
            if not succeeded or not destination.is_file() or destination.stat().st_size == 0:
                raise RuntimeError('Local archive export did not complete for '+case)
            sample['export'] = {'returned_success': bool(succeeded),
                                'size_bytes': destination.stat().st_size,
                                'sha256': hashlib.sha256(destination.read_bytes()).hexdigest()}
            truth['samples'].append(sample)
            truth.pop('active_sample', None)
            journal('export_complete', case, file=sample['file'])
        terminal_status = 'complete'
    except Exception:
        truth['errors'].append({'case': active_case, 'error': traceback.format_exc(),
                                'policy': 'Sequence aborted before any later expression edit; earlier exports and active partial snapshot retained.'})
        journal('batch_error', active_case)
    finally:
        if doc is not None:
            journal('document_close_begin', active_case)
            if design is not None:
                try:
                    design.timeline.moveToEnd()
                except Exception:
                    terminal_status = 'failed'
                    truth['errors'].append({'case': active_case, 'phase': 'restore_owned_timeline',
                                            'error': traceback.format_exc()})
            try:
                doc.close(False)
                journal('document_closed', active_case, save=False)
            except Exception:
                terminal_status = 'failed'
                truth['errors'].append({'case': active_case, 'phase': 'close_owned_document',
                                        'error': traceback.format_exc()})
        truth['terminal_status'] = terminal_status
        truth['exported_sample_count'] = len(truth['samples'])
        journal('batch_complete' if terminal_status == 'complete' else 'batch_failed', active_case)
        (output / 'complete.txt').write_text('Parameter identity contrast sequence finished: '+terminal_status+'; consult ground_truth.json and errors.\n')
