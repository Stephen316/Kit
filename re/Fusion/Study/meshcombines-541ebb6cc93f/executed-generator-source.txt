"""Three owned MeshCombine captures through active executable preview bindings.

All helpers are self-contained and snapshotted. Import two explicit-centimetre
STLs in one owned BaseFeature, finish edit, then attempt one mesh Boolean. No
existing document, UI command, geometry-to-native identity or live self-run.
"""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

VERTICES = ((0., 0., 0.), (2., 0., 0.), (0., 3., 0.), (0., 0., 4.))
TRIANGLES = ((0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3))
CASES = {'join': 'JoinMeshCombineType', 'cut': 'CutMeshCombineType',
         'intersect': 'IntersectMeshCombineType'}


def _stl(vertices, name):
    lines, normals = ['solid '+name], []
    for indices in TRIANGLES:
        a, b, c = [vertices[i] for i in indices]
        u, v = [b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)]
        cross = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
        norm = math.sqrt(sum(x*x for x in cross))
        if not norm:
            raise ValueError('Degenerate owned tetrahedron facet')
        normal = [x/norm for x in cross]
        normals.append(normal)
        lines += ['  facet normal '+' '.join(format(x, '.17g') for x in normal), '    outer loop']
        lines += ['      vertex '+' '.join(format(x, '.17g') for x in vertex) for vertex in (a, b, c)]
        lines += ['    endloop', '  endfacet']
    return '\n'.join(lines+['endsolid '+name, '']), normals


def run(context):
    app = adsk.core.Application.get()
    cases = CASES
    if isinstance(context, dict) and 'cases' in context:
        selected = context['cases']
        if (not isinstance(selected, (list, tuple)) or not selected
                or len(set(selected)) != len(selected) or set(selected)-set(CASES)):
            raise ValueError('Select one to three distinct known MeshCombine cases')
        cases = {name: spec for name, spec in CASES.items() if name in selected}
    source = Path(__file__).resolve()
    output = source.parent/('meshcombines-'+uuid.uuid4().hex[:12])
    output.mkdir()
    executed = source.read_bytes()
    source_hash = hashlib.sha256(executed).hexdigest()
    (output/'executed-generator-source.txt').write_bytes(executed)
    sdk_path = Path(adsk.fusion.__file__).resolve()
    if sdk_path.suffix == '.pyc' and sdk_path.with_suffix('.py').is_file():
        sdk_path = sdk_path.with_suffix('.py')
    sources = {}
    for role, vertices in (('target', VERTICES),
            ('tool', tuple((p[0]+.5, p[1], p[2]) for p in VERTICES))):
        text, normals = _stl(vertices, 'owned_'+role+'_tetra')
        path = output/('owned-'+role+'-tetra.stl')
        path.write_text(text, encoding='ascii')
        sources[role] = dict(file=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            numeric_vertices=vertices, triangle_vertex_indices=TRIANGLES, facet_normals=normals,
            numeric_units='CentimeterMeshUnit', source_volume_cm3=4.,
            source_offset_cm=[.5, 0., 0.] if role == 'tool' else [0., 0., 0.])
    truth = dict(fusion_version=app.version, samples=[], errors=[], planned_cases=list(cases),
        executed_generator_sha256=source_hash, mesh_source_helper_sha256=source_hash,
        helper_scope='All STL, identity, mesh-array and readback helpers are in executed-generator-source.txt; helper hash is the complete executed self-contained source, not an external dependency',
        sdk_runtime_module=str(sdk_path), sdk_runtime_source_sha256=hashlib.sha256(sdk_path.read_bytes()).hexdigest(),
        sdk_operation_enum_values={n: int(getattr(adsk.fusion.MeshCombineOperationTypes, n)) for n in
            ('JoinMeshCombineType', 'CutMeshCombineType', 'IntersectMeshCombineType', 'MergeMeshCombineType')},
        sdk_algorithm_enum_values={n: int(getattr(adsk.fusion.MeshCombineAlgorithmTypes, n)) for n in
            ('LegacyMeshCombineAlgorithmType', 'EnhancedMeshCombineAlgorithmType')},
        sdk_scope='Active executable preview MeshCombineFeatures.createInput(targetBody,list[MeshBody])/add; documented input and rolled-feature target/tool/operation/algorithm/flags only',
        source_meshes=sources,
        algorithm_scope='Read actual default algorithm, explicitly request documented LegacyMeshCombineAlgorithmType, then capture actual input and rolled feature readbacks; Enhanced is inventoried but not exercised',
        identity_scope='Input roles come from actual targetBody/toolBodies getters and direct same-object equality. Tokens are opaque, array positions do not identify native records, and component meshes are not automatically feature-owned results.',
        geometry_scope='Exact pre-add arrays and independent current/before-node collections are captured. Analytic overlap/volume is corroboration only after separately proved typed provenance; no native identity chosen from coordinates.',
        analytic_reference_only=dict(source_volume_cm3=4., overlap_volume_cm3=1.6875,
            ideal_join_volume_cm3=6.3125, ideal_cut_volume_cm3=2.3125,
            ideal_intersect_volume_cm3=1.6875,
            scope='Two exact outward tetras offset+.5X; optional later corroboration, never assumed algorithm output or native topology identity'))

    def persist():
        (output/'ground_truth.json').write_text(json.dumps(truth, indent=2)+'\n')

    def journal(phase, case=None, **fields):
        event = dict(time_utc=datetime.now(timezone.utc).isoformat(), phase=phase, case=case,
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
        row['bounding_box_cm'] = observe('boundingBox', lambda: dict(
            min=body.boundingBox.minPoint.asArray(), max=body.boundingBox.maxPoint.asArray()), errors)
        for prop in ('baseOrFormFeature', 'parentComponent', 'assemblyContext', 'nativeObject'):
            row[prop] = observe(prop, lambda prop=prop: identity(getattr(body, prop)), errors)
        row['original_polygon_mesh'] = observe('mesh', lambda: mesh_array(body.mesh), errors)
        row['display_triangle_mesh'] = observe('displayMesh', lambda: mesh_array(body.displayMesh, True), errors)
        row['mesh_getter_errors'] = errors
        return row

    def component_meshes(root):
        errors = []
        bodies = observe('root.meshBodies', lambda: items(root.meshBodies), errors)
        return dict(count=len(bodies) if bodies is not None else None,
            meshes=[mesh_body(body) for body in bodies] if bodies is not None else None,
            getter_errors=errors)

    def parameter(value):
        if value is None:
            return None
        row, errors = identity(value), []
        for prop in ('name', 'role', 'value', 'unit', 'expression'):
            row[prop] = observe(prop, lambda prop=prop: getattr(value, prop), errors)
        row['createdBy'] = observe('createdBy', lambda: identity(value.createdBy), errors)
        row['parameter_getter_errors'] = errors
        return row

    def controls(entity, include_meshes=False, is_input=False):
        row, errors = identity(entity), []
        for prop in ('meshCombineOperationType', 'algorithmType'):
            row[prop] = observe(prop, lambda prop=prop: int(getattr(entity, prop)), errors)
        for prop in ('isKeepToolBodies', 'isNewComponent'):
            row[prop] = observe(prop, lambda prop=prop: bool(getattr(entity, prop)), errors)
        if is_input:
            row['targetBaseFeature'] = observe('targetBaseFeature', lambda: identity(entity.targetBaseFeature), errors)
        if include_meshes:
            row['targetBody'] = observe('targetBody', lambda: mesh_body(entity.targetBody), errors)
            row['toolBodies'] = observe('toolBodies', lambda: [mesh_body(b) for b in items(entity.toolBodies)], errors)
            row['tool_order_scope'] = 'Actual API list order retained; not an assumed native selection or asset order'
        row['control_getter_errors'] = errors
        return row

    def feature_truth(feature, include_meshes=False):
        if feature is None:
            return None
        row, errors = controls(feature, include_meshes), []
        for prop in ('healthState', 'errorOrWarningMessage', 'isParametric', 'isSuppressed'):
            row[prop] = observe(prop, lambda prop=prop: int(getattr(feature, prop)) if prop == 'healthState' else getattr(feature, prop), errors)
        for prop in ('parentComponent', 'baseFeature'):
            row[prop] = observe(prop, lambda prop=prop: identity(getattr(feature, prop)), errors)
        row['timeline_index'] = observe('timelineObject.index', lambda: feature.timelineObject.index, errors)
        for prop in ('bodies', 'faces'):
            row['brep_'+prop] = observe(prop, lambda prop=prop: None if getattr(feature, prop) is None
                else [identity(b) for b in items(getattr(feature, prop))], errors)
        row['brep_scope'] = 'Inherited BRep collections are recorded literally; they do not identify mesh output ownership'
        row['feature_getter_errors'] = errors
        return row

    def base_truth(base):
        row, errors = identity(base), []
        for prop in ('healthState', 'errorOrWarningMessage', 'isParametric'):
            row[prop] = observe(prop, lambda prop=prop: int(getattr(base, prop)) if prop == 'healthState' else getattr(base, prop), errors)
        row['mesh_bodies'] = observe('meshBodies', lambda: [mesh_body(b) for b in items(base.meshBodies)], errors)
        row['timeline_index'] = observe('timelineObject.index', lambda: base.timelineObject.index, errors)
        row['base_getter_errors'] = errors
        return row

    journal('batch_begin', output_directory=str(output))
    for case, operation_name in cases.items():
        doc = design = base = None
        editing = False
        sample = dict(case=case, file=case+'.f3d', getter_errors=[], setter_errors=[],
            phase='document_create', requested=dict(operation=operation_name,
                algorithm='LegacyMeshCombineAlgorithmType', keep_tool_bodies=False,
                new_component=False, targetBaseFeature_set=False))
        truth['active_sample'] = sample
        try:
            journal('owned_document_create_begin', case)
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            if design is None:
                raise RuntimeError('Owned document has no Fusion Design')
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sample['root_component'] = identity(root)
            sample['component_meshes_before_import'] = component_meshes(root)
            base = root.features.baseFeatures.add()
            base.name = 'Owned tetra pair import '+case
            sample['base_start_edit_returned'] = bool(base.startEdit())
            if not sample['base_start_edit_returned']:
                raise RuntimeError('Owned BaseFeature.startEdit returned false')
            editing = True
            sample['phase'] = 'owned_pair_import'
            handles = {}
            for role in ('target', 'tool'):
                imported = root.meshBodies.add(str(output/sources[role]['file']), adsk.fusion.MeshUnits.CentimeterMeshUnit, base)
                if imported is None or imported.count != 1:
                    raise RuntimeError('Owned '+role+' STL did not import exactly one MeshBody')
                mesh = imported.item(0)
                mesh.name = 'OwnedCombine'+role.title()+'_'+case
                handles[role] = mesh
            target, tool = handles['target'], handles['tool']
            sample['sources_during_edit'] = {role: mesh_body(mesh) for role, mesh in handles.items()}
            sample['base_finish_edit_returned'] = bool(base.finishEdit())
            if not sample['base_finish_edit_returned']:
                raise RuntimeError('Owned BaseFeature.finishEdit returned false')
            editing = False
            design.timeline.moveToEnd()
            sample['base_after_edit'] = base_truth(base)
            sample['sources_before_combine'] = {role: mesh_body(mesh) for role, mesh in handles.items()}
            sample['component_meshes_before_combine'] = component_meshes(root)
            sample['model_parameters_before'] = observe('modelParameters before',
                lambda: [parameter(p) for p in root.modelParameters], sample['getter_errors'])
            feature = None
            sample['phase'] = 'mesh_combine_attempt'
            try:
                collection = root.features.meshCombineFeatures
                sample['combine_collection_count_before'] = collection.count
                inputs = collection.createInput(target, [tool])
                if inputs is None:
                    raise RuntimeError('MeshCombine createInput returned null')
                sample['input_defaults'] = controls(inputs, True, True)
                operation = getattr(adsk.fusion.MeshCombineOperationTypes, operation_name)
                algorithm = adsk.fusion.MeshCombineAlgorithmTypes.LegacyMeshCombineAlgorithmType
                sample['requested'].update(operation_enum=int(operation), algorithm_enum=int(algorithm))
                for prop, value in (('meshCombineOperationType', operation), ('algorithmType', algorithm),
                        ('isKeepToolBodies', False), ('isNewComponent', False)):
                    try:
                        setattr(inputs, prop, value)
                    except Exception:
                        sample['setter_errors'].append(dict(property=prop, error=traceback.format_exc()))
                        raise
                sample['input_before_add'] = controls(inputs, True, True)
                sample['input_target_equals_import_handle'] = observe('input.targetBody == target',
                    lambda: inputs.targetBody == target, sample['getter_errors'])
                sample['input_tools_equal_import_handles'] = observe('input.toolBodies == [tool]',
                    lambda: [body == tool for body in inputs.toolBodies], sample['getter_errors'])
                journal('mesh_combine_add_begin', case)
                feature = collection.add(inputs)
                sample['add_returned_feature'] = feature is not None
                if feature is None:
                    raise RuntimeError('Parametric MeshCombine add returned null; current source meshes still exported')
                feature.name = 'OwnedMeshCombine_'+case
                sample['combine_status'] = 'FeatureReturned'
                journal('mesh_combine_feature_returned', case)
            except Exception:
                sample['combine_status'] = 'AttemptError'
                failure = dict(case=case, phase='mesh_combine_attempt', error=traceback.format_exc(),
                    policy='Preserve/export actual source/current mesh, no successful native feature or output assumed')
                sample['combine_error'] = failure
                truth['errors'].append(failure)
                journal('mesh_combine_attempt_error', case)
            design.timeline.moveToEnd()
            sample['compute_all_returned'] = observe('design.computeAll', lambda: design.computeAll(), sample['getter_errors'])
            sample['component_meshes_after_combine'] = component_meshes(root)
            sample['original_handles_after_combine'] = {role: observe('original '+role+' handle',
                lambda mesh=mesh: mesh_body(mesh), sample['getter_errors']) for role, mesh in handles.items()}
            sample['feature_at_timeline_end'] = feature_truth(feature)
            sample['base_after_combine'] = base_truth(base)
            sample['model_parameters_after'] = observe('modelParameters after',
                lambda: [parameter(p) for p in root.modelParameters], sample['getter_errors'])
            if feature is not None:
                try:
                    rolled = feature.timelineObject.rollTo(True)
                    sample['roll_before_feature_returned'] = bool(rolled)
                    if rolled:
                        sample['feature_before_node'] = feature_truth(feature, True)
                        sample['component_meshes_before_node'] = component_meshes(root)
                        sample['rolled_target_equals_import_handle'] = observe('feature.targetBody == target before node',
                            lambda: feature.targetBody == target, sample['getter_errors'])
                        sample['rolled_tools_equal_import_handles'] = observe('feature.toolBodies == [tool] before node',
                            lambda: [body == tool for body in feature.toolBodies], sample['getter_errors'])
                except Exception:
                    sample['getter_errors'].append(dict(getter='rolled MeshCombine snapshot', error=traceback.format_exc()))
                finally:
                    design.timeline.moveToEnd()
            sample['combine_collection_count_after'] = observe('combineFeatures count after',
                lambda: root.features.meshCombineFeatures.count, sample['getter_errors'])
            sample['timeline_count'] = design.timeline.count
            sample['timeline_marker_position'] = design.timeline.markerPosition
            sample['phase'] = 'local_export'
            journal('local_export_begin', case)
            destination = output/sample['file']
            succeeded = design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(destination)))
            if not succeeded or not destination.is_file() or not destination.stat().st_size:
                raise RuntimeError('Local owned MeshCombine archive export failed')
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
                    closed = doc.close(False)
                    sample['close_owned_document_returned'] = bool(closed)
                    journal('owned_document_close_returned', case, save=False, returned=bool(closed))
                    if not closed:
                        truth['errors'].append(dict(case=case, phase='close_owned_document', error='close(False) returned false'))
                except Exception:
                    truth['errors'].append(dict(case=case, phase='close_owned_document', error=traceback.format_exc()))
            truth.pop('active_sample', None)
            persist()
    truth['terminal_status'] = 'complete' if len(truth['samples']) == len(cases) and not truth['errors'] else 'complete_with_errors'
    truth['exported_sample_count'] = len(truth['samples'])
    journal('batch_terminal')
    (output/'complete.txt').write_text('MeshCombine terminal: '+truth['terminal_status']+'; inspect actual arrays, controls and errors.\n')
