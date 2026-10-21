"""Bounded stored Rule-Fillet blend/spring grids and VBL component definitions.

This does not reconstruct the procedural blend. Inline reference numbers are
retained in their own namespace, and cache parameters are never negated to fit
native edge parameters. VBL_SURF contains component UV grids, not a standalone
XYZ tensor grid, so it deliberately remains unsupported as a surface evaluator.
"""
import math

from decode_bspline import knot_vector, scalar_lists
from decode_fillet_spline_caches import _expect, _finite
from decode_spring_curve_cache import decode_spring_curve_cache


def _bounds(tokens, cursor, count):
    values, flags = [], []
    for _ in range(count):
        flag = _expect(tokens, cursor, 'boolean_token')
        if not isinstance(flag, bool):
            raise ValueError('Rule blend bound flag must be Boolean')
        flags.append(flag)
        cursor += 1
        values.append(_expect(tokens, cursor, 'double') if flag else None)
        cursor += int(flag)
    return values, flags, cursor


def _surface_grid(tokens, start):
    _expect(tokens, start, 'entity_name', 'nurbs')
    du = _expect(tokens, start+1, 'integer', 3)
    dv = _expect(tokens, start+2, 'integer', 3)
    _expect(tokens, start+3, 'entity_name', 'both')
    flags = [_expect(tokens, start+i, 'enum', 0) for i in range(4, 8)]
    ku, cu, nu, cursor = knot_vector(tokens, start+10, _expect(tokens, start+8, 'integer'), du)
    kv, cv, nv, cursor = knot_vector(tokens, cursor, _expect(tokens, start+9, 'integer'), dv)
    if nu*nv > 100000:
        raise ValueError('Rule blend control grid exceeds limit')
    flat = [_expect(tokens, cursor+i, 'double') for i in range(4*nu*nv)]
    weights = flat[3::4]
    if any(not math.isfinite(w) or w <= 0 for w in weights):
        raise ValueError('Rule blend weights must be finite and positive')
    points = [flat[i:i+3] for i in range(0, len(flat), 4)]
    return {'degree_u': du, 'degree_v': dv, 'control_count_u': nu, 'control_count_v': nv,
            'raw_control_points': [points[v*nu+u] for u in range(nu) for v in range(nv)],
            'weights': [weights[v*nu+u] for u in range(nu) for v in range(nv)],
            'is_rational': True, 'knots_u': ku, 'knots_v': kv,
            'stored_compact_knots_u': cu, 'stored_compact_knots_v': cv,
            'stored_control_grid_order': 'u-fast', 'normalized_control_grid_order': 'v-fast',
            'parameter_domain_u': [ku[du], ku[-du-1]],
            'parameter_domain_v': [kv[dv], kv[-dv-1]], 'stored_axis_flags': flags}, cursor+4*nu*nv


def decode_rule_blend_inline(tokens, start):
    """Read one observed unbounded planar/straight rational blend patch.

    start is its Boolean wrapper; end includes the four outer bound fields.
    This strict branch accepts captured all-false bounds and two trailer flags.
    The established reader continues to handle the earlier finite-bound form.
    """
    _finite(tokens)
    _expect(tokens, start, 'boolean_token', False)
    _expect(tokens, start+1, 'subtype_start')
    _expect(tokens, start+2, 'entity_name', 'srf_srf_v_bl_spl_sur')
    _expect(tokens, start+3, 'integer', 23100)
    cursor = start+4
    for _ in range(2):
        _expect(tokens, cursor, 'string', 'blend_support_surface')
        _expect(tokens, cursor+1, 'entity_name', 'plane')
        for offset, kind in ((2, 'position_vector'), (3, 'direction_vector'), (4, 'direction_vector')):
            _expect(tokens, cursor+offset, kind)
        for offset in range(5, 10):
            _expect(tokens, cursor+offset, 'boolean_token', False)
        for offset, value in ((10, 'null_curve'), (11, 'nullbs'), (13, 'nullbs'), (15, 'nullbs')):
            _expect(tokens, cursor+offset, 'entity_name', value)
        _expect(tokens, cursor+12, 'position_vector')
        _expect(tokens, cursor+14, 'integer', 0)
        cursor += 16
    _expect(tokens, cursor, 'entity_name', 'straight')
    spine = {'raw_origin': _expect(tokens, cursor+1, 'position_vector'),
             'raw_direction': _expect(tokens, cursor+2, 'direction_vector')}
    bounds, flags, cursor = _bounds(tokens, cursor+3, 2)
    if flags != [False, False]:
        raise ValueError('Rule blend fallback requires captured unbounded spine')
    spine.update(stored_bounds=bounds, stored_bound_flags=flags)
    _expect(tokens, cursor, 'double')
    _expect(tokens, cursor+1, 'double')
    _expect(tokens, cursor+2, 'enum', 1)
    cursor += 3
    widths = []
    for _ in range(2):
        _expect(tokens, cursor, 'entity_name', 'edge_offset')
        _expect(tokens, cursor+1, 'enum', 0)
        _expect(tokens, cursor+2, 'boolean_token', True)
        widths.append([_expect(tokens, cursor+i, 'double') for i in (3, 4, 5)])
        cursor += 6
    _expect(tokens, cursor, 'enum', 0)
    for offset in (1, 3):
        _expect(tokens, cursor+offset, 'boolean_token', True)
        _expect(tokens, cursor+offset+1, 'double')
    for offset in (5, 6):
        _expect(tokens, cursor+offset, 'boolean_token', False)
    for offset in (7, 10):
        _expect(tokens, cursor+offset, 'integer', 1)
    for offset in (8, 9):
        _expect(tokens, cursor+offset, 'double')
    _expect(tokens, cursor+11, 'enum', 0)
    grid_start = cursor+12
    cache, cursor = _surface_grid(tokens, grid_start)
    trailer_start = cursor
    scalar = _expect(tokens, cursor, 'double')
    lists, cursor = scalar_lists(tokens, cursor+1, 6)
    _expect(tokens, cursor, 'boolean_token', False)
    for offset in (1, 2, 3):
        _expect(tokens, cursor+offset, 'integer', 0)
    _expect(tokens, cursor+4, 'entity_name', 'null_curve')
    trailer_flag = _expect(tokens, cursor+5, 'boolean_token')
    if not isinstance(trailer_flag, bool):
        raise ValueError('Rule blend trailer flag must be Boolean')
    for offset in range(6, 9):
        _expect(tokens, cursor+offset, 'boolean_token', False)
    for offset in (9, 10):
        _expect(tokens, cursor+offset, 'entity_name', 'nullbs')
    _expect(tokens, cursor+11, 'subtype_end')
    bounds, flags, cursor = _bounds(tokens, cursor+12, 4)
    if flags != [False]*4:
        raise ValueError('Rule blend fallback requires captured unbounded outer interval')
    cache.update(stored_parameter_interval_u=bounds[:2], stored_parameter_interval_v=bounds[2:],
                 stored_outer_bound_flags=flags, stored_wrapper_flag=False,
                 stored_spine_kind='straight', stored_spine=spine, stored_blend_mode_code=1,
                 stored_edge_offset_scalar_triples=widths,
                 stored_procedural_definition=tokens[start+2:grid_start], stored_grid_start_token=grid_start,
                 stored_cache_trailer_scalar=scalar, stored_trailer_scalar_lists=lists,
                 stored_post_grid_flags=[trailer_flag, False, False, False],
                 stored_cache_trailer=tokens[trailer_start:cursor],
                 procedural_subtype='srf_srf_v_bl_spl_sur',
                 representation='Stored rational bicubic variable-blend approximation; procedural blend not reconstructed',
                 cache_status='No direct API surface-cache/evaluator comparison captured; approximation error unbounded',
                 periodicity_status='Literal axis flags retained; general periodicity/form semantics unresolved',
                 flag_scope='Literal flags/width triples retained; no orientation or parameter remapping inferred',
                 coordinate_scope='Raw ASM coordinates; body transforms and units/context not applied')
    return cache, cursor


def _spring(record):
    # Adapt only the one literal the earlier strict grammar over-restricted.
    # This local validation copy is never serialized or returned as source data.
    ts = record['tokens']
    _finite(ts)
    _, _, count, cursor = knot_vector(ts, 12, _expect(ts, 11, 'integer'), 3)
    ref_index = cursor+4*count+5
    ref = _expect(ts, ref_index, 'integer')
    if not 1 <= ref <= 1000000:
        raise ValueError('Rule spring fallback requires positive bounded inline reference')
    normalized = list(ts)
    normalized[ref_index] = dict(ts[ref_index], value=0)
    result = decode_spring_curve_cache(dict(record, tokens=normalized))
    result.update(stored_inline_surface_ref=ref, stored_cache_trailer=ts[cursor+4*count:],
                  reference_scope='Stored inline allocation number; surface binding requires typed subtype namespace and parent topology',
                  validation_scope='Earlier complete spring grammar reused with only its hardcoded ref0 predicate generalized; returned fields retain original ref')
    return result


def decode_rule_blend_cache(record):
    """Strict fallback for real XYZ grids; never manufacture a VBL surface grid."""
    ts = record['tokens']
    if record['name'] == 'intcurve-curve' and _expect(ts, 5, 'entity_name') == 'spring_int_cur':
        return _spring(record)
    if record['name'] == 'spline-surface' and _expect(ts, 5, 'entity_name') == 'srf_srf_v_bl_spl_sur':
        for i, kind, value in ((0, 'pointer', -1), (1, 'integer', -1), (2, 'pointer', -1)):
            _expect(ts, i, kind, value)
        cache, end = decode_rule_blend_inline(ts, 3)
        if end != len(ts):
            raise ValueError('Unconsumed Rule blend surface fields')
        return cache
    raise ValueError('No supported standalone Rule blend XYZ tensor/curve grid; VBL component UVs are separate metadata')


def _uv(tokens, start):
    _expect(tokens, start, 'entity_name', 'nubs')
    degree = _expect(tokens, start+1, 'integer')
    if degree not in (1, 5):
        raise ValueError('Unobserved VBL component UV degree')
    _expect(tokens, start+2, 'enum', 0)
    knots, compact, count, cursor = knot_vector(tokens, start+4, _expect(tokens, start+3, 'integer'), degree)
    flat = [_expect(tokens, cursor+i, 'double') for i in range(2*count)]
    return {'degree': degree, 'knots': knots, 'stored_compact_knots': compact,
            'raw_control_points': [flat[i:i+2] for i in range(0, len(flat), 2)],
            'weights': [], 'is_rational': False, 'stored_form_code': 0,
            'parameter_domain': [knots[degree], knots[-degree-1]]}, cursor+2*count


def _support(tokens, start):
    kind = _expect(tokens, start, 'entity_name')
    if kind == 'plane':
        vectors = [_expect(tokens, start+i, token_kind) for i, token_kind in
                   ((1, 'position_vector'), (2, 'direction_vector'), (3, 'direction_vector'))]
        flag = _expect(tokens, start+4, 'boolean_token')
        bounds, flags, end = _bounds(tokens, start+5, 4)
        result = dict(kind=kind, raw_origin=vectors[0], raw_normal=vectors[1],
                      raw_reference_axis=vectors[2], stored_sense_flag=flag,
                      stored_bounds=bounds, stored_bound_flags=flags)
    elif kind == 'spline':
        _expect(tokens, start+1, 'boolean_token', False)
        _expect(tokens, start+2, 'subtype_start')
        subtype = _expect(tokens, start+3, 'entity_name')
        if subtype == 'ref':
            ref = _expect(tokens, start+4, 'integer')
            if not 0 <= ref <= 1000000:
                raise ValueError('Invalid VBL inline surface reference')
            _expect(tokens, start+5, 'subtype_end')
            bounds, flags, end = _bounds(tokens, start+6, 4)
            result = dict(kind=kind, procedural_subtype='ref', stored_inline_surface_ref=ref,
                          stored_bounds=bounds, stored_bound_flags=flags)
        elif subtype == 'srf_srf_v_bl_spl_sur':
            cache, end = decode_rule_blend_inline(tokens, start+1)
            result = dict(kind=kind, procedural_subtype=subtype, stored_xyz_cache=cache)
        else:
            raise ValueError('Unobserved VBL component spline support subtype')
    else:
        raise ValueError('Unobserved VBL component support kind')
    result.update(token_start=start, token_end=end-1, stored_definition=tokens[start:end])
    return result, end


def decode_rule_blend_definition(record):
    """Read six VBL support/UV components, explicitly without surface geometry."""
    ts = record['tokens']
    if record['name'] != 'spline-surface':
        raise ValueError('VBL definition requires spline surface record')
    _finite(ts)
    for i, kind, value in ((0, 'pointer', -1), (1, 'integer', -1), (2, 'pointer', -1),
                           (3, 'boolean_token', False), (4, 'subtype_start', None),
                           (5, 'entity_name', 'VBL_SURF'), (6, 'integer', 23100), (7, 'integer', 6)):
        _expect(ts, i, kind, value)
    components, cursor = [], 8
    for slot in range(6):
        start = cursor
        _expect(ts, cursor, 'entity_name', 'pcurve')
        wrapper = _expect(ts, cursor+1, 'boolean_token')
        direction = _expect(ts, cursor+2, 'direction_vector')
        _expect(ts, cursor+3, 'boolean_token', True)
        _expect(ts, cursor+4, 'boolean_token', True)
        scalar = _expect(ts, cursor+5, 'double', 1.)
        support, cursor = _support(ts, cursor+6)
        uv, cursor = _uv(ts, cursor)
        flag = _expect(ts, cursor, 'boolean_token')
        trailing_scalar = _expect(ts, cursor+1, 'double', 0.)
        cursor += 2
        components.append(dict(slot=slot, token_start=start, token_end=cursor-1,
                               stored_wrapper_flag=wrapper, stored_direction_vector=direction,
                               stored_leading_flags=[True, True], stored_leading_scalar=scalar,
                               stored_support=support, stored_uv_cache=uv,
                               stored_terminal_flag=flag, stored_terminal_scalar=trailing_scalar))
    _expect(ts, cursor, 'integer', 9)
    scalar = _expect(ts, cursor+1, 'double')
    if scalar <= 0:
        raise ValueError('Unobserved nonpositive VBL terminal scalar')
    _expect(ts, cursor+2, 'subtype_end')
    bounds, flags, end = _bounds(ts, cursor+3, 4)
    if flags != [False]*4 or end != len(ts):
        raise ValueError('Unobserved VBL outer bounds/trailing fields')
    return dict(procedural_subtype='VBL_SURF', stored_version=23100, stored_component_count=6,
                components=components, stored_terminal_code=9, stored_terminal_scalar=scalar,
                stored_outer_bounds=bounds, stored_outer_bound_flags=flags,
                surface_geometry=None,
                scope='Six explicitly framed support/UV components; no standalone XYZ tensor grid, procedural reconstruction, support identity or surface evaluator inferred')


def validate_fixtures(root, zstd_library=None):
    """One new saved fixture and two prior Fillet controls; no live API calls."""
    import copy
    import hashlib
    import json
    from collections import Counter
    from functools import lru_cache
    from pathlib import Path
    from asm_records import inspect_asm
    from decode_asm_subtypes import decode_asm_subtypes, expand_asm_subtype_record
    from decode_bspline import decode_bspline, evaluate_curve, evaluate_surface
    from decode_pcurve_variants import encode_pcurve_fields
    from decode_variable_blend_cache import decode_variable_blend_cache
    from fusion_archive import read_members

    root = Path(root)
    filename = 'specialfillets-d50f7a4f04e0/rule_asymmetric.f3d'
    truth = next(s for s in json.loads((root/filename).parent.joinpath('ground_truth.json').read_text())['samples']
                 if s['file'] == Path(filename).name)
    report = dict(scope='Stored Rule-Fillet XYZ/UV caches and bounded VBL component definitions; no procedural regeneration or guessed source identity',
                  interfaces={'XYZ_fallback': 'decode_rule_blend_cache(record)',
                              'inline_patch': 'decode_rule_blend_inline(tokens,start)->cache,end',
                              'VBL_metadata_only': 'decode_rule_blend_definition(record)',
                              'validation': 'validate_fixtures(root,zstd_library=None)',
                              'integration': 'Keep previous blend/spring readers first, call XYZ fallback after failure, including namespace-expanded records. VBL metadata stays distinct from bspline_surface/evaluated geometry.'},
                  grammar={'blend': 'Version23100; two complete planar support descriptions, straight spine with two absent bounds, two edge_offset triples, bicubic rational NURBS tensor grid, six scalar lists, exact trailer, four absent outer bounds. First post-grid Boolean retained literally in both observed states.',
                           'spring': 'Complete earlier cubic rational XYZ plus linear UV/plane grammar, with positive inline allocation references instead of hardcoded0; original wrapper/terminal-enum pair and all raw trailer fields retained.',
                           'VBL': 'Version23100, exactly6 typed pcurve components; each has flags/vector/scalar, plane or spline support, degree1/5 NUBS UV grid and Boolean/zero scalar tail; then literal9, positive scalar, subtype end and four absent outer bounds. No standalone XYZ tensor grid exists in this framing.'},
                  actual_API={'settings': truth['settings'], 'actual_rule': truth['actual_rule'],
                              'curve_surface_evaluator_getters_captured': False,
                              'scope': 'Independent feature settings establish the captured Rule/asymmetric context; they do not validate stored ASM approximation error or parameterization'},
                  samples=[], independent_grid_checks=[], parameter_counterexamples=[], old_layout_controls=[], malformed_guards=[],
                  limitations=['Procedural blend/spring/VBL construction, approximation error and general flag/width semantics remain unresolved.',
                               'Inline reference numbers are not native object IDs or geometry record indices; this helper does not resolve support identity.',
                               'UV grids and XYZ grids retain independent domains; no automatic sign flip, orientation or cache-to-edge parameter mapping is applied.',
                               'VBL components expose stored support/UV descriptions only; no tensor grid or top-level surface evaluator is fabricated.',
                               'Raw coordinates remain in the ASM asset frame; no body/unit/context transform is applied.'])
    counts, originals, representatives = Counter(), {}, {}
    layout_checks = set()

    def basis(knots, degree, parameter, count):
        @lru_cache(None)
        def b(i, d):
            if d == 0:
                return float(knots[i] <= parameter < knots[i+1])
            dl, dr = knots[i+d]-knots[i], knots[i+d+1]-knots[i+1]
            return ((parameter-knots[i])/dl*b(i, d-1) if dl else 0.)+((knots[i+d+1]-parameter)/dr*b(i+1, d-1) if dr else 0.)
        return [b(i, degree) for i in range(count)]

    def check(cache, surface, label):
        errors = []
        for f in (.23, .51, .79):
            if surface:
                nu, nv = cache['control_count_u'], cache['control_count_v']
                au, bu = cache['parameter_domain_u']; av, bv = cache['parameter_domain_v']
                u, v = au+(bu-au)*f, av+(bv-av)*(1-f)
                bs_u = basis(cache['knots_u'], cache['degree_u'], u, nu)
                bs_v = basis(cache['knots_v'], cache['degree_v'], v, nv)
                coefficients = [bs_u[i]*bs_v[j]*cache['weights'][i*nv+j] for i in range(nu) for j in range(nv)]
                actual = evaluate_surface(cache, u, v)
            else:
                a, b = cache['parameter_domain']; parameter = a+(b-a)*f
                weights = cache['weights'] or [1.]*len(cache['raw_control_points'])
                coefficients = [b*w for b, w in zip(basis(cache['knots'], cache['degree'], parameter, len(weights)), weights)]
                actual = evaluate_curve(cache, parameter)
            points = cache['raw_control_points']
            expected = [sum(c*p[axis] for c, p in zip(coefficients, points))/sum(coefficients) for axis in range(len(points[0]))]
            error = math.dist(actual, expected)
            assert error < 1e-9, (label, error)
            errors.append(error)
        report['independent_grid_checks'].append(dict(label=label, method='Independent Cox basis sum versus homogeneous de Boor/tensor evaluation', samples=3, maximum_raw_error=max(errors)))

    for member, blob in read_members(root/filename, zstd_library).items():
        if '/Breps.BlobParts/' not in member or not member.endswith(('.smb', '.smbh')):
            continue
        parsed = inspect_asm(blob); catalog = decode_asm_subtypes(blob, parsed=parsed)
        row = dict(file=filename, member=member, XYZ_caches=[], VBL_definitions=[])
        for raw in parsed['records']:
            if raw['name'] not in ('spline-surface', 'intcurve-curve'):
                continue
            record, provenance = raw, None
            if raw['tokens'][5]['value'] == 'ref':
                expanded = expand_asm_subtype_record(raw, catalog, parsed['records'])
                record, provenance = expanded['record'], expanded['provenance']
            subtype = record['tokens'][5]['value']
            if subtype not in ('spring_int_cur', 'srf_srf_v_bl_spl_sur', 'VBL_SURF'):
                continue
            decoded = decode_rule_blend_definition(record) if subtype == 'VBL_SURF' else decode_rule_blend_cache(record)
            first, second = raw['name'].split('-')
            prefix = b'\x0e'+bytes([len(first)])+first.encode('utf8')+b'\x0d'+bytes([len(second)])+second.encode('utf8')
            replay = prefix+encode_pcurve_fields(raw['tokens'])+b'\x11'
            assert replay == blob[raw['offset']:raw['end_offset']]
            counts['full_original_record_replays'] += 1
            counts[subtype] += 1
            item = dict(record_index=raw['index'], expected_decoded=decoded,
                        original_record_replay={'matches': True, 'byte_count': len(replay), 'sha256': hashlib.sha256(replay).hexdigest()},
                        subtype_expansion_provenance=provenance)
            row['VBL_definitions' if subtype == 'VBL_SURF' else 'XYZ_caches'].append(item)
            representatives.setdefault(subtype, record)
            if subtype == 'VBL_SURF':
                counts['VBL_component_UV_views'] += len(decoded['components'])
                for component in decoded['components']:
                    uv = component['stored_uv_cache']; support = component['stored_support']
                    key = ('UV', uv['degree'], support['kind'])
                    if key not in layout_checks:
                        check(uv, False, str((raw['index'], component['slot'], key)))
                        layout_checks.add(key)
            elif subtype == 'spring_int_cur':
                originals[raw['index']] = decoded
                key = ('spring', decoded['stored_wrapper_flag'], decoded['stored_terminal_enum'])
                if key not in layout_checks:
                    check(decoded, False, str((raw['index'], key)))
                    check(decoded['stored_embedded_uv_cache'], False, str((raw['index'], 'springUV')))
                    layout_checks.add(key)
            else:
                key = ('blend', decoded['stored_post_grid_flags'][0])
                if key not in layout_checks:
                    check(decoded, True, str((raw['index'], key)))
                    layout_checks.add(key)
        # Literal typed edge parameters are evidence about limits only, not a
        # license to normalize signs based on a matching endpoint coordinate.
        for edge in parsed['records']:
            if edge['name'] != 'edge' or edge['section'] != 'geometry':
                continue
            ts = edge['tokens']; curve = ts[8]['value']
            if curve not in originals:
                continue
            cache = originals[curve]; a, b = cache['parameter_domain']
            parameters = [ts[4]['value'], ts[6]['value']]
            if not all(a-1e-12 <= p <= b+1e-12 for p in parameters):
                report['parameter_counterexamples'].append(dict(edge_record_index=edge['index'], curve_record_index=curve,
                    stored_native_parameters=parameters, stored_XYZ_domain=cache['parameter_domain'],
                    wrapper=cache['stored_wrapper_flag'], terminal_enum=cache['stored_terminal_enum'],
                    interpretation='Native edge limits cannot directly evaluate this stored cache domain; mapping remains unresolved and no negation applied'))
        report['samples'].append(row)

    # Old strict readers remain first and retain their exact dictionaries.
    for control in ('edgemodes-87edbf67527b/fillet_asymmetric.f3d', 'edgemodes-87edbf67527b/fillet_chord.f3d'):
        found = set()
        for member, blob in read_members(root/control, zstd_library).items():
            if not member.endswith(('.smb', '.smbh')): continue
            parsed = inspect_asm(blob); catalog = decode_asm_subtypes(blob, parsed=parsed)
            for r in parsed['records']:
                if r['name'] not in ('spline-surface', 'intcurve-curve'):continue
                if r['tokens'][5]['value'] == 'ref': r=expand_asm_subtype_record(r,catalog,parsed['records'])['record']
                sub = r['tokens'][5]['value']
                if sub in found or sub not in ('spring_int_cur', 'srf_srf_v_bl_spl_sur'):continue
                old_reader = decode_spring_curve_cache if sub == 'spring_int_cur' else decode_variable_blend_cache
                old = old_reader(r)
                combined = decode_bspline(r)
                assert old == combined
                found.add(sub)
                report['old_layout_controls'].append(dict(file=control, member=member, record_index=r['index'], subtype=sub, default_dictionary_unchanged=True))
        assert found == {'spring_int_cur', 'srf_srf_v_bl_spl_sur'}

    def reject(label, record, decoder):
        try: decoder(record)
        except (ValueError, IndexError, KeyError) as error:
            report['malformed_guards'].append(dict(label=label, rejected=True, reason=str(error)))
        else: raise AssertionError(label+' accepted')

    surface = copy.deepcopy(representatives['srf_srf_v_bl_spl_sur'])
    cached = decode_rule_blend_cache(surface); start = cached['stored_grid_start_token']
    _, _, _, cursor = knot_vector(surface['tokens'], start+10, surface['tokens'][start+8]['value'], 3)
    _, _, _, cursor = knot_vector(surface['tokens'], cursor, surface['tokens'][start+9]['value'], 3)
    surface['tokens'][cursor+3]['value'] = 0.
    reject('Nonpositive rational surface weight', surface, decode_rule_blend_cache)
    surface = copy.deepcopy(representatives['srf_srf_v_bl_spl_sur']); surface['tokens'][42]['value'] = True
    reject('Present spine bound missing scalar', surface, decode_rule_blend_cache)
    spring = copy.deepcopy(representatives['spring_int_cur'])
    _, _, count, cursor = knot_vector(spring['tokens'], 12, spring['tokens'][11]['value'], 3)
    spring['tokens'][cursor+4*count+5]['value'] = -1
    reject('Negative inline spring allocation number', spring, decode_rule_blend_cache)
    vbl = copy.deepcopy(representatives['VBL_SURF']); vbl['tokens'][7]['value'] = 5
    reject('VBL component count differs from framed six', vbl, decode_rule_blend_definition)
    vbl = copy.deepcopy(representatives['VBL_SURF']); vbl['tokens'] = vbl['tokens'][:-1]
    reject('Missing VBL outer field', vbl, decode_rule_blend_definition)
    reject('VBL is not a standalone XYZ tensor grid', representatives['VBL_SURF'], decode_rule_blend_cache)
    report['validation'] = dict(counts, independent_grid_checks=len(report['independent_grid_checks']),
        independent_evaluation_samples=3*len(report['independent_grid_checks']),
        maximum_independent_error=max(x['maximum_raw_error'] for x in report['independent_grid_checks']),
        old_layout_controls=len(report['old_layout_controls']), malformed_guards_passed=len(report['malformed_guards']),
        edge_parameter_domain_counterexamples=len(report['parameter_counterexamples']), new_live_API_calls=0,
        standalone_VBL_surface_evaluators=0)
    return report
