"""Owned Faceted conversion ownership contrasts; prepared, root dispatch only.

Two BaseFeature operation cases and a two-input Parametric case. A null add()
return is documented for non-parametric conversion and retained without a
conversion-success claim; actual independent component collections decide truth.
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

CASES = {
    'base_feature_closed': ('BaseFeatureMeshConvertOperationType', False, 1),
    'base_feature_open': ('BaseFeatureMeshConvertOperationType', True, 1),
    'two_mesh_parametric': ('ParametricFeatureMeshConvertOperationType', False, 2),
}


def run(context):
    app = adsk.core.Application.get()
    cases = CASES
    if isinstance(context, dict) and 'cases' in context:
        selected = context['cases']
        if not isinstance(selected, (list, tuple)) or not selected or len(set(selected)) != len(selected) or set(selected)-set(CASES):
            raise ValueError('Select one to three distinct known MeshConvert operation cases')
        cases = {name: spec for name, spec in CASES.items() if name in selected}
    source = Path(__file__).resolve()
    # Python.RunScript need not add this study directory to sys.path. Loading
    # the owned sibling by absolute path runs definitions only, not its run().
    helper_source = source.with_name('GenerateMeshContrasts.py')
    helper = runpy.run_path(str(helper_source))
    vertices, triangles = helper['VERTICES'], helper['TRIANGLES']
    output = source.parent/('meshconvertoperations-'+uuid.uuid4().hex[:12])
    output.mkdir()
    executed = source.read_bytes()
    dependency = helper_source.read_bytes()
    (output/'executed-generator-source.txt').write_bytes(executed)
    (output/'executed-mesh-source-helper.txt').write_bytes(dependency)
    stl, normals = helper['_stl']()
    stl_path = output/'owned-closed-tetra.stl'
    stl_path.write_text(stl, encoding='ascii')
    # Each source facet occupies seven ASCII lines; remove the opposite face.
    lines = stl.splitlines()
    if len(lines) != 30 or len(triangles) != 4:
        raise ValueError('Unexpected owned helper tetra STL framing')
    open_path = output/'owned-open-tetra.stl'
    open_path.write_text('\n'.join(lines[:22]+['endsolid owned_tetra', '']), encoding='ascii')
    truth = {'samples': [], 'errors': [], 'fusion_version': app.version,
        'executed_generator_sha256': hashlib.sha256(executed).hexdigest(),
        'mesh_source_helper_sha256': hashlib.sha256(dependency).hexdigest(),
        'planned_cases': list(cases),
        'source_meshes': [
            {'file': stl_path.name, 'sha256': hashlib.sha256(stl_path.read_bytes()).hexdigest(),
             'numeric_vertices': vertices, 'triangle_indices': triangles, 'facet_normals': normals,
             'source_closed': True, 'import_units': 'CentimeterMeshUnit'},
            {'file': open_path.name, 'sha256': hashlib.sha256(open_path.read_bytes()).hexdigest(),
             'numeric_vertices': vertices, 'triangle_indices': triangles[:3], 'facet_normals': normals[:3],
             'source_closed': False, 'import_units': 'CentimeterMeshUnit'}],
        'sdk_scope': 'ACTIVE executable adsk.fusion bindings; MeshConvert classes/enums are preview and may change. createInput([mesh])/add only; no UI commands, Organic or licensing assumptions.',
        'sdk_runtime_module': getattr(adsk.fusion, '__file__', None),
        'sdk_runtime_sha256': hashlib.sha256(Path(adsk.fusion.__file__).read_bytes()).hexdigest(),
        'scope': 'Three newly owned parametric documents; owned imports finished before Convert; explicit conversion operation and one/two input handles; independent current mesh, BRep, BaseFeature and timeline snapshots.',
        'controls_scope': 'Faceted only; BaseFeature operation closed/open and Parametric operation two disjoint closed meshes. Organic-only controls not called.',
        'identity_scope': 'Opaque tokens retained as returned; no native ID or persistent topology inference. Returned object type controls the applicable feature/base getters.',
        'operation_scope': 'MeshConvertFeatures.add documents null for non-parametric conversion. Null is retained, not treated as proof of failure or conversion success; current collections/history remain independent evidence.'}
    sdk_text = Path(adsk.fusion.__file__).read_text()
    sdk_blocks = []
    for class_name in ('MeshConvertFeatures', 'MeshConvertFeatureInput', 'MeshConvertFeature', 'MeshConvertOperationTypes', 'MeshConvertMethodTypes', 'BaseFeature', 'Feature', 'TimelineObject'):
        begin = sdk_text.index('class '+class_name+'(')
        end = sdk_text.find('\nclass ', begin+1)
        sdk_blocks.append(sdk_text[begin:] if end < 0 else sdk_text[begin:end])
    sdk_snapshot = '\n'.join(sdk_blocks).encode()
    (output/'executed-sdk-surface.txt').write_bytes(sdk_snapshot)
    truth['executed_sdk_surface_sha256'] = hashlib.sha256(sdk_snapshot).hexdigest()
    # A second closed tetra is translated in the owned ASCII source, before import.
    translated_lines = []
    for line in stl.splitlines():
        if line.strip().startswith('vertex '):
            fields = line.split()
            translated_lines.append('      vertex '+str(float(fields[1])+6.0)+' '+fields[2]+' '+fields[3])
        else:
            translated_lines.append(line)
    second_path = output/'owned-second-closed-tetra.stl'
    second_path.write_text('\n'.join(translated_lines)+'\n', encoding='ascii')
    truth['source_meshes'].append({'file': second_path.name,
        'sha256': hashlib.sha256(second_path.read_bytes()).hexdigest(),
        'numeric_vertices': [[v[0]+6.0,v[1],v[2]] for v in vertices],
        'triangle_indices': triangles, 'facet_normals': normals, 'source_closed': True,
        'import_units': 'CentimeterMeshUnit', 'source_translation_cm': [6.0,0.0,0.0]})


    def persist():
        (output/'ground_truth.json').write_text(json.dumps(truth, indent=2)+'\n')

    def journal(phase, case=None, **fields):
        event = {'time_utc': datetime.now(timezone.utc).isoformat(), 'phase': phase,
            'case': case, 'sample_count': len(truth['samples']), 'error_count': len(truth['errors']), **fields}
        with (output/'journal.jsonl').open('a') as stream:
            stream.write(json.dumps(event)+'\n')
        (output/'progress.json').write_text(json.dumps(event, indent=2)+'\n')
        persist()

    def observe(label, getter, errors):
        try:
            return getter()
        except Exception:
            errors.append({'getter': label, 'error': traceback.format_exc()})
            return None

    def items(value):
        if value is None:
            return None
        if hasattr(value, 'item') and hasattr(value, 'count'):
            return [value.item(i) for i in range(value.count)]
        return list(value)

    def identity(entity):
        if entity is None:
            return None
        errors, row = [], {}
        for prop in ('objectType', 'isValid'):
            row[prop] = observe(prop, lambda prop=prop: getattr(entity, prop), errors)
        # core.Plane has neither name nor token; record only declared identities.
        for prop in ('name', 'entityToken'):
            if hasattr(type(entity), prop):
                row[prop] = observe(prop, lambda prop=prop: getattr(entity, prop), errors)
        row['getter_errors'] = errors
        return row

    def xyz(point):
        return [point.x, point.y, point.z]

    def mesh_array(mesh, display=False):
        if mesh is None:
            return None
        row, errors = {}, []
        props = ['objectType', 'nodeCount', 'nodeCoordinatesAsDouble', 'triangleCount', 'normalVectorsAsDouble']
        props += ['nodeIndices', 'surfaceTolerance'] if display else ['quadCount', 'polygonCount', 'triangleNodeIndices', 'triangleFaceGroupTempIds']
        for prop in props:
            row[prop] = observe(prop, lambda prop=prop: getattr(mesh, prop), errors)
        # Empty polygon arrays in this API throw InternalValidationError. Preserve
        # that actual behavior independently; they cannot prevent other getters.
        if not display:
            for prop in ('quadNodeIndices', 'polygonNodeIndices', 'nodeCountPerPolygon'):
                row[prop] = observe(prop, lambda prop=prop: getattr(mesh, prop), errors)
        row['getter_errors'] = errors
        return row

    def mesh_body(body):
        if body is None:
            return None
        row, errors = identity(body), []
        for prop in ('area', 'volume', 'isClosed', 'isOriented', 'isVisible'):
            row[prop] = observe(prop, lambda prop=prop: getattr(body, prop), errors)
        for prop in ('baseOrFormFeature', 'parentComponent', 'assemblyContext', 'nativeObject'):
            row[prop] = observe(prop, lambda prop=prop: identity(getattr(body, prop)), errors)
        row['bounding_box_cm'] = observe('boundingBox', lambda: {'min': xyz(body.boundingBox.minPoint), 'max': xyz(body.boundingBox.maxPoint)}, errors)
        row['original_polygon_mesh'] = observe('mesh', lambda: mesh_array(body.mesh), errors)
        row['display_triangle_mesh'] = observe('displayMesh', lambda: mesh_array(body.displayMesh, True), errors)
        row['mesh_getter_errors'] = errors
        return row

    def component_meshes(root):
        bodies = items(root.meshBodies)
        return {'count': len(bodies), 'meshes': [mesh_body(b) for b in bodies]}

    def base_truth(base):
        row, errors = identity(base), []
        for prop in ('healthState', 'errorOrWarningMessage', 'isParametric', 'isSuppressed'):
            row[prop] = observe(prop, lambda prop=prop: int(getattr(base, prop)) if prop == 'healthState' else getattr(base, prop), errors)
        row['parentComponent'] = observe('parentComponent', lambda: identity(base.parentComponent), errors)
        row['baseFeature'] = observe('baseFeature', lambda: identity(base.baseFeature), errors)
        row['mesh_bodies'] = observe('meshBodies', lambda: [mesh_body(b) for b in items(base.meshBodies)], errors)
        row['brep_source_bodies'] = observe('sourceBodies', lambda: [identity(b) for b in items(base.sourceBodies)], errors)
        row['brep_bodies'] = observe('bodies', lambda: [identity(b) for b in items(base.bodies)], errors)
        row['collection_scope'] = 'BRep sourceBodies/bodies are not mesh source/result collections'
        row['timeline_index'] = observe('timelineObject.index', lambda: base.timelineObject.index, errors)
        row['base_getter_errors'] = errors
        return row

    def parameter_truth(parameter):
        if parameter is None:
            return None
        errors, row = [], {}
        for prop in ('objectType', 'name', 'expression', 'unit', 'value', 'valueType'):
            row[prop] = observe(prop, lambda prop=prop: int(parameter.valueType) if prop == 'valueType' else getattr(parameter, prop), errors)
        if hasattr(type(parameter), 'role'):
            row['role'] = observe('role', lambda: parameter.role, errors)
        if hasattr(type(parameter), 'createdBy'):
            row['createdBy'] = observe('createdBy', lambda: identity(parameter.createdBy), errors)
        row['getter_errors'] = errors
        return row

    def value_input_truth(value):
        if value is None:
            return None
        errors, row = [], {}
        for prop in ('objectType', 'valueType', 'realValue', 'stringValue'):
            row[prop] = observe(prop, lambda prop=prop: int(value.valueType) if prop == 'valueType' else getattr(value, prop), errors)
        row['getter_errors'] = errors
        return row

    def analytic_geometry(geometry):
        row, errors = identity(geometry), []
        if geometry is None:
            return None
        for prop in ('origin', 'normal', 'axis', 'center', 'referenceVector', 'startPoint', 'endPoint'):
            if hasattr(type(geometry), prop):
                row[prop] = observe(prop, lambda prop=prop: xyz(getattr(geometry, prop)), errors)
        for prop in ('radius', 'halfAngle', 'majorRadius', 'minorRadius', 'surfaceType', 'curveType'):
            if hasattr(type(geometry), prop):
                row[prop] = observe(prop, lambda prop=prop: int(getattr(geometry, prop)) if prop in ('surfaceType', 'curveType') else getattr(geometry, prop), errors)
        row['geometry_getter_errors'] = errors
        return row

    def brep_body(body):
        row, errors = identity(body), []
        for prop in ('tempId', 'isSolid', 'area', 'volume', 'isVisible'):
            row[prop] = observe(prop, lambda prop=prop: getattr(body, prop), errors)
        row['bounding_box_cm'] = observe('boundingBox', lambda: {'min': xyz(body.boundingBox.minPoint), 'max': xyz(body.boundingBox.maxPoint)}, errors)
        row['parentComponent'] = observe('parentComponent', lambda: identity(body.parentComponent), errors)
        row['baseOrFormFeature'] = observe('baseOrFormFeature', lambda: identity(body.baseOrFormFeature), errors)
        row['vertices'] = observe('vertices', lambda: [{'tempId': v.tempId, 'position_cm': xyz(v.geometry)} for v in items(body.vertices)], errors)
        edge_rows = []
        for edge in items(body.edges):
            edge_errors, edge_row = [], {}
            edge_row['tempId'] = observe('tempId', lambda: edge.tempId, edge_errors)
            edge_row['start_vertex_tempId'] = observe('startVertex.tempId', lambda: None if edge.startVertex is None else edge.startVertex.tempId, edge_errors)
            edge_row['end_vertex_tempId'] = observe('endVertex.tempId', lambda: None if edge.endVertex is None else edge.endVertex.tempId, edge_errors)
            edge_row['geometry'] = observe('geometry', lambda: analytic_geometry(edge.geometry), edge_errors)
            edge_row['face_tempIds'] = observe('faces', lambda: [f.tempId for f in items(edge.faces)], edge_errors)
            edge_row['getter_errors'] = edge_errors
            edge_rows.append(edge_row)
        row['edges'] = edge_rows
        face_rows = []
        for face in items(body.faces):
            face_errors, face_row = [], {}
            for prop in ('tempId', 'area', 'isParamReversed'):
                face_row[prop] = observe(prop, lambda prop=prop: getattr(face, prop), face_errors)
            face_row['geometry'] = observe('geometry', lambda: analytic_geometry(face.geometry), face_errors)
            face_row['edge_tempIds'] = observe('edges', lambda: [e.tempId for e in items(face.edges)], face_errors)
            face_row['loops'] = observe('loops', lambda: [{'isOuter': loop.isOuter,
                'coedges': [{'edge_tempId': coedge.edge.tempId, 'isOpposedToEdge': coedge.isOpposedToEdge} for coedge in items(loop.coEdges)]} for loop in items(face.loops)], face_errors)
            face_row['getter_errors'] = face_errors
            face_rows.append(face_row)
        row['faces'] = face_rows
        row['shell_count'] = observe('shells.count', lambda: body.shells.count, errors)
        row['lump_count'] = observe('lumps.count', lambda: body.lumps.count, errors)
        row['body_getter_errors'] = errors
        return row

    def brep_collection(collection):
        if collection is None:
            return None
        bodies = items(collection)
        return {'count': len(bodies), 'bodies': [brep_body(b) for b in bodies]}

    def input_truth(inp):
        row, errors = identity(inp), []
        for prop in ('meshConvertMethodType', 'meshConvertOperationType'):
            row[prop] = observe(prop, lambda prop=prop: int(getattr(inp, prop)), errors)
        row['inputBodies'] = observe('inputBodies', lambda: [identity(b) for b in items(inp.inputBodies)], errors)
        row['targetBaseFeature'] = observe('targetBaseFeature', lambda: identity(inp.targetBaseFeature), errors)
        row['inactive_controls_scope'] = 'Faceted only: resolution/accuracy/numberOfFaces/preprocess getters and setters not called'
        row['input_getter_errors'] = errors
        return row

    def feature_truth(feature):
        if feature is None:
            return None
        row, errors = identity(feature), []
        for prop in ('meshConvertMethodType', 'healthState', 'errorOrWarningMessage', 'isParametric', 'isSuppressed'):
            row[prop] = observe(prop, lambda prop=prop: int(getattr(feature, prop)) if prop in ('meshConvertMethodType', 'meshConvertResolutionType', 'meshConvertAccuracyType', 'healthState') else getattr(feature, prop), errors)
        row['inputBodies'] = observe('inputBodies', lambda: [identity(b) for b in items(feature.inputBodies)], errors)
        row['baseFeature'] = observe('baseFeature', lambda: identity(feature.baseFeature), errors)
        row['parentComponent'] = observe('parentComponent', lambda: identity(feature.parentComponent), errors)
        row['brep_bodies'] = observe('bodies', lambda: brep_collection(feature.bodies), errors)
        row['face_count'] = observe('faces', lambda: None if feature.faces is None else feature.faces.count, errors)
        row['timeline_index'] = observe('timelineObject.index', lambda: feature.timelineObject.index, errors)
        row['feature_getter_errors'] = errors
        return row

    def returned_truth(entity):
        if entity is None:
            return None
        if adsk.fusion.MeshConvertFeature.cast(entity) is not None:
            return {'actual_type_branch': 'MeshConvertFeature', 'snapshot': feature_truth(entity)}
        if adsk.fusion.BaseFeature.cast(entity) is not None:
            return {'actual_type_branch': 'BaseFeature', 'snapshot': base_truth(entity)}
        return {'actual_type_branch': 'OtherReturnedType', 'snapshot': identity(entity)}

    def history_truth(design, root):
        row, errors = {}, []
        row['timeline_count'] = observe('timeline.count', lambda: design.timeline.count, errors)
        row['timeline_marker_position'] = observe('timeline.markerPosition', lambda: design.timeline.markerPosition, errors)
        row['base_features'] = observe('baseFeatures', lambda: [base_truth(b) for b in items(root.features.baseFeatures)], errors)
        row['convert_features'] = observe('meshConvertFeatures', lambda: [feature_truth(f) for f in items(root.features.meshConvertFeatures)], errors)
        timeline = []
        for i in range(design.timeline.count):
            entry, entry_errors = {}, []
            item = design.timeline.item(i)
            for prop in ('index', 'isGroup', 'isSuppressed'):
                entry[prop] = observe('timeline.'+prop, lambda prop=prop: getattr(item, prop), entry_errors)
            entry['entity'] = observe('timeline.entity', lambda: identity(item.entity), entry_errors)
            entry['getter_errors'] = entry_errors
            timeline.append(entry)
        row['timeline_entries'] = timeline
        row['getter_errors'] = errors
        return row

    journal('batch_begin', output_directory=str(output), planned_sample_count=len(cases))
    for case, (operation_name, is_open, input_count) in cases.items():
        method_name = 'FacetedMeshConvertMethodType'
        doc, design, base, editing = None, None, None, False
        selected_stl = open_path if is_open else stl_path
        sample = {'case': case, 'file': case+'.f3d', 'phase': 'document_create', 'getter_errors': [],
            'requested': {'meshConvertMethodType': method_name, 'meshConvertOperationType': operation_name, 'input_count': input_count,
                'source_file': selected_stl.name, 'source_files': [selected_stl.name]+([second_path.name] if input_count == 2 else []), 'source_triangle_count': 3 if is_open else 4, 'source_closed': not is_open,
                'targetBaseFeature_set': False}}
        truth['active_sample'] = sample
        try:
            journal('owned_document_create_begin', case)
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            journal('owned_document_created', case)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            if design is None:
                raise RuntimeError('Owned document has no Fusion Design product')
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sample['root_component'] = identity(root)
            sample['component_meshes_before_import'] = component_meshes(root)
            sample['component_brep_before_import'] = brep_collection(root.bRepBodies)
            base = root.features.baseFeatures.add()
            base.name = 'Owned tetra import '+case
            started = base.startEdit(); sample['base_start_edit_returned'] = bool(started)
            if not started:
                raise RuntimeError('BaseFeature.startEdit returned false')
            editing = True
            sample['phase'] = 'owned_mesh_import'
            imported = root.meshBodies.add(str(selected_stl), adsk.fusion.MeshUnits.CentimeterMeshUnit, base)
            if imported is None or imported.count != 1:
                raise RuntimeError('Owned STL did not import exactly one mesh')
            mesh = imported.item(0); mesh.name = 'OwnedTetraSource_'+case
            selected_meshes = [mesh]
            if input_count == 2:
                second_import = root.meshBodies.add(str(second_path), adsk.fusion.MeshUnits.CentimeterMeshUnit, base)
                if second_import is None or second_import.count != 1:
                    raise RuntimeError('Second owned STL did not import exactly one mesh')
                second_mesh = second_import.item(0)
                second_mesh.name = 'OwnedTetraSecond_'+case
                selected_meshes.append(second_mesh)
            sample['source_meshes_during_edit'] = [mesh_body(b) for b in selected_meshes]
            sample['base_during_edit'] = base_truth(base)
            sample['source_during_edit'] = mesh_body(mesh)
            finished = base.finishEdit(); sample['base_finish_edit_returned'] = bool(finished)
            if not finished:
                raise RuntimeError('BaseFeature.finishEdit returned false')
            editing = False
            design.timeline.moveToEnd()
            sample['base_after_edit'] = base_truth(base)
            sample['component_meshes_before_convert'] = component_meshes(root)
            sample['source_before_convert'] = mesh_body(mesh)
            sample['selected_meshes_before_convert'] = [mesh_body(b) for b in selected_meshes]
            sample['history_before_convert'] = history_truth(design, root)
            sample['component_brep_before_convert'] = brep_collection(root.bRepBodies)
            feature = None
            sample['phase'] = 'mesh_convert_attempt'
            try:
                collection = root.features.meshConvertFeatures
                sample['convert_collection_count_before'] = collection.count
                inp = collection.createInput(selected_meshes)
                if inp is None:
                    raise RuntimeError('MeshConvert createInput returned null')
                sample['input_defaults'] = input_truth(inp)
                inp.meshConvertMethodType = getattr(adsk.fusion.MeshConvertMethodTypes, method_name)
                inp.meshConvertOperationType = getattr(adsk.fusion.MeshConvertOperationTypes, operation_name)
                sample['input_before_add'] = input_truth(inp)
                sample['input_body_equals_import_handles'] = observe('inputBodies == selected handles', lambda: len(items(inp.inputBodies)) == input_count and all(a == b for a,b in zip(items(inp.inputBodies),selected_meshes)), sample['getter_errors'])
                journal('mesh_convert_add_begin', case)
                feature = collection.add(inp)
                sample['add_returned_nonnull'] = feature is not None
                sample['actual_returned_identity'] = identity(feature)
                sample['convert_status'] = ('ObjectReturned' if feature is not None else
                    'NullReturnedNonParametricOperation' if operation_name == 'BaseFeatureMeshConvertOperationType' else 'NullReturnedParametricOperation')
                sample['add_return_scope'] = ('Null is documented for non-parametric conversion; actual independent document changes remain separate'
                    if operation_name == 'BaseFeatureMeshConvertOperationType' else
                    'Parametric operation: actual null is retained separately from documented non-parametric null; no invented conversion success')
                if feature is not None and hasattr(type(feature), 'name'):
                    feature.name = 'Owned Mesh Convert Operation '+case
                journal('mesh_convert_add_returned', case, actual_returned_type=None if feature is None else feature.objectType)
            except Exception:
                sample['convert_status'] = 'AttemptError'
                error = {'case': case, 'phase': 'mesh_convert_attempt', 'error': traceback.format_exc(),
                    'policy': 'Preserve actual current source/mesh/BRep state and export; no conversion success inferred from feature name'}
                sample['convert_error'] = error
                truth['errors'].append(error)
                journal('mesh_convert_attempt_error', case)
            design.timeline.moveToEnd()
            sample['compute_all_returned'] = bool(design.computeAll())
            sample['component_meshes_after_convert'] = component_meshes(root)
            sample['component_brep_after_convert'] = observe('root.bRepBodies', lambda: brep_collection(root.bRepBodies), sample['getter_errors'])
            sample['original_mesh_handles_after_convert'] = [observe('source handle '+str(i)+' after convert', lambda body=body: mesh_body(body), sample['getter_errors']) for i,body in enumerate(selected_meshes)]
            sample['returned_at_timeline_end'] = returned_truth(feature)
            sample['history_after_convert'] = history_truth(design, root)
            sample['base_after_convert'] = base_truth(base)
            sample['parameters_after_convert'] = observe('design.allParameters', lambda: [parameter_truth(p) for p in items(design.allParameters)], sample['getter_errors'])
            if feature is not None and (adsk.fusion.MeshConvertFeature.cast(feature) is not None or adsk.fusion.BaseFeature.cast(feature) is not None):
                try:
                    rolled = feature.timelineObject.rollTo(True)
                    sample['roll_before_feature_returned'] = bool(rolled)
                    if rolled:
                        sample['returned_before_node'] = returned_truth(feature)
                        sample['component_meshes_before_node'] = component_meshes(root)
                        sample['component_brep_before_node'] = observe('root.bRepBodies before node', lambda: brep_collection(root.bRepBodies), sample['getter_errors'])
                except Exception:
                    sample['getter_errors'].append({'getter': 'roll/snapshot before owned MeshConvert node', 'error': traceback.format_exc()})
                finally:
                    design.timeline.moveToEnd()
            sample['convert_collection_count_after'] = observe('convert count after', lambda: root.features.meshConvertFeatures.count, sample['getter_errors'])
            sample['timeline_count'] = design.timeline.count
            sample['timeline_marker_position'] = design.timeline.markerPosition
            sample['phase'] = 'local_export'
            journal('local_export_begin', case, file=sample['file'])
            destination = output/sample['file']
            succeeded = design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(destination)))
            if not succeeded or not destination.is_file() or destination.stat().st_size == 0:
                raise RuntimeError('Local owned archive export did not complete')
            sample['export'] = {'returned_success': bool(succeeded), 'size_bytes': destination.stat().st_size,
                'sha256': hashlib.sha256(destination.read_bytes()).hexdigest()}
            sample['phase'] = 'export_complete'
            truth['samples'].append(sample); truth.pop('active_sample', None)
            journal('local_export_complete', case, file=sample['file'])
        except Exception:
            truth['errors'].append({'case': case, 'phase': sample['phase'], 'error': traceback.format_exc(), 'partial_sample': sample})
            truth.pop('active_sample', None)
            journal('case_error', case)
        finally:
            if editing and base is not None:
                try:
                    returned = base.finishEdit()
                    journal('cleanup_base_finish_edit_returned', case, returned=bool(returned))
                    if not returned:
                        truth['errors'].append({'case': case, 'phase': 'cleanup_base_edit', 'error': 'finishEdit returned false'})
                except Exception:
                    truth['errors'].append({'case': case, 'phase': 'cleanup_base_edit', 'error': traceback.format_exc()})
            if design is not None:
                try:
                    design.timeline.moveToEnd()
                except Exception:
                    truth['errors'].append({'case': case, 'phase': 'restore_owned_timeline', 'error': traceback.format_exc()})
            if doc is not None:
                try:
                    journal('owned_document_close_begin', case, save=False)
                    closed = doc.close(False)
                    sample['close_owned_document_returned'] = bool(closed)
                    journal('owned_document_close_returned', case, returned=bool(closed), save=False)
                    if not closed:
                        truth['errors'].append({'case': case, 'phase': 'close_owned_document', 'error': 'close(False) returned false'})
                except Exception:
                    truth['errors'].append({'case': case, 'phase': 'close_owned_document', 'error': traceback.format_exc()})
            persist()
    journal('batch_complete', planned_sample_count=len(cases), exported_sample_count=len(truth['samples']))
    (output/'complete.txt').write_text('terminal; inspect actual Convert status/errors, mesh arrays and independent BRep topology in ground_truth.json\n')
