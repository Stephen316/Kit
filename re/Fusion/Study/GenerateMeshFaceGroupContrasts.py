"""Three owned octahedron GenerateFaceGroups method/angle contrasts.

Prepared against the active c139 preview API. Run only through Fusion after
root review. Raw triangle face-group temporary IDs are observations, never
persistent native identities or assumed geometric partitions.
"""
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path
import traceback
import runpy
import uuid

import adsk.core
import adsk.fusion

CASES={'fast_twenty_degrees':('FastGenerateFaceGroupsType',20.0),
       'fast_eighty_degrees':('FastGenerateFaceGroupsType',80.0),
       'accurate_boundary_point_zero_zero_one':('AccurateGenerateFaceGroupsType',0.001)}


def run(context):
    app=adsk.core.Application.get();source=Path(__file__).resolve()
    cases=CASES
    if isinstance(context,dict) and 'cases' in context:
        selected=context['cases']
        if not isinstance(selected,(list,tuple)) or not selected or len(set(selected))!=len(selected) or set(selected)-set(CASES):
            raise ValueError('Select one to three distinct known MeshGenerateFaceGroups cases')
        cases={name:spec for name,spec in CASES.items() if name in selected}
    helper_source=source.with_name('GenerateMeshReduceContrasts.py')
    helper=runpy.run_path(str(helper_source))
    output=source.parent/('meshfacegroups-'+uuid.uuid4().hex[:12]);output.mkdir()
    executed=source.read_bytes();(output/'executed-generator-source.txt').write_bytes(executed)
    dependency=helper_source.read_bytes();(output/'executed-mesh-source-helper.txt').write_bytes(dependency)
    stl,normals=helper['_stl']();stl_path=output/'owned-octahedron.stl';stl_path.write_text(stl,encoding='ascii')
    sdk_path=Path(adsk.fusion.__file__).resolve()
    if sdk_path.suffix=='.pyc' and sdk_path.with_suffix('.py').is_file():sdk_path=sdk_path.with_suffix('.py')
    sdk_bytes=sdk_path.read_bytes()
    truth=dict(fusion_version=app.version,samples=[],errors=[],planned_cases=list(cases),
        executed_generator_sha256=hashlib.sha256(executed).hexdigest(),
        mesh_source_helper_sha256=hashlib.sha256(dependency).hexdigest(),
        helper_scope='Owned octahedron helper loaded by absolute runpy; exact source+helper snapshots retained, no sibling sys.path dependency',
        sdk_runtime_module=str(sdk_path),sdk_runtime_source_sha256=hashlib.sha256(sdk_bytes).hexdigest(),
        sdk_method_enum_values={name:int(getattr(adsk.fusion.MeshGenerateFaceGroupsMethodTypes,name)) for name in ('FastGenerateFaceGroupsType','AccurateGenerateFaceGroupsType')},
        sdk_scope='Active executable c139 preview MeshGenerateFaceGroupsFeatures.createInput(mesh)/add. Fast angleThreshold/minimumFaceGroupSize and Accurate boundaryTolerance are ValueInput on input, ModelParameter on feature; documented inactive controls not read.',
        source_mesh=dict(file=stl_path.name,sha256=hashlib.sha256(stl_path.read_bytes()).hexdigest(),numeric_vertices=helper['VERTICES'],
            triangle_vertex_indices=helper['TRIANGLES'],facet_normals=normals,vertex_count=6,triangle_count=8,
            import_units='CentimeterMeshUnit',analytic_source_volume_cm3=4.0/3.0),
        result_scope='Face-group controls are requests, never assumed partitions. Component mesh arrays/scalars and source-handle snapshots are labeled independently; MeshFeature bodies/faces are documented BRep-null and do not supply mesh ownership.',
        controls_scope='Same owned regular octahedron; Fast angle20deg/80deg with minimumFaceGroupSize0.02; Accurate boundaryTolerance0.001 supplied as real internal scalar. Requested values are distinct from actual parameter units/values; group counts and IDs never assumed.',
        identity_scope='Opaque tokens retained as getter evidence only; direct handle equality is recorded separately, never decoded into native IDs.')

    def persist():(output/'ground_truth.json').write_text(json.dumps(truth,indent=2)+'\n')
    def journal(phase,case=None,**fields):
        event=dict(time_utc=datetime.now(timezone.utc).isoformat(),phase=phase,case=case,
            sample_count=len(truth['samples']),error_count=len(truth['errors']),**fields)
        with (output/'journal.jsonl').open('a') as stream:stream.write(json.dumps(event)+'\n')
        (output/'progress.json').write_text(json.dumps(event,indent=2)+'\n');persist()
    def observe(label,getter,errors):
        try:return getter()
        except Exception:
            errors.append(dict(getter=label,error=traceback.format_exc()));return None
    def items(collection):
        if collection is None:return None
        if hasattr(collection,'item') and hasattr(collection,'count'):return [collection.item(i) for i in range(collection.count)]
        return list(collection)
    def identity(entity):
        if entity is None:return None
        result,errors={},[]
        for prop in ('objectType','isValid','name','entityToken'):
            if hasattr(type(entity),prop):result[prop]=observe(prop,lambda prop=prop:getattr(entity,prop),errors)
        result['getter_errors']=errors;return result
    def mesh_array(mesh,display=False):
        if mesh is None:return None
        result,errors={},[]
        props=['objectType','nodeCount','nodeCoordinatesAsDouble','triangleCount','normalVectorsAsDouble']
        props+=['nodeIndices','surfaceTolerance'] if display else ['quadCount','polygonCount','triangleNodeIndices',
            'triangleFaceGroupTempIds','quadNodeIndices','polygonNodeIndices','nodeCountPerPolygon']
        for prop in props:result[prop]=observe(prop,lambda prop=prop:getattr(mesh,prop),errors)
        result['getter_errors']=errors;return result
    def mesh_body(body):
        if body is None:return None
        result,errors=identity(body),[]
        for prop in ('area','volume','isClosed','isOriented','isVisible','isLightBulbOn'):
            result[prop]=observe(prop,lambda prop=prop:getattr(body,prop),errors)
        result['bounding_box_cm']=observe('boundingBox',lambda:dict(min=body.boundingBox.minPoint.asArray(),max=body.boundingBox.maxPoint.asArray()),errors)
        for prop in ('baseOrFormFeature','parentComponent','assemblyContext','nativeObject'):
            result[prop]=observe(prop,lambda prop=prop:identity(getattr(body,prop)),errors)
        result['original_polygon_mesh']=observe('mesh',lambda:mesh_array(body.mesh),errors)
        result['display_triangle_mesh']=observe('displayMesh',lambda:mesh_array(body.displayMesh,True),errors)
        result['mesh_getter_errors']=errors;return result
    def component_meshes(root):
        errors=[];bodies=observe('root.meshBodies',lambda:items(root.meshBodies),errors)
        return dict(count=len(bodies) if bodies is not None else None,meshes=[mesh_body(b) for b in bodies] if bodies is not None else None,getter_errors=errors)
    def parameter(parameter):
        if parameter is None:return None
        result,errors=identity(parameter),[]
        for prop in ('name','role','value','unit','expression'):
            result[prop]=observe(prop,lambda prop=prop:getattr(parameter,prop),errors)
        result['createdBy']=observe('createdBy',lambda:identity(parameter.createdBy),errors)
        result['parameter_getter_errors']=errors;return result
    def value_input(value):
        if value is None:return None
        result,errors=identity(value),[]
        kind=observe('valueType',lambda:value.valueType,errors)
        result['valueType']=int(kind) if kind is not None else None
        if kind==adsk.core.ValueTypes.RealValueType:result['realValue']=observe('realValue',lambda:value.realValue,errors)
        elif kind==adsk.core.ValueTypes.StringValueType:result['stringValue']=observe('stringValue',lambda:value.stringValue,errors)
        result['value_getter_errors']=errors;return result
    def controls(entity,is_input=False):
        result,errors=identity(entity),[]
        method=observe('meshGenerateFaceGroupsMethodType',lambda:int(entity.meshGenerateFaceGroupsMethodType),errors)
        result['meshGenerateFaceGroupsMethodType']=method
        fast=int(adsk.fusion.MeshGenerateFaceGroupsMethodTypes.FastGenerateFaceGroupsType)
        accurate=int(adsk.fusion.MeshGenerateFaceGroupsMethodTypes.AccurateGenerateFaceGroupsType)
        active=('angleThreshold','minimumFaceGroupSize') if method==fast else ('boundaryTolerance',) if method==accurate else ()
        result['active_control_fields']=list(active)
        for prop in ('angleThreshold','minimumFaceGroupSize','boundaryTolerance'):
            if prop not in active:
                result[prop]=None;result[prop+'_status']='Inactive for actual method; getter not invoked'
                continue
            value=observe(prop,lambda prop=prop:getattr(entity,prop),errors)
            result[prop]=value_input(value) if is_input else parameter(value)
        result['control_getter_errors']=errors;return result
    def feature_truth(feature,include_input=False):
        if feature is None:return None
        result,errors=controls(feature),[]
        for prop in ('healthState','errorOrWarningMessage','isParametric','isSuppressed'):
            result[prop]=observe(prop,lambda prop=prop:int(getattr(feature,prop)) if prop=='healthState' else getattr(feature,prop),errors)
        for prop in ('parentComponent','baseFeature'):
            result[prop]=observe(prop,lambda prop=prop:identity(getattr(feature,prop)),errors)
        result['timeline_index']=observe('timelineObject.index',lambda:feature.timelineObject.index,errors)
        result['brep_bodies']=observe('bodies',lambda:None if feature.bodies is None else [identity(b) for b in items(feature.bodies)],errors)
        result['brep_faces']=observe('faces',lambda:None if feature.faces is None else [identity(f) for f in items(feature.faces)],errors)
        if include_input:result['mesh']=observe('mesh at rollTo(True)',lambda:mesh_body(feature.mesh),errors)
        result['feature_getter_errors']=errors;return result
    def base_truth(base):
        result,errors=identity(base),[]
        for prop in ('healthState','errorOrWarningMessage','isParametric'):
            result[prop]=observe(prop,lambda prop=prop:int(getattr(base,prop)) if prop=='healthState' else getattr(base,prop),errors)
        result['mesh_bodies']=observe('meshBodies',lambda:[mesh_body(b) for b in items(base.meshBodies)],errors)
        result['brep_source_bodies']=observe('sourceBodies',lambda:[identity(b) for b in items(base.sourceBodies)],errors)
        result['timeline_index']=observe('timelineObject.index',lambda:base.timelineObject.index,errors)
        result['brep_bodies']=observe('bodies',lambda:[identity(b) for b in items(base.bodies)],errors)
        result['base_getter_errors']=errors;return result

    journal('batch_begin',output_directory=str(output))
    for case,(method_name,control_value) in cases.items():
        doc=design=base=None;editing=False
        sample=dict(case=case,file=case+'.f3d',getter_errors=[],setter_errors=[],phase='document_create',
            requested=dict(method=method_name,
                angle_threshold_degrees=control_value if method_name=='FastGenerateFaceGroupsType' else None,
                minimum_face_group_size=0.02 if method_name=='FastGenerateFaceGroupsType' else None,
                boundary_tolerance_real=control_value if method_name=='AccurateGenerateFaceGroupsType' else None,
                targetBaseFeature_set=False))
        truth['active_sample']=sample
        try:
            journal('owned_document_create_begin',case)
            doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            if design is None:raise RuntimeError('Owned document has no Fusion Design')
            design.designType=adsk.fusion.DesignTypes.ParametricDesignType;root=design.rootComponent
            sample['root_component']=identity(root);sample['component_meshes_before_import']=component_meshes(root)
            base=root.features.baseFeatures.add();base.name='Owned octahedron import '+case
            started=base.startEdit();sample['base_start_edit_returned']=bool(started)
            if not started:raise RuntimeError('Owned BaseFeature.startEdit returned false')
            editing=True;sample['phase']='owned_mesh_import'
            imported=root.meshBodies.add(str(stl_path),adsk.fusion.MeshUnits.CentimeterMeshUnit,base)
            if imported is None or imported.count!=1:raise RuntimeError('Owned STL did not import exactly one MeshBody')
            mesh=imported.item(0);mesh.name='OwnedFaceGroupsSource_'+case
            sample['source_during_edit']=mesh_body(mesh)
            finished=base.finishEdit();sample['base_finish_edit_returned']=bool(finished)
            if not finished:raise RuntimeError('Owned BaseFeature.finishEdit returned false')
            editing=False;design.timeline.moveToEnd()
            sample['base_after_edit']=base_truth(base)
            sample['source_before_face_groups']=mesh_body(mesh);sample['component_meshes_before_face_groups']=component_meshes(root)
            sample['model_parameters_before']=observe('modelParameters before',lambda:[parameter(p) for p in root.modelParameters],sample['getter_errors'])
            feature=None;sample['phase']='mesh_face_groups_attempt'
            try:
                collection=root.features.meshGenerateFaceGroupsFeatures
                sample['face_groups_collection_count_before']=collection.count
                inputs=collection.createInput(mesh)
                if inputs is None:raise RuntimeError('MeshGenerateFaceGroups createInput returned null')
                sample['input_defaults']=controls(inputs,True)
                sample['input_defaults_targetBaseFeature']=observe('input.targetBaseFeature defaults',lambda:identity(inputs.targetBaseFeature),sample['getter_errors'])
                method=getattr(adsk.fusion.MeshGenerateFaceGroupsMethodTypes,method_name)
                sample['requested']['method_enum']=int(method)
                try:inputs.meshGenerateFaceGroupsMethodType=method
                except Exception:
                    sample['setter_errors'].append(dict(property='meshGenerateFaceGroupsMethodType',error=traceback.format_exc()));raise
                requested_values=(('angleThreshold',math.radians(control_value)),('minimumFaceGroupSize',0.02)) if method_name=='FastGenerateFaceGroupsType' else (('boundaryTolerance',control_value),)
                sample['requested_value_inputs']={}
                for prop,real_value in requested_values:
                    value=adsk.core.ValueInput.createByReal(real_value)
                    sample['requested_value_inputs'][prop]=value_input(value)
                    try:setattr(inputs,prop,value)
                    except Exception:
                        sample['setter_errors'].append(dict(property=prop,error=traceback.format_exc()));raise
                sample['input_before_add']=controls(inputs,True)
                sample['input_mesh_equals_import_handle']=observe('input.mesh == source',lambda:inputs.mesh==mesh,sample['getter_errors'])
                sample['input_mesh']=observe('input.mesh',lambda:mesh_body(inputs.mesh),sample['getter_errors'])
                sample['input_targetBaseFeature']=observe('input.targetBaseFeature',lambda:identity(inputs.targetBaseFeature),sample['getter_errors'])
                journal('mesh_face_groups_add_begin',case)
                feature=collection.add(inputs);sample['add_returned_feature']=feature is not None
                if feature is None:raise RuntimeError('Parametric MeshGenerateFaceGroups add returned null; actual current meshes still exported')
                feature.name='OwnedMeshGenerateFaceGroups_'+case;sample['face_groups_status']='FeatureReturned'
                journal('mesh_face_groups_feature_returned',case)
            except Exception:
                sample['face_groups_status']='AttemptError'
                failure=dict(case=case,phase='mesh_face_groups_attempt',error=traceback.format_exc(),policy='Preserve/export actual source/current mesh; result group counts and failed feature support never assumed')
                sample['face_groups_error']=failure;truth['errors'].append(failure);journal('mesh_face_groups_attempt_error',case)
            design.timeline.moveToEnd();sample['compute_all_returned']=observe('design.computeAll',lambda:design.computeAll(),sample['getter_errors'])
            sample['component_meshes_after_face_groups']=component_meshes(root)
            sample['original_source_handle_after_face_groups']=observe('original source handle',lambda:mesh_body(mesh),sample['getter_errors'])
            sample['feature_at_timeline_end']=feature_truth(feature)
            sample['base_after_face_groups']=base_truth(base)
            sample['model_parameters_after']=observe('modelParameters after',lambda:[parameter(p) for p in root.modelParameters],sample['getter_errors'])
            if feature is not None:
                try:
                    rolled=feature.timelineObject.rollTo(True);sample['roll_before_feature_returned']=bool(rolled)
                    if rolled:
                        sample['feature_before_node']=feature_truth(feature,True)
                        sample['component_meshes_before_node']=component_meshes(root)
                        sample['feature_input_mesh_equals_import_handle']=observe('feature.mesh == source at rollback',lambda:feature.mesh==mesh,sample['getter_errors'])
                except Exception:sample['getter_errors'].append(dict(getter='roll/actual MeshGenerateFaceGroups before-node snapshot',error=traceback.format_exc()))
                finally:design.timeline.moveToEnd()
            sample['face_groups_collection_count_after']=observe('face_groupsFeatures count after',lambda:root.features.meshGenerateFaceGroupsFeatures.count,sample['getter_errors'])
            sample['timeline_count']=design.timeline.count;sample['timeline_marker_position']=design.timeline.markerPosition
            sample['phase']='local_export';journal('local_export_begin',case)
            destination=output/sample['file'];succeeded=design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(destination)))
            if not succeeded or not destination.is_file() or not destination.stat().st_size:raise RuntimeError('Local owned MeshGenerateFaceGroups archive export failed')
            sample['export']=dict(returned_success=bool(succeeded),size_bytes=destination.stat().st_size,sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
            sample['phase']='export_complete';truth['samples'].append(sample);journal('local_export_complete',case)
        except Exception:
            truth['errors'].append(dict(case=case,phase=sample['phase'],error=traceback.format_exc(),partial_sample=sample));journal('case_error',case)
        finally:
            if editing and base is not None:
                try:
                    returned=base.finishEdit();sample['cleanup_base_finish_edit_returned']=bool(returned)
                    if not returned:truth['errors'].append(dict(case=case,phase='cleanup_base_edit',error='finishEdit returned false'))
                except Exception:truth['errors'].append(dict(case=case,phase='cleanup_base_edit',error=traceback.format_exc()))
            if design is not None:
                try:design.timeline.moveToEnd()
                except Exception:truth['errors'].append(dict(case=case,phase='restore_owned_timeline',error=traceback.format_exc()))
            if doc is not None:
                try:
                    journal('owned_document_close_begin',case,save=False)
                    closed=doc.close(False);sample['close_owned_document_returned']=bool(closed)
                    journal('owned_document_close_returned',case,returned=bool(closed),save=False)
                    if not closed:truth['errors'].append(dict(case=case,phase='close_owned_document',error='close(False) returned false'))
                except Exception:truth['errors'].append(dict(case=case,phase='close_owned_document',error=traceback.format_exc()))
            truth.pop('active_sample',None);persist()
    truth['terminal_status']='complete' if len(truth['samples'])==len(cases) and not truth['errors'] else 'complete_with_errors'
    truth['exported_sample_count']=len(truth['samples']);journal('batch_terminal')
    (output/'complete.txt').write_text('MeshGenerateFaceGroups terminal: '+truth['terminal_status']+'; inspect actual errors/arrays/parameter units.\n')
