"""Prepared owned RigidGroup active/suppressed/nested membership contrasts.

Uses documented RigidGroups.add(occurrences, includeChildren). The installed API
has no includeChildren getter: request and actual returned membership remain
separate evidence. No live execution occurs until root invokes run().
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CASES=('root_active','root_suppressed','nested_include_children')
OUTPUT_PREFIX='rigidgroups-'


def run(context):
    app=adsk.core.Application.get()
    batch_id=uuid.uuid4().hex[:12]
    output=Path(__file__).resolve().parent/(OUTPUT_PREFIX+batch_id)
    output.mkdir()
    source=Path(__file__).read_bytes()
    (output/'executed-generator-source.txt').write_bytes(source)
    truth=dict(batch_id=batch_id,fusion_version=app.version,samples=[],errors=[],requested_cases=list(CASES),
        executed_generator_sha256=hashlib.sha256(source).hexdigest(),
        execution_scope='Three fresh owned parametric documents, local archives and closeFalse; no global settings or existing user document edits',
        evidence_scope='API requested selected occurrences/includeChildren and independent returned RigidGroup.occurrences; actual suppression and before/immediate-after/after source placements',
        placement_scope='API occurrence transforms are snapshots with explicit assemblyContext/nativeObject provenance; no solved native assembly placement inferred',
        omitted_getters={'includeChildren':'No public RigidGroup includeChildren getter in installed SDK; retain passed value and actual occurrence membership separately',
            'direct healthState/errorOrWarningMessage':'Use documented timelineObject health properties instead'})
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
                journal('getter_error',field=label);return None
        def body_truth(body,label):
            return dict(name=observe(label+'.name',lambda:body.name),
                entity_type=observe(label+'.objectType',lambda:body.objectType),
                entity_token=observe(label+'.entityToken',lambda:body.entityToken),
                bounding_box_cm=observe(label+'.boundingBox',lambda:dict(min=body.boundingBox.minPoint.asArray(),max=body.boundingBox.maxPoint.asArray())))
        def occurrence_truth(occurrence,label):
            if occurrence is None:return dict(status='returned_null')
            return dict(name=observe(label+'.name',lambda:occurrence.name),
                full_path_name=observe(label+'.fullPathName',lambda:occurrence.fullPathName),
                component_name=observe(label+'.component.name',lambda:occurrence.component.name),
                entity_token=observe(label+'.entityToken',lambda:occurrence.entityToken),
                transform=observe(label+'.transform2',lambda:occurrence.transform2.asArray()),
                assembly_context_path=observe(label+'.assemblyContext',lambda:occurrence.assemblyContext.fullPathName if occurrence.assemblyContext else None),
                native_object_token=observe(label+'.nativeObject.entityToken',lambda:occurrence.nativeObject.entityToken if occurrence.nativeObject else None),
                native_object_transform=observe(label+'.nativeObject.transform2',lambda:occurrence.nativeObject.transform2.asArray() if occurrence.nativeObject else None),
                body_count=observe(label+'.bRepBodies.count',lambda:occurrence.bRepBodies.count),
                bodies=[body_truth(b,label+'.bodies['+str(i)+']') for i,b in enumerate(occurrence.bRepBodies)])
        def all_occurrences(root,label):
            return [occurrence_truth(o,label+'['+str(i)+']') for i,o in enumerate(root.allOccurrences)]
        def group_truth(group,label):
            occurrences=observe(label+'.occurrences',lambda:group.occurrences)
            return dict(name=observe(label+'.name',lambda:group.name),
                entity_type=observe(label+'.objectType',lambda:group.objectType),
                entity_token=observe(label+'.entityToken',lambda:group.entityToken),
                parent_component_name=observe(label+'.parentComponent.name',lambda:group.parentComponent.name),
                is_suppressed=observe(label+'.isSuppressed',lambda:group.isSuppressed),
                timeline_index=observe(label+'.timelineObject.index',lambda:group.timelineObject.index),
                occurrences=[occurrence_truth(o,label+'.occurrences['+str(i)+']') for i,o in enumerate(occurrences)] if occurrences is not None else None,
                occurrence_count=observe(label+'.occurrences.count',lambda:group.occurrences.count),
                actual_include_children=None,include_children_status='Unavailable getter; requested add argument retained separately')
        try:
            if case not in CASES:raise ValueError('Unknown bounded RigidGroup case')
            journal('document_create_begin')
            doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            design.designType=adsk.fusion.DesignTypes.ParametricDesignType
            root=design.rootComponent
            point,value=adsk.core.Point3D.create,adsk.core.ValueInput.createByReal
            def add_occurrence(component,name,translation,with_body=True):
                matrix=adsk.core.Matrix3D.create();matrix.translation=adsk.core.Vector3D.create(*translation)
                occurrence=component.occurrences.addNewComponent(matrix);occurrence.component.name=name
                if with_body:
                    sketch=occurrence.component.sketches.add(occurrence.component.xYConstructionPlane)
                    sketch.name=name+'Profile'
                    sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0,0,0),point(1,1,0))
                    extrusion=occurrence.component.features.extrudeFeatures.addSimple(sketch.profiles.item(0),value(1.),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                    extrusion.name=name+'Extrude';extrusion.bodies.item(0).name=name+'Body'
                return occurrence
            first=add_occurrence(root,'RigidGroupFirst',(1.,2.,0.))
            if case=='nested_include_children':
                second=add_occurrence(root,'RigidGroupParent',(2.,3.,1.),False)
                child=add_occurrence(second.component,'RigidGroupChild',(4.,-1.,2.))
                sample['requested_nested_child_native']=occurrence_truth(child,'requested_child_native')
                sample['requested_local_translations_cm']=dict(first=[1.,2.,0.],parent=[2.,3.,1.],child=[4.,-1.,2.])
            else:
                second=add_occurrence(root,'RigidGroupSecond',(4.,-1.,2.))
                sample['requested_local_translations_cm']=dict(first=[1.,2.,0.],second=[4.,-1.,2.])
            sample['compute_before']=observe('design.computeAll.before',lambda:design.computeAll())
            sample['selected_occurrences_before']=[occurrence_truth(o,'selected_before['+str(i)+']') for i,o in enumerate((first,second))]
            sample['all_occurrences_before']=all_occurrences(root,'all_before')
            requested_include_children=case=='nested_include_children'
            sample['requested_include_children']=requested_include_children
            sample['requested_is_suppressed']=case=='root_suppressed'
            selected=adsk.core.ObjectCollection.create();selected.add(first);selected.add(second)
            journal('rigid_group_add_begin')
            group=root.rigidGroups.add(selected,requested_include_children)
            if group is None:raise RuntimeError('RigidGroups.add returnedNone')
            group.name='ProbeRigidGroup'+case.title().replace('_','')
            journal('rigid_group_added')
            sample['actual_group_initial']=group_truth(group,'group_initial')
            sample['all_occurrences_immediately_after_add']=all_occurrences(root,'all_immediately_after')
            if sample['requested_is_suppressed']:
                try:
                    group.isSuppressed=True
                    sample['suppression_setter_success']=True
                except Exception:
                    sample['suppression_setter_success']=False
                    sample['setter_errors'].append(dict(field='group.isSuppressed=True',error=traceback.format_exc()))
                    journal('suppression_setter_error')
            else:sample['suppression_setter_success']=None
            sample['compute_after']=observe('design.computeAll.after',lambda:design.computeAll())
            sample['actual_group_final']=group_truth(group,'group_final')
            sample['observed_suppression_matches_request']=sample['actual_group_final']['is_suppressed']==sample['requested_is_suppressed']
            sample['health_state']=observe('group.timelineObject.healthState',lambda:int(group.timelineObject.healthState))
            sample['warning']=observe('group.timelineObject.errorOrWarningMessage',lambda:group.timelineObject.errorOrWarningMessage)
            sample['all_occurrences_after']=all_occurrences(root,'all_after')
            sample['selected_occurrences_after']=[occurrence_truth(o,'selected_after['+str(i)+']') for i,o in enumerate((first,second))]
            sample['rigid_group_count']=root.rigidGroups.count
            sample['rigid_group_names']=[g.name for g in root.rigidGroups]
            design.timeline.moveToEnd()
            destination=output/sample['file'];journal('export_begin')
            succeeded=design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(destination)))
            if not succeeded or not destination.is_file() or not destination.stat().st_size:raise RuntimeError('Local RigidGroup export failed')
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
    (output/'complete.txt').write_text('RigidGroup contrasts terminal: '+truth['terminal_status']+'; inspect case/getter/setter errors.\n')
