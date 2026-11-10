"""Owned asymmetric-fillet flip and swapped-offset contrasts using public API.

SDK isFlipped reverses offset directions. Source geometry is captured before
consumption and under rollback; no native/ASM orientation is assigned here.
"""
import hashlib
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CONFIGS = {
    'unequal_default_false': {'offset_one_cm': .12, 'offset_two_cm': .28, 'is_flipped': False},
    'unequal_flipped_true': {'offset_one_cm': .12, 'offset_two_cm': .28, 'is_flipped': True},
    'swapped_offsets_false': {'offset_one_cm': .28, 'offset_two_cm': .12, 'is_flipped': False},
}
CASES = tuple(CONFIGS)


def run(context):
    app = adsk.core.Application.get(); root = Path(__file__).resolve().parent
    output = root/('asymmetricfilletflips-'+uuid.uuid4().hex[:12]); output.mkdir()
    generator_source=Path(__file__).read_bytes()
    (output/'executed-generator-source.txt').write_bytes(generator_source)
    cases = context.get('cases', CASES) if isinstance(context, dict) else CASES
    if not isinstance(cases, (tuple, list)) or any(case not in CONFIGS for case in cases):
        raise ValueError('Unknown asymmetric-fillet flip cases')
    truth = {'fusion_version': app.version, 'samples': [], 'errors': [], 'status': 'running',
        'executed_generator_sha256':hashlib.sha256(generator_source).hexdigest(),
        'SDK_scope': 'AsymmetricFilletEdgeSetInput.isFlipped reverses offsetOne/offsetTwo directions; AsymmetricFilletEdgeSet.isFlipped requires timeline immediately before feature. Offsets are cm for real ValueInputs.',
        'identity_scope': 'Actual API source getters retained before fillet consumes the edge and after rollback; no serialized native/ASM identity or orientation assigned by this generator'}

    def save(event=None):
        (output/'ground_truth.json').write_text(json.dumps(truth, indent=2)+'\n')
        (output/'progress.json').write_text(json.dumps({'status':truth['status'],'samples':[
            {'case':sample['case'],'status':sample['status']} for sample in truth['samples']],'errors':len(truth['errors'])}, indent=2)+'\n')
        if event:
            with (output/'journal.jsonl').open('a') as journal: journal.write(json.dumps(event)+'\n')

    save({'event':'started','cases':list(cases)})
    for case in cases:
        requested = {**CONFIGS[case], 'is_tangent_chain':False,'rolling_ball_corner':True,
                     'source_selection':'First edge of seed endFaces.item(0); fixture construction only'}
        sample = {'case':case,'file':case+'.f3d','requested':requested,'status':'creating_document','getter_errors':[]}
        truth['samples'].append(sample); document = None; design = None; save({'event':'case_started','case':case})
        try:
            document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType; component = design.rootComponent
            point = adsk.core.Point3D.create; value = adsk.core.ValueInput.createByReal

            def read(field, callback):
                try: return callback()
                except Exception:
                    sample['getter_errors'].append({'field':field,'error':traceback.format_exc()})
                    return None

            def parameter(item, label):
                if item is None: return {'getter_returned_null':True}
                return {'entity_type':item.objectType,'name':item.name,'role':item.role,'raw_value':item.value,
                        'unit':item.unit,'expression':item.expression,
                        'created_by':read(label+'.created_by',lambda:getattr(item.createdBy,'name',None))}

            def body_truth(body, label):
                return {'entity_type':body.objectType,'name':body.name,'is_solid':body.isSolid,
                        'entity_token':read(label+'.token',lambda:body.entityToken),
                        'face_count':body.faces.count,'edge_count':body.edges.count,'vertex_count':body.vertices.count,
                        'volume_cm3':body.volume,'bounds_min_cm':list(body.boundingBox.minPoint.asArray()),
                        'bounds_max_cm':list(body.boundingBox.maxPoint.asArray())}

            def edge_truth(edge, label):
                result = {'entity_type':edge.objectType,
                    'entity_token':read(label+'.token',lambda:edge.entityToken),
                    'temporary_id':read(label+'.temp_id',lambda:edge.tempId),
                    'body':body_truth(edge.body,label+'.body'),'geometry_type':edge.geometry.objectType,
                    'is_param_reversed':edge.isParamReversed,
                    'start_vertex_cm':list(edge.startVertex.geometry.asArray()),
                    'end_vertex_cm':list(edge.endVertex.geometry.asArray()),
                    'incident_face_geometry_types':[face.geometry.objectType for face in edge.faces]}
                evaluator = edge.evaluator; accepted, low, high = evaluator.getParameterExtents()
                result['trimmed_evaluator_extent_returned'] = accepted
                result['trimmed_parameter_extents'] = [low,high]
                result['trimmed_evaluator_samples'] = []
                if accepted:
                    for fraction in (0.,.25,.5,.75,1.):
                        u = low+(high-low)*fraction
                        ok, position = evaluator.getPointAtParameter(u)
                        result['trimmed_evaluator_samples'].append({'parameter_fraction':fraction,'parameter':u,
                            'returned':ok,'point_cm':list(position.asArray()) if ok else None})
                return result

            sketch = component.sketches.add(component.xYConstructionPlane); sketch.name = 'AsymmetricFilletSeedProfile'
            sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(1,1,0),point(5,4,0))
            seed = component.features.extrudeFeatures.addSimple(sketch.profiles.item(0),value(2.),
                                                               adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            seed.name = 'AsymmetricFilletSeedExtrude'; seed.bodies.item(0).name = 'AsymmetricFilletSeedBody'
            top = seed.endFaces.item(0); selected = top.edges.item(0)
            sample['selected_source_edge_before_fillet'] = edge_truth(selected,'source_before')
            if adsk.core.Line3D.cast(selected.geometry) is None:
                raise RuntimeError('Controlled selected source must be a straight BRepEdge')
            entities = adsk.core.ObjectCollection.create(); entities.add(selected)
            inputs = component.features.filletFeatures.createInput(); inputs.isRollingBallCorner = True
            edge_input = inputs.edgeSetInputs.addAsymmetricRadiusEdgeSet(entities,
                value(requested['offset_one_cm']),value(requested['offset_two_cm']),False)
            if edge_input is None: raise RuntimeError('Asymmetric-radius edge-set input returned null')
            sample['input_default_is_flipped_before_set'] = edge_input.isFlipped
            edge_input.isFlipped = requested['is_flipped']
            sample['actual_input'] = {'edge_set_type':edge_input.objectType,
                'offset_one_value_input_real':edge_input.offsetOne.realValue,
                'offset_two_value_input_real':edge_input.offsetTwo.realValue,
                'is_flipped':edge_input.isFlipped,
                'continuity':int(edge_input.continuity),'entity_count':edge_input.entities.count,
                'entity_types':[entity.objectType for entity in edge_input.entities]}
            sample['status']='adding_fillet';save({'event':'adding_fillet','case':case})
            feature = component.features.filletFeatures.add(inputs)
            if feature is None: raise RuntimeError('Asymmetric Fillet add returned null')
            feature.name = 'ProbeAsymmetricFilletFlip'
            sample['compute_all_returned'] = design.computeAll()
            sample['health_state'] = feature.healthState; sample['warning'] = feature.errorOrWarningMessage
            sample['result_bodies'] = [body_truth(body,'result_body') for body in feature.bodies]
            sample['root_body_count'] = component.bRepBodies.count
            sample['status']='reading_actual_getters';save({'event':'reading_actual_getters','case':case})
            feature.timelineObject.rollTo(True)
            settings = {'feature_type':feature.objectType,'feature_name':feature.name,
                'rolling_ball_corner':feature.isRollingBallCorner,'fillet_feature_type':int(feature.filletFeatureType),
                'edge_sets':[]}
            for index in range(feature.edgeSets.count):
                edge_set = adsk.fusion.AsymmetricFilletEdgeSet.cast(feature.edgeSets.item(index))
                if edge_set is None: raise RuntimeError('Actual feature edge set is not AsymmetricFilletEdgeSet')
                entry = {'index':index,'entity_type':edge_set.objectType,'is_tangent_chain':edge_set.isTangentChain,
                    'continuity':int(edge_set.continuity),
                    'offset_one':parameter(edge_set.offsetOne,'offset_one'),
                    'offset_two':parameter(edge_set.offsetTwo,'offset_two'),
                    'is_flipped':edge_set.isFlipped,
                    'tangency_weight':parameter(edge_set.tangencyWeight,'tangency_weight'),
                    'actual_source_edges':[edge_truth(edge_set.edges.item(i),'actual_source.'+str(i)) for i in range(edge_set.edges.count)]}
                settings['edge_sets'].append(entry)
            sample['settings'] = settings
            design.timeline.moveToEnd()
            sample['parameters'] = [parameter(p,'model_parameter') for p in component.modelParameters]
            sample['status']='exporting';save({'event':'exporting','case':case})
            options = design.exportManager.createFusionArchiveExportOptions(str(output/sample['file']))
            if not design.exportManager.execute(options): raise RuntimeError('Asymmetric Fillet export failed')
            sample['status']='exported';save({'event':'exported','case':case})
        except Exception:
            sample['status']='error';truth['errors'].append({'case':case,'error':traceback.format_exc()});save({'event':'case_error','case':case})
        finally:
            if document is not None:
                try:
                    if design is not None: design.timeline.moveToEnd()
                    sample['close_owned_document_result'] = document.close(False)
                except Exception:
                    sample['getter_errors'].append({'field':'close_owned_document','error':traceback.format_exc()})
            save({'event':'case_finished','case':case,'status':sample['status']})
    truth['status']='complete';save({'event':'complete'})
    (output/'complete.txt').write_text('Asymmetric Fillet flip contrasts finished; inspect actual samples/errors.\n')
