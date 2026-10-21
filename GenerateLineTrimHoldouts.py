"""Prepared Line/Line selected-profile fraction holdouts; no live dispatch.

Reuses the existing profile portion/source/evaluator/journal/export scaffolding.
Actual native tuples and all-six-field cached naming must establish identity;
source segment fractions will be derived only after real captures qualify it.
"""
from pathlib import Path
import runpy


CASE_SPECS = {
    'reverse_rectangle_creation': {
        'rectangles': [(2.0, -1.0, 5.0, 2.0), (0.0, 0.0, 4.0, 3.0)],
        'selection': 'min_area', 'expected_profile_count': 3,
        'requested': {
            'sources': 'Original intersecting rectangles, creation order reversed: [2,-1]-[5,2], then[0,0]-[4,3]cm',
            'selection': 'Smallest overlap [2,0]-[4,2]cm',
            'experiment': 'Separate raw native source tags/creation order from full-tuple portion identity and derived source fractions'},
    },
    'translated_unequal_rectangles': {
        'rectangles': [(1.0, 2.0, 7.0, 6.0), (5.0, 0.0, 9.0, 4.5)],
        'selection': 'min_area', 'expected_profile_count': 3,
        'requested': {
            'sources': 'Unequal translated rectangles [1,2]-[7,6] and[5,0]-[9,4.5]cm',
            'selection': 'Smallest overlap [5,2]-[7,4.5]cm, area5cm²',
            'experiment': 'Change actual trim positions/fractions while retaining two-portion source layout; no fixed endpoint/fraction encoding assumed'},
    },
}


def run(context):
    specs = CASE_SPECS
    if isinstance(context, dict) and 'cases' in context:
        requested = context['cases']
        unknown = set(requested)-set(CASE_SPECS)
        if unknown:
            raise ValueError('Unknown Line-trim holdout cases: '+repr(sorted(unknown)))
        specs = {name: spec for name, spec in CASE_SPECS.items() if name in requested}
    source = Path(__file__).resolve().with_name('GenerateTrimmedProfileContrasts.py')
    namespace = runpy.run_path(str(source))
    namespace['run']({'case_specs': specs, 'output_prefix': 'linetrimholdouts-'})
