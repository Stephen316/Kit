"""Prepared owned datum Mirrors selecting offset/tilted construction-plane supports.

Exactly two fresh same-root parametric documents. Source/support API transforms
are captured before Mirror; the after collection is independent of resultFeatures
and does not presume native output identity. Execution is serialized by root.
"""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CASES = ('offset_selected_support', 'tilted_selected_support')
OUTPUT_PREFIX = 'datummirrorsupport-'


def run(context):
    app = adsk.core.Application.get()
    batch_id = uuid.uuid4().hex[:12]
    output = Path(__file__).resolve().parent / (OUTPUT_PREFIX+batch_id)
    output.mkdir()
    truth = dict(batch_id=batch_id, fusion_version=app.version, samples=[], errors=[],
        requested_cases=list(CASES),
        execution_scope='Two independent newly owned same-root parametric documents; local export and closeFalse only',
        evidence_scope='Explicit API source/support handles before Mirror and independently enumerated constructionPlanes after Mirror; no output/timeline/definition identity invented from collection order',
        omitted_getters={'isCombine':'Prior datum cases raise inapplicable dcMirror InternalValidationError',
                         'stitchTolerance':'Prior datum cases raise inapplicable dcMirror InternalValidationError'})
    cases=context.get('cases',CASES) if isinstance(context,dict) else CASES
    for case in cases:
        sample=dict(case=case,file=case+'.f3d',getter_errors=[])
        doc=design=None
        def persist():
            (output/'ground_truth.json').write_text(json.dumps(truth,indent=2)+'\n')
        def journal(phase,**fields):
            event=dict(time_utc=datetime.now(timezone.utc).isoformat(),batch_id=batch_id,
                case=case,phase=phase,completed=len(truth['samples']),errors=len(truth['errors']),**fields)
            with (output/'journal.jsonl').open('a') as stream:stream.write(json.dumps(event)+'\n')
            (output/'progress.json').write_text(json.dumps(event,indent=2)+'\n')
            truth['active_sample']=sample;persist()
        def observe(field,getter):
            try:return getter()
            except Exception:
                sample['getter_errors'].append(dict(field=field,error=traceback.format_exc()))
                journal('getter_error',field=field)
                return None
        def plane_truth(plane,label):
            def timeline_truth():
                timeline=plane.timelineObject
                if timeline is None:return dict(status='returned_null')
                entity=timeline.entity
                return dict(status='returned_entity',index=timeline.index,
                    entity_type=entity.objectType if entity else None,
                    entity_name=getattr(entity,'name',None) if entity else None)
            return dict(entity_type=observe(label+'.objectType',lambda:plane.objectType),
                name=observe(label+'.name',lambda:plane.name),
                entity_token=observe(label+'.entityToken',lambda:plane.entityToken),
                component_name=observe(label+'.component.name',lambda:plane.component.name),
                origin_cm=observe(label+'.geometry.origin',lambda:plane.geometry.origin.asArray()),
                normal=observe(label+'.geometry.normal',lambda:plane.geometry.normal.asArray()),
                transform=observe(label+'.transform',lambda:plane.transform.asArray()),
                is_parametric=observe(label+'.isParametric',lambda:plane.isParametric),
                timeline=observe(label+'.timelineObject',timeline_truth),
                definition_type=observe(label+'.definition.objectType',lambda:plane.definition.objectType if plane.definition else None))
        def collection_truth(component,label):
            return [plane_truth(component.constructionPlanes.item(i),label+'['+str(i)+']')
                    for i in range(component.constructionPlanes.count)]
        try:
            if case not in CASES:raise ValueError('Unknown bounded datum support case')
            journal('document_create_begin')
            doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            design.designType=adsk.fusion.DesignTypes.ParametricDesignType
            root=design.rootComponent
            value=adsk.core.ValueInput.createByReal
            source_input=root.constructionPlanes.createInput()
            source_ok=source_input.setByOffset(root.xYConstructionPlane,value(3.0))
            sample['source_setter']=dict(method='setByOffset',returned=bool(source_ok),offset_cm=3.0,
                source_origin_plane_name=root.xYConstructionPlane.name)
            if not source_ok:raise RuntimeError('Source plane offset setter rejected')
            source=root.constructionPlanes.add(source_input)
            if source is None:raise RuntimeError('Source plane add returnedNone')
            source.name='DatumMirrorIndependentSource'
            support_input=root.constructionPlanes.createInput()
            if case=='offset_selected_support':
                support_ok=support_input.setByOffset(root.xYConstructionPlane,value(1.0))
                sample['support_setter']=dict(method='setByOffset',returned=bool(support_ok),offset_cm=1.0,
                    source_origin_plane_name=root.xYConstructionPlane.name)
            else:
                support_ok=support_input.setByAngle(root.yConstructionAxis,value(math.pi/6),root.xYConstructionPlane)
                sample['support_setter']=dict(method='setByAngle',returned=bool(support_ok),angle_rad=math.pi/6,
                    rotation_axis_name=root.yConstructionAxis.name,source_origin_plane_name=root.xYConstructionPlane.name)
            if not support_ok:raise RuntimeError('Selected support plane setter rejected')
            support=root.constructionPlanes.add(support_input)
            if support is None:raise RuntimeError('Selected support plane add returnedNone')
            support.name='DatumMirrorSelectedSupport'
            sample['compute_before']=observe('design.computeAll.before',lambda:design.computeAll())
            sample['requested_source']=plane_truth(source,'requested_source')
            sample['requested_mirror_plane']=plane_truth(support,'requested_mirror_plane')
            sample['construction_planes_before']=collection_truth(root,'before_planes')
            sample['construction_plane_count_before']=root.constructionPlanes.count
            if source.entityToken==support.entityToken:raise RuntimeError('Independent source/support handles coincide')
            entities=adsk.core.ObjectCollection.create();entities.add(source)
            journal('mirror_add_begin')
            mirror_input=root.features.mirrorFeatures.createInput(entities,support)
            feature=root.features.mirrorFeatures.add(mirror_input)
            if feature is None:raise RuntimeError('Datum Mirror add returnedNone')
            feature.name='ProbeDatumMirrorConstructionSupport'
            journal('mirror_added')
            feature.timelineObject.rollTo(True)
            actual_inputs=observe('feature.inputEntities',lambda:feature.inputEntities)
            sample['actual_inputs']=[plane_truth(entity,'actual_inputs['+str(i)+']') for i,entity in enumerate(actual_inputs)] if actual_inputs is not None else None
            errors_before=len(sample['getter_errors'])
            selected=observe('feature.mirrorPlane',lambda:feature.mirrorPlane)
            sample['mirror_plane_getter_status']='getter_failed' if len(sample['getter_errors'])>errors_before else ('returned_entity' if selected is not None else 'returned_null')
            sample['actual_mirror_plane']=plane_truth(selected,'actual_mirror_plane') if selected is not None else None
            design.timeline.moveToEnd()
            sample['compute_after']=observe('design.computeAll.after',lambda:design.computeAll())
            sample['feature_identity']=dict(entity_type=feature.objectType,name=feature.name,
                entity_token=observe('feature.entityToken',lambda:feature.entityToken),timeline_index=feature.timelineObject.index)
            results=observe('feature.resultFeatures',lambda:feature.resultFeatures)
            sample['api_result_features']=dict(status='returned_null' if results is None and not any(e['field']=='feature.resultFeatures' for e in sample['getter_errors']) else ('getter_failed' if results is None else 'returned_collection'),
                entities=[plane_truth(entity,'resultFeatures['+str(i)+']') for i,entity in enumerate(results)] if results is not None else [])
            sample['construction_planes_after']=collection_truth(root,'after_planes')
            sample['construction_plane_count_after']=root.constructionPlanes.count
            sample['source_handle_after']=plane_truth(source,'source_handle_after')
            sample['support_handle_after']=plane_truth(support,'support_handle_after')
            sample['health_state']=observe('feature.healthState',lambda:int(feature.healthState))
            sample['warning']=observe('feature.errorOrWarningMessage',lambda:feature.errorOrWarningMessage)
            sample['parameters']=observe('root.modelParameters',lambda:[dict(name=p.name,role=p.role,value=p.value,
                expression=p.expression,unit=p.unit,created_by=p.createdBy.name if p.createdBy else None) for p in root.modelParameters])
            design.timeline.moveToEnd()
            destination=output/sample['file'];journal('export_begin')
            succeeded=design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(destination)))
            if not succeeded or not destination.is_file() or not destination.stat().st_size:
                raise RuntimeError('Local datum Mirror support export did not complete')
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
    (output/'complete.txt').write_text('Datum Mirror support contrasts terminal: '+truth['terminal_status']+'; inspect getter/case errors.\n')
