"""Compare logical rotations, typed body caches and actual element getter matrices.

This audit does not supply production instance transforms or assign any native
element ID to a body. Getter disagreement remains an explicit unresolved issue.
"""
import json
import math
from pathlib import Path

from decode_basics import decode_basics
from decode_pattern_placements import _same_matrix_set
from decode_placement import transform_point
from decode_sketch import same


def rotation(axis, origin, angle):
    x, y, z = axis
    c, s = math.cos(angle), math.sin(angle)
    d = 1-c
    rows = [[c+x*x*d, x*y*d-z*s, x*z*d+y*s],
            [y*x*d+z*s, c+y*y*d, y*z*d-x*s],
            [z*x*d-y*s, z*y*d+x*s, c+z*z*d]]
    return [value for i, row in enumerate(rows)
            for value in row+[origin[i]-sum(row[k]*origin[k] for k in range(3))]]+[0., 0., 0., 1.]


def audit(root, zstd_library):
    root = Path(root)
    folder = root/'circularmodes-45f859c1f1b6'
    truth = json.loads((folder/'ground_truth.json').read_text())
    report = {'scope': 'Bounded physical-cache corroboration of ordinary logical rotations; not a native element/body mapping or getter semantics decoder',
              'cases': [], 'new_API_calls': 0,
              'limitations': ['Four existing unsuppressed body-input cases only; no arbitrary feature/suppression/context claim.',
                             'Matrices are calculated from explicit source axis/quantity/angle; no native per-instance matrix storage is claimed.',
                             'Body IDs are established by typed same-blob joins before checking the unordered geometry multiset.',
                             'Saved element getter matrices disagree; neither the audit nor candidate matching identifies the cause.',
                             'Production circular placement failures remain unresolved.']}
    for case in ('body_full', 'body_negative', 'body_symmetric', 'multiple_customaxis'):
        relative = 'circularmodes-45f859c1f1b6/'+case+'.f3d'
        stream = decode_basics(root/relative, zstd_library)['streams'][0]
        feature = next(f for f in stream['features'] if f['kind'] == 'CircularPattern')
        settings = feature['tool_settings']
        actual = next(s for s in truth['samples'] if s['file'] == case+'.f3d')
        axis = settings['axis']['entity']
        quantity, angle = settings['quantity'], settings['total_angle_radians']
        assert settings['pattern_entity_type'] == 'Bodies' and settings['suppressed_element_ids'] == []
        assert same(axis['origin_cm'], actual['settings']['axis_origin_cm']) and same(axis['direction'], actual['settings']['axis_direction'])
        assert quantity == actual['settings']['quantity'] and angle == actual['settings']['total_angle_radians']
        step = angle/(quantity if math.isclose(abs(angle), 2*math.pi, abs_tol=1e-9) else quantity-1)
        angles = ([i*step for i in range(quantity)] if not settings['is_symmetric']
                  else [(i-(quantity-1)/2)*step for i in range(quantity)])
        matrices = [rotation(axis['direction'], axis['origin_cm'], theta) for theta in angles]
        bodies = {b['native_body_object_id']: b for b in stream['body_placement']['bodies']}
        seeds = [bodies[identity]['component_vertex_positions_cm'] for identity in settings['native_input_body_object_ids']]
        remaining = [b['component_vertex_positions_cm'] for b in bodies.values()]
        assert len(remaining) == quantity*len(seeds) == actual['settings']['result_body_count']
        for matrix in matrices:
            for seed in seeds:
                transformed = sorted(transform_point(matrix, p) for p in seed)
                match = next((i for i, points in enumerate(remaining) if len(points) == len(transformed)
                              and all(same(a, b) for a, b in zip(sorted(points), transformed))), None)
                assert match is not None, case
                remaining.pop(match)
        assert not remaining
        getters = [entry['transform'] for entry in actual['pattern_elements']]
        assert not _same_matrix_set(matrices, getters), case
        assert any(u['feature_object_id'] == feature['object_id'] for u in stream['pattern_placements']['unresolved'])
        report['cases'].append({'file': relative, 'feature_object_id': feature['object_id'],
                                'native_input_body_object_ids': settings['native_input_body_object_ids'],
                                'actual_API_quantity': actual['settings']['quantity'],
                                'actual_API_total_angle_radians': actual['settings']['total_angle_radians'],
                                'axis_origin_cm': axis['origin_cm'], 'axis_direction': axis['direction'],
                                'is_symmetric': settings['is_symmetric'],
                                'calculated_logical_angles_radians': angles,
                                'calculated_logical_rotation_matrices': matrices,
                                'typed_cached_body_count': len(bodies),
                                'unordered_transformed_seed_vertex_multiset_matches_caches': True,
                                'actual_API_pattern_elements': actual['pattern_elements'],
                                'getter_matrix_multiset_matches_calculated_rotations': False,
                                'production_getter_semantics_still_unresolved': True})
    return report


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    zstd = next(Path('/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production').glob(
        '*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib'))
    report = audit(root, zstd)
    (root/'circular-cache-rotation-audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'saved_cases': len(report['cases']),
                      'typed_cached_bodies_corroborated': sum(c['typed_cached_body_count'] for c in report['cases']),
                      'getter_disagreements_preserved': len(report['cases'])}))
