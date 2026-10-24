"""Journaled owned-document Draft parting-line preview API contrasts.

Public installed SDK: fixed input setter(curves,isChained); moving input setter
(curves,isChained,direction,angle,fixedEdges). A box wall is split at mid-height
so a bounded shared BRepEdge is explicitly available as the parting line. No
existing user documents, global settings or inferred native topology are used.
Root reviews and dispatches this generator serially; this file never self-runs.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CASES=('fixed_three','fixed_seven','moving_both_three')


def run(context):
    app=adsk.core.Application.get();source=Path(__file__).resolve()
    output=source.parent/('partinglinedrafts-'+uuid.uuid4().hex[:12]);output.mkdir()
    executed=source.read_bytes();(output/'executed-generator-source.txt').write_bytes(executed)
    cases=list(context.get('cases',CASES)) if isinstance(context,dict) else list(CASES)
    truth=dict(fusion_version=app.version,samples=[],errors=[],requested_cases=cases,
        executed_generator_sha256=hashlib.sha256(executed).hexdigest(),
        sdk_scope='Installed preview DraftFeatureInput setters; fixed parting line remains in place, moving line shifts with opposing edges fixed. Actual getter/exception evidence decides support.',
        setup_scope='One owned box wall split at mid-height. Geometric selectors choose actual API setup entities; coordinates/order are never asserted to identify serialized persistent topology.')
    point,value=adsk.core.Point3D.create,adsk.core.ValueInput.createByString

    def persist():
        (output/'ground_truth.json').write_text(json.dumps(truth,indent=2)+'\n')

    def journal(phase,case=None,**fields):
        event=dict(phase=phase,case=case,time_utc=datetime.now(timezone.utc).isoformat(),
            sample_count=len(truth['samples']),error_count=len(truth['errors']),**fields)
        with (output/'journal.jsonl').open('a') as stream:stream.write(json.dumps(event)+'\n')
        (output/'progress.json').write_text(json.dumps(event,indent=2)+'\n');persist()

    journal('batch_begin')
    for case in cases:
        doc=design=None
        sample=dict(case=case,file=case+'.f3d',getter_errors=[],setter_errors=[])
        truth['active_sample']=sample

        def observe(label,callback):
            try:return callback()
            except Exception:
                sample['getter_errors'].append(dict(field=label,error=traceback.format_exc()));return None

        def setter(label,callback):
            try:
                returned=callback();sample.setdefault('setter_returns',{})[label]=returned;return returned
            except Exception:
                sample['setter_errors'].append(dict(field=label,error=traceback.format_exc()));raise

        def entity_truth(entity,label):
            if entity is None:return None
            return dict(entity_type=observe(label+'.type',lambda:entity.objectType),
                entity_token=observe(label+'.token',lambda:entity.entityToken))

        def body_truth(body,label):
            result=entity_truth(body,label)
            result.update(name=observe(label+'.name',lambda:body.name),
                parent_component_name=observe(label+'.parentComponent',lambda:body.parentComponent.name),
                is_solid=observe(label+'.isSolid',lambda:body.isSolid),
                face_count=observe(label+'.faces.count',lambda:body.faces.count),
                edge_count=observe(label+'.edges.count',lambda:body.edges.count),
                volume_cm3=observe(label+'.volume',lambda:body.volume),
                bounding_box_cm=observe(label+'.boundingBox',lambda:dict(min=body.boundingBox.minPoint.asArray(),max=body.boundingBox.maxPoint.asArray())))
            return result

        def face_truth(face,label):
            result=entity_truth(face,label);geometry=observe(label+'.geometry',lambda:face.geometry)
            result.update(temp_id=observe(label+'.tempId',lambda:face.tempId),
                body_name=observe(label+'.body.name',lambda:face.body.name),
                body_entity_token=observe(label+'.body.token',lambda:face.body.entityToken),
                geometry_type=observe(label+'.geometry.type',lambda:geometry.objectType),
                point_on_face_cm=observe(label+'.pointOnFace',lambda:face.pointOnFace.asArray()),
                centroid_cm=observe(label+'.centroid',lambda:face.centroid.asArray()),
                area_cm2=observe(label+'.area',lambda:face.area),
                is_param_reversed=observe(label+'.isParamReversed',lambda:face.isParamReversed))
            if adsk.core.Plane.cast(geometry) is not None:
                result.update(plane_origin_cm=observe(label+'.plane.origin',lambda:geometry.origin.asArray()),
                    plane_normal=observe(label+'.plane.normal',lambda:geometry.normal.asArray()))
            return result

        def edge_truth(edge,label):
            result=entity_truth(edge,label);geometry=observe(label+'.geometry',lambda:edge.geometry)
            result.update(temp_id=observe(label+'.tempId',lambda:edge.tempId),
                body_name=observe(label+'.body.name',lambda:edge.body.name),
                body_entity_token=observe(label+'.body.token',lambda:edge.body.entityToken),
                geometry_type=observe(label+'.geometry.type',lambda:geometry.objectType),
                start_vertex_cm=observe(label+'.startVertex',lambda:edge.startVertex.geometry.asArray()),
                end_vertex_cm=observe(label+'.endVertex',lambda:edge.endVertex.geometry.asArray()),
                length_cm=observe(label+'.length',lambda:edge.length),
                adjacent_faces=observe(label+'.faces',lambda:[face_truth(f,label+'.faces['+str(i)+']') for i,f in enumerate(edge.faces)]))
            if adsk.core.Line3D.cast(geometry) is not None:
                result.update(line_start_cm=observe(label+'.line.start',lambda:geometry.startPoint.asArray()),
                    line_end_cm=observe(label+'.line.end',lambda:geometry.endPoint.asArray()))
            def evaluated():
                evaluator=edge.evaluator;ok,low,high=evaluator.getParameterExtents()
                if not ok:raise RuntimeError('Actual bounded edge parameter extents failed')
                parameters=[low,(low+high)/2.,high];ok,points=evaluator.getPointsAtParameters(parameters)
                if not ok:raise RuntimeError('Actual bounded edge point evaluation failed')
                return dict(parameter_extents=[low,high],parameters=parameters,points_cm=[p.asArray() for p in points])
            result['actual_trimmed_evaluator']=observe(label+'.evaluator',evaluated)
            return result

        def source_truth(entity,label):
            if adsk.fusion.BRepEdge.cast(entity) is not None:return edge_truth(entity,label)
            if adsk.fusion.BRepFace.cast(entity) is not None:return face_truth(entity,label)
            result=entity_truth(entity,label)
            if adsk.fusion.ConstructionPlane.cast(entity) is not None:
                result.update(name=observe(label+'.name',lambda:entity.name),
                    origin_cm=observe(label+'.plane.origin',lambda:entity.geometry.origin.asArray()),
                    normal=observe(label+'.plane.normal',lambda:entity.geometry.normal.asArray()))
            return result

        def definition_truth(definition,label):
            if definition is None:return None
            # Extent definitions have no entityToken contract; retain objectType only.
            result=dict(entity_type=observe(label+'.type',lambda:definition.objectType))
            if adsk.fusion.AngleExtentDefinition.cast(definition) is not None:
                result.update(angle_mode='SingleAngle',is_symmetric=observe(label+'.isSymmetric',lambda:definition.isSymmetric),
                    angle_one_radians=observe(label+'.angle.value',lambda:definition.angle.value),angle_two_radians=None)
            elif adsk.fusion.TwoSidesAngleExtentDefinition.cast(definition) is not None:
                result.update(angle_mode='TwoAngles',angle_one_radians=observe(label+'.angleOne.value',lambda:definition.angleOne.value),
                    angle_two_radians=observe(label+'.angleTwo.value',lambda:definition.angleTwo.value))
            return result

        try:
            if case not in CASES:raise ValueError('Unknown owned parting-line case '+str(case))
            journal('creating_document',case)
            doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            design.designType=adsk.fusion.DesignTypes.ParametricDesignType;root=design.rootComponent
            sketch=root.sketches.add(root.xYConstructionPlane);sketch.name='PartingDraftSeedProfile'
            sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0,0,0),point(3,2,0))
            seed=root.features.extrudeFeatures.addSimple(sketch.profiles.item(0),value('20 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            seed.name='PartingDraftSeedExtrude';body=seed.bodies.item(0);body.name='PartingDraftSeedBody'
            # Choose a known setup wall using actual API planar face geometry.
            walls=[f for f in body.faces if adsk.core.Plane.cast(f.geometry) is not None
                and abs(f.centroid.y)<1e-7 and abs(abs(f.geometry.normal.y)-1)<1e-7]
            if len(walls)!=1:raise RuntimeError('Owned box does not have exactly one planar y=0 setup wall')
            sample['unsplit_wall']=face_truth(walls[0],'setup.unsplit_wall')
            plane_input=root.constructionPlanes.createInput()
            if not setter('setup.setByOffset',lambda:plane_input.setByOffset(root.xYConstructionPlane,value('10 mm'))):
                raise RuntimeError('Documented middle-plane offset setter returned false')
            middle=root.constructionPlanes.add(plane_input);middle.name='PartingDraftMiddlePlane'
            split_faces=adsk.core.ObjectCollection.create();split_faces.add(walls[0])
            split_input=root.features.splitFaceFeatures.createInput(split_faces,middle,False)
            splitter=root.features.splitFaceFeatures.add(split_input)
            if splitter is None:raise RuntimeError('Owned setup SplitFace returned null')
            splitter.name='PartingDraftWallSplit'
            sample['setup_split_health']=observe('setup.split.healthState',lambda:int(splitter.healthState))
            sample['setup_split_warning']=observe('setup.split.warning',lambda:splitter.errorOrWarningMessage)
            # The actual shared bounded edge must meet both coplanar wall patches.
            line_candidates=[]
            for edge in body.edges:
                if adsk.core.Line3D.cast(edge.geometry) is None:continue
                a,b=edge.startVertex.geometry,edge.endVertex.geometry
                if max(abs(a.y),abs(b.y),abs(a.z-1),abs(b.z-1))>1e-7:continue
                neighbors=[f for f in edge.faces if adsk.core.Plane.cast(f.geometry) is not None
                    and abs(f.centroid.y)<1e-7 and abs(abs(f.geometry.normal.y)-1)<1e-7]
                if len(neighbors)==2:line_candidates.append((edge,neighbors))
            if len(line_candidates)!=1:raise RuntimeError('Owned split wall lacks one unambiguous actual shared parting edge')
            parting,faces=line_candidates[0];faces=sorted(faces,key=lambda face:face.centroid.z)
            fixed_edges=[]
            for height in (0.,2.):
                candidates=[e for e in body.edges if adsk.core.Line3D.cast(e.geometry) is not None
                    and max(abs(e.startVertex.geometry.y),abs(e.endVertex.geometry.y),
                        abs(e.startVertex.geometry.z-height),abs(e.endVertex.geometry.z-height))<1e-7]
                if len(candidates)!=1:raise RuntimeError('Owned wall opposing fixed edge not unique at '+str(height))
                fixed_edges.append(candidates[0])
            moving=case.startswith('moving');angle='7 deg' if case=='fixed_seven' else '3 deg'
            direction=adsk.fusion.MovingPartingLineDirections.BothAnglesMovingPartingLineDirection
            pull=root.xYConstructionPlane
            sample['requested']=dict(mode='MovingPartingLine' if moving else 'FixedPartingLine',angle=angle,
                is_chained=False,is_tangent_chain=False,is_direction_flipped=False,is_symmetric=True if not moving else None,
                moving_direction=int(direction) if moving else None,
                input_faces=[face_truth(f,'requested.faces['+str(i)+']') for i,f in enumerate(faces)],
                pull_geometry=source_truth(pull,'requested.pull'),
                parting_line_curves=[edge_truth(parting,'requested.parting[0]')],
                fixed_edges=[edge_truth(e,'requested.fixed['+str(i)+']') for i,e in enumerate(fixed_edges)] if moving else [])
            sample['before_body']=body_truth(body,'before.body');sample['before_root_body_count']=root.bRepBodies.count
            inputs=root.features.draftFeatures.createInput(faces,pull,False)
            if inputs is None:raise RuntimeError('Draft createInput returned null')
            inputs.isDirectionFlipped=False
            journal('creating_draft',case)
            if moving:
                accepted=setter('setMovingPartingLineDraftFeatureType',lambda:inputs.setMovingPartingLineDraftFeatureType([parting],False,direction,value(angle),fixed_edges))
            else:
                if not setter('setSingleAngle',lambda:inputs.setSingleAngle(True,value(angle))):raise RuntimeError('Fixed parting angle setter returned false')
                accepted=setter('setFixedPartingLineDraftFeatureType',lambda:inputs.setFixedPartingLineDraftFeatureType([parting],False))
            if not accepted:raise RuntimeError('Documented parting-line setter returned false')
            sample['actual_input_types']=dict(draft_type=observe('input.draftType',lambda:int(inputs.draftType)),
                parting_line_type=observe('input.partingLineType',lambda:int(inputs.partingLineType)),
                moving_direction=observe('input.movingPartingLineDirection',lambda:int(inputs.movingPartingLineDirection)) if moving else None)
            feature=root.features.draftFeatures.add(inputs)
            if feature is None:raise RuntimeError('Parting-line Draft add returned null')
            feature.name='ProbePartingDraft'+''.join(piece.capitalize() for piece in case.split('_'))
            sample['compute_returned']=observe('design.computeAll',lambda:design.computeAll())
            sample['feature_identity']=dict(name=feature.name,entity_type=feature.objectType,
                entity_token=observe('feature.token',lambda:feature.entityToken),timeline_index=feature.timelineObject.index)
            journal('reading_actual_rollback',case)
            if not feature.timelineObject.rollTo(True):raise RuntimeError('Parting-line Draft rollback returned false')
            sample['settings']=dict(draft_type=observe('feature.draftType',lambda:int(feature.draftType)),
                parting_line_type=observe('feature.partingLineType',lambda:int(feature.partingLineType)),
                is_direction_flipped=observe('feature.isDirectionFlipped',lambda:feature.isDirectionFlipped),
                is_tangent_chain=observe('feature.isTangentChain',lambda:feature.isTangentChain),
                moving_direction=observe('feature.movingPartingLineDirection',lambda:int(feature.movingPartingLineDirection)) if moving else None,
                definition=definition_truth(observe('feature.draftDefinition',lambda:feature.draftDefinition),'actual.definition'),
                input_faces=observe('feature.inputFaces',lambda:[face_truth(f,'actual.faces['+str(i)+']') for i,f in enumerate(feature.inputFaces)]),
                pull_geometry=source_truth(observe('feature.plane',lambda:feature.plane),'actual.pull'),
                parting_line_curves=observe('feature.partingLineCurves',lambda:[source_truth(e,'actual.parting['+str(i)+']') for i,e in enumerate(feature.partingLineCurves)]),
                moving_fixed_edges=observe('feature.movingPartingLineFixedEdges',lambda:[edge_truth(e,'actual.fixed['+str(i)+']') for i,e in enumerate(feature.movingPartingLineFixedEdges)]) if moving else None,
                is_chained=None,is_chained_status='Requested False; installed DraftFeature has no independent public parting-line chaining getter')
            design.timeline.moveToEnd()
            sample['health_state']=observe('feature.healthState',lambda:int(feature.healthState))
            sample['warning']=observe('feature.warning',lambda:feature.errorOrWarningMessage)
            sample['is_suppressed']=observe('feature.isSuppressed',lambda:feature.isSuppressed)
            sample['feature_bodies']=observe('feature.bodies',lambda:[body_truth(b,'feature.bodies['+str(i)+']') for i,b in enumerate(feature.bodies)])
            sample['root_bodies']=observe('root.bRepBodies',lambda:[body_truth(b,'root.bodies['+str(i)+']') for i,b in enumerate(root.bRepBodies)])
            sample['parameters']=observe('root.modelParameters',lambda:[dict(name=p.name,role=p.role,value=p.value,unit=p.unit,expression=p.expression,created_by=p.createdBy.name if p.createdBy else None) for p in root.modelParameters])
            design.timeline.moveToEnd();destination=output/sample['file'];journal('export_begin',case)
            succeeded=design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(destination)))
            if not succeeded or not destination.is_file() or not destination.stat().st_size:raise RuntimeError('Parting-line Draft local export failed')
            sample['export']=dict(returned_success=bool(succeeded),byte_count=destination.stat().st_size,sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
            truth['samples'].append(sample);journal('export_complete',case)
        except Exception:
            truth['errors'].append(dict(case=case,error=traceback.format_exc(),partial_capture=sample));journal('case_failed',case)
        finally:
            if design is not None:
                try:design.timeline.moveToEnd()
                except Exception:sample['getter_errors'].append(dict(field='finally.restore_timeline',error=traceback.format_exc()))
            if doc is not None:
                try:
                    sample['close_owned_document_returned']=doc.close(False)
                    journal('owned_document_close_returned',case,save=False,returned=sample['close_owned_document_returned'])
                except Exception:sample['getter_errors'].append(dict(field='finally.closeFalse',error=traceback.format_exc()))
            truth.pop('active_sample',None);persist()
    truth['terminal_status']='complete' if len(truth['samples'])==len(cases) and not truth['errors'] else 'complete_with_errors'
    truth['exported_sample_count']=len(truth['samples']);journal('batch_terminal')
    (output/'complete.txt').write_text('Parting-line Draft terminal: '+truth['terminal_status']+'; inspect actual errors.\n')
