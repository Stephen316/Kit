"""Journaled documented Mirror feature/face/occurrence/datum and Scale Sketch inputs."""

import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ('mirror_two_features', 'mirror_boss_faces', 'mirror_occurrence',
         'mirror_construction_plane', 'scale_two_sketches')


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/('remainingbodyinputs-'+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {'fusion_version': app.version, 'samples': [], 'errors': [],
             'sdk_evidence': {'MirrorFeatureInput.inputEntities': 'Homogeneous BRepFace/PartFeature/BRepBody/Occurrence collection; a single construction datum is also allowed',
                              'MirrorFeatureInput.patternComputeOption': 'Only applies to feature inputs; other input enum getters remain inactive evidence',
                              'ScaleFeatureInput.inputEntities': 'Parametric uniform input supports sketches; nonuniform sketch scaling unsupported',
                              'participant_bodies': 'No MirrorFeature participantBodies SDK property; actual source input and feature result collections are captured separately'}}
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByReal
    cases = context.get('cases', CASES) if isinstance(context, dict) else CASES
    for case in cases:
        doc = design = None
        sample = {'case': case, 'file': case+'.f3d', 'getter_errors': [], 'journal': []}

        def checkpoint(phase):
            sample['journal'].append(phase)
            truth['in_progress'] = sample
            (output/'progress.json').write_text(json.dumps({'case': case, 'phase': phase, 'completed': len(truth['samples'])})+'\n')
            (output/'ground_truth.json').write_text(json.dumps(truth, indent=2)+'\n')

        def observe(field, getter):
            try:
                return getter()
            except Exception:
                sample['getter_errors'].append({'field': field, 'error': traceback.format_exc()})
                checkpoint('getter_failed:'+field)
                return None

        def token(entity):
            return observe('entityToken:'+entity.objectType, lambda: entity.entityToken)

        def body_truth(body):
            return {'entity_type': body.objectType, 'name': body.name, 'entity_token': token(body),
                    'is_solid': body.isSolid,
                    'bounding_box_cm': {'min': body.boundingBox.minPoint.asArray(), 'max': body.boundingBox.maxPoint.asArray()}}

        def entity_truth(entity):
            result = {'entity_type': entity.objectType, 'entity_token': token(entity)}
            sketch = adsk.fusion.Sketch.cast(entity)
            feature = adsk.fusion.Feature.cast(entity)
            body = adsk.fusion.BRepBody.cast(entity)
            face = adsk.fusion.BRepFace.cast(entity)
            occurrence = adsk.fusion.Occurrence.cast(entity)
            plane = adsk.fusion.ConstructionPlane.cast(entity)
            construction_point = adsk.fusion.ConstructionPoint.cast(entity)
            if sketch:
                result.update(sketch_name=sketch.name, curve_count=sketch.sketchCurves.count,
                              line_endpoints_cm=[{'start': line.startSketchPoint.worldGeometry.asArray(),
                                                  'end': line.endSketchPoint.worldGeometry.asArray()} for line in sketch.sketchCurves.sketchLines])
            elif feature:
                result.update(name=feature.name, timeline_index=feature.timelineObject.index,
                              parent_component_name=feature.parentComponent.name,
                              source_feature_bodies=[body_truth(b) for b in feature.bodies])
            elif body:
                result.update(body_truth(body))
            elif face:
                result.update(source_body=body_truth(face.body), surface_type=int(face.geometry.surfaceType),
                              point_on_face_cm=face.pointOnFace.asArray())
                geometry = adsk.core.Plane.cast(face.geometry)
                if geometry:
                    result.update(origin_cm=geometry.origin.asArray(), normal=geometry.normal.asArray())
            elif occurrence:
                result.update(name=occurrence.name, full_path_name=occurrence.fullPathName,
                              component_name=occurrence.component.name,
                              transform=occurrence.transform2.asArray(),
                              bodies=[body_truth(b) for b in occurrence.bRepBodies])
            elif plane:
                result.update(name=plane.name, origin_cm=plane.geometry.origin.asArray(), normal=plane.geometry.normal.asArray())
            elif construction_point:
                result.update(name=construction_point.name, position_cm=construction_point.geometry.asArray())
            return result

        def rectangle(component, name, low, high, plane=None):
            sketch = component.sketches.add(plane if plane is not None else component.xYConstructionPlane)
            sketch.name = name
            sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(*low), point(*high))
            return sketch

        def extrude(component, name, sketch, distance, operation=None):
            operation = operation if operation is not None else adsk.fusion.FeatureOperations.NewBodyFeatureOperation
            feature = component.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value(distance), operation)
            feature.name = name
            return feature

        try:
            checkpoint('starting_case')
            if case not in CASES:
                raise ValueError('Unknown documented body input case')
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            entities = adsk.core.ObjectCollection.create()
            mirror_plane = root.yZConstructionPlane
            if case == 'mirror_two_features':
                seeds = []
                for index, x in enumerate((1, 6)):
                    sketch = rectangle(root, 'FeatureInputSketch'+str(index+1), (x,1,0), (x+2,3,0))
                    seed = extrude(root, 'FeatureInputExtrude'+str(index+1), sketch, 2)
                    seed.bodies.item(0).name = 'FeatureInputBody'+str(index+1)
                    seeds.append(seed)
                # Preserve request order explicitly; API normalization is separate.
                entities.add(seeds[1]); entities.add(seeds[0])
            elif case == 'mirror_boss_faces':
                base_sketch = rectangle(root, 'FaceInputBaseSketch', (-5,0,0), (5,4,0))
                base = extrude(root, 'FaceInputBaseExtrude', base_sketch, 1)
                base.bodies.item(0).name = 'FaceInputJoinedBody'
                plane_input = root.constructionPlanes.createInput()
                if not plane_input.setByOffset(root.xYConstructionPlane, value(1)):
                    raise RuntimeError('Boss support plane rejected')
                boss_plane = root.constructionPlanes.add(plane_input)
                boss_plane.name = 'BossSupportPlane'
                boss_sketch = root.sketches.add(boss_plane)
                boss_sketch.name = 'FaceInputBossSketch'
                boss_sketch.sketchCurves.sketchCircles.addByCenterRadius(point(2,2,0),0.5)
                boss = extrude(root, 'FaceInputBossExtrude', boss_sketch, 1, adsk.fusion.FeatureOperations.JoinFeatureOperation)
                # Complete new boss boundary: cylindrical side and planar top cap.
                for face in list(boss.sideFaces)+list(boss.endFaces):
                    entities.add(face)
                sample['requested_face_scope'] = 'All side/end faces of joined circular boss; API actual face order/types captured independently'
            elif case == 'mirror_occurrence':
                transform = adsk.core.Matrix3D.create()
                transform.translation = adsk.core.Vector3D.create(4,1,0)
                occurrence = root.occurrences.addNewComponent(transform)
                occurrence.component.name = 'OccurrenceMirrorSource'
                sketch = rectangle(occurrence.component, 'OccurrenceInputSketch', (0,0,0), (2,2,0))
                seed = extrude(occurrence.component, 'OccurrenceInputExtrude', sketch, 1)
                seed.bodies.item(0).name = 'OccurrenceInputBody'
                entities.add(occurrence)
            elif case == 'mirror_construction_plane':
                plane_input = root.constructionPlanes.createInput()
                if not plane_input.setByOffset(root.yZConstructionPlane, value(2)):
                    raise RuntimeError('Source construction plane rejected')
                plane = root.constructionPlanes.add(plane_input)
                plane.name = 'MirrorInputDatumPlane'
                entities.add(plane)
            else:
                first = rectangle(root, 'ScaleInputSketch1', (1,1,0), (4,3,0))
                second = rectangle(root, 'ScaleInputSketch2', (6,-2,0), (8,1,0))
                entities.add(second); entities.add(first)
            sample['requested_inputs'] = [entity_truth(entity) for entity in entities]
            sample['root_occurrences_before'] = observe('root.occurrences.before', lambda: [entity_truth(o) for o in root.occurrences])
            sample['root_construction_plane_names_before'] = [p.name for p in root.constructionPlanes]
            checkpoint('creating_input')
            if case == 'scale_two_sketches':
                sample['requested_settings'] = {'is_uniform': True, 'factor':0.8}
                sample['requested_point'] = entity_truth(root.originConstructionPoint)
                inputs = root.features.scaleFeatures.createInput(entities, root.originConstructionPoint, value(0.8))
                feature = root.features.scaleFeatures.add(inputs)
            else:
                sample['requested_settings'] = {'is_combine':False, 'active_compute':case=='mirror_two_features',
                                                'compute_option':1 if case=='mirror_two_features' else None}
                sample['requested_mirror_plane'] = entity_truth(mirror_plane)
                inputs = root.features.mirrorFeatures.createInput(entities, mirror_plane)
                inputs.isCombine = False
                if case == 'mirror_two_features':
                    inputs.patternComputeOption = adsk.fusion.PatternComputeOptions.IdenticalPatternCompute
                feature = root.features.mirrorFeatures.add(inputs)
            if feature is None:
                raise RuntimeError('Feature add returned null')
            feature.name = 'ProbeRemainingBodyInput'
            checkpoint('feature_added')
            feature.timelineObject.rollTo(True)
            checkpoint('reading_rolled_back_inputs')
            sample['actual_inputs'] = observe('feature.inputEntities', lambda: [entity_truth(entity) for entity in feature.inputEntities])
            if case == 'scale_two_sketches':
                sample['actual_point'] = observe('feature.point', lambda: entity_truth(feature.point))
                sample['settings'] = {'is_uniform':observe('isUniform',lambda:feature.isUniform),
                                      'factor':observe('scaleFactor',lambda:feature.scaleFactor.value)}
            else:
                sample['actual_mirror_plane'] = observe('mirrorPlane',lambda:entity_truth(feature.mirrorPlane))
                sample['settings'] = {'is_combine':observe('isCombine',lambda:feature.isCombine),
                                      'stitch_tolerance_cm':observe('stitchTolerance',lambda:feature.stitchTolerance.value),
                                      'stored_api_compute_getter':observe('patternComputeOption',lambda:int(feature.patternComputeOption)),
                                      'compute_expected_applicable':case=='mirror_two_features'}
            design.timeline.moveToEnd()
            checkpoint('reading_result_collections')
            sample['feature_identity'] = {'entity_type':feature.objectType,'name':feature.name,'entity_token':token(feature),'timeline_index':feature.timelineObject.index}
            sample['health_state'] = observe('healthState',lambda:int(feature.healthState))
            sample['warning'] = observe('errorOrWarningMessage',lambda:feature.errorOrWarningMessage)
            sample['api_feature_bodies'] = observe('feature.bodies',lambda:[body_truth(b) for b in feature.bodies])
            if case.startswith('mirror'):
                sample['api_result_features'] = observe('resultFeatures',lambda:[entity_truth(f) for f in feature.resultFeatures] if feature.resultFeatures else None)
            sample['root_body_names_after'] = [b.name for b in root.bRepBodies]
            sample['root_occurrences_after'] = observe('root.occurrences.after',lambda:[entity_truth(o) for o in root.occurrences])
            sample['root_construction_plane_names_after'] = [p.name for p in root.constructionPlanes]
            sample['root_sketch_names_after'] = [s.name for s in root.sketches]
            sample['parameters'] = observe('root.modelParameters',lambda:[{'name':p.name,'role':p.role,'value':p.value,'unit':p.unit,
                                             'expression':p.expression,'created_by':p.createdBy.name if p.createdBy else None} for p in root.modelParameters])
            checkpoint('exporting')
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample['file']))):
                raise RuntimeError('Remaining input archive export failed')
            sample['export_exists'] = (output/sample['file']).is_file()
            checkpoint('exported')
            truth['samples'].append(sample)
        except Exception:
            truth['errors'].append({'case':case,'error':traceback.format_exc(),'partial_capture':sample})
            checkpoint('case_failed')
        finally:
            if design is not None:
                try: design.timeline.moveToEnd()
                except Exception: sample['getter_errors'].append({'field':'finally.restore_timeline','error':traceback.format_exc()})
            if doc is not None:
                try: doc.close(False)
                except Exception: sample['getter_errors'].append({'field':'finally.closeFalse','error':traceback.format_exc()})
            truth.pop('in_progress',None)
            (output/'ground_truth.json').write_text(json.dumps(truth,indent=2)+'\n')
            (output/'progress.json').write_text(json.dumps({'case':case,'phase':'case_finished','completed':len(truth['samples']),'errors':len(truth['errors'])})+'\n')
    (output/'complete.txt').write_text('Remaining documented input capture terminal; consult errors and getter_errors.\n')
