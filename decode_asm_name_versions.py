"""Literal same-FACE naming attribute versions in canonical ASM journals.

This reader never rewrites canonical tags or materializes a historical state.
Geometry entity ordinals, inspection indices and native Design IDs are distinct.
"""
import struct

from asm_records import inspect_asm
from decode_asm_history import decode_asm_history
from decode_asm_recipe_tags import decode_asm_generic_tags, encode_generic_tag_payload
from decode_brep import decode_topology
from decode_counted_asm_names import DEFINITION, decode_counted_asm_name

SCOPE = ('Observed slot0 literal initial-head/trailing generic-tag pair with an identical '
         'raw typed FACE-owner ordinal; complete naming tuples and paired BODY stored-ID values are provenance '
         'only. No canonical-tag mutation, materialization, chronology, current/persistent identity '
         'or native FPM/descriptor bridge.')
def decode_asm_name_versions(blob, *, parsed=None):
    """Return decoded/unresolved/scope and full literal journal_history when targeted.

    A caller may query ``trailing_attribute.terms`` as an entire version tuple.
    It must independently qualify its native source against
    ``initial_body_record_index``; the paired trailing BODY is never substituted.
    """
    canonical = inspect_asm(blob)
    if parsed is not None and parsed != canonical:
        raise ValueError('ASM naming-version parsed records differ from source bytes')
    parsed = canonical
    history = decode_asm_history(blob, parsed=parsed)
    result = dict(decoded=[], unresolved=[], journal_history=None, scope=SCOPE)
    records = parsed['records']
    table = history['geometry_entities']
    entities = [records[row['inspection_record_index']] for row in table]

    def integer(token, tag):
        value = token['value']
        if token['tag'] != tag or not isinstance(value, int) or isinstance(value, bool):
            raise ValueError('Naming-version header lacks typed integer/pointer')
        return value

    def generic(record):
        ts = record['tokens']
        return (record['name'] == 'ATTRIB_CUSTOM-attrib' and len(ts) > 5
                and ts[5]['kind'] == 'string' and ts[5]['value'] == DEFINITION)

    candidates = []
    for state in history['journal_states']:
        for entry in state['entries']:
            left, right = entry['pointer_sides']
            x, y = left['stored_geometry_entity_ordinal'], right['stored_geometry_entity_ordinal']
            if min(x, y) < 0:
                continue
            trailing, initial = entities[x], entities[y]
            if (not generic(trailing) or not generic(initial)
                    or trailing['section'] != 'trailing_states' or initial['section'] != 'geometry'):
                continue
            owner = initial['tokens'][4]
            if (owner['tag'] != 12 or not isinstance(owner['value'], int)
                    or not 0 <= owner['value'] < len(entities)
                    or entities[owner['value']]['name'] != 'face'):
                continue
            candidates.append((state, entry, x, y))
    if not candidates:
        return result
    result['journal_history'] = history

    try:
        if len(candidates) != 1:
            raise ValueError('Naming-version FACE pair is not unique across the complete journal')
        state, entry, trailing_ordinal, initial_ordinal = candidates[0]
        if state['delta_state_slot'] != 0:
            raise ValueError('Naming-version pair is outside the observed literal slot0 family')
        # A repeated side cannot establish a unique attribute version, even if
        # the duplicate pair happens to contain exactly the same literal names.
        for side in (0, 1):
            ids = [e['pointer_sides'][side]['stored_geometry_entity_ordinal'] for e in state['entries']]
            ids = [i for i in ids if i != -1]
            if len(set(ids)) != len(ids):
                raise ValueError('Naming-version slot0 repeats a nonnull geometry entity ordinal')
        initial_tags = decode_asm_generic_tags(blob, parsed=parsed, allow_fpm_tracking=True)
        topology = decode_topology(parsed)
        if initial_tags['unresolved'] or topology['unresolved']:
            raise ValueError('Naming-version requires complete initial naming and reciprocal topology')
        nodes = {n['index']: n for n in topology['nodes']}

        def attribute(ordinal, section):
            record = entities[ordinal]
            if record['section'] != section or not generic(record):
                raise ValueError('Naming-version attribute leaves its explicit initial/trailing section')
            ts = record['tokens']
            header = [integer(ts[i], 4 if i == 1 else 12) for i in range(5)]
            if header[1:4] != [-1, -1, -1] or section == 'trailing_states' and header[0] != -1:
                raise ValueError('Naming-version requires a singleton trailing attribute and null chain links')
            owner = header[4]
            if not 0 <= owner < len(entities) or entities[owner]['name'] != 'face' or table[owner]['section'] != 'geometry':
                raise ValueError('Naming-version attribute owner is not one typed initial FACE')
            payload = decode_counted_asm_name(record)
            encoded = b''.join(bytes([ts[i]['tag']])+struct.pack('<q', header[i]) for i in range(5))
            encoded += encode_generic_tag_payload(payload)
            start, end = ts[0]['offset'], record['end_offset']-1
            if (encoded != blob[start:end] or bytes.fromhex(payload['payload_hex'])
                    != blob[payload['payload_offset']:payload['payload_end_offset']]):
                raise ValueError('Naming-version full header/counting payload replay differs')
            nested = None
            if header[0] != -1:
                child_ordinal = header[0]
                if section != 'geometry' or not 0 <= child_ordinal < len(entities):
                    raise ValueError('Naming-version initial metadata child leaves the geometry ordinal table')
                child = entities[child_ordinal]
                proofs = [p for p in initial_tags['ignored_validated_other_definition_attributes']
                    if p['attribute_record_index'] == child['index']
                    and p['owner_record_index'] == record['index']
                    and p.get('parent_topology_owner_record_index') == entities[owner]['index']
                    and p.get('parent_owner_attribute_chain') == [record['index']]]
                if len(proofs) != 1 or child['section'] != 'geometry' or not generic(child):
                    raise ValueError('Naming-version initial nested metadata lacks the existing validated child proof')
                ct = child['tokens']
                child_header = [integer(ct[i], 4 if i == 1 else 12) for i in range(5)]
                if child_header != [-1, -1, -1, -1, ordinal]:
                    raise ValueError('Naming-version nested metadata child header/backlink differs')
                cp = proofs[0]
                terms = cp['terms']
                if (cp['stored_term_count'] != 1 or terms[0]['name'] != '' or terms[0]['stored_index'] != 0
                        or terms[0]['stored_reference_component_count'] != 1
                        or terms[0]['stored_reference_components_int32'][0] <= 0):
                    raise ValueError('Naming-version nested metadata empty-name payload differs')
                child_bytes = b''.join(bytes([ct[i]['tag']])+struct.pack('<q', child_header[i]) for i in range(5))
                child_bytes += encode_generic_tag_payload(cp)
                cs, ce = ct[0]['offset'], child['end_offset']-1
                if child_bytes != blob[cs:ce]:
                    raise ValueError('Naming-version nested metadata full payload replay differs')
                nested = dict(record_index=child['index'], geometry_entity_ordinal=child_ordinal,
                    stored_header_fields=child_header, terms=terms,
                    full_payload_offset=cs, full_payload_end_offset=ce,
                    full_payload_hex=child_bytes.hex(), exact_full_payload_replay=True,
                    existing_initial_catalog_proof=cp)
            return dict(record_index=record['index'], geometry_entity_ordinal=ordinal,
                section=section, owner_geometry_entity_ordinal=owner,
                stored_header_fields=header, terms=payload['terms'], counted_payload=payload,
                full_payload_offset=start, full_payload_end_offset=end,
                full_payload_hex=encoded.hex(), exact_full_payload_replay=True,
                **({'validated_nested_metadata':nested} if nested is not None else {}))

        initial = attribute(initial_ordinal, 'geometry')
        trailing = attribute(trailing_ordinal, 'trailing_states')
        owner = initial['owner_geometry_entity_ordinal']
        if trailing['owner_geometry_entity_ordinal'] != owner:
            raise ValueError('Naming-version pair does not retain the exact same FACE owner ordinal')
        face_record = entities[owner]
        face_index = face_record['index']
        if integer(face_record['tokens'][0], 12) != initial_ordinal:
            raise ValueError('Naming-version initial attribute is not its FACE attribute head')
        tags = [t for t in initial_tags['tags'] if t['attribute_record_index'] == initial['record_index']]
        if (len(tags) != 1 or tags[0]['owner_kind'] != 'face' or tags[0]['owner_record_index'] != face_index
                or tags[0]['owner_attribute_chain'] != [initial['record_index']]
                or tags[0]['terms'] != initial['terms']):
            raise ValueError('Naming-version initial singleton head/owner proof disagrees')
        if len(initial['terms']) != 1 or len(trailing['terms']) != 1:
            raise ValueError('Naming-version requires one complete term on each paired attribute')
        a, b = initial['terms'][0], trailing['terms'][0]
        if 'validated_nested_metadata' in initial:
            if initial['terms'] != trailing['terms']:
                raise ValueError('Naming-version nested-child family requires identical complete paired tuples')
        elif (a['name'] != b['name'] or a['stored_index'] != b['stored_index']
                or a['stored_reference_component_count'] != 2 or b['stored_reference_component_count'] != 1
                or a['stored_reference_components_int32'][:1] != b['stored_reference_components_int32']):
            raise ValueError('Naming-version complete tuples differ from the observed two/one component family')
        graphs = [g for g in topology['body_graphs'] if face_index in g['face_indices']]
        if len(graphs) != 1 or nodes.get(face_index, {}).get('kind') != 'face':
            raise ValueError('Naming-version FACE lacks one reciprocal initial BODY graph')
        body_index = graphs[0]['body_index']
        body = nodes[body_index]
        body_ordinal = next(e['geometry_entity_ordinal'] for e in table if e['inspection_record_index'] == body_index)
        pairs = [e for e in state['entries'] if e['pointer_sides'][1]['stored_geometry_entity_ordinal'] == body_ordinal]
        if len(pairs) != 1:
            raise ValueError('Naming-version initial BODY lacks one literal slot0 pair')
        body_pair = pairs[0]
        other_ordinal = body_pair['pointer_sides'][0]['stored_geometry_entity_ordinal']
        if (other_ordinal < 0 or table[other_ordinal]['section'] != 'trailing_states'
                or entities[other_ordinal]['name'] != 'body'):
            raise ValueError('Naming-version paired BODY target is not a typed trailing BODY')
        other = entities[other_ordinal]
        other_id = integer(other['tokens'][1], 4)
        if integer(entities[body_ordinal]['tokens'][1], 4) != body['stored_entity_id']:
            raise ValueError('Naming-version initial BODY stored-ID copies differ')
        paired_body = dict(initial_record_index=body_index, initial_geometry_entity_ordinal=body_ordinal,
            initial_stored_entity_id=body['stored_entity_id'], trailing_record_index=other['index'],
            trailing_geometry_entity_ordinal=other_ordinal, trailing_stored_entity_id=other_id,
            stored_ids_equal=body['stored_entity_id'] == other_id,
            journal_pair=dict(delta_state_slot=0, **body_pair), identity_upgrade=False,
            scope='Literal same-journal typed BODY pair only; equal or unequal stored IDs do not establish a native BODY identity bridge')
        result['decoded'].append(dict(initial_attribute=initial, trailing_attribute=trailing,
            owner_face_record_index=face_index, owner_face_geometry_entity_ordinal=owner,
            initial_body_record_index=body_index, initial_body_stored_entity_id=body['stored_entity_id'],
            initial_face_body_graph_membership=[body_index],
            journal_pair=dict(delta_state_slot=0, **entry), paired_body_version=paired_body,
            canonical_tag_catalog_unchanged=True, materialized_state=None,
            chronological_state=None, persistent_face_identity=None, native_FPM_descriptor_bridge=None,
            scope=SCOPE))
    except (ValueError, KeyError, IndexError, TypeError, UnicodeError, struct.error, StopIteration) as error:
        result['unresolved'].append(dict(reason=str(error)))
    return result
