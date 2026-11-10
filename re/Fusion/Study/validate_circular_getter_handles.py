"""Actual import readback: retained/fresh/reverse PatternElement getter proof."""
import hashlib
from itertools import product
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAPTURE = 'circulargetterhandles-4240ab8c3e99/ground_truth.json'


def _near(a, b, tol=1e-9):
    return len(a) == len(b) and all(abs(x-y) <= tol for x, y in zip(a, b))


def _bounds(flat):
    return [v for field in ('min', 'max') for v in flat[field]]


def _transformed_bounds(bounds, matrix):
    corners = product(*zip(bounds['min'], bounds['max']))
    points = [[sum(matrix[4*r+c]*p[c] for c in range(3))+matrix[4*r+3] for r in range(3)] for p in corners]
    return [min(p[k] for p in points) for k in range(3)]+[max(p[k] for p in points) for k in range(3)]


def _rotation(theta):
    c, s = math.cos(theta), math.sin(theta)
    return [c,-s,0.,0.,s,c,0.,0.,0.,0.,1.,0.,0.,0.,0.,1.]


def validate(root=ROOT):
    root = Path(root)
    raw = (root/CAPTURE).read_bytes(); capture = json.loads(raw)
    original = json.loads((root/'circularmodes-45f859c1f1b6/ground_truth.json').read_text())
    assert capture['status'] == 'complete' and not capture['errors'] and len(capture['samples']) == 2
    rows = []; reads = stable = getter_disagreements = logical_matches = face_rows = 0
    for sample in capture['samples']:
        assert sample['status'] == 'read_complete' and sample['close_owned_document'] == {'value': True}
        filename = sample['file']; source = (root/filename).read_bytes()
        assert hashlib.sha256(source).hexdigest() == sample['archive_sha256']
        truth, = [s for s in original['samples'] if s['file'] == Path(filename).name]
        settings = sample['settings']; old = truth['settings']
        assert settings['quantity'] == old['quantity'] == 4
        assert settings['is_symmetric'] is old['is_symmetric'] is False
        assert settings['total_angle_radians'] == old['total_angle_radians']
        assert not settings['suppressed_ids'] and settings['result_body_count'] == 4
        assert old['axis_origin_cm'] == [0.,0.,0.] and old['axis_direction'] == [0.,0.,1.]
        forward = sample['retained_forward']; backward = {r['requested_collection_index']: r for r in sample['retained_reverse']}
        fresh = {r['requested_collection_index']: r for r in sample['fresh_per_property']}
        repeat = {r['requested_collection_index']: r for r in sample['repeated_item']}
        assert sample['python_handles_are_pairwise_distinct'] is True
        assert len(forward) == len(backward) == len(fresh) == len(repeat) == 4
        seed_faces = forward[0]['faces']['value']; seed_bounds = seed_faces[0]['body_bounds_cm']
        quantity = int(settings['quantity']); total = settings['total_angle_radians']
        step = total/(quantity if math.isclose(abs(total), math.tau, abs_tol=1e-9) else quantity-1)
        elements = []
        for row in forward:
            i = row['requested_collection_index']
            matrices = []
            expected_faces = row['faces']['value']; assert len(expected_faces) == 6
            actual_bounds = expected_faces[0]['body_bounds_cm']
            assert all(f['body_bounds_cm'] == actual_bounds for f in expected_faces)
            face_rows += len(expected_faces)
            for other in [row, backward[i], repeat[i]['first'], repeat[i]['second']]:
                assert other['id_before'] == other['id_after'] == {'value': i}
                assert other['parent_feature_name'] == {'value': 'ProbeCircularPattern'}
                assert other['is_suppressed'] == {'value': False}
                assert other['faces']['value'] == expected_faces
                for key in ('transform_first', 'transform_second'):
                    matrices.append(other[key]['value']); reads += 1
            assert fresh[i]['id'] == {'value': i} and fresh[i]['is_suppressed'] == {'value': False}
            matrices.append(fresh[i]['transform']['value']); reads += 1
            assert all(_near(matrices[0], m, 1e-12) for m in matrices[1:])
            old_matrix = next(r['transform'] for r in truth['pattern_elements'] if r['id'] == i)
            assert _near(matrices[0], old_matrix, 1e-12)
            stable += 1
            actual = _bounds(actual_bounds)
            predicted_getter = _transformed_bounds(seed_bounds, matrices[0])
            predicted_logical = _transformed_bounds(seed_bounds, _rotation(i*step))
            getter_matches = _near(actual, predicted_getter)
            logical_match = _near(actual, predicted_logical)
            assert logical_match
            assert getter_matches is (i == 0)
            logical_matches += 1; getter_disagreements += not getter_matches
            elements.append({'actual_API_element_id': i, 'collection_index': i,
                'same_handle_fresh_repeat_reverse_matrices_stable': True,
                'matches_original_saved_getter': True, 'copied_matrix_read_count': len(matrices),
                'actual_API_face_count': len(expected_faces), 'actual_API_face_body_bounds_cm': actual_bounds,
                'getter_transform_bounds_match_actual_face_body': getter_matches,
                'source_control_logical_rotation_bounds_match_actual_face_body': logical_match,
                'source_control_logical_angle_degrees': math.degrees(i*step),
                'getter_rotation_angle_degrees': math.degrees(math.atan2(matrices[0][4], matrices[0][0]))})
        rows.append({'file': filename, 'archive_sha256': sample['archive_sha256'], 'elements': elements,
            'owned_import_closed_without_save': True,
            'axis_scope': 'Root +Z origin axis from original saved API settings and the unchanged source archive; no live axis getter captured by this probe'})
    assert (stable, reads, getter_disagreements, logical_matches, face_rows) == (8, 72, 6, 8, 48)
    return {'scope': 'Two actual Fusion import readback probes; getter-access controls and actual PatternElement.faces/body getters, no native placement correction',
        'capture': CAPTURE, 'capture_sha256': hashlib.sha256(raw).hexdigest(), 'fusion_version': capture['fusion_version'],
        'samples': rows, 'summary': {'imported_owned_files': 2, 'stable_element_getters': stable,
            'actual_matrix_reads': reads, 'actual_API_element_face_rows': face_rows,
            'getter_transform_physical_body_disagreements': getter_disagreements,
            'source_control_logical_rotation_body_matches': logical_matches, 'actual_API_capture_errors': 0,
            'owned_documents_closed_without_save': 2, 'native_element_to_BODY_ID_assignments_claimed': 0},
        'findings': ['The transform discrepancy survives import and retained, fresh, repeated and reverse-access reads; none of these access patterns explains it in the two observed cases.',
            'Actual per-element face BODY bounds follow the ordinary source-control rotation while each nonseed transform getter predicts another BODY location.',
            'The original unresolved transform-getter diagnostic stays valid. No skipped-index correction or SDK implementation-bug claim is promoted.'],
        'limitations': ['Only unsuppressed root-component quantity-four full/negative cases were imported; symmetry, other quantities and contexts remain untested here.',
            'API body bounds corroborate physical positions; they do not establish serialized native element-to-BODY identity, persistent topology or feature regeneration.',
            'Opaque API entity tokens remain unparsed; no cross-session token equality or numeric feature identity is inferred.']}


if __name__ == '__main__':
    report = validate()
    (ROOT/'circular-getter-handle-decoding.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['summary'], sort_keys=True))
