"""Zero-BRep mappings whose component collection also lists typed meshes."""
import struct

from decode_body_mapping_variants import MAPPING
from decode_body_properties import COLLECTION
from decode_extrude import optional_reference
from decode_parameters import read_string
from decode_sketch import reference

SCOPE = ('Explicit empty native BRep mapping in a qualified component-owned mixed mesh/BRep '
         'collection. Listed meshes are not BRep mapping entries; no blob, mesh-to-ASM association, '
         'API handle assignment or lifecycle state is inferred.')
ROW_SCOPE = 'Typed reciprocal native mapping/body collection/context/component joins only; ASM root/final-body lifecycle unresolved'
COMPONENT = 'E03784ED-5E19-4E14-B9F2-3B07017018CD'
COMPONENT_BASE = '42054630-20A0-40E1-B969-CFE9E742F5C9'
CONTEXT = '372234A0-2A6C-4122-8047-E74DBA04F326'


def decode_mixed_empty_body_mappings(data, records, assembly, *,
                                      mixed_collections=None, body_properties=None):
    """Return decoded/unresolved/scope; ordinary pure-empty/positive mappings skip."""
    from decode_mixed_body_collections import decode_mixed_body_collections
    fresh = decode_mixed_body_collections(data, records, assembly, body_properties)
    matches = mixed_collections is None or mixed_collections == fresh
    primary = {}
    for record in records:
        if record.is_primary:
            primary.setdefault(record.object_id, []).append(record)

    def typed(identity, guid):
        rows = primary.get(identity, [])
        if len(rows) != 1 or rows[0].class_guid != guid:
            raise ValueError('Mixed empty mapping typed identity missing, ambiguous or wrong class')
        record = rows[0]
        return record, data[record.body:record.end]

    result = dict(decoded=[], unresolved=[], scope=SCOPE)
    for qualified in fresh['decoded']:
        if (qualified['role'] != 'StoredHistoryMapping74CA'
                or qualified['body_member_object_ids'] or not qualified['mesh_member_object_ids']):
            continue
        identity = qualified['mapping_record_object_id']
        try:
            if not matches:
                raise ValueError('Mixed empty mapping supplied collection proof differs from native source')
            record, body = typed(identity, MAPPING)
            if len(body) != 22 or body[:6] != bytes(6) or body[17] != 0:
                raise ValueError('Mixed empty mapping requires exact zero-entry22-byte framing')
            owner = reference(body, 6)
            filename, end = read_string(body, 18)
            if filename or end != 22 or owner != qualified['object_id']:
                raise ValueError('Mixed empty mapping filename/collection owner differs')
            collection_record, collection = typed(owner, COLLECTION)
            component_id = qualified['component_object_id']
            typed(component_id, COMPONENT)
            component_bases = [r for r in records if not r.is_primary
                and r.object_id == component_id and r.class_guid == COMPONENT_BASE]
            if len(component_bases) != 1:
                raise ValueError('Mixed empty mapping component inherited owner is missing or ambiguous')
            component_base = component_bases[0]
            component = data[component_base.body:component_base.end]
            context_id = qualified['context_record_object_id']
            if reference(component, 76) != owner or reference(component, 154) != context_id:
                raise ValueError('Mixed empty mapping does not use component ordinary collection/context slots')
            context_record, context = typed(context_id, CONTEXT)
            if len(context) != 23 or context[:12] != bytes(12) or reference(context, 12) != component_id:
                raise ValueError('Mixed empty mapping context/component backlink differs')
            if reference(collection, len(collection)-11) != component_id:
                raise ValueError('Mixed empty mapping collection/component backlink differs')
            count = struct.unpack_from('<I', collection, 7)[0]
            if (struct.unpack_from('<I', collection, 3)[0] != 0
                    or count != len(qualified['mixed_member_object_ids'])):
                raise ValueError('Mixed empty mapping independent BRep/mixed counts differ')
            cursor = 11+11*count
            if collection[cursor] != 1:
                raise ValueError('Mixed empty mapping collection branch marker differs')
            _, cursor = optional_reference(collection, cursor+1)
            mapping_slot = cursor
            if reference(collection, cursor) != identity or collection[cursor+11] != 1:
                raise ValueError('Mixed empty mapping collection/mapping references do not reciprocate')
            context_slot = cursor+12
            if reference(collection, context_slot) != context_id:
                raise ValueError('Mixed empty mapping collection context reference differs')
            # Independent complete replay of the admitted mapping record.
            replay = bytes(6)+b'\1'+struct.pack('<Q', owner)+bytes(2)+bytes(5)
            if replay != body:
                raise ValueError('Mixed empty mapping full payload replay differs')
            result['decoded'].append(dict(mapping_record_object_id=identity, owner_object_id=owner,
                component_object_id=component_id, context_record_object_id=context_id,
                body_count=0, bindings=[], history_blob_member=None,
                mapping_status='ExplicitEmptyMappingNoBodiesOrBlob', scope=ROW_SCOPE,
                mixed_collection_proof=dict(role=qualified['role'],
                    listed_mesh_object_ids=qualified['mesh_member_object_ids'],
                    mixed_member_object_ids=qualified['mixed_member_object_ids'],
                    BRep_member_object_ids=[], stored_BRep_count=0, stored_mixed_member_count=count,
                    component_collection_reference_offset=component_base.body+76,
                    component_context_reference_offset=component_base.body+154,
                    collection_mapping_reference_offset=collection_record.body+mapping_slot,
                    collection_context_reference_offset=collection_record.body+context_slot,
                    mapping_owner_reference_offset=record.body+6,
                    context_component_reference_offset=context_record.body+12,
                    mapping_payload_hex=body.hex(), exact_full_mapping_payload_replay=True,
                    mesh_ASM_binding=None, API_handle_assignment=None, lifecycle=None,
                    scope=SCOPE)))
        except (ValueError, KeyError, IndexError, TypeError, struct.error, UnicodeError) as error:
            result['unresolved'].append(dict(object_id=identity, reason=str(error)))
    return result
