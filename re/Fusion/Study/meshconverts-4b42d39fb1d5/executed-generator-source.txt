"""Three bounded owned MeshConvert probes; root dispatches serially.

Faceted/Prismatic closed tetra and Faceted open three-triangle tetra. Active
executable SDK only; Organic-only values are retained as inactive getter truth.
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
    'faceted_closed': ('FacetedMeshConvertMethodType', False),
    'prismatic_closed': ('PrismaticMeshConvertMethodType', False),
    'faceted_open': ('FacetedMeshConvertMethodType', True),
}


def run(context):
    app = adsk.core.Application.get()
    cases = CASES
    if isinstance(context, dict) and 'cases' in context:
        selected = context['cases']
        if not isinstance(selected, (list, tuple)) or not selected or len(set(selected)) != len(selected) or set(selected)-set(CASES):
            raise ValueError('Select one to three distinct known MeshConvert cases')
        cases = {name: spec for name, spec in CASES.items() if name in selected}
    source = Path(__file__).resolve()
    # Python.RunScript need not add this study directory to sys.path. Loading
    # the owned sibling by absolute path runs definitions only, not its run().
    helper_source = source.with_name('GenerateMeshContrasts.py')
    helper = runpy.run_path(str(helper_source))
    vertices, triangles = helper['VERTICES'], helper['TRIANGLES']
    output = source.parent/('meshconverts-'+uuid.uuid4().hex[:12])
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
        'scope': 'Three newly owned parametric documents, local closed/open tetra STL imports through BaseFeature edit/finish, Convert outside edit, actual input and feature getters, mesh and BRep collections recorded separately.',
        'controls_scope': 'Closed Faceted vs closed Prismatic; closed vs open Faceted. Explicit ParametricFeature operation in all cases. No conversion success inferred from feature name or health alone.',
        'identity_scope': 'Tokens are opaque getter snapshots, never decoded as native IDs or compared for identity. Actual source mesh arrays captured before Convert; BRep bodies/topology and current mesh collection captured independently.',
        'inactive_controls_scope': 'Resolution/accuracy/numberOfFaces/preprocess are Organic-only controls; actual getter values/errors retained without an active-settings claim.',
        'operation_scope': 'Operation type exists on MeshConvertFeatureInput only; actual input defaults and explicit ParametricFeature setting are captured. Feature has no operation getter; isParametric is observed separately.'}


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
        for prop in ('healthState', 'errorOrWarningMessage', 'isParametric'):
            row[prop] = observe(prop, lambda prop=prop: int(getattr(base, prop)) if prop == 'healthState' else getattr(base, prop), errors)
        row['mesh_bodies'] = observe('meshBodies', lambda: [mesh_body(b) for b in items(base.meshBodies)], errors)
        row['brep_source_bodies'] = observe('sourceBodies', lambda: [identity(b) for b in items(base.sourceBodies)], errors)
        row['brep_bodies'] = observe('bodies', lambda: [identity(b) for b in items(base.bodies)], errors)
        row['collection_scope'] = 'BRep sourceBodies/bodies are not mesh source/result collections'
        row['base_getter_errors'] = errors
        return row

    def parameter_truth(parameter):
        if parameter is None:
            return None
        errors, row = [], {}
        for prop in ('objectType', 'name', 'expression', 'unit', 'value', 'valueType'):
            row[prop] = observe(prop, lambda prop=prop: int(parameter.valueType) if prop == 'valueType' else getattr(parameter, prop), errors)
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
        for prop in ('meshConvertMethodType', 'meshConvertOperationType', 'meshConvertResolutionType', 'meshConvertAccuracyType', 'isPreprocessHoles'):
            row[prop] = observe(prop, lambda prop=prop: bool(getattr(inp, prop)) if prop == 'isPreprocessHoles' else int(getattr(inp, prop)), errors)
        row['inputBodies'] = observe('inputBodies', lambda: [identity(b) for b in items(inp.inputBodies)], errors)
        row['targetBaseFeature'] = observe('targetBaseFeature', lambda: identity(inp.targetBaseFeature), errors)
        row['numberOfFaces'] = observe('numberOfFaces', lambda: value_input_truth(inp.numberOfFaces), errors)
        row['inactive_controls_scope'] = 'Only method/operation/inputBodies active for this Faceted/Prismatic probe'
        row['input_getter_errors'] = errors
        return row

    def feature_truth(feature):
        if feature is None:
            return None
        row, errors = identity(feature), []
        for prop in ('meshConvertMethodType', 'meshConvertResolutionType', 'meshConvertAccuracyType', 'isPreprocessHoles', 'healthState', 'errorOrWarningMessage', 'isParametric', 'isSuppressed'):
            row[prop] = observe(prop, lambda prop=prop: int(getattr(feature, prop)) if prop in ('meshConvertMethodType', 'meshConvertResolutionType', 'meshConvertAccuracyType', 'healthState') else getattr(feature, prop), errors)
        row['inputBodies'] = observe('inputBodies', lambda: [identity(b) for b in items(feature.inputBodies)], errors)
        row['baseFeature'] = observe('baseFeature', lambda: identity(feature.baseFeature), errors)
        row['parentComponent'] = observe('parentComponent', lambda: identity(feature.parentComponent), errors)
        row['numberOfFaces'] = observe('numberOfFaces', lambda: parameter_truth(feature.numberOfFaces), errors)
        row['brep_bodies'] = observe('bodies', lambda: brep_collection(feature.bodies), errors)
        row['face_count'] = observe('faces', lambda: None if feature.faces is None else feature.faces.count, errors)
        row['feature_getter_errors'] = errors
        return row

    journal('batch_begin', output_directory=str(output), planned_sample_count=len(cases))
    for case, (method_name, is_open) in cases.items():
        doc, design, base, editing = None, None, None, False
        selected_stl = open_path if is_open else stl_path
        sample = {'case': case, 'file': case+'.f3d', 'phase': 'document_create', 'getter_errors': [],
            'requested': {'meshConvertMethodType': method_name, 'meshConvertOperationType': 'ParametricFeatureMeshConvertOperationType',
                'source_file': selected_stl.name, 'source_triangle_count': 3 if is_open else 4, 'source_closed': not is_open,
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
            sample['component_brep_before_convert'] = brep_collection(root.bRepBodies)
            feature = None
            sample['phase'] = 'mesh_convert_attempt'
            try:
                collection = root.features.meshConvertFeatures
                sample['convert_collection_count_before'] = collection.count
                inp = collection.createInput([mesh])
                if inp is None:
                    raise RuntimeError('MeshConvert createInput returned null')
                sample['input_defaults'] = input_truth(inp)
                inp.meshConvertMethodType = getattr(adsk.fusion.MeshConvertMethodTypes, method_name)
                inp.meshConvertOperationType = adsk.fusion.MeshConvertOperationTypes.ParametricFeatureMeshConvertOperationType
                sample['input_before_add'] = input_truth(inp)
                sample['input_body_equals_import_handle'] = observe('inputBodies[0] == source', lambda: len(items(inp.inputBodies)) == 1 and items(inp.inputBodies)[0] == mesh, sample['getter_errors'])
                journal('mesh_convert_add_begin', case)
                feature = collection.add(inp)
                sample['add_returned_feature'] = feature is not None
                if feature is None:
                    raise RuntimeError('Explicit parametric MeshConvert add returned null; actual current mesh/BRep state still captured and exported')
                feature.name = 'Owned Mesh Convert '+case
                sample['convert_status'] = 'FeatureReturned'
                journal('mesh_convert_feature_returned', case)
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
            sample['original_mesh_handle_after_convert'] = observe('source handle after convert', lambda: mesh_body(mesh), sample['getter_errors'])
            sample['feature_at_timeline_end'] = feature_truth(feature)
            sample['base_after_convert'] = base_truth(base)
            sample['parameters_after_convert'] = observe('design.allParameters', lambda: [parameter_truth(p) for p in items(design.allParameters)], sample['getter_errors'])
            if feature is not None:
                try:
                    rolled = feature.timelineObject.rollTo(True)
                    sample['roll_before_feature_returned'] = bool(rolled)
                    if rolled:
                        sample['feature_before_node'] = feature_truth(feature)
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
                    journal('owned_document_close_returned', case, returned=bool(closed), save=False)
                    if not closed:
                        truth['errors'].append({'case': case, 'phase': 'close_owned_document', 'error': 'close(False) returned false'})
                except Exception:
                    truth['errors'].append({'case': case, 'phase': 'close_owned_document', 'error': traceback.format_exc()})
            persist()
    journal('batch_complete', planned_sample_count=len(cases), exported_sample_count=len(truth['samples']))
    (output/'complete.txt').write_text('terminal; inspect actual Convert status/errors, mesh arrays and independent BRep topology in ground_truth.json\n')
