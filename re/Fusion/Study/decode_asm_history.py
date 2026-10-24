"""Bounded ASM geometry-entity and delta-journal pointer namespaces.

Initial and trailing geometry share an entity-ordinal table. History records and
section markers are excluded. Delta states have a separate slot table. Neither
table is a native Design object ID or the inspection-record index. Journal pair
sides and chain direction retain raw meanings; no history replay is performed.
"""

import struct

from asm_records import inspect_asm

SCOPE = ('Observed ASM geometry entity ordinals, delta-state slots and reciprocal journal links with literal pointer-pair entries; '
         'inspection indices retained separately; chronology, transition-side semantics and materialized state topology unresolved')


def decode_asm_history(blob, *, parsed=None):
    """Return geometry_entities/journal_states/neighbor_chain/unresolved/scope.

    Each journal entry retains both sides, including stored ordinal -1 with a
    null target. This function does not mutate records or compose an active
    pointer table. Unsupported layouts raise ValueError.
    """
    parsed = inspect_asm(blob) if parsed is None else parsed
    if not parsed['complete_token_stream'] or parsed['total_bytes'] != len(blob):
        raise ValueError('ASM history namespaces require a complete matching token stream')
    records = parsed['records']
    if any(r['index'] != i for i, r in enumerate(records)):
        raise ValueError('ASM inspection record indices are not contiguous')
    markers = [r for r in records if r['record_kind'] == 'marker']
    marker_names = [r['name'] for r in markers]
    has_history = marker_names == ['Begin-of-ASM-History-Data', 'End-of-ASM-History-Section', 'End-of-ASM-data']
    if not has_history and marker_names != ['End-of-ASM-data']:
        raise ValueError('Unsupported ASM history section-marker sequence')
    if markers[-1]['index'] != len(records)-1:
        raise ValueError('ASM final marker does not terminate the record table')
    entities = []
    for r in records:
        if r['record_kind'] != 'entity':
            continue
        expected = ('geometry' if not has_history or r['index'] < markers[0]['index'] else
                    'history' if r['index'] < markers[1]['index'] else 'trailing_states')
        if r['section'] != expected:
            raise ValueError('ASM entity section disagrees with explicit marker bounds')
        if expected != 'history':
            entities.append(r)
    table = [{'geometry_entity_ordinal': i, 'inspection_record_index': r['index'],
              'section': r['section'], 'kind': r['name'], 'record_offset': r['offset'],
              'record_end_offset': r['end_offset']} for i, r in enumerate(entities)]

    def integer(token, tag):
        value = token['value']
        if token['tag'] != tag or not isinstance(value, int) or isinstance(value, bool):
            raise ValueError('ASM journal integer/pointer token type mismatch')
        return value

    def target(token, side):
        slot = integer(token, 12)
        if slot != -1 and not 0 <= slot < len(table):
            raise ValueError('ASM journal pointer leaves geometry-entity ordinal table')
        row = table[slot] if slot != -1 else None
        return {'pointer_side': side, 'stored_geometry_entity_ordinal': slot,
                'inspection_record_index': row['inspection_record_index'] if row else None,
                'target_kind': row['kind'] if row else None,
                'target_section': row['section'] if row else None, 'token_offset': token['offset']}

    result = {'geometry_entities': table, 'journal_states': [], 'neighbor_chain': [],
              'unresolved': [], 'geometry_entity_count': len(table), 'inspection_record_count': len(records),
              'geometry_namespace': 'Initial plus trailing entity records, excluding all history records and all section markers',
              'journal_namespace': 'Delta-state slot is its zero-based position among delta_state records, excluding history_stream',
              'state_topology_status': 'No state is materialized or labeled current/final', 'scope': SCOPE}
    if not has_history:
        return result
    history = [r for r in records if r['section'] == 'history' and r['record_kind'] == 'entity']
    if not history or history[0]['name'] != 'history_stream' or any(r['name'] != 'delta_state' for r in history[1:]):
        raise ValueError('Unsupported ASM history entity sequence')
    header = history[0]['tokens']
    if ([t['tag'] for t in header] != [4, 4, 4, 4, 12, 12, 12, 12]
            or [t['value'] for t in header[4:]] != [-1, 0, 1, -1]):
        raise ValueError('Unsupported ASM history-stream header/reference fields')
    result['history_stream'] = {'inspection_record_index': history[0]['index'],
        'raw_header_integers': [integer(t, 4) for t in header[:4]],
        'raw_pointer_fields': [integer(t, 12) for t in header[4:]],
        'scope': 'Observed header retained; integer meanings and history-stream pointer roles unresolved'}
    states = result['journal_states']
    for slot, r in enumerate(history[1:]):
        ts = r['tokens']
        if (len(ts) < 11 or [t['tag'] for t in ts[:9]] != [4, 4, 4, 12, 12, 12, 12, 12, 11]
                or [ts[i]['value'] for i in (1, 2, 5, 6, 7, 8)] != [1, 0, slot, -1, 0, False]):
            raise ValueError('Unsupported ASM delta-state header/self-slot fields')
        neighbors = [integer(ts[i], 12) for i in (3, 4)]
        if any(v != -1 and not 0 <= v < len(history)-1 for v in neighbors):
            raise ValueError('ASM journal neighbor leaves delta-state slot table')
        if len(ts) == 11:
            if [(t['tag'], t['value']) for t in ts[9:]] != [(4, 0), (4, 0)]:
                raise ValueError('Unsupported empty ASM delta-state trailer')
            triples = []
        else:
            if ([(t['tag'], t['value']) for t in ts[9:12]] != [(4, 1), (12, slot), (4, 2)]
                    or [(t['tag'], t['value']) for t in ts[-3:]] != [(4, 0)]*3 or (len(ts)-15) % 3):
                raise ValueError('Unsupported ASM journal entry-block framing')
            triples = ts[12:-3]
        entries = []
        for i in range(0, len(triples), 3):
            flag, left, right = triples[i:i+3]
            if integer(flag, 4) != 1:
                raise ValueError('Unsupported ASM journal pointer-pair entry flag')
            entries.append({'entry_ordinal': i//3, 'stored_entry_flag': 1,
                            'pointer_sides': [target(left, 0), target(right, 1)]})
        payload = b''.join(bytes([t['tag']])+(b'' if t['tag'] == 11 else struct.pack('<q', integer(t, t['tag']))) for t in ts)
        begin, end = ts[0]['offset'], r['end_offset']-1
        if blob[begin:end] != payload:
            raise ValueError('ASM journal exact payload replay disagrees')
        states.append({'delta_state_slot': slot, 'inspection_record_index': r['index'],
            'record_offset': r['offset'], 'stored_header_integer': integer(ts[0], 4),
            'raw_header_values': [t['value'] for t in ts[:9]], 'neighbor_slots_fields_3_4': neighbors,
            'entries': entries, 'entry_count': len(entries), 'payload_offset': begin, 'payload_end_offset': end,
            'scope': 'Typed pair sides and reciprocal neighbor links only; transition direction and entity replacement semantics unresolved'})
    for state in states:
        for side, neighbor in enumerate(state['neighbor_slots_fields_3_4']):
            if neighbor != -1 and states[neighbor]['neighbor_slots_fields_3_4'][1-side] != state['delta_state_slot']:
                raise ValueError('ASM journal neighbor links are not reciprocal')
    starts = [s['delta_state_slot'] for s in states if s['neighbor_slots_fields_3_4'][0] == -1]
    if len(starts) != 1:
        raise ValueError('ASM journal must have one field-three-null chain boundary')
    current = starts[0]
    while current != -1:
        if current in result['neighbor_chain']:
            raise ValueError('ASM journal neighbor chain contains a cycle')
        result['neighbor_chain'].append(current)
        current = states[current]['neighbor_slots_fields_3_4'][1]
    if len(result['neighbor_chain']) != len(states):
        raise ValueError('ASM journal neighbor chain does not cover all delta-state slots')
    return result
