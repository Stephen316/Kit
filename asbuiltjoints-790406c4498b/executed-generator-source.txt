"""Prepared journaled AsBuiltJoint Rigid/Revolute/Slider contrasts.

Each case creates a fresh owned root document, two translated component
occurrences with simple bodies, and one documented AsBuiltJoint. Stored/API
placements are snapshots, not evidence of a general assembly solver.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CASES=('rigid','revolute','slider')
OUTPUT_PREFIX='asbuiltjoints-'


def run(context):
    app=adsk.core.Application.get()
    batch_id=uuid.uuid4().hex[:12]
    output=Path(__file__).resolve().parent/(OUTPUT_PREFIX+batch_id)
    output.mkdir()
    generator_source=Path(__file__).read_bytes()
    (output/'executed-generator-source.txt').write_bytes(generator_source)
    truth=dict(batch_id=batch_id,fusion_version=app.version,samples=[],errors=[],requested_cases=list(CASES),
        executed_generator_sha256=hashlib.sha256(generator_source).hexdigest(),
        execution_scope='At most three fresh owned parametric documents; two owned component occurrences each; local exports/closeFalse; no global settings or user document edits',
        placement_scope='Actual occurrence transform snapshots before/after joint creation and limit edits; no assumption that native caches are solved world placements',
        API_scope='AsBuiltJoints.createInput(occurrenceOne,occurrenceTwo,geometry), null geometry for Rigid; documented JointGeometry component-origin ConstructionPoint proxy for Revolute/Slider',
        omitted_getters={'isLocked':'Not exposed by the installed AsBuiltJoint API',
            'angle/offset/isFlipped':'Ordinary Joint alignment getters are not exposed by AsBuiltJoint',
            'healthState/errorOrWarningMessage':'Captured on documented timelineObject instead of invented AsBuiltJoint feature properties'})
    cases=context.get('cases',CASES) if isinstance(context,dict) else CASES
    for case in cases:
        doc=design=None
        sample=dict(case=case,file=case+'.f3d',getter_errors=[],setter_errors=[])
        def persist():
            (output/'ground_truth.json').write_text(json.dumps(truth,indent=2)+'\n')
        def journal(phase,**fields):
            event=dict(time_utc=datetime.now(timezone.utc).isoformat(),batch_id=batch_id,case=case,
                phase=phase,completed=len(truth['samples']),error_count=len(truth['errors']),**fields)
            with (output/'journal.jsonl').open('a') as stream:stream.write(json.dumps(event)+'\n')
            (output/'progress.json').write_text(json.dumps(event,indent=2)+'\n')
            truth['active_sample']=sample;persist()
        def observe(label,getter):
            try:return getter()
            except Exception:
                sample['getter_errors'].append(dict(field=label,error=traceback.format_exc()))
                journal('getter_error',field=label)
                return None
        def set_value(label,setter):
            try:setter();return True
            except Exception:
                sample['setter_errors'].append(dict(field=label,error=traceback.format_exc()))
                journal('setter_error',field=label)
                return False
        def entity_truth(entity,label):
            if entity is None:return dict(status='returned_null')
            result=dict(status='returned_entity',entity_type=observe(label+'.objectType',lambda:entity.objectType),
                name=observe(label+'.name',lambda:entity.name),entity_token=observe(label+'.entityToken',lambda:entity.entityToken))
            point=adsk.fusion.ConstructionPoint.cast(entity)
            if point is not None:
                result.update(component_name=observe(label+'.component.name',lambda:point.component.name),
                    point_cm=observe(label+'.geometry',lambda:point.geometry.asArray()),
                    assembly_context_path=observe(label+'.assemblyContext',lambda:point.assemblyContext.fullPathName if point.assemblyContext else None),
                    native_object_token=observe(label+'.nativeObject.entityToken',lambda:point.nativeObject.entityToken if point.nativeObject else None))
            return result
        def geometry_truth(geometry,label):
            if geometry is None:return dict(status='returned_null')
            return dict(status='returned_geometry',geometry_type=observe(label+'.geometryType',lambda:int(geometry.geometryType)),
                key_point_type=observe(label+'.keyPointType',lambda:int(geometry.keyPointType)),
                origin_cm=observe(label+'.origin',lambda:geometry.origin.asArray()),
                primary_axis=observe(label+'.primaryAxisVector',lambda:geometry.primaryAxisVector.asArray()),
                secondary_axis=observe(label+'.secondaryAxisVector',lambda:geometry.secondaryAxisVector.asArray()),
                third_axis=observe(label+'.thirdAxisVector',lambda:geometry.thirdAxisVector.asArray()),
                entity_one=entity_truth(observe(label+'.entityOne',lambda:geometry.entityOne),label+'.entityOne'),
                entity_two=entity_truth(observe(label+'.entityTwo',lambda:geometry.entityTwo),label+'.entityTwo'))
        def body_truth(body,label):
            return dict(name=observe(label+'.name',lambda:body.name),entity_type=observe(label+'.objectType',lambda:body.objectType),
                entity_token=observe(label+'.entityToken',lambda:body.entityToken),
                bounding_box_cm=observe(label+'.boundingBox',lambda:dict(min=body.boundingBox.minPoint.asArray(),max=body.boundingBox.maxPoint.asArray())))
        def occurrence_truth(occurrence,label):
            if occurrence is None:return dict(status='returned_null')
            return dict(name=observe(label+'.name',lambda:occurrence.name),full_path_name=observe(label+'.fullPathName',lambda:occurrence.fullPathName),
                component_name=observe(label+'.component.name',lambda:occurrence.component.name),
                entity_token=observe(label+'.entityToken',lambda:occurrence.entityToken),
                transform=observe(label+'.transform2',lambda:occurrence.transform2.asArray()),
                is_grounded=observe(label+'.isGrounded',lambda:occurrence.isGrounded),
                body_count=observe(label+'.bRepBodies.count',lambda:occurrence.bRepBodies.count),
                bodies=[body_truth(body,label+'.bodies['+str(i)+']') for i,body in enumerate(occurrence.bRepBodies)])
        def motion_truth(joint,label):
            base=observe(label+'.jointMotion',lambda:joint.jointMotion)
            if base is None:return dict(status='returned_null_or_getter_error')
            classes={'revolute':adsk.fusion.RevoluteJointMotion,'slider':adsk.fusion.SliderJointMotion}
            motion=classes[case].cast(base) if case in classes else base
            if motion is None:raise RuntimeError('Actual AsBuilt motion cast does not match requested case')
            result=dict(entity_type=observe(label+'.motion.objectType',lambda:motion.objectType),
                joint_type=observe(label+'.jointType',lambda:int(motion.jointType)),directions={},vectors={},current_values={},limits={})
            if case!='rigid':
                direction,vector,current,limit=('rotationAxis','rotationAxisVector','rotationValue','rotationLimits') if case=='revolute' else ('slideDirection','slideDirectionVector','slideValue','slideLimits')
                result['directions'][direction]=observe(label+'.'+direction,lambda:int(getattr(motion,direction)))
                result['vectors'][vector]=observe(label+'.'+vector,lambda:getattr(motion,vector).asArray())
                result['current_values'][current]=observe(label+'.'+current,lambda:getattr(motion,current))
                limits=observe(label+'.'+limit,lambda:getattr(motion,limit))
                if limits is not None:
                    result['limits'][limit]={field:observe(label+'.'+limit+'.'+field,lambda field=field:getattr(limits,field)) for field in (
                        'minimumValue','maximumValue','restValue','isMinimumValueEnabled','isMaximumValueEnabled','isRestValueEnabled')}
            return result
        try:
            if case not in CASES:raise ValueError('Unknown bounded AsBuilt case')
            journal('document_create_begin')
            doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            design.designType=adsk.fusion.DesignTypes.ParametricDesignType
            root=design.rootComponent
            point,value=adsk.core.Point3D.create,adsk.core.ValueInput.createByReal
            occurrences=[]
            requested_translations=((1.,2.,0.),(4.,-1.,2.))
            for index,name in enumerate(('AsBuiltFixed','AsBuiltMoving')):
                matrix=adsk.core.Matrix3D.create();matrix.translation=adsk.core.Vector3D.create(*requested_translations[index])
                occurrence=root.occurrences.addNewComponent(matrix);occurrence.component.name=name
                sketch=occurrence.component.sketches.add(occurrence.component.xYConstructionPlane)
                sketch.name=name+'Profile'
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0,0,0),point(1,1,0))
                extrusion=occurrence.component.features.extrudeFeatures.addSimple(sketch.profiles.item(0),value(1.),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                extrusion.name=name+'Extrude';extrusion.bodies.item(0).name=name+'Body'
                occurrences.append(occurrence)
            occurrences[0].isGrounded=True
            sample['requested_translations_cm']=[list(v) for v in requested_translations]
            sample['compute_before']=observe('design.computeAll.before',lambda:design.computeAll())
            sample['occurrences_before']=[occurrence_truth(o,'before['+str(i)+']') for i,o in enumerate(occurrences)]
            geometry=None
            if case!='rigid':
                proxy=occurrences[1].component.originConstructionPoint.createForAssemblyContext(occurrences[1])
                sample['requested_geometry_source']=entity_truth(proxy,'requested_geometry_source')
                geometry=adsk.fusion.JointGeometry.createByPoint(proxy)
                if geometry is None:raise RuntimeError('Documented origin ConstructionPoint JointGeometry rejected')
            else:sample['requested_geometry_source']=dict(status='not_used_for_rigid')
            sample['requested_joint_geometry']=geometry_truth(geometry,'requested_geometry')
            inputs=root.asBuiltJoints.createInput(occurrences[1],occurrences[0],geometry)
            if inputs is None:raise RuntimeError('AsBuiltJoints.createInput returnedNone')
            if case=='rigid':ok=inputs.setAsRigidJointMotion()
            elif case=='revolute':ok=inputs.setAsRevoluteJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
            else:ok=inputs.setAsSliderJointMotion(adsk.fusion.JointDirections.XAxisJointDirection)
            sample['motion_input_setter_returned']=bool(ok)
            if not ok:raise RuntimeError('AsBuilt motion input setter rejected')
            journal('joint_add_begin')
            joint=root.asBuiltJoints.add(inputs)
            if joint is None:raise RuntimeError('AsBuiltJoints.add returnedNone')
            joint.name='ProbeAsBuilt'+case.title()
            journal('joint_added')
            sample['occurrences_immediately_after_add']=[occurrence_truth(o,'immediately_after['+str(i)+']') for i,o in enumerate(occurrences)]
            sample['motion_before_limits']=motion_truth(joint,'motion_before_limits')
            if case!='rigid':
                motion=(adsk.fusion.RevoluteJointMotion if case=='revolute' else adsk.fusion.SliderJointMotion).cast(joint.jointMotion)
                limits=motion.rotationLimits if case=='revolute' else motion.slideLimits
                requested=dict(minimumValue=-.4 if case=='revolute' else -.8,maximumValue=1.1 if case=='revolute' else 1.8,
                    restValue=.2 if case=='revolute' else .3,isMinimumValueEnabled=True,isMaximumValueEnabled=case=='revolute',isRestValueEnabled=False)
                sample['requested_motion_limits']=requested
                sample['limit_setter_success']={field:set_value('limits.'+field,lambda field=field,setting=setting:setattr(limits,field,setting)) for field,setting in requested.items()}
            else:sample['requested_motion_limits']={}
            sample['compute_after']=observe('design.computeAll.after',lambda:design.computeAll())
            sample['feature_identity']=dict(name=joint.name,entity_type=joint.objectType,
                entity_token=observe('joint.entityToken',lambda:joint.entityToken),
                timeline_index=observe('joint.timelineObject.index',lambda:joint.timelineObject.index),
                parent_component_name=observe('joint.parentComponent.name',lambda:joint.parentComponent.name))
            sample['actual_occurrence_one']=occurrence_truth(observe('joint.occurrenceOne',lambda:joint.occurrenceOne),'actual_occurrence_one')
            sample['actual_occurrence_two']=occurrence_truth(observe('joint.occurrenceTwo',lambda:joint.occurrenceTwo),'actual_occurrence_two')
            sample['actual_joint_geometry']=geometry_truth(observe('joint.geometry',lambda:joint.geometry),'actual_geometry')
            sample['actual_joint_transform']=observe('joint.transform',lambda:joint.transform.asArray())
            sample['actual_motion']=motion_truth(joint,'actual_motion')
            sample['is_suppressed']=observe('joint.isSuppressed',lambda:joint.isSuppressed)
            sample['health_state']=observe('joint.timelineObject.healthState',lambda:int(joint.timelineObject.healthState))
            sample['warning']=observe('joint.timelineObject.errorOrWarningMessage',lambda:joint.timelineObject.errorOrWarningMessage)
            sample['occurrences_after']=[occurrence_truth(o,'after['+str(i)+']') for i,o in enumerate(occurrences)]
            sample['as_built_joint_count']=root.asBuiltJoints.count
            sample['as_built_joint_names']=[j.name for j in root.asBuiltJoints]
            sample['parameters']=observe('root.modelParameters',lambda:[dict(name=p.name,role=p.role,value=p.value,unit=p.unit,
                expression=p.expression,created_by=p.createdBy.name if p.createdBy else None) for p in root.modelParameters])
            design.timeline.moveToEnd()
            destination=output/sample['file'];journal('export_begin')
            succeeded=design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(destination)))
            if not succeeded or not destination.is_file() or not destination.stat().st_size:raise RuntimeError('Local AsBuilt export failed')
            sample['export']=dict(returned_success=bool(succeeded),byte_count=destination.stat().st_size,
                sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
            truth['samples'].append(sample);journal('export_complete')
        except Exception:
            truth['errors'].append(dict(case=case,error=traceback.format_exc(),partial_capture=sample))
            journal('case_failed')
        finally:
            if design is not None:
                try:design.timeline.moveToEnd()
                except Exception:sample['getter_errors'].append(dict(field='finally.restore_timeline',error=traceback.format_exc()))
            if doc is not None:
                try:
                    sample['close_owned_document_returned']=doc.close(False)
                    journal('owned_document_close_returned',save=False,returned=sample['close_owned_document_returned'])
                except Exception:sample['getter_errors'].append(dict(field='finally.closeFalse',error=traceback.format_exc()))
            truth.pop('active_sample',None);persist()
    truth['terminal_status']='complete' if len(truth['samples'])==len(cases) and not truth['errors'] else 'complete_with_errors'
    truth['exported_sample_count']=len(truth['samples'])
    (output/'ground_truth.json').write_text(json.dumps(truth,indent=2)+'\n')
    (output/'complete.txt').write_text('AsBuilt contrasts terminal: '+truth['terminal_status']+'; inspect case/getter/setter errors.\n')
