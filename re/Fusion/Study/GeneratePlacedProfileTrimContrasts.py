"""Prepared placed-profile contrasts; root dispatches the shared capture code.

Requests actual support-plane/Sketch transform, independent sketchToModelSpace
basis/portion samples and source worldGeometry truth. The direct Sketch.transform
getter is documented component-to-sketch; no forward-transform label is inferred.
"""
from pathlib import Path
import runpy

CASE_SPECS = {
    'offset_xy_circle_lens': {
        'circles': [(-1.0, 0.0, 2.0), (1.0, 0.0, 2.0)],
        'plane_spec': {'kind': 'OffsetXY', 'offset_cm': 1.25},
        'selection': 'min_area', 'expected_profile_count': 3,
        'requested': {
            'sources': 'Two radius2cm circles centered(-1,0) and(1,0) in sketch-local coordinates',
            'support_plane': 'XY plane offset1.25cm', 'selection': 'Smaller lens region',
            'experiment': 'Keep source-circle portion selectors/local geometry while introducing explicit component-space translation'},
    },
    'origin_xz_mixed_segment': {
        'geometry_sources': [
            {'kind': 'Circle', 'center_cm': [0.0, 0.0], 'radius_cm': 2.0},
            {'kind': 'Line', 'start_cm': [-3.0, 0.5], 'end_cm': [3.0, 0.5]}],
        'plane_spec': {'kind': 'OriginXZ'},
        'selection': 'min_area', 'expected_profile_count': 2,
        'requested': {
            'sources': 'Circle and finite horizontal Line in native sketch-local coordinates',
            'support_plane': 'Root origin XZ plane', 'selection': 'Smaller circular segment in sketch coordinates',
            'experiment': 'Recover placed mixed portions through explicit canonical Sketch basis; do not assume world XY or assembly placement'},
    },
    'angled_rectangle_overlap': {
        'rectangles': [(0.0, 0.0, 4.0, 3.0), (2.0, -1.0, 5.0, 2.0)],
        'plane_spec': {'kind': 'AngleXY', 'angle_deg': 30.0},
        'selection': 'min_area', 'expected_profile_count': 3,
        'requested': {
            'sources': 'Original intersecting rectangles in native sketch-local coordinates',
            'support_plane': 'Construction plane30deg about root X axis relative to XY',
            'selection': 'Smallest overlap [2,0]-[4,2] in sketch coordinates',
            'experiment': 'Derive local Line fractions unchanged, transform component points through proved rigid placement and compare every full-tuple named cache candidate'},
    },
}


def run(context):
    specs = CASE_SPECS
    if isinstance(context, dict) and 'cases' in context:
        requested = context['cases']; unknown = set(requested)-set(CASE_SPECS)
        if unknown:
            raise ValueError('Unknown placed-profile cases: '+repr(sorted(unknown)))
        specs = {name: spec for name, spec in CASE_SPECS.items() if name in requested}
    source = Path(__file__).resolve().with_name('GenerateTrimmedProfileContrasts.py')
    namespace = runpy.run_path(str(source))
    namespace['run']({'case_specs': specs, 'output_prefix': 'placedprofiletrims-'})
