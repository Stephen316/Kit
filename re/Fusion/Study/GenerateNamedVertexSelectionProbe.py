"""Two journaled vertex-selection contrasts on fresh imports of an owned fixture.

Only imported new documents are modified/exported/closed. Collection indices
construct the probe and are not asserted to be native names, IDs or recipes.
"""
import hashlib
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

SOURCE = 'splinepatches-900d152c2380/splinepatches.f3d'
CASES = ('construction_polynomial_vertex0', 'scale_rational_vertex2')


def run(context):
    app = adsk.core.Application.get(); root = Path(__file__).resolve().parent
    output = root/('namedvertexprobe-'+uuid.uuid4().hex[:12]); output.mkdir()
    cases = context.get('cases', CASES) if isinstance(context, dict) else CASES
    if not isinstance(cases, (tuple, list)) or any(case not in CASES for case in cases):
        raise ValueError('Unknown named-vertex probe cases')
    report = {'fusion_version': app.version, 'source_archive': SOURCE,
              'source_sha256': hashlib.sha256((root/SOURCE).read_bytes()).hexdigest(),
              'samples': [], 'errors': [], 'status': 'running',
              'scope': 'Actual selected BRepVertex getter evidence; tokens/temporary IDs/collection indices do not decode naming identity'}

    def save():
        (output/'ground_truth.json').write_text(json.dumps(report, indent=2)+'\n')
        (output/'progress.json').write_text(json.dumps({'status': report['status'], 'samples': [
            {'case': s['case'], 'status': s['status']} for s in report['samples']], 'errors': len(report['errors'])}, indent=2)+'\n')

    save()
    for case in cases:
        document = None
        sample = {'case': case, 'file': case+'.f3d', 'status': 'importing', 'getter_errors': []}
        report['samples'].append(sample); save()
        try:
            document = app.importManager.importToNewDocument(app.importManager.createFusionArchiveImportOptions(str(root/SOURCE)))
            if document is None:
                raise RuntimeError('Owned archive import did not return a new document')
            design = adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))
            if design is None or design.designType != adsk.fusion.DesignTypes.ParametricDesignType:
                raise RuntimeError('Named vertex source must remain an imported parametric design')
            component = design.rootComponent; design.timeline.moveToEnd()

            def read(field, callback):
                try: return callback()
                except Exception:
                    sample['getter_errors'].append({'field': field, 'error': traceback.format_exc()})
                    return None

            def body_truth(body, label):
                return {'entity_type': body.objectType, 'name': body.name,
                        'entity_token': read(label+'.entity_token', lambda: body.entityToken),
                        'vertex_count': body.vertices.count, 'edge_count': body.edges.count, 'face_count': body.faces.count,
                        'is_solid': body.isSolid,
                        'bounds_min_cm': read(label+'.bounds_min', lambda: list(body.boundingBox.minPoint.asArray())),
                        'bounds_max_cm': read(label+'.bounds_max', lambda: list(body.boundingBox.maxPoint.asArray()))}

            def vertex_truth(vertex, label):
                result = {'entity_type': vertex.objectType,
                          'entity_token': read(label+'.entity_token', lambda: vertex.entityToken),
                          'temporary_id': read(label+'.temporary_id', lambda: vertex.tempId),
                          'world_point_cm': list(vertex.geometry.asArray()),
                          'body': body_truth(vertex.body, label+'.body'), 'incident_edges': []}
                for i in range(vertex.edges.count):
                    edge = vertex.edges.item(i)
                    result['incident_edges'].append({'entity_type': edge.objectType,
                        'entity_token': read(label+'.edge'+str(i)+'.token', lambda edge=edge: edge.entityToken),
                        'temporary_id': read(label+'.edge'+str(i)+'.temp_id', lambda edge=edge: edge.tempId),
                        'geometry_type': read(label+'.edge'+str(i)+'.geometry_type', lambda edge=edge: edge.geometry.objectType),
                        'start_vertex_cm': read(label+'.edge'+str(i)+'.start', lambda edge=edge: list(edge.startVertex.geometry.asArray())),
                        'end_vertex_cm': read(label+'.edge'+str(i)+'.end', lambda edge=edge: list(edge.endVertex.geometry.asArray()))})
                return result

            body_name, vertex_index = ('PolynomialPatch', 0) if case.startswith('construction_') else ('RationalPatch', 2)
            bodies = [body for body in component.bRepBodies if body.name == body_name]
            if len(bodies) != 1 or bodies[0].vertices.count != 4:
                raise RuntimeError('Expected one four-vertex named source patch')
            body = bodies[0]; vertex = body.vertices.item(vertex_index)
            sample['requested_source'] = {'body_name': body_name, 'vertex_collection_index': vertex_index,
                'index_scope': 'Probe construction only, not a persistent identity or native naming interpretation'}
            sample['source_vertex_inventory'] = [vertex_truth(body.vertices.item(i), 'source_vertices.'+str(i)) for i in range(body.vertices.count)]
            sample['selected_vertex_before_feature'] = vertex_truth(vertex, 'selected_before')
            sample['status'] = 'creating_feature'; save()
            if case.startswith('construction_'):
                inputs = component.constructionPoints.createInput()
                sample['set_by_point_accepted'] = inputs.setByPoint(vertex)
                if not sample['set_by_point_accepted']:
                    raise RuntimeError('ConstructionPointInput.setByPoint(BRepVertex) rejected')
                feature = component.constructionPoints.add(inputs)
                feature.name = 'ProbeNamedPatchVertexPoint'
                definition = feature.definition
                sample['actual'] = {'feature_type': feature.objectType, 'feature_name': feature.name,
                    'is_parametric': feature.isParametric, 'world_point_cm': list(feature.geometry.asArray()),
                    'definition_type': definition.objectType}
                point_definition = adsk.fusion.ConstructionPointPointDefinition.cast(definition)
                if point_definition is None:
                    raise RuntimeError('Actual construction point did not retain ByPoint definition')
                selected = point_definition.pointEntity
                actual_vertex = adsk.fusion.BRepVertex.cast(selected)
                sample['actual']['point_entity_type'] = selected.objectType
                if actual_vertex is None:
                    raise RuntimeError('Actual ByPoint source getter is not BRepVertex')
                sample['actual']['source_vertex'] = vertex_truth(actual_vertex, 'actual_definition_vertex')
            else:
                collection = adsk.core.ObjectCollection.create(); collection.add(body)
                inputs = component.features.scaleFeatures.createInput(collection, vertex, adsk.core.ValueInput.createByReal(1.25))
                if inputs is None: raise RuntimeError('Scale BRepVertex input rejected')
                feature = component.features.scaleFeatures.add(inputs)
                if feature is None: raise RuntimeError('Parametric Scale add returned no feature')
                feature.name = 'ProbeNamedPatchVertexScale'
                sample['actual'] = {'feature_type': feature.objectType, 'feature_name': feature.name,
                    'result_bodies': [body_truth(b, 'scale_result') for b in feature.bodies]}
                feature.timelineObject.rollTo(True)
                actual_point = feature.point; actual_vertex = adsk.fusion.BRepVertex.cast(actual_point)
                sample['actual'].update(point_type=actual_point.objectType, is_uniform=feature.isUniform,
                    scale_factor=feature.scaleFactor.value,
                    input_entities=[{'entity_type': entity.objectType, 'name': getattr(entity, 'name', None)} for entity in feature.inputEntities])
                if actual_vertex is None: raise RuntimeError('Actual Scale.point getter is not BRepVertex')
                sample['actual']['source_vertex'] = vertex_truth(actual_vertex, 'actual_scale_vertex')
            design.timeline.moveToEnd()
            sample['parameters'] = [{'name': p.name, 'role': p.role, 'value': p.value, 'unit': p.unit} for p in component.modelParameters]
            sample['root_bodies_after'] = [body_truth(b, 'root_after') for b in component.bRepBodies]
            sample['status'] = 'exporting'; save()
            options = design.exportManager.createFusionArchiveExportOptions(str(output/sample['file']))
            if not design.exportManager.execute(options): raise RuntimeError('Owned vertex probe export failed')
            sample['status'] = 'exported'; save()
        except Exception:
            sample['status'] = 'error'; report['errors'].append({'case': case, 'error': traceback.format_exc()}); save()
        finally:
            if document is not None:
                try:
                    design = adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))
                    if design: design.timeline.moveToEnd()
                    sample['close_owned_document_result'] = document.close(False)
                except Exception:
                    sample['getter_errors'].append({'field': 'close_owned_document', 'error': traceback.format_exc()})
            save()
    report['status'] = 'complete'; save()
    (output/'complete.txt').write_text('Named vertex probe finished; inspect actual samples/errors.\n')
