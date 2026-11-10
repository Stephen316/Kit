"""Observed same-definition CopyPaste occurrence provenance and stored caches.

Source UUID routes and reciprocal created-occurrence datum establish identity.
Stored matrices are historical evidence, not solved/current assembly placement.
"""
import struct
import uuid

from decode_assembly import OCCURRENCE_GUID, OCCURRENCE_COLLECTION_GUID, collection, occurrence, multiply
from decode_component_creation import decode_component_creation, OCCURRENCE_DATUM, BOOKKEEPING
from decode_component_body_proxies import FRAME, FRAME_LINK, ROUTE_LIST, ROUTE
from decode_parameters import read_string
from decode_placement import IDENTITY, rigid_matrix
from decode_sketch import numbers, reference, same

COPY_PASTE = 'D57B1A22-9D5A-4D7D-A909-E08C579612CA'
SCOPE = 'Captured same-component-definition CopyPaste: explicit source occurrence UUID route, created occurrence datum, reciprocal owners and historical matrix caches; component duplication, external links, replay and solved world state unresolved'


def decode_copy_paste_occurrences(data, records, features, assembly, component_creation=None):
    """Return decoded/unresolved/scope; may reuse prior component creation summary."""
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {i: items[0] for i, items in grouped.items() if len(items) == 1}
    creations = (component_creation if component_creation is not None else
                 decode_component_creation(data, records, features, assembly))['decoded']
    components = {c['object_id']: c for c in assembly['components']}
    occurrences = assembly['native_occurrences']

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('CopyPaste typed reference missing, ambiguous or wrong class')
        return record, data[record.body:record.end]

    def text_uuid(payload, position):
        text, position = read_string(payload, position)
        if len(text) != 36:
            raise ValueError('Unobserved CopyPaste route UUID length')
        uuid.UUID(text)
        return text, position

    def frame(identity, owner, explicit_matrix):
        _, payload = typed(identity, FRAME)
        if (payload[:20] != bytes(20) or payload[20:37] != struct.pack('<I', 3)+bytes(13)
                or len(payload) != (206 if explicit_matrix else 78)):
            raise ValueError('Unobserved CopyPaste context frame framing')
        link_id = reference(payload, 37)
        if explicit_matrix:
            if payload[48] != 0 or payload[177] != 0:
                raise ValueError('Unobserved CopyPaste explicit source-frame cache flag')
            matrix, owner_offset = rigid_matrix(numbers(payload, 49, 16)), 178
        else:
            if payload[48:50] != b'\1\0':
                raise ValueError('Unobserved CopyPaste second-frame identity shortcut')
            matrix, owner_offset = list(IDENTITY), 50
        if reference(payload, owner_offset) != owner or payload[owner_offset+22:] != bytes(6):
            raise ValueError('CopyPaste context frame reciprocal owner disagrees')
        wrapper_id = reference(payload, owner_offset+11)
        _, wrapper = typed(wrapper_id, ROUTE_LIST)
        if len(wrapper) != 18 or wrapper[:7] != bytes.fromhex('00000001000000'):
            raise ValueError('Unobserved CopyPaste one-route wrapper')
        route_id = reference(wrapper, 7)
        _, route = typed(route_id, ROUTE)
        expected_mode = 1 if explicit_matrix else 0
        if len(route) != (406 if explicit_matrix else 258) or route[:6] != b'\0\0'+struct.pack('<I', expected_mode):
            raise ValueError('Unobserved CopyPaste route mode/count')
        occurrence_uuid, position = text_uuid(route, 6)
        context_namespace = context_entity = None
        if explicit_matrix:
            context_namespace, position = text_uuid(route, position)
            context_entity, position = text_uuid(route, position)
            if route[position:position+8] != struct.pack('<Q', 2):
                raise ValueError('Unobserved CopyPaste populated route association field')
            position += 8
        else:
            if occurrence_uuid != str(uuid.UUID(int=0)) or route[position:position+12] != struct.pack('<IQ', 0, 1):
                raise ValueError('Unobserved CopyPaste empty occurrence route')
            position += 12
        terminal_namespace, position = text_uuid(route, position)
        terminal_entity, position = text_uuid(route, position)
        if (route[position:] != struct.pack('<QI', 2, 0)
                or (explicit_matrix and context_namespace != terminal_namespace)):
            raise ValueError('CopyPaste route namespace/footer disagrees')
        return {'object_id': identity, 'frame_link_object_id': link_id,
                'route_wrapper_object_id': wrapper_id, 'route_object_id': route_id,
                'stored_route_mode': expected_mode, 'stored_occurrence_uuid_text': occurrence_uuid,
                'context_namespace_text': context_namespace, 'context_entity_guid_text': context_entity,
                'terminal_namespace_text': terminal_namespace, 'terminal_entity_guid_text': terminal_entity,
                'stored_context_matrix': matrix}

    def native_occurrence(identity):
        record, _ = typed(identity, OCCURRENCE_GUID)
        matches = [o for o in occurrences if o['object_id'] == identity]
        if len(matches) != 1 or record.payload_start is None:
            raise ValueError('CopyPaste occurrence missing/ambiguous in assembly summary')
        actual = occurrence(data[record.payload_start:record.end], identity)
        if any(actual[k] != matches[0][k] for k in ('component_object_id', 'instance_guid_text', 'parent_collection_object_id')):
            raise ValueError('CopyPaste independently framed occurrence disagrees with assembly summary')
        return actual

    decoded, unresolved = [], []
    for record in records:
        if not record.is_primary or record.class_guid != COPY_PASTE:
            continue
        try:
            owner = record.object_id
            if primary.get(owner) is not record:
                raise ValueError('CopyPaste feature identity ambiguous')
            payload = data[record.body:record.end]
            if (len(payload) != 507 or payload[:3] != bytes(3) or payload[14] != 0
                    or payload[154:158] != bytes(4) or payload[169:171] != b'\1\0'):
                raise ValueError('Unobserved CopyPaste feature/cache framing')
            first_matrix = rigid_matrix(numbers(payload, 15, 16))
            source_frame = frame(reference(payload, 3), owner, True)
            second_frame = frame(reference(payload, 143), owner, False)
            if (source_frame['terminal_namespace_text'], source_frame['terminal_entity_guid_text']) != (second_frame['terminal_namespace_text'], second_frame['terminal_entity_guid_text']):
                raise ValueError('CopyPaste source/second route terminal mismatch')
            _, source_link = typed(source_frame['frame_link_object_id'], FRAME_LINK)
            if (len(source_link) != 199 or source_link[:38] != bytes.fromhex('0000000000000000000000000000030100000001000000010200000000000000000101000000')
                    or source_link[49:59] != bytes.fromhex('00000000010000000100') or source_link[70] != 0):
                raise ValueError('Unobserved CopyPaste source context-link/cache framing')
            owner_component_id, source_snapshot_id = reference(source_link, 38), reference(source_link, 59)
            if not same(rigid_matrix(numbers(source_link, 71, 16)), source_frame['stored_context_matrix']):
                raise ValueError('CopyPaste repeated source-frame/context-link matrices disagree')
            _, second_link = typed(second_frame['frame_link_object_id'], FRAME_LINK)
            if (len(second_link) != 53 or second_link[:34] != bytes.fromhex('00000000000000000000000000000300000000010200000000000000000101000000')
                    or reference(second_link, 34) != owner_component_id or second_link[45:] != bytes.fromhex('ffffffff00000000')
                    or owner_component_id not in components):
                raise ValueError('CopyPaste second context-link owner component disagrees')
            source_matches = [o for o in occurrences if o['instance_guid_text'] == source_frame['stored_occurrence_uuid_text']]
            if len(source_matches) != 1:
                raise ValueError('CopyPaste source route instance UUID missing or ambiguous')
            source = native_occurrence(source_matches[0]['object_id'])
            source_creations = [c for c in creations if c['snapshot_object_id'] == source_snapshot_id
                                and c['native_occurrence_object_id'] == source['object_id']]
            if len(source_creations) != 1 or not same(source_creations[0]['snapshot_transform'], source_frame['stored_context_matrix']):
                raise ValueError('CopyPaste source route/frame does not agree with explicit creation snapshot')
            datum_id = reference(payload, 158)
            _, datum = typed(datum_id, OCCURRENCE_DATUM)
            if (len(datum) != 39 or datum[:2] != bytes(2) or datum[13:16] != b'\1\0\0'
                    or datum[27] != 0 or reference(datum, 28) != owner):
                raise ValueError('CopyPaste created occurrence datum owner disagrees')
            bookkeeping_id = reference(datum, 16)
            _, bookkeeping = typed(bookkeeping_id, BOOKKEEPING)
            if len(bookkeeping) != 39 or reference(bookkeeping, 12) != datum_id:
                raise ValueError('CopyPaste occurrence datum bookkeeping backlink disagrees')
            created = native_occurrence(reference(datum, 2))
            if (created['object_id'] == source['object_id'] or created['component_object_id'] != source['component_object_id']
                    or created['component_object_id'] not in components
                    or created['parent_collection_object_id'] != source['parent_collection_object_id']):
                raise ValueError('Only captured distinct occurrences of same definition in same parent supported')
            collection_record, collection_body = typed(created['parent_collection_object_id'], OCCURRENCE_COLLECTION_GUID)
            parent = collection(collection_body, collection_record.object_id)
            if (parent['component_object_id'] != owner_component_id
                    or any(i not in parent['occurrence_object_ids'] for i in (created['object_id'], source['object_id']))):
                raise ValueError('CopyPaste occurrences are not reciprocal members of context owner collection')
            result_matrix = rigid_matrix(numbers(payload, 171, 16))
            namespace, cursor = text_uuid(payload, 299)
            if (namespace != str(uuid.UUID(int=0)) or cursor != 375
                    or payload[375:382] != bytes.fromhex('00000001000000')
                    or reference(payload, 382) != datum_id or payload[393:397] != b'\xff'*4):
                raise ValueError('CopyPaste repeated result datum/metadata framing disagrees')
            label, cursor = read_string(payload, 397)
            if label != 'CopyPaste':
                raise ValueError('CopyPaste native feature label disagrees')
            index = struct.unpack_from('<Q', payload, cursor)[0]
            name, cursor = read_string(payload, cursor+8)
            def occurrence_fields(item):
                return {'native_occurrence_object_id': item['object_id'], 'component_object_id': item['component_object_id'],
                        'component_name': components[item['component_object_id']]['name'],
                        'instance_number': item['instance_number'], 'instance_guid_text': item['instance_guid_text'],
                        'parent_collection_object_id': item['parent_collection_object_id'],
                        'occurrence_paths': [p['path'] for p in assembly.get('occurrence_paths', []) if p['native_occurrence_object_id'] == item['object_id']]}
            decoded.append({'feature_object_id': owner, 'kind': 'CopyPaste', 'stored_index': index, 'name': name or None,
                            'source_occurrence': occurrence_fields(source), 'created_occurrence': occurrence_fields(created),
                            'source_creation_feature_object_id': source_creations[0]['feature_object_id'],
                            'source_creation_snapshot_object_id': source_snapshot_id,
                            'owner_component_object_id': owner_component_id,
                            'owner_component_name': components[owner_component_id]['name'],
                            'created_occurrence_datum_object_id': datum_id,
                            'datum_bookkeeping_object_id': bookkeeping_id,
                            'source_context_frame': source_frame, 'second_context_frame': second_frame,
                            'stored_first_feature_matrix': first_matrix, 'stored_created_occurrence_matrix': result_matrix,
                            'source_times_first_equals_created_cache': same(multiply(source_frame['stored_context_matrix'], first_matrix), result_matrix),
                            'first_times_source_equals_created_cache': same(multiply(first_matrix, source_frame['stored_context_matrix']), result_matrix),
                            'source_cache_matches_current_native_occurrence_cache': same(source_frame['stored_context_matrix'], source['local_transform']),
                            'created_cache_matches_current_native_occurrence_cache': same(result_matrix, created['local_transform']),
                            'matrix_scope': 'Stored historical matrices, cm, row-major. Arithmetic cache relationship reported without asserting general transform roles or current solved world placement.',
                            'uninterpreted_metadata_suffix_hex': payload[cursor:].hex(), 'scope': SCOPE})
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
            unresolved.append({'feature_object_id': record.object_id, 'class_guid': COPY_PASTE, 'reason': str(error)})
    return {'decoded': decoded, 'unresolved': unresolved, 'scope': SCOPE}
