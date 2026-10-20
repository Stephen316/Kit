"""Observed circular pattern controls, element records and owned inputs."""

import math
import struct
import uuid

from decode_body_selections import decode_body_selections
from decode_parameters import read_string
from decode_selection import native_proxy_references, resolve_native_selection
from decode_sketch import reference


FEATURE = "11F1A5CE-2B57-4476-8480-6994621493C9"
CONTROL = "7493A99D-EDFC-4932-8B75-4120A8FA7875"
ELEMENT = "AD719C1A-11AF-4537-BB41-030A9091D36B"
COLLECTION = "8DB90DAE-3FF5-4E01-BACC-00AAA3EBB3EF"


def decode_circular_pattern(data, records, body, feature, known, features=None, body_selections=None):
    if feature["class_guid"] != FEATURE or body[:6] != bytes.fromhex("000100000000"):
        raise ValueError("Unsupported circular pattern feature prefix/class")
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: items[0] for identity, items in grouped.items() if len(items) == 1}

    def typed(identity, guid):
        matches = [record for record in records if record.is_primary and record.object_id == identity
                   and record.class_guid == guid]
        if len(matches) != 1:
            raise ValueError("Circular pattern typed reference missing or ambiguous")
        record = matches[0]
        return record, data[record.body:record.end]

    bindings = {parameter["binding_object_id"]: parameter for parameter in feature["parameters"]}

    def parameter(identity, role):
        item = bindings.get(identity)
        if item is None or item["role"] != role:
            raise ValueError("Circular pattern parameter binding disagrees with role: "+role)
        return item["raw_float64"]

    control_id, collection_id = reference(body, 6), reference(body, 17)
    _, payload = typed(control_id, CONTROL)
    if (len(payload) < 106 or payload[:2] != b"\0\0" or payload[2] not in (0, 1)
            or payload[25:37] != b"\0"*12 or payload[45:49] != b"\xff"*4
            or payload[49] not in (0, 1)):
        raise ValueError("Unsupported circular pattern control header")
    angle_id, axis_id = reference(payload, 3), reference(payload, 14)
    angle = parameter(angle_id, "TotalAngle")
    compute_option, entity_type = struct.unpack_from("<II", payload, 37)
    if compute_option not in (0, 1, 2) or entity_type not in (1, 2):
        raise ValueError("Only observed circular feature/body compute/entity modes are supported")
    pair_count = struct.unpack_from("<I", payload, 50)[0]
    if not 1 <= pair_count <= 1023 or 54+16*pair_count+4 > len(payload):
        raise ValueError("Unsupported circular pattern ordinal table count")
    pairs = [list(struct.unpack_from("<QQ", payload, 54+16*i)) for i in range(pair_count)]
    cursor = 54+16*pair_count
    quantity = struct.unpack_from("<I", payload, cursor)[0]
    if quantity != pair_count+1 or [pair[0] for pair in pairs] != list(range(2, quantity+1)):
        raise ValueError("Circular pattern stored ordinal/count sequence disagrees")
    element_ids = [reference(payload, cursor+4+11*i) for i in range(quantity)]
    element_ordinals = []
    for identity in element_ids:
        _, element = typed(identity, ELEMENT)
        if (len(element) != 17 or element[:2] != b"\0\0"
                or reference(element, 6) != control_id):
            raise ValueError("Circular pattern element ordinal/controller references disagree")
        element_ordinals.append(struct.unpack_from("<I", element, 2)[0])
    if sorted(element_ordinals) != list(range(1, quantity+1)):
        raise ValueError("Circular pattern element ordinals do not cover the declared quantity")
    cursor += 4+11*quantity
    quantity_id = reference(payload, cursor)
    cached_quantity = parameter(quantity_id, "countU")
    if not cached_quantity.is_integer() or int(cached_quantity) != quantity:
        raise ValueError("Circular pattern quantity binding disagrees with element count")
    if reference(payload, cursor+11) != feature["object_id"]:
        raise ValueError("Circular pattern controller owner mismatch")
    input_proxy_id = reference(payload, cursor+22)
    proxy, proxy_payload = typed(input_proxy_id, "2CA5A1CD-C99B-4C9B-91AF-57989148E841")
    if reference(proxy_payload, len(proxy_payload)-11) != feature["object_id"]:
        raise ValueError("Circular pattern input proxy owner mismatch")
    proxy_descriptors, _ = native_proxy_references(data, proxy)
    cursor += 33
    suppressed_count = struct.unpack_from("<I", payload, cursor)[0]
    if suppressed_count >= quantity or len(payload) != cursor+4+4*suppressed_count:
        raise ValueError("Unsupported circular pattern suppression list size")
    suppressed = list(struct.unpack_from("<"+"I"*suppressed_count, payload, cursor+4))
    if len(set(suppressed)) != suppressed_count or any(identity not in element_ordinals or identity == 1 for identity in suppressed):
        raise ValueError("Invalid or duplicate circular pattern suppression identifiers")
    if payload[2] and suppressed:
        raise ValueError("Symmetric circular suppression/API identifier mapping has not been observed")
    api_suppressed = [identity-1 for identity in suppressed]
    _, inputs = typed(collection_id, COLLECTION)
    count = struct.unpack_from("<I", inputs, 6)[0]
    if inputs[:6] != b"\0"*6 or not 1 <= count <= 1024 or len(inputs) != 74+26*count:
        raise ValueError("Unsupported circular pattern input collection")
    selected = []
    native_bodies = None
    source_features = {item["object_id"]: item for item in (features or [])}
    if entity_type == 2:
        decoded_bodies = body_selections or decode_body_selections(data, records)
        native_bodies = {item["object_id"]: item for item in decoded_bodies["body_descriptors"]}
    for index in range(count):
        cursor = 10+26*index
        descriptor_id, association_id = reference(inputs, cursor), reference(inputs, cursor+15)
        if struct.unpack_from("<I", inputs, cursor+11)[0] != 1:
            raise ValueError("Unsupported circular pattern input association count")
        descriptor = primary.get(descriptor_id)
        if descriptor is None or reference(data[descriptor.body:descriptor.end], descriptor.end-descriptor.body-11) != feature["object_id"]:
            raise ValueError("Circular pattern selected descriptor owner missing or disagrees")
        typed(association_id, "C46D3EEB-40E1-43FA-83DC-9CB204335417")
        item = {"descriptor_object_id": descriptor_id, "descriptor_class_guid": descriptor.class_guid,
                "association_record_object_id": association_id}
        if entity_type == 2:
            if descriptor.class_guid != "9716F783-676D-42E0-93F9-EBF273E7C035" or descriptor_id not in native_bodies:
                raise ValueError("Circular body input descriptor identity remains unresolved")
            item.update(native_body_object_id=native_bodies[descriptor_id]["native_body_object_id"],
                        body_anchor_object_id=native_bodies[descriptor_id]["body_anchor_object_id"])
        else:
            definition = data[descriptor.body:descriptor.end]
            if (descriptor.class_guid != "5A1BF548-241F-46FD-9FB5-E4B05126EB9D" or len(definition) != 263
                    or definition[:2] != b"\0\0" or struct.unpack_from("<I", definition, 13)[0] != 1):
                raise ValueError("Unsupported circular feature-input descriptor")
            namespace, offset = read_string(definition, 17)
            identity_text, offset = read_string(definition, offset)
            if len(namespace) != 36 or len(identity_text) != 36:
                raise ValueError("Unsupported feature-input UUID fields")
            uuid.UUID(namespace)
            uuid.UUID(identity_text)
            leaf_id = reference(definition, 2)
            _, leaf = typed(leaf_id, "90055C05-546C-4EE7-B3C9-3DD922AD0C9C")
            if len(leaf) != 10 or leaf[:2] != b"\0\0":
                raise ValueError("Unsupported circular feature-input identity leaf")
            source_id = struct.unpack_from("<Q", leaf, 2)[0]
            source = primary.get(source_id)
            if source is None or source_id == feature["object_id"]:
                raise ValueError("Circular input source feature is missing or self-referential")
            named = source_features.get(source_id)
            if named is not None and named["class_guid"] != source.class_guid:
                raise ValueError("Circular input feature class disagrees with named source feature")
            if named is None and source.class_guid != "DD405BC2-D673-44F0-8833-5CB2A1C186C7":
                raise ValueError("Unobserved circular pattern input feature class")
            item.update(source_feature_object_id=source_id, source_feature_class_guid=source.class_guid,
                        source_feature_kind=named["kind"] if named else "Extrude",
                        source_feature_name=named.get("name") if named else None,
                        terminal_object_id=leaf_id,
                        association="Owned typed descriptor and bounded leaf contain an explicit source feature identity")
        selected.append(item)
    if (reference(inputs, 10+26*count) != feature["object_id"]
            or reference(inputs, len(inputs)-11) != feature["object_id"]
            or proxy_descriptors != [item["descriptor_object_id"] for item in selected]):
        raise ValueError("Circular pattern input collection/proxy descriptor lists or owners disagree")
    result_count = struct.unpack_from("<I", body, 32)[0]
    if body[28:32] != b"\0"*4 or result_count > 100000:
        raise ValueError("Unsupported circular pattern result list header")
    results = [reference(body, 36+11*i) for i in range(result_count)]
    for identity in results:
        _, result = typed(identity, "D26351F0-5940-4D23-AA20-2C35475A6D9E")
        if len(result) != 102 or reference(result, 91) != feature["object_id"]:
            raise ValueError("Circular pattern result anchor owner disagrees with feature")
    if entity_type == 2 and result_count != (quantity-1-suppressed_count)*count:
        raise ValueError("Circular body pattern result reference count disagrees with active copies")
    axis = resolve_native_selection(data, records, axis_id, known)
    return {"quantity": quantity, "total_angle_radians": angle,
            "total_angle_degrees": math.degrees(angle), "is_symmetric": bool(payload[2]),
            "axis_selection_record_object_id": axis_id, "axis": axis,
            "control_record_object_id": control_id, "quantity_binding_object_id": quantity_id,
            "angle_binding_object_id": angle_id,
            "pattern_entity_type": {1: "Features", 2: "Bodies"}[entity_type],
            "pattern_entity_type_code": entity_type,
            "pattern_compute_option": {0: "Optimized", 1: "Identical", 2: "Adjust"}[compute_option],
            "pattern_compute_option_code": compute_option,
            "compute_applies_to_feature_inputs": entity_type == 1,
            "stored_angle_mode_flag": payload[49],
            "stored_instance_ordinal_pairs": pairs,
            "ordinal_pair_scope": "Stored one-based ordinals and opaque integers; no ASM record index or transform inferred",
            "element_record_object_ids": element_ids, "stored_element_ordinals": element_ordinals,
            "stored_suppressed_element_ordinals": suppressed,
            "suppressed_element_ids": api_suppressed,
            "suppression_status": "Observed non-symmetric native ordinal minus one matches API element ID; symmetric suppression remains unsupported",
            "input_selection_record_object_id": input_proxy_id,
            "input_entity_collection_object_id": collection_id, "input_count": count,
            "input_body_count": count if entity_type == 2 else None,
            "input_feature_count": count if entity_type == 1 else None,
            "native_input_body_object_ids": [item["native_body_object_id"] for item in selected] if entity_type == 2 else [],
            "source_feature_object_ids": [item["source_feature_object_id"] for item in selected] if entity_type == 1 else [],
            "input_descriptors": selected,
            "result_record_object_ids": results, "generated_result_reference_count": result_count,
            "input_selection_status": "Explicit collection and owned input proxy lists agree; observed native body or source feature identities recovered",
            "compute_status": "Observed feature-input compute options decoded; stored option does not change body-pattern compute semantics",
            "geometry_status": "Native controls and references only; no pattern geometry regeneration"}
