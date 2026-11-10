"""Observed closed Patch par_int_cur XYZ/UV form2 approximation caches.

Finite clamped grids can be evaluated in their stored domain. Closure of these
cached endpoints does not assign universal form-enum periodicity or reconstruct
an exact circle, procedural boundary or coedge parameterization.
"""
import math

from decode_fillet_spline_caches import _expect
from decode_parameter_curve_cache import decode_parameter_curve_cache

SCOPE = ('Observed closed cubic polynomial par_int_cur XYZ/UV form2 caches with '
         'one literal spline-reference support; independent cache evaluation only, '
         'exact procedural geometry, periodicity and coedge parameterization unresolved')


def decode_closed_parameter_curve_cache(record):
    tokens = record['tokens']
    if record['name'] != 'intcurve-curve' or len(tokens) != 169:
        raise ValueError('Unobserved closed parameter-curve record shape')
    if [(token['kind'], token['value']) for token in tokens[:3]] != [
            ('pointer', -1), ('integer', -1), ('pointer', -1)]:
        raise ValueError('Unsupported closed parameter-curve typed header')
    _expect(tokens, 3, 'boolean_token', False)
    for index, kind, value in (
            (8, 'entity_name', 'nubs'), (9, 'integer', 3), (10, 'enum', 2), (11, 'integer', 9),
            (106, 'entity_name', 'spline'), (107, 'boolean_token', False),
            (109, 'entity_name', 'ref'), (116, 'entity_name', 'null_surface'),
            (117, 'entity_name', 'nubs'), (118, 'integer', 3), (119, 'enum', 2), (120, 'integer', 8)):
        _expect(tokens, index, kind, value)
    for index in (112, 113, 114, 115):
        _expect(tokens, index, 'boolean_token', False)
    for index in (160, 161, 162, 163):
        _expect(tokens, index, 'integer', 0)
    cache = decode_parameter_curve_cache(record, allowed_grid_forms=(0, 2))
    uv = cache['stored_embedded_uv_cache']
    for grid, dimensions, count, compact_count in ((cache, 3, 25, 9), (uv, 2, 10, 8)):
        if (grid['degree'] != 3 or grid['stored_form_code'] != 2 or grid['is_rational']
                or grid['weights'] or len(grid['raw_control_points']) != count
                or len(grid['stored_compact_knots']) != compact_count):
            raise ValueError('Unsupported closed cubic polynomial parameter-curve grid')
        if any(len(point) != dimensions or any(not math.isfinite(value) for value in point)
               for point in grid['raw_control_points']):
            raise ValueError('Invalid closed parameter-curve control coordinates')
        domain = grid['parameter_domain']
        if (not math.isclose(domain[0], -math.pi, rel_tol=0., abs_tol=1e-12)
                or not math.isclose(domain[1], math.pi, rel_tol=0., abs_tol=1e-12)):
            raise ValueError('Unobserved closed parameter-curve stored domain')
        if grid['raw_control_points'][0] != grid['raw_control_points'][-1]:
            raise ValueError('Stored closed parameter-curve endpoints differ')
        grid.update(is_periodic=None, cached_endpoints_coincide=True,
            periodicity_status='Form code2 retained; clamped cached endpoints coincide, but universal periodicity or extension semantics remain unresolved')
    support = cache['stored_support_definition']
    if (support['kind'] != 'spline' or support.get('procedural_subtype') != 'ref'
            or support.get('stored_wrapper_flag') is not False
            or len(support['stored_definition']) != 10
            or cache['stored_parameter_interval'] != [None, None]
            or cache['stored_interval_flags'] != [False, False]
            or cache['stored_trailer_scalar_lists'] != [[], [], [], []]):
        raise ValueError('Unsupported closed parameter-curve support or trailer')
    cache.update(representation='Stored closed cubic polynomial XYZ and cubic UV form2 approximation caches; exact parameter-defined curve is not reconstructed',
        cache_status='Closed cache structure independently evaluable; saved source-Circle API evaluations have nonzero deviations and do not establish exact cache equality',
        closure_scope='Coincident first/last controls of each clamped grid establish cached endpoint closure inside the stored domain only',
        scope=SCOPE)
    return cache
