"""Journaled active Mirror feature-compute and planar-face plane contrasts.

Run only through the root agent's serial Fusion dispatcher. Every case owns a
new unsaved document; failures and the latest in-progress sample stay on disk.
"""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ('feature_optimized', 'feature_identical', 'feature_adjust', 'body_brep_face_plane')


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/('mirrorfeatures-'+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {'fusion_version': app.version, 'samples': [], 'errors': [],
             'scope': 'Three same-Extrude feature inputs with actual active compute getters; one body input mirrored across an actual planar BRepFace',
             'sdk_evidence': {'compute': 'MirrorFeatureInput.patternComputeOption applies only to feature inputs; Optimized0/Identical1/Adjust2 are requested independently of native encoding',
                              'mirror_plane': 'MirrorFeatures.createInput accepts planar BRepFace or ConstructionPlane',
                              'input_getter': 'MirrorFeature.inputEntities requires timeline immediately before feature',
                              'participant_bodies': 'MirrorFeature has no participantBodies property in the local SDK. Actual source-feature/source-input bodies and Feature.bodies/resultFeatures are captured separately.'}}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByReal
    cases = context.get('cases', CASES) if isinstance(context, dict) else CASES
    for case in cases:
        sample = {'case': case, 'file': case+'.f3d', 'getter_errors': [], 'journal': []}
        doc = design = None

        def checkpoint(phase):
            sample['journal'].append(phase)
            truth['in_progress'] = sample
            (output/'progress.json').write_text(json.dumps({'case': case, 'phase': phase, 'completed_samples': len(truth['samples'])})+'\n')
            (output/'ground_truth.json').write_text(json.dumps(truth, indent=2)+'\n')

        def observe(field, getter):
            try:
                return getter()
            except Exception:
                sample['getter_errors'].append({'field': field, 'error': traceback.format_exc()})
                checkpoint('getter_failed:'+field)
                return None

        def body_truth(body):
            return {'entity_type': body.objectType, 'name': body.name,
                    'entity_token': observe('body.token', lambda: body.entityToken),
                    'is_solid': body.isSolid,
                    'bounding_box_cm': {'min': body.boundingBox.minPoint.asArray(), 'max': body.boundingBox.maxPoint.asArray()}}

        def feature_truth(feature):
            return {'entity_type': feature.objectType, 'name': feature.name,
                    'entity_token': observe('feature.token', lambda: feature.entityToken),
                    'timeline_index': observe('feature.timeline_index', lambda: feature.timelineObject.index),
                    'parent_component_name': feature.parentComponent.name}

        def entity_truth(entity):
            feature = adsk.fusion.Feature.cast(entity)
            body = adsk.fusion.BRepBody.cast(entity)
            face = adsk.fusion.BRepFace.cast(entity)
            if feature:
                return {**feature_truth(feature), 'source_feature_bodies': [body_truth(b) for b in feature.bodies]}
            if body:
                return body_truth(body)
            if face:
                return {'entity_type': face.objectType, 'entity_token': face.entityToken,
                        'body': body_truth(face.body), 'surface_type': int(face.geometry.surfaceType)}
            return {'entity_type': entity.objectType}

        def plane_truth(entity):
            face = adsk.fusion.BRepFace.cast(entity)
            plane = adsk.fusion.ConstructionPlane.cast(entity)
            result = {'entity_type': entity.objectType, 'entity_token': entity.entityToken}
            if face:
                geometry = adsk.core.Plane.cast(face.geometry)
                result.update(source_body=body_truth(face.body), surface_type=int(face.geometry.surfaceType),
                              point_on_face_cm=face.pointOnFace.asArray())
            elif plane:
                geometry = plane.geometry
                result['name'] = plane.name
            else:
                raise RuntimeError('Actual mirrorPlane is not a planar face or construction plane')
            if geometry is None:
                raise RuntimeError('Actual mirrorPlane geometry is not planar')
            result.update(origin_cm=geometry.origin.asArray(), normal=geometry.normal.asArray())
            return result

        try:
            checkpoint('starting_case')
            if case not in CASES:
                raise ValueError('Unknown Mirror feature contrast')
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            checkpoint('creating_same_seed')
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.name = 'MirrorSeedSketch'
            sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(1, 1, 0), point(4, 4, 0))
            seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value(2), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            seed.name = 'MirrorSeedExtrude'
            seed.bodies.item(0).name = 'MirrorSeedBody'
            entities = adsk.core.ObjectCollection.create()
            if case == 'body_brep_face_plane':
                entities.add(seed.bodies.item(0))
                support_sketch = root.sketches.add(root.xYConstructionPlane)
                support_sketch.name = 'MirrorPlaneSupportSketch'
                support_sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(-4, -4, 0), point(-2, -2, 0))
                support = root.features.extrudeFeatures.addSimple(support_sketch.profiles.item(0), value(3), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                support.name = 'MirrorPlaneSupportExtrude'
                support.bodies.item(0).name = 'MirrorPlaneSupportBody'
                if support.endFaces.count != 1:
                    raise RuntimeError('Controlled planar support end face missing or ambiguous')
                mirror_plane = support.endFaces.item(0)
                requested_compute = None
            else:
                entities.add(seed)
                mirror_plane = root.yZConstructionPlane
                requested_compute = {'feature_optimized': adsk.fusion.PatternComputeOptions.OptimizedPatternCompute,
                                     'feature_identical': adsk.fusion.PatternComputeOptions.IdenticalPatternCompute,
                                     'feature_adjust': adsk.fusion.PatternComputeOptions.AdjustPatternCompute}[case]
            sample['requested'] = {'input_kind': 'BRepBody' if requested_compute is None else 'ExtrudeFeature',
                                   'source_feature_name': seed.name, 'compute_option': int(requested_compute) if requested_compute is not None else None,
                                   'is_combine': False, 'stitch_tolerance_cm': 0.001}
            sample['input_entities_before_mirror'] = [entity_truth(entity) for entity in entities]
            sample['mirror_plane_before_mirror'] = plane_truth(mirror_plane)
            checkpoint('creating_mirror_input')
            inputs = root.features.mirrorFeatures.createInput(entities, mirror_plane)
            inputs.isCombine = False
            inputs.stitchTolerance = value(0.001)
            if requested_compute is not None:
                inputs.patternComputeOption = requested_compute
            checkpoint('adding_mirror_feature')
            feature = root.features.mirrorFeatures.add(inputs)
            if feature is None:
                raise RuntimeError('MirrorFeatures.add returned null')
            feature.name = 'ProbeMirrorFeatureModes'
            checkpoint('mirror_added')
            feature.timelineObject.rollTo(True)
            checkpoint('reading_rolled_back_inputs')
            sample['actual_inputs'] = observe('inputEntities', lambda: [entity_truth(entity) for entity in feature.inputEntities])
            sample['actual_mirror_plane'] = observe('mirrorPlane', lambda: plane_truth(feature.mirrorPlane))
            sample['settings'] = {}
            for name, getter in (('compute_option', lambda: int(feature.patternComputeOption)),
                                 ('is_combine', lambda: feature.isCombine),
                                 ('stitch_tolerance_cm', lambda: feature.stitchTolerance.value)):
                sample['settings'][name] = observe(name, getter)
            design.timeline.moveToEnd()
            checkpoint('reading_results_at_timeline_end')
            sample['feature'] = feature_truth(feature)
            sample['settings']['health_state'] = observe('healthState', lambda: int(feature.healthState))
            sample['settings']['warning'] = observe('errorOrWarningMessage', lambda: feature.errorOrWarningMessage)
            sample['api_feature_bodies'] = observe('feature.bodies', lambda: [body_truth(b) for b in feature.bodies])
            sample['api_result_features'] = observe('feature.resultFeatures', lambda: [feature_truth(f) for f in feature.resultFeatures] if feature.resultFeatures else None)
            sample['root_bodies'] = observe('root.bRepBodies', lambda: [body_truth(b) for b in root.bRepBodies])
            sample['parameters'] = observe('root.modelParameters', lambda: [{'name': p.name, 'role': p.role, 'value': p.value, 'unit': p.unit,
                                                                            'expression': p.expression,
                                                                            'created_by': p.createdBy.name if p.createdBy else None} for p in root.modelParameters])
            checkpoint('exporting')
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample['file']))):
                raise RuntimeError('Mirror feature contrast export failed')
            sample['export_exists'] = (output/sample['file']).is_file()
            checkpoint('exported')
            truth['samples'].append(sample)
        except Exception:
            truth['errors'].append({'case': case, 'error': traceback.format_exc(), 'partial_capture': sample})
            checkpoint('case_failed')
        finally:
            if design is not None:
                try:
                    design.timeline.moveToEnd()
                except Exception:
                    sample['getter_errors'].append({'field': 'finally.restore_timeline', 'error': traceback.format_exc()})
            if doc is not None:
                try:
                    doc.close(False)
                except Exception:
                    sample['getter_errors'].append({'field': 'finally.close_unsaved_document', 'error': traceback.format_exc()})
            truth.pop('in_progress', None)
            (output/'ground_truth.json').write_text(json.dumps(truth, indent=2)+'\n')
            (output/'progress.json').write_text(json.dumps({'case': case, 'phase': 'case_finished', 'completed_samples': len(truth['samples']), 'errors': len(truth['errors'])})+'\n')
    (output/'complete.txt').write_text('Mirror feature captures terminal; inspect errors/getter_errors.\n')
