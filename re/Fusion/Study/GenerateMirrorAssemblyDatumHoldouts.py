"""Journaled nested-occurrence and plane-orientation Mirror holdouts.

Known irrelevant combine/tolerance getters are deliberately omitted. Actual
resultFeatures null returns, getter failures and independent plane/occurrence
collection geometry remain distinct evidence.
"""

import json
import math
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion


CASES = ('nested_occurrence_yz', 'nested_occurrence_rotated_parent_xz',
         'plane_xy_positive_offset', 'plane_xz_negative_offset')


def run(context):
    app = adsk.core.Application.get()
    output = Path(__file__).resolve().parent/('mirrorassemblydatum-'+uuid.uuid4().hex[:12])
    output.mkdir()
    truth = {'fusion_version':app.version,'samples':[],'errors':[],
             'scope':'Nested actual occurrence input context plus two datum orientations/offsets. Source and result collection geometry are independent API observations; no native reflection/ownership mapping is presumed.',
             'omitted_getters':{'isCombine':'Prior actual non-body cases raise dcMirror InternalValidationError; inapplicable body control is not retried',
                                'stitchTolerance':'Prior actual non-body cases raise dcMirror InternalValidationError; no tolerance field invented',
                                'datum_mirrorPlane':'Prior actual datum getter returnsNone; requested mirror-plane identity/geometry is separately retained'}}
    point,value=adsk.core.Point3D.create,adsk.core.ValueInput.createByReal
    cases=context.get('cases',CASES) if isinstance(context,dict) else CASES
    for case in cases:
        sample={'case':case,'file':case+'.f3d','getter_errors':[],'journal':[]}
        doc=design=None

        def checkpoint(phase):
            sample['journal'].append(phase)
            truth['in_progress']=sample
            (output/'progress.json').write_text(json.dumps({'case':case,'phase':phase,'completed':len(truth['samples'])})+'\n')
            (output/'ground_truth.json').write_text(json.dumps(truth,indent=2)+'\n')

        def observe(field,getter):
            try:return getter()
            except Exception:
                sample['getter_errors'].append({'field':field,'error':traceback.format_exc()})
                checkpoint('getter_failed:'+field)
                return None

        def plane_truth(plane):
            timeline=observe('plane.timelineObject',lambda:plane.timelineObject)
            timeline_identity=None
            if timeline is not None:
                timeline_identity={'index':timeline.index,
                    'entity_type':observe('plane.timelineObject.entity.type',lambda:timeline.entity.objectType),
                    'entity_name':observe('plane.timelineObject.entity.name',lambda:getattr(timeline.entity,'name',None))}
            return {'entity_type':plane.objectType,'name':plane.name,'entity_token':plane.entityToken,
                    'origin_cm':plane.geometry.origin.asArray(),'normal':plane.geometry.normal.asArray(),
                    'transform':plane.transform.asArray(),'component_name':plane.component.name,
                    'timeline':timeline_identity,'is_parametric':plane.isParametric,
                    'definition_type':observe('plane.definition.type',lambda:plane.definition.objectType if plane.definition else None)}

        def body_truth(body):
            return {'entity_type':body.objectType,'name':body.name,'entity_token':body.entityToken,
                    'bounding_box_cm':{'min':body.boundingBox.minPoint.asArray(),'max':body.boundingBox.maxPoint.asArray()}}

        def occurrence_truth(occurrence):
            context=occurrence.assemblyContext
            native=occurrence.nativeObject
            return {'entity_type':occurrence.objectType,'name':occurrence.name,'full_path_name':occurrence.fullPathName,
                    'component_name':occurrence.component.name,'entity_token':occurrence.entityToken,
                    'transform':occurrence.transform2.asArray(),
                    'assembly_context_path':context.fullPathName if context else None,
                    'native_object_token':observe('occurrence.nativeObject.entityToken',lambda:native.entityToken) if native else None,
                    'bodies':[body_truth(b) for b in occurrence.bRepBodies]}

        def entity_truth(entity):
            plane=adsk.fusion.ConstructionPlane.cast(entity)
            occurrence=adsk.fusion.Occurrence.cast(entity)
            if plane:return plane_truth(plane)
            if occurrence:return occurrence_truth(occurrence)
            return {'entity_type':entity.objectType,'name':getattr(entity,'name',None),
                    'entity_token':observe('result.entityToken',lambda:entity.entityToken)}

        def result_features_truth(feature):
            results=feature.resultFeatures
            if results is None:
                return {'status':'returned_null','entities':[],
                        'scope':'Actual resultFeatures getter returnedNone; independently enumerated construction planes/occurrences are separate evidence'}
            return {'status':'returned_collection','count':results.count,'entities':[entity_truth(entity) for entity in results]}

        try:
            checkpoint('starting_case')
            if case not in CASES:raise ValueError('Unknown assembly/datum holdout')
            doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            design.designType=adsk.fusion.DesignTypes.ParametricDesignType
            root=design.rootComponent
            entities=adsk.core.ObjectCollection.create()
            if case.startswith('nested_'):
                parent_transform=adsk.core.Matrix3D.create()
                if case=='nested_occurrence_rotated_parent_xz':
                    parent_transform.setToRotation(math.pi/2,adsk.core.Vector3D.create(0,0,1),point(0,0,0))
                parent_transform.translation=adsk.core.Vector3D.create(2,3,1)
                parent=root.occurrences.addNewComponent(parent_transform)
                parent.component.name='NestedMirrorParent'
                child_transform=adsk.core.Matrix3D.create()
                child_transform.translation=adsk.core.Vector3D.create(3,-1,2)
                child=parent.component.occurrences.addNewComponent(child_transform)
                child.component.name='NestedMirrorSource'
                sketch=child.component.sketches.add(child.component.xYConstructionPlane)
                sketch.name='NestedSourceSketch'
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0,0,0),point(2,1,0))
                seed=child.component.features.extrudeFeatures.addSimple(sketch.profiles.item(0),value(1),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                seed.name='NestedSourceExtrude';seed.bodies.item(0).name='NestedSourceBody'
                if parent.childOccurrences.count!=1:raise RuntimeError('One nested source occurrence expected')
                selected=parent.childOccurrences.item(0)
                entities.add(selected)
                mirror_plane=root.xZConstructionPlane if case.endswith('_xz') else root.yZConstructionPlane
                sample['requested_source']=occurrence_truth(selected)
                sample['requested_parent']=occurrence_truth(parent)
            else:
                source_plane=root.xYConstructionPlane if case=='plane_xy_positive_offset' else root.xZConstructionPlane
                offset=3 if case=='plane_xy_positive_offset' else -2
                plane_input=root.constructionPlanes.createInput()
                if not plane_input.setByOffset(source_plane,value(offset)):raise RuntimeError('Source offset plane rejected')
                selected=root.constructionPlanes.add(plane_input)
                selected.name='MirroredDatumSource'
                entities.add(selected)
                mirror_plane=source_plane
                sample['requested_offset_cm']=offset
                sample['requested_source']=plane_truth(selected)
            # Base planes have no ordinary timeline entity. Their source identity
            # is captured without invoking timelineObject on the base plane.
            sample['requested_mirror_plane']={'entity_type':mirror_plane.objectType,'name':mirror_plane.name,
                    'entity_token':mirror_plane.entityToken,'origin_cm':mirror_plane.geometry.origin.asArray(),
                    'normal':mirror_plane.geometry.normal.asArray()}
            sample['construction_planes_before']=[plane_truth(p) for p in root.constructionPlanes]
            sample['all_occurrences_before']=[occurrence_truth(o) for o in root.allOccurrences]
            checkpoint('adding_mirror')
            inputs=root.features.mirrorFeatures.createInput(entities,mirror_plane)
            feature=root.features.mirrorFeatures.add(inputs)
            if feature is None:raise RuntimeError('Mirror add returnedNone')
            feature.name='ProbeMirrorAssemblyDatum'
            checkpoint('feature_added')
            feature.timelineObject.rollTo(True)
            sample['actual_inputs']=observe('inputEntities',lambda:[entity_truth(e) for e in feature.inputEntities])
            if case.startswith('nested_'):
                errors_before=len(sample['getter_errors'])
                actual_plane=observe('mirrorPlane',lambda:feature.mirrorPlane)
                sample['actual_mirror_plane']=({'entity_type':actual_plane.objectType,'name':actual_plane.name,
                        'entity_token':actual_plane.entityToken,'origin_cm':actual_plane.geometry.origin.asArray(),
                        'normal':actual_plane.geometry.normal.asArray()} if actual_plane else None)
                sample['mirror_plane_getter_status']=('getter_failed' if len(sample['getter_errors'])>errors_before
                        else 'returned_entity' if actual_plane else 'returned_null')
            else:
                sample['mirror_plane_getter_status']='not_requested_prior_actual_datum_getter_unavailable'
            design.timeline.moveToEnd()
            checkpoint('reading_results')
            sample['feature_identity']={'entity_type':feature.objectType,'name':feature.name,'entity_token':feature.entityToken,
                                        'timeline_index':feature.timelineObject.index}
            sample['api_result_features']=observe('resultFeatures',lambda:result_features_truth(feature))
            sample['construction_planes_after']=[plane_truth(p) for p in root.constructionPlanes]
            sample['all_occurrences_after']=[occurrence_truth(o) for o in root.allOccurrences]
            sample['health_state']=observe('healthState',lambda:int(feature.healthState))
            sample['warning']=observe('errorOrWarningMessage',lambda:feature.errorOrWarningMessage)
            sample['parameters']=observe('parameters',lambda:[{'name':p.name,'role':p.role,'value':p.value,'unit':p.unit,
                        'expression':p.expression,'created_by':p.createdBy.name if p.createdBy else None} for p in root.modelParameters])
            checkpoint('exporting')
            if not design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(output/sample['file']))):
                raise RuntimeError('Assembly/datum archive export failed')
            sample['export_exists']=(output/sample['file']).is_file()
            checkpoint('exported');truth['samples'].append(sample)
        except Exception:
            truth['errors'].append({'case':case,'error':traceback.format_exc(),'partial_capture':sample})
            checkpoint('case_failed')
        finally:
            if design is not None:
                try:design.timeline.moveToEnd()
                except Exception:sample['getter_errors'].append({'field':'finally.restore_timeline','error':traceback.format_exc()})
            if doc is not None:
                try:doc.close(False)
                except Exception:sample['getter_errors'].append({'field':'finally.closeFalse','error':traceback.format_exc()})
            truth.pop('in_progress',None)
            (output/'ground_truth.json').write_text(json.dumps(truth,indent=2)+'\n')
            (output/'progress.json').write_text(json.dumps({'case':case,'phase':'case_finished','completed':len(truth['samples']),'errors':len(truth['errors'])})+'\n')
    (output/'complete.txt').write_text('Assembly/datum Mirror holdouts terminal; consult case/getter errors.\n')
