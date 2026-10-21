"""Owned Rule-fillet surface observations, with one temporary conversion per body."""

from datetime import datetime, timezone
import gc
import hashlib
import json
import math
from pathlib import Path
import uuid

import adsk.core
import adsk.fusion

HALTED_ATTRIBUTE = '_fusion_study_rule_surface_halted_documents'
WITNESS_HALTED_ATTRIBUTE = '_fusion_study_rule_surface_witness_halted_native_handles'
MAX_WITNESSES_PER_CASE = 8
CASES = (('offsets_one_two', '2 mm'), ('offsets_one_three', '3 mm'))


def run(context):
    if (getattr(adsk.fusion, HALTED_ATTRIBUTE, None)
            or getattr(adsk.fusion, WITNESS_HALTED_ATTRIBUTE, None)
            or getattr(adsk.fusion, '_codex_FusionFileStudy_surface_trim_halted_native_handles', None)):
        raise RuntimeError('Prior owned native handles remain quarantined; no capture started')
    app = adsk.core.Application.get()
    source = Path(__file__).resolve()
    folder = source.parent / ('rulefilletsurfaces-' + uuid.uuid4().hex[:12])
    folder.mkdir()
    executed = source.read_bytes()
    (folder / 'executed-generator-source.txt').write_bytes(executed)
    sdk_sources, sdk_hashes = [], {}
    for module, names in ((adsk.core, ('Base', 'ObjectCollection', 'ValueInput',
                                     'SurfaceEvaluator', 'NurbsSurface', 'Point3DVector')),
                          (adsk.fusion, ('BRepBody', 'BRepFace', 'BRepConvertOptions',
                                         'FilletFeatures', 'RuleFilletFeatureInput', 'Design',
                                         'Timeline', 'TimelineObject', 'OffsetFeatures',
                                         'OffsetFeatureInput', 'OffsetFeature'))):
        sdk_path = Path(module.__file__)
        raw = sdk_path.read_bytes()
        sdk_hashes[str(sdk_path)] = hashlib.sha256(raw).hexdigest()
        text = raw.decode()
        for name in names:
            start = text.index('class ' + name + '(')
            end = text.find('\nclass ', start + 1)
            sdk_sources.append(text[start:] if end < 0 else text[start:end])
    sdk_surface = '\n'.join(sdk_sources).encode()
    (folder / 'executed-sdk-surface.txt').write_bytes(sdk_surface)
    truth = dict(fusion_version=app.version, samples=[], errors=[],
        planned_cases=[name for name, _ in CASES],
        executed_generator_sha256=hashlib.sha256(executed).hexdigest(),
        sdk_runtime_sha256=sdk_hashes,
        executed_sdk_surface_sha256=hashlib.sha256(sdk_surface).hexdigest(),
        scope='Fresh owned parametric documents; no user document, global keyboard, or native/API topology assignment. Direct surface data and temporary API conversion remain separate.',
        lifecycle_policy='Populate frame returns JSON only; garbage collect while owned document is open, short final recompute/export frame, collect, then close(False). On failure retain owned document and stop without another case.',
        conversion_scope='One ProceduralToNURBSConversion per result body; temporary result never added to design. API tempId matches retain every split; native file records are not assigned by face order or coordinates.',
        witness_scope='After unchanged source-only archive export, at most eight singleton zero-offset NewBody consumers across all bodies in each case. Same-document opaque tokens are resolved through the API; native recipe/VBL binding remains unproven until exported typed ownership and complete naming are inspected.',
        witness_identity_method='adsk.core.Base.__eq__ on valid same-type BRepFace/OffsetFeature wrappers delegates to native equality; token strings, Python identity, coordinates, enumeration order and tempId are not identity tests',
        witness_lifecycle_policy='Create frame returns JSON; GC while document open; rolled getter frame returns JSON; GC while still before node; fresh restoration frame; GC open; separate witness export/finalizer; GC then close(False). Any failure retains native aliases/document and halts without another face/case.',
        maximum_witnesses_per_case=MAX_WITNESSES_PER_CASE,
        point_tolerance_cm=float(app.pointTolerance))

    def journal(phase, case=None, **fields):
        row = dict(time_utc=datetime.now(timezone.utc).isoformat(), phase=phase,
                   case=case, sample_count=len(truth['samples']), error_count=len(truth['errors']), **fields)
        with (folder / 'journal.jsonl').open('a') as stream:
            stream.write(json.dumps(row) + '\n')
        (folder / 'progress.json').write_text(json.dumps(row, indent=2) + '\n')
        (folder / 'ground_truth.json').write_text(json.dumps(truth, indent=2, allow_nan=False) + '\n')

    def read(errors, label, getter):
        try:
            return getter()
        except Exception as error:
            errors.append(dict(field=label, error_type=type(error).__name__, error=str(error)))
            return None

    def xyz(point):
        return [float(point.x), float(point.y), float(point.z)]

    def uv(point):
        return [float(point.x), float(point.y)]

    def nurbs(surface):
        if not isinstance(surface, adsk.core.NurbsSurface):
            return dict(available=False, reason='Actual surface is not NurbsSurface')
        result = surface.getData()
        row = dict(available=True, tuple_length=len(result), success=bool(result[0]))
        if not result[0]:
            return row
        if len(result) != 11:
            raise RuntimeError('Unexpected actual NurbsSurface.getData tuple extent')
        _, du, dv, nu, nv, points, ku, kv, weights, pu, pv = result
        if not 1 <= int(nu) * int(nv) <= 250000:
            raise RuntimeError('NURBS capture control count outside bounded scope')
        row.update(degree_u=int(du), degree_v=int(dv), count_u=int(nu), count_v=int(nv),
            control_points_cm=[xyz(points[i]) for i in range(len(points))],
            knots_u=list(ku), knots_v=list(kv), weights=list(weights),
            properties_u=int(pu), properties_v=int(pv),
            control_order='Literal API array order; no native tensor ordering inferred')
        if len(row['control_points_cm']) != int(nu) * int(nv):
            raise RuntimeError('Actual NURBS control array/count disagree')
        return row

    def evaluate(face, parameter):
        evaluator = face.evaluator
        row = dict(uv=uv(parameter), is_parameter_on_face=bool(evaluator.isParameterOnFace(parameter)))
        if not row['is_parameter_on_face']:
            return row
        ok, point = evaluator.getPointAtParameter(parameter)
        row.update(point_success=bool(ok), point_cm=xyz(point) if ok else None)
        ok, du, dv = evaluator.getFirstDerivative(parameter)
        row.update(derivative_success=bool(ok), partial_u=xyz(du) if ok else None,
                   partial_v=xyz(dv) if ok else None)
        return row

    def face_data(face, deep):
        errors = []
        surface = face.geometry
        row = dict(temp_id=int(face.tempId), object_type=face.objectType,
            is_temporary=bool(face.body.isTemporary), surface_type=int(surface.surfaceType),
            geometry_object_type=surface.objectType, is_param_reversed=bool(face.isParamReversed),
            area_cm2=float(face.area), edge_count=face.edges.count, loop_count=face.loops.count,
            point_on_face_cm=xyz(face.pointOnFace), getter_errors=errors)
        if not face.body.isTemporary:
            row['entity_token'] = read(errors, 'entityToken', lambda: face.entityToken)
        if not deep:
            return row
        row['nurbs_data'] = read(errors, 'geometry.getData', lambda: nurbs(surface))
        evaluator = face.evaluator
        bounds = evaluator.parametricRange()
        lower, upper = uv(bounds.minPoint), uv(bounds.maxPoint)
        row['parameter_range'] = [lower, upper]
        ok, anchor = evaluator.getParameterAtPoint(face.pointOnFace)
        row['anchor_parameter_success'] = bool(ok)
        row['samples'] = []
        if ok:
            row['samples'].append(read(errors, 'anchor evaluation', lambda: evaluate(face, anchor)))
            for axis in (0, 1):
                extent = upper[axis] - lower[axis]
                if not math.isfinite(extent) or not 0 < extent < 1e20:
                    continue
                candidate = uv(anchor)
                candidate[axis] += .05 * extent
                parameter = adsk.core.Point2D.create(*candidate)
                row['samples'].append(read(errors, 'axis ' + str(axis) + ' evaluation',
                    lambda parameter=parameter: evaluate(face, parameter)))
        return row

    def populate(doc, case, offset_two):
        # Every SDK wrapper in this frame dies before the caller closes doc.
        design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        point, value = adsk.core.Point3D.create, adsk.core.ValueInput.createByString
        sketch = root.sketches.add(root.xYConstructionPlane)
        sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0, 0, 0), point(6, 5, 0))
        seed = root.features.extrudeFeatures.addSimple(sketch.profiles.item(0), value('10 mm'),
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        seed.name = 'FilletSeed'
        seed.bodies.item(0).name = 'FilletTarget'
        plane_input = root.constructionPlanes.createInput()
        if not plane_input.setByOffset(root.xYConstructionPlane, value('10 mm')):
            raise RuntimeError('Owned boss plane input rejected')
        plane = root.constructionPlanes.add(plane_input)
        profile = root.sketches.add(plane)
        profile.sketchCurves.sketchLines.addTwoPointRectangle(point(2, 1.5, 0), point(4, 3.5, 0))
        boss = root.features.extrudeFeatures.addSimple(profile.profiles.item(0), value('20 mm'),
            adsk.fusion.FeatureOperations.JoinFeatureOperation)
        boss.name = 'FilletBoss'
        inputs = root.features.filletFeatures.createRuleFilletInput()
        if not inputs.setByAllEdges([boss]):
            raise RuntimeError('Owned Rule source rejected')
        inputs.topologyType = 0
        inputs.isRollingBallCorner = False
        if not inputs.setAsymmetricOffsets(value('1 mm'), value(offset_two)):
            raise RuntimeError('Owned asymmetric offsets rejected')
        journal('creating_feature', case)
        feature = root.features.filletFeatures.addRuleFillet(inputs)
        if feature is None:
            raise RuntimeError('Rule Fillet creation returned null')
        feature.name = 'ProbeRuleSurface'
        if not design.computeAll() or int(feature.healthState) != 0:
            raise RuntimeError('Owned Rule Fillet did not compute healthy')
        sample = dict(file=case + '.f3d', requested_offsets=['1 mm', offset_two],
            requested_topology_type=0, requested_rolling_ball_corner=False,
            feature_type=feature.objectType, feature_health_state=int(feature.healthState),
            feature_warning=feature.errorOrWarningMessage,
            parameters=[dict(name=p.name, role=p.role, value=p.value, unit=p.unit) for p in root.modelParameters],
            result_bodies=[], getter_errors=[])
        total_selected = 0
        for body in feature.bodies:
            body_row = dict(name=body.name, entity_token=body.entityToken, is_temporary=bool(body.isTemporary),
                volume_cm3=float(body.volume), face_count=body.faces.count, edge_count=body.edges.count,
                faces=[], conversion_option=int(adsk.fusion.BRepConvertOptions.ProceduralToNURBSConversion),
                converted_faces=[], converted_matches=[], getter_errors=[])
            selected = [f for f in body.faces if f.loops.count == 1 and f.edges.count == 6]
            body_row['deep_face_temp_ids'] = [int(f.tempId) for f in selected]
            body_row['deep_scope'] = 'All single-loop six-edge API faces; topology signature is not a native face assignment'
            total_selected += len(selected)
            if total_selected > MAX_WITNESSES_PER_CASE:
                raise RuntimeError('Six-edge face capture exceeds eight faces across all case bodies')
            selected_ids = set(body_row['deep_face_temp_ids'])
            for face in body.faces:
                body_row['faces'].append(face_data(face, int(face.tempId) in selected_ids))
            journal('converting_temporary_body', case, source_face_count=body.faces.count)
            converted = body.convert(adsk.fusion.BRepConvertOptions.ProceduralToNURBSConversion)
            body_row['conversion_returned_body'] = converted is not None
            if converted is not None:
                if not converted.isTemporary:
                    raise RuntimeError('Unexpected non-temporary conversion result; halt before export')
                body_row['converted_is_temporary'] = bool(converted.isTemporary)
                body_row['converted_face_count'] = converted.faces.count
                for face in converted.faces:
                    body_row['converted_faces'].append(face_data(face, int(face.tempId) in selected_ids))
                for source_face in selected:
                    matches = [f for f in converted.findByTempId(source_face.tempId)
                               if isinstance(f, adsk.fusion.BRepFace)]
                    mapping = dict(source_face_temp_id=int(source_face.tempId), match_count=len(matches), matches=[])
                    source_data = next(f for f in body_row['faces'] if f['temp_id'] == source_face.tempId)
                    for face in matches:
                        pair = dict(converted_face_temp_id=int(face.tempId), point_comparisons=[], getter_errors=[])
                        for source_sample in source_data.get('samples', []):
                            if not source_sample or not source_sample.get('point_success'):
                                continue
                            source_point = point(*source_sample['point_cm'])
                            ok, parameter = face.evaluator.getParameterAtPoint(source_point)
                            comparison = dict(source_uv=source_sample['uv'], source_point_cm=xyz(source_point),
                                converted_parameter_success=bool(ok),
                                source_point_on_converted_face=bool(face.isPointOnFace(source_point)))
                            if ok:
                                comparison['converted_evaluation'] = read(pair['getter_errors'],
                                    'independent converted UV evaluation', lambda: evaluate(face, parameter))
                            pair['point_comparisons'].append(comparison)
                        mapping['matches'].append(pair)
                    body_row['converted_matches'].append(mapping)
            sample['result_bodies'].append(body_row)
        sample['total_deep_face_count'] = total_selected
        return sample

    def quarantine_witness(doc, phase, handles):
        # No exception or traceback is stored. Native aliases stay alive on a
        # stable SDK module if model state or cleanup is uncertain.
        retained = list(getattr(adsk.fusion, WITNESS_HALTED_ATTRIBUTE, []))
        retained.append(dict(phase=phase, document=doc, native_handles=handles))
        setattr(adsk.fusion, WITNESS_HALTED_ATTRIBUTE, retained)

    def same_api_entity(left, right):
        # The installed SWIG Base equality delegates to _core.Base___eq__
        # after a compatible Python type check. Do not compare opaque tokens.
        if (type(left) is not type(right) or not left.isValid or not right.isValid):
            return False
        return bool(adsk.core.Base.__eq__(left, right))

    def resolve_single(design, token, expected_type, doc):
        matches = None
        try:
            if not isinstance(token, str) or not token:
                raise RuntimeError('Required same-document API token is unavailable')
            matches = design.findEntityByToken(token)
            if len(matches) != 1 or not isinstance(matches[0], expected_type) or not matches[0].isValid:
                raise RuntimeError('Same-document API token did not resolve to one valid '+expected_type.__name__)
            return matches[0]
        except Exception:
            quarantine_witness(doc, 'resolve_single', dict(design=design, matches=matches))
            raise

    def create_witness(doc, source_token, witness_name, prior_source_tokens):
        design = root = offsets = source_face = source_body = entities = distance = inputs = None
        feature = input_entities = input_face = input_distance = parameter = previous = looked_up_feature = None
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            root = design.rootComponent
            offsets = root.features.offsetFeatures
            source_face = resolve_single(design, source_token, adsk.fusion.BRepFace, doc)
            source_body = source_face.body
            for previous_token in prior_source_tokens:
                previous = resolve_single(design, previous_token, adsk.fusion.BRepFace, doc)
                if same_api_entity(source_face, previous):
                    raise RuntimeError('Two witness requests resolve to the same API source face')
                previous = None
            entities = adsk.core.ObjectCollection.create()
            if not entities.add(source_face) or entities.count != 1:
                raise RuntimeError('Singleton witness source collection rejected')
            distance = adsk.core.ValueInput.createByReal(0.)
            inputs = offsets.createInput(entities, distance,
                adsk.fusion.FeatureOperations.NewBodyFeatureOperation, False)
            if inputs is None:
                raise RuntimeError('Zero-offset witness input returned null; no fallback attempted')
            input_entities = inputs.entities
            input_distance = inputs.distance
            input_face = adsk.fusion.BRepFace.cast(input_entities.item(0)) if input_entities.count == 1 else None
            input_equal = input_face is not None and same_api_entity(input_face, source_face)
            if (not input_equal or inputs.isChainSelection
                    or inputs.operation != adsk.fusion.FeatureOperations.NewBodyFeatureOperation
                    or float(input_distance.realValue) != 0.):
                raise RuntimeError('Actual zero-offset singleton witness input differs from request')
            row = dict(name=witness_name, source_face_token=source_token,
                source_API_face_temp_id=int(source_face.tempId), source_body_token=source_body.entityToken,
                source_body_name=source_body.name, source_token_resolution_count=1,
                input_entities_count=int(input_entities.count), input_entity_object_type=input_face.objectType,
                input_entity_equals_resolved_source=input_equal,
                actual_input_chain_selection=bool(inputs.isChainSelection),
                actual_input_operation=int(inputs.operation), actual_input_distance_cm=float(input_distance.realValue),
                actual_input_offset_type=int(inputs.offsetType),
                identity_scope='Native API Base equality and same-document token lookup only; no native ASM/tempId assignment')
            feature = offsets.add(inputs)
            if feature is None:
                raise RuntimeError('Zero-offset witness feature returned null; no fallback attempted')
            feature.name = witness_name
            if feature.name != witness_name or not design.computeAll() or int(feature.healthState) != 0:
                raise RuntimeError('Owned witness name/recompute/health verification failed')
            looked_up_feature = offsets.itemByName(witness_name)
            if looked_up_feature is None or not same_api_entity(feature, looked_up_feature):
                raise RuntimeError('Unique witness feature metadata lookup differs from created API feature')
            parameter = feature.distance
            row.update(feature_entity_token=feature.entityToken, feature_object_type=feature.objectType,
                feature_health_state=int(feature.healthState), feature_warning=feature.errorOrWarningMessage,
                actual_chain_selection=bool(feature.isChainSelection), actual_operation=int(feature.operation),
                actual_distance_cm=float(parameter.value), actual_offset_type=int(feature.offsetType),
                native_recipe_binding=None,
                native_binding_requirement='Unique feature metadata plus typed owned proxy/descriptor/recipe/sourceBODY and unique complete face terms; not feature name, token or tempId alone')
            if (row['actual_chain_selection'] or row['actual_operation'] != int(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
                    or row['actual_distance_cm'] != 0.):
                raise RuntimeError('Actual created witness controls differ from singleton zero-offset NewBody')
            return row
        except Exception:
            quarantine_witness(doc, 'create_witness', dict(design=design, root=root, offsets=offsets, source_face=source_face,
                source_body=source_body, entities=entities, distance=distance, inputs=inputs,
                input_entities=input_entities, input_face=input_face, input_distance=input_distance,
                parameter=parameter, previous=previous,
                feature=feature, looked_up_feature=looked_up_feature))
            raise

    def read_rolled_witness(doc, feature_token, source_token):
        design = feature = timeline_object = source_face = selected = selected_face = None
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            feature = resolve_single(design, feature_token, adsk.fusion.OffsetFeature, doc)
            timeline_object = feature.timelineObject
            if not timeline_object.rollTo(True):
                raise RuntimeError('Witness rollback before node returned false')
            # Resolve the same source token in the documented getter state.
            source_face = resolve_single(design, source_token, adsk.fusion.BRepFace, doc)
            selected = feature.entities
            selected_face = adsk.fusion.BRepFace.cast(selected.item(0)) if selected.count == 1 else None
            equal = selected_face is not None and same_api_entity(selected_face, source_face)
            if not equal:
                raise RuntimeError('Rolled witness singleton entities do not equal the API-resolved source face')
            return dict(rolled_before_node=True, entities_count=int(selected.count),
                entity_object_type=selected_face.objectType, entity_equals_resolved_source=equal,
                identity_method='adsk.core.Base.__eq__; no token-string or tempId comparison',
                marker_position=int(design.timeline.markerPosition),
                scope='Actual Offset input readback in the documented pre-node state only')
        except Exception:
            quarantine_witness(doc, 'read_rolled_witness', dict(design=design, feature=feature,
                timeline_object=timeline_object, source_face=source_face,
                selected=selected, selected_face=selected_face))
            raise

    def restore_after_witness(doc):
        design = timeline = None
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            timeline = design.timeline
            if not timeline.moveToEnd() or not design.computeAll():
                raise RuntimeError('Witness timeline restoration/recompute failed')
            return dict(moved_to_end=True, compute_completed=True, marker_position=int(timeline.markerPosition))
        except Exception:
            quarantine_witness(doc, 'restore_after_witness', dict(design=design, timeline=timeline))
            raise

    def finalize(doc, destination):
        design = manager = options = None
        try:
            design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
            if not design.computeAll():
                raise RuntimeError('Post-release owned recompute failed')
            manager = design.exportManager
            options = manager.createFusionArchiveExportOptions(str(destination))
            return bool(manager.execute(options))
        except Exception:
            quarantine_witness(doc, 'finalize', dict(design=design, manager=manager, options=options))
            raise

    journal('batch_begin')
    for case, offset in CASES:
        doc = None
        sample = None
        try:
            journal('creating_owned_document', case)
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            sample = populate(doc, case, offset)
            sample['populate_frame_gc_collected'] = gc.collect()
            journal('wrappers_released_before_export', case)
            if not finalize(doc, folder / sample['file']):
                raise RuntimeError('Owned archive export returned false')
            sample['finalize_frame_gc_collected'] = gc.collect()
            sample['archive_sha256'] = hashlib.sha256((folder / sample['file']).read_bytes()).hexdigest()
            sample['archive_size_bytes'] = (folder / sample['file']).stat().st_size
            sample['pre_witness_archive_scope'] = 'Original Rule source and temporary-conversion observations; no witness feature existed at export'
            truth['samples'].append(sample)
            journal('pre_witness_export_complete', case, file=sample['file'], sha256=sample['archive_sha256'])
            requests = [dict(source_face_token=face['entity_token'],
                             source_API_face_temp_id=face['temp_id'])
                        for body in sample['result_bodies'] for face in body['faces']
                        if face['temp_id'] in body['deep_face_temp_ids']]
            if not 0 < len(requests) <= MAX_WITNESSES_PER_CASE:
                raise RuntimeError('Witness requests outside one-to-eight per-case bound')
            sample['witnesses'] = []
            prior_tokens = []
            for ordinal, request in enumerate(requests):
                witness_name = 'WitnessRuleSurface_'+case+'_'+str(ordinal)
                journal('creating_face_witness', case, witness_ordinal=ordinal)
                witness = create_witness(doc, request['source_face_token'], witness_name, prior_tokens)
                sample['witnesses'].append(witness)
                witness['create_frame_gc_collected'] = gc.collect()
                journal('witness_create_wrappers_released', case, witness_ordinal=ordinal)
                witness['rolled_input'] = read_rolled_witness(doc, witness['feature_entity_token'], request['source_face_token'])
                witness['rolled_getter_frame_gc_collected_before_restore'] = gc.collect()
                journal('witness_rolled_wrappers_released_before_restore', case, witness_ordinal=ordinal)
                witness['restoration'] = restore_after_witness(doc)
                witness['restoration_frame_gc_collected'] = gc.collect()
                prior_tokens.append(request['source_face_token'])
                journal('witness_restored', case, witness_ordinal=ordinal)
            witness_file = case+'_witnesses.f3d'
            if not finalize(doc, folder / witness_file):
                raise RuntimeError('Owned witness archive export returned false')
            sample['witness_finalize_frame_gc_collected'] = gc.collect()
            sample['witness_archive'] = dict(file=witness_file,
                sha256=hashlib.sha256((folder / witness_file).read_bytes()).hexdigest(),
                size_bytes=(folder / witness_file).stat().st_size,
                witness_count=len(sample['witnesses']),
                scope='Additional singleton Offset consumers only; typed native source/VBL association remains pending offline qualification')
            if hashlib.sha256((folder / sample['file']).read_bytes()).hexdigest() != sample['archive_sha256']:
                raise RuntimeError('Original pre-witness archive bytes changed')
            sample['pre_witness_archive_hash_unchanged'] = True
            journal('witness_export_complete', case, file=witness_file, witness_count=len(sample['witnesses']))
            sample['close_owned_document_returned'] = bool(doc.close(False))
            if not sample['close_owned_document_returned']:
                raise RuntimeError('Owned close(False) returned false')
            doc = None
            journal('owned_document_closed', case)
        except Exception as error:
            truth['errors'].append(dict(case=case, error_type=type(error).__name__, error=str(error),
                owned_document_retained=doc is not None, automatic_retry=False,
                pre_witness_archive_preserved=sample is not None and (folder / sample['file']).is_file(),
                native_witness_handles_quarantined=bool(getattr(adsk.fusion, WITNESS_HALTED_ATTRIBUTE, None))))
            if doc is not None:
                retained = list(getattr(adsk.fusion, HALTED_ATTRIBUTE, []))
                retained.append(doc)
                setattr(adsk.fusion, HALTED_ATTRIBUTE, retained)
            journal('batch_halted', case)
            (folder / 'halted.txt').write_text('Owned document retained; inspect error. No retry or further case.\n')
            return
    journal('batch_complete')
    (folder / 'complete.txt').write_text('Complete; inspect actual truth and journal.\n')
