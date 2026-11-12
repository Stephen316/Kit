"""Prepared public RemoveFeatures.add body/root/nested occurrence contrasts.

Every case owns a fresh document. Source, rolled-back itemToRemove and final
collections are independent API observations; removal target provenance is not
inferred from final visibility, collection order or missing entities.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CASES=('root_body','root_occurrence','nested_occurrence')
OUTPUT_PREFIX='removecontrasts-'


def run(context):
    app=adsk.core.Application.get();batch_id=uuid.uuid4().hex[:12]
    output=Path(__file__).resolve().parent/(OUTPUT_PREFIX+batch_id);output.mkdir()
    source=Path(__file__).read_bytes();(output/'executed-generator-source.txt').write_bytes(source)
    truth=dict(batch_id=batch_id,fusion_version=app.version,samples=[],errors=[],requested_cases=list(CASES),
        executed_generator_sha256=hashlib.sha256(source).hexdigest(),
        execution_scope='Three new owned parametric documents; local native export and closeFalse only; no global settings or existing document changes',
        API_scope='Documented RemoveFeatures.add(single solid body or component occurrence); itemToRemove read only while timeline is immediately before owned RemoveFeature',
        evidence_scope='Named requested source before removal, rolled-back actual itemToRemove, independent before/rolled-back/after collections and feature getters. Current collection absence does not assign persistent native identity or general lifecycle semantics.')
    cases=context.get('cases',CASES) if isinstance(context,dict) else CASES
    for case in cases:
        doc=design=None
        sample=dict(case=case,file=case+'.f3d',getter_errors=[])
        def persist():
            (output/'ground_truth.json').write_text(json.dumps(truth,indent=2)+'\n')
        def journal(phase,**fields):
            event=dict(time_utc=datetime.now(timezone.utc).isoformat(),batch_id=batch_id,case=case,
                phase=phase,completed=len(truth['samples']),error_count=len(truth['errors']),**fields)
            with (output/'journal.jsonl').open('a') as stream:stream.write(json.dumps(event)+'\n')
            (output/'progress.json').write_text(json.dumps(event,indent=2)+'\n');truth['active_sample']=sample;persist()
        def observe(label,getter):
            try:return getter()
            except Exception:
                sample['getter_errors'].append(dict(field=label,error=traceback.format_exc()))
                journal('getter_error',field=label);return None
        def body_truth(body,label):
            if body is None:return dict(status='returned_null')
            return dict(status='returned_body',entity_type=observe(label+'.objectType',lambda:body.objectType),
                name=observe(label+'.name',lambda:body.name),entity_token=observe(label+'.entityToken',lambda:body.entityToken),
                component_name=observe(label+'.parentComponent.name',lambda:body.parentComponent.name),
                assembly_context_path=observe(label+'.assemblyContext',lambda:body.assemblyContext.fullPathName if body.assemblyContext else None),
                is_solid=observe(label+'.isSolid',lambda:body.isSolid),
                bounding_box_cm=observe(label+'.boundingBox',lambda:dict(min=body.boundingBox.minPoint.asArray(),max=body.boundingBox.maxPoint.asArray())))
        def occurrence_truth(occurrence,label):
            if occurrence is None:return dict(status='returned_null')
            bodies=observe(label+'.bRepBodies',lambda:occurrence.bRepBodies)
            return dict(status='returned_occurrence',entity_type=observe(label+'.objectType',lambda:occurrence.objectType),
                name=observe(label+'.name',lambda:occurrence.name),full_path_name=observe(label+'.fullPathName',lambda:occurrence.fullPathName),
                component_name=observe(label+'.component.name',lambda:occurrence.component.name),
                entity_token=observe(label+'.entityToken',lambda:occurrence.entityToken),
                transform=observe(label+'.transform2',lambda:occurrence.transform2.asArray()),
                assembly_context_path=observe(label+'.assemblyContext',lambda:occurrence.assemblyContext.fullPathName if occurrence.assemblyContext else None),
                native_object_token=observe(label+'.nativeObject.entityToken',lambda:occurrence.nativeObject.entityToken if occurrence.nativeObject else None),
                native_object_transform=observe(label+'.nativeObject.transform2',lambda:occurrence.nativeObject.transform2.asArray() if occurrence.nativeObject else None),
                bodies=[body_truth(b,label+'.bodies['+str(i)+']') for i,b in enumerate(bodies)] if bodies is not None else None)
        def entity_truth(entity,label):
            if entity is None:return dict(status='returned_null')
            occurrence=adsk.fusion.Occurrence.cast(entity)
            if occurrence is not None:return occurrence_truth(occurrence,label)
            body=adsk.fusion.BRepBody.cast(entity)
            if body is not None:return body_truth(body,label)
            return dict(status='unanticipated_type',entity_type=observe(label+'.objectType',lambda:entity.objectType))
        def component_truth(component,label):
            bodies=observe(label+'.bRepBodies',lambda:component.bRepBodies)
            occurrences=observe(label+'.occurrences',lambda:component.occurrences)
            return dict(name=observe(label+'.name',lambda:component.name),
                body_count=observe(label+'.bRepBodies.count',lambda:component.bRepBodies.count),
                occurrence_count=observe(label+'.occurrences.count',lambda:component.occurrences.count),
                bodies=[body_truth(b,label+'.bodies['+str(i)+']') for i,b in enumerate(bodies)] if bodies is not None else None,
                occurrences=[occurrence_truth(o,label+'.occurrences['+str(i)+']') for i,o in enumerate(occurrences)] if occurrences is not None else None)
        def root_collections(root,label):
            all_occurrences=observe(label+'.allOccurrences',lambda:root.allOccurrences)
            return dict(root=component_truth(root,label+'.root'),
                all_occurrences=[occurrence_truth(o,label+'.all_occurrences['+str(i)+']') for i,o in enumerate(all_occurrences)] if all_occurrences is not None else None,
                all_occurrence_count=observe(label+'.allOccurrences.count',lambda:root.allOccurrences.count))
        def parameters(root,label):
            return observe(label,lambda:[dict(name=p.name,role=p.role,value=p.value,unit=p.unit,expression=p.expression,
                created_by=p.createdBy.name if p.createdBy else None) for p in root.modelParameters])
        try:
            if case not in CASES:raise ValueError('Unknown bounded RemoveFeature case')
            journal('document_create_begin')
            doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            design.designType=adsk.fusion.DesignTypes.ParametricDesignType;root=design.rootComponent
            point,value=adsk.core.Point3D.create,adsk.core.ValueInput.createByReal
            def box(component,name,x=0.):
                sketch=component.sketches.add(component.xYConstructionPlane);sketch.name=name+'Profile'
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(x,0,0),point(x+1,1,0))
                feature=component.features.extrudeFeatures.addSimple(sketch.profiles.item(0),value(1.),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                feature.name=name+'Extrude';body=feature.bodies.item(0);body.name=name+'Body';return body
            def occurrence(component,name,translation,with_body=True):
                matrix=adsk.core.Matrix3D.create();matrix.translation=adsk.core.Vector3D.create(*translation)
                result=component.occurrences.addNewComponent(matrix);result.component.name=name
                if with_body:box(result.component,name)
                return result
            parent=None
            if case=='root_body':
                target=box(root,'RemoveTarget');box(root,'RemoveSurvivor',4.)
                target_component=root
            elif case=='root_occurrence':
                target=occurrence(root,'RemoveTargetComponent',(2.,1.,0.))
                occurrence(root,'RemoveSurvivorComponent',(6.,-1.,2.));target_component=target.component
            else:
                parent=occurrence(root,'RemoveParentComponent',(2.,3.,1.),False)
                child=occurrence(parent.component,'RemoveTargetChild',(4.,-1.,2.))
                target=child.createForAssemblyContext(parent)
                if target is None:raise RuntimeError('Documented nested occurrence assembly proxy returnedNone')
                occurrence(root,'RemoveSurvivorComponent',(7.,0.,0.));target_component=child.component
                sample['requested_native_child_before']=occurrence_truth(child,'requested_native_child_before')
                sample['requested_parent_before']=occurrence_truth(parent,'requested_parent_before')
            sample['compute_before']=observe('design.computeAll.before',lambda:design.computeAll())
            sample['requested_target_before']=entity_truth(target,'requested_target_before')
            sample['collections_before']=root_collections(root,'before')
            sample['source_component_before']=component_truth(target_component,'source_component_before')
            sample['parameters_before']=parameters(root,'root.modelParameters.before')
            journal('remove_add_begin')
            feature=root.features.removeFeatures.add(target)
            if feature is None:raise RuntimeError('RemoveFeatures.add returnedNone')
            feature.name='ProbeRemove'+case.title().replace('_','');journal('remove_added')
            feature.timelineObject.rollTo(True);journal('rolled_back_before_remove')
            item=observe('feature.itemToRemove.rolled_back',lambda:feature.itemToRemove)
            sample['actual_item_to_remove']=entity_truth(item,'actual_item_to_remove')
            sample['collections_rolled_back']=root_collections(root,'rolled_back')
            design.timeline.moveToEnd();journal('timeline_restored_after_remove')
            sample['compute_after']=observe('design.computeAll.after',lambda:design.computeAll())
            sample['feature_identity']=dict(name=feature.name,entity_type=feature.objectType,
                entity_token=observe('feature.entityToken',lambda:feature.entityToken),
                timeline_index=observe('feature.timelineObject.index',lambda:feature.timelineObject.index),
                parent_component_name=observe('feature.parentComponent.name',lambda:feature.parentComponent.name))
            sample['is_suppressed']=observe('feature.isSuppressed',lambda:feature.isSuppressed)
            sample['health_state']=observe('feature.healthState',lambda:int(feature.healthState))
            sample['warning']=observe('feature.errorOrWarningMessage',lambda:feature.errorOrWarningMessage)
            feature_bodies=observe('feature.bodies',lambda:feature.bodies)
            sample['actual_feature_bodies']=[body_truth(b,'feature.bodies['+str(i)+']') for i,b in enumerate(feature_bodies)] if feature_bodies is not None else None
            sample['collections_after']=root_collections(root,'after')
            sample['source_component_after']=component_truth(target_component,'source_component_after')
            if parent is not None:sample['parent_component_after']=component_truth(parent.component,'parent_component_after')
            sample['parameters_after']=parameters(root,'root.modelParameters.after')
            sample['remove_feature_count']=root.features.removeFeatures.count
            sample['remove_feature_names']=[f.name for f in root.features.removeFeatures]
            design.timeline.moveToEnd();destination=output/sample['file'];journal('export_begin')
            succeeded=design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(destination)))
            if not succeeded or not destination.is_file() or not destination.stat().st_size:raise RuntimeError('Local RemoveFeature export failed')
            sample['export']=dict(returned_success=bool(succeeded),byte_count=destination.stat().st_size,
                sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
            truth['samples'].append(sample);journal('export_complete')
        except Exception:
            truth['errors'].append(dict(case=case,error=traceback.format_exc(),partial_capture=sample));journal('case_failed')
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
    (output/'complete.txt').write_text('RemoveFeature contrasts terminal: '+truth['terminal_status']+'; inspect case/getter errors.\n')
