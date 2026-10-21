"""Prepared owned SurfaceTrim face/body/SketchLine tool contrasts; root dispatch only.

Pending TrimFeatureInput transactions must finish with add() or cancel() before
any timeline change, export or close. Failed cancellation stops the batch.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CASES = ('sheet_face','sheet_body','sketch_line')


def run(context):
    app=adsk.core.Application.get()
    cases=CASES
    if isinstance(context,dict) and 'cases' in context:
        selected=context['cases']
        if not isinstance(selected,(list,tuple)) or not selected or len(set(selected))!=len(selected) or set(selected)-set(CASES):
            raise ValueError('Select one to three known distinct SurfaceTrim tool cases')
        cases=tuple(case for case in CASES if case in selected)
    source=Path(__file__).resolve();output=source.parent/('surfacetrimtools-'+uuid.uuid4().hex[:12]);output.mkdir()
    executed=source.read_bytes();(output/'executed-generator-source.txt').write_bytes(executed)
    sdk_path=Path(adsk.fusion.__file__);sdk=sdk_path.read_bytes();text=sdk.decode();blocks=[]
    for name in ('TrimFeatures','TrimFeatureInput','TrimFeature','BRepCells','BRepCell','PatchFeatures','PatchFeatureInput','PatchFeature','SketchLines'):
        start=text.index('class '+name+'(');end=text.find('\nclass ',start+1)
        blocks.append(text[start:] if end<0 else text[start:end])
    surface='\n'.join(blocks).encode();(output/'executed-sdk-surface.txt').write_bytes(surface)
    truth=dict(fusion_version=app.version,samples=[],errors=[],planned_cases=list(cases),helper_dependencies=[],
        executed_generator_sha256=hashlib.sha256(executed).hexdigest(),sdk_runtime_module=str(sdk_path),
        sdk_runtime_sha256=hashlib.sha256(sdk).hexdigest(),executed_sdk_surface_sha256=hashlib.sha256(surface).hexdigest(),
        scope='Fresh owned parametric documents only. Independent XY target Patch and XZ sheet face/body tool or XY SketchLine. Exact tool argument, normalized input/rolled feature tool, all temporary cells and current results remain distinct. Cell indices label API enumeration only; selection is an explicit observed geometric request, not persistent/native identity.',
        requested_setup=dict(target_xy_cm=[[-2.,-1.],[2.,1.]],target_z_cm=0.,
            sheet_tool_local_XZ_cm=[[-3.,-1.],[3.,1.]],line_xy_cm=[[-3.,0.],[3.,0.]],
            selection='Clear every cell; remove only the unique target-plane cell with bounding-box center y>0. All other valid cells remain unselected.'),
        transaction_policy='Every returned TrimFeatureInput is added or cancelled in finally before timeline/export/close. A failed cancellation halts the batch and leaves the owned document untouched for diagnosis.')

    if isinstance(context,dict) and context.get('entrypoint_source_path'):
        entrypoint=Path(context['entrypoint_source_path']).resolve()
        if entrypoint.parent!=source.parent or entrypoint.name!='GenerateSurfaceTrimRemainingContrasts.py' or not entrypoint.is_file():
            raise ValueError('Unexpected owned SurfaceTrim resume entrypoint')
        entrypoint_bytes=entrypoint.read_bytes()
        (output/'executed-entrypoint-source.txt').write_bytes(entrypoint_bytes)
        truth['entrypoint_provenance']=dict(source_path=str(entrypoint),
            sha256=hashlib.sha256(entrypoint_bytes).hexdigest(),executed_snapshot='executed-entrypoint-source.txt',
            invocation='Absolute runpy of GenerateSurfaceTrimToolContrasts.py; remaining sheet_body/sketch_line only')

    def persist():
        (output/'ground_truth.json').write_text(json.dumps(truth,indent=2)+'\n')

    def journal(phase,case=None,**fields):
        row=dict(time_utc=datetime.now(timezone.utc).isoformat(),phase=phase,case=case,
            sample_count=len(truth['samples']),error_count=len(truth['errors']),**fields)
        with (output/'journal.jsonl').open('a') as stream:stream.write(json.dumps(row)+'\n')
        (output/'progress.json').write_text(json.dumps(row,indent=2)+'\n');persist()

    def read(label,getter,errors):
        try:return getter()
        except Exception:
            errors.append(dict(getter=label,error=traceback.format_exc()));return None

    def items(collection):
        if hasattr(collection,'item') and hasattr(collection,'count'):
            return [collection.item(i) for i in range(collection.count)]
        return list(collection)

    def xyz(point):return [point.x,point.y,point.z]

    def identity(entity):
        if entity is None:return None
        row,errors={},[]
        for prop in ('objectType','isValid','name','entityToken'):
            if hasattr(type(entity),prop):row[prop]=read(prop,lambda prop=prop:getattr(entity,prop),errors)
        row['getter_errors']=errors;return row

    def geometry_truth(geometry):
        if geometry is None:return None
        row,errors=identity(geometry),[]
        for prop in ('origin','normal','axis','center','referenceVector','startPoint','endPoint'):
            if hasattr(type(geometry),prop):row[prop]=read(prop,lambda prop=prop:xyz(getattr(geometry,prop)),errors)
        for prop in ('radius','surfaceType','curveType'):
            if hasattr(type(geometry),prop):row[prop]=read(prop,lambda prop=prop:getattr(geometry,prop),errors)
        row['getter_errors']=errors;return row

    def face_truth(face):
        row,errors=identity(face),[]
        for prop in ('tempId','area','isParamReversed'):
            row[prop]=read(prop,lambda prop=prop:getattr(face,prop),errors)
        row['body']=read('body',lambda:identity(face.body),errors)
        row['body_parent_component']=read('body.parentComponent',lambda:identity(face.body.parentComponent),errors)
        row['geometry']=read('geometry',lambda:geometry_truth(face.geometry),errors)
        row['edges']=read('edges',lambda:[dict(tempId=edge.tempId,geometry=geometry_truth(edge.geometry),
            start_cm=None if edge.startVertex is None else xyz(edge.startVertex.geometry),
            end_cm=None if edge.endVertex is None else xyz(edge.endVertex.geometry)) for edge in items(face.edges)],errors)
        row['loops']=read('loops',lambda:[dict(isOuter=loop.isOuter,
            coedges=[dict(edge_tempId=coedge.edge.tempId,isOpposedToEdge=coedge.isOpposedToEdge) for coedge in items(loop.coEdges)]) for loop in items(face.loops)],errors)
        row['getter_errors']=errors;return row

    def body_truth(body):
        row,errors=identity(body),[]
        for prop in ('isSolid','area','volume','isVisible','isTemporary'):
            row[prop]=read(prop,lambda prop=prop:getattr(body,prop),errors)
        row['parentComponent']=read('parentComponent',lambda:identity(body.parentComponent),errors)
        row['bounding_box_cm']=read('boundingBox',lambda:dict(min=xyz(body.boundingBox.minPoint),max=xyz(body.boundingBox.maxPoint)),errors)
        row['vertices']=read('vertices',lambda:[dict(tempId=vertex.tempId,position_cm=xyz(vertex.geometry)) for vertex in items(body.vertices)],errors)
        row['faces']=read('faces',lambda:[face_truth(face) for face in items(body.faces)],errors)
        row['getter_errors']=errors;return row

    def bodies_truth(collection):return [body_truth(body) for body in items(collection)]

    def tool_truth(tool):
        if tool is None:return None
        face=adsk.fusion.BRepFace.cast(tool);body=adsk.fusion.BRepBody.cast(tool);line=adsk.fusion.SketchLine.cast(tool)
        if face is not None:return dict(actual_type_branch='BRepFace',value=face_truth(face))
        if body is not None:return dict(actual_type_branch='BRepBody',value=body_truth(body))
        if line is not None:
            row,errors=identity(line),[]
            row['parentSketch']=read('parentSketch',lambda:identity(line.parentSketch),errors)
            row['sketch_transform']=read('parentSketch.transform',lambda:line.parentSketch.transform.asArray(),errors)
            row['sketch_origin']=read('parentSketch.origin',lambda:xyz(line.parentSketch.origin),errors)
            row['geometry_local']=read('geometry',lambda:geometry_truth(line.geometry),errors)
            row['geometry_world']=read('worldGeometry',lambda:geometry_truth(line.worldGeometry),errors)
            row['start_world_cm']=read('startSketchPoint.worldGeometry',lambda:xyz(line.startSketchPoint.worldGeometry),errors)
            row['end_world_cm']=read('endSketchPoint.worldGeometry',lambda:xyz(line.endSketchPoint.worldGeometry),errors)
            row['getter_errors']=errors;return dict(actual_type_branch='SketchLine',value=row)
        return dict(actual_type_branch='Other',value=identity(tool))

    def cells_truth(cells):
        result=[]
        for index,cell in enumerate(items(cells)):
            row,errors=dict(api_enumeration_index=index,identity=identity(cell)),[]
            row['isSelected']=read('isSelected',lambda:cell.isSelected,errors)
            row['sourceTools']=read('sourceTools',lambda:[tool_truth(tool) for tool in items(cell.sourceTools)],errors)
            row['transient_cell_body']=read('cellBody',lambda:body_truth(cell.cellBody),errors)
            row['getter_errors']=errors;result.append(row)
        return result

    def feature_truth(feature,definition=False):
        if feature is None:return None
        row,errors=identity(feature),[]
        for prop in ('healthState','errorOrWarningMessage','isParametric','isSuppressed'):
            row[prop]=read(prop,lambda prop=prop:getattr(feature,prop),errors)
        row['parentComponent']=read('parentComponent',lambda:identity(feature.parentComponent),errors)
        row['timeline_index']=read('timelineObject.index',lambda:feature.timelineObject.index,errors)
        row['bodies']=read('bodies',lambda:bodies_truth(feature.bodies),errors)
        if definition:
            row['trimTool']=read('trimTool',lambda:tool_truth(feature.trimTool),errors)
            row['bRepCells']=read('bRepCells',lambda:cells_truth(feature.bRepCells),errors)
            row['cells_modified_here']=False
        row['getter_errors']=errors;return row

    def parameter_truth(parameter):
        row,errors=identity(parameter),[]
        for prop in ('value','unit','expression','role'):
            row[prop]=read(prop,lambda prop=prop:getattr(parameter,prop),errors)
        row['createdBy']=read('createdBy',lambda:identity(parameter.createdBy),errors)
        row['getter_errors']=errors;return row

    def patch(root,plane,corners,name):
        sketch=root.sketches.add(plane);sketch.name=name+'_Sketch'
        point=adsk.core.Point3D.create
        sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(*corners[0],0.),point(*corners[1],0.))
        if sketch.profiles.count!=1:raise RuntimeError('Owned Patch profile is not unique')
        profile=sketch.profiles.item(0)
        inp=root.features.patchFeatures.createInput(profile,adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        if inp is None:raise RuntimeError('Owned Patch input returned null')
        feature=root.features.patchFeatures.add(inp)
        if feature is None or feature.bodies.count!=1:raise RuntimeError('Owned Patch add did not produce one body')
        feature.name=name;body=feature.bodies.item(0);body.name=name+'_Body'
        if body.isSolid or body.faces.count!=1:raise RuntimeError('Owned rectangular Patch must be one non-solid face')
        return feature,body,sketch

    journal('batch_begin',planned_sample_count=len(cases),output_directory=str(output))
    for case in cases:
        doc,design,pending,feature=None,None,None,None
        transaction_unsettled=False
        sample=dict(case=case,file=case+'.f3d',phase='document_create',getter_errors=[],
            requested=dict(trim_tool_argument_type={'sheet_face':'BRepFace','sheet_body':'BRepBody','sketch_line':'SketchLine'}[case],
                remove_target_positive_y_half=True,targetBaseFeature_set=False))
        truth['active_sample']=sample
        try:
            doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            if design is None:raise RuntimeError('Owned document lacks Fusion design')
            design.designType=adsk.fusion.DesignTypes.ParametricDesignType;root=design.rootComponent
            sample['root_component']=identity(root)
            sample['phase']='owned_target_patch_setup'
            target_feature,target,target_sketch=patch(root,root.xYConstructionPlane,[[-2.,-1.],[2.,1.]],'OwnedTrimTarget_'+case)
            sample['target_patch_sketch']=dict(identity=identity(target_sketch),transform=target_sketch.transform.asArray())
            tool_body=None;tool_feature=None
            if case=='sketch_line':
                sketch=root.sketches.add(root.xYConstructionPlane);sketch.name='OwnedTrimLine_'+case
                tool=sketch.sketchCurves.sketchLines.addByTwoPoints(adsk.core.Point3D.create(-3.,0.,0.),adsk.core.Point3D.create(3.,0.,0.))
            else:
                tool_feature,tool_body,tool_sketch=patch(root,root.xZConstructionPlane,[[-3.,-1.],[3.,1.]],'OwnedTrimTool_'+case)
                sample['tool_patch_sketch']=dict(identity=identity(tool_sketch),transform=tool_sketch.transform.asArray())
                tool=tool_body.faces.item(0) if case=='sheet_face' else tool_body
            design.timeline.moveToEnd()
            sample['exact_createInput_tool_argument']=tool_truth(tool)
            sample['target_body_before_trim']=body_truth(target)
            sample['tool_body_before_trim']=None if tool_body is None else body_truth(tool_body)
            sample['target_patch_feature_before_trim']=feature_truth(target_feature)
            sample['tool_patch_feature_before_trim']=feature_truth(tool_feature)
            sample['component_bodies_before_trim']=bodies_truth(root.bRepBodies)
            sample['trim_collection_count_before']=root.features.trimFeatures.count
            sample['phase']='trim_transaction'
            try:
                journal('trim_createInput_begin',case)
                transaction_unsettled=True
                pending=root.features.trimFeatures.createInput(tool)
                sample['createInput_returned_nonnull']=pending is not None
                if pending is None:
                    transaction_unsettled=False
                    sample['transaction_completion']='createInput returned null; no input object to cancel'
                    raise RuntimeError('Trim createInput returned null')
                journal('trim_transaction_started',case)
                sample['input_identity']=identity(pending)
                sample['input_actual_trimTool']=read('input.trimTool',lambda:tool_truth(pending.trimTool),sample['getter_errors'])
                sample['input_targetBaseFeature']=read('input.targetBaseFeature',lambda:identity(pending.targetBaseFeature),sample['getter_errors'])
                cells=pending.bRepCells
                sample['input_cells_before_selection']=cells_truth(cells)
                sample['clear_cell_selection_assignments']=[]
                for index,cell in enumerate(items(cells)):
                    cell.isSelected=False
                    sample['clear_cell_selection_assignments'].append(dict(api_enumeration_index=index,actual_after=bool(cell.isSelected)))
                    if cell.isSelected:raise RuntimeError('An owned trim cell did not clear its selection')
                sample['input_cells_after_clearing']=cells_truth(cells)
                positive,negative=[],[];candidates=[]
                for index,cell in enumerate(items(cells)):
                    bounds=cell.cellBody.boundingBox;lo=xyz(bounds.minPoint);hi=xyz(bounds.maxPoint)
                    center=[(a+b)/2. for a,b in zip(lo,hi)]
                    target_plane=(abs(lo[2])<1e-7 and abs(hi[2])<1e-7)
                    target_extent=(abs(lo[0]+2.)<1e-7 and abs(hi[0]-2.)<1e-7 and lo[1]>=-1.-1e-7 and hi[1]<=1.+1e-7)
                    eligible=target_plane and target_extent and hi[1]-lo[1]>1e-7
                    candidates.append(dict(api_enumeration_index=index,bounding_box_min_cm=lo,bounding_box_max_cm=hi,
                        bounding_box_center_cm=center,target_plane_bounds_match=target_plane,target_extent_bounds_match=target_extent,
                        eligible_for_owned_target_half_request=eligible))
                    if eligible and center[1]>1e-7:positive.append(index)
                    if eligible and center[1]<-1e-7:negative.append(index)
                sample['selection_candidate_geometry']=candidates
                sample['positive_y_target_candidate_indices']=positive;sample['negative_y_target_candidate_indices']=negative
                if len(positive)!=1 or len(negative)!=1:raise RuntimeError('Trim cell geometry did not produce one unambiguous positive and negative target half')
                cells.item(positive[0]).isSelected=True
                sample['input_cells_after_selection']=cells_truth(cells)
                selected=[index for index,cell in enumerate(items(cells)) if cell.isSelected]
                sample['selected_input_cell_indices']=selected
                if selected!=positive:raise RuntimeError('Actual selected trim cells disagree with the unique target-half request')
                journal('trim_add_begin',case,selected_cell_indices=selected)
                feature=root.features.trimFeatures.add(pending)
                sample['add_returned_feature']=feature is not None
                if feature is None:raise RuntimeError('Trim add returned null')
                pending=None;transaction_unsettled=False
                sample['transaction_completion']='add returned feature'
                feature.name='OwnedSurfaceTrim_'+case;sample['trim_status']='FeatureReturned'
                journal('trim_feature_returned',case)
            except Exception:
                sample['trim_status']='AttemptError'
                error=dict(case=case,phase='trim_transaction',error=traceback.format_exc())
                sample['trim_error']=error;truth['errors'].append(error);journal('trim_attempt_error',case)
            finally:
                if pending is not None:
                    journal('pending_trim_cancel_begin',case)
                    cancelled=pending.cancel();sample['pending_trim_cancel_returned']=bool(cancelled)
                    journal('pending_trim_cancel_returned',case,returned=bool(cancelled))
                    if not cancelled:raise RuntimeError('Pending Trim input cancel returned false; batch must halt before timeline/export/close')
                    pending=None;transaction_unsettled=False;sample['transaction_completion']='cancel returned true'
            if pending is not None or transaction_unsettled:raise RuntimeError('Unfinished or uncertain Trim transaction before timeline operations')
            design.timeline.moveToEnd();sample['compute_all_returned']=bool(design.computeAll())
            sample['feature_at_timeline_end']=feature_truth(feature)
            sample['component_bodies_after_trim']=bodies_truth(root.bRepBodies)
            sample['original_target_handle_after_trim']=read('original target after trim',lambda:body_truth(target),sample['getter_errors'])
            sample['original_tool_handle_after_trim']=read('original tool after trim',lambda:tool_truth(tool),sample['getter_errors'])
            sample['model_parameters_after']=[parameter_truth(parameter) for parameter in items(root.modelParameters)]
            if feature is not None:
                try:
                    rolled=feature.timelineObject.rollTo(True);sample['roll_before_feature_returned']=bool(rolled)
                    if rolled:
                        sample['feature_before_node']=feature_truth(feature,True)
                        sample['component_bodies_before_node']=bodies_truth(root.bRepBodies)
                        sample['original_target_handle_before_node']=read('original target before node',lambda:body_truth(target),sample['getter_errors'])
                        sample['original_tool_argument_before_node']=read('original tool before node',lambda:tool_truth(tool),sample['getter_errors'])
                except Exception:
                    sample['getter_errors'].append(dict(getter='owned Trim roll/snapshot',error=traceback.format_exc()))
                finally:design.timeline.moveToEnd()
            sample['trim_collection_count_after']=root.features.trimFeatures.count
            sample['timeline_count']=design.timeline.count;sample['timeline_marker_position']=design.timeline.markerPosition
            sample['phase']='local_export';journal('local_export_begin',case,file=sample['file'])
            destination=output/sample['file'];success=design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(destination)))
            if not success or not destination.is_file() or destination.stat().st_size==0:raise RuntimeError('Owned local SurfaceTrim export did not complete')
            sample['export']=dict(returned_success=bool(success),size_bytes=destination.stat().st_size,sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
            sample['phase']='export_complete';truth['samples'].append(sample);truth.pop('active_sample',None)
            journal('local_export_complete',case,file=sample['file'])
        except Exception:
            truth['errors'].append(dict(case=case,phase=sample['phase'],error=traceback.format_exc(),partial_sample=sample))
            truth.pop('active_sample',None);journal('case_error',case)
        finally:
            if pending is None and not transaction_unsettled:
                if design is not None:
                    try:design.timeline.moveToEnd()
                    except Exception:truth['errors'].append(dict(case=case,phase='restore_owned_timeline',error=traceback.format_exc()))
                if doc is not None:
                    try:
                        journal('owned_document_close_begin',case,save=False)
                        closed=doc.close(False);sample['close_owned_document_returned']=bool(closed)
                        if not closed:truth['errors'].append(dict(case=case,phase='close_owned_document',error='close(False) returned false'))
                        journal('owned_document_close_returned',case,save=False,returned=bool(closed))
                    except Exception:truth['errors'].append(dict(case=case,phase='close_owned_document',error=traceback.format_exc()))
            else:
                sample['cleanup_status']='Halted with unfinished or uncertain owned Trim transaction after failed cancellation or createInput exception; no timeline/export/close attempted'
                truth['halted_unfinished_transaction']=dict(case=case,owned_document=identity(doc),reason=sample['cleanup_status'])
                journal('batch_halted_unfinished_transaction',case)
            persist()
        if pending is not None or transaction_unsettled:break
    truth['terminal_status']='HaltedUnfinishedTransaction' if truth.get('halted_unfinished_transaction') else ('Complete' if not truth['errors'] else 'CompleteWithErrors')
    journal('batch_complete',terminal_status=truth['terminal_status'])
    (output/'complete.txt').write_text('SurfaceTrim tool capture finished; consult terminal_status, ground_truth.json and journal.jsonl.\n')
