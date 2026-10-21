"""Explicit bounded UV caches and namespace-qualified compact pcurve bindings.

Inline allocation numbers stay separate from geometry record pointers. UV
support selection requires literal topology and subtype-namespace identity;
coordinates/endpoints never choose a support slot or orientation.
"""
import math
import struct

from decode_bspline import knot_vector, read_token

SCOPE = 'Observed explicit NUBS UV caches with bounded support wrappers, or compact pcurve to stored UV slot through typed parent topology and exact inline support identity; sign, procedural evaluation and general coedge parameterization unresolved'


def encode_pcurve_fields(tokens):
    """Typed field replay only, not a CAD archive writer."""
    out = b''
    for token in tokens:
        tag, value = token['tag'], token['value']
        out += bytes([tag])
        if tag in (4, 12, 21):
            out += struct.pack('<q', value)
        elif tag == 6:
            out += struct.pack('<d', value)
        elif tag in (7, 13, 14):
            raw = value.encode('utf-8')
            if len(raw) > 255:
                raise ValueError('Pcurve replay short string exceeds255 bytes')
            out += bytes([len(raw)])+raw
        elif tag in (19, 20):
            out += struct.pack('<3d', *value)
        elif tag not in (10, 11, 15, 16):
            raise ValueError('Unobserved pcurve replay token tag')
    return out


def _finite(values):
    if not all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) for value in values):
        raise ValueError('Nonfinite/invalid pcurve cache numeric value')


def _bounds(tokens, start, count):
    values, flags, cursor = [], [], start
    for _ in range(count):
        flag = read_token(tokens, cursor, 'boolean_token')
        flags.append(flag)
        cursor += 1
        value = read_token(tokens, cursor, 'double') if flag else None
        cursor += int(flag)
        if value is not None:
            _finite([value])
        values.append(value)
    return values, flags, cursor


def _header(record):
    tokens = record['tokens']
    if (record['name'] != 'pcurve' or len(tokens) < 7
            or [t['kind'] for t in tokens[:3]] != ['pointer', 'integer', 'pointer']
            or [t['value'] for t in tokens[:3]] != [-1, -1, -1]):
        raise ValueError('Unobserved pcurve typed header')
    return tokens


def _surface(tokens, start):
    """Bound one support definition and four explicit optional bounds."""
    kind = read_token(tokens, start, 'entity_name')
    cursor = start+1
    result = {'kind': kind, 'token_start': start}
    if kind == 'plane':
        values = [read_token(tokens, cursor+i, field) for i, field in enumerate(('position_vector', 'direction_vector', 'direction_vector'))]
        for value in values:
            _finite(value)
        result.update(raw_origin=values[0], normal=values[1], stored_reference_axis=values[2],
                      stored_plane_flag=read_token(tokens, cursor+3, 'boolean_token'))
        cursor += 4
        result['definition_status'] = 'Explicit plane fields retained; no global source identity or evaluator inferred'
    elif kind == 'spline':
        result['stored_wrapper_flag'] = read_token(tokens, cursor, 'boolean_token')
        cursor += 1
        if tokens[cursor]['kind'] != 'subtype_start':
            raise ValueError('Pcurve support spline lacks explicit bracket')
        beginning = cursor
        subtype = read_token(tokens, cursor+1, 'entity_name')
        result.update(subtype_token_start=beginning, procedural_subtype=subtype)
        if subtype == 'ref':
            number = read_token(tokens, cursor+2, 'integer')
            if number < 0 or tokens[cursor+3]['kind'] != 'subtype_end':
                raise ValueError('Pcurve support ref bracket/index unsupported')
            result.update(stored_inline_surface_ref=number,
                reference_scope='Blob-local inline allocation reference; not a geometry record or Design object ID')
            cursor += 4
            result['definition_status'] = 'Exact ref bracket retained; surface identity requires the separate subtype catalog'
        else:
            if subtype not in ('sweep_sur', 'cyl_spl_sur', 'VBL_SURF') or read_token(tokens, cursor+2, 'integer') != 23100:
                raise ValueError('Unobserved bounded inline pcurve support subtype/version')
            depth = 0
            while cursor < len(tokens):
                field = tokens[cursor]
                depth += int(field['kind'] == 'subtype_start')-int(field['kind'] == 'subtype_end')
                if not 0 <= depth <= 128:
                    raise ValueError('Pcurve inline support bracket depth unsupported')
                cursor += 1
                if depth == 0:
                    break
            if depth:
                raise ValueError('Unclosed pcurve inline support definition')
            result['definition_status'] = 'Explicitly bounded stored inline support payload retained; procedural surface body is not evaluated or claimed decoded by this UV reader'
        result['subtype_token_end'] = cursor-1
    else:
        raise ValueError('Unobserved pcurve support definition kind')
    bounds, flags, cursor = _bounds(tokens, cursor, 4)
    result.update(stored_parameter_interval_u=bounds[:2], stored_parameter_interval_v=bounds[2:],
        stored_interval_flags=flags, token_end=cursor,
        stored_definition_bytes_hex=encode_pcurve_fields(tokens[start:cursor]).hex())
    return result, cursor


def decode_pcurve_variants(record):
    """Explicit prefix0 UV cache with support interval/definition variants."""
    tokens = _header(record)
    if read_token(tokens, 3, 'integer') != 0:
        raise ValueError('Compact pcurve requires namespace-qualified postpass')
    prefix = read_token(tokens, 4, 'boolean_token')
    if tokens[5]['kind'] != 'subtype_start' or read_token(tokens, 6, 'entity_name') != 'exp_par_cur':
        raise ValueError('Unobserved explicit UV pcurve subtype')
    if read_token(tokens, 7, 'entity_name') != 'nubs':
        raise ValueError('Only observed non-rational explicit UV pcurves supported')
    degree, form = read_token(tokens, 8, 'integer'), read_token(tokens, 9, 'enum')
    if (degree, form) not in ((1, 0), (1, 2), (3, 0)):
        raise ValueError('Unobserved explicit pcurve degree/form')
    knots, compact, count, cursor = knot_vector(tokens, 11, read_token(tokens, 10, 'integer'), degree)
    values = [read_token(tokens, cursor+i, 'double') for i in range(2*count)]
    cursor += 2*count
    scalar = read_token(tokens, cursor, 'double')
    _finite(knots+values+[scalar])
    support, cursor = _surface(tokens, cursor+1)
    if tokens[cursor]['kind'] != 'subtype_end' or cursor+3 != len(tokens):
        raise ValueError('Pcurve explicit support/trailer does not end at its own wrapper boundary')
    offset = [read_token(tokens, cursor+1+i, 'double') for i in range(2)]
    _finite(offset)
    raw = [values[i:i+2] for i in range(0, len(values), 2)]
    shifted = [[value+shift for value, shift in zip(point, offset)] for point in raw]
    return {'degree': degree, 'knots': knots, 'stored_compact_knots': compact,
        'raw_control_points_uv': raw, 'parameter_offset_uv': offset, 'control_points_uv': shifted,
        'weights': [], 'parameter_domain': [knots[degree], knots[-degree-1]], 'stored_form_code': form,
        'stored_prefix_integer': 0, 'stored_prefix_flag_4': prefix, 'stored_control_count': count,
        'uninterpreted_cache_scalar': scalar, 'stored_support_definition': support,
        'stored_inline_surface_ref': support.get('stored_inline_surface_ref'),
        'reference_scope': 'Inline surface references are separate allocation IDs; parent surface association requires independently qualified namespace/topology',
        'coordinate_system': 'Stored support surface UV cache coordinates; flags do not establish exact coedge parameterization',
        'representation': 'Stored explicit clamped non-rational UV NUBS cache with strictly framed support bounds and retained inline definition',
        'cache_status': 'UV control grid decoded; no direct API UV evaluator comparison captured; retained inline support bodies are not procedurally evaluated',
        'flag_scope': 'Literal wrapper flags and support interval fields retained; no coedge reversal or parameter remapping inferred',
        'scope': SCOPE}


def validate_fixtures(root, zstd_library=None):
    """Four focused saved archives: explicit variants and qualified UV slots."""
    import copy
    import hashlib
    import json
    from functools import lru_cache
    from pathlib import Path
    from asm_records import inspect_asm
    from decode_asm_subtypes import decode_asm_subtypes
    from decode_brep import decode_topology
    from decode_pcurve import _decode_observed_pcurve, decode_pcurve, evaluate_pcurve
    from fusion_archive import read_members

    root = Path(root)
    files = ['solidsweeps-5b5ecd5e01b9/solid_twist_sixty.f3d', 'embosstext-cd769aa41cdf/two_texts.f3d',
             'tappedholes-409e96788503/modeled_full.f3d', 'specialfillets-d50f7a4f04e0/rule_asymmetric.f3d']
    report = {'scope': SCOPE, 'interfaces': {
        'explicit_fallback': 'decode_pcurve_variants(record): after the existing explicit reader fails',
        'compact_postpass': 'decode_compact_pcurve(record,records,nodes,subtype_catalog): after typed curve/coedge/edge/loop/face nodes exist',
        'validator': 'validate_fixtures(root,zstd_library=None)',
        'expected_outputs': 'samples[].blobs[].new_records[].expected_uv_cache contains complete per-record helper output',
        'integration': 'Keep original pcurve reader first. Dispatch explicit prefix0 fallback only on failure. Postpass observed compact7-token selectors±1/±2 only with a qualified same-blob subtype catalog and parent topology. Preserve all unsupported diagnostics; no UV selected by coordinates or guessed inline record IDs.'},
        'grammar': {
            'explicit': 'Existing exp_par_cur/nubs degree1 or3 control grid, followed scalar, support definition, four optional finite support bounds, wrapper end and two explicit UV offsets. Every field is bounded and consumed exactly.',
            'support': 'Exact spline/ref bracket or bounded version23100 sweep_sur/cyl_spl_sur/VBL_SURF inline block. Four support interval fields each have a Boolean plus optional double. Inline procedural bodies retained verbatim; this UV reader does not claim their geometry decoded. Explicit plane field grammar is supported but not present among the new outer-support cases in this four-file subset.',
            'compact': 'Exactly7 typed fields: pointer-1,integer-1,pointer-1,nonzero integer selector,typed geometry pointer to intcurve,two stored offset doubles. Captured offsets are zero; nonzero compact offsets remain unsupported.',
            'slot_identity': 'Owning coedge->edge.curve must equal the typed compact curve pointer. Reciprocal owning coedge ring and face loop chain establish parentface.surface. The blob-local subtype catalog resolves this surface and parent intcurve ordered support definitions to the same unique definition index. Only then must selector magnitude1/2 agree with ordered UV slot0/1.',
            'sign': 'Both positive and negative selector values are captured. Sign is retained literally; no reversal, surface sense or curve-parameter transformation inferred.'},
        'limitations': [
            'Stored UV control caches are approximations; no direct API UV evaluator was captured. Independent polynomial checks validate decoding/evaluation of those stored fields only.',
            'The compact parent identity requires a namespace-qualified spline support. Direct plane-only support identity and ambiguous repeated support identities are rejected; matching plane coordinates is not a substitute.',
            'Opaque inline procedural surface definitions are strictly bracket/version/bounds framed and replayable but not procedurally evaluated by this reader.',
            'Inline allocation numbers, geometry record pointers, global inspection indices and native Design object IDs are separate namespaces.',
            'Nonzero compact offsets, rational UV controls, unobserved degrees/forms/selectors, missing parent UV slots and unresolved namespace or topology remain unsupported.',
            'This focused report covers four saved archives/eight blobs. Its counts are diagnostic recovery within that subset, not whole-format coverage.'],
        'samples': [], 'independent_UV_checks': [], 'old_layout_controls': [], 'malformed_guards': []}
    totals = {'blobs': 0, 'new_explicit': 0, 'new_compact': 0, 'prior_explicit': 0, 'byte_replays': 0}
    seen_checks = set()
    saved = None

    def independent(cache):
        points, knots, degree = cache['control_points_uv'], cache['knots'], cache['degree']
        errors = []
        for fraction in (.25, .5, .75):
            a, b = cache['parameter_domain']
            parameter = a+(b-a)*fraction

            @lru_cache(None)
            def basis(index, order):
                if order == 0:
                    return float(knots[index] <= parameter < knots[index+1])
                left_span, right_span = knots[index+order]-knots[index], knots[index+order+1]-knots[index+1]
                left = (parameter-knots[index])/left_span*basis(index, order-1) if left_span else 0.
                right = (knots[index+order+1]-parameter)/right_span*basis(index+1, order-1) if right_span else 0.
                return left+right

            expected = [sum(basis(i, degree)*point[axis] for i, point in enumerate(points)) for axis in (0, 1)]
            actual = evaluate_pcurve(cache, parameter)
            error = math.dist(actual, expected)
            assert error < 1e-9, (parameter, actual, expected)
            errors.append(error)
        return {'method': 'Independent Cox basis summation versus existing de Boor evaluation at three interior parameters',
                'sample_count': 3, 'maximum_error_uv': max(errors)}

    for filename in files:
        entry = {'file': filename, 'blobs': []}
        truth = json.loads((root/filename).parent.joinpath('ground_truth.json').read_text())
        entry['capture_evidence'] = {'sample_present': any(s['file'] == Path(filename).name for s in truth['samples']),
            'API_UV_getter_captured': False, 'scope': 'Saved native export; no API truth injected into UV or support identity fields'}
        old_control_added = False
        for member, blob in read_members(root/filename, zstd_library).items():
            if '/Breps.BlobParts/' not in member or not member.endswith(('.smb', '.smbh')):
                continue
            parsed = inspect_asm(blob)
            catalog = decode_asm_subtypes(blob, parsed=parsed)
            topology = decode_topology(parsed, subtype_catalog=catalog)
            nodes = {node['index']: node for node in topology['nodes']}
            row = {'member': member, 'new_records': [], 'prior_explicit_count': 0, 'unresolved_pcurves': []}
            totals['blobs'] += 1
            for record in parsed['records']:
                if record['name'] != 'pcurve' or record['section'] != 'geometry':
                    continue
                try:
                    old = _decode_observed_pcurve(record)
                except (ValueError, IndexError):
                    old = None
                if old is not None:
                    totals['prior_explicit'] += 1
                    row['prior_explicit_count'] += 1
                    if not old_control_added:
                        assert decode_pcurve(record) == old
                        report['old_layout_controls'].append({'file': filename, 'member': member, 'record_index': record['index'],
                            'default_dictionary_unchanged': True})
                        old_control_added = True
                    continue
                try:
                    compact = record['tokens'][3]['value'] != 0
                    decoded = (decode_compact_pcurve(record, parsed['records'], nodes, catalog) if compact else decode_pcurve_variants(record))
                    counters = 'new_compact' if compact else 'new_explicit'
                    totals[counters] += 1
                    raw = b'\x0d\x06pcurve'+encode_pcurve_fields(record['tokens'])+b'\x11'
                    assert raw == blob[record['offset']:record['end_offset']]
                    totals['byte_replays'] += 1
                    assert nodes[record['index']]['uv_curve'] == decoded
                    result = {'record_index': record['index'], 'layout': counters, 'expected_uv_cache': decoded,
                        'full_typed_record_replay': {'byte_count': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'matches': True}}
                    support = decoded.get('stored_support_definition', {})
                    key = (compact, decoded['degree'], decoded['stored_prefix_integer'], support.get('kind'), support.get('procedural_subtype'),
                           tuple(support.get('stored_interval_flags', [])))
                    if key not in seen_checks:
                        checked = independent(decoded)
                        checked.update(file=filename, member=member, record_index=record['index'], layout=counters,
                                       degree=decoded['degree'], stored_prefix_integer=decoded['stored_prefix_integer'])
                        report['independent_UV_checks'].append(checked)
                        seen_checks.add(key)
                    row['new_records'].append(result)
                except (ValueError, IndexError, KeyError) as error:
                    row['unresolved_pcurves'].append({'index': record['index'], 'reason': str(error)})
            assert not row['unresolved_pcurves'], (filename, member, row['unresolved_pcurves'])
            entry['blobs'].append(row)
            if filename.startswith('solidsweeps-') and member.endswith('.smbh'):
                saved = blob, parsed, catalog, nodes
        report['samples'].append(entry)

    blob, parsed, catalog, nodes = saved
    records = parsed['records']
    explicit = copy.deepcopy(records[116])
    compact = records[124]

    def reject(label, action):
        try:
            action()
        except (ValueError, IndexError, KeyError) as error:
            report['malformed_guards'].append({'label': label, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError(label+' was accepted')

    changed = copy.deepcopy(explicit)
    del changed['tokens'][29]
    reject('Finite support bound missing its double', lambda: decode_pcurve_variants(changed))
    changed2 = copy.deepcopy(explicit)
    changed2['tokens'][24]['value'] = -1
    reject('Negative inline surface allocation reference', lambda: decode_pcurve_variants(changed2))
    changed3 = copy.deepcopy(explicit)
    changed3['tokens'][12]['value'] = 0
    reject('Unsupported compact knot multiplicity', lambda: decode_pcurve_variants(changed3))
    changed4 = copy.deepcopy(compact)
    changed4['tokens'][3]['value'] = -2
    reject('Selector magnitude disagrees with independently matched parent support', lambda: decode_compact_pcurve(changed4, records, nodes, catalog))
    changed5 = copy.deepcopy(compact)
    changed5['tokens'][4]['value'] = 27
    reject('Geometry pointer targets a surface instead of an intcurve', lambda: decode_compact_pcurve(changed5, records, nodes, catalog))
    stale = copy.deepcopy(records)
    stale[27]['tokens'][6]['value'] += 1
    reject('Stale parent namespace host', lambda: decode_compact_pcurve(compact, stale, nodes, catalog))
    report['validation'] = dict(totals, saved_files=len(files), new_UV_caches=totals['new_explicit']+totals['new_compact'],
        independent_UV_layout_checks=len(report['independent_UV_checks']), independent_UV_samples=3*len(report['independent_UV_checks']),
        old_layout_controls=len(report['old_layout_controls']), malformed_guards_passed=len(report['malformed_guards']),
        API_UV_evaluator_claims=0, selector_sign_interpretations=0, new_API_calls=0)
    return report


def decode_compact_pcurve(record, records, nodes, subtype_catalog):
    """Postpass compact pcurve -> typed curve UV slot -> parent support identity."""
    from decode_asm_subtypes import _record_fingerprint, resolve_asm_subtype

    tokens = _header(record)
    selector = read_token(tokens, 3, 'integer')
    if len(tokens) != 7 or selector not in (1, -1, 2, -2):
        raise ValueError('Only observed compact pcurve selectors positive/negative1/2 supported')
    target = read_token(tokens, 4, 'pointer')
    offset = [read_token(tokens, 5+i, 'double') for i in range(2)]
    _finite(offset)
    # Nonzero compact shifts have not been contrasted; retain unsupported rather
    # than applying a translation because the explicit representation has one.
    if offset != [0., 0.]:
        raise ValueError('Nonzero compact pcurve offset semantics uncontrasted')
    limit = next((r['index'] for r in records if r['record_kind'] == 'marker'), len(records))
    by = {r['index']: r for r in records[:limit]}
    all_records = {r['index']: r for r in records}

    def resolve_surface(record_index, token_start):
        proof = resolve_asm_subtype(subtype_catalog, record_index, token_start, expected_kind='surface')
        for identity in {record_index, proof['target_definition']['record_index']}:
            host = all_records.get(identity)
            if host is None or subtype_catalog['record_fingerprints'].get(str(identity)) != _record_fingerprint(host):
                raise ValueError('Compact pcurve namespace host is stale or belongs to another blob catalog')
        return proof
    if target not in by or by[target]['name'] != 'intcurve-curve':
        raise ValueError('Compact pcurve typed geometry pointer does not name an initial intcurve')
    parent = nodes.get(target)
    cache = parent.get('bspline_curve') if parent and parent['kind'] == 'intcurve-curve' else None
    if cache is None:
        raise ValueError('Compact pcurve parent XYZ/UV caches unresolved')
    if cache.get('procedural_subtype') == 'par_int_cur':
        supports = [cache['stored_support_definition'], {'kind': 'null_surface'}]
        uv_slots = [cache['stored_embedded_uv_cache'], None]
    elif cache.get('procedural_subtype') == 'int_int_cur':
        supports, uv_slots = cache.get('stored_supports'), cache.get('stored_embedded_uv_caches')
        if supports is None or uv_slots is None:
            from decode_asm_subtypes import expand_asm_subtype_record
            from decode_intersection_curve_variants import decode_intersection_curve_variants
            source_record = by[target]
            if source_record['tokens'][5]['value'] == 'ref':
                source_record = expand_asm_subtype_record(source_record, subtype_catalog, records)['record']
            ordered = decode_intersection_curve_variants(source_record)
            supports, uv_slots = ordered['stored_supports'], ordered['stored_embedded_uv_caches']
    else:
        raise ValueError('Compact pcurve parent subtype has no admitted ordered UV/support slots')
    if supports is None or uv_slots is None or len(supports) != 2 or len(uv_slots) != 2:
        raise ValueError('Compact pcurve parent lacks two explicitly ordered support/UV slots')
    coedges = [node for node in nodes.values() if node['kind'] == 'coedge' and node.get('pcurve_index') == record['index']]
    if len(coedges) != 1:
        raise ValueError('Compact pcurve must have one explicit owning coedge')
    coedge = coedges[0]
    edge = nodes.get(coedge['edge_index'])
    loop = nodes.get(coedge.get('loop_index'))
    face = nodes.get(loop['face_index']) if loop and loop['kind'] == 'loop' else None
    if (edge is None or edge['kind'] != 'edge' or edge['curve_index'] != target
            or face is None or face['kind'] != 'face'):
        raise ValueError('Compact pcurve/coedge/edge/loop/face typed source route disagrees')
    # Independently bound the owning coedge ring and face loop chain. No UV or
    # world-coordinate coincidence establishes this parent relationship.
    ring, current = [], loop['first_coedge_index']
    while current not in ring:
        node = nodes.get(current)
        if node is None or node['kind'] != 'coedge' or node.get('loop_index') != loop['index'] or len(ring) > len(nodes):
            raise ValueError('Compact pcurve owning loop ring is not bounded/reciprocal')
        following = nodes.get(node['next_coedge_index'])
        if following is None or following.get('previous_coedge_index') != current:
            raise ValueError('Compact pcurve coedge next/previous links disagree')
        ring.append(current)
        current = node['next_coedge_index']
    if current != loop['first_coedge_index'] or coedge['index'] not in ring:
        raise ValueError('Compact pcurve coedge is not in the claimed closed owning ring')
    loops, current = [], face['first_loop_index']
    while current is not None:
        node = nodes.get(current)
        if current in loops or node is None or node['kind'] != 'loop' or node['face_index'] != face['index']:
            raise ValueError('Compact pcurve face/loop ownership not reciprocal')
        loops.append(current)
        current = node['next_loop_index']
    if loop['index'] not in loops:
        raise ValueError('Compact pcurve loop absent from claimed parent face')
    surface_id = face['surface_index']
    if surface_id not in by or by[surface_id]['name'] != 'spline-surface':
        raise ValueError('Compact pcurve parent surface has no admitted explicit inline namespace identity')
    face_support = resolve_surface(surface_id, 4)
    definition = face_support['target_definition']['definition_index']
    matches, support_proofs = [], []
    for slot, support in enumerate(supports):
        if support.get('kind') != 'spline':
            continue
        fields = support.get('stored_definition', [])
        starts = [token for token in fields if token['kind'] == 'subtype_start']
        if not starts:
            raise ValueError('Compact pcurve support spline has no original explicit subtype location')
        # Raw offsets locate the source definition even after an expanded
        # top-level ref imports fields from a different host record.
        locations = [block for block in subtype_catalog['blocks'] if block['byte_start'] == starts[0]['offset']]
        if len(locations) != 1:
            raise ValueError('Compact pcurve support source span missing/ambiguous in namespace catalog')
        location = locations[0]
        proof = resolve_surface(location['record_index'], location['token_start'])
        support_proofs.append({'slot': slot, 'namespace_proof': proof})
        if proof['target_definition']['definition_index'] == definition:
            matches.append(slot)
    if len(matches) != 1 or matches[0] != abs(selector)-1:
        raise ValueError('Compact pcurve selector does not agree with unique parent-face/support namespace identity')
    slot = matches[0]
    uv = uv_slots[slot]
    if uv is None or uv.get('weights') or not uv.get('raw_control_points'):
        raise ValueError('Compact pcurve selected support has no admitted explicit polynomial UV cache')
    raw = uv['raw_control_points']
    if any(len(point) != 2 for point in raw):
        raise ValueError('Compact pcurve selected cache is not two-dimensional UV')
    _finite(uv['knots']+[value for point in raw for value in point])
    return {'degree': uv['degree'], 'knots': uv['knots'], 'stored_compact_knots': uv['stored_compact_knots'],
        'raw_control_points_uv': raw, 'parameter_offset_uv': offset, 'control_points_uv': raw,
        'weights': [], 'parameter_domain': uv['parameter_domain'], 'stored_form_code': uv['stored_form_code'],
        'stored_prefix_integer': selector, 'stored_selected_support_slot': slot,
        'stored_intcurve_record_pointer': target, 'owning_coedge_index': coedge['index'],
        'parent_loop_index': loop['index'], 'parent_face_index': face['index'], 'parent_surface_record_index': surface_id,
        'parent_surface_namespace': face_support, 'parent_intcurve_support_namespaces': support_proofs,
        'selected_support_definition_index': definition,
        'representation': 'Stored embedded UV NUBS cache selected through typed parent curve and exact parent-surface inline identity',
        'flag_scope': 'Magnitude of observed selector agrees support slot1/2; sign retained literally, without reversal/orientation/parameter remapping semantics',
        'coordinate_system': 'Selected explicitly identified parent support UV cache; no implicit surface evaluation or world conversion',
        'cache_status': 'Stored UV cache recovered by typed topology and namespace identity; exact coedge/cache parameterization and API evaluator equivalence unresolved',
        'scope': SCOPE}
