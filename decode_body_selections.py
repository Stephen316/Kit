"""Explicit native body descriptor/anchor references, without topology guessing.

Identities here are native design object IDs, including historical inputs. They
are not ASM entity indices and do not establish which bodies are currently live.
"""

import struct
import uuid

from decode_body_properties import BODY
from decode_parameters import read_string
from decode_selection import native_proxy_references
from decode_sketch import attributes, numbers, reference


ANCHOR = "D26351F0-5940-4D23-AA20-2C35475A6D9E"
DESCRIPTOR = "9716F783-676D-42E0-93F9-EBF273E7C035"
PROXY = "2CA5A1CD-C99B-4C9B-91AF-57989148E841"
RECIPE = "7ACC2A03-0261-4879-A14A-A93D661A5BDC"
CONTEXT = "C46D3EEB-40E1-43FA-83DC-9CB204335417"
HELPER = "5FBE538E-139B-46D4-BCAF-CC796D1E1F78"
SUPPORT = "6CCF41D5-40BE-48ED-A834-18F3EAED6C57"


def decode_body_selections(data, records, body_properties=None):
    """Return typed anchors, owned body descriptors and body selection proxies.

    ``body_properties`` is the existing decoder's output. Optional names and
    component IDs come only from that independently checked ownership map.
    """
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: values[0] for identity, values in grouped.items() if len(values) == 1}
    properties = {item["object_id"]: item for item in (body_properties or {}).get("bodies", [])}
    anchors, descriptors, selections, unresolved = [], [], [], []

    def typed(identity, guid):
        target = primary.get(identity)
        if target is None or target.class_guid != guid:
            raise ValueError("Typed body selection reference missing, ambiguous or wrong class: " + str(identity))
        return target

    def owner(identity):
        if identity not in primary:
            raise ValueError("Body selection owner missing or ambiguous")
        return identity

    def text_uuid(payload, cursor):
        text, end = read_string(payload, cursor)
        if len(text) != 36:
            raise ValueError("Unsupported body selection UUID field")
        uuid.UUID(text)
        return text, end

    def enrich(identity):
        prop = properties.get(identity, {})
        keys = ("name", "name_status", "stored_body_tag", "component_object_id", "component_name",
                "collection_object_id", "ownership_evidence")
        return {key: prop[key] for key in keys if key in prop}

    for record in primary.values():
        if record.class_guid != ANCHOR:
            continue
        payload = data[record.body:record.end]
        try:
            if len(payload) != 102 or payload[:2] != b"\0\0":
                raise ValueError("Unsupported native body anchor prefix/length")
            native_uuid, cursor = text_uuid(payload, 2)
            if cursor != 78 or any(value not in (0, 1) for value in payload[cursor:cursor+2]):
                raise ValueError("Unsupported body anchor flag fields")
            body_id = reference(payload, cursor+2)
            typed(body_id, BODY)
            source_owner = owner(reference(payload, cursor+13))
            anchors.append({"object_id": record.object_id, "class_guid": ANCHOR,
                            "native_body_object_id": body_id, "source_owner_object_id": source_owner,
                            "native_uuid_text": native_uuid,
                            "stored_flags": list(payload[cursor:cursor+2]),
                            "native_body_reference_offset": record.body+cursor+2,
                            "body_properties": enrich(body_id),
                            "association": "Typed anchor contains an explicit reference to the native body record",
                            "lifecycle_status": "Historical or resulting identity; current visibility not inferred"})
        except (ValueError, UnicodeError, IndexError, struct.error) as error:
            unresolved.append({"object_id": record.object_id, "kind": "BodyAnchor", "reason": str(error)})
    anchor_map = {item["object_id"]: item for item in anchors}

    for record in primary.values():
        if record.class_guid != DESCRIPTOR:
            continue
        payload = data[record.body:record.end]
        try:
            if payload[:6] != bytes.fromhex("000001000000"):
                raise ValueError("Unsupported owned body descriptor prefix")
            stored_identifier = struct.unpack_from("<Q", payload, 6)[0]
            stored_kind = struct.unpack_from("<I", payload, 14)[0]
            recipe_id = reference(payload, 18)
            typed(recipe_id, RECIPE)
            if struct.unpack_from("<I", payload, 29)[0] != 1:
                raise ValueError("Unsupported body descriptor namespace count")
            namespace, cursor = text_uuid(payload, 33)
            entity_uuid, cursor = text_uuid(payload, cursor)
            if struct.unpack_from("<Q", payload, cursor)[0] != 2:
                raise ValueError("Unsupported body descriptor association header")
            context_count = struct.unpack_from("<I", payload, cursor+8)[0]
            if context_count not in (0, 1):
                raise ValueError("Unsupported body descriptor context count")
            context_ids = [reference(payload, cursor+12+11*i) for i in range(context_count)]
            for identity in context_ids:
                typed(identity, CONTEXT)
            cursor += 12+11*context_count
            if struct.unpack_from("<I", payload, cursor)[0] != 1:
                raise ValueError("Unsupported body descriptor anchor count")
            anchor_id = reference(payload, cursor+4)
            typed(anchor_id, ANCHOR)
            if anchor_id not in anchor_map:
                raise ValueError("Referenced body anchor was not decoded")
            cursor += 15
            if len(payload)-cursor != 67:
                raise ValueError("Unsupported body descriptor trailer size")
            if (payload[cursor+14:cursor+18] != b"\x01\x01\0\0"
                    or payload[cursor+26:cursor+30] != b"\x01\x01\0\0"
                    or payload[cursor+41:cursor+44] != b"\x01\0\0"
                    or payload[cursor+55] != 0):
                raise ValueError("Unsupported body descriptor trailer markers")
            helper_id, support_id = reference(payload, cursor+30), reference(payload, cursor+44)
            typed(helper_id, HELPER)
            support = typed(support_id, SUPPORT)
            support_payload = data[support.body:support.end]
            if support_payload[:6] != bytes.fromhex("000001000000"):
                raise ValueError("Unsupported body descriptor support prefix")
            support_uuid, support_cursor = text_uuid(support_payload, 6)
            if support_uuid != anchor_map[anchor_id]["native_uuid_text"]:
                raise ValueError("Body descriptor support/anchor native UUIDs disagree")
            if any(value not in (0, 1) for value in support_payload[support_cursor+8:support_cursor+10]):
                raise ValueError("Unsupported body descriptor support flag fields")
            support_count = struct.unpack_from("<I", support_payload, support_cursor+10)[0]
            support_cursor += 14
            if not 1 <= support_count <= 1024 or len(support_payload) != support_cursor+19*support_count+27:
                raise ValueError("Unsupported body descriptor support reference count")
            support_refs = [reference(support_payload, support_cursor+19*i) for i in range(support_count)]
            if (reference(support_payload, len(support_payload)-27) != record.object_id
                    or anchor_map[anchor_id]["source_owner_object_id"] not in support_refs):
                raise ValueError("Body descriptor/support ownership is not reciprocal")
            feature_id = owner(reference(payload, cursor+56))
            anchor = anchor_map[anchor_id]
            descriptors.append({"object_id": record.object_id, "class_guid": DESCRIPTOR,
                                "owner_object_id": feature_id,
                                "body_anchor_object_id": anchor_id,
                                "native_body_object_id": anchor["native_body_object_id"],
                                "body_properties": anchor["body_properties"],
                                "source_owner_object_id": anchor["source_owner_object_id"],
                                "recipe_record_object_id": recipe_id,
                                "stored_identifier": stored_identifier,
                                "identifier_scope": "Opaque stored identifier; not a native body ID or ASM record index",
                                "stored_kind_field": stored_kind,
                                "namespace_text": namespace, "entity_uuid_text": entity_uuid,
                                "context_record_object_ids": context_ids,
                                "stored_trailer_kind_field": struct.unpack_from("<I", payload, cursor)[0],
                                "uninterpreted_trailer_field_hex": payload[cursor+4:cursor+14].hex(),
                                "uninterpreted_cached_scalar": numbers(payload, cursor+18, 1)[0],
                                "helper_record_object_id": helper_id, "support_record_object_id": support_id,
                                "support_reference_object_ids": support_refs,
                                "association": "Owned descriptor -> counted typed body anchor -> explicit native body reference",
                                "lifecycle_status": "Selection identity retained; historical input is not replaced with a resulting body"})
        except (ValueError, UnicodeError, IndexError, struct.error) as error:
            unresolved.append({"object_id": record.object_id, "kind": "BodyDescriptor", "reason": str(error)})
    descriptor_map = {item["object_id"]: item for item in descriptors}

    for record in primary.values():
        if record.class_guid != PROXY:
            continue
        body_candidate = False
        try:
            payload = data[record.body:record.end]
            if len(payload) < 6 or payload[0] != 0 or payload[1] not in (0, 1):
                continue
            cursor = attributes(payload, 2)[1] if payload[1] else 2
            count = struct.unpack_from("<I", payload, cursor)[0]
            if not 1 <= count <= 1024 or cursor+4+11*count > len(payload):
                continue
            first_ids = [reference(payload, cursor+4+11*i) for i in range(count)]
            body_candidate = any(primary.get(identity) and primary[identity].class_guid == DESCRIPTOR
                                 for identity in first_ids)
            if not body_candidate:
                continue
            descriptor_ids, props = native_proxy_references(data, record)
            # Other proxy families select faces, edges, sketches or construction
            # entities. This module makes no claims about those families.
            if not any(primary.get(identity) and primary[identity].class_guid == DESCRIPTOR
                       for identity in descriptor_ids):
                continue
            feature_id = owner(reference(payload, len(payload)-11))
            if any(identity not in descriptor_map for identity in descriptor_ids):
                raise ValueError("Proxy contains unresolved or mixed body/other descriptor families")
            selected = [descriptor_map[identity] for identity in descriptor_ids]
            if any(item["owner_object_id"] != feature_id for item in selected):
                raise ValueError("Body proxy and descriptor owners disagree")
            selections.append({"selection_record_object_id": record.object_id,
                               "owner_object_id": feature_id, "attributes": props,
                               "descriptor_object_ids": descriptor_ids,
                               "native_body_object_ids": [item["native_body_object_id"] for item in selected],
                               "association": "Explicit counted proxy list with matching descriptor owners"})
        except (ValueError, UnicodeError, IndexError, struct.error) as error:
            if body_candidate:
                unresolved.append({"object_id": record.object_id, "kind": "BodySelectionProxy", "reason": str(error)})
    return {"body_anchors": anchors, "body_descriptors": descriptors, "selection_proxies": selections,
            "unresolved": unresolved,
            "scope": "Observed explicit native body identities and owned body descriptors; face/edge topology, context semantics and current body lifecycle remain unresolved"}
