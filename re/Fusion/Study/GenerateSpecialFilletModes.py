"""Journaled full-round and rule-fillet definition/input contrasts."""

from datetime import datetime, timezone
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CASES = ('full_automatic', 'full_explicit', 'rule_all_both', 'rule_all_rounds',
         'rule_all_fillets', 'rule_between_faces', 'rule_asymmetric')


def run(context):
    app = adsk.core.Application.get()
    folder = Path(__file__).resolve().parent/('specialfillets-'+uuid.uuid4().hex[:12])
    folder.mkdir()
    truth = {'fusion_version': app.version, 'samples': [], 'errors': []}
    cases = context.get('cases', CASES) if isinstance(context, dict) else CASES
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString

    def journal(phase, case=None):
        event = {'phase': phase, 'case': case, 'time_utc': datetime.now(timezone.utc).isoformat(),
                 'sample_count': len(truth['samples']), 'error_count': len(truth['errors'])}
        with (folder/'journal.jsonl').open('a') as stream:
            stream.write(json.dumps(event)+'\n')
        (folder/'progress.json').write_text(json.dumps(event, indent=2)+'\n')
        (folder/'ground_truth.json').write_text(json.dumps(truth, indent=2)+'\n')

    def entity_truth(entity):
        result = {'entity_type': entity.objectType, 'entity_token': entity.entityToken}
        if isinstance(entity, adsk.fusion.BRepFace):
            result.update(body_name=entity.body.name, surface_type=int(entity.geometry.surfaceType),
                          centroid_cm=entity.centroid.asArray(), point_on_face_cm=entity.pointOnFace.asArray())
            if isinstance(entity.geometry, adsk.core.Plane):
                result.update(origin_cm=entity.geometry.origin.asArray(), normal=entity.geometry.normal.asArray())
        else:
            result.update(name=entity.name, timeline_index=entity.timelineObject.index,
                          body_names=[b.name for b in entity.bodies])
        return result

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
            sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0, 0, 0), point(2 if case.startswith('full') else 6, 5, 0))
            seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value('30 mm' if case.startswith('full') else '10 mm'),
                                                        adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            seed.name = 'FilletSeed'
            seed.bodies.item(0).name = 'FilletTarget'
            center = seed.endFaces.item(0)
            side_one = next(f for f in seed.sideFaces if abs(f.geometry.normal.x) > .99 and abs(f.geometry.origin.x) < 1e-6)
            side_two = next(f for f in seed.sideFaces if abs(f.geometry.normal.x) > .99 and abs(f.geometry.origin.x-2) < 1e-6) if case.startswith('full') else None
            if case == 'full_explicit_swapped':
                side_one, side_two = side_two, side_one
            journal('preparing_definition', case)
            if case.startswith('full'):
                automatic = case == 'full_automatic'
                inputs = root.features.filletFeatures.createFullRoundFilletInput()
                if inputs.faceSets.add(center, [side_one], [side_two], automatic) is None:
                    raise RuntimeError('Full round face-set creation rejected')
                sample['requested'] = {'mode': 'FullRound', 'are_automatic_side_faces': automatic,
                                       'center': entity_truth(center), 'side_one': [entity_truth(side_one)], 'side_two': [entity_truth(side_two)]}
                journal('creating_feature', case)
                feature = root.features.filletFeatures.addFullRoundFillet(inputs)
            else:
                inputs = root.features.filletFeatures.createRuleFilletInput()
                if case.startswith('rule_between_faces'):
                    first, second = ([side_one], [center]) if case.endswith('_swapped') else ([center], [side_one])
                    accepted = inputs.setByBetweenFacesOrFeatures(first, second)
                    sample['requested'] = {'mode': 'Rule', 'source_one': [entity_truth(f) for f in first], 'source_two': [entity_truth(f) for f in second]}
                else:
                    plane_input = root.constructionPlanes.createInput()
                    plane_input.setByOffset(root.xYConstructionPlane, value('10 mm'))
                    plane = root.constructionPlanes.add(plane_input)
                    profile = root.sketches.add(plane)
                    profile.sketchCurves.sketchLines.addTwoPointRectangle(point(2, 1.5, 0), point(4, 3.5, 0))
                    boss = root.features.extrudeFeatures.addSimple(profile.profiles.item(0), value('20 mm'),
                                                                adsk.fusion.FeatureOperations.JoinFeatureOperation)
                    boss.name = 'FilletBoss'
                    accepted = inputs.setByAllEdges([boss])
                    sample['requested'] = {'mode': 'Rule', 'sources': [entity_truth(boss)]}
                if not accepted:
                    raise RuntimeError('Rule fillet source definition rejected')
                topology = {'rule_all_rounds': 1, 'rule_all_fillets': 2}.get(case, 0)
                inputs.topologyType = topology
                inputs.isRollingBallCorner = case != 'rule_asymmetric'
                if case == 'rule_asymmetric':
                    if not inputs.setAsymmetricOffsets(value('1 mm'), value('2 mm')):
                        raise RuntimeError('Asymmetric rule fillet offsets rejected')
                else:
                    inputs.radius = value('1 mm')
                sample['requested'].update(topology_type=topology, rolling_ball_corner=inputs.isRollingBallCorner)
                journal('creating_feature', case)
                feature = root.features.filletFeatures.addRuleFillet(inputs)
            if feature is None:
                raise RuntimeError('Fillet add returned None')
            feature.name = 'ProbeSpecialFillet'
            if not design.computeAll():
                raise RuntimeError('Fillet computation failed')
            sample['feature_type'] = feature.objectType
            sample['settings'] = {'fillet_feature_type': int(feature.filletFeatureType),
                                  'is_rolling_ball_corner': observe('isRollingBallCorner', lambda: feature.isRollingBallCorner),
                                  'health_state': int(feature.healthState), 'warning': feature.errorOrWarningMessage}
            journal('reading_actual_sources', case)
            feature.timelineObject.rollTo(True)
            if case.startswith('full'):
                sample['actual_face_sets'] = [{'are_automatic_side_faces': item.areAutomaticSideFaces,
                                              'center': entity_truth(item.centerFace),
                                              'side_one': [entity_truth(f) for f in item.sideOneFaces],
                                              'side_two': [entity_truth(f) for f in item.sideTwoFaces]}
                                             for item in feature.fullRoundFilletFaceSets]
            else:
                actual = feature.ruleFilletSettings
                def parameter_truth(parameter):
                    return None if parameter is None else {'name': parameter.name, 'role': parameter.role, 'value': parameter.value, 'unit': parameter.unit}
                sample['actual_rule'] = {'rule_type': int(actual.ruleType), 'topology_type': int(actual.topologyType),
                                         'is_constant_radius': actual.isConstantRadius,
                                         'radius': parameter_truth(actual.radius),
                                         'offset_one': parameter_truth(actual.asymmetricOffsetOne),
                                         'offset_two': parameter_truth(actual.asymmetricOffsetTwo),
                                         'sources': [entity_truth(e) for e in actual.facesOrFeatures],
                                         'source_one': [entity_truth(e) for e in actual.facesOrFeaturesOne],
                                         'source_two': [entity_truth(e) for e in actual.facesOrFeaturesTwo]}
            design.timeline.moveToEnd()
            sample['parameters'] = [{'name': p.name, 'role': p.role, 'value': p.value, 'unit': p.unit,
                                     'created_by': getattr(p.createdBy, 'name', None)} for p in root.modelParameters]
            sample['result_bodies'] = [{'name': b.name, 'faces': b.faces.count, 'edges': b.edges.count, 'volume_cm3': b.volume}
                                       for b in feature.bodies]
            journal('exporting', case)
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(folder/sample['file']))):
                raise RuntimeError('Special fillet export failed')
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
                    truth['errors'].append({'case': case, 'cleanup': 'timeline_restore', 'error': traceback.format_exc()})
            if doc is not None:
                doc.close(False)
            journal('case_terminal', case)
    journal('batch_complete')
    (folder/'complete.txt').write_text('Special fillet capture terminal; inspect errors.\n')
