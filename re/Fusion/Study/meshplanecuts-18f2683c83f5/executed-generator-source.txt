"""Owned MeshPlaneCut probe using the ACTIVE executable Python bindings.

Those bindings explicitly mark MeshPlaneCut classes/enums as not officially
supported. The public callable route is used without UI commands. Three cases
vary fill, then cut type; flip stays false and gets no varied-control claim.
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
    'trim_no_fill': ('TrimMeshPlaneCutType', 'NoFillMeshPlaneCutFillType'),
    'trim_minimal_fill': ('TrimMeshPlaneCutType', 'MinimalMeshPlaneCutFillType'),
    'split_body_minimal_fill': ('SplitBodyMeshPlaneCutType', 'MinimalMeshPlaneCutFillType'),
}


def run(context):
    app = adsk.core.Application.get()
    cases = CASES
    if isinstance(context, dict) and 'cases' in context:
        selected = context['cases']
        if not isinstance(selected, (list, tuple)) or not selected or len(set(selected)) != len(selected) or set(selected)-set(CASES):
            raise ValueError('Select one to three distinct known MeshPlaneCut cases')
        cases = {name: spec for name, spec in CASES.items() if name in selected}
    source = Path(__file__).resolve()
    # Python.RunScript need not add this study directory to sys.path. Loading
    # the owned sibling by absolute path runs definitions only, not its run().
    helper_source = source.with_name('GenerateMeshContrasts.py')
    helper = runpy.run_path(str(helper_source))
    vertices, triangles = helper['VERTICES'], helper['TRIANGLES']
    output = source.parent/('meshplanecuts-'+uuid.uuid4().hex[:12])
    output.mkdir()
    executed = source.read_bytes()
    dependency = helper_source.read_bytes()
    (output/'executed-generator-source.txt').write_bytes(executed)
    (output/'executed-mesh-source-helper.txt').write_bytes(dependency)
    stl, normals = helper['_stl']()
    stl_path = output/'owned-tetra.stl'
    stl_path.write_text(stl, encoding='ascii')
    truth = {'samples': [], 'errors': [], 'fusion_version': app.version,
        'executed_generator_sha256': hashlib.sha256(executed).hexdigest(),
        'mesh_source_helper_sha256': hashlib.sha256(dependency).hexdigest(),
        'planned_cases': list(cases),
        'source_mesh': {'file': stl_path.name, 'sha256': hashlib.sha256(stl_path.read_bytes()).hexdigest(),
            'numeric_vertices': vertices, 'triangle_indices': triangles, 'facet_normals': normals,
            'import_units': 'CentimeterMeshUnit', 'analytic_source_volume_cm3': 4.0},
        'sdk_scope': 'ACTIVE executable adsk.fusion module; MeshPlaneCut classes/enums are explicitly not officially supported. Callable createInput(mesh,cutPlane)/add route only; no UI commands.',
        'sdk_runtime_module': getattr(adsk.fusion, '__file__', None),
        'scope': 'At most three newly owned parametric documents. One local tetra import per document, offset ConstructionPlane z=1cm, then one PlaneCut attempt outside BaseFeature edit. Record real arrays/settings/errors before and after; no BRep conversion, solver replay or persistent lifecycle claims.',
        'controls_scope': 'First contrast changes only NoFill to MinimalFill; second changes only Trim to SplitBody at MinimalFill. isFlip=False in all cases; UniformFill and SplitFaces untested.',
        'identity_scope': 'API tokens are opaque snapshots, never decoded as native IDs or compared for identity. Direct same-handle equality may be recorded separately. Input source arrays are captured before modification; current component collections are not automatically feature-owned result identities.',
        'plane_scope': 'Feature exposes mesh/type/fill/flip but no cutPlane getter. Actual input.cutPlane and owned ConstructionPlane geometry are captured independently; no fictitious feature plane getter.'}

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

    def plane_truth(plane):
        row, errors = identity(plane), []
        geometry = observe('geometry', lambda: plane.geometry, errors) if not isinstance(plane, adsk.core.Plane) else plane
        if geometry is not None:
            row['origin_cm'] = observe('geometry.origin', lambda: xyz(geometry.origin), errors)
            row['normal'] = observe('geometry.normal', lambda: xyz(geometry.normal), errors)
        row['plane_getter_errors'] = errors
        return row

    def input_truth(inp):
        row, errors = identity(inp), []
        for prop in ('meshPlaneCutType', 'meshPlaneCutFillType', 'isFlip'):
            row[prop] = observe(prop, lambda prop=prop: bool(getattr(inp, prop)) if prop == 'isFlip' else int(getattr(inp, prop)), errors)
        row['mesh'] = observe('mesh', lambda: identity(inp.mesh), errors)
        row['cutPlane'] = observe('cutPlane', lambda: plane_truth(inp.cutPlane), errors)
        row['targetBaseFeature'] = observe('targetBaseFeature', lambda: identity(inp.targetBaseFeature), errors)
        row['input_getter_errors'] = errors
        return row

    def feature_truth(feature):
        if feature is None:
            return None
        row, errors = identity(feature), []
        for prop in ('meshPlaneCutType', 'meshPlaneCutFillType', 'isFlip', 'healthState', 'errorOrWarningMessage', 'isParametric', 'isSuppressed'):
            row[prop] = observe(prop, lambda prop=prop: int(getattr(feature, prop)) if prop in ('meshPlaneCutType', 'meshPlaneCutFillType', 'healthState') else getattr(feature, prop), errors)
        row['mesh'] = observe('mesh', lambda: identity(feature.mesh), errors)
        row['baseFeature'] = observe('baseFeature', lambda: identity(feature.baseFeature), errors)
        row['parentComponent'] = observe('parentComponent', lambda: identity(feature.parentComponent), errors)
        row['brep_bodies'] = observe('bodies', lambda: None if feature.bodies is None else [identity(b) for b in items(feature.bodies)], errors)
        row['feature_getter_errors'] = errors
        return row

    journal('batch_begin', output_directory=str(output), planned_sample_count=len(cases))
    for case, (cut_name, fill_name) in cases.items():
        doc, design, base, editing = None, None, None, False
        sample = {'case': case, 'file': case+'.f3d', 'phase': 'document_create', 'getter_errors': [],
            'requested': {'meshPlaneCutType': cut_name, 'meshPlaneCutFillType': fill_name, 'isFlip': False,
                'plane_offset_cm': 1.0, 'plane_support': 'Root xYConstructionPlane', 'targetBaseFeature_set': False}}
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
            base = root.features.baseFeatures.add()
            base.name = 'Owned tetra import '+case
            started = base.startEdit(); sample['base_start_edit_returned'] = bool(started)
            if not started:
                raise RuntimeError('BaseFeature.startEdit returned false')
            editing = True
            sample['phase'] = 'owned_mesh_import'
            imported = root.meshBodies.add(str(stl_path), adsk.fusion.MeshUnits.CentimeterMeshUnit, base)
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
            sample['component_meshes_before_cut'] = component_meshes(root)
            sample['source_before_cut'] = mesh_body(mesh)
            sample['phase'] = 'owned_cut_plane'
            plane_input = root.constructionPlanes.createInput()
            configured = plane_input.setByOffset(root.xYConstructionPlane, adsk.core.ValueInput.createByReal(1.0))
            sample['plane_set_by_offset_returned'] = bool(configured)
            if not configured:
                raise RuntimeError('Owned plane setByOffset returned false')
            plane = root.constructionPlanes.add(plane_input)
            if plane is None:
                raise RuntimeError('Owned cut plane creation returned null')
            plane.name = 'Owned cut plane z1cm'
            sample['cut_plane'] = plane_truth(plane)
            feature = None
            sample['phase'] = 'plane_cut_attempt'
            try:
                collection = root.features.meshPlaneCutFeatures
                sample['plane_cut_collection_count_before'] = collection.count
                inp = collection.createInput(mesh, plane)
                if inp is None:
                    raise RuntimeError('MeshPlaneCut createInput returned null')
                sample['input_defaults'] = input_truth(inp)
                inp.meshPlaneCutType = getattr(adsk.fusion.MeshPlaneCutTypes, cut_name)
                inp.meshPlaneCutFillType = getattr(adsk.fusion.MeshPlaneCutFillTypes, fill_name)
                inp.isFlip = False
                sample['input_before_add'] = input_truth(inp)
                sample['input_mesh_equals_import_handle'] = observe('input.mesh == source', lambda: inp.mesh == mesh, sample['getter_errors'])
                sample['input_plane_equals_owned_plane'] = observe('input.cutPlane == plane', lambda: inp.cutPlane == plane, sample['getter_errors'])
                journal('plane_cut_add_begin', case)
                feature = collection.add(inp)
                sample['add_returned_feature'] = feature is not None
                if feature is None:
                    raise RuntimeError('Parametric PlaneCut add returned null; actual current meshes still captured and exported')
                feature.name = 'Owned Mesh Plane Cut '+case
                sample['plane_cut_status'] = 'FeatureReturned'
                journal('plane_cut_feature_returned', case)
            except Exception:
                sample['plane_cut_status'] = 'AttemptError'
                error = {'case': case, 'phase': 'plane_cut_attempt', 'error': traceback.format_exc(),
                    'policy': 'Preserve actual imported/current mesh and export it; failed PlaneCut is never labelled decoded or successful'}
                sample['plane_cut_error'] = error
                truth['errors'].append(error)
                journal('plane_cut_attempt_error', case)
            design.timeline.moveToEnd()
            sample['compute_all_returned'] = bool(design.computeAll())
            sample['component_meshes_after_cut'] = component_meshes(root)
            sample['original_source_handle_after_cut'] = observe('source handle after cut', lambda: mesh_body(mesh), sample['getter_errors'])
            sample['feature_at_timeline_end'] = feature_truth(feature)
            sample['base_after_cut'] = base_truth(base)
            if feature is not None:
                try:
                    rolled = feature.timelineObject.rollTo(True)
                    sample['roll_before_feature_returned'] = bool(rolled)
                    if rolled:
                        sample['feature_before_node'] = feature_truth(feature)
                        sample['component_meshes_before_node'] = component_meshes(root)
                except Exception:
                    sample['getter_errors'].append({'getter': 'roll/snapshot before owned PlaneCut node', 'error': traceback.format_exc()})
                finally:
                    design.timeline.moveToEnd()
            sample['plane_cut_collection_count_after'] = observe('plane cut count after', lambda: root.features.meshPlaneCutFeatures.count, sample['getter_errors'])
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
    (output/'complete.txt').write_text('terminal; inspect actual PlaneCut status/errors and source/result arrays in ground_truth.json\n')
