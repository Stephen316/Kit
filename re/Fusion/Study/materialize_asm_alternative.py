"""Qualified slot-zero alternate box topology from observed ASM journals.

This opt-in view applies one literal journal pair table to initial geometry.
It is not chronological replay, an active/final-body classifier or a serialized
ASM file. Original entity ordinals/record indices remain in an explicit map.
"""

import copy

from asm_records import inspect_asm
from decode_asm_history import decode_asm_history
from decode_brep import decode_topology

SCOPE = ('Observed three-state slot0 side0 alternate cache view, qualified by typed pair aliases, pointer closure and reciprocal single-box topology; '
         'not chronological replay, current/final state, native face identity or API evaluator equivalence')
BOX_COUNTS = {'lump': 1, 'shell': 1, 'face': 6, 'loop': 6, 'coedge': 24, 'edge': 12, 'vertex': 8}


def materialize_asm_alternative(blob, *, state_slot=0, pointer_side=0, parsed=None, history=None):
    """Return topology/view_parsed plus literal aliases and per-record origins.

    Only the captured three-state [0,2,1] schema and side1→side0 alternative
    relative to initial geometry are admitted. ``view_parsed`` is a nonserialized
    in-memory topology input: offsets still name original bytes, pointer tokens
    explicitly name dense view indices. No source objects are modified.
    """
    if state_slot != 0 or pointer_side != 0:
        raise ValueError('Only observed slot0 side0 alternative is supported')
    parsed = inspect_asm(blob) if parsed is None else parsed
    canonical = decode_asm_history(blob, parsed=parsed)
    if history is not None and history != canonical:
        raise ValueError('Supplied ASM history namespace differs from source bytes/records')
    history = canonical
    states = history['journal_states']
    if (len(states) != 3 or history['neighbor_chain'] != [0, 2, 1] or states[1]['entries']
            or any(e['pointer_sides'][0]['stored_geometry_entity_ordinal'] != -1 for e in states[2]['entries'])):
        raise ValueError('Unobserved ASM alternate-view journal schema')
    table = history['geometry_entities']
    originals = parsed['records']
    source_entities = [originals[e['inspection_record_index']] for e in table]
    initial = {e['geometry_entity_ordinal'] for e in table if e['section'] == 'geometry'}
    selected_sides = [[], []]
    aliases, alias_evidence = {}, []
    for e in states[0]['entries']:
        sides = e['pointer_sides']
        if all(s['stored_geometry_entity_ordinal'] == -1 for s in sides):
            raise ValueError('Empty pointer pair cannot qualify an alternate view')
        for side in (0, 1):
            slot = sides[side]['stored_geometry_entity_ordinal']
            if slot != -1:
                if sides[side]['target_section'] != ('trailing_states' if side == 0 else 'geometry'):
                    raise ValueError('Alternate pair sides cross unobserved initial/trailing sections')
                selected_sides[side].append(slot)
        if all(s['stored_geometry_entity_ordinal'] != -1 for s in sides):
            left, right = [s['stored_geometry_entity_ordinal'] for s in sides]
            if sides[0]['target_kind'] != sides[1]['target_kind']:
                raise ValueError('Alternate journal alias changes entity kind')
            if right in aliases or left in aliases.values():
                raise ValueError('Ambiguous or nonbijective alternate journal alias')
            aliases[right] = left
            alias_evidence.append({'entry_ordinal': e['entry_ordinal'],
                'side1_entity_ordinal': right, 'side0_entity_ordinal': left,
                'side1_inspection_record_index': sides[1]['inspection_record_index'],
                'side0_inspection_record_index': sides[0]['inspection_record_index'],
                'kind': sides[0]['target_kind'],
                'scope': 'Literal pair-local alias for this qualified alternate view, not persistent identity'})
    if any(len(set(slots)) != len(slots) for slots in selected_sides):
        raise ValueError('Duplicate nonnull pointer side makes alternate membership ambiguous')
    left, right = [set(slots) for slots in selected_sides]
    if not left or not right or left & right or not right <= initial:
        raise ValueError('Alternate pointer sides do not separate supported baseline/replacement tables')
    chosen = sorted((initial-right) | left)
    dense = {slot: i for i, slot in enumerate(chosen)}
    view_records, origins, rewrites = [], [], []
    naive_dangling = 0
    for slot in chosen:
        original = source_entities[slot]
        viewed = copy.deepcopy(original)
        viewed['index'] = dense[slot]
        viewed['section'] = 'geometry'
        origins.append({'view_record_index': dense[slot], 'geometry_entity_ordinal': slot,
            'inspection_record_index': original['index'], 'section': original['section'], 'kind': original['name']})
        for field, token in enumerate(viewed['tokens']):
            if token['tag'] != 12:
                continue
            raw = token['value']
            if raw == -1:
                continue
            if raw not in dense:
                naive_dangling += 1
            resolved = aliases.get(raw, raw)
            if resolved not in dense:
                raise ValueError('Alternate journal aliases leave a dangling geometry pointer')
            token['value'] = dense[resolved]
            rewrites.append({'view_record_index': dense[slot], 'source_geometry_entity_ordinal': slot,
                'source_inspection_record_index': original['index'], 'token_field': field,
                'token_offset': token['offset'], 'stored_target_geometry_entity_ordinal': raw,
                'aliased_target_geometry_entity_ordinal': resolved,
                'target_source_inspection_record_index': source_entities[resolved]['index'],
                'target_view_record_index': dense[resolved], 'used_literal_pair_alias': raw in aliases})
        view_records.append(viewed)
    view = {'records': view_records, 'complete_token_stream': True,
        'is_materialized_view': True,
        'scope': 'In-memory qualified alternate topology input; source offsets retained, pointers rewritten to view indices; not original serialized ASM tokens'}
    topology = decode_topology(view)
    graphs = topology['body_graphs']
    if (topology['unresolved'] or len(graphs) != 1 or graphs[0]['counts'] != BOX_COUNTS
            or not graphs[0]['all_coedges_have_partners'] or len(graphs[0]['raw_vertex_positions']) != 8
            or graphs[0]['surface_record_types'] != {'plane-surface': 6}):
        raise ValueError('Alternate view lacks the observed closed reciprocal single-box topology')
    return {'state_slot': 0, 'pointer_side': 0, 'baseline': 'Explicit initial geometry section',
        'selected_geometry_entity_ordinals': chosen, 'origin_map': origins,
        'literal_pair_aliases': alias_evidence, 'rewritten_pointer_evidence': rewrites,
        'naive_membership_dangling_pointer_count': naive_dangling,
        'qualified_dangling_pointer_count': 0, 'topology': topology, 'view_parsed': view,
        'qualification': 'Typed sides, unique kind-preserving aliases, complete pointer closure, zero unresolved topology and reciprocal closed box incidence',
        'scope': SCOPE}
