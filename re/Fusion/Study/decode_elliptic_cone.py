"""Boundary-qualified elliptic cone locus for one observed ASM field layout.

The encoded reference ellipse and signed pair define an observed geometric
quadric. This does not assign native UV direction, angle or parameter formulas.
The separate parameter scale must match the ellipse radius in this narrow case.
"""

import math

from decode_fillet_spline_caches import _expect, _finite


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def decode_elliptic_cone(record):
    if record['name'] != 'cone-surface':
        raise ValueError('Elliptic cone reader requires cone-surface')
    tokens = record['tokens']; _finite(tokens)
    origin = _expect(tokens, 3, 'position_vector')
    axis = _expect(tokens, 4, 'direction_vector')
    reference = _expect(tokens, 5, 'direction_vector')
    ratio = _expect(tokens, 6, 'double')
    major = math.hypot(*reference)
    if not (0 < ratio < 1 and not math.isclose(ratio, 1., abs_tol=1e-10, rel_tol=0)
            and math.isfinite(major) and major > 0):
        raise ValueError('Unsupported noncircular elliptic cone base ellipse')
    if not math.isclose(dot(axis, axis), 1., abs_tol=1e-9):
        raise ValueError('Non-unit elliptic cone axis')
    if not math.isclose(dot(axis, reference), 0., abs_tol=1e-9):
        raise ValueError('Elliptic cone reference is not perpendicular to axis')
    _expect(tokens, 7, 'boolean_token', False)
    _expect(tokens, 8, 'boolean_token', False)
    sine, cosine = _expect(tokens, 9, 'double'), _expect(tokens, 10, 'double')
    if not math.isclose(sine*sine+cosine*cosine, 1., abs_tol=1e-9) or abs(sine) <= 1e-12 or cosine <= 0:
        raise ValueError('Unsupported elliptic cone angular pair')
    parameter_scale = _expect(tokens, 11, 'double')
    if parameter_scale <= 0 or not math.isclose(parameter_scale, major, abs_tol=1e-10, rel_tol=1e-10):
        raise ValueError('Unqualified elliptic cone parameter-scale/base-radius contrast')
    flag = _expect(tokens, 12, 'boolean_token')
    cursor, intervals, interval_flags = 13, [], []
    for _ in range(4):
        finite = _expect(tokens, cursor, 'boolean_token')
        interval_flags.append(finite); cursor += 1
        intervals.append(_expect(tokens, cursor, 'double') if finite else None)
        cursor += int(finite)
    if cursor != len(tokens):
        raise ValueError('Unsupported elliptic cone parameter trailer')
    major_unit = [v/major for v in reference]
    minor_unit = cross(axis, major_unit)
    minor = major*ratio
    rate = sine/(cosine*major)
    apex = [p-d/rate for p, d in zip(origin, axis)]
    return {'kind': 'EllipticCone', 'raw_origin': origin, 'axis': axis,
            'stored_reference_axis': reference, 'stored_axis_ratio': ratio,
            'raw_major_radius': major, 'raw_minor_radius': minor,
            'derived_minor_reference_axis': [minor*d for d in minor_unit],
            'stored_cone_angular_pair': [sine, cosine], 'stored_u_parameter_scale': parameter_scale,
            'stored_parameter_flag_12': flag, 'stored_interval_flags': interval_flags,
            'u_interval': intervals[:2], 'v_interval': intervals[2:],
            'geometric_locus': {'major_basis_unit': major_unit, 'minor_basis_unit': minor_unit,
                                'axial_relative_radius_rate': rate, 'raw_apex': apex,
                                'equation': '(dot(P-origin,E)/a)^2+(dot(P-origin,F)/b)^2=(1+k*dot(P-origin,axis))^2',
                                'symbols': 'E/F are stored major/derived minor unit bases; a/b are physical reference-ellipse radii; k is the boundary-qualified geometric axial scale rate.',
                                'qualification': 'Observed positive-cosine, nonzero-slope elliptic layout with parameter scale equal to physical major radius; two typed boundary circles independently qualify this geometric locus.'},
            'parameterization_scope': 'Raw signed pair/parameter scale/flag preserved; no native UV sign, parameter-to-angle formula, half-angle or periodic extension assigned',
            'coordinate_scope': 'Raw ASM coordinates and lengths; body transform and unit context not applied'}


def elliptic_cone_locus_residual(geometry, point):
    """Dimensionless implicit-quadric residual, not a distance or native UV."""
    if geometry['kind'] != 'EllipticCone' or len(point) != 3 or not all(math.isfinite(v) for v in point):
        raise ValueError('Invalid elliptic cone locus input')
    delta = [p-o for p, o in zip(point, geometry['raw_origin'])]
    locus = geometry['geometric_locus']
    x = dot(delta, locus['major_basis_unit'])/geometry['raw_major_radius']
    y = dot(delta, locus['minor_basis_unit'])/geometry['raw_minor_radius']
    scale = 1+locus['axial_relative_radius_rate']*dot(delta, geometry['axis'])
    return x*x+y*y-scale*scale
