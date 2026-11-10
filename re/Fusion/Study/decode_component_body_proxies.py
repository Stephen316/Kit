"""Observed body selection proxies with two populated component-context slots.

Slot order and explicitly stored occurrence UUIDs are retained. No source/target
coordinate interpretation, occurrence transform, or body lifecycle is inferred.
"""

import struct
import uuid

from decode_body_selections import CONTEXT, DESCRIPTOR, HELPER, PROXY, SUPPORT
from decode_extrude import optional_reference
from decode_parameters import read_string
from decode_sketch import attributes, numbers, reference


FRAME = "2E3AC990-483D-4A55-8662-C064B976A957"
FRAME_LINK = "549FBB80-B890-473E-A5C0-415D3D9BF4E6"
ROUTE_LIST = "FF415D89-A1DB-44AC-B824-E9A772B86ED4"
ROUTE = "96CBEA21-17E0-4BCB-BA77-04EA87B47934"
SECONDARY = "2DF7DA30-A4E4-4260-AFD1-D9C7154CB44B"
BODY_LINK = "CB4F4CC2-9D6F-48BA-9B1F-20C1992C9C9C"
BODY_LEAF = "90055C05-546C-4EE7-B3C9-3DD922AD0C9C"


def decode_component_body_proxies(data, records, body_selections, assembly=None):
    """Decode the observed populated-context variant after body descriptors."""
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: values[0] for identity, values in grouped.items() if len(values) == 1}
    descriptors = {item["object_id"]: item for item in body_selections["body_descriptors"]}
    occurrences = (assembly or {}).get("native_occurrences", [])
    decoded, unresolved = [], []

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError("Component body proxy typed reference missing, ambiguous or wrong class")
        return record, data[record.body:record.end]

    def text_uuid(payload, cursor):
        text, cursor = read_string(payload, cursor)
        if len(text) != 36:
            raise ValueError("Unsupported component-context UUID field")
        uuid.UUID(text)
        return text, cursor

    def descriptor_context(descriptor):
        identities = descriptor["context_record_object_ids"]
        if len(identities) != 1:
            raise ValueError("Expected one observed body descriptor context")
        identity = identities[0]
        _, payload = typed(identity, CONTEXT)
        if len(payload) != 181 or payload[:2] != b"\0\0" or payload[6:10] != b"\0"*4:
            raise ValueError("Unsupported descriptor context layout")
        namespace, cursor = text_uuid(payload, 10)
        context_uuid, cursor = text_uuid(payload, cursor)
        if namespace != descriptor["namespace_text"] or struct.unpack_from("<Q", payload, cursor)[0] != 2:
            raise ValueError("Descriptor context namespace/header disagrees")
        link_id = reference(payload, cursor+8)
        _, link = typed(link_id, BODY_LINK)
        if len(link) != 14 or link[:2] != b"\0\0" or link[-1:] != b"\0":
            raise ValueError("Unsupported descriptor-context body link")
        leaf_id = reference(link, 2)
        _, leaf = typed(leaf_id, BODY_LEAF)
        if len(leaf) != 10 or leaf[:2] != b"\0\0":
            raise ValueError("Unsupported descriptor-context body leaf")
        identity_from_context = struct.unpack_from("<Q", leaf, 2)[0]
        if identity_from_context != descriptor["native_body_object_id"]:
            raise ValueError("Descriptor-context body identity disagrees with typed body anchor")
        return {"object_id": identity, "namespace_text": namespace, "context_uuid_text": context_uuid,
                "stored_index_field": struct.unpack_from("<I", payload, 2)[0],
                "body_link_object_id": link_id, "body_leaf_object_id": leaf_id,
                "native_body_object_id": identity_from_context}

    def frame(identity, owner_id, descriptor, context):
        _, payload = typed(identity, FRAME)
        if (len(payload) != 78 or payload[:20] != b"\0"*20
                or struct.unpack_from("<I", payload, 20)[0] != 3 or payload[24:37] != b"\0"*13
                or payload[48:50] != b"\x01\0" or payload[72:] != b"\0"*6
                or reference(payload, 50) != owner_id):
            raise ValueError("Unsupported component-context frame layout/owner")
        frame_id, list_id = reference(payload, 37), reference(payload, 61)
        typed(frame_id, FRAME_LINK)
        _, listing = typed(list_id, ROUTE_LIST)
        if len(listing) != 18 or listing[:7] != bytes.fromhex("00000001000000"):
            raise ValueError("Unsupported component-context route wrapper")
        route_id = reference(listing, 7)
        _, route = typed(route_id, ROUTE)
        if route[:2] != b"\0\0":
            raise ValueError("Unsupported component-context route prefix")
        mode = struct.unpack_from("<I", route, 2)[0]
        occurrence_uuid, cursor = text_uuid(route, 6)
        stored_occurrence = None
        if mode == 1:
            namespace, cursor = text_uuid(route, cursor)
            route_context, cursor = text_uuid(route, cursor)
            if (namespace != context["namespace_text"] or route_context != context["context_uuid_text"]
                    or struct.unpack_from("<Q", route, cursor)[0] != 2):
                raise ValueError("Populated route context disagrees with descriptor context")
            cursor += 8
            matches = [item for item in occurrences if item.get("instance_guid_text") == occurrence_uuid]
            if len(matches) > 1:
                raise ValueError("Occurrence UUID is ambiguous in assembly records")
            if matches:
                stored_occurrence = {key: matches[0][key] for key in
                                     ("object_id", "component_object_id", "instance_number", "instance_guid_text")}
        elif mode == 0:
            if occurrence_uuid != str(uuid.UUID(int=0)) or route[cursor:cursor+12] != struct.pack("<IQ", 0, 1):
                raise ValueError("Unsupported empty occurrence route")
            cursor += 12
        else:
            raise ValueError("Unsupported component-context route mode")
        namespace, cursor = text_uuid(route, cursor)
        entity_uuid, cursor = text_uuid(route, cursor)
        if (namespace != descriptor["namespace_text"] or entity_uuid != descriptor["entity_uuid_text"]
                or route[cursor:] != struct.pack("<QI", 2, 0)):
            raise ValueError("Component route does not terminate at the selected body descriptor")
        return {"object_id": identity, "frame_link_object_id": frame_id,
                "route_wrapper_object_id": list_id, "route_object_id": route_id,
                "stored_route_mode": mode, "stored_occurrence_uuid_text": occurrence_uuid,
                "matching_native_occurrence": stored_occurrence,
                "association": "Explicit owned frame and route; namespace/entity UUIDs match the selected descriptor"}

    for record in primary.values():
        if record.class_guid != PROXY:
            continue
        payload = data[record.body:record.end]
        candidate = False
        try:
            if payload[:2] != b"\0\0" and payload[:2] != b"\0\x01":
                continue
            props, cursor = attributes(payload, 2) if payload[1] else ({}, 2)
            count = struct.unpack_from("<I", payload, cursor)[0]
            if not 1 <= count <= 1024 or cursor+4+11*count > len(payload):
                continue
            identities = [reference(payload, cursor+4+11*i) for i in range(count)]
            cursor += 4+11*count
            if payload[cursor:cursor+2] == b"\0\0":
                continue
            candidate = any(primary.get(identity) and primary[identity].class_guid == DESCRIPTOR for identity in identities)
            if not candidate:
                continue
            if count != 1 or identities[0] not in descriptors:
                raise ValueError("Only the observed single decoded body descriptor context variant is supported")
            descriptor = descriptors[identities[0]]
            context_ids = []
            for _ in range(2):
                identity, cursor = optional_reference(payload, cursor)
                if identity is None:
                    raise ValueError("Only two populated component-context slots observed")
                typed(identity, FRAME)
                context_ids.append(identity)
            if struct.unpack_from("<I", payload, cursor)[0] != 1:
                raise ValueError("Unsupported component proxy secondary-list count")
            secondary_id = reference(payload, cursor+4)
            _, secondary = typed(secondary_id, SECONDARY)
            if secondary != bytes.fromhex("0000010100"):
                raise ValueError("Unsupported component proxy secondary payload")
            cursor += 15
            if (len(payload)-cursor != 71 or payload[cursor+18:cursor+22] != b"\x01\x01\0\0"
                    or payload[cursor+30:cursor+34] != b"\x01\x01\0\0"
                    or payload[cursor+45:cursor+48] != b"\x01\0\0" or payload[cursor+59] != 0):
                raise ValueError("Unsupported component proxy trailer")
            helper_id, support_id = reference(payload, cursor+34), reference(payload, cursor+48)
            typed(helper_id, HELPER)
            _, support = typed(support_id, SUPPORT)
            if (len(support) != 58 or support[:12] != bytes.fromhex("000000000000010101000000")
                    or reference(support, 12) != descriptor["object_id"] or reference(support, 31) != record.object_id):
                raise ValueError("Component proxy/support/descriptor references are not reciprocal")
            owner_id = reference(payload, cursor+60)
            if owner_id != descriptor["owner_object_id"] or owner_id not in primary:
                raise ValueError("Component proxy/descriptor owner mismatch")
            context = descriptor_context(descriptor)
            frames = [frame(identity, owner_id, descriptor, context) for identity in context_ids]
            decoded.append({"selection_record_object_id": record.object_id, "owner_object_id": owner_id,
                            "attributes": props, "descriptor_object_ids": identities,
                            "native_body_object_ids": [descriptor["native_body_object_id"]],
                            "body_properties": descriptor["body_properties"],
                            "context_slots": frames, "descriptor_context": context,
                            "secondary_record_object_id": secondary_id, "helper_record_object_id": helper_id,
                            "support_record_object_id": support_id,
                            "uninterpreted_trailer_prefix_hex": payload[cursor:cursor+18].hex(),
                            "uninterpreted_cached_scalar": numbers(payload, cursor+22, 1)[0],
                            "association": "Owned proxy and reciprocal support select a body whose anchor and independent context leaf agree",
                            "context_status": "Ordered native context links recovered; slot direction, transforms and lifecycle remain unresolved"})
        except (ValueError, UnicodeError, IndexError, struct.error) as error:
            if candidate:
                unresolved.append({"object_id": record.object_id, "kind": "ComponentBodySelectionProxy", "reason": str(error)})
    return {"decoded": decoded, "unresolved": unresolved,
            "scope": "Observed two populated component-context body proxy slots; occurrence UUID association only, without transform or lifecycle interpretation"}
