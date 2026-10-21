"""Prepared owned CombineFaceGroups probes; no existing document is edited.

Eight actual groups are first generated on a closed octahedron. Selection uses
actual triangle/group incidence only inside this capture generator, then passes
real FaceGroup handles. Temporary labels/tokens are never native persistent IDs.
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

CASES={'adjacent_pair':(2,False),'adjacent_pair_reversed':(2,True),'connected_triple':(3,False)}


def run(context):
    app=adsk.core.Application.get();source=Path(__file__).resolve()
    cases=CASES
    if isinstance(context,dict) and 'cases' in context:
        selected=context['cases']
        if not isinstance(selected,(list,tuple)) or not selected or len(set(selected))!=len(selected) or set(selected)-set(CASES):
            raise ValueError('Select one to three distinct known MeshCombineFaceGroups cases')
        cases={name:spec for name,spec in CASES.items() if name in selected}
    helper_source=source.with_name('GenerateMeshReduceContrasts.py')
    helper=runpy.run_path(str(helper_source))
    output=source.parent/('meshcombinefacegroups-'+uuid.uuid4().hex[:12]);output.mkdir()
    executed=source.read_bytes();(output/'executed-generator-source.txt').write_bytes(executed)
    dependency=helper_source.read_bytes();(output/'executed-mesh-source-helper.txt').write_bytes(dependency)
    stl,normals=helper['_stl']();stl_path=output/'owned-octahedron.stl';stl_path.write_text(stl,encoding='ascii')
    sdk_path=Path(adsk.fusion.__file__).resolve()
    if sdk_path.suffix=='.pyc' and sdk_path.with_suffix('.py').is_file():sdk_path=sdk_path.with_suffix('.py')
    sdk_bytes=sdk_path.read_bytes()
    sdk_source=sdk_bytes.decode('utf-8')
    excerpts=[]
    for class_name in ('FaceGroup','FaceGroups','MeshCombineFaceGroupsFeatureInput','MeshCombineFaceGroupsFeatures','MeshCombineFaceGroupsFeature'):
        start=sdk_source.index('class '+class_name+'(')
        end=sdk_source.find('\nclass ',start+1)
        excerpts.append(sdk_source[start:end if end>=0 else len(sdk_source)])
    sdk_snapshot='\n\n'.join(excerpts).encode('utf-8')
    (output/'executed-sdk-facegroups-surface.txt').write_bytes(sdk_snapshot)
    truth=dict(fusion_version=app.version,samples=[],errors=[],planned_cases=list(cases),
        executed_generator_sha256=hashlib.sha256(executed).hexdigest(),
        mesh_source_helper_sha256=hashlib.sha256(dependency).hexdigest(),
        helper_scope='Owned octahedron helper loaded by absolute runpy; exact source+helper snapshots retained, no sibling sys.path dependency',
        sdk_runtime_module=str(sdk_path),sdk_runtime_source_sha256=hashlib.sha256(sdk_bytes).hexdigest(),
        sdk_surface_snapshot='executed-sdk-facegroups-surface.txt',sdk_surface_snapshot_sha256=hashlib.sha256(sdk_snapshot).hexdigest(),
        sdk_method_enum_values={name:int(getattr(adsk.fusion.MeshGenerateFaceGroupsMethodTypes,name)) for name in ('FastGenerateFaceGroupsType','AccurateGenerateFaceGroupsType')},
        sdk_scope='Active c139 preview MeshCombineFaceGroupsFeatures.createInput(list[FaceGroup])/add; all inputs same MeshBody. inputFaceGroups getter requires rollback on feature. FaceGroup.tempId valid only while parent mesh is unmodified; actual parentBody equality captured.',
        source_mesh=dict(file=stl_path.name,sha256=hashlib.sha256(stl_path.read_bytes()).hexdigest(),numeric_vertices=helper['VERTICES'],
            triangle_vertex_indices=helper['TRIANGLES'],facet_normals=normals,vertex_count=6,triangle_count=8,
            import_units='CentimeterMeshUnit',analytic_source_volume_cm3=4.0/3.0),
        result_scope='Face-group controls are requests, never assumed partitions. Component mesh arrays/scalars and source-handle snapshots are labeled independently; MeshFeature bodies/faces are documented BRep-null and do not supply mesh ownership.',
        controls_scope='Same owned octahedron generated Fast20deg/min0.02; actual8 groups required before selecting2 adjacent groups, same2 reversed, or3 connected. Group labels/collection order and output partition are observed, never assumed persistent.',
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
        result['face_groups']=observe('faceGroups',lambda:[face_group(group,body) for group in items(body.faceGroups)],errors)
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

    def face_group(group,expected_mesh=None):
        if group is None:return None
        result,errors=identity(group),[]
        for prop in ('tempId','area','isPlanar'):
            result[prop]=observe(prop,lambda prop=prop:getattr(group,prop),errors)
        result['centroid_cm']=observe('centroid',lambda:group.centroid.asArray(),errors)
        result['bounding_box_cm']=observe('boundingBox',lambda:dict(min=group.boundingBox.minPoint.asArray(),max=group.boundingBox.maxPoint.asArray()),errors)
        for prop in ('parentBody','nativeObject','assemblyContext'):
            result[prop]=observe(prop,lambda prop=prop:identity(getattr(group,prop)),errors)
        if expected_mesh is not None:
            result['parentBody_equals_expected_mesh']=observe('parentBody == expected mesh',lambda:group.parentBody==expected_mesh,errors)
        result['group_getter_errors']=errors;return result
    def handle_readback(groups,submitted,expected_mesh):
        errors=[]
        actual=observe('inputFaceGroups',lambda:items(groups()),errors)
        return dict(groups=[face_group(group,expected_mesh) for group in actual] if actual is not None else None,
            ordered_equals_submitted=[[observe('readback handle equality',lambda group=group,wanted=wanted:group==wanted,errors) for wanted in submitted] for group in actual] if actual is not None else None,
            getter_errors=errors)
    def combine_truth(feature,submitted,expected_mesh,rolled=False):
        if feature is None:return None
        result,errors=identity(feature),[]
        for prop in ('healthState','errorOrWarningMessage','isParametric','isSuppressed'):
            result[prop]=observe(prop,lambda prop=prop:int(getattr(feature,prop)) if prop=='healthState' else getattr(feature,prop),errors)
        for prop in ('parentComponent','baseFeature'):
            result[prop]=observe(prop,lambda prop=prop:identity(getattr(feature,prop)),errors)
        result['timeline_index']=observe('timelineObject.index',lambda:feature.timelineObject.index,errors)
        result['mesh']=observe('mesh',lambda:mesh_body(feature.mesh),errors)
        result['mesh_equals_expected_source']=observe('feature.mesh == source',lambda:feature.mesh==expected_mesh,errors)
        if rolled:
            result['inputFaceGroups']=handle_readback(lambda:feature.inputFaceGroups,submitted,expected_mesh)
        else:
            result['inputFaceGroups']=None
            result['inputFaceGroups_status']='Requires immediately-before-feature timeline position; not invoked at timeline end'
        result['feature_getter_errors']=errors;return result
    def select_connected_groups(mesh,quantity,reverse):
        polygon=mesh.mesh
        indices=list(polygon.triangleNodeIndices);labels=list(polygon.triangleFaceGroupTempIds)
        groups=items(mesh.faceGroups)
        group_ids=[group.tempId for group in groups]
        if len(indices)!=24 or len(labels)!=8 or len(groups)!=8 or len(set(labels))!=8 or set(labels)!=set(group_ids):
            raise RuntimeError('Actual Fast20 octahedron did not provide8 distinct matching triangle/group labels')
        by_id={group.tempId:group for group in groups}
        owners={}
        for ordinal,label in enumerate(labels):
            tri=indices[3*ordinal:3*ordinal+3]
            for position in range(3):
                edge=tuple(sorted((tri[position],tri[(position+1)%3])))
                owners.setdefault(edge,[]).append(label)
        if any(len(labels)!=2 for labels in owners.values()):raise RuntimeError('Actual prepared mesh is not closed edge-paired')
        adjacency={label:set() for label in labels}
        for pair in owners.values():
            if pair[0]!=pair[1]:
                adjacency[pair[0]].add(pair[1]);adjacency[pair[1]].add(pair[0])
        seed=min(adjacency);neighbors=sorted(adjacency[seed])
        if len(neighbors)<quantity-1:raise RuntimeError('Actual triangle-group adjacency insufficient')
        chosen=[seed]+neighbors[:quantity-1]
        if reverse:chosen=list(reversed(chosen))
        selected=[by_id[label] for label in chosen]
        if not all(group.parentBody==mesh for group in selected):raise RuntimeError('Selected group parentBody differs from owned source handle')
        proof=dict(actual_triangle_node_indices=indices,actual_triangle_face_group_temp_ids=labels,
            group_collection_temp_ids=group_ids,adjacency_by_temporary_id={str(key):sorted(value) for key,value in adjacency.items()},
            selected_temporary_ids=chosen,selection_scope='Generator-only actual triangle-edge adjacency chooses FaceGroup handles via temporary IDs; no native persistent-ID inference',
            selected_groups=[face_group(group,mesh) for group in selected])
        return selected,proof

    journal('batch_begin',output_directory=str(output))
    for case,(quantity,reverse) in cases.items():
        doc=design=base=None;editing=False
        sample=dict(case=case,file=case+'.f3d',getter_errors=[],setter_errors=[],phase='document_create',
            requested=dict(group_quantity=quantity,reverse_input_order=reverse,
                preparation_method='FastGenerateFaceGroupsType',preparation_angle_degrees=20.,
                preparation_minimum_face_group_size=0.02,targetBaseFeature_set=False))
        truth['active_sample']=sample
        try:
            journal('owned_document_create_begin',case)
            doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            if design is None:raise RuntimeError('Owned document has no Fusion Design')
            design.designType=adsk.fusion.DesignTypes.ParametricDesignType;root=design.rootComponent
            sample['root_component']=identity(root)
            base=root.features.baseFeatures.add();base.name='Owned octahedron import '+case
            started=base.startEdit();sample['base_start_edit_returned']=bool(started)
            if not started:raise RuntimeError('Owned BaseFeature.startEdit returned false')
            editing=True;sample['phase']='owned_mesh_import'
            imported=root.meshBodies.add(str(stl_path),adsk.fusion.MeshUnits.CentimeterMeshUnit,base)
            if imported is None or imported.count!=1:raise RuntimeError('Owned STL did not import exactly one MeshBody')
            mesh=imported.item(0);mesh.name='OwnedCombineFaceGroupsSource_'+case
            sample['source_during_edit']=mesh_body(mesh)
            finished=base.finishEdit();sample['base_finish_edit_returned']=bool(finished)
            if not finished:raise RuntimeError('Owned BaseFeature.finishEdit returned false')
            editing=False;design.timeline.moveToEnd()
            sample['base_after_edit']=base_truth(base)
            sample['component_meshes_after_import']=component_meshes(root)
            feature=prepared=None;selected=[]
            try:
                sample['phase']='prepare_eight_groups'
                inputs=root.features.meshGenerateFaceGroupsFeatures.createInput(mesh)
                if inputs is None:raise RuntimeError('Preparation GenerateFaceGroups createInput returned null')
                inputs.meshGenerateFaceGroupsMethodType=adsk.fusion.MeshGenerateFaceGroupsMethodTypes.FastGenerateFaceGroupsType
                inputs.angleThreshold=adsk.core.ValueInput.createByReal(math.radians(20.))
                inputs.minimumFaceGroupSize=adsk.core.ValueInput.createByReal(0.02)
                sample['preparation_input_controls']=controls(inputs,True)
                journal('prepare_generate_groups_add_begin',case)
                prepared=root.features.meshGenerateFaceGroupsFeatures.add(inputs)
                if prepared is None:raise RuntimeError('Preparation GenerateFaceGroups add returned null')
                prepared.name='OwnedPreparationFaceGroups_'+case
                design.timeline.moveToEnd();design.computeAll()
                sample['preparation_feature']=feature_truth(prepared)
                sample['component_meshes_before_combine_groups']=component_meshes(root)
                sample['phase']='select_actual_connected_groups'
                selected,proof=select_connected_groups(mesh,quantity,reverse)
                sample['selection_proof']=proof
                collection=root.features.meshCombineFaceGroupsFeatures
                sample['combine_collection_count_before']=collection.count
                inputs=collection.createInput(selected)
                if inputs is None:raise RuntimeError('MeshCombineFaceGroups createInput returned null')
                sample['inputFaceGroups_before_add']=handle_readback(lambda:inputs.inputFaceGroups,selected,mesh)
                sample['input_targetBaseFeature']=observe('input.targetBaseFeature',lambda:identity(inputs.targetBaseFeature),sample['getter_errors'])
                sample['phase']='combine_face_groups_add';journal('combine_face_groups_add_begin',case)
                feature=collection.add(inputs);sample['add_returned_feature']=feature is not None
                if feature is None:raise RuntimeError('Parametric MeshCombineFaceGroups add returned null')
                feature.name='OwnedMeshCombineFaceGroups_'+case
                sample['combine_status']='FeatureReturned';journal('combine_face_groups_feature_returned',case)
            except Exception:
                sample['combine_status']='AttemptError'
                failure=dict(case=case,phase=sample['phase'],error=traceback.format_exc())
                sample['combine_error']=failure;truth['errors'].append(failure);journal('combine_face_groups_attempt_error',case)
            design.timeline.moveToEnd();sample['compute_all_returned']=observe('computeAll',lambda:design.computeAll(),sample['getter_errors'])
            sample['component_meshes_after_combine_groups']=component_meshes(root)
            sample['feature_at_timeline_end']=combine_truth(feature,selected,mesh)
            sample['base_after_combine_groups']=base_truth(base)
            sample['model_parameters_after']=observe('modelParameters after',lambda:[parameter(p) for p in root.modelParameters],sample['getter_errors'])
            if feature is not None:
                try:
                    rolled=feature.timelineObject.rollTo(True);sample['roll_before_feature_returned']=bool(rolled)
                    if rolled:
                        sample['feature_before_node']=combine_truth(feature,selected,mesh,True)
                        sample['component_meshes_before_node']=component_meshes(root)
                except Exception:sample['getter_errors'].append(dict(getter='roll before CombineFaceGroups',error=traceback.format_exc()))
                finally:design.timeline.moveToEnd()
            sample['combine_collection_count_after']=observe('combine count',lambda:root.features.meshCombineFaceGroupsFeatures.count,sample['getter_errors'])
            sample['timeline_count']=design.timeline.count;sample['timeline_marker_position']=design.timeline.markerPosition
            sample['phase']='local_export';journal('local_export_begin',case)
            destination=output/sample['file'];succeeded=design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(destination)))
            if not succeeded or not destination.is_file() or not destination.stat().st_size:raise RuntimeError('Owned local archive export failed')
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
    (output/'complete.txt').write_text('MeshCombineFaceGroups terminal: '+truth['terminal_status']+'; inspect actual group handles/IDs/errors.\n')
