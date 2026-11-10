"""Prepared independent selector/order and repeated-source profile contrasts.

Reuses GenerateTrimmedProfileContrasts truth/journal/export/close scaffolding via
its case_specs hook. No native selector predictions are installed in a decoder.
Actual exports and full six-literal naming routes must decide support later.
"""
from pathlib import Path
import runpy


CASE_SPECS = {
    'shifted_unequal_lens': {
        'circles': [(-1.0, 0.0, 2.0), (1.5, 0.0, 1.6)],
        'selection': 'min_area', 'expected_profile_count': 3,
        'requested': {
            'sources': 'Radius2cm circle centered(-1,0), radius1.6cm circle centered(1.5,0)',
            'selection': 'Smallest lens region; intersection angles differ from original equal-circle capture',
            'experiment': 'Distinguish literal selector identity from fixed geometric angles; no selector-to-angle rule assumed'},
    },
    'reverse_creation_lens': {
        'circles': [(1.0, 0.0, 2.0), (-1.0, 0.0, 2.0)],
        'selection': 'min_area', 'expected_profile_count': 3,
        'requested': {
            'sources': 'Original equal-radius circle geometry with creation order reversed',
            'selection': 'Smallest lens region',
            'experiment': 'Separate creation order/native source tags from source geometry and selected portion; native IDs remain independently qualified'},
    },
    'repeated_circle': {
        'circles': [(0.0, 0.0, 3.0), (-2.0, 0.0, 1.6), (2.0, 0.0, 1.6)],
        'selection': 'max_area', 'expected_profile_count': 5,
        'requested': {
            'sources': 'Radius3cm central circle cut by disjoint radius1.6cm circles centered(-2,0) and(2,0)',
            'selection': 'Largest remaining central region; expect two separate portions of the same underlying central Circle',
            'expected_repeated_source_count': 2,
            'experiment': 'Require distinct complete native reference tuples to qualify repeated-source portions; do not assign portions using coordinates'},
    },
    'repeated_circle_reverse_creation': {
        'circles': [(2.0, 0.0, 1.6), (-2.0, 0.0, 1.6), (0.0, 0.0, 3.0)],
        'selection': 'max_area', 'expected_profile_count': 5,
        'requested': {
            'sources': 'Same three-circle geometry as repeated_circle; creation order reversed',
            'selection': 'Same largest central region; central Circle created last',
            'expected_repeated_source_count': 2,
            'experiment': 'Independent holdout of repeated-source full-tuple identity under changed creation order'},
    },
}


def run(context):
    specs = CASE_SPECS
    if isinstance(context, dict) and 'cases' in context:
        requested = context['cases']
        unknown = set(requested)-set(CASE_SPECS)
        if unknown:
            raise ValueError('Unknown holdout cases: '+repr(sorted(unknown)))
        specs = {name: spec for name, spec in CASE_SPECS.items() if name in requested}
    source = Path(__file__).resolve().with_name('GenerateTrimmedProfileContrasts.py')
    namespace = runpy.run_path(str(source))
    namespace['run']({'case_specs': specs, 'output_prefix': 'trimselectorholdouts-'})
