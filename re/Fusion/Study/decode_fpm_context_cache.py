"""Qualified FPM Line-context cache fields, separate from source evaluation.

The55-byte shape alone does not identify a Line. Admission requires separately
qualified recipe/tag/FPM owner agreement in the bounded alternate view. Stored
point/vector fields are checked against that cache only after its identity joins.
"""
import math
import struct

from decode_body_selections import ANCHOR, HELPER, SUPPORT
from decode_recipe_components import decode_counted_recipe
from decode_selection_context_recipes import TOPOLOGY
from decode_sketch import reference

CONTEXT = '50AEE8B4-9456-4DD7-847D-6F6C909BBB9D'
FEATURES = {'Chamfer': 'F757D611-217B-4B72-9C41-B617BDCE43DA', 'Fillet': 'A07D5F17-68CB-464D-9935-BF68E98A865F'}
SCOPE = 'Observed FPM-qualified Fillet/Chamfer Line context point/vector cache and exact correspondence to bounded alternate-view start/displacement; historical source identity, chronology, general evaluator and flag/scale semantics remain unresolved'


def encode_fpm_context_cache(item):
    """Replay all55 stored context bytes; flags and float signs stay literal."""
    return bytes.fromhex(item['stored_prefix_hex'])+struct.pack('<6d', *(item['cached_raw_point']+item['stored_raw_vector']))+bytes.fromhex(item['stored_tail_hex'])


def inspect_fpm_context_cache(data, records, track):
    """Additional context fields for a track produced from identical source data.

    Native descriptor/context/recipe/owner/anchor/support identities are rechecked.
    The prior FPM pass supplies the independently qualified same-blob topology;
    an unqualified numeric track is deliberately insufficient for this helper.
    """
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: rows[0] for identity, rows in grouped.items() if len(rows) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('FPM context typed native reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]

    native = track['numeric_descriptor_correspondence']
    qualified = track['alternative_view_correspondence']
    attribute = track['FPM_attribute']
    if (qualified is None or qualified['recipe_and_FPM_owner_agree'] is not True
            or qualified['state_slot'] != 0 or qualified['pointer_side'] != 0
            or track['alternative_view_unresolved_reason'] is not None
            or qualified['cached_view_edge']['primitive_kind'] != 'Line'
            or attribute['cached_attribute_owner_edge']['primitive_kind'] != 'Line'):
        raise ValueError('FPM context requires a separately qualified named-recipe/FPM Line owner agreement')
    descriptor_id = native['numerically_matching_descriptor_object_id']
    if (descriptor_id != track['stored_tracking_literal'] or descriptor_id != attribute['stored_tracking_literal']
            or qualified['recipe_object_id'] != native['primary_recipe_object_id']
            or qualified['FPM_owner_edge_origin']['geometry_entity_ordinal'] != attribute['owner_edge_geometry_ordinal']
            or qualified['FPM_owner_edge_origin']['inspection_record_index'] != attribute['owner_edge_record_index']
            or qualified['FPM_attribute_origin']['inspection_record_index'] != attribute['attribute_record_index']):
        raise ValueError('FPM context prerequisite tracking/recipe/owner provenance disagrees')
    _, descriptor = typed(descriptor_id, TOPOLOGY)
    owner = native['descriptor_owner_object_id']
    owner_kind = native['descriptor_owner_kind']
    if owner_kind not in FEATURES:
        raise ValueError('FPM context role requires captured Fillet or Chamfer owner')
    typed(owner, FEATURES[owner_kind])
    if (len(descriptor) != 276 or descriptor[:3] != bytes(3) or descriptor[3] not in (0, 1)
            or struct.unpack_from('<I', descriptor, 15)[0] != 1
            or descriptor[171:183] != struct.pack('<QI', 2, 1)
            or struct.unpack_from('<I', descriptor, 194)[0] != 1
            or reference(descriptor, 265) != owner
            or reference(descriptor, 4) != native['primary_recipe_object_id']):
        raise ValueError('FPM context descriptor frame/recipe/owner disagrees')
    recipe_rec, _ = typed(native['primary_recipe_object_id'], '7ACC2A03-0261-4879-A14A-A93D661A5BDC')
    recipe = decode_counted_recipe(data, recipe_rec)
    if (recipe['payload_kind'] != 'edge_recipe_data' or recipe['payload_hex'] != native['primary_recipe_payload_hex']
            or recipe['name_table'] != native['primary_recipe_name_table']):
        raise ValueError('FPM context primary recipe differs from independently qualified input')
    context_id = reference(descriptor, 183)
    _, payload = typed(context_id, CONTEXT)
    if (context_id != native['context_object_id'] or len(payload) != 55 or payload[:2] != bytes(2)
            or payload[50:] != bytes.fromhex('0000000100')):
        raise ValueError('Unobserved FPM55-byte context extent/prefix/tail or role identity')
    anchor_id = reference(descriptor, 198)
    _, anchor = typed(anchor_id, ANCHOR)
    if (anchor_id != native['body_anchor_object_id'] or len(anchor) != 102 or anchor[:2] != bytes(2)
            or reference(anchor, 80) != native['native_body_object_id']
            or reference(anchor, 91) != native['historical_source_owner_object_id']):
        raise ValueError('FPM context historical anchor correspondence disagrees')
    helper_id, support_id = reference(descriptor, 239), reference(descriptor, 253)
    _, helper = typed(helper_id, HELPER)
    _, support = typed(support_id, SUPPORT)
    if (helper_id != native['helper_object_id'] or support_id != native['support_object_id']
            or helper != bytes.fromhex('0001000000000000000000000000')
            or len(support) != 58 or support[:12] != bytes.fromhex('000000000000010101000000')
            or reference(support, 12) != native['historical_source_owner_object_id']
            or reference(support, 31) != descriptor_id or support[-8:] != bytes(8)):
        raise ValueError('FPM context descriptor/helper/support reciprocity disagrees')
    values = list(struct.unpack_from('<6d', payload, 2))
    point, vector = values[:3], values[3:]
    norm = math.hypot(*vector)
    if not all(math.isfinite(x) for x in values) or not math.isfinite(norm) or norm <= 1e-12:
        raise ValueError('FPM context point/vector cache is nonfinite or degenerate')
    curve = qualified['cached_view_edge']
    domain = curve['parameter_domain']
    if (len(domain) != 2 or not all(math.isfinite(x) for x in domain) or not domain[1] > domain[0]
            or len(curve['raw_origin']) != 3 or len(curve['direction']) != 3):
        raise ValueError('FPM context prerequisite Line domain/vector invalid')
    origin, direction = curve['raw_origin'], curve['direction']
    if not all(math.isfinite(x) for x in origin+direction):
        raise ValueError('FPM context prerequisite Line cache nonfinite')
    expected_start = [o+domain[0]*d for o, d in zip(origin, direction)]
    expected_end = [o+domain[1]*d for o, d in zip(origin, direction)]
    expected_vector = [b-a for a, b in zip(expected_start, expected_end)]
    owner_cache = attribute['cached_attribute_owner_edge']
    owner_points = [item['raw_point'] for item in owner_cache['endpoint_caches']]

    def same(a, b):
        return len(a) == len(b) and all(math.isclose(x, y, rel_tol=0, abs_tol=1e-9) for x, y in zip(a, b))

    if (len(owner_points) != 2 or not same(expected_start, owner_points[0]) or not same(expected_end, owner_points[1])
            or not same(point, expected_start) or not same(vector, expected_vector)):
        raise ValueError('FPM native context does not agree with qualified-view Line start/displacement caches')
    unit = [x/norm for x in vector]
    if not same(unit, direction):
        raise ValueError('FPM context normalized vector disagrees with qualified-view Line direction')
    result = {'numerically_matching_descriptor_object_id': descriptor_id, 'descriptor_owner_object_id': owner,
        'descriptor_owner_kind': owner_kind, 'context_object_id': context_id, 'context_class_guid': CONTEXT,
        'primary_recipe_object_id': recipe['object_id'], 'body_anchor_object_id': anchor_id,
        'native_body_object_id': native['native_body_object_id'], 'historical_source_owner_object_id': native['historical_source_owner_object_id'],
        'history_blob_member': native['history_blob_member'], 'support_object_id': support_id,
        'FPM_attribute_record_index': attribute['attribute_record_index'],
        'FPM_owner_edge_geometry_ordinal': attribute['owner_edge_geometry_ordinal'],
        'FPM_owner_edge_record_index': attribute['owner_edge_record_index'],
        'qualified_view_state_slot': 0, 'qualified_view_pointer_side': 0,
        'qualified_view_edge_origin': qualified['FPM_owner_edge_origin'],
        'stored_prefix_hex': payload[:2].hex(), 'cached_raw_point': point, 'stored_raw_vector': vector,
        'derived_unit_direction': unit, 'stored_vector_magnitude': norm,
        'stored_tail_hex': payload[50:].hex(), 'stored_tail_bytes': list(payload[50:]), 'payload_hex': payload.hex(),
        'cache_correspondence': {'point_matches_qualified_line_start': True, 'vector_matches_qualified_endpoint_displacement': True,
            'normalized_vector_matches_qualified_unit_direction': True,
            'qualified_start_point': expected_start, 'qualified_end_point': expected_end,
            'qualified_line_parameter_domain': domain},
        'semantic_gate': 'Typed Fillet/Chamfer descriptor primary recipe, explicit native/body/blob tracking, and separately qualified alternate-view named-face/endpoint incidence agree with the reciprocal FPM Line owner before interpreting cache fields',
        'vector_scale_status': 'Observed stored vector equals qualified endpoint displacement; its magnitude stays separate from the unit direction. General context scale, curve parameterization and trim semantics remain unassigned.',
        'tail_status': 'Exact literal0000000100 retained without flag, direction, closure or state semantics',
        'coordinate_scope': 'Raw stored root-component cache values; no selected-edge API evaluator was captured for these fixtures, and no occurrence/world conversion is inferred',
        'qualified_historical_state': None, 'exact_selected_source_identity': None, 'source_geometry': None,
        'scope': SCOPE}
    if encode_fpm_context_cache(result) != payload:
        raise ValueError('FPM context55-byte exact replay disagrees')
    return result


def decode_fpm_context_cache(data, records, fpm_summary):
    """Additional decoded/unresolved/scope; never mutate or clear prior failures."""
    decoded, unresolved = [], []
    for track in fpm_summary['tracks']:
        try:
            decoded.append(inspect_fpm_context_cache(data, records, track))
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
            unresolved.append({'stored_tracking_literal': track.get('stored_tracking_literal'),
                'numerically_matching_descriptor_object_id': track.get('numeric_descriptor_correspondence', {}).get('numerically_matching_descriptor_object_id'),
                'reason': str(error)})
    return {'decoded': decoded, 'unresolved': unresolved, 'scope': SCOPE}


def validate_fixtures(root, zstd_library=None):
    """Ten context caches through eight saved FPM cases and two role controls."""
    import copy
    import json
    from pathlib import Path
    from decode_basics import decode_basics
    from decode_fpm_tracking import decode_fpm_selection_tracking
    from fusion_archive import read_members
    from fusion_metadata import design_records

    root = Path(root)
    files = ['edgemodes-52695761f185/chamfer_multiple.f3d', 'edgemodes-52695761f185/fillet_curvature.f3d',
             'edgemodes-87edbf67527b/chamfer_angle.f3d', 'edgemodes-87edbf67527b/chamfer_angle_flipped.f3d',
             'edgemodes-87edbf67527b/fillet_multiple.f3d', 'edgemodes-87edbf67527b/fillet_asymmetric.f3d',
             'edgemodes-87edbf67527b/fillet_chord.f3d', 'edgemodes-87edbf67527b/fillet_variable.f3d']
    report = {'scope': SCOPE, 'interfaces': {
        'individual': 'inspect_fpm_context_cache(data,records,track)',
        'summary': 'decode_fpm_context_cache(data,records,fpm_summary)',
        'exact_replay': 'encode_fpm_context_cache(item)',
        'validator': 'validate_fixtures(root,zstd_library=None)',
        'integration': 'Attach only to the corresponding FPM numeric track as cached_context_line_comparison, or retain separate fpm_context_cache summary. Keep original FPM source/state fields null and preserve initial selection-context/tool failures.',
        'expected_outputs': 'samples[].expected_summary and controls[].expected_summary contain complete context helper outputs'},
        'framing': {
            'context': 'Typed50AEE context is exactly55bytes: zero16, six finite float64 values, exact trailer0000000100. Full payload byte replay preserves float signs and trailer literals.',
            'semantic_gate': 'Existing FPM pass must independently qualify a named-recipe/FPM Line owner in slot0/side0 alternate view. Native descriptor context reference, edge recipe bytes/name table, Fillet/Chamfer owner GUID, anchor/helper and reciprocal source support are rechecked.',
            'observed_correspondence': 'First three float64 fields match the qualified Line start and typed owner endpoint cache. Last three match qualified end-minus-start displacement; separately normalized direction agrees the qualified unit Line direction. No coordinates select an entity.',
            'trailer': 'Five literal bytes[0,0,0,1,0] retained. No boolean orientation, closure, selection, state or trim semantics assigned.'},
        'limitations': [
            'No selected-edge geometry or evaluator getters were captured for these old EdgeMode samples. Comparisons in the FPM cases are independent serialized-context versus qualified ASM cache comparisons, not API evaluator equivalence.',
            'Qualified alternate-view provenance stays literal slot0/side0. Historical selected-source identity and chronological/current/final-state interpretation remain unassigned.',
            'The55-byte class/shape alone does not identify natural curve type. Only already-qualified FPM Line tracks enter this decoder; same-shaped Revolve/Silhouette contexts are exclusion/corroboration controls, not new attachments.',
            'Stored vector magnitude3 is observed endpoint displacement scale here. General context vector scale, natural-curve parameterization, trim/closure and trailer semantics remain unresolved.',
            'The recorded raw caches occur in controlled root-component fixtures. No header-unit conversion, occurrence transform or general world-coordinate claim is made.'],
        'samples': [], 'controls': [], 'comparisons': [], 'malformed_guards': []}
    loaded = {}

    def load(filename):
        stream = decode_basics(root/filename, zstd_library)['streams'][0]
        members = read_members(root/filename, zstd_library)
        data = members[stream['member']]
        records, _ = design_records(data, members[stream['member'].replace('BulkStream.dat', 'MetaStream.dat')])
        fpm = decode_fpm_selection_tracking(data, records, stream['features'], stream['member'], members,
            stream['body_asm_identifiers'], stream['body_selections'])
        return data, records, stream, fpm

    def check(label, actual, expected):
        assert actual == expected, (label, actual, expected)
        report['comparisons'].append({'label': label, 'actual': actual, 'expected': expected, 'passed': True})

    def same(a, b):
        return len(a) == len(b) and all(math.isclose(x, y, rel_tol=0, abs_tol=1e-9) for x, y in zip(a, b))

    count = 0
    for filename in files:
        data, records, stream, fpm = load(filename)
        before = copy.deepcopy(fpm)
        output = decode_fpm_context_cache(data, records, fpm)
        check(filename+' every qualified FPM track has one context cache', len(output['decoded']), len(fpm['tracks']))
        check(filename+' no additional context-cache failure', output['unresolved'], [])
        check(filename+' prior FPM summary preserved exactly', fpm == before, True)
        for item in output['decoded']:
            count += 1
            descriptor = item['numerically_matching_descriptor_object_id']
            check(filename+f' descriptor{descriptor} exact55-byte replay', encode_fpm_context_cache(item).hex(), item['payload_hex'])
            check(filename+f' descriptor{descriptor} literal trailer retained', item['stored_tail_bytes'], [0, 0, 0, 1, 0])
            check(filename+f' descriptor{descriptor} captured displacement magnitude remains3', item['stored_vector_magnitude'], 3.)
            comparison = item['cache_correspondence']
            check(filename+f' descriptor{descriptor} point equals qualified start', same(item['cached_raw_point'], comparison['qualified_start_point']), True)
            check(filename+f' descriptor{descriptor} vector equals qualified endpoint displacement',
                  same(item['stored_raw_vector'], [b-a for a, b in zip(comparison['qualified_start_point'], comparison['qualified_end_point'])]), True)
            check(filename+f' descriptor{descriptor} natural/evaluated source geometry remains unclaimed', item['source_geometry'], None)
            check(filename+f' descriptor{descriptor} historical state remains unassigned', item['qualified_historical_state'], None)
            check(filename+f' descriptor{descriptor} exact selected-source identity remains unassigned', item['exact_selected_source_identity'], None)
        actual = next(sample for sample in json.loads((root/filename).parent.joinpath('ground_truth.json').read_text())['samples'] if sample['file'] == Path(filename).name)
        report['samples'].append({'file': filename, 'expected_summary': output,
            'API_evidence': {'actual_edge_sets': actual['settings']['edge_sets'],
                'selected_edge_geometry_getter_captured': False,
                'scope': 'Actual tool settings only. Context values are compared with separately qualified serialized edge caches, not an invented source API evaluator.'}})
        loaded[Path(filename).name] = data, records, stream, fpm, output

    normal = loaded['chamfer_angle.f3d'][-1]['decoded'][0]
    flipped = loaded['chamfer_angle_flipped.f3d'][-1]['decoded'][0]
    check('Actual Chamfer flip does not alter source context payload', normal['payload_hex'], flipped['payload_hex'])
    vector_signs = sorted({tuple(item['derived_unit_direction']) for sample in report['samples'] for item in sample['expected_summary']['decoded']})
    check('Distinct named edge operands cover both stored direction signs', [list(x) for x in vector_signs], [[0., -1., 0.], [0., 1., 0.]])

    # Same schema in independently captured API roles corroborates field layout,
    # but no FPM role exists and the new helper must not attach it.
    for filename, descriptor_id in [('revolveaxes-14700158dba9/brep_edge_offset_x.f3d', 350),
                                    ('silhouettedirections-805c2eaa2411/faces_brep_edge_x.f3d', 366)]:
        data, records, stream, fpm = load(filename)
        output = decode_fpm_context_cache(data, records, fpm)
        check(filename+' same-shaped context is not an FPM attachment', output['decoded'], [])
        by_id = {r.object_id: r for r in records if r.is_primary}
        desc = by_id[descriptor_id]
        context_id = reference(data[desc.body:desc.end], 183)
        rec = by_id[context_id]
        payload = data[rec.body:rec.end]
        check(filename+' independently corroborated context schema', [rec.class_guid, len(payload), payload[50:].hex()], [CONTEXT, 55, '0000000100'])
        values = list(struct.unpack_from('<6d', payload, 2))
        sample = next(s for s in json.loads((root/filename).parent.joinpath('ground_truth.json').read_text())['samples'] if s['file'] == Path(filename).name)
        if filename.startswith('revolveaxes'):
            actual = sample['actual_axis']
            start, end = actual['start_cm'], actual['end_cm']
        else:
            actual = sample['actual_direction']
            start, end = actual['start_vertex_cm'], actual['end_vertex_cm']
        check(filename+' point vs actual independent edge getter', same(values[:3], start), True)
        check(filename+' stored vector vs actual endpoint getter displacement', same(values[3:], [b-a for a, b in zip(start, end)]), True)
        report['controls'].append({'file': filename, 'expected_summary': output,
            'independent_API_corroboration': {'start_cm': start, 'end_cm': end, 'stored_context_point': values[:3],
                'stored_context_vector': values[3:], 'stored_vector_magnitude': math.hypot(*values[3:]),
                'scope': 'Actual getter comparison in an existing independent linear source role. No new FPM attachment or cross-role generalization.'}})

    data, records, stream, fpm, output = loaded['chamfer_angle.f3d']
    track, item = fpm['tracks'][0], output['decoded'][0]
    by_id = {r.object_id: r for r in records if r.is_primary}

    def reject(label, changed_data=data, changed_track=track):
        try:
            inspect_fpm_context_cache(changed_data, records, changed_track)
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
            report['malformed_guards'].append({'label': label, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError(label+' was accepted')

    context_rec = by_id[item['context_object_id']]
    for label, offset, replacement in [('Context point disagrees with qualified owner', 2, struct.pack('<d', 11.)),
                                       ('Degenerate stored context vector', 26, bytes(24)),
                                       ('Scaled vector disagrees with qualified displacement', 34, struct.pack('<d', -6.)),
                                       ('Unknown literal trailer frame', 53, b'\x02')]:
        changed = bytearray(data)
        changed[context_rec.body+offset:context_rec.body+offset+len(replacement)] = replacement
        reject(label, bytes(changed))
    desc_rec = by_id[item['numerically_matching_descriptor_object_id']]
    changed = bytearray(data)
    struct.pack_into('<Q', changed, desc_rec.body+184, item['primary_recipe_object_id'])
    reject('Context reference targets wrong native record class', bytes(changed))
    unqualified = copy.deepcopy(track)
    unqualified['alternative_view_correspondence'] = None
    reject('Numeric FPM correspondence without qualified Line view', changed_track=unqualified)
    recipe_rec = by_id[item['primary_recipe_object_id']]
    raw = bytes.fromhex(track['numeric_descriptor_correspondence']['primary_recipe_payload_hex'])
    start = data.find(raw, recipe_rec.body, recipe_rec.end)
    assert start >= 0
    changed = bytearray(data)
    struct.pack_into('<i', changed, start+12, 2)
    reject('Stale prerequisite recipe cannot validate altered native input', bytes(changed))
    report['validation'] = {'saved_FPM_files': len(files), 'qualified_context_caches': count, 'exact55_byte_payload_replays': count,
        'independent_API_schema_controls': len(report['controls']), 'comparisons_passed': len(report['comparisons']),
        'malformed_guards_passed': len(report['malformed_guards']), 'source_API_evaluator_claims': 0,
        'state_or_exact_source_identity_claims': 0, 'context_or_tool_failures_cleared': 0, 'new_API_calls': 0}
    return report
