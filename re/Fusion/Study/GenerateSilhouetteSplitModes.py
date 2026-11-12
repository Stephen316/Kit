"""Owned cylinder SilhouetteSplit operation and direction-source contrasts."""

from datetime import datetime, timezone
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CASES = ('faces_axis_x', 'faces_axis_y', 'solid_axis_x', 'shelled_axis_x', 'faces_plane_yz')


def run(context):
    app = adsk.core.Application.get()
    folder = Path(__file__).resolve().parent/('silhouettesplits-'+uuid.uuid4().hex[:12])
    folder.mkdir()
    truth = {'fusion_version': app.version, 'samples': [], 'errors': []}
    cases = context.get('cases', CASES) if isinstance(context, dict) else CASES
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString

    def journal(phase, case=None):
        event = {'phase': phase, 'case': case, 'time_utc': datetime.now(timezone.utc).isoformat(),
                 'sample_count': len(truth['samples']), 'error_count': len(truth['errors'])}
        with (folder/'journal.jsonl').open('a') as output:
            output.write(json.dumps(event)+'\n')
        (folder/'progress.json').write_text(json.dumps(event, indent=2)+'\n')
        (folder/'ground_truth.json').write_text(json.dumps(truth, indent=2)+'\n')

    def body_truth(body):
        return {'entity_type': body.objectType, 'entity_token': body.entityToken, 'name': body.name,
                'is_solid': body.isSolid, 'faces': body.faces.count, 'edges': body.edges.count,
                'volume_cm3': body.volume, 'bounding_box_cm': [body.boundingBox.minPoint.asArray(), body.boundingBox.maxPoint.asArray()]}

    journal('batch_begin')
    for case in cases:
        doc = None
        design = None
        sample = {'file': case+'.f3d', 'getter_errors': []}

        def observe(field, read):
            try:
                return read()
            except Exception:
                sample['getter_errors'].append({'field': field, 'error': traceback.format_exc()})
                return None

        try:
            journal('creating_document', case)
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.name = 'SilhouetteSourceProfile'
            sketch.sketchCurves.sketchCircles.addByCenterRadius(point(1, .5, 0), 2)
            seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value('40 mm'),
                                                        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            seed.name = 'SilhouetteCylinder'
            body = seed.bodies.item(0)
            body.name = 'SilhouetteTarget'
            if case == 'shelled_hollow_axis_x':
                targets = adsk.core.ObjectCollection.create()
                targets.add(body)
                shell_input = root.features.shellFeatures.createInput(targets, False)
                shell_input.insideThickness = value('2 mm')
                shell = root.features.shellFeatures.add(shell_input)
                shell.name = 'SilhouetteHollowSource'
                body = shell.bodies.item(0)
                body.name = 'SilhouetteTarget'
            direction = root.yConstructionAxis if case == 'faces_axis_y' else root.xConstructionAxis
            if case == 'faces_plane_yz':
                direction = root.yZConstructionPlane
            operation = (adsk.fusion.SilhouetteSplitOperations.SilhouetteSplitSolidBodyOperation if case.startswith('solid') else
                         adsk.fusion.SilhouetteSplitOperations.SilhouetteSplitShelledBodyOperation if case.startswith('shelled') else
                         adsk.fusion.SilhouetteSplitOperations.SilhouetteSplitFacesOnlyOperation)
            sample['requested'] = {'operation': int(operation), 'direction_type': direction.objectType, 'direction_name': direction.name}
            journal('creating_feature', case)
            inputs = root.features.silhouetteSplitFeatures.createInput(direction, body, operation)
            feature = root.features.silhouetteSplitFeatures.add(inputs)
            if feature is None:
                raise RuntimeError('SilhouetteSplit add returned None')
            feature.name = 'ProbeSilhouetteSplit'
            if not design.computeAll():
                raise RuntimeError('Silhouette split recomputation failed')
            journal('reading_actual_inputs', case)
            feature.timelineObject.rollTo(True)
            selected = feature.viewDirection
            source = {'entity_type': selected.objectType, 'entity_token': selected.entityToken,
                      'name': selected.name, 'origin_cm': selected.geometry.origin.asArray()}
            if isinstance(selected, adsk.fusion.ConstructionAxis):
                source['direction'] = selected.geometry.direction.asArray()
            else:
                source['normal'] = selected.geometry.normal.asArray()
            sample['actual_direction'] = source
            sample['actual_target'] = body_truth(feature.targetBody)
            design.timeline.moveToEnd()
            sample['feature_type'] = feature.objectType
            sample['settings'] = {'operation': int(feature.operation), 'is_suppressed': feature.isSuppressed,
                                  'health_state': int(feature.healthState), 'warning': feature.errorOrWarningMessage}
            sample['feature_bodies'] = observe('feature.bodies', lambda: [body_truth(b) for b in feature.bodies])
            sample['root_bodies'] = observe('root.bRepBodies', lambda: [body_truth(b) for b in root.bRepBodies])
            sample['parameters'] = [{'name': p.name, 'role': p.role, 'unit': p.unit, 'value': p.value,
                                     'created_by': getattr(p.createdBy, 'name', None)} for p in root.modelParameters]
            journal('exporting', case)
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(folder/sample['file']))):
                raise RuntimeError('Silhouette split export failed')
            truth['samples'].append(sample)
            journal('export_complete', case)
        except Exception:
            truth['errors'].append({'case': case, 'error': traceback.format_exc(), 'partial': sample})
            journal('case_error', case)
        finally:
            if design is not None:
                try:
                    design.timeline.moveToEnd()
                except Exception:
                    truth['errors'].append({'case': case, 'cleanup': 'restore_timeline', 'error': traceback.format_exc()})
            if doc is not None:
                doc.close(False)
            journal('case_terminal', case)
    journal('batch_complete')
    (folder/'complete.txt').write_text('SilhouetteSplit capture terminal; consult errors.\n')
