"""Bounded stored NUBS grids in observed sweep_sur wrappers.

Profile/path/rail/expression descriptions are framed and retained. This reader
does not execute expressions or reconstruct the exact procedural sweep.
"""

from decode_bspline import decode_bspline, knot_vector, scalar_lists
from decode_fillet_spline_caches import _finite


def decode_sweep_surface_inline(tokens, start, *, allow_true_wrapper=False):
    """Read Boolean + subtype + four outer interval fields; return cache/end.

    ``start`` names the wrapper Boolean, both for a standalone surface record
    (field3) and a separately bounded inline support. No global ID is invented.
    """
    cursor = start

    def take(kind, expected=None):
        nonlocal cursor
        if cursor >= len(tokens) or tokens[cursor]['kind'] != kind:
            raise ValueError('Unexpected sweep cache token at field '+str(cursor))
        value = tokens[cursor]['value']
        if expected is not None and value != expected:
            raise ValueError('Unsupported sweep cache field '+str(cursor))
        cursor += 1
        return value

    def intervals(count):
        return [take('double') if take('boolean_token') else None for _ in range(count)]

    def curve():
        nonlocal cursor
        beginning = cursor
        name = take('entity_name')
        if name == 'straight':
            take('position_vector'); take('direction_vector')
            bounds = intervals(2)
        elif name == 'ellipse':
            take('position_vector'); take('direction_vector'); take('direction_vector')
            if take('double') <= 0:
                raise ValueError('Invalid sweep support ellipse ratio')
            bounds = intervals(2)
        elif name == 'intcurve':
            wrapper_start = cursor
            take('boolean_token', False)
            take('subtype_start')
            take('entity_name', 'exact_int_cur')
            depth = 1
            while cursor < len(tokens) and depth:
                kind = tokens[cursor]['kind']
                depth += int(kind == 'subtype_start')-int(kind == 'subtype_end')
                if depth > 128:
                    raise ValueError('Excessive inline sweep curve nesting')
                cursor += 1
            if depth:
                raise ValueError('Unclosed inline sweep curve wrapper')
            bounds = intervals(2)
            # Existing exact-curve framing validates the entire bounded body.
            fake_header = [{'kind': 'pointer', 'value': -1}, {'kind': 'integer', 'value': -1},
                           {'kind': 'pointer', 'value': -1}]
            decode_bspline({'name': 'intcurve-curve', 'tokens': fake_header+tokens[wrapper_start:cursor]})
        else:
            raise ValueError('Unsupported sweep profile/path curve '+str(name))
        return {'kind': name, 'token_fields': tokens[beginning:cursor], 'stored_bounds': bounds}

    wrapper = take('boolean_token')
    if wrapper and not allow_true_wrapper:
        raise ValueError('True sweep wrapper requires explicit observed inline-support admission')
    take('subtype_start'); take('entity_name', 'sweep_sur'); take('integer', 23100)
    prefix_flag = take('boolean_token')
    take('integer', -1)
    profile = curve()
    profile_bounds = intervals(2)
    extra_profile_frame = take('boolean_token')
    if extra_profile_frame:
        take('position_vector'); take('direction_vector')
    take('position_vector')
    for _ in range(3):
        take('direction_vector')
    mode = take('integer')
    if mode not in (1, 2, 3, 5):
        raise ValueError('Unobserved sweep cache mode')
    path_flag = take('boolean_token')
    path = curve()
    path_bounds = intervals(2)
    take('double'); take('boolean_token', False)
    if mode == 1:
        expression = take('string')
        count = take('integer')
        if count not in (0, 3) or not isinstance(expression, str) or not 1 <= len(expression) <= 8192:
            raise ValueError('Unsupported bounded sweep expression/operand layout')
        for _ in range(count):
            take('string', 'EDGE'); curve(); take('double'); take('double')
        take('boolean_token', bool(count))
    elif mode == 2:
        take('boolean_token', True)
        curve(); intervals(2)
        take('integer', 4); take('integer', 8)
        for _ in range(12):
            take('double')
        take('boolean_token', False)
        a, b = take('boolean_token'), take('boolean_token')
        if (a, b) not in ((False, False), (True, False), (True, True)):
            raise ValueError('Unobserved sweep guide cache flags')
    elif mode == 3:
        take('entity_name', 'plane'); take('position_vector')
        take('direction_vector'); take('direction_vector')
        for _ in range(7):
            take('boolean_token', False)
    else:
        take('integer', 1); take('boolean_token', False)
        curve(); intervals(2); take('double'); take('boolean_token', False)
        take('string', 'VEC(0,0,1)'); take('integer', 0); take('boolean_token', False)
        take('position_vector'); take('direction_vector'); take('double'); take('double')
    take('enum', 0)
    grid_start = cursor
    take('entity_name', 'nubs')
    du, dv = take('integer', 3), take('integer', 3)
    flags = [take('enum') for _ in range(4)]
    if flags not in ([0, 0, 0, 0], [2, 0, 0, 0]):
        raise ValueError('Unobserved sweep surface axis flags')
    unique_u, unique_v = take('integer'), take('integer')
    ku, compact_u, nu, cursor = knot_vector(tokens, cursor, unique_u, du)
    kv, compact_v, nv, cursor = knot_vector(tokens, cursor, unique_v, dv)
    if nu*nv > 100000:
        raise ValueError('Sweep surface grid exceeds supported limit')
    flat = [take('double') for _ in range(3*nu*nv)]
    trailer_start = cursor
    scalar = take('double')
    lists, cursor = scalar_lists(tokens, cursor, 6)
    take('boolean_token', False); take('subtype_end')
    bounds = intervals(4)
    _finite(tokens[start:cursor])
    controls = [flat[i:i+3] for i in range(0, len(flat), 3)]
    cache = {'degree_u': du, 'degree_v': dv, 'control_count_u': nu, 'control_count_v': nv,
        'raw_control_points': [controls[v*nu+u] for u in range(nu) for v in range(nv)],
        'weights': [], 'is_rational': False, 'knots_u': ku, 'knots_v': kv,
        'stored_compact_knots_u': compact_u, 'stored_compact_knots_v': compact_v,
        'stored_control_grid_order': 'u-fast', 'normalized_control_grid_order': 'v-fast',
        'parameter_domain_u': [ku[du], ku[-du-1]], 'parameter_domain_v': [kv[dv], kv[-dv-1]],
        'stored_parameter_interval_u': bounds[:2], 'stored_parameter_interval_v': bounds[2:],
        'stored_axis_flags': flags, 'stored_wrapper_flag': wrapper,
        'stored_sweep_prefix_flag': prefix_flag, 'stored_extra_profile_frame_flag': extra_profile_frame,
        'stored_sweep_mode_code': mode, 'stored_sweep_path_flag': path_flag,
        'stored_profile_description': profile, 'stored_path_description': path,
        'stored_profile_bounds': profile_bounds, 'stored_path_bounds': path_bounds,
        'stored_procedural_definition': tokens[start:grid_start],
        'stored_cache_trailer_scalar': scalar, 'stored_trailer_scalar_lists': lists,
        'stored_cache_trailer': tokens[trailer_start:cursor], 'procedural_subtype': 'sweep_sur',
        'periodicity_status': 'Literal axis flags retained; clamped cache domain is not a general periodic surface model',
        'representation': 'Stored bicubic non-rational sweep approximation; exact procedural sweep is not reconstructed',
        'cache_status': 'No direct API surface evaluator comparison captured; approximation error is unbounded',
        'flag_scope': 'Flags, frames, expressions and native mode codes retained without new orientation or procedural evaluation claims',
        'coordinate_scope': 'Raw ASM coordinates; body transforms and units/context not applied'}
    return cache, cursor


def decode_sweep_surface_cache(record):
    if record['name'] != 'spline-surface':
        raise ValueError('Sweep cache requires a spline-surface record')
    cache, end = decode_sweep_surface_inline(record['tokens'], 3)
    if end != len(record['tokens']):
        raise ValueError('Unconsumed sweep surface record fields')
    return cache
