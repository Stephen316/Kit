"""Prepared three-case selected-profile trim capture; never dispatches itself.

ProfileCurve.geometry is the documented geometric portion, while sketchEntity
identifies its underlying source. Geometry selects the requested capture region
only; native tag/trim identity requires later inspection of actual exports.
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

CASES = ('circle_lens', 'circle_right_complement', 'rectangle_overlap')
OUTPUT_PREFIX = 'trimmedprofiles-'


def run(context):
    app = adsk.core.Application.get()
    specs=context.get('case_specs') if isinstance(context,dict) else None
    prefix=context.get('output_prefix',OUTPUT_PREFIX) if isinstance(context,dict) else OUTPUT_PREFIX
    if not isinstance(prefix,str) or not prefix or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in prefix):
        raise ValueError('Capture prefix must be one bounded local directory name')
    if specs is not None:
        if not isinstance(specs,dict) or not 1<=len(specs)<=4:
            raise ValueError('Expected one to four bounded trim-selector case specifications')
        for name,spec in specs.items():
            if not isinstance(name,str) or not name or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_' for c in name):
                raise ValueError('Unsupported trim-selector case name')
            if not isinstance(spec,dict) or ('circles' in spec)==('rectangles' in spec):
                raise ValueError('Expected exactly one controlled source geometry family')
            if 'circles' in spec:
                circles=spec['circles']
                invalid_geometry=(not 2<=len(circles)<=3 or any(len(circle)!=3 or not all(math.isfinite(v) for v in circle)
                                  or circle[2]<=0 for circle in circles))
            else:
                rectangles=spec['rectangles']
                invalid_geometry=(len(rectangles)!=2 or any(len(rectangle)!=4 or not all(math.isfinite(v) for v in rectangle)
                                  or rectangle[0]>=rectangle[2] or rectangle[1]>=rectangle[3] for rectangle in rectangles))
            if (invalid_geometry or spec['selection'] not in ('min_area','max_area','max_centroid_x')
                    or not 1<=spec['expected_profile_count']<=16):
                raise ValueError('Unobserved or invalid controlled trim-selector input')
    output = Path(__file__).resolve().parent / (prefix + uuid.uuid4().hex[:12])
    output.mkdir()
    generator_source=Path(__file__).read_bytes()
    (output/'executed-generator-source.txt').write_bytes(generator_source)
    cases = [case for case in (specs if specs is not None else CASES)
             if not isinstance(context, dict) or 'cases' not in context or case in context['cases']]
    truth = {'fusion_version': app.version, 'samples': [], 'errors': [],
             'planned_cases': list(specs) if specs is not None else list(CASES),
             'executed_generator_sha256': hashlib.sha256(generator_source).hexdigest(),
             'scope': ('Three owned local documents, independent archive exports, close(False); no cloud saves.' if specs is None
                       else str(len(cases))+' owned local documents, independent archive exports, close(False); no cloud saves.'),
             'identity_scope': 'Direct API sketchEntity equality supplies source array indices. Tokens are opaque evidence; they are not parsed as native IDs. Native profile references await actual saved-file inspection.',
             'geometry_scope': 'ProfileCurve.geometry and its evaluator describe the actual profile portion; source SketchCircle/SketchLine geometry is recorded separately. Profile region choice uses area/centroid only in this generator.',
             'capture_status': 'running'}

    def persist():
        (output / 'ground_truth.json').write_text(json.dumps(truth, indent=2)+'\n')

    def journal(phase, case=None, **fields):
        event = {'time_utc': datetime.now(timezone.utc).isoformat(), 'phase': phase,
                 'case': case, 'sample_count': len(truth['samples']),
                 'error_count': len(truth['errors']), **fields}
        with (output / 'journal.jsonl').open('a') as stream:
            stream.write(json.dumps(event)+'\n')
        (output / 'progress.json').write_text(json.dumps(event, indent=2)+'\n')
        persist()

    def observe(label, getter, errors):
        try:
            return getter()
        except Exception:
            errors.append({'getter': label, 'error': traceback.format_exc()})
            return None

    def serial(value):
        if value is None or isinstance(value, (str, bool, int, float)):
            return value
        if hasattr(value, 'asArray'):
            return list(value.asArray())
        return [serial(item) for item in value]

    def items(collection):
        return [collection.item(i) for i in range(collection.count)]

    def geometry_truth(geometry):
        errors = []
        result = {'getter_errors': errors}
        if geometry is None:
            result['geometry_missing'] = True
            return result
        result['object_type'] = observe('objectType', lambda: geometry.objectType, errors)
        result['data'] = observe('getData', lambda: serial(geometry.getData()), errors)
        evaluator = observe('evaluator', lambda: geometry.evaluator, errors)
        if evaluator is not None:
            bounds = observe('evaluator.getParameterExtents', lambda: serial(evaluator.getParameterExtents()), errors)
            result['parameter_extents'] = bounds
            if bounds and bounds[0] and len(bounds) == 3:
                start, end = bounds[1:]
                result['evaluated_points'] = []
                for role, parameter in (('start', start), ('midpoint', (start+end)/2), ('end', end)):
                    point_result = observe('evaluator.getPointAtParameter.'+role,
                                           lambda parameter=parameter: serial(evaluator.getPointAtParameter(parameter)), errors)
                    result['evaluated_points'].append({'role': role, 'parameter': parameter, 'result_cm': point_result})
        return result

    def source_truth(entity, index):
        errors = []
        return {'source_index': index, 'object_type': observe('objectType', lambda: entity.objectType, errors),
                'entity_token': observe('entityToken', lambda: entity.entityToken, errors),
                'is_reference': observe('isReference', lambda: entity.isReference, errors),
                'is_construction': observe('isConstruction', lambda: entity.isConstruction, errors),
                'full_sketch_geometry': geometry_truth(observe('geometry', lambda: entity.geometry, errors)),
                'getter_errors': errors}

    def profile_truth(profile, sources):
        errors = []
        result = {'getter_errors': errors, 'loops': []}
        result['entity_token'] = observe('entityToken', lambda: profile.entityToken, errors)
        properties = observe('areaProperties', lambda: profile.areaProperties(), errors)
        if properties is not None:
            result['area_cm2'] = observe('areaProperties.area', lambda: properties.area, errors)
            result['centroid_cm'] = observe('areaProperties.centroid', lambda: serial(properties.centroid), errors)
        loops = observe('profileLoops', lambda: items(profile.profileLoops), errors)
        for loop_index, loop in enumerate(loops or []):
            row = {'loop_index': loop_index, 'getter_errors': [], 'curves': []}
            row['is_outer'] = observe('isOuter', lambda: loop.isOuter, row['getter_errors'])
            curves = observe('profileCurves', lambda: items(loop.profileCurves), row['getter_errors'])
            for curve_index, curve in enumerate(curves or []):
                entry = {'curve_index': curve_index, 'getter_errors': []}
                source = observe('sketchEntity', lambda: curve.sketchEntity, entry['getter_errors'])
                entry['source_indices_by_api_equality'] = observe(
                    'sketchEntity equality', lambda: [i for i, candidate in enumerate(sources) if candidate == source], entry['getter_errors'])
                entry['underlying_sketch_entity_token'] = observe('sketchEntity.entityToken', lambda: source.entityToken, entry['getter_errors'])
                entry['underlying_sketch_entity_type'] = observe('sketchEntity.objectType', lambda: source.objectType, entry['getter_errors'])
                entry['geometry_type'] = observe('geometryType', lambda: int(curve.geometryType), entry['getter_errors'])
                entry['portion_geometry'] = geometry_truth(observe('geometry', lambda: curve.geometry, entry['getter_errors']))
                row['curves'].append(entry)
            result['loops'].append(row)
        return result

    journal('batch_begin', planned_sample_count=len(cases))
    for case in cases:
        document = None
        try:
            journal('document_create_begin', case)
            document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            journal('document_created', case)
            design = adsk.fusion.Design.cast(document.products.itemByProductType('DesignProductType'))
            if design is None:
                raise RuntimeError('Owned document lacks Fusion Design')
            design.designType = adsk.fusion.DesignTypes.ParametricDesignType
            component = design.rootComponent
            sketch = component.sketches.add(component.xYConstructionPlane)
            sketch.name = 'TrimmedProfileSources'
            point = adsk.core.Point3D.create
            if specs is not None:
                spec=specs[case]
                for cx,cy,radius in spec.get('circles',[]):
                    sketch.sketchCurves.sketchCircles.addByCenterRadius(point(cx,cy,0),radius)
                for xmin,ymin,xmax,ymax in spec.get('rectangles',[]):
                    sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(xmin,ymin,0),point(xmax,ymax,0))
                requested={'controlled_specification':spec}
            elif case.startswith('circle_'):
                sketch.sketchCurves.sketchCircles.addByCenterRadius(point(-1, 0, 0), 2)
                sketch.sketchCurves.sketchCircles.addByCenterRadius(point(1, 0, 0), 2)
                requested = {'sources': 'Two radius-2cm circles centered at(-1,0) and(1,0)',
                             'selection': 'Minimum area lens' if case == 'circle_lens' else 'Maximum centroid-X complementary crescent'}
            else:
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(0, 0, 0), point(4, 3, 0))
                sketch.sketchCurves.sketchLines.addTwoPointRectangle(point(2, -1, 0), point(5, 2, 0))
                requested = {'sources': 'Rectangles [0,0]-[4,3] and[2,-1]-[5,2]cm',
                             'selection': 'Minimum area overlap [2,0]-[4,2]cm; four truncated source Lines'}
            if not design.computeAll():
                raise RuntimeError('Source computeAll returned false')
            sources = items(sketch.sketchCurves)
            candidates = items(sketch.profiles)
            expected_count=specs[case]['expected_profile_count'] if specs is not None else 3
            if len(candidates) != expected_count:
                raise RuntimeError('Expected '+str(expected_count)+' intersection regions; got '+str(len(candidates)))
            properties = [profile.areaProperties() for profile in candidates]
            selection=specs[case]['selection'] if specs is not None else ('max_centroid_x' if case=='circle_right_complement' else 'min_area')
            if selection=='max_centroid_x':
                selected_index = max(range(len(candidates)), key=lambda i: properties[i].centroid.x)
            elif selection=='max_area':
                selected_index = max(range(len(candidates)), key=lambda i: properties[i].area)
            else:
                selected_index = min(range(len(candidates)), key=lambda i: properties[i].area)
            selected = candidates[selected_index]
            sample = {'case': case, 'file': case+'.f3d', 'requested': requested,
                      'getter_errors': [], 'sketch_name': sketch.name,
                      'source_curves': [source_truth(entity, i) for i, entity in enumerate(sources)],
                      'available_profile_count': len(candidates), 'selected_candidate_index': selected_index,
                      'candidate_profiles': [profile_truth(profile, sources) for profile in candidates]}
            # Truth is captured while profiles are valid, before creating their consumer.
            sample['selected_profile'] = sample['candidate_profiles'][selected_index]
            truth['active_sample'] = sample
            journal('profile_truth_captured', case)
            feature = component.features.extrudeFeatures.addSimple(
                selected, adsk.core.ValueInput.createByString('10 mm'),
                adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            feature.name = 'SelectedTrimmedProfile'
            sample['feature_name'] = feature.name
            if not design.computeAll():
                raise RuntimeError('Extrude computeAll returned false')
            design.timeline.moveToEnd()
            sample['timeline_marker'] = observe('timeline.markerPosition', lambda: design.timeline.markerPosition, sample['getter_errors'])
            sample['timeline_count'] = observe('timeline.count', lambda: design.timeline.count, sample['getter_errors'])
            sample['post_feature_source_curves'] = [source_truth(entity, i) for i, entity in enumerate(items(sketch.sketchCurves))]
            sample['result_bodies'] = []
            for body in items(feature.bodies):
                sample['result_bodies'].append({
                    'volume_cm3': observe('body.volume', lambda: body.volume, sample['getter_errors']),
                    'bounds_cm': observe('body.boundingBox', lambda: [serial(body.boundingBox.minPoint), serial(body.boundingBox.maxPoint)], sample['getter_errors'])})
            destination = output / sample['file']
            journal('export_begin', case, file=sample['file'])
            options = design.exportManager.createFusionArchiveExportOptions(str(destination))
            succeeded = design.exportManager.execute(options)
            if not succeeded or not destination.is_file() or not destination.stat().st_size:
                raise RuntimeError('Local archive export failed')
            sample['export'] = {'returned_success': bool(succeeded), 'size_bytes': destination.stat().st_size,
                                'sha256': hashlib.sha256(destination.read_bytes()).hexdigest()}
            truth['samples'].append(sample)
            truth.pop('active_sample', None)
            journal('export_complete', case, file=sample['file'])
        except Exception:
            truth['errors'].append({'case': case, 'error': traceback.format_exc(),
                                    'active_sample': truth.pop('active_sample', None)})
            journal('case_failed', case)
        finally:
            if document is not None:
                try:
                    closed=document.close(False)
                    journal('owned_document_close_returned', case, returned=closed, save=False)
                except Exception:
                    truth['errors'].append({'case': case, 'phase': 'close_owned_document', 'error': traceback.format_exc()})
                    journal('close_failed', case)
    truth['capture_status'] = 'complete_with_errors' if truth['errors'] else 'complete'
    journal('batch_complete', status=truth['capture_status'])
    (output / 'complete.txt').write_text('Terminal batch; inspect ground_truth.json errors and actual exports.\n')
