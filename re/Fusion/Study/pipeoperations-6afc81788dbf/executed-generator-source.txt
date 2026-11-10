"""Owned straight-sketch Pipe Join/Cut/Intersect through one explicit target.

All source and participant identities are API getters, with opaque tokens.
Join target inference is distinct from documented Cut/Intersect participant
selection; no serialized target role or native operation code is assumed.
"""
import hashlib
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CASES=('join','cut','intersect')


def run(context):
    app=adsk.core.Application.get();root=Path(__file__).resolve().parent
    output=root/('pipeoperations-'+uuid.uuid4().hex[:12]);output.mkdir()
    source=Path(__file__).read_bytes();(output/'executed-generator-source.txt').write_bytes(source)
    cases=context.get('cases',CASES) if isinstance(context,dict) else CASES
    if not isinstance(cases,(tuple,list)) or any(c not in CASES for c in cases):raise ValueError('Unknown Pipe operation case')
    truth={'status':'running','fusion_version':app.version,'samples':[],'errors':[],
        'executed_generator_sha256':hashlib.sha256(source).hexdigest(),
        'SDK_scope':'PipeFeatures.createInput(path,operation); circular sectionSize real internal cm; participantBodies applies to Cut/Intersect only; actual path/participants read after rollback before feature.',
        'identity_scope':'Requested source geometry/target identities retained independently; no native code, ASM identity or tool/target role inferred from coordinate coincidence'}
    def save(event):
        (output/'ground_truth.json').write_text(json.dumps(truth,indent=2)+'\n')
        (output/'progress.json').write_text(json.dumps({'status':truth['status'],'samples':[{'case':s['case'],'status':s['status']} for s in truth['samples']],'errors':len(truth['errors'])},indent=2)+'\n')
        with (output/'journal.jsonl').open('a') as handle:handle.write(json.dumps(event)+'\n')
    save({'event':'started','cases':list(cases)})
    for case in cases:
        sample={'case':case,'file':case+'.f3d','status':'creating_document','getter_errors':[],
            'requested':{'operation':case,'section_type':'Circular','section_size_cm':.6,'is_hollow':False,'distance_one':1.,
                'path_start_cm':[-1.,0.,0.],'path_end_cm':[4.,0.,0.],'target_bounds_min_cm':[0.,-1.,-1.],'target_bounds_max_cm':[3.,1.,1.],
                'explicit_participant_bodies_set':case in ('cut','intersect')}}
        truth['samples'].append(sample);document=None;design=None;save({'event':'case_started','case':case})
        try:
            document=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design=adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))
            design.designType=adsk.fusion.DesignTypes.ParametricDesignType;component=design.rootComponent
            point=adsk.core.Point3D.create;value=adsk.core.ValueInput.createByReal
            def read(label,callback):
                try:return callback()
                except Exception:
                    sample['getter_errors'].append({'field':label,'error':traceback.format_exc()});return {'getter_failed':True}
            def body_truth(body,label):
                return {'entity_type':body.objectType,'name':body.name,'entity_token':read(label+'.entityToken',lambda:body.entityToken),
                    'is_solid':body.isSolid,'face_count':body.faces.count,'edge_count':body.edges.count,'vertex_count':body.vertices.count,'volume_cm3':body.volume,
                    'bounds_min_cm':list(body.boundingBox.minPoint.asArray()),'bounds_max_cm':list(body.boundingBox.maxPoint.asArray())}
            def parameter(p):
                if p is None:return {'getter_returned_null':True}
                return {'entity_type':p.objectType,'name':p.name,'role':p.role,'raw_value':p.value,'unit':p.unit,'expression':p.expression,
                    'created_by':read('parameter.createdBy',lambda:getattr(p.createdBy,'name',None))}
            def geometry(geom):
                evaluator=geom.evaluator;ok,low,high=evaluator.getParameterExtents()
                result={'entity_type':geom.objectType,'parameter_extents_returned':ok,'parameter_extents':[low,high],'samples':[]}
                if ok:
                    for fraction in (0.,.5,1.):
                        u=low+(high-low)*fraction;accepted,p=evaluator.getPointAtParameter(u)
                        result['samples'].append({'fraction':fraction,'parameter':u,'returned':accepted,'point_cm':list(p.asArray()) if accepted else None})
                return result
            def curve_truth(curve):
                result={'entity_type':curve.objectType,'entity_token':read('curve.entityToken',lambda:curve.entityToken)}
                selected=adsk.fusion.SketchCurve.cast(curve)
                if selected:
                    result.update(sketch_name=selected.parentSketch.name,sketch_token=read('curve.sketchToken',lambda:selected.parentSketch.entityToken),
                        natural_world_geometry=geometry(selected.worldGeometry))
                    line=adsk.fusion.SketchLine.cast(selected)
                    if line:result.update(start_world_cm=list(line.startSketchPoint.worldGeometry.asArray()),end_world_cm=list(line.endSketchPoint.worldGeometry.asArray()))
                return result
            def path_truth(path):
                if path is None:return {'getter_returned_null':True}
                return {'entity_type':path.objectType,'count':path.count,'is_closed':path.isClosed,'members':[
                    {'index':i,'is_opposed_to_entity':path.item(i).isOpposedToEntity,'entity':curve_truth(path.item(i).entity),
                        'path_curve_geometry':geometry(path.item(i).curve)} for i in range(path.count)]}
            plane_input=component.constructionPlanes.createInput()
            if not plane_input.setByOffset(component.xYConstructionPlane,value(-1.)):raise RuntimeError('Target base plane rejected')
            plane=component.constructionPlanes.add(plane_input);plane.name='PipeTargetBasePlane'
            sketch=component.sketches.add(plane);sketch.name='PipeTargetProfile'
            sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0.,-1.,0.),point(3.,1.,0.))
            seed=component.features.extrudeFeatures.addSimple(sketch.profiles.item(0),value(2.),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            seed.name='PipeTargetExtrude';target=seed.bodies.item(0);target.name='PipeOperationTarget'
            path_sketch=component.sketches.add(component.xYConstructionPlane);path_sketch.name='PipeOperationPathSketch'
            line=path_sketch.sketchCurves.sketchLines.addByTwoPoints(point(-1.,0.,0.),point(4.,0.,0.))
            path=adsk.fusion.Path.create(line,adsk.fusion.ChainedCurveOptions.noChainedCurves)
            if path is None:raise RuntimeError('Owned Pipe path creation failed')
            sample['source_before_pipe']={'path':path_truth(path),'target_body':body_truth(target,'target_before')}
            operation={'join':adsk.fusion.FeatureOperations.JoinFeatureOperation,'cut':adsk.fusion.FeatureOperations.CutFeatureOperation,
                'intersect':adsk.fusion.FeatureOperations.IntersectFeatureOperation}[case]
            inputs=component.features.pipeFeatures.createInput(path,operation)
            if inputs is None:raise RuntimeError('Pipe operation input returned null')
            inputs.sectionType=adsk.fusion.PipeSectionTypes.CircularPipeSectionType;inputs.sectionSize=value(.6);inputs.isHollow=False;inputs.distanceOne=value(1.)
            if case in ('cut','intersect'):inputs.participantBodies=[target]
            sample['actual_input_before_add']={'operation':int(inputs.operation),'section_type':int(inputs.sectionType),'is_hollow':inputs.isHollow,
                'section_size_real':inputs.sectionSize.realValue,'distance_one_real':inputs.distanceOne.realValue,
                'participant_bodies':read('input.participantBodies',lambda:[body_truth(b,'input_participant') for b in inputs.participantBodies]) if case in ('cut','intersect') else {'applicable':False,'scope':'Documented participant property applies to Cut/Intersect; Join inference left to Fusion'}}
            sample['status']='adding_pipe';save({'event':'adding_pipe','case':case})
            feature=component.features.pipeFeatures.add(inputs)
            if feature is None:raise RuntimeError('Pipe operation add returned null')
            feature.name='ProbePipeOperation_'+case;sample['compute_all_returned']=design.computeAll()
            sample['health_state']=feature.healthState;sample['warning']=feature.errorOrWarningMessage
            sample['result_bodies']=[body_truth(b,'result') for b in feature.bodies]
            sample['root_bodies_after']=[body_truth(b,'root_result') for b in component.bRepBodies]
            feature.timelineObject.rollTo(True)
            sample['settings']={'operation':int(feature.operation),'section_type':int(feature.sectionType),'is_hollow':feature.isHollow,
                'section_size':parameter(feature.sectionSize),'section_thickness':parameter(feature.sectionThickness),
                'distance_one':parameter(feature.distanceOne),'distance_two':parameter(feature.distanceTwo),'path':path_truth(feature.path),
                'participant_bodies':read('feature.participantBodies',lambda:[body_truth(b,'actual_participant') for b in feature.participantBodies]) if case in ('cut','intersect') else {'applicable':False,'scope':'No inactive Join participant getter called'}}
            design.timeline.moveToEnd();sample['parameters']=[parameter(p) for p in component.modelParameters]
            sample['status']='exporting';save({'event':'exporting','case':case})
            options=design.exportManager.createFusionArchiveExportOptions(str(output/sample['file']))
            if not design.exportManager.execute(options):raise RuntimeError('Pipe operation export failed')
            sample['status']='exported';save({'event':'exported','case':case})
        except Exception:
            sample['status']='error';truth['errors'].append({'case':case,'error':traceback.format_exc()});save({'event':'case_error','case':case})
        finally:
            if document is not None:
                try:
                    if design is not None:design.timeline.moveToEnd()
                    sample['close_owned_document_result']=document.close(False)
                except Exception:sample['getter_errors'].append({'field':'close_owned_document','error':traceback.format_exc()})
            save({'event':'case_finished','case':case,'status':sample['status']})
    truth['status']='complete';save({'event':'complete'})
    (output/'complete.txt').write_text('Pipe operation contrasts finished; inspect actual results/errors.\n')
