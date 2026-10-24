"""Observed encoded circular helices and restricted helical-line surfaces.

These records contain analytic fields, not B-spline grids. Stored finite domains
are used literally. No handedness label, arbitrary domain or parameter sign map
is inferred from the thread feature or source geometry.
"""

import math

from decode_fillet_spline_caches import _expect, _finite

def _dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def _cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def _frame(origin, a, b, advance, axis):
    radius = math.sqrt(_dot(a, a))
    if (radius <= 0 or not math.isclose(_dot(a, a), _dot(b, b), rel_tol=1e-9, abs_tol=1e-12)
            or not math.isclose(_dot(axis, axis), 1., abs_tol=1e-9)
            or any(abs(_dot(v, axis)) > 1e-9 for v in (a, b)) or abs(_dot(a, b)) > 1e-9):
        raise ValueError('Unobserved noncircular/nonorthogonal helix frame')
    if any(abs(x-radius*radius*y) > 1e-9 for x, y in zip(_cross(a, b), axis)):
        raise ValueError('Helix cosine/sine frame does not match its literal axis')
    pitch = _dot(advance, axis)
    if pitch <= 0 or any(abs(x-pitch*y) > 1e-9 for x, y in zip(advance, axis)):
        raise ValueError('Unobserved nonaxial/zero helix per-turn advance')
    return {'raw_origin': origin, 'raw_radial_cos_vector': a, 'raw_radial_sin_vector': b,
            'raw_advance_per_turn_vector': advance, 'raw_axis': axis,
            'derived_radius_raw': radius, 'derived_advance_per_turn_magnitude_raw': pitch}


def _restricted_surface_frame(cache):
    a, b, axis = [cache[k] for k in ('raw_radial_cos_vector', 'raw_radial_sin_vector', 'raw_axis')]
    profile = cache['stored_line_coefficient_vector']
    if (abs(axis[0]) > 1e-9 or abs(axis[1]) > 1e-9 or abs(abs(axis[2])-1.) > 1e-9
            or a[0] <= 0 or abs(a[1]) > 1e-9 or abs(a[2]) > 1e-9
            or abs(b[0]) > 1e-9 or abs(b[2]) > 1e-9
            or abs(b[1]-a[0]*axis[2]) > 1e-9 or abs(profile[1]) > 1e-9):
        raise ValueError('Helical-line evaluator only supports captured Z-axis/+X-radial near-zero-Dy frames')


def decode_helix_cache(record):
    """Read an observed helix_int_cur or helix_spl_line encoded definition."""
    ts = record['tokens']
    if record['name'] not in ('intcurve-curve', 'spline-surface'):
        raise ValueError('Unsupported encoded helix record class')
    _finite(ts)
    for i, kind, value in ((0, 'pointer', -1), (1, 'integer', -1), (2, 'pointer', -1),
                           (3, 'boolean_token', False), (4, 'subtype_start', None), (6, 'integer', 23100)):
        _expect(ts, i, kind, value)
    subtype = _expect(ts, 5, 'entity_name')
    curve = record['name'] == 'intcurve-curve' and subtype == 'helix_int_cur'
    surface = record['name'] == 'spline-surface' and subtype == 'helix_spl_line'
    if not curve and not surface:
        raise ValueError('Unsupported encoded helix subtype/class combination')
    count, frame_start = (1, 11) if curve else (3, 19)
    pairs = []
    for i in range(count):
        cursor = 7+4*i
        _expect(ts, cursor, 'boolean_token', True)
        lo = _expect(ts, cursor+1, 'double')
        _expect(ts, cursor+2, 'boolean_token', True)
        hi = _expect(ts, cursor+3, 'double')
        if not lo < hi:
            raise ValueError('Encoded helix requires its observed increasing finite bounds')
        pairs.append([lo, hi])
    origin = _expect(ts, frame_start, 'position_vector')
    a, b, advance = [_expect(ts, frame_start+i, 'direction_vector') for i in (1, 2, 3)]
    _expect(ts, frame_start+4, 'double', 0.)
    axis = _expect(ts, frame_start+5, 'direction_vector')
    frame = _frame(origin, a, b, advance, axis)
    for i, value in enumerate(('null_surface', 'null_surface', 'nullbs', 'nullbs'), frame_start+6):
        _expect(ts, i, 'entity_name', value)
    cursor = frame_start+10
    result = {**frame, 'procedural_subtype': subtype, 'stored_wrapper_flag': False,
        'stored_definition_intervals': pairs, 'stored_zero_scalar': ts[frame_start+4]['value'],
        'coordinate_scope': 'Raw ASM coordinates; body transforms and units/context not applied',
        'identity_scope': 'Encoded geometry only; native topology identity and current/final lifecycle not inferred',
        'handedness_scope': 'Literal axis/radial/advance vectors retained; no API handedness/sign conversion inferred'}
    if curve:
        _expect(ts, cursor, 'subtype_end')
        _expect(ts, cursor+1, 'boolean_token', False)
        _expect(ts, cursor+2, 'boolean_token', False)
        if cursor+3 != len(ts):
            raise ValueError('Unconsumed encoded helix curve trailer')
        result.update(encoded_curve_kind='CircularHelix', parameter_domain=pairs[0],
            stored_outer_interval=[None, None],
            evaluation_formula='O + A*cos(t) + B*sin(t) + advance_per_turn*t/(2*pi)',
            representation='Observed explicit circular helix fields and encoded finite parameter interval; no B-spline grid',
            evaluation_scope='Direct encoded parameter formula corroborated by typed edge endpoints; no external API evaluator comparison')
    else:
        profile = _expect(ts, cursor, 'direction_vector')
        _expect(ts, cursor+1, 'subtype_end')
        cursor += 2
        limits = []
        for _ in range(4):
            _expect(ts, cursor, 'boolean_token', True)
            limits.append(_expect(ts, cursor+1, 'double'))
            cursor += 2
        if cursor != len(ts) or limits[0] >= limits[1] or limits[2] >= limits[3]:
            raise ValueError('Unobserved helical-line surface trailer/UV limits')
        result.update(encoded_surface_kind='HelicalLineSurface', stored_line_coefficient_vector=profile,
            parameter_domain_u=limits[:2], parameter_domain_v=limits[2:],
            stored_outer_uv_limits=limits,
            representation='Observed encoded helical-line surface; restricted evaluator, no B-spline grid',
            evaluation_formula='O + (1+Dx*u)*(A*cos(v)+B*sin(v)) + advance_per_turn*v/(2*pi) + axis*Dz*u',
            evaluation_scope='Only captured Z-axis/+X-radial frames and numerical near-zero Dy admitted. General transverse coefficient semantics remain unresolved.',
            domain_scope='Stored outer UV limits used literally; the three definition interval-pair roles remain partially unqualified')
        _restricted_surface_frame(result)
    return result


def _parameter(value, domain):
    if not math.isfinite(value):
        raise ValueError('Nonfinite encoded helix parameter')
    lo, hi = domain
    if value < lo:
        if lo-value > 1e-12:
            raise ValueError('Parameter outside encoded helix limits')
        value = lo
    if value > hi:
        if value-hi > 1e-12:
            raise ValueError('Parameter outside encoded helix limits')
        value = hi
    return value


def evaluate_helix_curve(cache, parameter):
    if cache.get('encoded_curve_kind') != 'CircularHelix':
        raise ValueError('Expected an encoded circular helix curve')
    parameter = _parameter(parameter, cache['parameter_domain'])
    return [o+a*math.cos(parameter)+b*math.sin(parameter)+w*parameter/(2*math.pi)
            for o, a, b, w in zip(cache['raw_origin'], cache['raw_radial_cos_vector'],
                cache['raw_radial_sin_vector'], cache['raw_advance_per_turn_vector'])]


def evaluate_helix_surface(cache, u, v):
    if cache.get('encoded_surface_kind') != 'HelicalLineSurface':
        raise ValueError('Expected an encoded helical-line surface')
    _restricted_surface_frame(cache)
    u, v = _parameter(u, cache['parameter_domain_u']), _parameter(v, cache['parameter_domain_v'])
    # Dy is admitted only as numerical zero; no general transverse term is inferred.
    dx, _, dz = cache['stored_line_coefficient_vector']
    return [o+(1+dx*u)*(a*math.cos(v)+b*math.sin(v))+w*v/(2*math.pi)+axis*dz*u
            for o, a, b, w, axis in zip(cache['raw_origin'], cache['raw_radial_cos_vector'],
                cache['raw_radial_sin_vector'], cache['raw_advance_per_turn_vector'], cache['raw_axis'])]
