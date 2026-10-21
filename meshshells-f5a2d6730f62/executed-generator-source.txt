"""Owned open/closed-tetrahedron MeshShell thickness contrasts, using active SDK.

Run only through Fusion after root review. The exact owned tetrahedron helper is
loaded by absolute runpy and snapshotted; no sibling sys.path assumptions.
Requested thickness values do not imply algorithm or result geometry support.
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

CASES={'open_thickness_point_one':(False,0.1),
       'open_thickness_point_two':(False,0.2),
       'closed_thickness_point_one':(True,0.1)}


def _owned_stl(vertices,triangles):
    lines,normals=['solid owned_shell_tetra'],[]
    for indices in triangles:
        a,b,c=[vertices[i] for i in indices]
        u,v=[b[i]-a[i] for i in range(3)],[c[i]-a[i] for i in range(3)]
        cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
        length=math.sqrt(sum(x*x for x in cross))
        if not length:raise ValueError('Owned tetra facet is degenerate')
        normal=[x/length for x in cross];normals.append(normal)
        lines+=['  facet normal '+' '.join(format(x,'.17g') for x in normal),'    outer loop']
        lines+=['      vertex '+' '.join(format(x,'.17g') for x in point) for point in (a,b,c)]
        lines+=['    endloop','  endfacet']
    return '\n'.join(lines+['endsolid owned_shell_tetra','']),normals


def run(context):
    app=adsk.core.Application.get();source=Path(__file__).resolve()
    cases=CASES
    if isinstance(context,dict) and 'cases' in context:
        selected=context['cases']
        if not isinstance(selected,(list,tuple)) or not selected or len(set(selected))!=len(selected) or set(selected)-set(CASES):
            raise ValueError('Select one to three distinct known MeshShell cases')
        cases={name:spec for name,spec in CASES.items() if name in selected}
    helper_source=source.with_name('GenerateMeshContrasts.py')
    helper=runpy.run_path(str(helper_source))
    output=source.parent/('meshshells-'+uuid.uuid4().hex[:12]);output.mkdir()
    executed=source.read_bytes();(output/'executed-generator-source.txt').write_bytes(executed)
    dependency=helper_source.read_bytes();(output/'executed-mesh-source-helper.txt').write_bytes(dependency)
    source_meshes={}
    for closed in (False,True):
        triangles=helper['TRIANGLES'] if closed else helper['TRIANGLES'][:3]
        stl,normals=_owned_stl(helper['VERTICES'],triangles)
        stl_path=output/('owned-closed-tetra.stl' if closed else 'owned-open-tetra.stl')
        stl_path.write_text(stl,encoding='ascii')
        source_meshes['closed' if closed else 'open']=dict(file=stl_path.name,
            sha256=hashlib.sha256(stl_path.read_bytes()).hexdigest(),numeric_vertices=helper['VERTICES'],
            triangle_vertex_indices=triangles,facet_normals=normals,vertex_count=4,
            triangle_count=len(triangles),import_units='CentimeterMeshUnit',
            requested_closed_source=closed,analytic_enclosed_volume_cm3=4.0 if closed else None,
            geometry_scope='Owned numeric tetra facets; three coordinate-plane facets retain an open triangular boundary. Actual imported getters authoritative.')
    sdk_path=Path(adsk.fusion.__file__).resolve()
    if sdk_path.suffix=='.pyc' and sdk_path.with_suffix('.py').is_file():sdk_path=sdk_path.with_suffix('.py')
    sdk_bytes=sdk_path.read_bytes()
    truth=dict(fusion_version=app.version,samples=[],errors=[],planned_cases=list(cases),
        executed_generator_sha256=hashlib.sha256(executed).hexdigest(),
        mesh_source_helper_sha256=hashlib.sha256(dependency).hexdigest(),
        helper_scope='Owned tetra VERTICES/TRIANGLES loaded by absolute runpy; this generator frames either all4facets or first3facets asSTL. Exact source+helper snapshots retained, no sibling sys.path dependency',
        sdk_runtime_module=str(sdk_path),sdk_runtime_source_sha256=hashlib.sha256(sdk_bytes).hexdigest(),
        sdk_scope='Active executable c139 adsk.fusion preview MeshShellFeatureInput/MeshShellFeature APIs: createInput(mesh)/add, thickness ValueInput on input, thickness ModelParameter on feature; feature.mesh captured only after rollTo(True)',
        source_meshes=source_meshes,
        result_scope='Thickness is a request, never an assumed result. Component mesh arrays/scalars and source-handle snapshots are labeled independently; MeshFeature bodies/faces are documented BRep-null and do not supply mesh ownership.',
        controls_scope='Open three-triangle tetra thickness0.1/0.2cm and closed four-triangle tetra0.1cm; one bounded add percase after owned BaseFeature import finished. SDK documents default0.2 but no numerical bounds; actual input/result/parameter getters authoritative.',
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
        actual=observe('thickness',lambda:entity.thickness,errors)
        result['thickness']=value_input(actual) if is_input else parameter(actual)
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
    for case,(closed,thickness) in cases.items():
        source_mesh=source_meshes['closed' if closed else 'open'];stl_path=output/source_mesh['file']
        doc=design=base=None;editing=False
        sample=dict(case=case,file=case+'.f3d',getter_errors=[],setter_errors=[],phase='document_create',
            requested=dict(thickness_cm=thickness,closed_source=closed,source_mesh=source_mesh,value_representation='ValueInput.createByReal',targetBaseFeature_set=False))
        truth['active_sample']=sample
        try:
            journal('owned_document_create_begin',case)
            doc=app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design=adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            if design is None:raise RuntimeError('Owned document has no Fusion Design')
            design.designType=adsk.fusion.DesignTypes.ParametricDesignType;root=design.rootComponent
            sample['root_component']=identity(root);sample['component_meshes_before_import']=component_meshes(root)
            base=root.features.baseFeatures.add();base.name='Owned tetra import '+case
            started=base.startEdit();sample['base_start_edit_returned']=bool(started)
            if not started:raise RuntimeError('Owned BaseFeature.startEdit returned false')
            editing=True;sample['phase']='owned_mesh_import'
            imported=root.meshBodies.add(str(stl_path),adsk.fusion.MeshUnits.CentimeterMeshUnit,base)
            if imported is None or imported.count!=1:raise RuntimeError('Owned STL did not import exactly one MeshBody')
            mesh=imported.item(0);mesh.name='OwnedTetraSource_'+case
            sample['source_during_edit']=mesh_body(mesh)
            finished=base.finishEdit();sample['base_finish_edit_returned']=bool(finished)
            if not finished:raise RuntimeError('Owned BaseFeature.finishEdit returned false')
            editing=False;design.timeline.moveToEnd()
            sample['base_after_edit']=base_truth(base)
            sample['source_before_shell']=mesh_body(mesh);sample['component_meshes_before_shell']=component_meshes(root)
            sample['model_parameters_before']=observe('modelParameters before',lambda:[parameter(p) for p in root.modelParameters],sample['getter_errors'])
            feature=None;sample['phase']='mesh_shell_attempt'
            try:
                collection=root.features.meshShellFeatures
                sample['shell_collection_count_before']=collection.count
                inputs=collection.createInput(mesh)
                if inputs is None:raise RuntimeError('MeshShell createInput returned null')
                sample['input_defaults']=controls(inputs,True)
                sample['input_defaults_targetBaseFeature']=observe('input defaults targetBaseFeature',lambda:identity(inputs.targetBaseFeature),sample['getter_errors'])
                requested_value=adsk.core.ValueInput.createByReal(thickness)
                sample['requested_value_input']=value_input(requested_value)
                try:inputs.thickness=requested_value
                except Exception:
                    sample['setter_errors'].append(dict(property='thickness',error=traceback.format_exc()));raise
                sample['input_before_add']=controls(inputs,True)
                sample['input_mesh_equals_import_handle']=observe('input.mesh == source',lambda:inputs.mesh==mesh,sample['getter_errors'])
                sample['input_mesh']=observe('input.mesh',lambda:mesh_body(inputs.mesh),sample['getter_errors'])
                sample['input_targetBaseFeature']=observe('input.targetBaseFeature',lambda:identity(inputs.targetBaseFeature),sample['getter_errors'])
                journal('mesh_shell_add_begin',case)
                feature=collection.add(inputs);sample['add_returned_feature']=feature is not None
                if feature is None:raise RuntimeError('Parametric MeshShell add returned null; actual current meshes still exported')
                feature.name='OwnedMeshShell_'+case;sample['shell_status']='FeatureReturned'
                journal('mesh_shell_feature_returned',case)
            except Exception:
                sample['shell_status']='AttemptError'
                failure=dict(case=case,phase='mesh_shell_attempt',error=traceback.format_exc(),policy='Preserve/export actual source/current mesh; thickness/result changes and failed feature support never assumed')
                sample['shell_error']=failure;truth['errors'].append(failure);journal('mesh_shell_attempt_error',case)
            design.timeline.moveToEnd();sample['compute_all_returned']=observe('design.computeAll',lambda:design.computeAll(),sample['getter_errors'])
            sample['component_meshes_after_shell']=component_meshes(root)
            sample['original_source_handle_after_shell']=observe('original source handle',lambda:mesh_body(mesh),sample['getter_errors'])
            sample['feature_at_timeline_end']=feature_truth(feature)
            sample['base_after_shell']=base_truth(base)
            sample['model_parameters_after']=observe('modelParameters after',lambda:[parameter(p) for p in root.modelParameters],sample['getter_errors'])
            if feature is not None:
                try:
                    rolled=feature.timelineObject.rollTo(True);sample['roll_before_feature_returned']=bool(rolled)
                    if rolled:
                        sample['feature_before_node']=feature_truth(feature,True)
                        sample['component_meshes_before_node']=component_meshes(root)
                        sample['feature_input_mesh_equals_import_handle']=observe('feature.mesh == source at rollback',lambda:feature.mesh==mesh,sample['getter_errors'])
                except Exception:sample['getter_errors'].append(dict(getter='roll/actual MeshShell before-node snapshot',error=traceback.format_exc()))
                finally:design.timeline.moveToEnd()
            sample['shell_collection_count_after']=observe('shellFeatures count after',lambda:root.features.meshShellFeatures.count,sample['getter_errors'])
            sample['timeline_count']=design.timeline.count;sample['timeline_marker_position']=design.timeline.markerPosition
            sample['phase']='local_export';journal('local_export_begin',case)
            destination=output/sample['file'];succeeded=design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(destination)))
            if not succeeded or not destination.is_file() or not destination.stat().st_size:raise RuntimeError('Local owned MeshShell archive export failed')
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
    (output/'complete.txt').write_text('MeshShell terminal: '+truth['terminal_status']+'; inspect actual errors/arrays/parameter units.\n')
