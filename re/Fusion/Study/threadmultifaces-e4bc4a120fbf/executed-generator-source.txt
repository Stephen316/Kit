"""Prepared owned two-face cosmetic Thread probes; root dispatches serially.

Full external, partial external, full internal. No modeled helices, existing user
documents, global preferences or library edits. Installed thread data is queried.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import traceback
import uuid

import adsk.core
import adsk.fusion

CASES = {
    'external_two_full': {'internal': False, 'partial': False},
    'external_two_partial': {'internal': False, 'partial': True},
    'internal_two_full': {'internal': True, 'partial': False},
}


def run(context):
    app = adsk.core.Application.get()
    cases = CASES
    if isinstance(context, dict) and 'cases' in context:
        selected = context['cases']
        if not isinstance(selected, (list, tuple)) or not selected or len(selected) != len(set(selected)) or set(selected)-set(CASES):
            raise ValueError('Select one to three distinct known multi-face Thread cases')
        cases = {name: spec for name, spec in CASES.items() if name in selected}
    source = Path(__file__).resolve()
    output = source.parent/('threadmultifaces-'+uuid.uuid4().hex[:12])
    output.mkdir()
    executed = source.read_bytes()
    (output/'executed-generator-source.txt').write_bytes(executed)
    sdk_path = Path(adsk.fusion.__file__)
    sdk = sdk_path.read_bytes()
    sdk_text = sdk.decode()
    sdk_blocks = []
    for name in ('ThreadFeatures', 'ThreadFeatureInput', 'ThreadFeature', 'ThreadInfo', 'ThreadDataQuery', 'ThreadLocations'):
        begin = sdk_text.index('class '+name+'(')
        end = sdk_text.find('\nclass ', begin+1)
        sdk_blocks.append(sdk_text[begin:] if end < 0 else sdk_text[begin:end])
    surface = '\n'.join(sdk_blocks).encode()
    (output/'executed-sdk-surface.txt').write_bytes(surface)
    truth = dict(samples=[], errors=[], fusion_version=app.version, planned_cases=list(cases),
        executed_generator_sha256=hashlib.sha256(executed).hexdigest(),
        sdk_runtime_module=str(sdk_path), sdk_runtime_sha256=hashlib.sha256(sdk).hexdigest(),
        executed_sdk_surface_sha256=hashlib.sha256(surface).hexdigest(), helper_dependencies=[],
        scope='Fresh owned parametric documents, two separately created root bodies, installed recommended straight metric data and cosmetic Thread only. Plural face selections and independent bodies/results are captured; tokens are opaque, no persistent ID mapping inferred.',
        applicability_scope='Full-length cases do not call length/offset/location getters or setters. Partial case uses7mm length/2mm offset/HighEnd; actual getter normalization/errors retained. No modeled thread geometry requested.')

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

    def xyz(point):
        return [point.x, point.y, point.z]

    def cylinder_truth(geometry):
        if geometry is None:
            return None
        row, errors = identity(geometry), []
        for prop in ('origin', 'axis'):
            row[prop] = observe(prop, lambda prop=prop: xyz(getattr(geometry, prop)), errors)
        row['radius_cm'] = observe('radius', lambda: geometry.radius, errors)
        row['getter_errors'] = errors
        return row

    def face_truth(face):
        row, errors = identity(face), []
        for prop in ('tempId', 'area', 'isParamReversed'):
            row[prop] = observe(prop, lambda prop=prop: getattr(face, prop), errors)
        row['body'] = observe('body', lambda: identity(face.body), errors)
        row['body_parent_component'] = observe('body.parentComponent', lambda: identity(face.body.parentComponent), errors)
        row['assemblyContext'] = observe('assemblyContext', lambda: identity(face.assemblyContext), errors)
        row['nativeObject'] = observe('nativeObject', lambda: identity(face.nativeObject), errors)
        row['geometry_object_type'] = observe('geometry.objectType', lambda: face.geometry.objectType, errors)
        cylinder = observe('Cylinder.cast', lambda: adsk.core.Cylinder.cast(face.geometry), errors)
        row['cylinder'] = None if cylinder is None else cylinder_truth(cylinder)
        row['edges'] = observe('edges', lambda: [dict(tempId=e.tempId,
            start_vertex_tempId=None if e.startVertex is None else e.startVertex.tempId,
            end_vertex_tempId=None if e.endVertex is None else e.endVertex.tempId,
            geometry_object_type=e.geometry.objectType) for e in items(face.edges)], errors)
        row['getter_errors'] = errors
        return row

    def body_truth(body):
        row, errors = identity(body), []
        for prop in ('tempId', 'isSolid', 'area', 'volume', 'isVisible'):
            row[prop] = observe(prop, lambda prop=prop: getattr(body, prop), errors)
        row['parentComponent'] = observe('parentComponent', lambda: identity(body.parentComponent), errors)
        row['baseOrFormFeature'] = observe('baseOrFormFeature', lambda: identity(body.baseOrFormFeature), errors)
        row['bounding_box_cm'] = observe('boundingBox', lambda: dict(min=xyz(body.boundingBox.minPoint),max=xyz(body.boundingBox.maxPoint)), errors)
        row['vertices'] = observe('vertices', lambda: [dict(tempId=v.tempId,position_cm=xyz(v.geometry)) for v in items(body.vertices)], errors)
        row['faces'] = observe('faces', lambda: [face_truth(f) for f in items(body.faces)], errors)
        row['getter_errors'] = errors
        return row

    def body_collection(collection):
        values = items(collection)
        return None if values is None else dict(count=len(values), bodies=[body_truth(body) for body in values])

    def info_truth(info):
        if info is None:
            return None
        row, errors = identity(info), []
        for prop in ('threadType', 'threadSize', 'threadDesignation', 'threadClass', 'isInternal', 'isRightHanded',
                     'isTapered', 'threadAngle', 'threadPitch', 'majorDiameter', 'minorDiameter', 'pitchDiameter', 'isHubLibraryThread', 'hubLibraryId'):
            row[prop] = observe(prop, lambda prop=prop: getattr(info, prop), errors)
        row['getter_errors'] = errors
        return row

    def value_truth(value, parameter=False):
        if value is None:
            return None
        row, errors = identity(value), []
        properties = ('name','role','expression','unit','value') if parameter else ('valueType','realValue','stringValue')
        for prop in properties:
            row[prop] = observe(prop, lambda prop=prop: int(value.valueType) if prop == 'valueType' else getattr(value, prop), errors)
        if parameter:
            row['createdBy'] = observe('createdBy', lambda: identity(value.createdBy), errors)
        row['getter_errors'] = errors
        return row

    def thread_truth(entity, partial, is_feature=False):
        row, errors = identity(entity), []
        for prop in ('isModeled','isFullLength'):
            row[prop] = observe(prop, lambda prop=prop: getattr(entity, prop), errors)
        row['threadInfo'] = observe('threadInfo', lambda: info_truth(entity.threadInfo), errors)
        row['inputCylindricalFaces'] = observe('inputCylindricalFaces', lambda: [face_truth(f) for f in items(entity.inputCylindricalFaces)], errors)
        if row['isFullLength'] is False:
            row['threadLength'] = observe('threadLength', lambda: value_truth(entity.threadLength,is_feature), errors)
            row['threadOffset'] = observe('threadOffset', lambda: value_truth(entity.threadOffset,is_feature), errors)
            row['threadLocation'] = observe('threadLocation', lambda: int(entity.threadLocation), errors)
        else:
            status = 'NotCalled_FullLength' if row['isFullLength'] is True else 'NotCalled_FullLengthGetterUnresolved'
            row['inactive_partial_controls'] = dict(threadLength=status,threadOffset=status,threadLocation=status)
        if is_feature:
            for prop in ('healthState','errorOrWarningMessage','isParametric','isSuppressed'):
                row[prop] = observe(prop, lambda prop=prop: int(entity.healthState) if prop == 'healthState' else getattr(entity,prop), errors)
            row['parentComponent'] = observe('parentComponent', lambda: identity(entity.parentComponent), errors)
            row['baseFeature'] = observe('baseFeature', lambda: identity(entity.baseFeature), errors)
            row['timeline_index'] = observe('timelineObject.index', lambda: entity.timelineObject.index, errors)
            row['bodies'] = observe('bodies', lambda: body_collection(entity.bodies), errors)
            row['faces'] = observe('faces', lambda: None if entity.faces is None else [face_truth(f) for f in items(entity.faces)], errors)
        else:
            row['targetBaseFeature'] = observe('targetBaseFeature', lambda: identity(entity.targetBaseFeature), errors)
        row['control_getter_errors'] = errors
        return row

    def feature_identity(feature):
        row, errors = identity(feature), []
        for prop in ('healthState','errorOrWarningMessage','isParametric'):
            row[prop] = observe(prop, lambda prop=prop: int(feature.healthState) if prop == 'healthState' else getattr(feature,prop), errors)
        row['timeline_index'] = observe('timelineObject.index', lambda: feature.timelineObject.index, errors)
        row['bodies'] = observe('bodies', lambda: body_collection(feature.bodies), errors)
        row['getter_errors'] = errors
        return row

    journal('batch_begin', output_directory=str(output), planned_sample_count=len(cases))
    for case, spec in cases.items():
        doc, design = None, None
        partial, internal = spec['partial'], spec['internal']
        sample = dict(case=case,file=case+'.f3d',phase='document_create',getter_errors=[],setter_errors=[],
            requested=dict(internal=internal,partial=partial,isModeled=False,source_body_count=2,
                source_radius_cm=0.6,annulus_outer_radius_cm=1.2 if internal else None,
                source_height_cm=2.0,source_centers_cm=[[0,0,0],[3,0,0]],
                threadLength='7 mm' if partial else 'NotCalled_FullLength',
                threadOffset='2 mm' if partial else 'NotCalled_FullLength',
                threadLocation='HighEndThreadLocation' if partial else 'NotCalled_FullLength'))
        truth['active_sample'] = sample
        try:
            journal('owned_document_create_begin',case)
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            if design is None:
                raise RuntimeError('Owned document lacks Fusion design product')
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            root = design.rootComponent
            sample['root_component'] = identity(root)
            sample['bodies_before_setup'] = body_collection(root.bRepBodies)
            sources, seeds, source_bodies = [], [], []
            for index, center_x in enumerate((0.0,3.0)):
                sample['phase'] = 'owned_source_'+str(index)
                sketch = root.sketches.add(root.xYConstructionPlane)
                sketch.name = 'OwnedThreadProfile_'+str(index)+'_'+case
                center = adsk.core.Point3D.create(center_x,0,0)
                sketch.sketchCurves.sketchCircles.addByCenterRadius(center,0.6)
                if internal:
                    sketch.sketchCurves.sketchCircles.addByCenterRadius(center,1.2)
                profiles = [p for p in items(sketch.profiles) if p.profileLoops.count == (2 if internal else 1)]
                if len(profiles) != 1:
                    raise RuntimeError('Owned source profile is not unique')
                seed = root.features.extrudeFeatures.addSimple(profiles[0], adsk.core.ValueInput.createByString('20 mm'),
                    adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                if seed is None or seed.bodies.count != 1:
                    raise RuntimeError('Owned source Extrude did not produce one body')
                seed.name = 'OwnedThreadCylinderExtrude_'+str(index)+'_'+case
                body = seed.bodies.item(0);body.name = 'OwnedThreadCylinder_'+str(index)+'_'+case
                matching = []
                for face in items(body.faces):
                    cylinder = adsk.core.Cylinder.cast(face.geometry)
                    if cylinder is not None and abs(cylinder.radius-0.6) < 1e-9:
                        matching.append(face)
                if len(matching) != 1:
                    raise RuntimeError('Owned cylindrical thread source face not unique')
                sources.append(matching[0]);seeds.append(seed);source_bodies.append(body)
            sample['setup_features'] = [feature_identity(seed) for seed in seeds]
            sample['selected_faces_before_thread'] = [face_truth(face) for face in sources]
            sample['source_bodies_before_thread'] = [body_truth(body) for body in source_bodies]
            sample['component_bodies_before_thread'] = body_collection(root.bRepBodies)
            sample['phase'] = 'installed_thread_recommendation'
            query = adsk.fusion.ThreadDataQuery.create(False)
            family = query.defaultMetricThreadType
            ok, designation, thread_class = query.recommendThreadData(1.2,internal,family)
            sample['installed_recommendation'] = dict(returned_success=bool(ok),diameter_cm=1.2,is_internal=internal,
                thread_type=family,designation=designation,thread_class=thread_class)
            if not ok:
                raise RuntimeError('Installed metric thread recommendation failed')
            info = adsk.fusion.ThreadInfo.create(False,internal,family,designation,thread_class,True)
            if info is None:
                raise RuntimeError('Documented ThreadInfo.create returned null')
            sample['requested_thread_info'] = info_truth(info)
            collection = adsk.core.ObjectCollection.create()
            sample['source_collection_add_returns'] = [bool(collection.add(face)) for face in sources]
            if not all(sample['source_collection_add_returns']):
                raise RuntimeError('Owned source ObjectCollection rejected a face')
            sample['thread_collection_count_before'] = root.features.threadFeatures.count
            sample['phase'] = 'thread_input'
            inp = root.features.threadFeatures.createInput(collection,info)
            if inp is None:
                raise RuntimeError('Plural cylindrical Thread createInput returned null')
            sample['input_defaults'] = thread_truth(inp,False)
            for prop, requested in (('isModeled',False),('isFullLength',not partial)):
                try:
                    setattr(inp,prop,requested)
                except Exception:
                    sample['setter_errors'].append(dict(setter=prop,error=traceback.format_exc()))
                    raise
            if partial:
                for prop,text in (('threadLength','7 mm'),('threadOffset','2 mm')):
                    value = adsk.core.ValueInput.createByString(text)
                    sample['requested_'+prop+'_ValueInput'] = value_truth(value)
                    try:
                        setattr(inp,prop,value)
                    except Exception:
                        sample['setter_errors'].append(dict(setter=prop,error=traceback.format_exc()))
                        raise
                try:
                    inp.threadLocation = adsk.fusion.ThreadLocations.HighEndThreadLocation
                except Exception:
                    sample['setter_errors'].append(dict(setter='threadLocation',error=traceback.format_exc()))
                    raise
            sample['input_before_add'] = thread_truth(inp,partial)
            sample['input_faces_equal_selected_handles'] = observe('inputCylindricalFaces equal selected handles',
                lambda: len(items(inp.inputCylindricalFaces)) == len(sources) and all(a == b for a,b in zip(items(inp.inputCylindricalFaces),sources)),sample['getter_errors'])
            sample['phase'] = 'thread_add'
            journal('thread_add_begin',case)
            feature = root.features.threadFeatures.add(inp)
            sample['add_returned_feature'] = feature is not None
            if feature is None:
                raise RuntimeError('Cosmetic plural Thread add returned null')
            feature.name = 'OwnedThreadMultiFace_'+case
            sample['thread_status'] = 'FeatureReturned'
            design.timeline.moveToEnd()
            sample['compute_all_returned'] = bool(design.computeAll())
            sample['feature_at_timeline_end'] = thread_truth(feature,partial,True)
            sample['component_bodies_after_thread'] = body_collection(root.bRepBodies)
            sample['model_parameters_after'] = [value_truth(p,True) for p in items(root.modelParameters)]
            try:
                rolled = feature.timelineObject.rollTo(True)
                sample['roll_before_feature_returned'] = bool(rolled)
                if rolled:
                    sample['feature_before_node'] = thread_truth(feature,partial,True)
                    sample['selected_faces_before_node'] = [face_truth(face) for face in sources]
                    sample['component_bodies_before_node'] = body_collection(root.bRepBodies)
                    sample['feature_input_faces_equal_selected_handles'] = observe('feature inputCylindricalFaces equal selected handles',
                        lambda: len(items(feature.inputCylindricalFaces)) == len(sources) and all(a == b for a,b in zip(items(feature.inputCylindricalFaces),sources)),sample['getter_errors'])
            except Exception:
                sample['getter_errors'].append(dict(getter='owned Thread roll/snapshot',error=traceback.format_exc()))
            finally:
                design.timeline.moveToEnd()
            sample['thread_collection_count_after'] = root.features.threadFeatures.count
            sample['timeline_count'] = design.timeline.count
            sample['timeline_marker_position'] = design.timeline.markerPosition
            sample['phase'] = 'local_export'
            journal('local_export_begin',case,file=sample['file'])
            destination = output/sample['file']
            succeeded = design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(destination)))
            if not succeeded or not destination.is_file() or destination.stat().st_size == 0:
                raise RuntimeError('Local owned Thread archive export did not complete')
            sample['export'] = dict(returned_success=bool(succeeded),size_bytes=destination.stat().st_size,
                sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
            sample['phase'] = 'export_complete'
            truth['samples'].append(sample);truth.pop('active_sample',None)
            journal('local_export_complete',case,file=sample['file'])
        except Exception:
            truth['errors'].append(dict(case=case,phase=sample['phase'],error=traceback.format_exc(),partial_sample=sample))
            truth.pop('active_sample',None)
            journal('case_error',case)
        finally:
            if design is not None:
                try:
                    design.timeline.moveToEnd()
                except Exception:
                    truth['errors'].append(dict(case=case,phase='restore_owned_timeline',error=traceback.format_exc()))
            if doc is not None:
                try:
                    journal('owned_document_close_begin',case,save=False)
                    closed = doc.close(False)
                    sample['close_owned_document_returned'] = bool(closed)
                    journal('owned_document_close_returned',case,returned=bool(closed),save=False)
                    if not closed:
                        truth['errors'].append(dict(case=case,phase='close_owned_document',error='close(False) returned false'))
                except Exception:
                    truth['errors'].append(dict(case=case,phase='close_owned_document',error=traceback.format_exc()))
            persist()
    truth['terminal_status'] = 'Complete' if not truth['errors'] else 'CompleteWithErrors'
    journal('batch_terminal',planned_sample_count=len(cases),exported_sample_count=len(truth['samples']),terminal_status=truth['terminal_status'])
    (output/'complete.txt').write_text('terminal; inspect actual exported samples, all getter/case errors and owned document closes\n')
