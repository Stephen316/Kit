"""Prepared owned ReplaceFace sheet-face/body targets; root dispatch only.

One 4x3x2cm solid, one independent oversized Patch atz1cm. Direct face, whole
sheet body, and face with tangent-chain True. No user documents/global settings.
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
    'sheet_face': {'target': 'BRepFace', 'tangent': False},
    'sheet_body': {'target': 'BRepBody', 'tangent': False},
    'sheet_face_tangent': {'target': 'BRepFace', 'tangent': True},
}


def run(context):
    app = adsk.core.Application.get()
    cases = CASES
    if isinstance(context, dict) and 'cases' in context:
        selected = context['cases']
        if not isinstance(selected, (list,tuple)) or not selected or len(set(selected)) != len(selected) or set(selected)-set(CASES):
            raise ValueError('Select one to three known distinct ReplaceFace target cases')
        cases = {name:spec for name,spec in CASES.items() if name in selected}
    source = Path(__file__).resolve()
    output = source.parent/('replacefacetargets-'+uuid.uuid4().hex[:12])
    output.mkdir()
    executed = source.read_bytes()
    (output/'executed-generator-source.txt').write_bytes(executed)
    sdk_path = Path(adsk.fusion.__file__)
    sdk = sdk_path.read_bytes()
    sdk_text = sdk.decode()
    sdk_blocks = []
    for name in ('ReplaceFaceFeatures','ReplaceFaceFeatureInput','ReplaceFaceFeature','PatchFeatures','PatchFeatureInput','PatchFeature','ConstructionPlaneInput'):
        begin = sdk_text.index('class '+name+'(')
        end = sdk_text.find('\nclass ',begin+1)
        sdk_blocks.append(sdk_text[begin:] if end < 0 else sdk_text[begin:end])
    surface = '\n'.join(sdk_blocks).encode()
    (output/'executed-sdk-surface.txt').write_bytes(surface)
    truth = dict(samples=[],errors=[],fusion_version=app.version,planned_cases=list(cases),
        executed_generator_sha256=hashlib.sha256(executed).hexdigest(),
        sdk_runtime_module=str(sdk_path),sdk_runtime_sha256=hashlib.sha256(sdk).hexdigest(),
        executed_sdk_surface_sha256=hashlib.sha256(surface).hexdigest(),helper_dependencies=[],
        scope='Fresh owned parametric documents; separate source solid and oversized rectangular Patch sheet. Exact BRepFace versus BRepBody createInput target argument and tangent flag captured. API source/target/result identities remain separate; no native topology IDs inferred from coordinates.',
        source_setup=dict(block_xy_cm=[[0,0],[4,3]],block_height_cm=2.0,
            patch_xy_cm=[[-1,-1],[5,4]],patch_offset_cm=1.0),
        applicability_scope='ReplaceFaceFeature exposes targetFaces but no sourceFaces property in this SDK. SourceFaces are captured from actual input before add; feature.faces is separately retained without relabeling it as original sources.')

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

    def selection_truth(value):
        if value is None:
            return None
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

    def feature_truth(feature):
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
        if adsk.fusion.ReplaceFaceFeature.cast(feature) is not None:
            row['targetFaces'] = observe('targetFaces',lambda:selection_truth(feature.targetFaces),errors)
            row['isTangentChain'] = observe('isTangentChain',lambda:feature.isTangentChain,errors)
            row['sourceFaces_scope'] = 'No public feature.sourceFaces getter; actual input.sourceFaces captured separately before add'
        row['getter_errors'] = errors
        return row

    def input_truth(inp):
        row,errors = identity(inp),[]
        row['sourceFaces'] = observe('sourceFaces',lambda:selection_truth(inp.sourceFaces),errors)
        row['targetFaces'] = observe('targetFaces',lambda:selection_truth(inp.targetFaces),errors)
        row['isTangentChain'] = observe('isTangentChain',lambda:inp.isTangentChain,errors)
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
            requested=dict(target_argument_type=spec['target'],isTangentChain=spec['tangent'],
                source_face_role='Owned block Extrude end face',target_role='Independent owned Patch sheet',targetBaseFeature_set=False))
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
            sketch = root.sketches.add(root.xYConstructionPlane);sketch.name='OwnedReplaceBlockProfile_'+case
            sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0,0,0),point(4,3,0))
            seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0),value('20 mm'),adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            if seed is None or seed.bodies.count != 1 or seed.endFaces.count != 1:
                raise RuntimeError('Owned source block lacks unique body/end face')
            seed.name = 'OwnedReplaceBlockExtrude_'+case
            solid = seed.bodies.item(0);solid.name='OwnedReplaceBlock_'+case
            source_face = seed.endFaces.item(0)
            sample['phase'] = 'owned_replacement_sheet_setup'
            plane_input = root.constructionPlanes.createInput()
            offset = value('10 mm')
            sample['support_plane_setByOffset_returned'] = bool(plane_input.setByOffset(root.xYConstructionPlane,offset))
            if not sample['support_plane_setByOffset_returned']:
                raise RuntimeError('Owned Patch support plane input rejected offset')
            plane = root.constructionPlanes.add(plane_input)
            if plane is None:
                raise RuntimeError('Owned Patch support plane add returned null')
            plane.name='OwnedReplacePatchPlane_'+case
            patch_sketch = root.sketches.add(plane);patch_sketch.name='OwnedReplacePatchBoundary_'+case
            patch_sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(-1,-1,0),point(5,4,0))
            if patch_sketch.profiles.count != 1:
                raise RuntimeError('Owned rectangular Patch profile not unique')
            profile = patch_sketch.profiles.item(0)
            patch_input = root.features.patchFeatures.createInput(profile,adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            if patch_input is None:
                raise RuntimeError('Owned Patch createInput returned null')
            patch = root.features.patchFeatures.add(patch_input)
            if patch is None or patch.bodies.count != 1:
                raise RuntimeError('Owned Patch add did not return exactly one body')
            patch.name='OwnedReplacementPatch_'+case
            sheet = patch.bodies.item(0);sheet.name='OwnedReplacementSheet_'+case
            if sheet.isSolid or sheet.faces.count != 1:
                raise RuntimeError('Owned rectangular Patch is not one non-solid face')
            target = sheet.faces.item(0) if spec['target']=='BRepFace' else sheet
            design.timeline.moveToEnd()
            sample['source_setup_feature_before_replace'] = feature_truth(seed)
            sample['patch_setup_feature_before_replace'] = feature_truth(patch)
            sample['support_plane_before_replace'] = selection_truth(plane)
            sample['patch_profile_before_replace'] = dict(identity=identity(profile),profile_loop_count=observe('Patch profile.profileLoops.count',lambda:profile.profileLoops.count,sample['getter_errors']))
            sample['selected_source_face_before_replace'] = face_truth(source_face)
            sample['exact_createInput_target_argument_before_replace'] = selection_truth(target)
            sample['source_solid_before_replace'] = body_truth(solid)
            sample['target_sheet_before_replace'] = body_truth(sheet)
            sample['component_bodies_before_replace'] = body_collection(root.bRepBodies)
            source_faces = adsk.core.ObjectCollection.create()
            if not source_faces.add(source_face):
                raise RuntimeError('Owned source ObjectCollection rejected face')
            feature = None
            sample['phase'] = 'replace_attempt'
            try:
                sample['replace_collection_count_before'] = root.features.replaceFaceFeatures.count
                inp = root.features.replaceFaceFeatures.createInput(source_faces,spec['tangent'],target)
                if inp is None:
                    raise RuntimeError('ReplaceFace createInput returned null')
                sample['input_before_add'] = input_truth(inp)
                sample['exact_createInput_arguments'] = dict(source_argument_type=source_faces.objectType,
                    source_count=source_faces.count,target_argument_type=target.objectType,isTangentChain=spec['tangent'])
                journal('replace_add_begin',case)
                feature = root.features.replaceFaceFeatures.add(inp)
                sample['add_returned_feature'] = feature is not None
                if feature is None:
                    raise RuntimeError('ReplaceFace add returned null; unchanged document state will be captured/exported')
                feature.name='OwnedReplaceFaceTarget_'+case
                sample['replace_status']='FeatureReturned'
                journal('replace_feature_returned',case)
            except Exception:
                sample['replace_status']='AttemptError'
                error=dict(case=case,phase='replace_attempt',error=traceback.format_exc(),
                    policy='Preserve actual independent body/target collections and export; no success inferred from name or requested geometry')
                sample['replace_error']=error;truth['errors'].append(error)
                journal('replace_attempt_error',case)
            design.timeline.moveToEnd()
            sample['compute_all_returned'] = bool(design.computeAll())
            sample['feature_at_timeline_end'] = feature_truth(feature)
            sample['component_bodies_after_replace'] = body_collection(root.bRepBodies)
            sample['original_source_body_handle_after_replace'] = observe('original source body after replace',lambda:body_truth(solid),sample['getter_errors'])
            sample['original_target_sheet_handle_after_replace'] = observe('original target sheet after replace',lambda:body_truth(sheet),sample['getter_errors'])
            sample['model_parameters_after'] = [parameter_truth(p) for p in items(root.modelParameters)]
            if feature is not None:
                try:
                    rolled = feature.timelineObject.rollTo(True)
                    sample['roll_before_feature_returned'] = bool(rolled)
                    if rolled:
                        sample['feature_before_node'] = feature_truth(feature)
                        sample['component_bodies_before_node'] = body_collection(root.bRepBodies)
                        sample['original_source_face_before_node'] = observe('original source face rolled',lambda:face_truth(source_face),sample['getter_errors'])
                        sample['original_target_argument_before_node'] = observe('original target rolled',lambda:selection_truth(target),sample['getter_errors'])
                except Exception:
                    sample['getter_errors'].append(dict(getter='owned ReplaceFace roll/snapshot',error=traceback.format_exc()))
                finally:
                    design.timeline.moveToEnd()
            sample['replace_collection_count_after'] = root.features.replaceFaceFeatures.count
            sample['timeline_count'] = design.timeline.count
            sample['timeline_marker_position'] = design.timeline.markerPosition
            sample['phase']='local_export'
            journal('local_export_begin',case,file=sample['file'])
            destination=output/sample['file']
            succeeded=design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(destination)))
            if not succeeded or not destination.is_file() or destination.stat().st_size==0:
                raise RuntimeError('Local owned ReplaceFace export did not complete')
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
    (output/'complete.txt').write_text('terminal; inspect all actual target/source/results and recorded setup/attempt/getter/close errors\n')
