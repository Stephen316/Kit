"""Explicit CreateComponent -> component scope -> occurrence snapshot links.

Snapshot transforms are historical placement evidence. They are not a solved
assembly state, and the rest of the internal snapshot feature stays unsupported.
"""

import struct

from decode_assembly import OCCURRENCE_GUID
from decode_dependencies import SCOPE_GUID, scope_datum
from decode_parameters import read_string
from decode_placement import IDENTITY, rigid_matrix
from decode_sketch import numbers, reference, same


CREATE_COMPONENT = '78B9DEFC-DA1C-4ED0-A395-40890BDAE590'
SNAPSHOT = '54F9ACE8-B5B8-4A6E-B582-64F629511DE4'
OCCURRENCE_DATUM = '2D6E13A1-BBEF-4FB3-9277-00D99F634136'
BOOKKEEPING = '6CCF41D5-40BE-48ED-A834-18F3EAED6C57'
NIL_UUID = '00000000-0000-0000-0000-000000000000'


def decode_component_creation(data, records, features, assembly):
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: items[0] for identity, items in grouped.items() if len(items) == 1}
    components = {c['object_id']: c for c in assembly['components']}
    occurrences = {o['object_id']: o for o in assembly['native_occurrences']}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError('Component creation typed reference missing, ambiguous or wrong class')
        return data[record.body:record.end]

    decoded, unresolved = [], []
    for feature in features:
        if feature['class_guid'] != CREATE_COMPONENT:
            continue
        identity = feature['object_id']
        try:
            body = typed(identity, CREATE_COMPONENT)
            namespace, end = read_string(body, 13)
            label, label_end = read_string(body, 100)
            if (len(body) != 222 or body[:2] != bytes(2) or namespace != NIL_UUID or end != 89
                    or body[89:100] != bytes(7)+b'\xff'*4 or label != 'CreateComponent'
                    or label_end != 134 or struct.unpack_from('<Q', body, 134)[0] != feature['stored_index']
                    or body[-1:] != b'\0'):
                raise ValueError('Unobserved CreateComponent header/identity layout')
            scope_id, snapshot_id = reference(body, 2), reference(body, 210)
            scope = scope_datum(typed(scope_id, SCOPE_GUID), scope_id, components)
            if scope['optional_related_object_id'] != snapshot_id:
                raise ValueError('Component creation scope/snapshot correspondence disagrees')
            snapshot = typed(snapshot_id, SNAPSHOT)
            if snapshot[:6] != bytes(6) or snapshot[17] != 1:
                raise ValueError('Unobserved component snapshot prefix')
            datum_id = reference(snapshot, 6)
            if snapshot[18] == 1:
                matrix, cursor = list(IDENTITY), 19
            elif snapshot[18] == 0:
                matrix, cursor = rigid_matrix(numbers(snapshot, 19, 16)), 147
            else:
                raise ValueError('Unobserved component snapshot transform flag')
            namespace, end = read_string(snapshot, cursor)
            if (namespace != NIL_UUID or len(snapshot) != end+157
                    or snapshot[end:end+7] != bytes.fromhex('00000001000000')
                    or reference(snapshot, end+7) != datum_id
                    or struct.unpack_from('<I', snapshot, end+38)[0] != 3
                    or [reference(snapshot, end+42+11*i) for i in range(3)] != [snapshot_id, identity, scope_id]
                    or reference(snapshot, len(snapshot)-12) != snapshot_id or snapshot[-1:] != b'\0'):
                raise ValueError('Component snapshot repeated datum/creation/scope references disagree')
            datum = typed(datum_id, OCCURRENCE_DATUM)
            if (len(datum) != 39 or datum[:2] != bytes(2) or datum[13:16] != b'\1\0\0'
                    or datum[27] != 0 or reference(datum, 28) != snapshot_id):
                raise ValueError('Component occurrence datum snapshot owner disagrees')
            bookkeeping_id = reference(datum, 16)
            bookkeeping = typed(bookkeeping_id, BOOKKEEPING)
            if len(bookkeeping) != 39 or reference(bookkeeping, 12) != datum_id:
                raise ValueError('Component occurrence datum bookkeeping backlink disagrees')
            occurrence_id = reference(datum, 2)
            typed(occurrence_id, OCCURRENCE_GUID)
            occurrence = occurrences.get(occurrence_id)
            if (occurrence is None or occurrence['component_object_id'] != scope['component_object_id']
                    or occurrence['parent_collection_object_id'] is None):
                raise ValueError('Created occurrence/component membership unresolved')
            paths = [p for p in assembly['occurrence_paths'] if p['native_occurrence_object_id'] == occurrence_id]
            decoded.append({'feature_object_id': identity, 'kind': 'CreateComponent',
                            'component_object_id': scope['component_object_id'],
                            'component_name': scope['component_name'], 'component_scope_object_id': scope_id,
                            'snapshot_object_id': snapshot_id, 'occurrence_datum_object_id': datum_id,
                            'datum_bookkeeping_object_id': bookkeeping_id,
                            'native_occurrence_object_id': occurrence_id,
                            'occurrence_paths': [p['path'] for p in paths],
                            'snapshot_transform': matrix,
                            'snapshot_uses_identity_shortcut': bool(snapshot[18]),
                            'snapshot_matches_occurrence_cache': same(matrix, occurrence['local_transform']),
                            'transform_scope': 'Historical parent-local placement, cm, row-major; no joint solution or replay',
                            'association': 'CreateComponent/scope/snapshot links, repeated occurrence datum and reciprocal bookkeeping agree',
                            'snapshot_schema_status': 'Only explicit placement and creation correspondence decoded; other snapshot feature fields unsupported'})
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
            unresolved.append({'feature_object_id': identity, 'kind': 'CreateComponent', 'reason': str(error)})
    return {'decoded': decoded, 'unresolved': unresolved,
            'scope': 'Observed local component creation and explicit historical occurrence placement; copying, external links and replay unsupported'}
