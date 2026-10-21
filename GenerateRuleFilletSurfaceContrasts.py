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
CASES = (('offsets_one_two', '2 mm'), ('offsets_one_three', '3 mm'))


def run(context):
    if (getattr(adsk.fusion, HALTED_ATTRIBUTE, None)
            or getattr(adsk.fusion, '_codex_FusionFileStudy_surface_trim_halted_native_handles', None)):
        raise RuntimeError('Prior owned native handles remain quarantined; no capture started')
    app = adsk.core.Application.get()
    source = Path(__file__).resolve()
    folder = source.parent / ('rulefilletsurfaces-' + uuid.uuid4().hex[:12])
    folder.mkdir()
    executed = source.read_bytes()
    (folder / 'executed-generator-source.txt').write_bytes(executed)
    sdk_sources, sdk_hashes = [], {}
    for module, names in ((adsk.core, ('SurfaceEvaluator', 'NurbsSurface', 'Point3DVector')),
                          (adsk.fusion, ('BRepBody', 'BRepFace', 'BRepConvertOptions',
                                         'FilletFeatures', 'RuleFilletFeatureInput'))):
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
        for body in feature.bodies:
            body_row = dict(name=body.name, entity_token=body.entityToken, is_temporary=bool(body.isTemporary),
                volume_cm3=float(body.volume), face_count=body.faces.count, edge_count=body.edges.count,
                faces=[], conversion_option=int(adsk.fusion.BRepConvertOptions.ProceduralToNURBSConversion),
                converted_faces=[], converted_matches=[], getter_errors=[])
            selected = [f for f in body.faces if f.loops.count == 1 and f.edges.count == 6]
            body_row['deep_face_temp_ids'] = [int(f.tempId) for f in selected]
            body_row['deep_scope'] = 'All single-loop six-edge API faces; topology signature is not a native face assignment'
            if len(selected) > 8:
                raise RuntimeError('Six-edge face capture exceeds reviewed eight-face bound')
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
        return sample

    def finalize(doc, destination):
        design = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
        if not design.computeAll():
            raise RuntimeError('Post-release owned recompute failed')
        return bool(design.exportManager.execute(design.exportManager.createFusionArchiveExportOptions(str(destination))))

    journal('batch_begin')
    for case, offset in CASES:
        doc = None
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
            truth['samples'].append(sample)
            journal('export_complete', case)
            sample['close_owned_document_returned'] = bool(doc.close(False))
            if not sample['close_owned_document_returned']:
                raise RuntimeError('Owned close(False) returned false')
            doc = None
            journal('owned_document_closed', case)
        except Exception as error:
            truth['errors'].append(dict(case=case, error_type=type(error).__name__, error=str(error),
                owned_document_retained=doc is not None, automatic_retry=False))
            if doc is not None:
                retained = list(getattr(adsk.fusion, HALTED_ATTRIBUTE, []))
                retained.append(doc)
                setattr(adsk.fusion, HALTED_ATTRIBUTE, retained)
            journal('batch_halted', case)
            (folder / 'halted.txt').write_text('Owned document retained; inspect error. No retry or further case.\n')
            return
    journal('batch_complete')
    (folder / 'complete.txt').write_text('Complete; inspect actual truth and journal.\n')
