"""Owned preview MeshRemove captures, prepared for parent-only serial dispatch.

The actual add result is an array. Neither feature cardinality nor remaining
mesh count/identity is assumed from documentation or array positions.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import runpy
import traceback
import uuid

import adsk.core
import adsk.fusion

HELPER = Path('/Users/stephenh/.codex/visualizations/2026/10/17/01a14ba1-a51c-7f72-b92e-9f1f0114012e/FusionFileStudy/GenerateMeshSeparateContrasts.py')
CASES = {'one_remove_one': (1, [0]), 'two_remove_first': (2, [0]), 'two_remove_both': (2, [0, 1])}


def run(context):
    app = adsk.core.Application.get()
    cases = CASES
    if isinstance(context, dict) and 'cases' in context:
        selected = context['cases']
        if not isinstance(selected, (list, tuple)) or not selected or len(set(selected)) != len(selected) or set(selected)-set(CASES):
            raise ValueError('Select distinct known MeshRemove cases')
        cases = {n: c for n, c in CASES.items() if n in selected}
    source = Path(__file__).resolve()
    output = source.parent/('meshremoves-'+uuid.uuid4().hex[:12])
    output.mkdir()
    executed = source.read_bytes()
    source_sha = hashlib.sha256(executed).hexdigest()
    (output/'executed-generator-source.txt').write_bytes(executed)
    helper_bytes = HELPER.read_bytes()
    (output/'executed-STL-helper-source.txt').write_bytes(helper_bytes)
    helper_sha = hashlib.sha256(helper_bytes).hexdigest()
    helper = runpy.run_path(str(HELPER.resolve()), run_name='owned_mesh_remove_stl_helpers')
    # runpy only defines the owned helper module; its Fusion run() is never called.
    sdk_path = Path(adsk.fusion.__file__).resolve()
    if sdk_path.suffix == '.pyc' and sdk_path.with_suffix('.py').is_file():
        sdk_path = sdk_path.with_suffix('.py')
    sdk_bytes = sdk_path.read_bytes()
    sdk_text = sdk_bytes.decode('utf-8')
    snippets = []
    for name in ('MeshRemoveFeatureInput', 'MeshRemoveFeatures', 'MeshRemoveFeature', 'MeshRemoveFeatureVector'):
        start = sdk_text.index('class '+name+'(')
        end = sdk_text.find('\nclass ', start+1)
        snippets.append(sdk_text[start:end if end >= 0 else None])
    sdk_snapshot = '\n\n'.join(snippets)
    (output/'executed-sdk-mesh-remove-surface.txt').write_text(sdk_snapshot)
    vertices, triangles = helper['_source_data'](False)
    sources = []
    for index, shift in enumerate((0., 4.)):
        points = [(p[0]+shift, p[1], p[2]) for p in vertices]
        text, normals = helper['_stl'](points, triangles, 'owned_remove_tetra_'+str(index))
        path = output/('owned-remove-tetra-'+str(index)+'.stl')
        path.write_text(text, encoding='ascii')
        sources.append(dict(file=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            numeric_vertices=points, triangle_vertex_indices=triangles, facet_normals=normals,
            offset_cm=[shift, 0., 0.], source_signed_volume_cm3=4., one_STL_solid=True,
            import_units='CentimeterMeshUnit'))
    truth = dict(fusion_version=app.version, samples=[], errors=[], planned_cases=list(cases),
        executed_generator_sha256=source_sha, mesh_source_helper_sha256=helper_sha,
        mesh_source_helper_path=str(HELPER.resolve()), helper_snapshot='executed-STL-helper-source.txt',
        helper_execution_scope='Absolute runpy loads owned Separate STL helper definitions only; its run() is never called',
        sdk_runtime_module=str(sdk_path), sdk_runtime_source_sha256=hashlib.sha256(sdk_bytes).hexdigest(),
        sdk_surface_snapshot='executed-sdk-mesh-remove-surface.txt',
        sdk_surface_snapshot_sha256=hashlib.sha256(sdk_snapshot.encode()).hexdigest(), source_meshes=sources,
        SDK_scope='Preview MeshRemoveFeatures.createInput(list[MeshBody]); add returns array per documentation. Actual returned type/count/features independently captured.',
        input_scope='Separate one-solid STL imports into one fresh owned BaseFeature edit, finish before Remove. No merger, imported-array identity guess or existing document edits.',
        identity_scope='Requested source list positions are separate from actual input getter and handle equality matrices. Tokens remain opaque; geometry/name/order never chooses native identity.',
        result_scope='Current collections, each returned feature and rolled inputs recorded. No assumed one-feature-per-input, deletion flag, source lifecycle or remaining output identity.')

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
        row, errors = identity(value), []
        for prop in ('name', 'role', 'value', 'unit', 'expression'):
            row[prop] = observe(prop, lambda prop=prop: getattr(value, prop), errors)
        row['createdBy'] = observe('createdBy', lambda: identity(value.createdBy), errors)
        row['parameter_getter_errors'] = errors
        return row

    def equality_matrix(left, right, errors, label):
        return [[observe(label+' '+str(i)+','+str(j), lambda a=a,b=b: a == b, errors)
            for j,b in enumerate(right)] for i,a in enumerate(left)]

    def input_truth(inputs):
        row, errors = identity(inputs), []
        bodies = observe('inputBodies', lambda: items(inputs.inputBodies), errors)
        row['inputBodies'] = [mesh_body(b) for b in bodies] if bodies is not None else None
        row['input_body_count'] = len(bodies) if bodies is not None else None
        row['targetBaseFeature'] = observe('targetBaseFeature', lambda: identity(inputs.targetBaseFeature), errors)
        row['input_getter_errors'] = errors
        return row

    def feature_truth(feature):
        row, errors = identity(feature), []
        for prop in ('healthState', 'errorOrWarningMessage', 'isParametric', 'isSuppressed'):
            row[prop] = observe(prop, lambda prop=prop: int(getattr(feature, prop)) if prop == 'healthState' else getattr(feature, prop), errors)
        bodies = observe('inputBodies', lambda: items(feature.inputBodies), errors)
        row['inputBodies'] = [mesh_body(b) for b in bodies] if bodies is not None else None
        row['input_body_count'] = len(bodies) if bodies is not None else None
        row['parentComponent'] = observe('parentComponent', lambda: identity(feature.parentComponent), errors)
        row['baseFeature'] = observe('baseFeature', lambda: identity(feature.baseFeature), errors)
        row['timeline_index'] = observe('timelineObject.index', lambda: feature.timelineObject.index, errors)
        for prop in ('bodies', 'faces'):
            row['brep_'+prop] = observe(prop, lambda prop=prop: None if getattr(feature, prop) is None
                else [identity(v) for v in items(getattr(feature, prop))], errors)
        row['brep_scope'] = 'Inherited BRep collections literal only; not a mesh result collection'
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
    for case, (import_count, requested_indices) in cases.items():
        doc = design = base = None
        editing = False
        sample = dict(case=case, file=case+'.f3d', getter_errors=[], phase='document_create',
            requested=dict(separate_STL_import_count=import_count, remove_import_request_indices=requested_indices,
                targetBaseFeature_set=False, documentation_feature_cardinality_not_assumed=True))
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
            base.name = 'Owned Remove import '+case
            sample['base_start_edit_returned'] = bool(base.startEdit())
            if not sample['base_start_edit_returned']:
                raise RuntimeError('Owned BaseFeature.startEdit returned false')
            editing = True
            all_handles, import_batches = [], []
            sample['phase'] = 'owned_STL_import'
            for index in range(import_count):
                journal('owned_STL_import_begin', case, source_request_index=index)
                collection = root.meshBodies.add(str(output/sources[index]['file']), adsk.fusion.MeshUnits.CentimeterMeshUnit, base)
                handles = items(collection) if collection is not None else None
                if handles is None:
                    raise RuntimeError('Owned STL import returned null collection')
                for j, mesh in enumerate(handles):
                    mesh.name = 'OwnedRemoveSource_'+case+'_request'+str(index)+'_item'+str(j)
                import_batches.append(handles)
                all_handles.extend(handles)
                sample.setdefault('imports', []).append(dict(source_request_index=index, actual_count=len(handles),
                    actual_meshes_during_edit=[mesh_body(m) for m in handles]))
                journal('owned_STL_import_complete', case, source_request_index=index, actual_count=len(handles))
            sample['base_finish_edit_returned'] = bool(base.finishEdit())
            if not sample['base_finish_edit_returned']:
                raise RuntimeError('Owned BaseFeature.finishEdit returned false')
            editing = False
            design.timeline.moveToEnd()
            sample['base_after_edit'] = base_truth(base)
            sample['all_imported_meshes_before_remove'] = [mesh_body(m) for m in all_handles]
            sample['component_meshes_before_remove'] = component_meshes(root)
            sample['model_parameters_before'] = observe('modelParameters before', lambda: [parameter(p) for p in root.modelParameters], sample['getter_errors'])
            returned_features = []
            sample['phase'] = 'mesh_remove_attempt'
            try:
                if any(len(batch) != 1 for batch in import_batches):
                    raise RuntimeError('A separate owned one-solid STL did not import exactly one MeshBody; no removal input manufactured')
                selected_handles = [import_batches[index][0] for index in requested_indices]
                sample['selected_actual_meshes_before_add'] = [mesh_body(m) for m in selected_handles]
                collection = root.features.meshRemoveFeatures
                sample['remove_collection_count_before'] = collection.count
                inputs = collection.createInput(selected_handles)
                if inputs is None:
                    raise RuntimeError('MeshRemove createInput returned null')
                sample['input_defaults'] = input_truth(inputs)
                sample['input_before_add'] = input_truth(inputs)
                actual_inputs = observe('inputBodies handle list', lambda: items(inputs.inputBodies), sample['getter_errors'])
                sample['input_bodies_vs_requested_handle_equality'] = equality_matrix(actual_inputs, selected_handles, sample['getter_errors'], 'configured input vs request') if actual_inputs is not None else None
                sample['input_bodies_vs_all_imported_handle_equality'] = equality_matrix(actual_inputs, all_handles, sample['getter_errors'], 'configured input vs all imports') if actual_inputs is not None else None
                journal('mesh_remove_add_begin', case)
                returned = collection.add(inputs)
                sample['add_returned_python_type'] = type(returned).__name__
                sample['add_returned_null'] = returned is None
                if returned is None:
                    raise RuntimeError('MeshRemove add returned null; current meshes still exported')
                returned_features = items(returned)
                sample['add_returned_feature_count'] = len(returned_features)
                sample['add_returned_object_types'] = [observe('returned feature objectType '+str(i), lambda f=f: f.objectType, sample['getter_errors']) for i,f in enumerate(returned_features)]
                for index, feature in enumerate(returned_features):
                    if feature is None:
                        raise RuntimeError('MeshRemove add returned array containing null feature')
                    feature.name = 'OwnedMeshRemove_'+case+'_returned'+str(index)
                sample['remove_status'] = 'FeatureArrayReturned'
                journal('mesh_remove_feature_array_returned', case, actual_count=len(returned_features))
            except Exception:
                sample['remove_status'] = 'AttemptError'
                error = dict(case=case, phase='mesh_remove_attempt', error=traceback.format_exc(),
                    policy='Preserve actual add/import errors, returned cardinality and current arrays; no successful removal assumed')
                sample['remove_error'] = error
                truth['errors'].append(error)
                journal('mesh_remove_attempt_error', case)
            design.timeline.moveToEnd()
            sample['compute_all_returned'] = observe('design.computeAll', lambda: design.computeAll(), sample['getter_errors'])
            sample['component_meshes_after_remove'] = component_meshes(root)
            current_handles = observe('root current mesh handles', lambda: items(root.meshBodies), sample['getter_errors'])
            sample['remaining_current_vs_all_imported_handle_equality'] = equality_matrix(current_handles, all_handles, sample['getter_errors'], 'remaining vs imports') if current_handles is not None else None
            sample['imported_handle_identity_after_remove'] = [identity(m) for m in all_handles]
            sample['features_at_timeline_end'] = [feature_truth(f) for f in returned_features if f is not None]
            sample['base_after_remove'] = base_truth(base)
            sample['model_parameters_after'] = observe('modelParameters after', lambda: [parameter(p) for p in root.modelParameters], sample['getter_errors'])
            sample['rolled_features'] = []
            for index, feature in enumerate(returned_features):
                if feature is None:
                    continue
                rolled = dict(returned_array_index=index, getter_errors=[])
                try:
                    rolled['roll_before_feature_returned'] = bool(feature.timelineObject.rollTo(True))
                    if rolled['roll_before_feature_returned']:
                        rolled['feature_before_node'] = feature_truth(feature)
                        rolled['component_meshes_before_node'] = component_meshes(root)
                        bodies = observe('rolled feature.inputBodies', lambda: items(feature.inputBodies), rolled['getter_errors'])
                        rolled['input_bodies_vs_all_imported_handle_equality'] = equality_matrix(bodies, all_handles, rolled['getter_errors'], 'rolled input vs all imports') if bodies is not None else None
                except Exception:
                    rolled['getter_errors'].append(dict(getter='MeshRemove rolled snapshot', error=traceback.format_exc()))
                finally:
                    design.timeline.moveToEnd()
                sample['rolled_features'].append(rolled)
            sample['remove_collection_count_after'] = observe('meshRemoveFeatures.count', lambda: root.features.meshRemoveFeatures.count, sample['getter_errors'])
            sample['remove_collection_at_timeline_end'] = observe('meshRemoveFeatures entries', lambda: [identity(f) for f in items(root.features.meshRemoveFeatures)], sample['getter_errors'])
            sample['timeline_count'] = design.timeline.count
            sample['timeline_marker_position'] = design.timeline.markerPosition
            sample['phase'] = 'local_export'
            journal('local_export_begin', case)
            destination = output/sample['file']
            succeeded = design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(destination)))
            if not succeeded or not destination.is_file() or not destination.stat().st_size:
                raise RuntimeError('Owned MeshRemove local archive export failed')
            sample['export'] = dict(returned_success=bool(succeeded),size_bytes=destination.stat().st_size,
                sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
            sample['phase'] = 'export_complete'
            truth['samples'].append(sample)
            journal('local_export_complete', case)
        except Exception:
            truth['errors'].append(dict(case=case,phase=sample['phase'],error=traceback.format_exc(),partial_sample=sample))
            journal('case_error', case)
        finally:
            if editing and base is not None:
                try:
                    finished=bool(base.finishEdit())
                    sample['cleanup_base_finish_edit_returned']=finished
                    if not finished: truth['errors'].append(dict(case=case,phase='cleanup_base_edit',error='finishEdit returned false'))
                except Exception:
                    truth['errors'].append(dict(case=case,phase='cleanup_base_edit',error=traceback.format_exc()))
            if design is not None:
                try: design.timeline.moveToEnd()
                except Exception: truth['errors'].append(dict(case=case,phase='restore_owned_timeline',error=traceback.format_exc()))
            if doc is not None:
                try:
                    journal('owned_document_close_begin',case,save=False)
                    returned=bool(doc.close(False))
                    sample['close_owned_document_returned']=returned
                    journal('owned_document_close_returned',case,save=False,returned=returned)
                    if not returned: truth['errors'].append(dict(case=case,phase='close_owned_document',error='close(False) returned false'))
                except Exception:
                    truth['errors'].append(dict(case=case,phase='close_owned_document',error=traceback.format_exc()))
            truth.pop('active_sample',None)
            persist()
    truth['terminal_status']='complete' if len(truth['samples'])==len(cases) and not truth['errors'] else 'complete_with_errors'
    truth['exported_sample_count']=len(truth['samples'])
    journal('batch_terminal')
    (output/'complete.txt').write_text('MeshRemove terminal: '+truth['terminal_status']+'; inspect actual returned arrays/current collections/errors.\n')
