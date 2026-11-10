"""Typed Boundary Fill sculpt tags in explicitly indexed ASM history snapshots.

Geometry pointers count geometry entities across the initial/trailing sections;
history journals have their own delta-state slots. Neither is a Design object ID
or the global inspection-record index. Journal pointer sides stay uninterpreted.
"""

import struct

from asm_records import INT64_ATTRIBUTE, inspect_asm

SCOPE = ('Observed SCULPT typed int64 face attributes, reciprocal snapshot owner chains and literal journal slot mentions; '
         'native tool numeric correspondence requires separate Design evidence; no final-state classification or history replay')
NAMES = ('SCULPT_TOOL_BODY', 'SCULPT_WORKPLANE_TOOL')


def decode_sculpt_tool_attributes(blob, *, parsed=None):
    """Return attributes/journal_states/unresolved/scope without mutating inputs.

    Strict failure raises ValueError. An attribute-free complete blob returns an
    empty result without attempting unrelated journal grammars. Contextual tag23
    framing is supplied by asm_records, not reinterpreted as a floating number.
    """
    parsed = inspect_asm(blob) if parsed is None else parsed
    if not parsed['complete_token_stream']:
        raise ValueError('Sculpt attributes require a complete ASM token stream')
    records = parsed['records']
    targets = [r for r in records if r['name'] == INT64_ATTRIBUTE]
    empty = {'attributes': [], 'journal_states': [], 'unresolved': [], 'scope': SCOPE}
    if not targets:
        return empty
    markers = [r for r in records if r['record_kind'] == 'marker']
    if [r['name'] for r in markers] != ['Begin-of-ASM-History-Data', 'End-of-ASM-History-Section', 'End-of-ASM-data']:
        raise ValueError('Unsupported sculpt section boundaries')
    if not markers[0]['index'] < markers[1]['index'] < markers[2]['index'] == len(records)-1:
        raise ValueError('Sculpt section marker order disagrees')
    entities = [r for r in records if r['record_kind'] == 'entity' and r['section'] in ('geometry', 'trailing_states')]
    ordinal = {r['index']: i for i, r in enumerate(entities)}
    if len(ordinal) != len(entities):
        raise ValueError('Duplicate ASM geometry inspection record indices')
    for r in entities:
        expected = 'geometry' if r['index'] < markers[0]['index'] else 'trailing_states'
        if r['section'] != expected or (expected == 'trailing_states' and r['index'] < markers[1]['index']):
            raise ValueError('Geometry entity crosses its explicit ASM section')

    def value(token, tag):
        v = token['value']
        if token['tag'] != tag or not isinstance(v, int) or isinstance(v, bool):
            raise ValueError('Sculpt typed integer/pointer field disagrees')
        return v

    def entity(slot, kind=None):
        if not isinstance(slot, int) or isinstance(slot, bool) or not 0 <= slot < len(entities):
            raise ValueError('Sculpt geometry pointer leaves geometry-entity table')
        r = entities[slot]
        if kind is not None and r['name'] != kind:
            raise ValueError('Sculpt geometry pointer target has wrong type')
        return r

    def pointer(record, field, kind=None, nullable=False):
        if not 0 <= field < len(record['tokens']):
            raise ValueError('Truncated sculpt owner pointer schema')
        slot = value(record['tokens'][field], 12)
        if nullable and slot == -1:
            return None
        entity(slot, kind)
        return slot

    # This is a separate namespace: delta-state slots are not geometry slots.
    history = [r for r in records if r['record_kind'] == 'entity' and r['section'] == 'history']
    if not history or history[0]['name'] != 'history_stream' or any(r['name'] != 'delta_state' for r in history[1:]):
        raise ValueError('Unsupported sculpt journal entity sequence')
    header = history[0]['tokens']
    if ([t['tag'] for t in header] != [4, 4, 4, 4, 12, 12, 12, 12]
            or [t['value'] for t in header[4:]] != [-1, 0, 1, -1]):
        raise ValueError('Unsupported sculpt history-stream header')
    states, mentions = [], {}
    for index, r in enumerate(history[1:]):
        ts = r['tokens']
        if (len(ts) < 11 or [t['tag'] for t in ts[:9]] != [4, 4, 4, 12, 12, 12, 12, 12, 11]
                or [ts[i]['value'] for i in (1, 2, 5, 6, 7, 8)] != [1, 0, index, -1, 0, False]):
            raise ValueError('Unsupported sculpt delta-state header/self slot')
        neighbors = [value(ts[i], 12) for i in (3, 4)]
        if any(v != -1 and not 0 <= v < len(history)-1 for v in neighbors):
            raise ValueError('Sculpt journal neighbor leaves delta-state table')
        if len(ts) == 11:
            if [(t['tag'], t['value']) for t in ts[9:]] != [(4, 0), (4, 0)]:
                raise ValueError('Unsupported empty sculpt journal state')
            triples = []
        else:
            if ([(t['tag'], t['value']) for t in ts[9:12]] != [(4, 1), (12, index), (4, 2)]
                    or [(t['tag'], t['value']) for t in ts[-3:]] != [(4, 0)]*3
                    or (len(ts)-15) % 3):
                raise ValueError('Unsupported sculpt journal entry-block framing')
            triples = ts[12:-3]
        count = len(triples)//3
        for j in range(count):
            flag, left, right = triples[j*3:j*3+3]
            if value(flag, 4) != 1:
                raise ValueError('Unsupported sculpt journal entry flag')
            for side, token in enumerate((left, right)):
                slot = value(token, 12)
                if slot != -1:
                    target = entity(slot)
                    mentions.setdefault(slot, []).append({'delta_state_slot': index,
                        'journal_record_index': r['index'], 'entry_ordinal': j, 'pointer_side': side,
                        'pointer_token_offset': token['offset'], 'geometry_entity_ordinal': slot,
                        'target_inspection_record_index': target['index']})
        states.append({'delta_state_slot': index, 'inspection_record_index': r['index'],
                       'stored_header_integer': value(ts[0], 4), 'neighbor_slots_fields_3_4': neighbors,
                       'entry_count': count, 'raw_header_values': [t['value'] for t in ts[:9]],
                       'scope': 'Reciprocal journal links and typed entry slots; chronological direction and transition-side semantics unresolved'})
    for s in states:
        for side, neighbor in enumerate(s['neighbor_slots_fields_3_4']):
            if neighbor != -1 and states[neighbor]['neighbor_slots_fields_3_4'][1-side] != s['delta_state_slot']:
                raise ValueError('Sculpt delta-state neighbor links are not reciprocal')
    starts = [s['delta_state_slot'] for s in states if s['neighbor_slots_fields_3_4'][0] == -1]
    chain, current = [], starts[0] if len(starts) == 1 else None
    while current is not None and current != -1:
        if current in chain:
            raise ValueError('Cyclic sculpt journal neighbor chain')
        chain.append(current)
        current = states[current]['neighbor_slots_fields_3_4'][1]
    if len(chain) != len(states):
        raise ValueError('Sculpt journal neighbors do not span one bounded chain')

    def member_chain(head, next_field, expected_kind, desired, owner_field, owner):
        current, seen = head, []
        while current is not None:
            if current in seen or len(seen) > len(entities):
                raise ValueError('Cyclic sculpt snapshot topology chain')
            seen.append(current)
            r = entity(current, expected_kind)
            if pointer(r, owner_field) != owner:
                raise ValueError('Sculpt snapshot topology ownership is not reciprocal')
            current = pointer(r, next_field, expected_kind, True)
        if desired not in seen:
            raise ValueError('Sculpt owner is absent from its parent topology chain')
        return seen

    attributes = []
    for r in targets:
        ts = r['tokens']
        if (r['index'] not in ordinal or len(ts) != 11
                or [t['tag'] for t in ts] != [12, 4, 12, 12, 12, 21, 21, 21, 21, 7, 23]
                or [t['value'] for t in ts[5:9]] != [2, 1, 1, 2]
                or ts[9]['value'] not in NAMES or ts[10]['kind'] != 'integer64'):
            raise ValueError('Unsupported SCULPT typed attribute layout/name')
        slot = ordinal[r['index']]
        owner_id = pointer(r, 4, 'face')
        face = entity(owner_id, 'face')
        current, previous, achain = pointer(face, 0, nullable=True), None, []
        while current is not None:
            if current in achain or len(achain) >= 128:
                raise ValueError('Cyclic or oversized sculpt face attribute chain')
            achain.append(current)
            attr = entity(current)
            at = attr['tokens']
            if (attr['name'] not in (INT64_ATTRIBUTE, 'ATTRIB_CUSTOM-attrib') or len(at) < 5
                    or [t['tag'] for t in at[:5]] != [12, 4, 12, 12, 12]
                    or [at[0]['value'], at[1]['value']] != [-1, -1]
                    or pointer(attr, 4, 'face') != owner_id
                    or pointer(attr, 3, nullable=True) != previous):
                raise ValueError('Sculpt face attribute owner/previous chain disagrees')
            previous, current = current, pointer(attr, 2, nullable=True)
        if slot not in achain:
            raise ValueError('Sculpt attribute is absent from claimed face owner chain')
        shell_id = pointer(face, 5, 'shell')
        shell = entity(shell_id, 'shell')
        lump_id = pointer(shell, 7, 'lump')
        lump = entity(lump_id, 'lump')
        body_id = pointer(lump, 5, 'body')
        body = entity(body_id, 'body')
        member_chain(pointer(shell, 5, 'face', True), 3, 'face', owner_id, 5, shell_id)
        member_chain(pointer(lump, 4, 'shell', True), 3, 'shell', shell_id, 7, lump_id)
        member_chain(pointer(body, 3, 'lump', True), 3, 'lump', lump_id, 5, body_id)
        payload = b''
        for token in ts:
            tag, v = token['tag'], token['value']
            if tag == 7:
                raw = v.encode('ascii')
                payload += bytes([tag, len(raw)])+raw
            else:
                payload += bytes([tag])+struct.pack('<q', v)
        start, end = ts[0]['offset'], r['end_offset']-1
        if blob[start:end] != payload:
            raise ValueError('Sculpt typed attribute payload replay disagrees')
        if slot not in mentions:
            raise ValueError('Sculpt attribute has no explicit journal slot mention')
        attributes.append({'attribute_record_index': r['index'], 'geometry_entity_ordinal': slot,
            'section': r['section'], 'attribute_name': ts[9]['value'], 'stored_signed_int64': value(ts[10], 23),
            'value_token_offset': ts[10]['offset'], 'raw_value_hex': struct.pack('<q', ts[10]['value']).hex(),
            'payload_offset': start, 'payload_end_offset': end, 'payload_hex': payload.hex(),
            'face_owner_entity_ordinal': owner_id, 'face_owner_record_index': face['index'],
            'owner_attribute_chain_entity_ordinals': achain,
            'owner_attribute_chain_record_indices': [entity(i)['index'] for i in achain],
            'snapshot_topology': {'shell_entity_ordinal': shell_id, 'shell_record_index': shell['index'],
                'lump_entity_ordinal': lump_id, 'lump_record_index': lump['index'],
                'body_entity_ordinal': body_id, 'body_record_index': body['index'],
                'body_stored_entity_id': value(body['tokens'][1], 4), 'body_section': body['section']},
            'journal_mentions': mentions[slot],
            'identity_scope': 'Face source tag value only; snapshot BODY identity is not replaced by this number',
            'polarity_scope': 'Signed literal preserved; negative workplane values do not establish selected-cell side'})
    return {'attributes': attributes, 'journal_states': states, 'unresolved': [],
            'geometry_entity_count': len(entities), 'inspection_record_count': len(records),
            'journal_neighbor_chain_from_field_3_null': chain,
            'pointer_namespace': 'Initial plus trailing geometry entities, excluding all section markers and history entities',
            'scope': SCOPE}
