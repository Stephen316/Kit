"""Observed native body collection ownership and typed custom-name field anchors."""

import math
import re
import struct

from decode_parameters import read_string
from decode_sketch import attributes, reference

BODY = "D3937028-C20C-4E65-B010-94AD418A5C20"
COLLECTION = "CD57BC48-50EC-47DC-975A-FB6DEA72F4DA"
NAME_HELPER = "702b9cd2-537c-429e-8cc4-22beeeb98c37"


def decode_body_properties(data, records, assembly):
    primary = {r.object_id: r for r in records if r.is_primary}
    components = {c["object_id"]: c for c in assembly["components"]}
    collections, unresolved, ownership = [], [], {}
    for record in primary.values():
        if record.class_guid != COLLECTION:
            continue
        body = data[record.body:record.end]
        try:
            if body[:3] != b"\0"*3:
                raise ValueError("Unsupported native body collection prefix")
            count = struct.unpack_from("<I", body, 7)[0]
            if count > 100000 or 11+11*count > len(body):
                raise ValueError("Unsupported body collection size")
            identities = [reference(body, 11+11*i) for i in range(count)]
            repeated = len(body)-15-11*count
            if repeated < 11+11*count or struct.unpack_from("<I", body, repeated)[0] != count:
                raise ValueError("Body collection repeated count disagrees")
            if [reference(body, repeated+4+11*i) for i in range(count)] != identities:
                raise ValueError("Body collection repeated membership disagrees")
            component_id = reference(body, len(body)-11)
            if component_id not in components:
                raise ValueError("Body collection component reference unresolved")
            for identity in identities:
                native = primary.get(identity)
                if native is None or native.class_guid != BODY or identity in ownership:
                    raise ValueError("Body collection member missing, unsupported or multiply owned")
                chunk = data[native.body:native.end]
                if reference(chunk, len(chunk)-11) != record.object_id:
                    raise ValueError("Body/collection ownership is not reciprocal")
            collection = {"object_id": record.object_id, "class_guid": COLLECTION, "component_object_id": component_id,
                          "component_name": components[component_id]["name"], "body_object_ids": identities,
                          "stored_field_at_3": struct.unpack_from("<I", body, 3)[0],
                          "uninterpreted_middle_hex": body[11+11*count:repeated].hex()}
            collections.append(collection)
            for identity in identities:
                ownership[identity] = collection
        except (ValueError, IndexError, struct.error) as error:
            unresolved.append({"object_id": record.object_id, "kind": "BodyCollection", "reason": str(error)})

    bodies = []
    for record in primary.values():
        if record.class_guid != BODY:
            continue
        body = data[record.body:record.end]
        item = {"object_id": record.object_id, "class_guid": BODY, "record_offset": record.start,
                "name": None, "name_status": "Stored body name field unresolved"}
        collection = ownership.get(record.object_id)
        if collection:
            item.update(collection_object_id=collection["object_id"],
                        component_object_id=collection["component_object_id"], component_name=collection["component_name"],
                        ownership_evidence="Repeated collection membership plus reciprocal native body/collection references")
        else:
            item["ownership_status"] = "Native body component ownership unresolved"
        try:
            if body[0] != 0 or body[1] not in (0, 1):
                raise ValueError("Unsupported native body tag layout")
            cursor = attributes(body, 2)[1] if body[1] else 2
            item["stored_body_tag"], _ = read_string(body, cursor)
            owner_id = reference(body, len(body)-11)
            marker = b"\x01"+struct.pack("<Q", owner_id)+b"\0\0"
            candidates = []
            for match in re.finditer(re.escape(marker), body):
                cursor = match.start()
                if cursor+23 > len(body)-11 or body[cursor+11] != 0:
                    continue
                try:
                    helper_id = reference(body, cursor+12)
                    helper = primary.get(helper_id)
                    if helper is None or helper.class_guid != NAME_HELPER:
                        continue
                    name, end = read_string(body, cursor+23)
                    if end+18 > len(body)-11:
                        continue
                    values = struct.unpack_from("<4f", body, end)
                    if not all(math.isfinite(v) and 0 <= v <= 1 for v in values):
                        continue
                    if body[end+16] not in (0, 1) or body[end+17] not in (0, 1):
                        continue
                    candidates.append((name, helper_id, cursor+23))
                except (ValueError, UnicodeError, IndexError, struct.error):
                    continue
            if len(candidates) != 1:
                raise ValueError("Typed body-name field anchor missing or ambiguous")
            name, helper_id, name_offset = candidates[0]
            item.update(name=name or None, name_helper_object_id=helper_id, name_field_offset=record.body+name_offset,
                        name_status="Stored custom name recovered" if name else "Stored name empty; default UI label not inferred",
                        name_evidence="Unique owner reference + typed helper reference + bounded UTF-16 field and observed trailer")
        except (ValueError, UnicodeError, IndexError, struct.error) as error:
            unresolved.append({"object_id": record.object_id, "kind": "BodyName", "reason": str(error)})
        bodies.append(item)
    return {"bodies": bodies, "collections": collections, "unresolved": unresolved,
            "scope": "Observed explicit component ownership and custom-name field anchors; material/property schemas remain partial"}
