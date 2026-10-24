"""Prepared ordered mixed Line/Circle profile-portion contrasts; no dispatch.

Reuses actual ProfileCurve/source/evaluator/export truth from the shared capture
scaffolding. Geometry selects the requested experimental region only. Native
full tuples and mapped cache names must establish decoder identity separately.
"""
from pathlib import Path
import runpy


BASE_CIRCLE = {'kind': 'Circle', 'center_cm': [0.0, 0.0], 'radius_cm': 2.0}
BASE_LINE = {'kind': 'Line', 'start_cm': [-3.0, 0.5], 'end_cm': [3.0, 0.5]}
CASE_SPECS = {
    'circle_line_segment': {
        'geometry_sources': [BASE_CIRCLE, BASE_LINE],
        'selection': 'min_area', 'expected_profile_count': 2,
        'requested': {
            'sources': 'Circle centered(0,0), radius2cm, then finite horizontal Line(-3,.5) to(3,.5)cm',
            'selection': 'Smaller circular segment above the Line',
            'experiment': 'Mixed-source profile: expect one Circle portion and the middle of three finite-Line portions; literal selectors remain unassigned until real export inspection'},
    },
    'line_circle_reverse_creation': {
        'geometry_sources': [BASE_LINE, BASE_CIRCLE],
        'selection': 'min_area', 'expected_profile_count': 2,
        'requested': {
            'sources': 'Same Circle/Line geometry with Line created first',
            'selection': 'Same smaller circular segment',
            'experiment': 'Discriminate source creation/native tag order from complete native portion identity; do not associate using coordinates or array order'},
    },
    'shifted_circle_line_segment': {
        'geometry_sources': [
            {'kind': 'Circle', 'center_cm': [1.0, -1.0], 'radius_cm': 1.5},
            {'kind': 'Line', 'start_cm': [-1.5, -0.4], 'end_cm': [3.5, -0.4]}],
        'selection': 'min_area', 'expected_profile_count': 2,
        'requested': {
            'sources': 'Circle centered(1,-1), radius1.5cm, Line(-1.5,-.4) to(3.5,-.4)cm',
            'selection': 'Smaller circular segment above shifted Line',
            'experiment': 'Change Circle intersection angles and central-Line fractions while retaining the proper two-intersection topology'},
    },
}


def run(context):
    specs = CASE_SPECS
    if isinstance(context, dict) and 'cases' in context:
        requested = context['cases']
        unknown = set(requested)-set(CASE_SPECS)
        if unknown:
            raise ValueError('Unknown mixed-profile cases: '+repr(sorted(unknown)))
        specs = {name: spec for name, spec in CASE_SPECS.items() if name in requested}
    source = Path(__file__).resolve().with_name('GenerateTrimmedProfileContrasts.py')
    namespace = runpy.run_path(str(source))
    namespace['run']({'case_specs': specs, 'output_prefix': 'mixedprofiletrims-'})
