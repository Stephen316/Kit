"""Prepared straight-path Feature-compute/Occurrence input contrasts.

Three fresh owned root documents, identical common path controls. Native input
schemas and active compute fields require later actual-export inspection.
"""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CASES=('feature_optimized','feature_identical','root_occurrence')
OUTPUT_PREFIX='pathpatterninputs-'


def run(context):
    app=adsk.core.Application.get();batch_id=uuid.uuid4().hex[:12]
    output=Path(__file__).resolve().parent/(OUTPUT_PREFIX+batch_id);output.mkdir()
    source=Path(__file__).read_bytes();(output/'executed-generator-source.txt').write_bytes(source)
    truth=dict(batch_id=batch_id,fusion_version=app.version,samples=[],errors=[],requested_cases=list(CASES),
        executed_generator_sha256=hashlib.sha256(source).hexdigest(),
        execution_scope='Three independent owned parametric root documents, local exports and closeFalse only; no existing document or global setting changes',
        API_scope='Documented PathPatternFeatures.createInput homogeneous Feature or Occurrence inputs; PathPatternFeatureInput.patternComputeOption is set only for feature inputs',
        evidence_scope='Requested source and path, actual rolled-back inputEntities/path, actual settings/elements/resultFeatures/collections/health; native identities and regeneration remain for offline inspection')
    cases=context.get('cases',CASES) if isinstance(context,dict) else CASES
    for case in cases:
        doc=design=None
        sample=dict(case=case,file=case+'.f3d',getter_errors=[],setter_errors=[])
        def persist():(output/'ground_truth.json').write_text(json.dumps(truth,indent=2)+'\n')
        def journal(phase,**fields):
            event=dict(time_utc=datetime.now(timezone.utc).isoformat(),batch_id=batch_id,case=case,
                phase=phase,completed=len(truth['samples']),error_count=len(truth['errors']),**fields)
            with (output/'journal.jsonl').open('a') as stream:stream.write(json.dumps(event)+'\n')
            (output/'progress.json').write_text(json.dumps(event,indent=2)+'\n');truth['active_sample']=sample;persist()
        def observe(label,getter):
            try:return getter()
            except Exception:
                sample['getter_errors'].append(dict(field=label,error=traceback.format_exc()));journal('getter_error',field=label);return None
        def body_truth(body,label):
            return dict(name=observe(label+'.name',lambda:body.name),entity_type=observe(label+'.objectType',lambda:body.objectType),
                entity_token=observe(label+'.entityToken',lambda:body.entityToken),
                bounding_box_cm=observe(label+'.boundingBox',lambda:dict(min=body.boundingBox.minPoint.asArray(),max=body.boundingBox.maxPoint.asArray())))
        def occurrence_truth(occurrence,label):
            bodies=observe(label+'.bRepBodies',lambda:occurrence.bRepBodies)
            return dict(name=observe(label+'.name',lambda:occurrence.name),full_path_name=observe(label+'.fullPathName',lambda:occurrence.fullPathName),
                component_name=observe(label+'.component.name',lambda:occurrence.component.name),
                entity_token=observe(label+'.entityToken',lambda:occurrence.entityToken),
                transform=observe(label+'.transform2',lambda:occurrence.transform2.asArray()),
                assembly_context_path=observe(label+'.assemblyContext',lambda:occurrence.assemblyContext.fullPathName if occurrence.assemblyContext else None),
                bodies=[body_truth(b,label+'.bodies['+str(i)+']') for i,b in enumerate(bodies)] if bodies is not None else None)
        def entity_truth(entity,label):
            if entity is None:return dict(status='returned_null')
            occurrence=adsk.fusion.Occurrence.cast(entity)
            if occurrence is not None:return dict(kind='Occurrence',**occurrence_truth(occurrence,label))
            feature=adsk.fusion.ExtrudeFeature.cast(entity)
            if feature is not None:
                bodies=observe(label+'.bodies',lambda:feature.bodies)
                return dict(kind='ExtrudeFeature',entity_type=feature.objectType,name=feature.name,
                    entity_token=observe(label+'.entityToken',lambda:feature.entityToken),
                    parent_component_name=observe(label+'.parentComponent.name',lambda:feature.parentComponent.name),
                    timeline_index=observe(label+'.timelineObject.index',lambda:feature.timelineObject.index),
                    bodies=[body_truth(b,label+'.bodies['+str(i)+']') for i,b in enumerate(bodies)] if bodies is not None else None)
            return dict(kind='Other',entity_type=observe(label+'.objectType',lambda:entity.objectType))
        def path_truth(path,label):
            if path is None:return dict(status='returned_null')
            rows=[]
            for i in range(path.count):
                item=path.item(i);source=item.entity
                rows.append(dict(curve_type=observe(label+'.curveType',lambda:int(item.curveType)),
                    source_entity_type=observe(label+'.entity.objectType',lambda:source.objectType),
                    source_entity_token=observe(label+'.entity.entityToken',lambda:source.entityToken),
                    source_sketch_name=observe(label+'.entity.parentSketch.name',lambda:source.parentSketch.name),
                    is_opposed_to_entity=observe(label+'.isOpposedToEntity',lambda:item.isOpposedToEntity),
                    path_curve_start_cm=observe(label+'.curve.startPoint',lambda:item.curve.startPoint.asArray()),
                    path_curve_end_cm=observe(label+'.curve.endPoint',lambda:item.curve.endPoint.asArray()),
                    source_start_cm=observe(label+'.entity.startSketchPoint',lambda:source.startSketchPoint.geometry.asArray()),
                    source_end_cm=observe(label+'.entity.endSketchPoint',lambda:source.endSketchPoint.geometry.asArray())))
            return dict(count=path.count,entities=rows)
        def root_collections(root,label):
            return dict(root_body_count=root.bRepBodies.count,
                root_bodies=[body_truth(b,label+'.bodies['+str(i)+']') for i,b in enumerate(root.bRepBodies)],
                root_occurrence_count=root.occurrences.count,
                all_occurrences=[occurrence_truth(o,label+'.occurrences['+str(i)+']') for i,o in enumerate(root.allOccurrences)])
        try:
            if case not in CASES:raise ValueError('Unknown bounded PathPattern input case')
            journal('document_create_begin')
            doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            design.designType=adsk.fusion.DesignTypes.ParametricDesignType;root=design.rootComponent
            point,value=adsk.core.Point3D.create,adsk.core.ValueInput.createByReal
            source_component=root
            if case=='root_occurrence':
                transform=adsk.core.Matrix3D.create();transform.translation=adsk.core.Vector3D.create(1.,2.,0.)
                source_occurrence=root.occurrences.addNewComponent(transform);source_occurrence.component.name='PathPatternSourceComponent'
                source_component=source_occurrence.component
            sketch=source_component.sketches.add(source_component.xYConstructionPlane);sketch.name='PathPatternSeedProfile'
            sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0,0,0),point(1,1,0))
            seed=source_component.features.extrudeFeatures.addSimple(sketch.profiles.item(0),value(1.),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            seed.name='PathPatternSeedExtrude';seed.bodies.item(0).name='PathPatternSeedBody'
            selected=source_occurrence if case=='root_occurrence' else seed
            source_path=root.sketches.add(root.xYConstructionPlane);source_path.name='InputContrastStraightPath'
            curve=source_path.sketchCurves.sketchLines.addByTwoPoints(point(0,0,0),point(6,0,0))
            path=root.features.createPath(curve,False)
            sample['compute_before']=observe('design.computeAll.before',lambda:design.computeAll())
            sample['requested_input']=entity_truth(selected,'requested_input')
            sample['requested_path']=path_truth(path,'requested_path')
            sample['collections_before']=root_collections(root,'before')
            entities=adsk.core.ObjectCollection.create();entities.add(selected)
            inputs=root.features.pathPatternFeatures.createInput(entities,path,value(3.),value(1.5),adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
            if inputs is None:raise RuntimeError('PathPatternFeatures.createInput returnedNone')
            inputs.startPoint=0.;inputs.isFlipDirection=False;inputs.isSymmetric=False;inputs.isOrientationAlongPath=False
            requested_compute=None
            if case!='root_occurrence':
                requested_compute=(adsk.fusion.PatternComputeOptions.OptimizedPatternCompute if case=='feature_optimized' else adsk.fusion.PatternComputeOptions.IdenticalPatternCompute)
                inputs.patternComputeOption=requested_compute
            sample['requested_compute_option']=int(requested_compute) if requested_compute is not None else None
            sample['requested_common_controls']=dict(quantity=3,distance_cm=1.5,distance_type=1,start_fraction=0.,is_flipped=False,is_symmetric=False,orientation_along_path=False)
            journal('pattern_add_begin');feature=root.features.pathPatternFeatures.add(inputs)
            if feature is None:raise RuntimeError('PathPatternFeatures.add returnedNone')
            feature.name='ProbePathPattern'+case.title().replace('_','');journal('pattern_added')
            feature.timelineObject.rollTo(True)
            actual=observe('feature.inputEntities',lambda:feature.inputEntities)
            sample['actual_inputs']=[entity_truth(e,'actual_inputs['+str(i)+']') for i,e in enumerate(actual)] if actual is not None else None
            sample['actual_path']=path_truth(observe('feature.path',lambda:feature.path),'actual_path')
            design.timeline.moveToEnd();sample['compute_after']=observe('design.computeAll.after',lambda:design.computeAll())
            sample['feature_identity']=dict(name=feature.name,entity_type=feature.objectType,
                entity_token=observe('feature.entityToken',lambda:feature.entityToken),timeline_index=feature.timelineObject.index,
                parent_component_name=feature.parentComponent.name)
            actual_type=observe('feature.patternEntityType',lambda:int(feature.patternEntityType))
            sample['settings']=dict(quantity=observe('feature.quantity.value',lambda:feature.quantity.value),
                distance_cm=observe('feature.distance.value',lambda:feature.distance.value),
                distance_type=observe('feature.patternDistanceType',lambda:int(feature.patternDistanceType)),
                start_fraction=observe('feature.startPoint',lambda:feature.startPoint),
                is_flipped=observe('feature.isFlipDirection',lambda:feature.isFlipDirection),
                is_symmetric=observe('feature.isSymmetric',lambda:feature.isSymmetric),
                orientation_along_path=observe('feature.isOrientationAlongPath',lambda:feature.isOrientationAlongPath),
                pattern_entity_type=actual_type,pattern_compute_option=observe('feature.patternComputeOption',lambda:int(feature.patternComputeOption)),
                suppressed_element_ids=observe('feature.suppressedElementsIds',lambda:list(feature.suppressedElementsIds)))
            elements=observe('feature.patternElements',lambda:feature.patternElements);element_rows=[]
            if elements is not None:
                for i in range(elements.count):
                    element=elements.item(i);label='element['+str(i)+']'
                    row=dict(id=observe(label+'.id',lambda:element.id),name=observe(label+'.name',lambda:element.name),
                        is_suppressed=observe(label+'.isSuppressed',lambda:element.isSuppressed),
                        transform=observe(label+'.transform',lambda:element.transform.asArray()))
                    if case=='root_occurrence':
                        occurrences=observe(label+'.occurrences',lambda:element.occurrences)
                        row['occurrences']=[occurrence_truth(o,label+'.occurrences['+str(j)+']') for j,o in enumerate(occurrences)] if occurrences is not None else None
                    else:
                        faces=observe(label+'.faces',lambda:element.faces);row['face_count']=len(faces) if faces is not None else None
                    element_rows.append(row)
            sample['pattern_elements']=element_rows
            results=observe('feature.resultFeatures',lambda:feature.resultFeatures)
            sample['result_features']=dict(status='getter_failed' if results is None and any(e['field']=='feature.resultFeatures' for e in sample['getter_errors']) else ('returned_null' if results is None else 'returned_collection'),
                entities=[entity_truth(e,'result_features['+str(i)+']') for i,e in enumerate(results)] if results is not None else [])
            feature_bodies=observe('feature.bodies',lambda:feature.bodies)
            sample['feature_bodies']=[body_truth(b,'feature.bodies['+str(i)+']') for i,b in enumerate(feature_bodies)] if feature_bodies is not None else None
            sample['health_state']=observe('feature.healthState',lambda:int(feature.healthState))
            sample['warning']=observe('feature.errorOrWarningMessage',lambda:feature.errorOrWarningMessage)
            sample['collections_after']=root_collections(root,'after')
            sample['parameters']=observe('root.modelParameters',lambda:[dict(name=p.name,role=p.role,value=p.value,unit=p.unit,
                expression=p.expression,created_by=p.createdBy.name if p.createdBy else None) for p in root.modelParameters])
            design.timeline.moveToEnd();destination=output/sample['file'];journal('export_begin')
            succeeded=design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(destination)))
            if not succeeded or not destination.is_file() or not destination.stat().st_size:raise RuntimeError('Local PathPattern input export failed')
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
    (output/'complete.txt').write_text('PathPattern input contrasts terminal: '+truth['terminal_status']+'; inspect case/getter errors.\n')
