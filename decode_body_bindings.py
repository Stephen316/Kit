"""Explicit native body/blob lists; ordered ASM root association is experimental."""

import struct

from decode_parameters import read_string
from decode_sketch import attributes, reference


def decode_body_bindings(data, records, member, asm_summary, body_properties=None):
    decoded, unresolved = [], []
    asset = member.rsplit("/FusionDesignSegmentType1/", 1)[0]
    primary = {r.object_id: r for r in records if r.is_primary}
    streams = {s["member"]: s for s in asm_summary["streams"]}
    properties = {b["object_id"]: b for b in (body_properties or {}).get("bodies", [])}
    for record in records:
        if not record.is_primary or record.class_guid != "74CA4562-59F8-4C97-8AD1-F8297C21F9AA":
            continue
        body = data[record.body:record.end]
        try:
            if body[:2] != b"\0\0":
                raise ValueError("Unsupported native history-blob binding prefix")
            count = struct.unpack_from("<I", body, 2)[0]
            if not 1 <= count <= 100000 or 6+16*count+16 > len(body):
                raise ValueError("Unsupported native body mapping count")
            entries = [struct.unpack_from("<QQ", body, 6+16*i) for i in range(count)]
            cursor = 6+16*count
            owner = reference(body, cursor)
            if body[cursor+11] != 0:
                raise ValueError("Unsupported history-blob filename separator")
            filename, end = read_string(body, cursor+12)
            if end != len(body) or not filename.startswith("BREP.") or not filename.endswith(".smbh") or "/" in filename or "\\" in filename:
                raise ValueError("Unsupported history-blob filename layout")
            blob_member = asset+"/Breps.BlobParts/"+filename
            stream = streams.get(blob_member)
            if stream is None:
                raise ValueError("Referenced history blob not found in this asset")
            if len({e[0] for e in entries}) != count or len({e[1] for e in entries}) != count:
                raise ValueError("Duplicate body handles or native body identities")
            roots = stream.get("declared_root_records", [])
            ordered_candidates = (stream.get("complete_token_stream") and len(roots) == count+1
                                  and roots[0]["kind"] == "asmheader"
                                  and all(r["kind"] == "body" for r in roots[1:]))
            bindings = []
            for ordinal, (handle, identity) in enumerate(entries):
                native = primary.get(identity)
                if native is None or native.class_guid != "D3937028-C20C-4E65-B010-94AD418A5C20":
                    raise ValueError("Native body entry does not resolve to the observed body class")
                chunk = data[native.body:native.end]
                if chunk[0] != 0 or chunk[1] not in (0, 1):
                    raise ValueError("Unsupported native body tag prefix")
                tag_cursor = attributes(chunk, 2)[1] if chunk[1] else 2
                tag, _ = read_string(chunk, tag_cursor)
                item = {"stored_handle": handle, "native_body_object_id": identity,
                        "stored_body_tag": tag, "native_body_record_offset": native.start,
                        "mapping_entry_ordinal": ordinal,
                        "handle_scope": "Opaque stored handle; not an ASM record index"}
                prop = properties.get(identity)
                if prop and "collection_object_id" in prop:
                    if prop["collection_object_id"] != owner:
                        raise ValueError("Blob mapping owner disagrees with native body collection")
                    item.update(name=prop["name"], name_status=prop["name_status"],
                                component_object_id=prop["component_object_id"], component_name=prop["component_name"])
                if ordered_candidates:
                    item["candidate_asm_body_index"] = roots[ordinal+1]["index"]
                    item["association_status"] = "Experimental ordered-entry/leading-root association; requires broader validation"
                else:
                    item["association_status"] = "ASM root association unresolved"
                bindings.append(item)
            decoded.append({"mapping_record_object_id": record.object_id, "owner_object_id": owner,
                            "history_blob_member": blob_member, "body_count": count, "bindings": bindings,
                            "scope": "Explicit native body/blob mapping; ordered ASM root association remains experimental"})
        except (ValueError, UnicodeError, IndexError, struct.error) as error:
            unresolved.append({"object_id": record.object_id, "reason": str(error)})
    return {"decoded": decoded, "unresolved": unresolved,
            "scope": "Native mapping tables and conditional root candidates; no guaranteed final-body identity"}
