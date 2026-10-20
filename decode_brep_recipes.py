"""Frame observed native topology-name recipes without inferring their geometry."""

import struct


RECIPE_GUID = "7ACC2A03-0261-4879-A14A-A93D661A5BDC"


def decode_recipe(data, record, primary_records=None):
    body = data[record.body:record.end]
    cursor = 0

    def take(count):
        nonlocal cursor
        if count < 0 or cursor+count > len(body):
            raise ValueError("Truncated topology recipe")
        result = body[cursor:cursor+count]
        cursor += count
        return result

    def integer():
        return struct.unpack("<I", take(4))[0]

    def text():
        size = integer()
        if not 1 <= size <= 128:
            raise ValueError("Unsupported recipe name length")
        value = take(size).decode("ascii")
        if any(ord(v) < 32 or ord(v) > 126 for v in value):
            raise ValueError("Nonprintable recipe name")
        return value

    if record.class_guid != RECIPE_GUID or not record.is_primary or take(2) != b"\0\0":
        raise ValueError("Unsupported topology-recipe class/prefix")
    header = [integer(), integer()]
    if header != [1, 3]:
        raise ValueError("Unsupported observed recipe header fields")
    count = integer()
    if not 1 <= count <= 100000:
        raise ValueError("Unsupported recipe name-table count")
    names = []
    for index in range(count):
        term_count = integer()
        if not 1 <= term_count <= 64:
            raise ValueError("Unsupported recipe term count")
        terms = []
        for _ in range(term_count):
            term = {"name": text(), "stored_index": integer()}
            tag = integer()
            if tag == 1:
                value = struct.unpack("<Q", take(8))[0]
            elif tag == 0:
                value = integer()
                if value != 0:
                    raise ValueError("Unsupported null recipe reference value")
            else:
                raise ValueError("Unsupported recipe reference tag")
            term.update(stored_reference_tag=tag, stored_reference_value=value)
            target = (primary_records or {}).get(value) if tag == 1 else None
            if target is not None:
                term["matching_primary_record"] = {"object_id": target.object_id, "class_guid": target.class_guid,
                                                   "record_offset": target.start,
                                                   "scope": "Numeric identity match in this stream; persistent topology meaning unresolved"}
            terms.append(term)
        names.append({"table_index": index, "terms": terms})
    if integer() != 0:
        raise ValueError("Unsupported recipe payload separator")
    kind = text()
    if not kind.endswith("_recipe_data"):
        raise ValueError("Unsupported recipe payload-kind name")
    payload_offset = cursor
    payload = take(len(body)-cursor)
    result = {"object_id": record.object_id, "class_guid": record.class_guid, "record_offset": record.start,
              "stored_header_fields": header, "name_table": names, "payload_kind": kind,
              "payload_relative_offset": payload_offset, "payload_length": len(payload), "payload_hex": payload.hex(),
              "scope": "Observed grouped terms and tagged numeric references; topology operation semantics unresolved"}
    if kind in ("body_recipe_data", "face_recipe_data", "bounded_face_recipe_data") and len(payload)%4 == 0:
        result["uninterpreted_payload_int32"] = list(struct.unpack("<"+"i"*(len(payload)//4), payload))
    return result


def decode_recipes(data, records):
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {key: values[0] for key, values in grouped.items() if len(values) == 1}
    decoded, unresolved = [], []
    for record in records:
        if record.class_guid != RECIPE_GUID or not record.is_primary:
            continue
        try:
            decoded.append(decode_recipe(data, record, primary))
        except (ValueError, UnicodeError, IndexError, struct.error) as error:
            unresolved.append({"object_id": record.object_id, "reason": str(error)})
    return {"recipes": decoded, "unresolved": unresolved,
            "scope": "Observed structural recipe framing only; no face/edge identity or chosen-cell reconstruction"}
