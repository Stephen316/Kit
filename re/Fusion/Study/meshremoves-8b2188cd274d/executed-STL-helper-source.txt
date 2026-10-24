"""Owned preview MeshSeparate probes; dispatch only through run().

Two disconnected tetrahedra are written into ONE STL solid. Import count and
actual API face groups decide whether one MeshBody was obtained. No existing
document, UI call, mesh merging fallback or assumed output count is used.
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
CASES = {'two_shells': ('disconnected', 'ShellMeshSeparateType'),
    'two_face_groups': ('disconnected', 'FaceGroupMeshSeparateType'),
    'connected_shell_control': ('connected', 'ShellMeshSeparateType')}


def _source_data(disconnected):
    vertices = list(VERTICES)
    triangles = list(TRIANGLES)
    if disconnected:
        vertices += [(p[0]+4., p[1], p[2]) for p in VERTICES]
        triangles += [tuple(i+4 for i in tri) for tri in TRIANGLES]
    return vertices, triangles


def _stl(vertices, triangles, name):
    lines, normals = ['solid '+name], []
    for tri in triangles:
        a, b, c = [vertices[i] for i in tri]
        u, v = [b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)]
        n = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
        length = math.sqrt(sum(x*x for x in n))
        if not length:
            raise ValueError('Degenerate owned tetrahedron facet')
        normal = [x/length for x in n]
        normals.append(normal)
        lines += ['  facet normal '+' '.join(format(x, '.17g') for x in normal), '    outer loop']
        lines += ['      vertex '+' '.join(format(x, '.17g') for x in point) for point in (a, b, c)]
        lines += ['    endloop', '  endfacet']
    return '\n'.join(lines+['endsolid '+name, '']), normals


def run(context):
    app = adsk.core.Application.get()
    cases = CASES
    if isinstance(context, dict) and 'cases' in context:
        requested = context['cases']
        if (not isinstance(requested, (list, tuple)) or not requested
                or len(set(requested)) != len(requested) or set(requested)-set(CASES)):
            raise ValueError('Select one to three distinct known MeshSeparate cases')
        cases = {name: value for name, value in CASES.items() if name in requested}
    source = Path(__file__).resolve()
    output = source.parent/('meshseparates-'+uuid.uuid4().hex[:12])
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
    for name in ('MeshSeparateTypes', 'MeshSeparateFeatureInput', 'MeshSeparateFeatures', 'MeshSeparateFeature'):
        start = sdk_text.index('class '+name+'(')
        end = sdk_text.find('\nclass ', start+1)
        sdk_snippets.append(sdk_text[start:end if end >= 0 else None])
    sdk_snapshot = '\n\n'.join(sdk_snippets)
    (output/'executed-sdk-mesh-separate-surface.txt').write_text(sdk_snapshot)
    sources = {}
    for name in ('connected', 'disconnected'):
        vertices, triangles = _source_data(name == 'disconnected')
        text, normals = _stl(vertices, triangles, 'owned_'+name+'_tetra')
        path = output/('owned-'+name+'-tetra.stl')
        path.write_text(text, encoding='ascii')
        sources[name] = dict(file=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            numeric_vertices=vertices, triangle_vertex_indices=triangles, facet_normals=normals,
            one_STL_solid=True, source_shell_count=2 if name == 'disconnected' else 1,
            source_signed_volume_cm3=8. if name == 'disconnected' else 4.,
            second_tetra_offset_cm=[4., 0., 0.] if name == 'disconnected' else None,
            import_units='CentimeterMeshUnit')
    truth = dict(fusion_version=app.version, samples=[], errors=[], planned_cases=list(cases),
        executed_generator_sha256=source_sha, mesh_source_helper_sha256=source_sha,
        helper_scope='All STL and serialization helpers are included in the exact executed-generator snapshot; helper hash is that same self-contained source',
        sdk_runtime_module=str(sdk_path), sdk_runtime_source_sha256=hashlib.sha256(sdk_bytes).hexdigest(),
        sdk_surface_snapshot='executed-sdk-mesh-separate-surface.txt',
        sdk_surface_snapshot_sha256=hashlib.sha256(sdk_snapshot.encode()).hexdigest(),
        sdk_method_enum_values={n: int(getattr(adsk.fusion.MeshSeparateTypes, n)) for n in
            ('ShellMeshSeparateType', 'FaceGroupMeshSeparateType')},
        sdk_scope='Active executable preview MeshSeparateFeatures.createInput(Base)/add; MeshBody input meshSeparateType controls, isKeepBody=False, feature.mesh getter only before node',
        inactive_control_scope='isMultipleBodies is documented only for face-group ObjectCollection inputs; no getter/setter call for these MeshBody cases',
        source_meshes=sources,
        import_scope='One STL import per owned BaseFeature. Only an actual count1 MeshBody input is passed to Separate. Multiple import results are preserved/exported and never merged or selected by geometry.',
        identity_scope='Input/rolled mesh handle equality and actual API collections are captured separately. Tokens stay opaque, array positions/custom names never choose native IDs or persistent ownership.',
        result_scope='No shell/face-group output count, success/no-op behavior, BaseFeature mesh ownership or lifecycle is presumed; actual arrays/health/errors determine evidence.')

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

    def controls(entity, include_mesh=False, is_input=False):
        row, errors = identity(entity), []
        row['meshSeparateType'] = observe('meshSeparateType', lambda: int(entity.meshSeparateType), errors)
        row['isKeepBody'] = observe('isKeepBody', lambda: bool(entity.isKeepBody), errors)
        row['isMultipleBodies'] = {'applicable': False, 'getter_called': False,
            'reason': 'Only valid for face-group collection inputs; this probe supplies MeshBody'}
        if is_input:
            row['targetBaseFeature'] = observe('targetBaseFeature', lambda: identity(entity.targetBaseFeature), errors)
        if include_mesh:
            actual = observe('mesh', lambda: entity.mesh, errors)
            row['input_entity'] = identity(actual)
            row['input_kind'] = 'MeshBody' if adsk.fusion.MeshBody.cast(actual) is not None else 'OtherOrNull'
            row['mesh_body'] = mesh_body(actual) if row['input_kind'] == 'MeshBody' else None
        row['control_getter_errors'] = errors
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
    for case, (source_name, method_name) in cases.items():
        doc = design = base = None
        editing = False
        sample = dict(case=case, file=case+'.f3d', getter_errors=[], setter_errors=[], phase='document_create',
            requested=dict(source=source_name, method=method_name, keep_body=False,
                isMultipleBodies_set=False, targetBaseFeature_set=False))
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
            base.name = 'Owned Separate import '+case
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
                mesh.name = 'OwnedSeparateSource_'+case+('_import'+str(index) if len(handles) != 1 else '')
            sample['imported_meshes_during_edit'] = [mesh_body(mesh) for mesh in handles]
            sample['base_finish_edit_returned'] = bool(base.finishEdit())
            if not sample['base_finish_edit_returned']:
                raise RuntimeError('Owned BaseFeature.finishEdit returned false')
            editing = False
            design.timeline.moveToEnd()
            sample['base_after_edit'] = base_truth(base)
            sample['imported_handles_before_separate'] = [mesh_body(mesh) for mesh in handles]
            sample['component_meshes_before_separate'] = component_meshes(root)
            sample['model_parameters_before'] = observe('modelParameters before',
                lambda: [parameter(p) for p in root.modelParameters], sample['getter_errors'])
            feature = None
            sample['phase'] = 'mesh_separate_attempt'
            try:
                if len(handles) != 1:
                    raise RuntimeError('Single-STL import produced '+str(len(handles))+' MeshBodies; one-body Separate input not manufactured')
                source_mesh = handles[0]
                sample['source_before_separate'] = mesh_body(source_mesh)
                collection = root.features.meshSeparateFeatures
                sample['separate_collection_count_before'] = collection.count
                inputs = collection.createInput(source_mesh)
                if inputs is None:
                    raise RuntimeError('MeshSeparate createInput returned null')
                sample['input_defaults'] = controls(inputs, True, True)
                method = getattr(adsk.fusion.MeshSeparateTypes, method_name)
                sample['requested']['method_enum'] = int(method)
                for prop, value in (('meshSeparateType', method), ('isKeepBody', False)):
                    try:
                        setattr(inputs, prop, value)
                    except Exception:
                        sample['setter_errors'].append(dict(property=prop, error=traceback.format_exc()))
                        raise
                sample['input_before_add'] = controls(inputs, True, True)
                sample['input_mesh_equals_import_handle'] = observe('input.mesh == source',
                    lambda: inputs.mesh == source_mesh, sample['getter_errors'])
                journal('mesh_separate_add_begin', case)
                feature = collection.add(inputs)
                sample['add_returned_feature'] = feature is not None
                if feature is None:
                    raise RuntimeError('Parametric MeshSeparate add returned null; actual unchanged/current mesh still exported')
                feature.name = 'OwnedMeshSeparate_'+case
                sample['separate_status'] = 'FeatureReturned'
                journal('mesh_separate_feature_returned', case)
            except Exception:
                sample['separate_status'] = 'AttemptError'
                error = dict(case=case, phase='mesh_separate_attempt', error=traceback.format_exc(),
                    policy='Preserve actual import/no-op/failure source and current arrays, export local archive; no successful separation or expected result count assumed')
                sample['separate_error'] = error
                truth['errors'].append(error)
                journal('mesh_separate_attempt_error', case)
            design.timeline.moveToEnd()
            sample['compute_all_returned'] = observe('design.computeAll', lambda: design.computeAll(), sample['getter_errors'])
            sample['component_meshes_after_separate'] = component_meshes(root)
            sample['original_handles_after_separate'] = [observe('original imported handle'+str(i),
                lambda mesh=mesh: mesh_body(mesh), sample['getter_errors']) for i, mesh in enumerate(handles)]
            sample['feature_at_timeline_end'] = feature_truth(feature)
            sample['base_after_separate'] = base_truth(base)
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
                    sample['getter_errors'].append(dict(getter='MeshSeparate rolled snapshot', error=traceback.format_exc()))
                finally:
                    design.timeline.moveToEnd()
            sample['separate_collection_count_after'] = observe('separateFeatures.count',
                lambda: root.features.meshSeparateFeatures.count, sample['getter_errors'])
            sample['timeline_count'] = design.timeline.count
            sample['timeline_marker_position'] = design.timeline.markerPosition
            sample['phase'] = 'local_export'
            journal('local_export_begin', case)
            destination = output/sample['file']
            succeeded = design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(destination)))
            if not succeeded or not destination.is_file() or not destination.stat().st_size:
                raise RuntimeError('Owned MeshSeparate local archive export failed')
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
    (output/'complete.txt').write_text('MeshSeparate terminal: '+truth['terminal_status']+'; inspect actual import/method/result/errors.\n')
