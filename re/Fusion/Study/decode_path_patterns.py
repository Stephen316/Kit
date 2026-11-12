"""Observed path-pattern shared controls and strict legacy body wrapper."""

import struct

from decode_selection import native_proxy_references, resolve_single_sketch_curve
from decode_sketch import numbers, reference


def parse_path_pattern_controls(data, records, control_id, feature, features, *, path_resolver=None,
        allowed_type_codes=((2, 2),), allow_empty_ordinal_pairs=False,
        auxiliary_resolver=None, element_resolver=None):
    """Parse shared controls; non-body layouts require explicit typed callbacks."""
    def primary(identity, guid):
        matches = [r for r in records if r.is_primary and r.object_id == identity and r.class_guid == guid]
        if len(matches) != 1:
            raise ValueError("Path-pattern typed reference missing or ambiguous")
        return matches[0]

    def owned_proxy(identity):
        record = primary(identity, "2CA5A1CD-C99B-4C9B-91AF-57989148E841")
        payload = data[record.body:record.end]
        if reference(payload, len(payload)-11) != feature["object_id"]:
            raise ValueError("Path-pattern proxy owner disagrees with feature")
        return native_proxy_references(data, record)[0]

    control = primary(control_id, "BE1FB171-D98A-4A4D-99C2-3738627CF79C")
    chunk = data[control.body:control.end]
    if (chunk[:5] != bytes.fromhex("0102000000") or chunk[16:20] != b"\0"*4
            or chunk[31:36] != b"\0"*5 or chunk[60] != 1 or any(v not in (0, 1) for v in chunk[61:64])
            or (chunk[113:125] != b"\0"*12 or struct.unpack_from("<II", chunk, 125) not in allowed_type_codes or chunk[133:137] != b"\xff"*4) or chunk[137] not in (0, 1)):
        raise ValueError("Unsupported path-pattern control layout")
    bindings = {p["binding_object_id"]: p for p in feature["parameters"]}

    def parameter(identity, role):
        parameter = bindings.get(identity)
        if parameter is None or parameter["role"] != role:
            raise ValueError("Path-pattern binding disagrees with role: "+role)
        return parameter["raw_float64"]

    quantity_id, distance_id = reference(chunk, 5), reference(chunk, 20)
    quantity = parameter(quantity_id, "countU")
    if not quantity.is_integer() or not 2 <= quantity <= 1024 or reference(chunk, 83) != distance_id:
        raise ValueError("Unsupported path-pattern quantity/repeated distance reference")
    quantity = int(quantity)
    distance = parameter(distance_id, "PathPatternDelta")
    if distance <= 0:
        raise ValueError("Only observed positive path-pattern distances supported")
    selection_id = reference(chunk, 64)
    path = (path_resolver(data, records, selection_id, feature["object_id"], features) if path_resolver
            else resolve_single_sketch_curve(data, records, selection_id, feature["object_id"], features, ("Line", "Arc")))
    native_start = numbers(chunk, 105, 1)[0]
    if not 0 <= native_start <= 1:
        raise ValueError("Path-pattern start fraction outside observed domain")
    pair_count = struct.unpack_from("<I", chunk, 138)[0]
    if pair_count != quantity-1 and not (allow_empty_ordinal_pairs and pair_count == 0):
        raise ValueError("Path-pattern ordinal table does not match quantity")
    pairs = [list(struct.unpack_from("<QQ", chunk, 142+16*i)) for i in range(pair_count)]
    if pairs and [p[0] for p in pairs] != list(range(1, quantity)):
        raise ValueError("Unsupported path-pattern ordinal sequence")
    cursor = 142+16*pair_count
    if struct.unpack_from("<I", chunk, cursor)[0] != quantity:
        raise ValueError("Path-pattern element-reference count disagrees with quantity")
    element_ids = [reference(chunk, cursor+4+11*i) for i in range(quantity)]
    element_details = []
    for ordinal, identity in enumerate(element_ids):
        if element_resolver is not None:
            detail = element_resolver(data, records, identity, ordinal, control_id, feature["object_id"])
            if not isinstance(detail, dict):
                raise ValueError("Path-pattern element callback did not return bounded provenance")
            element_details.append(detail)
            continue
        record = primary(identity, "AD719C1A-11AF-4537-BB41-030A9091D36B")
        payload = data[record.body:record.end]
        if (len(payload) != 17 or payload[:2] != b"\0\0" or struct.unpack_from("<I", payload, 2)[0] != ordinal
                or reference(payload, 6) != control_id):
            raise ValueError("Path-pattern element ordinal/controller references disagree")
    cursor += 4+11*quantity
    if reference(chunk, cursor) != quantity_id or reference(chunk, cursor+11) != feature["object_id"]:
        raise ValueError("Path-pattern quantity/owner footer disagrees")
    auxiliary_id = reference(chunk, cursor+22)
    auxiliary_details = None
    if auxiliary_resolver is None:
        auxiliary_descriptors = owned_proxy(auxiliary_id)
    else:
        auxiliary_details = auxiliary_resolver(data, records, auxiliary_id, feature["object_id"], features)
        if not isinstance(auxiliary_details, dict):
            raise ValueError("Path-pattern auxiliary callback did not return bounded provenance")
        auxiliary_descriptors = auxiliary_details.get("descriptor_object_ids", [])
        if not isinstance(auxiliary_descriptors, list):
            raise ValueError("Path-pattern auxiliary callback descriptor list invalid")
    cursor += 33
    suppressed_count = struct.unpack_from("<I", chunk, cursor)[0]
    if not 0 <= suppressed_count < quantity or len(chunk) != cursor+4+4*suppressed_count:
        raise ValueError("Unsupported pattern suppression list")
    suppressed = list(struct.unpack_from("<"+"I"*suppressed_count, chunk, cursor+4))
    if len(set(suppressed)) != suppressed_count or any(v >= quantity for v in suppressed):
        raise ValueError("Invalid path-pattern suppressed element IDs")
    result = {"quantity": quantity, "distance_cm": distance, "distance_type": "Extent" if chunk[137] else "Spacing",
            "is_flipped": bool(chunk[61]), "orientation_along_path": bool(chunk[62]), "is_symmetric": bool(chunk[63]),
            "stored_start_fraction": native_start, "start_fraction": 1.-native_start if chunk[61] else native_start,
            "start_fraction_scope": "Observed single line/arc mapping; flipped prefix stores fraction from the opposite end",
            "path": path, "element_record_object_ids": element_ids, "suppressed_element_ids": suppressed,
            "stored_instance_ordinal_pairs": pairs, "ordinal_pair_scope": "Ordinal plus opaque integer; not interpreted as an ASM index",
            "control_record_object_id": control_id, "quantity_binding_object_id": quantity_id,
            "distance_binding_object_id": distance_id, "stored_reference_xyz": numbers(chunk, 36, 3),
            "uninterpreted_cached_scalar": numbers(chunk, 75, 1)[0],
            "auxiliary_selection_record_object_id": auxiliary_id, "auxiliary_descriptor_object_ids": auxiliary_descriptors}
    if element_resolver is not None:
        result["element_details"] = element_details
    if auxiliary_resolver is not None:
        result["auxiliary_selection_details"] = auxiliary_details
    return result


def decode_path_pattern(data, records, body, feature, features, *, path_resolver=None):
    if feature["class_guid"] != "B0B3D9E5-1C25-47BC-ABCD-E723F193DF1B" or body[:6] != bytes.fromhex("000100000000"):
        raise ValueError("Unsupported body path-pattern prefix/class")

    def primary(identity, guid):
        matches = [r for r in records if r.is_primary and r.object_id == identity and r.class_guid == guid]
        if len(matches) != 1:
            raise ValueError("Path-pattern typed reference missing or ambiguous")
        return matches[0]

    control_id, entity_set_id = reference(body, 6), reference(body, 17)
    result = parse_path_pattern_controls(data, records, control_id, feature, features, path_resolver=path_resolver)
    quantity, suppressed_count = result["quantity"], len(result["suppressed_element_ids"])
    collection = primary(entity_set_id, "8DB90DAE-3FF5-4E01-BACC-00AAA3EBB3EF")
    payload = data[collection.body:collection.end]
    input_count = struct.unpack_from("<I", payload, 6)[0]
    if payload[:6] != b"\0"*6 or not 1 <= input_count <= 1024 or len(payload) != 74+26*input_count:
        raise ValueError("Unsupported path-pattern input entity collection")
    inputs = []
    for i in range(input_count):
        start = 10+26*i
        descriptor_id, association_id = reference(payload, start), reference(payload, start+15)
        if struct.unpack_from("<I", payload, start+11)[0] != 1:
            raise ValueError("Unsupported pattern input association count")
        record = primary(descriptor_id, "9716F783-676D-42E0-93F9-EBF273E7C035")
        primary(association_id, "C46D3EEB-40E1-43FA-83DC-9CB204335417")
        definition = data[record.body:record.end]
        if reference(definition, len(definition)-11) != feature["object_id"]:
            raise ValueError("Pattern input descriptor owner disagrees with feature")
        inputs.append({"descriptor_object_id": descriptor_id, "association_record_object_id": association_id})
    if reference(payload, 10+26*input_count) != feature["object_id"] or reference(payload, len(payload)-11) != feature["object_id"]:
        raise ValueError("Pattern entity collection owner copies disagree")
    result_count = struct.unpack_from("<I", body, 32)[0]
    if body[28:32] != b"\0"*4 or result_count != (quantity-1-suppressed_count)*input_count:
        raise ValueError("Observed body-pattern result-reference count disagrees")
    results = [reference(body, 36+11*i) for i in range(result_count)]
    for identity in results:
        primary(identity, "D26351F0-5940-4D23-AA20-2C35475A6D9E")
    result.update(input_body_count=input_count, input_entity_collection_object_id=entity_set_id,
                  input_descriptors=inputs, result_record_object_ids=results,
                  generated_result_reference_count=result_count,
                  input_selection_status="Observed owned body descriptors; persistent input/result topology mapping remains partial",
                  compute_status="Feature/occurrence patterns and compute options unsupported; no transform/solid regeneration")
    return result
