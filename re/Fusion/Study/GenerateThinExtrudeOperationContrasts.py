"""Prepared owned Join/Cut/Intersect thin-extrude captures; parent dispatch only.

A thin rectangular ring intersects an owned block and extends above it. Actual
failure, participant/result counts and topology are captured without an outcome
assumption. No existing document or global display setting is changed.
"""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import runpy
import traceback
import uuid

import adsk.core
import adsk.fusion

HELPER=Path('/Users/stephenh/.codex/visualizations/2026/10/17/01a14ba1-a51c-7f72-b92e-9f1f0114012e/FusionFileStudy/GenerateThinExtrudeContrasts.py')
CASES={'join':'JoinFeatureOperation','cut':'CutFeatureOperation','intersect':'IntersectFeatureOperation'}


def run(context):
    app=adsk.core.Application.get()
    cases=CASES
    if isinstance(context,dict) and 'cases' in context:
        selected=context['cases']
        if not isinstance(selected,(list,tuple)) or not selected or len(set(selected))!=len(selected) or set(selected)-set(CASES):
            raise ValueError('Select distinct known Thin Extrude operation cases')
        cases={n:c for n,c in CASES.items() if n in selected}
    source=Path(__file__).resolve()
    output=source.parent/('thinextrudeoperations-'+uuid.uuid4().hex[:12]);output.mkdir()
    source_bytes=source.read_bytes();helper_bytes=HELPER.read_bytes()
    (output/'executed-generator-source.txt').write_bytes(source_bytes)
    (output/'executed-thin-source-helper.txt').write_bytes(helper_bytes)
    helper=runpy.run_path(str(HELPER.resolve()),run_name='owned_thin_operation_source_helpers')
    source_config=dict(helper['CONFIGS']['closed_side1'])
    sdk_path=Path(adsk.fusion.__file__).resolve()
    if sdk_path.suffix=='.pyc' and sdk_path.with_suffix('.py').is_file():sdk_path=sdk_path.with_suffix('.py')
    sdk_bytes=sdk_path.read_bytes();sdk_text=sdk_bytes.decode('utf-8');blocks=[]
    for name in ('FeatureOperations','ThinExtrudeWallLocation','ExtentDirections','DistanceExtentDefinition','ExtrudeFeatures','ExtrudeFeatureInput','ExtrudeFeature'):
        start=sdk_text.index('class '+name+'(');end=sdk_text.find('\nclass ',start+1)
        blocks.append(sdk_text[start:end if end>=0 else None])
    sdk_snapshot='\n\n'.join(blocks)
    (output/'executed-sdk-thin-operation-surface.txt').write_text(sdk_snapshot)
    truth=dict(fusion_version=app.version,samples=[],errors=[],planned_cases=list(cases),
        executed_generator_sha256=hashlib.sha256(source_bytes).hexdigest(),
        source_helper_path=str(HELPER.resolve()),source_helper_sha256=hashlib.sha256(helper_bytes).hexdigest(),
        source_helper_snapshot='executed-thin-source-helper.txt',source_config=source_config,
        helper_scope='Absolute runpy reads owned Thin Extrude CONFIGS.closed_side1 length/thickness/wall location; its run is never called. Geometry/serializers are in executed generator snapshot.',
        sdk_runtime_module=str(sdk_path),sdk_runtime_source_sha256=hashlib.sha256(sdk_bytes).hexdigest(),
        sdk_surface_snapshot='executed-sdk-thin-operation-surface.txt',sdk_surface_snapshot_sha256=hashlib.sha256(sdk_snapshot.encode()).hexdigest(),
        operation_enum_values={n:int(getattr(adsk.fusion.FeatureOperations,n)) for n in CASES.values()},
        wall_location_enum_values={n:int(getattr(adsk.fusion.ThinExtrudeWallLocation,n)) for n in ('Side1','Center','Side2')},
        sdk_scope='Documented ExtrudeFeatures.createInput(profile,operation), DistanceExtentDefinition/setOneSideExtent, setThinExtrude; feature profile/participant reads under rollback. No unsupported C++/UI calls.',
        requested_geometry=dict(block_min_xy_cm=[-1.,-1.],block_max_xy_cm=[5.,4.],block_height_cm=1.5,
            thin_rectangle_min_xy_cm=[0.,0.],thin_rectangle_max_xy_cm=[4.,3.],thin_positive_length_cm=source_config['length_one'],
            thin_wall_location=source_config['one'],thin_wall_thickness_cm=source_config['thickness_one']),
        participant_scope='Explicit singleton participantBodies only for Cut/Intersect where documented; Join participant getter/setter not called and marked NotApplicable.',
        result_scope='Owned block and closed ring overlap; no operation success, body count, exact volume, topology or regeneration outcome assumed. Actual errors and geometry retained.',
        identity_scope='Selected profile/sketch and participant handles captured before use/under rollback; opaque tokens and temporary topology IDs stay literal and never become native record identities.')

    def persist():(output/'ground_truth.json').write_text(json.dumps(truth,indent=2)+'\n')
    def journal(phase,case=None,**fields):
        row=dict(time_utc=datetime.now(timezone.utc).isoformat(),phase=phase,case=case,
            sample_count=len(truth['samples']),error_count=len(truth['errors']),**fields)
        with (output/'journal.jsonl').open('a') as stream:stream.write(json.dumps(row)+'\n')
        (output/'progress.json').write_text(json.dumps(row,indent=2)+'\n');persist()
    def observe(label,getter,errors):
        try:return getter()
        except Exception:errors.append(dict(getter=label,error=traceback.format_exc()));return None
    def items(collection):
        if collection is None:return None
        if hasattr(collection,'item') and hasattr(collection,'count'):return [collection.item(i) for i in range(collection.count)]
        return list(collection)
    def identity(entity):
        if entity is None:return None
        row,errors={},[]
        for prop in ('objectType','isValid','name','entityToken'):
            if hasattr(type(entity),prop):row[prop]=observe(prop,lambda prop=prop:getattr(entity,prop),errors)
        row['getter_errors']=errors
        return row
    def point3(value):return list(value.asArray())
    def bounds(value):return dict(min=point3(value.minPoint),max=point3(value.maxPoint))
    def geometry(value):
        if value is None:return None
        row,errors=identity(value),[]
        plane=adsk.core.Plane.cast(value)
        line=adsk.core.Line3D.cast(value)
        circle=adsk.core.Circle3D.cast(value)
        if plane:
            row['origin_cm']=observe('Plane.origin',lambda:point3(plane.origin),errors)
            row['normal']=observe('Plane.normal',lambda:point3(plane.normal),errors)
        elif line:
            row['start_cm']=observe('Line3D.startPoint',lambda:point3(line.startPoint),errors)
            row['end_cm']=observe('Line3D.endPoint',lambda:point3(line.endPoint),errors)
        elif circle:
            row['center_cm']=observe('Circle3D.center',lambda:point3(circle.center),errors)
            row['normal']=observe('Circle3D.normal',lambda:point3(circle.normal),errors)
            row['radius_cm']=observe('Circle3D.radius',lambda:circle.radius,errors)
        row['geometry_getter_errors']=errors
        return row
    def vertex(v):
        row,errors=identity(v),[]
        row['tempId']=observe('vertex.tempId',lambda:v.tempId,errors)
        row['position_cm']=observe('vertex.geometry',lambda:point3(v.geometry),errors)
        row['vertex_getter_errors']=errors
        return row
    def edge(e):
        row,errors=identity(e),[]
        for prop in ('tempId','length','isDegenerate'):
            row[prop]=observe('edge.'+prop,lambda prop=prop:getattr(e,prop),errors)
        row['start_vertex']=observe('edge.startVertex',lambda:vertex(e.startVertex) if e.startVertex else None,errors)
        row['end_vertex']=observe('edge.endVertex',lambda:vertex(e.endVertex) if e.endVertex else None,errors)
        row['geometry']=observe('edge.geometry',lambda:geometry(e.geometry),errors)
        row['edge_getter_errors']=errors
        return row
    def face(f):
        row,errors=identity(f),[]
        for prop in ('tempId','area','isParamReversed'):
            row[prop]=observe('face.'+prop,lambda prop=prop:getattr(f,prop),errors)
        row['geometry']=observe('face.geometry',lambda:geometry(f.geometry),errors)
        row['edge_temp_ids']=observe('face.edges',lambda:[e.tempId for e in items(f.edges)],errors)
        row['vertex_temp_ids']=observe('face.vertices',lambda:[v.tempId for v in items(f.vertices)],errors)
        row['face_getter_errors']=errors
        return row
    def body(b):
        if b is None:return None
        row,errors=identity(b),[]
        for prop in ('isSolid','area','volume','isVisible'):
            row[prop]=observe('body.'+prop,lambda prop=prop:getattr(b,prop),errors)
        row['bounds_cm']=observe('body.boundingBox',lambda:bounds(b.boundingBox),errors)
        row['parentComponent']=observe('body.parentComponent',lambda:identity(b.parentComponent),errors)
        row['vertices']=observe('body.vertices',lambda:[vertex(v) for v in items(b.vertices)],errors)
        row['edges']=observe('body.edges',lambda:[edge(e) for e in items(b.edges)],errors)
        row['faces']=observe('body.faces',lambda:[face(f) for f in items(b.faces)],errors)
        row['topology_ID_scope']='Actual API temporary IDs only, not native object or persistent topology IDs'
        row['body_getter_errors']=errors
        return row
    def component_bodies(component):
        errors=[];values=observe('component.bRepBodies',lambda:items(component.bRepBodies),errors)
        return dict(count=len(values) if values is not None else None,bodies=[body(b) for b in values] if values is not None else None,getter_errors=errors)
    def parameter(p):
        if p is None:return None
        row,errors=identity(p),[]
        for prop in ('name','role','value','unit','expression'):
            row[prop]=observe('parameter.'+prop,lambda prop=prop:getattr(p,prop),errors)
        row['createdBy']=observe('parameter.createdBy',lambda:identity(p.createdBy),errors)
        row['parameter_getter_errors']=errors
        return row
    def numeric(value):
        if value is None:return None
        if adsk.fusion.ModelParameter.cast(value) is not None:return parameter(value)
        row,errors=identity(value),[]
        if adsk.core.ValueInput.cast(value) is not None:
            row['valueType']=observe('ValueInput.valueType',lambda:int(value.valueType),errors)
            row['realValue']=observe('ValueInput.realValue',lambda:value.realValue,errors)
        row['numeric_getter_errors']=errors
        return row
    def profile(p):
        if p is None:return None
        row,errors=identity(p),[]
        sketch=observe('profile.parentSketch',lambda:p.parentSketch,errors)
        row['parentSketch']=identity(sketch)
        if sketch is not None:
            row['sketch_transform']=observe('sketch.transform',lambda:list(sketch.transform.asArray()),errors)
        def loops():
            rows=[]
            for loop in items(p.profileLoops):
                curves=[]
                for pc in items(loop.profileCurves):
                    curve=pc.sketchEntity;entry=identity(curve)
                    line=adsk.fusion.SketchLine.cast(curve)
                    if line:
                        entry['start_world_cm']=point3(line.startSketchPoint.worldGeometry)
                        entry['end_world_cm']=point3(line.endSketchPoint.worldGeometry)
                    curves.append(entry)
                rows.append(dict(isOuter=loop.isOuter,curves=curves))
            return rows
        row['loops']=observe('profile.profileLoops',loops,errors)
        row['profile_getter_errors']=errors
        return row
    def extent(e):
        row,errors=identity(e),[]
        distance=adsk.fusion.DistanceExtentDefinition.cast(e)
        if distance is not None:row['distance']=observe('DistanceExtentDefinition.distance',lambda:numeric(distance.distance),errors)
        row['extent_getter_errors']=errors
        return row
    def controls(entity,operation_name,is_input=False):
        row,errors=identity(entity),[]
        for prop in ('operation','isThinExtrude','isSolid','hasTwoExtents','thinExtrudeWallLocationOne'):
            row[prop]=observe(prop,lambda prop=prop:int(getattr(entity,prop)) if prop in ('operation','thinExtrudeWallLocationOne') else getattr(entity,prop),errors)
        row['thinExtrudeWallThicknessOne']=observe('thinExtrudeWallThicknessOne',lambda:numeric(entity.thinExtrudeWallThicknessOne),errors)
        row['side_two']=dict(status='NotApplicable',getter_called=False,setter_called=False,reason='One-sided extrusion only')
        row['profile']=observe('profile',lambda:profile(entity.profile),errors)
        row['extentOne']=observe('extentOne',lambda:extent(entity.extentOne),errors)
        if is_input:row['targetBaseFeature']=observe('targetBaseFeature',lambda:identity(entity.targetBaseFeature),errors)
        else:
            row['startExtent']=observe('startExtent',lambda:identity(entity.startExtent),errors)
            row['taperAngleOne']=observe('taperAngleOne',lambda:parameter(entity.taperAngleOne),errors)
            row['extentType']=observe('extentType',lambda:int(entity.extentType),errors)
        if operation_name in ('cut','intersect'):
            row['participantBodies']=observe('participantBodies',lambda:None if entity.participantBodies is None else [body(b) for b in items(entity.participantBodies)],errors)
            row['participant_applicability']=dict(status='Applicable',getter_called=True)
        else:
            row['participantBodies']=None
            row['participant_applicability']=dict(status='NotApplicable',getter_called=False,setter_called=False,reason='SDK participantBodies applies to Cut/Intersect; Join uses actual source/result evidence')
        row['control_getter_errors']=errors
        return row
    def feature_summary(feature):
        if feature is None:return None
        row,errors=identity(feature),[]
        for prop in ('healthState','errorOrWarningMessage','isParametric','isSuppressed','operation','isThinExtrude'):
            row[prop]=observe(prop,lambda prop=prop:int(getattr(feature,prop)) if prop in ('healthState','operation') else getattr(feature,prop),errors)
        row['timeline_index']=observe('timelineObject.index',lambda:feature.timelineObject.index,errors)
        row['result_bodies']=observe('feature.bodies',lambda:[body(b) for b in items(feature.bodies)],errors)
        row['feature_getter_errors']=errors
        return row

    journal('batch_begin',output_directory=str(output))
    for case,operation_enum in cases.items():
        doc=design=None
        sample=dict(case=case,file=case+'.f3d',phase='new_document',getter_errors=[],setter_errors=[],requested=dict(
            operation=operation_enum,wall_location=source_config['one'],wall_thickness_cm=source_config['thickness_one'],
            extent_cm=source_config['length_one'],explicit_participant_set=case in ('cut','intersect')))
        truth['active_sample']=sample
        try:
            doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            if design is None:raise RuntimeError('Owned document has no Fusion Design')
            design.designType=adsk.fusion.DesignTypes.ParametricDesignType
            component=design.rootComponent
            sample['root_component']=identity(component)
            point=adsk.core.Point3D.create;value=adsk.core.ValueInput.createByReal
            seed_sketch=component.sketches.add(component.xYConstructionPlane);seed_sketch.name='OwnedThinOperationBlockProfile'
            seed_sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(-1.,-1.,0.),point(5.,4.,0.))
            seed_profile=seed_sketch.profiles.item(0)
            sample['seed_block_profile']=profile(seed_profile)
            seed=component.features.extrudeFeatures.addSimple(seed_profile,value(1.5),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            if seed is None:raise RuntimeError('Owned target block extrusion returned null')
            seed.name='OwnedThinOperationTargetBlockExtrude'
            if seed.bodies.count!=1:raise RuntimeError('Owned target block did not produce exactly one selectable BRepBody')
            target=seed.bodies.item(0);target.name='OwnedThinOperationTarget_'+case
            sample['seed_feature']=feature_summary(seed)
            sample['source_target_before_thin']=body(target)
            sample['component_bodies_before_thin']=component_bodies(component)
            sketch=component.sketches.add(component.xYConstructionPlane);sketch.name='OwnedThinOperationRingProfile'
            sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0.,0.,0.),point(4.,3.,0.))
            selected_profile=sketch.profiles.item(0)
            sample['source_thin_profile_before_feature']=profile(selected_profile)
            sample['model_parameters_before_thin']=[parameter(p) for p in component.modelParameters]
            feature=None
            try:
                sample['phase']='define_thin_operation';journal('thin_operation_define_begin',case)
                operation=getattr(adsk.fusion.FeatureOperations,operation_enum)
                inputs=component.features.extrudeFeatures.createInput(selected_profile,operation)
                if inputs is None:raise RuntimeError('Thin operation createInput returned null')
                requested_extent=adsk.fusion.DistanceExtentDefinition.create(value(source_config['length_one']))
                sample['set_extent_returned']=inputs.setOneSideExtent(requested_extent,adsk.fusion.ExtentDirections.PositiveExtentDirection)
                if not sample['set_extent_returned']:raise RuntimeError('Thin operation one-sided extent rejected')
                sample['set_thin_returned']=inputs.setThinExtrude(getattr(adsk.fusion.ThinExtrudeWallLocation,source_config['one']),value(source_config['thickness_one']))
                if not sample['set_thin_returned']:raise RuntimeError('Thin operation setThinExtrude rejected')
                sample['input_before_explicit_participant']=controls(inputs,case,True)
                if case in ('cut','intersect'):
                    try:inputs.participantBodies=[target]
                    except Exception:
                        sample['setter_errors'].append(dict(property='participantBodies',error=traceback.format_exc()));raise
                    sample['participant_setter_status']='Completed assignment; actual getters captured independently'
                    sample['input_participant_handle_equality']=observe('input.participantBodies singleton equals owned target',lambda:len(inputs.participantBodies)==1 and inputs.participantBodies[0]==target,sample['getter_errors'])
                else:sample['participant_setter_status']='NotApplicable: Join participantBodies not invoked'
                sample['actual_input_before_add']=controls(inputs,case,True)
                journal('thin_operation_add_begin',case)
                feature=component.features.extrudeFeatures.add(inputs)
                sample['add_returned_nonnull']=feature is not None
                if feature is None:raise RuntimeError('Parametric thin operation add returned null')
                feature.name='OwnedThinExtrudeOperation_'+case
                sample['operation_status']='FeatureReturned'
                journal('thin_operation_feature_returned',case)
            except Exception:
                sample['operation_status']='AttemptError'
                error=dict(case=case,phase=sample['phase'],error=traceback.format_exc(),scope='Actual owned API operation failure retained; source/setup archive exported, no native thin feature invented')
                sample['operation_error']=error;truth['errors'].append(error);journal('thin_operation_attempt_error',case)
            design.timeline.moveToEnd()
            sample['compute_all_returned']=observe('design.computeAll',lambda:design.computeAll(),sample['getter_errors'])
            sample['feature_at_timeline_end']=feature_summary(feature)
            sample['component_bodies_after_thin']=component_bodies(component)
            sample['original_target_handle_after_thin']=identity(target)
            sample['current_body_vs_original_target_handle_equality']=observe('current bodies vs original target handle',lambda:[b==target for b in items(component.bRepBodies)],sample['getter_errors'])
            sample['model_parameters_after_thin']=[parameter(p) for p in component.modelParameters]
            if feature is not None:
                try:
                    sample['roll_before_feature_returned']=bool(feature.timelineObject.rollTo(True))
                    if sample['roll_before_feature_returned']:
                        sample['feature_before_node']=controls(feature,case)
                        sample['component_bodies_before_node']=component_bodies(component)
                        if case in ('cut','intersect'):
                            sample['rolled_participant_handle_equality']=observe('rolled participantBodies equals owned target',lambda:len(feature.participantBodies)==1 and feature.participantBodies[0]==target,sample['getter_errors'])
                except Exception:sample['getter_errors'].append(dict(getter='Thin operation rolled definition snapshot',error=traceback.format_exc()))
                finally:design.timeline.moveToEnd()
            sample['timeline_count']=design.timeline.count;sample['timeline_marker_position']=design.timeline.markerPosition
            sample['phase']='local_export';journal('local_export_begin',case)
            destination=output/sample['file']
            accepted=design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(destination)))
            if not accepted or not destination.is_file() or not destination.stat().st_size:raise RuntimeError('Owned thin operation local export failed')
            sample['export']=dict(returned_success=bool(accepted),size_bytes=destination.stat().st_size,sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
            sample['phase']='export_complete';truth['samples'].append(sample);journal('local_export_complete',case)
        except Exception:
            truth['errors'].append(dict(case=case,phase=sample['phase'],error=traceback.format_exc(),partial_sample=sample));journal('case_error',case)
        finally:
            if design is not None:
                try:design.timeline.moveToEnd()
                except Exception:truth['errors'].append(dict(case=case,phase='restore_owned_timeline',error=traceback.format_exc()))
            if doc is not None:
                try:
                    journal('owned_document_close_begin',case,save=False)
                    returned=bool(doc.close(False));sample['close_owned_document_returned']=returned
                    journal('owned_document_close_returned',case,save=False,returned=returned)
                    if not returned:truth['errors'].append(dict(case=case,phase='owned_document_close',error='close(False) returned false'))
                except Exception:truth['errors'].append(dict(case=case,phase='owned_document_close',error=traceback.format_exc()))
            truth.pop('active_sample',None);persist()
    truth['terminal_status']='complete' if len(truth['samples'])==len(cases) and not truth['errors'] else 'complete_with_errors'
    truth['exported_sample_count']=len(truth['samples']);journal('batch_complete')
    (output/'complete.txt').write_text('Thin Extrude operation terminal: '+truth['terminal_status']+'; inspect actual operation/participant/results/errors.\n')
