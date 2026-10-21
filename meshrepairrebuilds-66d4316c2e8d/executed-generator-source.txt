"""Prepared owned MeshRepair Rebuild contrasts; no live dispatch.

Three newly owned closed tetrahedra contrast Fast/Accurate at density8 and Accurate offset0/0.05cm.
Actual outcomes are captured without presuming repair success or topology.
"""
from datetime import datetime, timezone
import hashlib
import json
import runpy
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

HELPER = Path('/Users/stephenh/.codex/visualizations/2026/10/17/01a14ba1-a51c-7f72-b92e-9f1f0114012e/FusionFileStudy/GenerateMeshSeparateContrasts.py')
CASES = {'fast_density_eight': ('FastMeshRepairRebuildType', 8.0, None),
    'accurate_density_eight_offset_zero': ('AccurateMeshRepairRebuildType', 8.0, 0.0),
    'accurate_density_eight_offset_point_zero_five': ('AccurateMeshRepairRebuildType', 8.0, 0.05)}


def run(context):
    app = adsk.core.Application.get()
    cases = CASES
    if isinstance(context, dict) and 'cases' in context:
        requested = context['cases']
        if (not isinstance(requested, (list, tuple)) or not requested
                or len(set(requested)) != len(requested) or set(requested)-set(CASES)):
            raise ValueError('Select one to three distinct known MeshRepair cases')
        cases = {name: value for name, value in CASES.items() if name in requested}
    source = Path(__file__).resolve()
    output = source.parent/('meshrepairrebuilds-'+uuid.uuid4().hex[:12])
    output.mkdir()
    executed = source.read_bytes()
    source_sha = hashlib.sha256(executed).hexdigest()
    (output/'executed-generator-source.txt').write_bytes(executed)
    sdk_path = Path(adsk.fusion.__file__).resolve()
    if sdk_path.suffix == '.pyc' and sdk_path.with_suffix('.py').is_file():
        sdk_path = sdk_path.with_suffix('.py')
    sdk_bytes = sdk_path.read_bytes()
    sdk_text = sdk_bytes.decode('utf-8')
    sdk_snippets = []
    for name in ('MeshRepairTypes', 'MeshRepairRebuildTypes', 'MeshRepairFeatureInput', 'MeshRepairFeatures', 'MeshRepairFeature'):
        start = sdk_text.index('class '+name+'(')
        end = sdk_text.find('\nclass ', start+1)
        sdk_snippets.append(sdk_text[start:end if end >= 0 else None])
    sdk_snapshot = '\n\n'.join(sdk_snippets)
    (output/'executed-sdk-mesh-repair-surface.txt').write_text(sdk_snapshot)
    helper_bytes = HELPER.read_bytes()
    helper_sha = hashlib.sha256(helper_bytes).hexdigest()
    (output/'executed-STL-helper-source.txt').write_bytes(helper_bytes)
    helper = runpy.run_path(str(HELPER.resolve()), run_name='owned_mesh_repair_stl_helpers')
    # Only helper definitions are loaded; the owned Separate generator's run is not called.
    sources = {}
    for name in ('closed',):
        vertices, triangles = helper['_source_data'](False)
        triangles = triangles[:3] if name == 'open' else triangles
        text, normals = helper['_stl'](vertices, triangles, 'owned_'+name+'_repair_tetra')
        path = output/('owned-'+name+'-repair-tetra.stl')
        path.write_text(text, encoding='ascii')
        sources[name] = dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            numeric_vertices=vertices,triangle_vertex_indices=triangles,facet_normals=normals,
            one_STL_solid=True,vertex_count=4,triangle_count=len(triangles),
            source_closed=name == 'closed',source_boundary_edge_count=3 if name == 'open' else 0,
            volume_reference_cm3=4. if name == 'closed' else None,
            volume_reference_scope='Open source has no enclosed volume; tetrahedral sums are not physical volume',
            import_units='CentimeterMeshUnit')
    truth = dict(fusion_version=app.version,samples=[],errors=[],planned_cases=list(cases),
        executed_generator_sha256=source_sha,mesh_source_helper_sha256=helper_sha,
        mesh_source_helper_path=str(HELPER.resolve()),helper_snapshot='executed-STL-helper-source.txt',
        helper_execution_scope='Absolute runpy loads owned Separate _source_data/_stl definitions only; its Fusion run is never called. Exact executed generator/helper snapshots retained.',
        sdk_runtime_module=str(sdk_path),sdk_runtime_source_sha256=hashlib.sha256(sdk_bytes).hexdigest(),
        sdk_surface_snapshot='executed-sdk-mesh-repair-surface.txt',
        sdk_surface_snapshot_sha256=hashlib.sha256(sdk_snapshot.encode()).hexdigest(),
        sdk_method_enum_values={n:int(getattr(adsk.fusion.MeshRepairTypes,n)) for n in ('StitchAndRemoveMeshRepairType','RebuildMeshRepairType')},
        sdk_rebuild_enum_values={n:int(getattr(adsk.fusion.MeshRepairRebuildTypes,n)) for n in ('FastMeshRepairRebuildType','AccurateMeshRepairRebuildType')},
        sdk_scope='Active preview createInput(mesh)/meshRepairType=Rebuild/meshRepairRebuildType/density/Accurate-only offset/add. Input numeric setters accept ValueInput; feature exposes ModelParameter. Feature.mesh getter only immediately before feature timeline node.',
        control_scope='Density8 is the documented lower bound8..256(default128); Fast/Accurate contrast at8, Accurate offset0/0.05cm. Offset is neither read nor set for actual Fast mode; no Wrap/OneTouch requests. Actual getters and errors override requested/default assumptions.',
        source_meshes=sources,
        import_scope='One owned one-solid STL import per fresh BaseFeature edit; finish before Repair. Multiple imports or null returns retained as actual failure, no merging.',
        identity_scope='Actual input/rolled mesh handle equality and explicit collections captured separately. Tokens stay opaque; arrays, order, names and coordinates do not choose native IDs.',
        result_scope='No repair success, hole closure, topology, output count, visibility or source lifecycle outcome assumed. All actual getters, health/errors and arrays retained.')

    def persist():
        (output/'ground_truth.json').write_text(json.dumps(truth, indent=2)+'\n')

    def journal(phase, case=None, **fields):
        event = dict(phase=phase, case=case, time_utc=datetime.now(timezone.utc).isoformat(),
            sample_count=len(truth['samples']), error_count=len(truth['errors']), **fields)
        with (output/'journal.jsonl').open('a') as stream:
            stream.write(json.dumps(event)+'\n')
        (output/'progress.json').write_text(json.dumps(event, indent=2)+'\n')
        persist()

    def observe(label, getter, errors):
        try:
            return getter()
        except Exception:
            errors.append(dict(getter=label, error=traceback.format_exc()))
            return None

    def items(collection):
        if collection is None:
            return None
        if hasattr(collection, 'item') and hasattr(collection, 'count'):
            return [collection.item(i) for i in range(collection.count)]
        return list(collection)

    def identity(entity):
        if entity is None:
            return None
        row, errors = {}, []
        for prop in ('objectType', 'isValid', 'name', 'entityToken'):
            if hasattr(type(entity), prop):
                row[prop] = observe(prop, lambda prop=prop: getattr(entity, prop), errors)
        row['getter_errors'] = errors
        return row

    def box(value):
        return dict(min=value.minPoint.asArray(), max=value.maxPoint.asArray())

    def face_group(value):
        row, errors = identity(value), []
        for prop in ('tempId', 'area', 'isPlanar'):
            row[prop] = observe(prop, lambda prop=prop: getattr(value, prop), errors)
        row['parentBody'] = observe('parentBody', lambda: identity(value.parentBody), errors)
        row['centroid_cm'] = observe('centroid', lambda: value.centroid.asArray(), errors)
        row['bounding_box_cm'] = observe('boundingBox', lambda: box(value.boundingBox), errors)
        row['face_group_getter_errors'] = errors
        row['temp_id_scope'] = 'Actual temporary API ID, valid only while owning mesh is unchanged; no native record conversion'
        return row

    def mesh_array(mesh, display=False):
        if mesh is None:
            return None
        row, errors = {}, []
        props = ['objectType', 'nodeCount', 'nodeCoordinatesAsDouble', 'triangleCount', 'normalVectorsAsDouble']
        props += ['nodeIndices', 'surfaceTolerance'] if display else [
            'quadCount', 'polygonCount', 'triangleNodeIndices', 'triangleFaceGroupTempIds',
            'quadNodeIndices', 'polygonNodeIndices', 'nodeCountPerPolygon']
        for prop in props:
            row[prop] = observe(prop, lambda prop=prop: getattr(mesh, prop), errors)
        row['getter_errors'] = errors
        return row

    def mesh_body(body):
        if body is None:
            return None
        row, errors = identity(body), []
        for prop in ('area', 'volume', 'isClosed', 'isOriented', 'isVisible', 'isLightBulbOn'):
            row[prop] = observe(prop, lambda prop=prop: getattr(body, prop), errors)
        row['bounding_box_cm'] = observe('boundingBox', lambda: box(body.boundingBox), errors)
        for prop in ('baseOrFormFeature', 'parentComponent', 'assemblyContext', 'nativeObject'):
            row[prop] = observe(prop, lambda prop=prop: identity(getattr(body, prop)), errors)
        row['original_polygon_mesh'] = observe('mesh', lambda: mesh_array(body.mesh), errors)
        row['display_triangle_mesh'] = observe('displayMesh', lambda: mesh_array(body.displayMesh, True), errors)
        row['face_groups'] = observe('faceGroups', lambda: [face_group(f) for f in items(body.faceGroups)], errors)
        row['mesh_getter_errors'] = errors
        return row

    def component_meshes(root):
        errors = []
        bodies = observe('root.meshBodies', lambda: items(root.meshBodies), errors)
        return dict(count=len(bodies) if bodies is not None else None,
            meshes=[mesh_body(b) for b in bodies] if bodies is not None else None, getter_errors=errors)

    def parameter(value):
        if value is None:
            return None
        row, errors = identity(value), []
        for prop in ('name', 'role', 'value', 'unit', 'expression'):
            row[prop] = observe(prop, lambda prop=prop: getattr(value, prop), errors)
        row['createdBy'] = observe('createdBy', lambda: identity(value.createdBy), errors)
        row['parameter_getter_errors'] = errors
        return row

    def value_input(value):
        if value is None:
            return None
        row, errors = identity(value), []
        kind = observe('valueType', lambda: value.valueType, errors)
        row['valueType'] = int(kind) if kind is not None else None
        if kind == adsk.core.ValueTypes.RealValueType:
            row['realValue'] = observe('realValue', lambda: value.realValue, errors)
        elif kind == adsk.core.ValueTypes.StringValueType:
            row['stringValue'] = observe('stringValue', lambda: value.stringValue, errors)
        row['value_input_getter_errors'] = errors
        return row

    def controls(entity,include_mesh=False,is_input=False):
        row,errors=identity(entity),[]
        method=observe('meshRepairType',lambda:int(entity.meshRepairType),errors)
        row['meshRepairType']=method
        row['control_activity']={}
        if method==int(adsk.fusion.MeshRepairTypes.RebuildMeshRepairType):
            rebuild=observe('meshRepairRebuildType',lambda:int(entity.meshRepairRebuildType),errors)
            row['meshRepairRebuildType']=rebuild
            row['control_activity']['meshRepairRebuildType']=dict(status='ApplicableToActualRebuild',getter_called=True)
            density=observe('density',lambda:entity.density,errors)
            row['density']=value_input(density) if is_input else parameter(density)
            row['control_activity']['density']=dict(status='ApplicableToActualRebuild',getter_called=True)
            if rebuild==int(adsk.fusion.MeshRepairRebuildTypes.AccurateMeshRepairRebuildType):
                offset=observe('offset',lambda:entity.offset,errors)
                row['offset']=value_input(offset) if is_input else parameter(offset)
                row['control_activity']['offset']=dict(status='ApplicableToActualAccurateRebuild',getter_called=True)
            else:
                row['offset']=None
                row['control_activity']['offset']=dict(status='NotApplicableOrUnresolved',getter_called=False,
                    reason='Offset getter requires observed Accurate Rebuild type; not invoked for Fast or unknown type')
        else:
            for prop in ('meshRepairRebuildType','density','offset'):
                row[prop]=None
                row['control_activity'][prop]=dict(status='NotApplicableOrUnresolved',getter_called=False,
                    reason='Actual Rebuild mode not observed; inactive getter not invoked')
        if is_input:
            row['targetBaseFeature']=observe('targetBaseFeature',lambda:identity(entity.targetBaseFeature),errors)
        if include_mesh:
            actual=observe('mesh',lambda:entity.mesh,errors)
            row['input_entity']=identity(actual)
            row['input_kind']='MeshBody' if adsk.fusion.MeshBody.cast(actual) is not None else 'OtherOrNull'
            row['mesh_body']=mesh_body(actual) if row['input_kind']=='MeshBody' else None
        row['control_getter_errors']=errors
        return row

    def feature_truth(feature, include_mesh=False):
        if feature is None:
            return None
        row, errors = controls(feature, include_mesh), []
        for prop in ('healthState', 'errorOrWarningMessage', 'isParametric', 'isSuppressed'):
            row[prop] = observe(prop, lambda prop=prop: int(getattr(feature, prop)) if prop == 'healthState' else getattr(feature, prop), errors)
        row['parentComponent'] = observe('parentComponent', lambda: identity(feature.parentComponent), errors)
        row['baseFeature'] = observe('baseFeature', lambda: identity(feature.baseFeature), errors)
        row['timeline_index'] = observe('timelineObject.index', lambda: feature.timelineObject.index, errors)
        for prop in ('bodies', 'faces'):
            row['brep_'+prop] = observe(prop, lambda prop=prop: None if getattr(feature, prop) is None
                else [identity(v) for v in items(getattr(feature, prop))], errors)
        row['brep_scope'] = 'Inherited BRep collections recorded literally; they are not an inferred mesh output collection'
        row['feature_getter_errors'] = errors
        return row

    def base_truth(base):
        row, errors = identity(base), []
        for prop in ('healthState', 'errorOrWarningMessage', 'isParametric'):
            row[prop] = observe(prop, lambda prop=prop: int(getattr(base, prop)) if prop == 'healthState' else getattr(base, prop), errors)
        row['mesh_bodies'] = observe('meshBodies', lambda: [mesh_body(m) for m in items(base.meshBodies)], errors)
        row['brep_source_bodies'] = observe('sourceBodies', lambda: [identity(b) for b in items(base.sourceBodies)], errors)
        row['brep_bodies'] = observe('bodies', lambda: [identity(b) for b in items(base.bodies)], errors)
        row['timeline_index'] = observe('timelineObject.index', lambda: base.timelineObject.index, errors)
        row['base_getter_errors'] = errors
        return row

    journal('batch_begin', output_directory=str(output))
    for case, (rebuild_name, density_value, offset_value) in cases.items():
        source_name, method_name = 'closed', 'RebuildMeshRepairType'
        doc = design = base = None
        editing = False
        sample = dict(case=case, file=case+'.f3d', getter_errors=[], setter_errors=[], phase='document_create',
            requested=dict(source=source_name,method=method_name,rebuild_method=rebuild_name,density=density_value,
                offset_cm=offset_value,offset_set=offset_value is not None,targetBaseFeature_set=False),
            setter_requests=[])
        truth['active_sample'] = sample
        try:
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            if design is None:
                raise RuntimeError('Owned document has no Fusion Design')
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sample['root_component'] = identity(root)
            sample['component_meshes_before_import'] = component_meshes(root)
            base = root.features.baseFeatures.add()
            base.name = 'Owned Rebuild import '+case
            sample['base_start_edit_returned'] = bool(base.startEdit())
            if not sample['base_start_edit_returned']:
                raise RuntimeError('Owned BaseFeature.startEdit returned false')
            editing = True
            sample['phase'] = 'owned_STL_import'
            journal('owned_STL_import_begin', case)
            imported = root.meshBodies.add(str(output/sources[source_name]['file']), adsk.fusion.MeshUnits.CentimeterMeshUnit, base)
            if imported is None:
                raise RuntimeError('Owned STL import returned null collection')
            handles = items(imported)
            sample['actual_imported_mesh_count'] = len(handles)
            for index, mesh in enumerate(handles):
                mesh.name = 'OwnedRebuildSource_'+case+('_import'+str(index) if len(handles) != 1 else '')
            sample['imported_meshes_during_edit'] = [mesh_body(mesh) for mesh in handles]
            sample['base_finish_edit_returned'] = bool(base.finishEdit())
            if not sample['base_finish_edit_returned']:
                raise RuntimeError('Owned BaseFeature.finishEdit returned false')
            editing = False
            design.timeline.moveToEnd()
            sample['base_after_edit'] = base_truth(base)
            sample['imported_handles_before_repair'] = [mesh_body(mesh) for mesh in handles]
            sample['component_meshes_before_repair'] = component_meshes(root)
            sample['model_parameters_before'] = observe('modelParameters before',
                lambda: [parameter(p) for p in root.modelParameters], sample['getter_errors'])
            feature = None
            sample['phase'] = 'mesh_repair_attempt'
            try:
                if len(handles) != 1:
                    raise RuntimeError('Single-STL import produced '+str(len(handles))+' MeshBodies; one-body Repair input not manufactured')
                source_mesh = handles[0]
                sample['source_before_repair'] = mesh_body(source_mesh)
                collection = root.features.meshRepairFeatures
                sample['repair_collection_count_before'] = collection.count
                inputs = collection.createInput(source_mesh)
                if inputs is None:
                    raise RuntimeError('MeshRepair createInput returned null')
                sample['input_defaults'] = controls(inputs, True, True)
                method = getattr(adsk.fusion.MeshRepairTypes, method_name)
                rebuild = getattr(adsk.fusion.MeshRepairRebuildTypes, rebuild_name)
                sample['requested']['method_enum'] = int(method)
                sample['requested']['rebuild_method_enum'] = int(rebuild)
                def assign(prop, value, requested):
                    entry=dict(property=prop,requested=requested,assignment_completed=False,
                        return_scope='Python property assignment has no exposed setter return value')
                    sample['setter_requests'].append(entry)
                    try:
                        setattr(inputs, prop, value)
                        entry['assignment_completed']=True
                    except Exception:
                        error=dict(property=prop,error=traceback.format_exc())
                        entry['error']=error['error'];sample['setter_errors'].append(error)
                        raise
                assign('meshRepairType',method,dict(enum_name=method_name,enum_value=int(method)))
                assign('meshRepairRebuildType',rebuild,dict(enum_name=rebuild_name,enum_value=int(rebuild)))
                density_input=adsk.core.ValueInput.createByReal(density_value)
                sample['requested_density_value_input']=value_input(density_input)
                assign('density',density_input,sample['requested_density_value_input'])
                if offset_value is not None:
                    offset_input=adsk.core.ValueInput.createByReal(offset_value)
                    sample['requested_offset_value_input']=value_input(offset_input)
                    assign('offset',offset_input,sample['requested_offset_value_input'])
                else:
                    sample['requested_offset_value_input']=None
                    sample['offset_setter_status']='Not invoked: requested Fast Rebuild has no applicable offset control'
                sample['input_before_add'] = controls(inputs, True, True)
                sample['input_mesh_equals_import_handle'] = observe('input.mesh == source',
                    lambda: inputs.mesh == source_mesh, sample['getter_errors'])
                journal('mesh_repair_add_begin', case)
                feature = collection.add(inputs)
                sample['add_returned_feature'] = feature is not None
                if feature is None:
                    raise RuntimeError('Parametric MeshRepair add returned null; actual unchanged/current mesh still exported')
                feature.name = 'OwnedMeshRepairRebuild_'+case
                sample['repair_status'] = 'FeatureReturned'
                journal('mesh_repair_feature_returned', case)
            except Exception:
                sample['repair_status'] = 'AttemptError'
                error = dict(case=case, phase='mesh_repair_attempt', error=traceback.format_exc(),
                    policy='Preserve actual import/no-op/failure source and current arrays, export local archive; no successful repair or expected result count assumed')
                sample['repair_error'] = error
                truth['errors'].append(error)
                journal('mesh_repair_attempt_error', case)
            design.timeline.moveToEnd()
            sample['compute_all_returned'] = observe('design.computeAll', lambda: design.computeAll(), sample['getter_errors'])
            sample['component_meshes_after_repair'] = component_meshes(root)
            sample['original_handles_after_repair'] = [observe('original imported handle'+str(i),
                lambda mesh=mesh: mesh_body(mesh), sample['getter_errors']) for i, mesh in enumerate(handles)]
            sample['feature_at_timeline_end'] = feature_truth(feature)
            sample['base_after_repair'] = base_truth(base)
            sample['model_parameters_after'] = observe('modelParameters after',
                lambda: [parameter(p) for p in root.modelParameters], sample['getter_errors'])
            if feature is not None:
                try:
                    sample['roll_before_feature_returned'] = bool(feature.timelineObject.rollTo(True))
                    if sample['roll_before_feature_returned']:
                        sample['feature_before_node'] = feature_truth(feature, True)
                        sample['component_meshes_before_node'] = component_meshes(root)
                        sample['rolled_mesh_equals_import_handle'] = observe('feature.mesh == source before node',
                            lambda: feature.mesh == handles[0], sample['getter_errors'])
                except Exception:
                    sample['getter_errors'].append(dict(getter='MeshRepair rolled snapshot', error=traceback.format_exc()))
                finally:
                    design.timeline.moveToEnd()
            sample['repair_collection_count_after'] = observe('repairFeatures.count',
                lambda: root.features.meshRepairFeatures.count, sample['getter_errors'])
            sample['timeline_count'] = design.timeline.count
            sample['timeline_marker_position'] = design.timeline.markerPosition
            sample['phase'] = 'local_export'
            journal('local_export_begin', case)
            destination = output/sample['file']
            succeeded = design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(destination)))
            if not succeeded or not destination.is_file() or not destination.stat().st_size:
                raise RuntimeError('Owned MeshRepair local archive export failed')
            sample['export'] = dict(returned_success=bool(succeeded), size_bytes=destination.stat().st_size,
                sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
            sample['phase'] = 'export_complete'
            truth['samples'].append(sample)
            journal('local_export_complete', case)
        except Exception:
            truth['errors'].append(dict(case=case, phase=sample['phase'], error=traceback.format_exc(), partial_sample=sample))
            journal('case_error', case)
        finally:
            if editing and base is not None:
                try:
                    finished = base.finishEdit()
                    sample['cleanup_base_finish_edit_returned'] = bool(finished)
                    if not finished:
                        truth['errors'].append(dict(case=case, phase='cleanup_base_edit', error='finishEdit returned false'))
                except Exception:
                    truth['errors'].append(dict(case=case, phase='cleanup_base_edit', error=traceback.format_exc()))
            if design is not None:
                try:
                    design.timeline.moveToEnd()
                except Exception:
                    truth['errors'].append(dict(case=case, phase='restore_owned_timeline', error=traceback.format_exc()))
            if doc is not None:
                try:
                    journal('owned_document_close_begin', case, save=False)
                    returned = bool(doc.close(False))
                    sample['close_owned_document_returned'] = returned
                    journal('owned_document_close_returned', case, save=False, returned=returned)
                    if not returned:
                        truth['errors'].append(dict(case=case, phase='close_owned_document', error='close(False) returned false'))
                except Exception:
                    truth['errors'].append(dict(case=case, phase='close_owned_document', error=traceback.format_exc()))
            truth.pop('active_sample', None)
            persist()
    truth['terminal_status'] = 'complete' if len(truth['samples']) == len(cases) and not truth['errors'] else 'complete_with_errors'
    truth['exported_sample_count'] = len(truth['samples'])
    journal('batch_terminal')
    (output/'complete.txt').write_text('MeshRepair terminal: '+truth['terminal_status']+'; inspect actual import/method/result/errors.\n')
