"""Three owned octahedron MeshReduce contrasts using active executable bindings.

No sibling imports or UI commands. All geometry helpers are in this snapshotted
source. Preview APIs are called only inside run(), in newly owned documents.
"""
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

VERTICES=((1.,0.,0.),(0.,1.,0.),(-1.,0.,0.),(0.,-1.,0.),(0.,0.,1.),(0.,0.,-1.))
TRIANGLES=((0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5))
CASES={'adaptive_count_six':('AdaptiveReduceType','FaceCountMeshReduceTargetType'),
       'uniform_count_six':('UniformReduceType','FaceCountMeshReduceTargetType'),
       'adaptive_proportion_fifty':('AdaptiveReduceType','ProportionMeshReduceTargetType')}


def _stl():
    lines=['solid owned_octahedron'];normals=[]
    for indices in TRIANGLES:
        a,b,c=[VERTICES[i] for i in indices]
        u,v=[b[i]-a[i] for i in range(3)],[c[i]-a[i] for i in range(3)]
        cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
        length=math.sqrt(sum(x*x for x in cross));normal=[x/length for x in cross];normals.append(normal)
        if sum(normal[i]*(a[i]+b[i]+c[i])/3. for i in range(3))<=0:raise ValueError('Owned octahedron facet not outward')
        lines+=['  facet normal '+' '.join(format(x,'.17g') for x in normal),'    outer loop']
        lines+=['      vertex '+' '.join(format(x,'.17g') for x in vertex) for vertex in (a,b,c)]
        lines+=['    endloop','  endfacet']
    return '\n'.join(lines+['endsolid owned_octahedron','']),normals


def run(context):
    app=adsk.core.Application.get();source=Path(__file__).resolve()
    cases=CASES
    if isinstance(context,dict) and 'cases' in context:
        selected=context['cases']
        if not isinstance(selected,(list,tuple)) or not selected or len(set(selected))!=len(selected) or set(selected)-set(CASES):
            raise ValueError('Select one to three distinct known MeshReduce cases')
        cases={name:spec for name,spec in CASES.items() if name in selected}
    real_proportion=None
    if isinstance(context,dict) and 'real_proportion' in context:
        candidate=context['real_proportion']
        if (isinstance(candidate,bool) or not isinstance(candidate,(int,float)) or not math.isfinite(candidate)
                or float(candidate)!=50.0 or list(cases)!=['adaptive_proportion_fifty']):
            raise ValueError('real_proportion opt-in requires exactly50.0 and only adaptive_proportion_fifty')
        real_proportion=float(candidate)
    output=source.parent/('meshreduces-'+uuid.uuid4().hex[:12]);output.mkdir()
    executed=source.read_bytes();(output/'executed-generator-source.txt').write_bytes(executed)
    stl,normals=_stl();stl_path=output/'owned-octahedron.stl';stl_path.write_text(stl,encoding='ascii')
    sdk_path=Path(adsk.fusion.__file__).resolve()
    if sdk_path.suffix=='.pyc' and sdk_path.with_suffix('.py').is_file():sdk_path=sdk_path.with_suffix('.py')
    sdk_bytes=sdk_path.read_bytes()
    truth=dict(fusion_version=app.version,samples=[],errors=[],planned_cases=list(cases),
        executed_generator_sha256=hashlib.sha256(executed).hexdigest(),
        helper_scope='Self-contained _stl/mesh/value helpers; executed-generator-source.txt is their exact source snapshot, no external helper or sibling import',
        sdk_runtime_module=str(sdk_path),sdk_runtime_source_sha256=hashlib.sha256(sdk_bytes).hexdigest(),
        sdk_method_enum_values={name:int(getattr(adsk.fusion.MeshReduceMethodTypes,name)) for name in ('AdaptiveReduceType','UniformReduceType')},
        sdk_target_enum_values={name:int(getattr(adsk.fusion.MeshReduceTargetTypes,name)) for name in ('FaceCountMeshReduceTargetType','ProportionMeshReduceTargetType','MaximumDeviationMeshReduceTargetType')},
        sdk_scope='Active executable c139 adsk.fusion preview MeshReduceFeatureInput/MeshReduceFeature APIs; documented createInput(mesh)/add, method/target properties and active facecount/proportion ValueInput/ModelParameter only',
        source_mesh=dict(file=stl_path.name,sha256=hashlib.sha256(stl_path.read_bytes()).hexdigest(),numeric_vertices=VERTICES,
            triangle_vertex_indices=TRIANGLES,facet_normals=normals,vertex_count=6,triangle_count=8,
            import_units='CentimeterMeshUnit',analytic_source_volume_cm3=4./3.),
        result_scope='Targets are requests, never assumed results. Component mesh arrays/scalars and source-handle snapshots are labeled independently; MeshFeature bodies/faces are documented BRep-null and do not supply mesh ownership.',
        proportion_scope=('Bounded holdout uses createByReal(50.0); default string50 % failure remains in its original archived snapshot. Record actual values/units without assuming percentage normalization.' if real_proportion is not None else 'Explicit string50 % is supplied; record actual ValueInput type/string/real where valid and ModelParameter value/unit/expression without assuming50 versus0.5 conversion.'),
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
        for prop in ('meshReduceMethodType','meshReduceTargetType'):
            result[prop]=observe(prop,lambda prop=prop:int(getattr(entity,prop)),errors)
        target=result['meshReduceTargetType']
        field=('facecount' if target==int(adsk.fusion.MeshReduceTargetTypes.FaceCountMeshReduceTargetType) else
            'proportion' if target==int(adsk.fusion.MeshReduceTargetTypes.ProportionMeshReduceTargetType) else
            'maximumDeviation' if target==int(adsk.fusion.MeshReduceTargetTypes.MaximumDeviationMeshReduceTargetType) else None)
        result['active_target_field']=field
        if field is not None:
            active=observe(field,lambda:getattr(entity,field),errors)
            result['active_target_value_input' if is_input else 'active_target_parameter']=(value_input(active) if is_input else parameter(active))
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
        result['timeline_index']=observe('timelineObject.index',lambda:feature.timelineObject.index,errors)
        result['brep_bodies']=observe('bodies',lambda:[identity(b) for b in items(base.bodies)],errors)
        result['base_getter_errors']=errors;return result

    journal('batch_begin',output_directory=str(output))
    for case,(method_name,target_name) in cases.items():
        doc=design=base=None;editing=False
        sample=dict(case=case,file=case+'.f3d',getter_errors=[],setter_errors=[],phase='document_create',
            requested=dict(method=method_name,target=target_name,facecount=6 if target_name=='FaceCountMeshReduceTargetType' else None,
                proportion_expression='50 %' if target_name=='ProportionMeshReduceTargetType' and real_proportion is None else None,
                proportion_real_value=real_proportion if target_name=='ProportionMeshReduceTargetType' else None,targetBaseFeature_set=False))
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
            mesh=imported.item(0);mesh.name='OwnedOctahedronSource_'+case
            sample['source_during_edit']=mesh_body(mesh)
            finished=base.finishEdit();sample['base_finish_edit_returned']=bool(finished)
            if not finished:raise RuntimeError('Owned BaseFeature.finishEdit returned false')
            editing=False;design.timeline.moveToEnd()
            sample['base_after_edit']=base_truth(base)
            sample['source_before_reduce']=mesh_body(mesh);sample['component_meshes_before_reduce']=component_meshes(root)
            sample['model_parameters_before']=observe('modelParameters before',lambda:[parameter(p) for p in root.modelParameters],sample['getter_errors'])
            feature=None;sample['phase']='mesh_reduce_attempt'
            try:
                collection=root.features.meshReduceFeatures
                sample['reduce_collection_count_before']=collection.count
                inputs=collection.createInput(mesh)
                if inputs is None:raise RuntimeError('MeshReduce createInput returned null')
                sample['input_defaults']=controls(inputs,True)
                sample['input_defaults_targetBaseFeature']=identity(inputs.targetBaseFeature)
                method=getattr(adsk.fusion.MeshReduceMethodTypes,method_name);target=getattr(adsk.fusion.MeshReduceTargetTypes,target_name)
                sample['requested']['method_enum']=int(method);sample['requested']['target_enum']=int(target)
                for prop,requested_value in (('meshReduceMethodType',method),('meshReduceTargetType',target)):
                    try:setattr(inputs,prop,requested_value)
                    except Exception:
                        sample['setter_errors'].append(dict(property=prop,error=traceback.format_exc()));raise
                target_field='facecount' if target_name=='FaceCountMeshReduceTargetType' else 'proportion'
                requested_value=(adsk.core.ValueInput.createByReal(6.0) if target_field=='facecount' else
                    adsk.core.ValueInput.createByReal(real_proportion) if real_proportion is not None else
                    adsk.core.ValueInput.createByString('50 %'))
                sample['requested_value_input']=value_input(requested_value)
                try:setattr(inputs,target_field,requested_value)
                except Exception:
                    sample['setter_errors'].append(dict(property=target_field,error=traceback.format_exc()));raise
                sample['input_before_add']=controls(inputs,True)
                sample['input_mesh_equals_import_handle']=observe('input.mesh == source',lambda:inputs.mesh==mesh,sample['getter_errors'])
                sample['input_mesh']=observe('input.mesh',lambda:mesh_body(inputs.mesh),sample['getter_errors'])
                sample['input_targetBaseFeature']=observe('input.targetBaseFeature',lambda:identity(inputs.targetBaseFeature),sample['getter_errors'])
                journal('mesh_reduce_add_begin',case)
                feature=collection.add(inputs);sample['add_returned_feature']=feature is not None
                if feature is None:raise RuntimeError('Parametric MeshReduce add returned null; actual current meshes still exported')
                feature.name='OwnedMeshReduce_'+case;sample['reduce_status']='FeatureReturned'
                journal('mesh_reduce_feature_returned',case)
            except Exception:
                sample['reduce_status']='AttemptError'
                failure=dict(case=case,phase='mesh_reduce_attempt',error=traceback.format_exc(),policy='Preserve/export actual source/current mesh; target/result counts and failed feature support never assumed')
                sample['reduce_error']=failure;truth['errors'].append(failure);journal('mesh_reduce_attempt_error',case)
            design.timeline.moveToEnd();sample['compute_all_returned']=observe('design.computeAll',lambda:design.computeAll(),sample['getter_errors'])
            sample['component_meshes_after_reduce']=component_meshes(root)
            sample['original_source_handle_after_reduce']=observe('original source handle',lambda:mesh_body(mesh),sample['getter_errors'])
            sample['feature_at_timeline_end']=feature_truth(feature)
            sample['base_after_reduce']=base_truth(base)
            sample['model_parameters_after']=observe('modelParameters after',lambda:[parameter(p) for p in root.modelParameters],sample['getter_errors'])
            if feature is not None:
                try:
                    rolled=feature.timelineObject.rollTo(True);sample['roll_before_feature_returned']=bool(rolled)
                    if rolled:
                        sample['feature_before_node']=feature_truth(feature,True)
                        sample['component_meshes_before_node']=component_meshes(root)
                        sample['feature_input_mesh_equals_import_handle']=observe('feature.mesh == source at rollback',lambda:feature.mesh==mesh,sample['getter_errors'])
                except Exception:sample['getter_errors'].append(dict(getter='roll/actual MeshReduce before-node snapshot',error=traceback.format_exc()))
                finally:design.timeline.moveToEnd()
            sample['reduce_collection_count_after']=observe('reduceFeatures count after',lambda:root.features.meshReduceFeatures.count,sample['getter_errors'])
            sample['timeline_count']=design.timeline.count;sample['timeline_marker_position']=design.timeline.markerPosition
            sample['phase']='local_export';journal('local_export_begin',case)
            destination=output/sample['file'];succeeded=design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(destination)))
            if not succeeded or not destination.is_file() or not destination.stat().st_size:raise RuntimeError('Local owned MeshReduce archive export failed')
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
    (output/'complete.txt').write_text('MeshReduce terminal: '+truth['terminal_status']+'; inspect actual errors/arrays/parameter units.\n')
