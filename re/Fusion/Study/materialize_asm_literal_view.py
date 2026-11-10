"""A nonserialized, pointer-closed view of explicit ASM journal pair literals.

This factory qualifies namespaces and references only. It does not identify a
native BODY, validate a shape, or assign chronological/current-state meaning.
"""
import copy
import struct

from asm_records import inspect_asm
from decode_asm_history import decode_asm_history

SCOPE = ('Nonserialized literal ASM journal-pair view with canonical entity ordinals, '
         'unique kind-preserving aliases, original record origins and complete pointer closure; '
         'no topology, native identity, chronology or current-state qualification')


def materialize_asm_literal_view(blob, *, state_slot=0, pointer_side=0,
                                 parsed=None, history=None):
    """Select a bounded initial/trailing pair table and return dense view rows.

    The observed construction retains initial entities not on side1, adds side0
    trailing entities, and follows explicit nonnull side1-to-side0 pairs. Raw
    offsets and original bytes are not rewritten or represented as saved ASM.
    """
    if type(state_slot) is not int or state_slot < 0 or type(pointer_side) is not int or pointer_side != 0:
        raise ValueError('Literal ASM view requires a nonnegative state slot and observed pointer side0')
    canonical = inspect_asm(blob)
    if parsed is not None and parsed != canonical:
        raise ValueError('Literal ASM view supplied parsed records differ from original bytes')
    parsed = canonical
    canonical_history = decode_asm_history(blob, parsed=parsed)
    if history is not None and history != canonical_history:
        raise ValueError('Literal ASM view supplied history differs from the canonical pointer namespace')
    history = canonical_history
    states = history['journal_states']
    if state_slot >= len(states):
        raise ValueError('Literal ASM view state slot leaves the canonical journal table')
    table = history['geometry_entities']
    entities = [parsed['records'][row['inspection_record_index']] for row in table]
    aliases, alias_evidence = {}, []
    selected = [[], []]
    for entry in states[state_slot]['entries']:
        left, right = entry['pointer_sides']
        x, y = left['stored_geometry_entity_ordinal'], right['stored_geometry_entity_ordinal']
        if x == y == -1:
            raise ValueError('Literal ASM view cannot qualify an empty pointer pair')
        for side, pointer in enumerate((left, right)):
            ordinal = pointer['stored_geometry_entity_ordinal']
            if ordinal == -1:
                continue
            if pointer['target_section'] != ('trailing_states' if side == 0 else 'geometry'):
                raise ValueError('Literal ASM pair leaves the explicit initial/trailing sections')
            selected[side].append(ordinal)
        if x != -1 and y != -1:
            if left['target_kind'] != right['target_kind']:
                raise ValueError('Literal ASM journal alias changes the typed entity kind')
            if y in aliases or x in aliases.values():
                raise ValueError('Literal ASM journal aliases are not unique and bijective')
            aliases[y] = x
            alias_evidence.append(dict(entry_ordinal=entry['entry_ordinal'],
                side1_entity_ordinal=y, side0_entity_ordinal=x,
                side1_inspection_record_index=right['inspection_record_index'],
                side0_inspection_record_index=left['inspection_record_index'],
                kind=left['target_kind'], pointer_sides=entry['pointer_sides'],
                scope='Literal pair-local pointer alias in this view only; no persistent or native historical identity'))
    if any(len(ids) != len(set(ids)) for ids in selected):
        raise ValueError('Literal ASM view repeats a nonnull journal side ordinal')
    left, right = map(set, selected)
    initial = {row['geometry_entity_ordinal'] for row in table if row['section'] == 'geometry'}
    if not left or not right or left & right or not right <= initial:
        raise ValueError('Literal ASM view does not separate bounded initial and trailing tables')
    chosen = sorted((initial-right) | left)
    dense = {ordinal: index for index, ordinal in enumerate(chosen)}
    origins, viewed_records, rewrites = [], [], []
    naive_dangling = 0
    for ordinal in chosen:
        original = entities[ordinal]
        viewed = copy.deepcopy(original)
        viewed['index'] = dense[ordinal]
        viewed['section'] = 'geometry'
        origins.append(dict(view_record_index=dense[ordinal], geometry_entity_ordinal=ordinal,
            inspection_record_index=original['index'], section=original['section'], kind=original['name'],
            original_record_offset=original['offset'], original_record_end_offset=original['end_offset']))
        for field, token in enumerate(viewed['tokens']):
            if token['tag'] != 12:
                continue
            raw = token['value']
            offset = token['offset']
            if (type(raw) is not int or blob[offset:offset+1] != b'\x0c'
                    or struct.unpack_from('<q', blob, offset+1)[0] != raw):
                raise ValueError('Literal ASM view pointer token disagrees with original bytes')
            if raw == -1:
                continue
            if not 0 <= raw < len(table):
                raise ValueError('Literal ASM view pointer leaves the geometry-entity namespace')
            if raw not in dense:
                naive_dangling += 1
            target = aliases.get(raw, raw)
            if target not in dense:
                raise ValueError('Literal ASM aliases leave a dangling geometry pointer')
            token['value'] = dense[target]
            rewrites.append(dict(view_record_index=dense[ordinal], source_geometry_entity_ordinal=ordinal,
                source_inspection_record_index=original['index'], token_field=field, token_offset=offset,
                stored_target_geometry_entity_ordinal=raw, aliased_target_geometry_entity_ordinal=target,
                target_source_inspection_record_index=entities[target]['index'],
                target_view_record_index=dense[target], used_literal_pair_alias=raw in aliases))
        viewed_records.append(viewed)
    view = dict(records=viewed_records, complete_token_stream=True, is_materialized_view=True,
        scope='Nonserialized literal ASM alias view; original byte offsets retained but pointers and row indices are dense view identifiers')
    return dict(state_slot=state_slot, pointer_side=pointer_side,
        baseline='Explicit initial geometry section', canonical_history=history,
        selected_geometry_entity_ordinals=chosen, origin_map=origins,
        literal_pair_aliases=alias_evidence, rewritten_pointer_evidence=rewrites,
        naive_membership_dangling_pointer_count=naive_dangling,
        qualified_dangling_pointer_count=0, view_parsed=view, scope=SCOPE)
