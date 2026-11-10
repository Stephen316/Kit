"""Small owned-document public Boss API probes with exact source journaling.

The installed API has no boss-height input: its shank attaches along the sketch
normal to an intersecting solid participant. A position-plane contrast changes
that source geometry; no height or license availability is presumed.
"""
import hashlib
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CONFIGS={
    'blank_diameter_08':{'diameter_cm':.8,'position_plane_z_cm':1.5},
    'blank_diameter_12':{'diameter_cm':1.2,'position_plane_z_cm':1.5},
    'blank_taller_position':{'diameter_cm':.8,'position_plane_z_cm':2.2},
}
CASES=tuple(CONFIGS)


def run(context):
    app=adsk.core.Application.get();root=Path(__file__).resolve().parent
    output=root/('bosscontrasts-'+uuid.uuid4().hex[:12]);output.mkdir()
    source=Path(__file__).read_bytes();(output/'executed-generator-source.txt').write_bytes(source)
    cases=context.get('cases',CASES) if isinstance(context,dict) else CASES
    if not isinstance(cases,(tuple,list)) or any(case not in CONFIGS for case in cases):raise ValueError('Unknown Boss case')
    truth={'status':'running','fusion_version':app.version,'samples':[],'errors':[],
        'executed_generator_sha256':hashlib.sha256(source).hexdigest(),
        'SDK_scope':'BossFeatures.createInput/setPositionBySketchPoints/createSideInput/setBlank/participantBodies/side2/add; actual BossFeature.createInput requires rollback. Solid participants only; ray attachment inferred by Fusion. No public shank-height input.',
        'availability_scope':'Installed public methods verified offline; license/design support is determined only by actual returned API results/errors'}
    def save(event):
        (output/'ground_truth.json').write_text(json.dumps(truth,indent=2)+'\n')
        (output/'progress.json').write_text(json.dumps({'status':truth['status'],'samples':[{'case':s['case'],'status':s['status']} for s in truth['samples']],'errors':len(truth['errors'])},indent=2)+'\n')
        with (output/'journal.jsonl').open('a') as handle:handle.write(json.dumps(event)+'\n')
    save({'event':'started','cases':list(cases)})
    for case in cases:
        requested={**CONFIGS[case],'side':'side2','is_default_direction':True,'offset_cm':0.,
            'shape':'Blank','rib_shape':'None','draft_angle_radians':0.,'root_radius_cm':0.,'tip_radius_cm':0.,'base_top_z_cm':.3}
        sample={'case':case,'file':case+'.f3d','requested':requested,'status':'creating_document','getter_errors':[]}
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
            def token(item,label):return read(label+'.entityToken',lambda:item.entityToken)
            def body_truth(body,label):
                return {'entity_type':body.objectType,'name':body.name,'entity_token':token(body,label),'is_solid':body.isSolid,
                    'face_count':body.faces.count,'edge_count':body.edges.count,'vertex_count':body.vertices.count,
                    'volume_cm3':body.volume,'bounds_min_cm':list(body.boundingBox.minPoint.asArray()),'bounds_max_cm':list(body.boundingBox.maxPoint.asArray())}
            def parameter(item):
                if item is None:return {'getter_returned_null':True}
                return {'entity_type':item.objectType,'name':item.name,'role':item.role,'raw_value':item.value,'unit':item.unit,'expression':item.expression,
                    'created_by':read('parameter.createdBy',lambda:getattr(item.createdBy,'name',None))}
            def point_truth(item,label):
                return {'entity_type':item.objectType,'entity_token':token(item,label),'sketch_name':item.parentSketch.name,
                    'sketch_token':token(item.parentSketch,label+'.sketch'),'world_cm':list(item.worldGeometry.asArray()),'sketch_local_cm':list(item.geometry.asArray())}
            def value_input(item):
                if item is None:return {'getter_returned_null':True}
                kind=item.valueType;result={'entity_type':item.objectType,'value_type':int(kind)}
                if kind==adsk.core.ValueTypes.RealValueType:result['real_value']=item.realValue
                elif kind==adsk.core.ValueTypes.StringValueType:result['string_value']=item.stringValue
                elif kind==adsk.core.ValueTypes.BooleanValueType:result['boolean_value']=item.booleanValue
                else:result['scope']='Uninterpreted non-real/string/boolean ValueInput'
                return result
            def side_truth(side,label):
                if side is None:return {'is_null':True}
                result={'is_null':False,'entity_type':side.objectType,'alignment_type':int(side.alignmentType),'rib_type':int(side.ribType)}
                for name in ('diameter','draftAngle','offsetClearance','rootRadius','tipRadius'):
                    result[name]=read(label+'.'+name,lambda n=name:value_input(getattr(side,n)))
                return result
            def input_truth(inp,label):
                return {'entity_type':inp.objectType,'is_default_direction':inp.isDefaultDirection,
                    'offset':value_input(inp.offset),'side1':side_truth(inp.side1,label+'.side1'),'side2':side_truth(inp.side2,label+'.side2'),
                    'participant_bodies':[body_truth(b,label+'.body') for b in inp.participantBodies]}
            base_sketch=component.sketches.add(component.xYConstructionPlane);base_sketch.name='BossBaseProfile'
            base_sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(-2.,-2.,0),point(2.,2.,0))
            seed=component.features.extrudeFeatures.addSimple(base_sketch.profiles.item(0),value(.3),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            seed.name='BossBaseExtrude';base=seed.bodies.item(0);base.name='BossParticipant'
            plane_input=component.constructionPlanes.createInput()
            if not plane_input.setByOffset(component.xYConstructionPlane,value(requested['position_plane_z_cm'])):raise RuntimeError('Owned position plane setup failed')
            plane=component.constructionPlanes.add(plane_input);plane.name='BossPositionPlane'
            sketch=component.sketches.add(plane);sketch.name='BossPositionSketch';position=sketch.sketchPoints.add(point(0.,0.,0.))
            sample['source_before_boss']={'position':point_truth(position,'requested_position'),'participant_body':body_truth(base,'requested_participant'),
                'position_plane_origin_cm':list(plane.geometry.origin.asArray()),'position_plane_normal':list(plane.geometry.normal.asArray())}
            inputs=component.features.bossFeatures.createInput()
            if inputs is None:raise RuntimeError('BossFeatures.createInput returned null (availability/setup failure)')
            sample['new_input_side_nulls']={'side1':inputs.side1 is None,'side2':inputs.side2 is None}
            if not inputs.setPositionBySketchPoints(position):raise RuntimeError('Boss position setter rejected owned SketchPoint')
            inputs.participantBodies=[base];inputs.isDefaultDirection=True;inputs.offset=value(0.)
            side=inputs.createSideInput()
            if side is None:raise RuntimeError('Boss createSideInput returned null')
            side.setBlank(value(requested['diameter_cm']))
            side.alignmentType=adsk.fusion.BossAlignmentTypes.BossAlignFlat
            side.ribType=adsk.fusion.BossRibShapeTypes.BossRibShapeNone
            side.draftAngle=value(0.);side.offsetClearance=value(0.);side.rootRadius=value(0.);side.tipRadius=value(0.)
            inputs.side2=side
            sample['actual_input_before_add']=input_truth(inputs,'input_before')
            sample['status']='adding_boss';save({'event':'adding_boss','case':case})
            bosses=component.features.bossFeatures.add(inputs)
            sample['add_returned_feature_count']=len(bosses)
            if not bosses:raise RuntimeError('Boss add returned empty feature list (availability/setup/geometry failure)')
            for i,feature in enumerate(bosses):feature.name='ProbeBlankBoss'+str(i+1)
            sample['compute_all_returned']=design.computeAll()
            sample['actual_features']=[]
            for feature in bosses:
                actual={'entity_type':feature.objectType,'name':feature.name,'entity_token':token(feature,'boss'),
                    'health_state':feature.healthState,'warning':feature.errorOrWarningMessage,
                    'result_bodies':[body_truth(b,'result') for b in feature.bodies]}
                sample['actual_features'].append(actual)
                feature.timelineObject.rollTo(True)
                actual['direction']=list(feature.direction.asArray());actual['is_direction_flipped']=feature.isDirectionFlipped
                actual['is_geometry_opposite']=feature.isGeometryOpposite
                actual['shape_type']=int(feature.shapeType);actual['alignment_type']=int(feature.alignmentType);actual['rib_type']=int(feature.ribType)
                position_definition=feature.positionDefinition
                actual['position_definition_type']=position_definition.objectType
                selected=adsk.fusion.SketchPointsBossPositionDefinition.cast(position_definition)
                if selected is not None:actual['position_points']=[point_truth(p,'actual_position') for p in selected.sketchPoints]
                actual['parameters']={name:read('boss.'+name,lambda n=name:parameter(getattr(feature,n)))
                    for name in ('offset','offsetClearance','diameter','draftAngle','rootRadius','tipRadius')}
                actual['create_input_readback']=read('boss.createInput',lambda:input_truth(feature.createInput(),'actual_input'))
                design.timeline.moveToEnd()
            sample['root_bodies_after']=[body_truth(b,'root_result') for b in component.bRepBodies]
            sample['all_model_parameters']=[parameter(p) for p in component.modelParameters]
            sample['status']='exporting';save({'event':'exporting','case':case})
            options=design.exportManager.createFusionArchiveExportOptions(str(output/sample['file']))
            if not design.exportManager.execute(options):raise RuntimeError('Boss export failed')
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
    (output/'complete.txt').write_text('Boss contrasts finished; inspect actual availability/results/errors.\n')
