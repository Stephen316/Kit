"""Observed Loft Join/Cut/Intersect/NewBody controls and explicit input bodies.

NewComponent requests normalize to NewBody in the captured API result. Native
component-context profiles are decoded independently; no extra operation enum is
invented from that request or from the presence of component context slots.
"""

import struct

from decode_body_selections import decode_body_selections
from decode_component_profile_selections import resolve_component_sketch_profiles
from decode_loft_modes import decode_loft_modes
from decode_profile_selections import resolve_sketch_profiles
from decode_sketch import reference


def resolve_loft_profiles(data, records, selection_id, owner_id, features):
    matches = [r for r in records if r.is_primary and r.object_id == selection_id
               and r.class_guid == '2CA5A1CD-C99B-4C9B-91AF-57989148E841']
    if len(matches) != 1:
        raise ValueError('Loft profile proxy missing or ambiguous')
    payload = data[matches[0].body:matches[0].end]
    if len(payload) == 125:
        return resolve_component_sketch_profiles(data, records, selection_id, owner_id, features)
    return resolve_sketch_profiles(data, records, selection_id, owner_id, features)


def decode_loft_operations(data, records, body, feature, features):
    result = decode_loft_modes(data, records, body, feature, features,
                               allowed_operation_codes=(1, 2, 3, 4), profile_resolver=resolve_loft_profiles)
    cursor = result['result_anchor_list_end_relative_offset']
    if body[cursor:cursor+4] != b'\0'*4:
        raise ValueError('Unobserved Loft post-anchor reserved field')
    count = struct.unpack_from('<I', body, cursor+4)[0]
    if count != (0 if result['stored_operation_code'] == 4 else 1):
        raise ValueError('Unobserved Loft operation/input-body proxy count')
    identities = [reference(body, cursor+8+11*i) for i in range(count)]
    if len(set(identities)) != count:
        raise ValueError('Duplicate Loft input-body proxy')
    # The following UUID-string framing is a boundary guard, not a decoded ID.
    if struct.unpack_from('<I', body, cursor+8+11*count)[0] != 36:
        raise ValueError('Unsupported Loft post-input-list framing')
    selected = []
    if identities:
        summary = decode_body_selections(data, records)
        for identity in identities:
            matches = [s for s in summary['selection_proxies'] if s['selection_record_object_id'] == identity
                       and s['owner_object_id'] == feature['object_id']]
            if len(matches) != 1 or len(matches[0]['descriptor_object_ids']) != 1:
                raise ValueError('Loft input body proxy/owner unresolved')
            proxy = matches[0]
            descriptors = [d for d in summary['body_descriptors'] if d['object_id'] == proxy['descriptor_object_ids'][0]
                           and d['owner_object_id'] == feature['object_id']]
            if len(descriptors) != 1:
                raise ValueError('Loft input body descriptor/owner unresolved')
            descriptor = descriptors[0]
            selected.append({'selection_record_object_id': identity,
                             'descriptor_object_id': descriptor['object_id'],
                             'native_body_object_id': descriptor['native_body_object_id'],
                             'body_anchor_object_id': descriptor['body_anchor_object_id'],
                             'source_owner_object_id': descriptor['source_owner_object_id'],
                             'association': 'Explicit counted Loft proxy, matching descriptor owner and typed native body anchor'})
    result.update(input_body_selection_record_object_ids=identities, input_bodies=selected,
                  input_body_status='Observed single input body for Join/Cut/Intersect; historical identity, result lifecycle and general participant scope unresolved',
                  component_operation_status='NewComponent API request can normalize to NewBody; component context does not establish a separate native operation code')
    return result
