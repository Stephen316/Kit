"""Prepared owned Profile SplitBody tools; root dispatch only.

Full rectangular Profile/one or two blocks; small Profile/extensionTrue. Profiles
remain sketch sources; no Patch or transient Profile.face tool body is created.
Exact API arguments and normalized rolled feature getters are captured separately.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CASES = {
    'full_profile_one_body': {'body_count': 1, 'extend': False, 'small': False},
    'small_profile_extended': {'body_count': 1, 'extend': True, 'small': True},
    'full_profile_two_bodies': {'body_count': 2, 'extend': False, 'small': False},
}


def run(context):
    app = adsk.core.Application.get()
    cases = CASES
    if isinstance(context, dict) and 'cases' in context:
        selected = context['cases']
        if not isinstance(selected, (list,tuple)) or not selected or len(set(selected)) != len(selected) or set(selected)-set(CASES):
            raise ValueError('Select one to three known distinct Profile SplitBody cases')
        cases = {name:spec for name,spec in CASES.items() if name in selected}
    source = Path(__file__).resolve()
    output = source.parent/('splitbodyprofiles-'+uuid.uuid4().hex[:12])
    output.mkdir()
    executed = source.read_bytes()
    (output/'executed-generator-source.txt').write_bytes(executed)
    sdk_path = Path(adsk.fusion.__file__)
    sdk = sdk_path.read_bytes()
    sdk_text = sdk.decode()
    sdk_blocks = []
    for name in ('SplitBodyFeatures','SplitBodyFeatureInput','SplitBodyFeature','ConstructionPlaneInput','Profile','ProfileLoop','ProfileCurve','Sketch','SketchLine','SketchPoint'):
        begin = sdk_text.index('class '+name+'(')
        end = sdk_text.find('\nclass ',begin+1)
        sdk_blocks.append(sdk_text[begin:] if end < 0 else sdk_text[begin:end])
    surface = '\n'.join(sdk_blocks).encode()
    (output/'executed-sdk-surface.txt').write_bytes(surface)
    truth = dict(samples=[],errors=[],fusion_version=app.version,planned_cases=list(cases),
        executed_generator_sha256=hashlib.sha256(executed).hexdigest(),
        sdk_runtime_module=str(sdk_path),sdk_runtime_sha256=hashlib.sha256(sdk).hexdigest(),
        executed_sdk_surface_sha256=hashlib.sha256(surface).hexdigest(),helper_dependencies=[],
        scope='Fresh owned parametric documents; one or two separate source solids and an independent sketch Profile. Exact Profile argument and body/ObjectCollection argument are captured separately from normalized input/rolled feature getters. No Patch/Profile.face tool BODY creation, token-derived native IDs, or source/result pairing.',
        source_setup=dict(block_xy_cm=[[[0,0],[4,3]],[[6,0],[10,3]]],block_height_cm=2.0,
            full_profile_xy_cm=[[-1,-1],[11,4]],small_profile_xy_cm=[[1,1],[3,2]],profile_offset_cm=1.0),
        applicability_scope='SplitBodyFeature.splitBodies and splittingTool require timeline immediately before the feature. Those getters are skipped at timeline end and captured under rollTo(True); end snapshots retain independent result bodies and health.')

    def persist():
        (output/'ground_truth.json').write_text(json.dumps(truth,indent=2)+'\n')

    def journal(phase,case=None,**fields):
        event = dict(time_utc=datetime.now(timezone.utc).isoformat(),phase=phase,case=case,
            sample_count=len(truth['samples']),error_count=len(truth['errors']),**fields)
        with (output/'journal.jsonl').open('a') as stream:
            stream.write(json.dumps(event)+'\n')
        (output/'progress.json').write_text(json.dumps(event,indent=2)+'\n');persist()

    def observe(label,getter,errors):
        try:
            return getter()
        except Exception:
            errors.append(dict(getter=label,error=traceback.format_exc()))
            return None

    def items(value):
        if value is None:
            return None
        if hasattr(value,'item') and hasattr(value,'count'):
            return [value.item(i) for i in range(value.count)]
        return list(value)

    def identity(entity):
        if entity is None:
            return None
        row,errors = {},[]
        for prop in ('objectType','isValid','name','entityToken'):
            if hasattr(type(entity),prop):
                row[prop] = observe(prop,lambda prop=prop:getattr(entity,prop),errors)
        row['getter_errors'] = errors
        return row

    def xyz(point):return [point.x,point.y,point.z]

    def geometry_truth(geometry):
        if geometry is None:
            return None
        row,errors = identity(geometry),[]
        for prop in ('origin','normal','axis','center','referenceVector','startPoint','endPoint'):
            if hasattr(type(geometry),prop):
                row[prop] = observe(prop,lambda prop=prop:xyz(getattr(geometry,prop)),errors)
        for prop in ('radius','halfAngle','surfaceType','curveType'):
            if hasattr(type(geometry),prop):
                row[prop] = observe(prop,lambda prop=prop:int(getattr(geometry,prop)) if prop in ('surfaceType','curveType') else getattr(geometry,prop),errors)
        row['getter_errors'] = errors
        return row

    def face_truth(face):
        row,errors = identity(face),[]
        for prop in ('tempId','area','isParamReversed'):
            row[prop] = observe(prop,lambda prop=prop:getattr(face,prop),errors)
        row['body'] = observe('body',lambda:identity(face.body),errors)
        row['body_parent_component'] = observe('body.parentComponent',lambda:identity(face.body.parentComponent),errors)
        row['geometry'] = observe('geometry',lambda:geometry_truth(face.geometry),errors)
        row['edges'] = observe('edges',lambda:[dict(tempId=edge.tempId,
            start_vertex_tempId=None if edge.startVertex is None else edge.startVertex.tempId,
            end_vertex_tempId=None if edge.endVertex is None else edge.endVertex.tempId,
            geometry=geometry_truth(edge.geometry)) for edge in items(face.edges)],errors)
        row['loops'] = observe('loops',lambda:[dict(isOuter=loop.isOuter,
            coedges=[dict(edge_tempId=coedge.edge.tempId,isOpposedToEdge=coedge.isOpposedToEdge) for coedge in items(loop.coEdges)]) for loop in items(face.loops)],errors)
        row['getter_errors'] = errors
        return row

    def body_truth(body):
        row,errors = identity(body),[]
        for prop in ('tempId','isSolid','area','volume','isVisible'):
            row[prop] = observe(prop,lambda prop=prop:getattr(body,prop),errors)
        row['parentComponent'] = observe('parentComponent',lambda:identity(body.parentComponent),errors)
        row['baseOrFormFeature'] = observe('baseOrFormFeature',lambda:identity(body.baseOrFormFeature),errors)
        row['bounding_box_cm'] = observe('boundingBox',lambda:dict(min=xyz(body.boundingBox.minPoint),max=xyz(body.boundingBox.maxPoint)),errors)
        row['vertices'] = observe('vertices',lambda:[dict(tempId=v.tempId,position_cm=xyz(v.geometry)) for v in items(body.vertices)],errors)
        row['faces'] = observe('faces',lambda:[face_truth(face) for face in items(body.faces)],errors)
        row['getter_errors'] = errors
        return row

    def body_collection(collection):
        bodies = items(collection)
        return None if bodies is None else dict(count=len(bodies),bodies=[body_truth(body) for body in bodies])

    def sketch_curve_truth(entity):
        row,errors = identity(entity),[]
        row['parentSketch'] = observe('parentSketch',lambda:identity(entity.parentSketch),errors)
        for prop in ('geometry','worldGeometry'):
            if hasattr(type(entity),prop):
                row[prop] = observe(prop,lambda prop=prop:geometry_truth(getattr(entity,prop)),errors)
        for prop in ('isConstruction','isReference','isFixed'):
            if hasattr(type(entity),prop):
                row[prop] = observe(prop,lambda prop=prop:getattr(entity,prop),errors)
        for prop in ('startSketchPoint','endSketchPoint'):
            if hasattr(type(entity),prop):
                point = observe(prop,lambda prop=prop:getattr(entity,prop),errors)
                if point is not None:
                    point_row = identity(point)
                    point_row['local_position_cm'] = observe(prop+'.geometry',lambda point=point:xyz(point.geometry),errors)
                    point_row['world_position_cm'] = observe(prop+'.worldGeometry',lambda point=point:xyz(point.worldGeometry),errors)
                    row[prop] = point_row
        row['source_tag_scope'] = 'Active SDK has no public sketch entityTag getter; opaque entityToken retained without decoding it as a native ID'
        row['getter_errors'] = errors
        return row

    def sketch_truth(sketch):
        row,errors = identity(sketch),[]
        row['parentComponent'] = observe('parentComponent',lambda:identity(sketch.parentComponent),errors)
        row['transform'] = observe('transform',lambda:sketch.transform.asArray(),errors)
        row['origin_cm'] = observe('origin',lambda:xyz(sketch.origin),errors)
        row['xDirection'] = observe('xDirection',lambda:xyz(sketch.xDirection),errors)
        row['yDirection'] = observe('yDirection',lambda:xyz(sketch.yDirection),errors)
        row['referencePlane'] = observe('referencePlane',lambda:identity(sketch.referencePlane),errors)
        row['sketchCurves'] = observe('sketchCurves',lambda:[sketch_curve_truth(curve) for curve in items(sketch.sketchCurves)],errors)
        row['profile_count'] = observe('profiles.count',lambda:sketch.profiles.count,errors)
        row['getter_errors'] = errors
        return row

    def profile_truth(profile):
        row,errors = identity(profile),[]
        row['parentSketch'] = observe('parentSketch',lambda:sketch_truth(profile.parentSketch),errors)
        row['API_profile_plane'] = observe('plane',lambda:geometry_truth(profile.plane),errors)
        row['isOnSketchPlane'] = observe('isOnSketchPlane',lambda:profile.isOnSketchPlane,errors)
        loops = []
        profile_loops = observe('profileLoops',lambda:items(profile.profileLoops),errors)
        for loop in profile_loops or []:
            loop_row,loop_errors = identity(loop),[]
            loop_row['isOuter'] = observe('isOuter',lambda:loop.isOuter,loop_errors)
            curves = []
            profile_curves = observe('profileCurves',lambda:items(loop.profileCurves),loop_errors)
            for curve in profile_curves or []:
                curve_row,curve_errors = identity(curve),[]
                curve_row['geometryType'] = observe('geometryType',lambda:int(curve.geometryType),curve_errors)
                curve_row['geometry'] = observe('geometry',lambda:geometry_truth(curve.geometry),curve_errors)
                curve_row['sketchEntity'] = observe('sketchEntity',lambda:sketch_curve_truth(curve.sketchEntity),curve_errors)
                curve_row['parentSketch'] = observe('parentSketch',lambda:identity(curve.parentSketch),curve_errors)
                curve_row['getter_errors'] = curve_errors
                curves.append(curve_row)
            loop_row['profileCurves'] = curves;loop_row['getter_errors'] = loop_errors
            loops.append(loop_row)
        row['profileLoops'] = loops
        row['profile_face_getter'] = 'NotCalled_NoTransientBRepToolIdentityAssumed'
        row['getter_errors'] = errors
        return row

    def selection_truth(value):
        if value is None:
            return None
        if adsk.fusion.Profile.cast(value) is not None:
            return dict(actual_type_branch='Profile',value=profile_truth(value))
        if adsk.fusion.BRepFace.cast(value) is not None:
            return dict(actual_type_branch='BRepFace',value=face_truth(value))
        if adsk.fusion.BRepBody.cast(value) is not None:
            return dict(actual_type_branch='BRepBody',value=body_truth(value))
        if adsk.fusion.ConstructionPlane.cast(value) is not None:
            row,errors = identity(value),[]
            row['geometry'] = observe('geometry',lambda:geometry_truth(value.geometry),errors)
            row['transform'] = observe('transform',lambda:value.transform.asArray(),errors)
            row['getter_errors'] = errors
            return dict(actual_type_branch='ConstructionPlane',value=row)
        if isinstance(value,(list,tuple)) or hasattr(value,'item') and hasattr(value,'count'):
            children = items(value)
            return dict(actual_type_branch='Collection',count=len(children),items=[selection_truth(v) for v in children])
        return dict(actual_type_branch='Other',value=identity(value))

    def feature_truth(feature, definition=False):
        if feature is None:
            return None
        row,errors = identity(feature),[]
        for prop in ('healthState','errorOrWarningMessage','isParametric','isSuppressed'):
            row[prop] = observe(prop,lambda prop=prop:int(feature.healthState) if prop=='healthState' else getattr(feature,prop),errors)
        row['parentComponent'] = observe('parentComponent',lambda:identity(feature.parentComponent),errors)
        row['baseFeature'] = observe('baseFeature',lambda:identity(feature.baseFeature),errors)
        row['timeline_index'] = observe('timelineObject.index',lambda:feature.timelineObject.index,errors)
        row['bodies'] = observe('bodies',lambda:body_collection(feature.bodies),errors)
        row['faces'] = observe('faces',lambda:None if feature.faces is None else [face_truth(face) for face in items(feature.faces)],errors)
        if adsk.fusion.SplitBodyFeature.cast(feature) is not None:
            row['isSplittingToolExtended'] = observe('isSplittingToolExtended',lambda:feature.isSplittingToolExtended,errors)
            if definition:
                row['splitBodies'] = observe('splitBodies',lambda:selection_truth(feature.splitBodies),errors)
                row['splittingTool'] = observe('splittingTool',lambda:selection_truth(feature.splittingTool),errors)
            else:
                row['definition_getter_scope'] = 'splitBodies/splittingTool not called here: SDK requires timeline before feature'
        row['getter_errors'] = errors
        return row

    def input_truth(inp):
        row,errors = identity(inp),[]
        row['splitBodies'] = observe('splitBodies',lambda:selection_truth(inp.splitBodies),errors)
        row['splittingTool'] = observe('splittingTool',lambda:selection_truth(inp.splittingTool),errors)
        row['isSplittingToolExtended'] = observe('isSplittingToolExtended',lambda:inp.isSplittingToolExtended,errors)
        row['targetBaseFeature'] = observe('targetBaseFeature',lambda:identity(inp.targetBaseFeature),errors)
        row['getter_errors'] = errors
        return row

    def parameter_truth(parameter):
        row,errors = identity(parameter),[]
        for prop in ('name','role','expression','unit','value'):
            row[prop] = observe(prop,lambda prop=prop:getattr(parameter,prop),errors)
        row['createdBy'] = observe('createdBy',lambda:identity(parameter.createdBy),errors)
        row['getter_errors'] = errors
        return row

    point,value = adsk.core.Point3D.create,adsk.core.ValueInput.createByString
    journal('batch_begin',output_directory=str(output),planned_sample_count=len(cases))
    for case,spec in cases.items():
        doc,design = None,None
        sample = dict(case=case,file=case+'.f3d',phase='document_create',getter_errors=[],
            requested=dict(splitting_tool_argument_type='Profile',isSplittingToolExtended=spec['extend'],small_profile=spec['small'],
                split_body_count=spec['body_count'],split_body_role='Owned block BRepBody or ObjectCollection',tool_role='Independent owned sketch Profile',targetBaseFeature_set=False))
        truth['active_sample'] = sample
        try:
            journal('owned_document_create_begin',case)
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            if design is None:
                raise RuntimeError('Owned document lacks Fusion design product')
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sample['root_component'] = identity(root)
            sample['bodies_before_setup'] = body_collection(root.bRepBodies)
            sample['phase'] = 'owned_block_setup'
            seeds,solids = [],[]
            for index in range(spec['body_count']):
                sketch = root.sketches.add(root.xYConstructionPlane)
                sketch.name = 'OwnedProfileSplitBlockSketch_'+str(index)+'_'+case
                base_x = 6.0*index
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(base_x,0,0),point(base_x+4,3,0))
                seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0),value('20 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                if seed is None or seed.bodies.count != 1:
                    raise RuntimeError('Owned source block lacks unique body')
                seed.name = 'OwnedProfileSplitBlockExtrude_'+str(index)+'_'+case
                solid = seed.bodies.item(0);solid.name='OwnedProfileSplitBlock_'+str(index)+'_'+case
                seeds.append(seed);solids.append(solid)
            if spec['body_count'] == 1:
                split_argument = solids[0]
            else:
                split_argument = adsk.core.ObjectCollection.create()
                sample['body_collection_add_returns'] = [bool(split_argument.add(body)) for body in solids]
                if not all(sample['body_collection_add_returns']):
                    raise RuntimeError('Owned body ObjectCollection rejected a source body')
            sample['phase'] = 'owned_profile_tool_setup'
            plane_input = root.constructionPlanes.createInput()
            offset = value('10 mm')
            sample['support_plane_setByOffset_returned'] = bool(plane_input.setByOffset(root.xYConstructionPlane,offset))
            if not sample['support_plane_setByOffset_returned']:
                raise RuntimeError('Owned Profile support plane input rejected offset')
            plane = root.constructionPlanes.add(plane_input)
            if plane is None:
                raise RuntimeError('Owned Profile support plane add returned null')
            plane.name='OwnedSplitProfilePlane_'+case
            tool_sketch = root.sketches.add(plane);tool_sketch.name='OwnedSplitProfileBoundary_'+case
            profile_corners = [[1,1],[3,2]] if spec['small'] else [[-1,-1],[11,4]]
            sample['actual_requested_profile_corners_local_cm'] = profile_corners
            tool_sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(profile_corners[0][0],profile_corners[0][1],0),point(profile_corners[1][0],profile_corners[1][1],0))
            if tool_sketch.profiles.count != 1:
                raise RuntimeError('Owned rectangular splitting Profile not unique')
            profile = tool_sketch.profiles.item(0)
            tool = profile
            if root.bRepBodies.count != spec['body_count']:
                raise RuntimeError('Controlled Profile setup unexpectedly added a BRep tool body')
            design.timeline.moveToEnd()
            sample['source_setup_features_before_split'] = [feature_truth(seed) for seed in seeds]
            sample['support_plane_before_split'] = selection_truth(plane)
            sample['profile_tool_before_split'] = profile_truth(profile)
            sample['tool_sketch_before_split'] = sketch_truth(tool_sketch)
            sample['exact_createInput_tool_argument_before_split'] = selection_truth(tool)
            sample['source_solids_before_split'] = [body_truth(body) for body in solids]
            sample['exact_createInput_split_body_argument_before_split'] = selection_truth(split_argument)
            sample['component_bodies_before_split'] = body_collection(root.bRepBodies)
            feature = None
            sample['phase'] = 'split_attempt'
            try:
                sample['split_collection_count_before'] = root.features.splitBodyFeatures.count
                inp = root.features.splitBodyFeatures.createInput(split_argument,tool,spec['extend'])
                if inp is None:
                    raise RuntimeError('SplitBody createInput returned null')
                sample['input_before_add'] = input_truth(inp)
                sample['exact_createInput_arguments'] = dict(split_body_argument_type=split_argument.objectType,
                    splitting_tool_argument_type=tool.objectType,isSplittingToolExtended=spec['extend'])
                journal('split_add_begin',case)
                feature = root.features.splitBodyFeatures.add(inp)
                sample['add_returned_feature'] = feature is not None
                if feature is None:
                    raise RuntimeError('SplitBody add returned null; unchanged document state will be captured/exported')
                feature.name='OwnedSplitBodyProfile_'+case
                sample['split_status']='FeatureReturned'
                journal('split_feature_returned',case)
            except Exception:
                sample['split_status']='AttemptError'
                error=dict(case=case,phase='split_attempt',error=traceback.format_exc(),
                    policy='Preserve actual independent body/tool collections and export; no success inferred from name or requested geometry')
                sample['split_error']=error;truth['errors'].append(error)
                journal('split_attempt_error',case)
            design.timeline.moveToEnd()
            sample['compute_all_returned'] = bool(design.computeAll())
            sample['feature_at_timeline_end'] = feature_truth(feature)
            sample['component_bodies_after_split'] = body_collection(root.bRepBodies)
            sample['original_source_body_handles_after_split'] = [observe('original source body '+str(index)+' after split',lambda body=body:body_truth(body),sample['getter_errors']) for index,body in enumerate(solids)]
            sample['model_parameters_after'] = [parameter_truth(p) for p in items(root.modelParameters)]
            if feature is not None:
                try:
                    rolled = feature.timelineObject.rollTo(True)
                    sample['roll_before_feature_returned'] = bool(rolled)
                    if rolled:
                        sample['feature_before_node'] = feature_truth(feature,True)
                        sample['component_bodies_before_node'] = body_collection(root.bRepBodies)
                        sample['original_tool_argument_before_node'] = observe('original tool rolled',lambda:selection_truth(tool),sample['getter_errors'])
                except Exception:
                    sample['getter_errors'].append(dict(getter='owned SplitBody roll/snapshot',error=traceback.format_exc()))
                finally:
                    design.timeline.moveToEnd()
            sample['split_collection_count_after'] = root.features.splitBodyFeatures.count
            sample['timeline_count'] = design.timeline.count
            sample['timeline_marker_position'] = design.timeline.markerPosition
            sample['phase']='local_export'
            journal('local_export_begin',case,file=sample['file'])
            destination=output/sample['file']
            succeeded=design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(destination)))
            if not succeeded or not destination.is_file() or destination.stat().st_size==0:
                raise RuntimeError('Local owned SplitBody export did not complete')
            sample['export']=dict(returned_success=bool(succeeded),size_bytes=destination.stat().st_size,
                sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
            sample['phase']='export_complete'
            truth['samples'].append(sample);truth.pop('active_sample',None)
            journal('local_export_complete',case,file=sample['file'])
        except Exception:
            truth['errors'].append(dict(case=case,phase=sample['phase'],error=traceback.format_exc(),partial_sample=sample))
            truth.pop('active_sample',None);journal('case_error',case)
        finally:
            if design is not None:
                try:
                    design.timeline.moveToEnd()
                except Exception:
                    truth['errors'].append(dict(case=case,phase='restore_owned_timeline',error=traceback.format_exc()))
            if doc is not None:
                try:
                    journal('owned_document_close_begin',case,save=False)
                    closed=doc.close(False);sample['close_owned_document_returned']=bool(closed)
                    journal('owned_document_close_returned',case,returned=bool(closed),save=False)
                    if not closed:
                        truth['errors'].append(dict(case=case,phase='close_owned_document',error='close(False) returned false'))
                except Exception:
                    truth['errors'].append(dict(case=case,phase='close_owned_document',error=traceback.format_exc()))
            persist()
    truth['terminal_status']='Complete' if not truth['errors'] else 'CompleteWithErrors'
    journal('batch_terminal',planned_sample_count=len(cases),exported_sample_count=len(truth['samples']),terminal_status=truth['terminal_status'])
    (output/'complete.txt').write_text('terminal; inspect all actual source/tool/results and recorded setup/attempt/getter/close errors\n')
