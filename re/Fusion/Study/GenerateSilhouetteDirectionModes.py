"""Journaled study-owned SilhouetteSplit BRep direction and custom-axis inputs.

SDK permits linear BRepEdge/planar BRepFace viewDirection. Custom axis uses the
parametric setByEdge API, not direct-model-only setByLine. Root dispatches serially.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CASES = ('faces_brep_edge_x', 'faces_brep_face_yz', 'faces_custom_axis_x')


def run(context):
    app = adsk.core.Application.get()
    folder = Path(__file__).resolve().parent/('silhouettedirections-'+uuid.uuid4().hex[:12])
    folder.mkdir()
    truth = {'fusion_version': app.version, 'samples': [], 'errors': [],
             'scope': 'Independent support block supplies a linear edge or planar face; custom axis defined from that edge. Actual rolled-back source geometry getters are independent evidence, not native geometry-cache decoding.'}
    cases = context.get('cases', CASES) if isinstance(context, dict) else CASES
    point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString

    def journal(phase, case=None):
        event = {'phase': phase, 'case': case, 'time_utc': datetime.now(timezone.utc).isoformat(),
                 'sample_count': len(truth['samples']), 'error_count': len(truth['errors'])}
        with (folder/'journal.jsonl').open('a') as output:
            output.write(json.dumps(event)+'\n')
        (folder/'progress.json').write_text(json.dumps(event, indent=2)+'\n')
        (folder/'ground_truth.json').write_text(json.dumps(truth, indent=2)+'\n')

    journal('batch_begin')
    for case in cases:
        doc = design = None
        sample = {'file': case+'.f3d', 'case': case, 'getter_errors': []}

        def observe(label, read):
            try:
                return read()
            except Exception:
                sample['getter_errors'].append({'field': label, 'error': traceback.format_exc()})
                return None

        def body_truth(body, label):
            return {'entity_type': observe(label+'.type', lambda: body.objectType),
                    'entity_token': observe(label+'.token', lambda: body.entityToken),
                    'name': observe(label+'.name', lambda: body.name),
                    'is_solid': observe(label+'.isSolid', lambda: body.isSolid),
                    'face_count': observe(label+'.faces', lambda: body.faces.count),
                    'edge_count': observe(label+'.edges', lambda: body.edges.count),
                    'volume_cm3': observe(label+'.volume', lambda: body.volume),
                    'bounding_box_cm': observe(label+'.bounds', lambda: [body.boundingBox.minPoint.asArray(), body.boundingBox.maxPoint.asArray()])}

        def source_truth(source, label, include_definition=True):
            result = {'entity_type': observe(label+'.type', lambda: source.objectType),
                      'entity_token': observe(label+'.token', lambda: source.entityToken)}
            geometry = observe(label+'.geometry', lambda: source.geometry)
            result['geometry_type'] = observe(label+'.geometry.type', lambda: geometry.objectType)
            if isinstance(source, adsk.fusion.BRepEdge):
                result['temp_id'] = observe(label+'.tempId', lambda: source.tempId)
                result['body'] = body_truth(source.body, label+'.body')
                result['start_vertex_cm'] = observe(label+'.startVertex', lambda: source.startVertex.geometry.asArray())
                result['end_vertex_cm'] = observe(label+'.endVertex', lambda: source.endVertex.geometry.asArray())
                result['line_start_cm'] = observe(label+'.line.start', lambda: geometry.startPoint.asArray())
                result['line_end_cm'] = observe(label+'.line.end', lambda: geometry.endPoint.asArray())
                result['line_origin_cm'] = observe(label+'.line.origin', lambda: geometry.asInfiniteLine().origin.asArray())
                result['line_direction'] = observe(label+'.line.direction', lambda: geometry.asInfiniteLine().direction.asArray())

                def evaluated():
                    evaluator = source.evaluator
                    ok, low, high = evaluator.getParameterExtents()
                    if not ok:
                        raise RuntimeError('Trimmed edge parameter extents failed')
                    parameters = [low, (low+high)/2., high]
                    ok, points = evaluator.getPointsAtParameters(parameters)
                    if not ok:
                        raise RuntimeError('Trimmed edge evaluator points failed')
                    return {'parameter_extents': [low, high], 'parameters': parameters,
                            'points_cm': [p.asArray() for p in points]}
                result['actual_trimmed_edge_evaluator'] = observe(label+'.trimmedEvaluator', evaluated)
            elif isinstance(source, adsk.fusion.BRepFace):
                result['temp_id'] = observe(label+'.tempId', lambda: source.tempId)
                result['body'] = body_truth(source.body, label+'.body')
                result['origin_cm'] = observe(label+'.plane.origin', lambda: geometry.origin.asArray())
                result['normal'] = observe(label+'.plane.normal', lambda: geometry.normal.asArray())
                result['area_cm2'] = observe(label+'.area', lambda: source.area)
                result['centroid_cm'] = observe(label+'.centroid', lambda: source.centroid.asArray())
                result['is_param_reversed'] = observe(label+'.isParamReversed', lambda: source.isParamReversed)
            elif isinstance(source, adsk.fusion.ConstructionAxis):
                result['name'] = observe(label+'.name', lambda: source.name)
                result['origin_cm'] = observe(label+'.axis.origin', lambda: geometry.origin.asArray())
                result['direction'] = observe(label+'.axis.direction', lambda: geometry.direction.asArray())
                if include_definition:
                    definition = observe(label+'.definition', lambda: source.definition)
                    result['definition_type'] = observe(label+'.definition.type', lambda: definition.objectType)
                    edge = observe(label+'.definition.edge', lambda: definition.edgeEntity)
                    if edge is not None:
                        result['definition_edge'] = source_truth(edge, label+'.definition.edge', False)
            return result

        try:
            if case not in CASES:
                raise ValueError('Unknown study case '+str(case))
            journal('creating_document', case)
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            support_sketch = root.sketches.add(root.xYConstructionPlane)
            support_sketch.name = 'SilhouetteDirectionSupportProfile'
            support_sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(6, -2, 0), point(8, -1, 0))
            support_feature = root.features.extrudeFeatures.addSimple(support_sketch.profiles.item(0), value('20 mm'),
                                      adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            support_feature.name = 'SilhouetteDirectionSupportExtrude'
            support = support_feature.bodies.item(0)
            support.name = 'SilhouetteDirectionSupportBody'
            candidates = []
            for edge in support.edges:
                geometry = edge.geometry
                if isinstance(geometry, adsk.core.Line3D):
                    direction = geometry.asInfiniteLine().direction
                    if not direction.normalize():
                        continue
                    if abs(abs(direction.x)-1.) < 1e-8 and abs(direction.y)+abs(direction.z) < 1e-8:
                        center = edge.startVertex.geometry
                        candidates.append((center.z, center.y, edge))
            if not candidates:
                raise RuntimeError('No linear X-direction support edge')
            source_edge = sorted(candidates, key=lambda item: item[:2])[0][2]
            if case == 'faces_brep_face_yz':
                faces = [face for face in support.faces if isinstance(face.geometry, adsk.core.Plane)
                         and abs(abs(face.geometry.normal.x)-1.) < 1e-8]
                if not faces:
                    raise RuntimeError('No planar YZ support face')
                selected = min(faces, key=lambda face: face.centroid.x)
            elif case == 'faces_custom_axis_x':
                axis_input = root.constructionAxes.createInput()
                setter = axis_input.setByEdge(source_edge)
                sample['custom_axis_setByEdge_returned'] = setter
                if not setter:
                    raise RuntimeError('Documented construction-axis setByEdge returned false')
                selected = root.constructionAxes.add(axis_input)
                selected.name = 'SilhouetteCustomSupportAxisX'
            else:
                selected = source_edge
            sample['source_before_split'] = source_truth(selected, 'source_before')
            sketch = root.sketches.add(root.xYConstructionPlane)
            sketch.name = 'SilhouetteTargetProfile'
            sketch.sketchCurves.sketchCircles.addByCenterRadius(point(1, .5, 0), 2)
            seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value('40 mm'),
                                     adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            seed.name = 'SilhouetteTargetCylinder'
            target = seed.bodies.item(0)
            target.name = 'SilhouetteDirectionTargetBody'
            operation = adsk.fusion.SilhouetteSplitOperations.SilhouetteSplitFacesOnlyOperation
            sample['requested'] = {'operation': int(operation), 'view_direction_type': selected.objectType,
                'source_support_body_name': support.name, 'target_body_name': target.name,
                'source_support_feature_name': support_feature.name, 'target_feature_name': seed.name}
            sample['target_before_split'] = body_truth(target, 'target_before')
            journal('creating_feature', case)
            inputs = root.features.silhouetteSplitFeatures.createInput(selected, target, operation)
            feature = root.features.silhouetteSplitFeatures.add(inputs)
            if feature is None:
                raise RuntimeError('SilhouetteSplit add returned None')
            feature.name = 'ProbeSilhouetteDirection'
            if not design.computeAll():
                raise RuntimeError('Silhouette direction recomputation failed')
            journal('reading_actual_rolledback_inputs', case)
            feature.timelineObject.rollTo(True)
            sample['actual_direction'] = source_truth(feature.viewDirection, 'actual_direction')
            sample['actual_target'] = body_truth(feature.targetBody, 'actual_target')
            design.timeline.moveToEnd()
            sample['feature_type'] = observe('feature.type', lambda: feature.objectType)
            sample['settings'] = {'operation': observe('feature.operation', lambda: int(feature.operation)),
                'is_suppressed': observe('feature.isSuppressed', lambda: feature.isSuppressed),
                'health_state': observe('feature.healthState', lambda: int(feature.healthState)),
                'warning': observe('feature.warning', lambda: feature.errorOrWarningMessage)}
            sample['feature_bodies'] = observe('feature.bodies', lambda: [body_truth(b, 'feature.body'+str(i)) for i,b in enumerate(feature.bodies)])
            sample['root_bodies'] = observe('root.bRepBodies', lambda: [body_truth(b, 'root.body'+str(i)) for i,b in enumerate(root.bRepBodies)])
            sample['parameters'] = [{'name': p.name, 'role': p.role, 'unit': p.unit, 'value': p.value,
                                    'created_by': getattr(p.createdBy, 'name', None)} for p in root.modelParameters]
            journal('exporting', case)
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(folder/sample['file']))):
                raise RuntimeError('Silhouette direction local export failed')
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
                try:
                    doc.close(False)
                except Exception:
                    truth['errors'].append({'case': case, 'cleanup': 'close_without_save', 'error': traceback.format_exc()})
            journal('case_terminal', case)
    journal('batch_complete')
    (folder/'complete.txt').write_text('Silhouette direction capture terminal; consult errors.\n')
