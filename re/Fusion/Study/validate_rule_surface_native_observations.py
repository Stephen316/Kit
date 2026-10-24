"""Offline Rule surface observations; API/native FACE identity stays unproved.

This reads saved capture JSON and archives only. The API getData grids are
evaluated independently of their saved face evaluators; no geometric comparison
selects an ASM face or promotes a procedural surface to an exact XYZ evaluator.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

from asm_records import inspect_asm
from decode_asm_subtypes import decode_asm_subtypes
from decode_brep import decode_topology
from decode_bspline import evaluate_surface
from decode_vbl_components import decode_vbl_components
from fusion_archive import read_members

ROOT = Path(__file__).resolve().parent
CAPTURE = 'rulefilletsurfaces-9dd46198ca8a'
VBL_REASON = 'VBL component definitions decoded; standalone XYZ surface evaluator remains unsupported'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def grid_comparison(face):
    """Use the established tensor convention; retain every saved observation."""
    data = face['nurbs_data']
    if not (data['available'] and data['success'] and data['tuple_length'] == 11):
        raise ValueError('Successful actual NurbsSurface.getData observation required')
    nu, nv = data['count_u'], data['count_v']
    if (type(nu) is not int or type(nv) is not int or not 1 <= nu * nv <= 250000
            or len(data['control_points_cm']) != nu * nv):
        raise ValueError('Actual NURBS control counts/array disagree')
    for axis, count in (('u', nu), ('v', nv)):
        degree, knots = data['degree_' + axis], data['knots_' + axis]
        if (type(degree) is not int or not 1 <= degree < count
                or len(knots) != count + degree + 1
                or any(not math.isfinite(x) for x in knots)
                or any(a > b for a, b in zip(knots, knots[1:]))):
            raise ValueError('Actual NURBS knot/degree/count framing differs')
    values = [v for p in data['control_points_cm'] for v in p] + data['weights']
    if (any(len(p) != 3 for p in data['control_points_cm'])
            or any(not math.isfinite(x) for x in values)
            or data['weights'] and (len(data['weights']) != nu * nv
                                     or any(w <= 0 for w in data['weights']))):
        raise ValueError('Actual NURBS control/weight data is invalid')
    cache = dict(degree_u=data['degree_u'], degree_v=data['degree_v'],
        control_count_u=nu, control_count_v=nv, knots_u=data['knots_u'], knots_v=data['knots_v'],
        weights=data['weights'], raw_control_points=data['control_points_cm'],
        parameter_domain_u=[data['knots_u'][data['degree_u']], data['knots_u'][-data['degree_u']-1]],
        parameter_domain_v=[data['knots_v'][data['degree_v']], data['knots_v'][-data['degree_v']-1]])
    evaluations = []
    for observation in face['samples']:
        if not (observation and observation['is_parameter_on_face']
                and observation['point_success'] and observation['derivative_success']):
            raise ValueError('Captured deep face sample is not a successful on-face observation')
        numeric = observation['uv'] + observation['point_cm'] + observation['partial_u'] + observation['partial_v']
        if any(not math.isfinite(x) for x in numeric):
            raise ValueError('Captured face evaluator data is not finite')
        predicted = evaluate_surface(cache, *observation['uv'])
        residual = math.dist(predicted, observation['point_cm'])
        if any(not math.isfinite(x) for x in predicted) or not math.isfinite(residual):
            raise ValueError('Derived tensor evaluation is not finite')
        evaluations.append(dict(actual_face_evaluator=observation,
            independently_evaluated_getData_grid_cm=predicted, residual_cm=residual))
    return dict(API_face_temp_id=face['temp_id'], API_geometry_object_type=face['geometry_object_type'],
        degree_u=data['degree_u'], degree_v=data['degree_v'], count_u=nu, count_v=nv,
        knot_count_u=len(data['knots_u']), knot_count_v=len(data['knots_v']),
        knot_domain_u=cache['parameter_domain_u'], knot_domain_v=cache['parameter_domain_v'],
        weight_count=len(data['weights']), properties_u=data['properties_u'], properties_v=data['properties_v'],
        actual_face_parameter_range=face['parameter_range'], evaluations=evaluations,
        source_control_array_sha256=hashlib.sha256(json.dumps(data, sort_keys=True, allow_nan=False).encode()).hexdigest(),
        control_order_scope='Existing tensor convention checked against converted API grids; no native VBL tensor/control correspondence',
        native_FACE_assignment=None)


def validate(zstd, capture=CAPTURE):
    folder = ROOT / capture
    truth = json.loads((folder / 'ground_truth.json').read_text())
    journal = [json.loads(line) for line in (folder / 'journal.jsonl').read_text().splitlines() if line]
    progress = json.loads((folder / 'progress.json').read_text())
    checks = []
    def check(label, value):
        if not value:
            raise AssertionError(label)
        checks.append(label)
    check('Executed generator snapshot hash matches saved provenance',
          digest(folder / 'executed-generator-source.txt') == truth['executed_generator_sha256'])
    check('Executed SDK surface snapshot hash matches saved provenance',
          digest(folder / 'executed-sdk-surface.txt') == truth['executed_sdk_surface_sha256'])
    sdk = []
    for path, expected in truth['sdk_runtime_sha256'].items():
        actual = digest(path)
        check('Installed SDK file matches capture hash: ' + Path(path).name, actual == expected)
        sdk.append(dict(path=path, captured_sha256=expected, independently_read_sha256=actual))
    terminal = journal[-1]
    check('Progress exactly matches terminal journal event', progress == terminal)
    phase = terminal['phase']
    check('Capture has an explicit halted or complete terminal event', phase in ('batch_halted', 'batch_complete'))
    if phase == 'batch_halted':
        check('Halted marker exists and complete marker is absent',
              (folder / 'halted.txt').is_file() and not (folder / 'complete.txt').exists())
        check('Halt retains actual errors and does not claim all planned cases',
              bool(truth['errors']) and len(truth['samples']) < len(truth['planned_cases']))
    else:
        check('Complete capture has complete marker and no case errors',
              (folder / 'complete.txt').is_file() and not truth['errors']
              and len(truth['samples']) == len(truth['planned_cases']))
    samples = []
    totals = Counter()
    direct_errors, converted_errors = [], []
    for sample in truth['samples']:
        archive = folder / sample['file']
        exports = [row for row in journal if row['phase'] == 'pre_witness_export_complete'
                   and row.get('file') == sample['file']]
        check(sample['file'] + ' exact healthy pre-witness archive/export proof',
              sample['feature_health_state'] == 0 and sample['feature_warning'] == ''
              and not sample['getter_errors'] and len(exports) == 1
              and digest(archive) == sample['archive_sha256'] == exports[0]['sha256']
              and archive.stat().st_size == sample['archive_size_bytes'])
        bodies = []
        for body in sample['result_bodies']:
            check(sample['file'] + ' owned source and temporary conversion flags',
                  body['is_temporary'] is False and body['conversion_returned_body'] is True
                  and body['converted_is_temporary'] is True and body['conversion_option'] == 0
                  and not body['getter_errors'] and len(body['faces']) == body['face_count']
                  and len(body['converted_faces']) == body['converted_face_count'])
            deep = [face for face in body['faces'] if 'nurbs_data' in face]
            converted = [face for face in body['converted_faces'] if 'nurbs_data' in face]
            check(sample['file'] + ' exact deep API face selection, not native assignment',
                  len(deep) == 8 and {f['temp_id'] for f in deep} == set(body['deep_face_temp_ids'])
                  and all(f['edge_count'] == 6 and f['loop_count'] == 1 for f in deep))
            check(sample['file'] + ' all recorded face getter errors absent',
                  all(not f['getter_errors'] for f in body['faces'] + body['converted_faces']))
            direct = [grid_comparison(face) for face in deep]
            converted_grids = [grid_comparison(face) for face in converted]
            de = [e['residual_cm'] for face in direct for e in face['evaluations']]
            ce = [e['residual_cm'] for face in converted_grids for e in face['evaluations']]
            check(sample['file'] + ' direct grid differs from actual face evaluator at every saved interior sample',
                  len(de) == 24 and all(x > 1e-8 for x in de))
            check(sample['file'] + ' converted own-grid control validates tensor convention',
                  len(ce) == 144 and max(ce) < 1e-10)
            projections = []
            for match in body['converted_matches']:
                check(sample['file'] + ' API conversion retains all six temporary matches',
                      match['match_count'] == len(match['matches']) == 6)
                for target in match['matches']:
                    check('Temporary match getter errors absent', not target['getter_errors'])
                    for observation in target['point_comparisons']:
                        evaluated = observation['converted_evaluation']
                        check('Projection success and on-parameter status do not imply source point lies on converted face',
                              observation['converted_parameter_success'] is True
                              and observation['source_point_on_converted_face'] is False
                              and evaluated['is_parameter_on_face'] is True
                              and evaluated['point_success'] is True and evaluated['derivative_success'] is True)
                        residual = math.dist(observation['source_point_cm'], evaluated['point_cm'])
                        check('Projection comparison is finite', math.isfinite(residual))
                        projections.append(dict(source_API_face_temp_id=match['source_face_temp_id'],
                            converted_API_face_temp_id=target['converted_face_temp_id'],
                            actual=observation, projection_residual_cm=residual,
                            native_FACE_assignment=None))
            check(sample['file'] + ' exactly 144 independent API projection observations', len(projections) == 144)
            direct_errors.extend(de); converted_errors.extend(ce)
            totals.update(source_API_faces=body['face_count'], deep_API_faces=len(deep),
                converted_API_faces=body['converted_face_count'], converted_deep_faces=len(converted),
                direct_interior_samples=len(de), converted_own_grid_samples=len(ce),
                conversion_matches=sum(m['match_count'] for m in body['converted_matches']),
                projected_evaluations=len(projections), source_point_on_converted_face_false=len(projections))
            bodies.append(dict(name=body['name'], actual_source_face_count=body['face_count'],
                actual_converted_face_count=body['converted_face_count'],
                actual_source_classes=[dict(surface_type=k[0], geometry_object_type=k[1], count=n)
                    for k, n in sorted(Counter((f['surface_type'], f['geometry_object_type']) for f in body['faces']).items())],
                direct_API_grid_comparisons=direct, converted_API_own_grid_controls=converted_grids,
                converted_API_projections=projections, native_FACE_assignment=None))
        native = []
        for member, blob in read_members(archive, zstd).items():
            if not member.endswith(('.smb', '.smbh')):
                continue
            parsed = inspect_asm(blob)
            catalog = decode_asm_subtypes(blob, parsed=parsed)
            topology = decode_topology(parsed, subtype_catalog=catalog)
            vbl = decode_vbl_components(blob, parsed=parsed, subtype_catalog=catalog, topology=topology)
            diagnostics = topology['unresolved']
            check(member + ' every native unresolved surface diagnostic retained',
                  len(diagnostics) == len(vbl['decoded']) and not vbl['unresolved']
                  and all(row['reason'] == VBL_REASON for row in diagnostics))
            check(member + ' no VBL interior evaluator introduced',
                  all(row['VBL_interior_geometry'] is None and row['stored_component_count'] == 6
                      for row in vbl['decoded']))
            native.append(dict(member=member, blob_sha256=hashlib.sha256(blob).hexdigest(),
                exact_native_surface_diagnostics=diagnostics,
                decoded_component_boundaries=[dict(surface_record_index=r['surface_record_index'],
                    face_record_index=r['face_index'], loop_record_index=r['loop_index'],
                    component_count=r['stored_component_count'],
                    raw_surface_subtype=parsed['records'][r['surface_record_index']]['tokens'][5]['value'],
                    VBL_interior_geometry=None, API_face_assignment=None) for r in vbl['decoded']]))
            totals['native_VBL_interior_diagnostics'] += len(diagnostics)
        check(sample['file'] + ' eight native VBL diagnostics remain independent of eight API deep faces',
              sum(len(row['exact_native_surface_diagnostics']) for row in native) == 8)
        samples.append(dict(archive=str(archive.relative_to(ROOT)), archive_sha256=digest(archive),
            actual_feature_health_state=sample['feature_health_state'], actual_warning=sample['feature_warning'],
            actual_pre_witness_export_event=exports[0], actual_requested_offsets=sample['requested_offsets'],
            actual_parameters=sample['parameters'], actual_recorded_witness_count=len(sample.get('witnesses', [])),
            witness_archive_recorded=sample.get('witness_archive'),
            native_API_FACE_mapping='UNPROVEN', body_observations=bodies, native_blob_observations=native))
    check('At least one actual exported sample exists', bool(samples))
    inputs = ['ground_truth.json', 'journal.jsonl', 'progress.json', 'executed-generator-source.txt', 'executed-sdk-surface.txt']
    inputs += [name for name in ('halted.txt', 'complete.txt') if (folder / name).is_file()]
    return dict(capture=capture, execution_status='HaltedAfterPreWitnessExport' if phase == 'batch_halted' else 'CompleteAsRecorded',
        actual_terminal_event=terminal, actual_errors=truth['errors'], planned_cases=truth['planned_cases'],
        actual_point_tolerance_cm=truth['point_tolerance_cm'], captured_fusion_version=truth['fusion_version'],
        input_sha256={name:digest(folder / name) for name in inputs}, SDK_runtime_provenance=sdk,
        executed_generator_sha256=truth['executed_generator_sha256'],
        executed_sdk_surface_sha256=truth['executed_sdk_surface_sha256'], samples=samples,
        checks=checks, validation=dict(totals, exported_samples=len(samples), check_count=len(checks),
            direct_grid_residual_range_cm=[min(direct_errors), max(direct_errors)],
            converted_own_grid_residual_range_cm=[min(converted_errors), max(converted_errors)],
            native_API_FACE_mapping='UNPROVEN', new_native_VBL_evaluators=0, main_runs=0, live_calls=0),
        source_sha256={name:digest(ROOT / name) for name in ('validate_rule_surface_native_observations.py',
            'decode_bspline.py', 'decode_nurbs.py', 'asm_records.py', 'decode_asm_subtypes.py',
            'decode_brep.py', 'decode_vbl_components.py')},
        limitations=['Direct API NurbsSurface class/getData success does not prove equality to the direct BRepFace evaluator; every captured interior comparison disagrees.',
            'Converted own-grid controls validate the numerical tensor convention only within converted API faces.',
            'Successful getParameterAtPoint and isParameterOnFace concern projected parameters; they do not contradict the separately false isPointOnFace(source point) observations.',
            'API tempId/findByTempId labels describe temporary conversion relationships only. No native FACE is selected by labels, coordinates, order, bounds or nearest geometry.',
            'Native VBL component boundaries and eight interior diagnostics remain unchanged; no standalone VBL XYZ evaluator or native/API surface identity is established.',
            'The original partial capture halted before a witness was recorded. Its healthy source export is not a completed batch or successful owned close.',
            'Later capture folders, witness archives and procedural semantics require separate evidence; this validator creates no inferred manifest.'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture', default=CAPTURE)
    parser.add_argument('--zstd')
    parser.add_argument('--output', default='rule-surface-native-observations.json')
    args = parser.parse_args()
    zstd = args.zstd or str(next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib')))
    result = validate(zstd, args.capture)
    Path(args.output).write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(result['validation'], sort_keys=True))
