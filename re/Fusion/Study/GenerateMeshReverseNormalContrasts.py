"""Owned closed/open MeshReverseNormal probes, including two reversals.

Use the active executable API only; export observations and retain getter errors.
No existing document is edited or saved.
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

CASES = {'closed_once': (False, 1), 'closed_twice': (False, 2), 'open_once': (True, 1)}


def run(context):
    app = adsk.core.Application.get()
    source = Path(__file__).resolve()
    helper_path = source.with_name('GenerateMeshContrasts.py')
    helper = runpy.run_path(str(helper_path))
    output = source.parent/('meshreversenormals-'+uuid.uuid4().hex[:12])
    output.mkdir()
    executed, dependency = source.read_bytes(), helper_path.read_bytes()
    (output/'executed-generator-source.txt').write_bytes(executed)
    (output/'executed-mesh-source-helper.txt').write_bytes(dependency)
    stl, normals = helper['_stl']()
    lines = stl.splitlines()
    if len(lines) != 30:
        raise ValueError('Unexpected owned tetra STL framing')
    closed_path, open_path = output/'owned-closed-tetra.stl', output/'owned-open-tetra.stl'
    closed_path.write_text(stl, encoding='ascii')
    open_path.write_text('\n'.join(lines[:22]+['endsolid owned_tetra', '']), encoding='ascii')
    truth = dict(samples=[], errors=[], fusion_version=app.version, planned_cases=list(CASES),
        executed_generator_sha256=hashlib.sha256(executed).hexdigest(),
        mesh_source_helper_sha256=hashlib.sha256(dependency).hexdigest(),
        sdk_runtime_module=adsk.fusion.__file__,
        sdk_runtime_sha256=hashlib.sha256(Path(adsk.fusion.__file__).read_bytes()).hexdigest(),
        source_vertices=helper['VERTICES'], source_closed_triangles=helper['TRIANGLES'],
        source_closed_facet_normals=normals,
        source_files=[dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in (closed_path,open_path)],
        scope='Fresh owned parametric documents; local STL import in BaseFeature edit, ReverseNormal outside edit. Actual arrays/normal pools/volumes captured before and after each operation. No orientation, volume sign, involution or mesh ownership assumed.',
        identity_scope='Explicit API handles and equality observations only; entity tokens stay opaque. Native persistent IDs are not inferred from geometry or collection indices.')

    def persist():
        (output/'ground_truth.json').write_text(json.dumps(truth,indent=2)+'\n')

    def journal(phase, case=None, **fields):
        row = dict(time_utc=datetime.now(timezone.utc).isoformat(), phase=phase, case=case,
                   sample_count=len(truth['samples']), error_count=len(truth['errors']), **fields)
        with (output/'journal.jsonl').open('a') as stream:
            stream.write(json.dumps(row)+'\n')
        (output/'progress.json').write_text(json.dumps(row,indent=2)+'\n')
        persist()

    def observe(label, getter, errors):
        try:
            return getter()
        except Exception:
            errors.append(dict(getter=label,error=traceback.format_exc()))
            return None

    def items(value):
        if value is None:
            return None
        if hasattr(value,'item') and hasattr(value,'count'):
            return [value.item(i) for i in range(value.count)]
        return list(value)

    def identity(entity):
        if entity is None:
            return None
        row, errors = {}, []
        for prop in ('objectType','name','isValid','entityToken'):
            if hasattr(type(entity),prop):
                row[prop] = observe(prop,lambda prop=prop:getattr(entity,prop),errors)
        row['getter_errors'] = errors
        return row

    def mesh_array(value, display=False):
        if value is None:
            return None
        row, errors = {}, []
        props = ['objectType','nodeCount','nodeCoordinatesAsDouble','triangleCount','normalVectorsAsDouble']
        props += ['nodeIndices','surfaceTolerance'] if display else ['triangleNodeIndices','triangleFaceGroupTempIds','quadCount','polygonCount','quadNodeIndices','polygonNodeIndices','nodeCountPerPolygon']
        for prop in props:
            row[prop] = observe(prop,lambda prop=prop:getattr(value,prop),errors)
        row['getter_errors'] = errors
        return row

    def mesh_body(value):
        if value is None:
            return None
        row, errors = identity(value), []
        for prop in ('area','volume','isClosed','isOriented','isVisible'):
            row[prop] = observe(prop,lambda prop=prop:getattr(value,prop),errors)
        for prop in ('parentComponent','baseOrFormFeature','nativeObject','assemblyContext'):
            row[prop] = observe(prop,lambda prop=prop:identity(getattr(value,prop)),errors)
        def bounds():
            b = value.boundingBox
            return dict(min=[b.minPoint.x,b.minPoint.y,b.minPoint.z], max=[b.maxPoint.x,b.maxPoint.y,b.maxPoint.z])
        row['bounding_box_cm'] = observe('boundingBox',bounds,errors)
        row['original_polygon_mesh'] = observe('mesh',lambda:mesh_array(value.mesh),errors)
        row['display_triangle_mesh'] = observe('displayMesh',lambda:mesh_array(value.displayMesh,True),errors)
        row['mesh_getter_errors'] = errors
        return row

    def meshes(root):
        bodies = items(root.meshBodies)
        return dict(count=len(bodies),meshes=[mesh_body(b) for b in bodies])

    def feature_truth(value, rolled=False):
        if value is None:
            return None
        row, errors = identity(value), []
        for prop in ('healthState','errorOrWarningMessage','isParametric','isSuppressed'):
            row[prop] = observe(prop,lambda prop=prop:int(getattr(value,prop)) if prop=='healthState' else getattr(value,prop),errors)
        for prop in ('baseFeature','parentComponent'):
            row[prop] = observe(prop,lambda prop=prop:identity(getattr(value,prop)),errors)
        for prop in ('bodies','faces'):
            row[prop] = observe(prop,lambda prop=prop:[identity(e) for e in items(getattr(value,prop))],errors)
        row['timeline_index'] = observe('timelineObject.index',lambda:value.timelineObject.index,errors)
        row['mesh'] = observe('mesh',lambda:mesh_body(value.mesh),errors)
        row['mesh_getter_scope'] = 'Immediately before this feature' if rolled else 'Timeline end; mesh getter may require rollback'
        row['getter_errors'] = errors
        return row

    def base_truth(value):
        row, errors = identity(value), []
        for prop in ('meshBodies','sourceBodies','bodies'):
            row[prop] = observe(prop,lambda prop=prop:[identity(e) for e in items(getattr(value,prop))],errors)
        row['timeline_index'] = observe('timelineObject.index',lambda:value.timelineObject.index,errors)
        row['getter_errors'] = errors
        return row

    persist()
    for case,(is_open,reversals) in CASES.items():
        doc = design = base = None
        editing = False
        sample = dict(case=case,file=case+'.f3d',requested=dict(open_source=is_open,reversals=reversals),
                      getter_errors=[],steps=[],phase='document_create')
        truth['active_sample'] = sample
        try:
            journal('owned_document_create_begin',case)
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            if design is None:
                raise RuntimeError('Owned document has no Fusion Design')
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            base = root.features.baseFeatures.add()
            base.name = 'Owned reverse-normal source '+case
            sample['base_start_edit_returned'] = bool(base.startEdit())
            if not sample['base_start_edit_returned']:
                raise RuntimeError('Owned BaseFeature.startEdit returned false')
            editing = True
            sample['phase'] = 'owned_mesh_import'
            path = open_path if is_open else closed_path
            imported = root.meshBodies.add(str(path),adsk.fusion.MeshUnits.CentimeterMeshUnit,base)
            if imported is None or imported.count != 1:
                raise RuntimeError('Owned STL did not import exactly one MeshBody')
            mesh = imported.item(0)
            mesh.name = 'OwnedReverseSource_'+case
            sample['source_during_edit'] = mesh_body(mesh)
            sample['base_finish_edit_returned'] = bool(base.finishEdit())
            if not sample['base_finish_edit_returned']:
                raise RuntimeError('Owned BaseFeature.finishEdit returned false')
            editing = False
            design.timeline.moveToEnd()
            sample['base_after_import'] = base_truth(base)
            sample['component_meshes_before_reverse'] = meshes(root)
            collection = root.features.meshReverseNormalFeatures
            for step_index in range(reversals):
                step = dict(step_index=step_index,getter_errors=[],phase='reverse_attempt')
                sample['steps'].append(step)
                feature = None
                try:
                    sample['phase'] = 'mesh_reverse_attempt'
                    if root.meshBodies.count != 1:
                        raise RuntimeError('Expected one actual current mesh before reverse')
                    target = root.meshBodies.item(0)
                    step['component_meshes_before'] = meshes(root)
                    step['collection_count_before'] = collection.count
                    inputs = collection.createInput(target)
                    if inputs is None:
                        raise RuntimeError('MeshReverseNormal createInput returned null')
                    step['input_targetBaseFeature'] = observe('input.targetBaseFeature',lambda:identity(inputs.targetBaseFeature),step['getter_errors'])
                    step['input_mesh'] = observe('input.mesh',lambda:mesh_body(inputs.mesh),step['getter_errors'])
                    step['input_mesh_equals_target'] = observe('input.mesh == target',lambda:inputs.mesh==target,step['getter_errors'])
                    journal('mesh_reverse_add_begin',case,step_index=step_index)
                    feature = collection.add(inputs)
                    step['add_returned_feature'] = feature is not None
                    if feature is None:
                        raise RuntimeError('Parametric MeshReverseNormal add returned null')
                    feature.name = 'OwnedMeshReverse_'+case+'_'+str(step_index+1)
                    step['status'] = 'FeatureReturned'
                    journal('mesh_reverse_feature_returned',case,step_index=step_index)
                except Exception:
                    step['status'] = 'AttemptError'
                    failure = dict(case=case,step_index=step_index,phase='mesh_reverse_attempt',error=traceback.format_exc())
                    step['error'] = failure
                    truth['errors'].append(failure)
                    journal('mesh_reverse_attempt_error',case,step_index=step_index)
                design.timeline.moveToEnd()
                step['compute_all_returned'] = observe('computeAll',lambda:design.computeAll(),step['getter_errors'])
                step['component_meshes_after'] = meshes(root)
                step['feature_at_timeline_end'] = feature_truth(feature)
                if feature is not None:
                    try:
                        step['roll_before_feature_returned'] = bool(feature.timelineObject.rollTo(True))
                        if step['roll_before_feature_returned']:
                            step['feature_before_node'] = feature_truth(feature,True)
                            step['component_meshes_before_node'] = meshes(root)
                            step['rolled_mesh_equals_target'] = observe('feature.mesh == target',lambda:feature.mesh==target,step['getter_errors'])
                    except Exception:
                        step['getter_errors'].append(dict(getter='roll before feature',error=traceback.format_exc()))
                    finally:
                        design.timeline.moveToEnd()
                step['collection_count_after'] = collection.count
                step['phase'] = 'observations_complete'
                if step['status'] == 'AttemptError':
                    break
            sample['component_meshes_after_reverse'] = meshes(root)
            sample['base_after_reverse'] = base_truth(base)
            sample['timeline_count'] = design.timeline.count
            sample['timeline_marker_position'] = design.timeline.markerPosition
            sample['phase'] = 'local_export'
            journal('local_export_begin',case)
            destination = output/sample['file']
            succeeded = design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(destination)))
            if not succeeded or not destination.is_file() or not destination.stat().st_size:
                raise RuntimeError('Owned local archive export failed')
            sample['export'] = dict(returned_success=bool(succeeded),size_bytes=destination.stat().st_size,sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
            sample['phase'] = 'export_complete'
            truth['samples'].append(sample)
            journal('local_export_complete',case)
        except Exception:
            truth['errors'].append(dict(case=case,phase=sample['phase'],error=traceback.format_exc(),partial_sample=sample))
            journal('case_error',case)
        finally:
            if editing and base is not None:
                observe('cleanup BaseFeature.finishEdit',lambda:base.finishEdit(),truth['errors'])
            if design is not None:
                observe('restore owned timeline',lambda:design.timeline.moveToEnd(),truth['errors'])
            if doc is not None:
                journal('owned_document_close_begin',case,save=False)
                closed = observe('close owned document',lambda:doc.close(False),truth['errors'])
                sample['close_owned_document_returned'] = bool(closed)
                journal('owned_document_close_returned',case,returned=bool(closed),save=False)
                if not closed:
                    truth['errors'].append(dict(case=case,phase='close_owned_document',error='close(False) did not return true'))
            truth.pop('active_sample',None)
            persist()
    truth['terminal_status'] = 'complete' if len(truth['samples'])==len(CASES) and not truth['errors'] else 'complete_with_errors'
    journal('batch_terminal')
    (output/'complete.txt').write_text('MeshReverseNormal terminal: '+truth['terminal_status']+'; inspect actual getter errors and arrays.\n')
