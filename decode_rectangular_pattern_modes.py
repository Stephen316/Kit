"""Observed rectangular body/feature inputs, compute modes and direction links."""

import math
import struct
import uuid

from decode_body_selections import decode_body_selections
from decode_extrude import optional_reference
from decode_parameters import read_string
from decode_placement import transform_vector
from decode_selection import native_proxy_references, resolve_native_selection
from decode_sketch import attributes, numbers, reference, same


FEATURE = "AE12AD3F-BB81-4B59-9D34-A599E58E4BF6"
CONTROL = "EA0E146E-3126-42F0-9280-0DE74AB17D78"


def stored_grid_key(u, v):
    """Observed one-based Cantor encoding of nonnegative grid coordinates."""
    return 1+(u+v)*(u+v+1)//2+u


def decode_rectangular_pattern_modes(data, records, body, feature, known, features=None, body_selections=None):
    primary_groups = {}
    for record in records:
        if record.is_primary:
            primary_groups.setdefault(record.object_id, []).append(record)
    primary = {identity: values[0] for identity, values in primary_groups.items() if len(values) == 1}
    if feature["class_guid"] != FEATURE or body[0] != 0 or body[1] not in (0, 1):
        raise ValueError("Unsupported rectangular pattern feature class/header")
    props, cursor = attributes(body, 2) if body[1] else ({}, 2)
    if props:
        raise ValueError("Unobserved rectangular pattern feature attributes")
    control_id, collection_id = reference(body, cursor), reference(body, cursor+11)
    feature_header_end = cursor+22

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError("Rectangular pattern typed reference missing, ambiguous or wrong class")
        return record, data[record.body:record.end]

    bindings = {item["binding_object_id"]: item for item in feature["parameters"]}

    def parameter(identity, role, integer=False):
        item = bindings.get(identity)
        if item is None or item["role"] != role:
            raise ValueError("Rectangular pattern binding disagrees with role: "+role)
        value = item["raw_float64"]
        if integer:
            if not value.is_integer() or not 1 <= value <= 1024:
                raise ValueError("Unsupported rectangular pattern quantity")
            value = int(value)
        return value

    def unit(vector):
        length = math.sqrt(sum(value*value for value in vector))
        if not math.isfinite(length) or length <= 1e-12:
            raise ValueError("Degenerate rectangular pattern direction")
        return [value/length for value in vector]

    _, payload = typed(control_id, CONTROL)
    if (len(payload) < 180 or payload[:5] != bytes.fromhex("0102000000")
            or payload[16:20] != b"\0"*4 or payload[31:44] != b"\0"*9+b"\xff"*4
            or any(value not in (0, 1) for value in payload[90:92])):
        raise ValueError("Unsupported rectangular pattern controller header")
    quantity_one_id, quantity_two_id = reference(payload, 5), reference(payload, 20)
    quantity_one, quantity_two = parameter(quantity_one_id, "countU", True), parameter(quantity_two_id, "CountV", True)
    total = quantity_one*quantity_two
    if not 2 <= total <= 1024 or reference(payload, 92) != quantity_two_id:
        raise ValueError("Rectangular pattern product/repeated quantity disagrees")
    one_id = reference(payload, 103)
    two_id, cursor = optional_reference(payload, 114)
    if payload[cursor:cursor+12] != b"\0"*12 or payload[cursor+20:cursor+24] != b"\xff"*4:
        raise ValueError("Unsupported rectangular pattern mode prefix")
    compute, entity_type = struct.unpack_from("<II", payload, cursor+12)
    if compute not in (0, 1, 2) or entity_type not in (1, 2) or payload[cursor+24] not in (0, 1):
        raise ValueError("Unobserved rectangular compute/entity/distance mode")
    extent = bool(payload[cursor+24])
    cursor += 25
    pair_count = struct.unpack_from("<I", payload, cursor)[0]
    if pair_count != total-1:
        raise ValueError("Rectangular pattern instance-pair count disagrees with quantities")
    pairs = [list(struct.unpack_from("<QQ", payload, cursor+4+16*i)) for i in range(pair_count)]
    grid_keys = [stored_grid_key(u, v) for v in range(quantity_two) for u in range(quantity_one)]
    if [pair[0] for pair in pairs] != sorted(set(grid_keys)-{1}):
        raise ValueError("Unobserved rectangular native grid-key sequence")
    cursor += 4+16*pair_count
    if struct.unpack_from("<I", payload, cursor)[0] != total:
        raise ValueError("Rectangular element-reference count disagrees")
    element_ids = [reference(payload, cursor+4+11*i) for i in range(total)]
    keys = []
    for identity in element_ids:
        _, element = typed(identity, "AD719C1A-11AF-4537-BB41-030A9091D36B")
        if len(element) != 17 or element[:2] != b"\0\0" or reference(element, 6) != control_id:
            raise ValueError("Rectangular element/controller reference disagrees")
        keys.append(struct.unpack_from("<I", element, 2)[0])
    if sorted(keys) != sorted(grid_keys):
        raise ValueError("Rectangular native element keys do not cover the declared grid")
    cursor += 4+11*total
    if reference(payload, cursor) != quantity_one_id or reference(payload, cursor+11) != feature["object_id"]:
        raise ValueError("Rectangular repeated quantity/controller owner disagrees")
    input_proxy_id = reference(payload, cursor+22)
    proxy, proxy_payload = typed(input_proxy_id, "2CA5A1CD-C99B-4C9B-91AF-57989148E841")
    if reference(proxy_payload, len(proxy_payload)-11) != feature["object_id"]:
        raise ValueError("Rectangular input proxy owner disagrees")
    proxy_descriptors, _ = native_proxy_references(data, proxy)
    cursor += 33
    suppressed_count = struct.unpack_from("<I", payload, cursor)[0]
    if suppressed_count >= total or len(payload) != cursor+4+4*suppressed_count:
        raise ValueError("Unsupported rectangular suppression table size")
    suppressed = list(struct.unpack_from("<"+"I"*suppressed_count, payload, cursor+4))
    if len(set(suppressed)) != suppressed_count or not set(suppressed).issubset(keys):
        raise ValueError("Rectangular stored suppression keys disagree with native element membership")

    def direction(identity):
        if identity is None:
            return None, None
        _, selection = typed(identity, "F2A7590D-6654-4674-B393-A2AEF4FEC48A")
        if (len(selection) != 202 or selection[:6] != bytes.fromhex("000008000000")
                or reference(selection, 191) != feature["object_id"]):
            raise ValueError("Unsupported rectangular direction selector/owner")
        if struct.unpack_from("<I", selection, 99)[0] != 1:
            raise ValueError("Unsupported rectangular direction descriptor count")
        descriptor_id = reference(selection, 103)
        _, descriptor = typed(descriptor_id, "5A1BF548-241F-46FD-9FB5-E4B05126EB9D")
        if (len(descriptor) != 263 or descriptor[:2] != b"\0\0"
                or struct.unpack_from("<I", descriptor, 13)[0] != 1
                or reference(descriptor, 252) != feature["object_id"]):
            raise ValueError("Rectangular direction descriptor class/count/owner mismatch")
        resolved = resolve_native_selection(data, records, identity, known)
        if resolved is not None and resolved["entity"]["kind"] == "ConstructionAxis":
            vector = unit(resolved["entity"]["direction"])
            if not same(vector, unit(numbers(selection, 30, 3))):
                raise ValueError("Axis and cached rectangular direction disagree")
            return vector, resolved
        leaf_id = reference(descriptor, 2)
        _, leaf = typed(leaf_id, "E2CEFD18-D755-4E09-8E7F-953A2F6D43F8")
        if len(leaf) != 26 or leaf[:10] != b"\0"*10:
            raise ValueError("Unsupported rectangular sketch-line identity leaf")
        sketch_id, tag = struct.unpack_from("<QQ", leaf, 10)
        candidates = [(sketch, curve) for sketch in (features or []) if sketch["kind"] == "Sketch"
                      and sketch["sketch_object_id"] == sketch_id for curve in sketch.get("geometry", [])
                      if curve.get("entity_tag") == tag and curve["kind"] == "Line"]
        if len(candidates) != 1:
            raise ValueError("Rectangular pattern sketch-line source missing or ambiguous")
        sketch, curve = candidates[0]
        vector = [b-a for a,b in zip(curve["start_cm"], curve["end_cm"])]
        if "placement" not in sketch:
            raise ValueError("Sketch-line pattern direction placement unresolved")
        vector = unit(transform_vector(sketch["placement"]["sketch_to_component_matrix"], vector))
        if not same(vector, unit(numbers(selection, 30, 3))):
            raise ValueError("Sketch-line and cached rectangular direction disagree")
        return vector, {"kind": "SketchLine", "selection_object_id": identity,
                        "descriptor_object_id": descriptor_id, "terminal_object_id": leaf_id,
                        "sketch_object_id": sketch_id, "curve_object_id": curve["object_id"],
                        "curve_entity_tag": tag, "sketch_name": sketch.get("name"),
                        "association": "Explicit descriptor/leaf sketch identity and curve tag, with matching cached direction"}

    one, one_selection = direction(one_id)
    two, two_selection = direction(two_id)
    stored_two = numbers(payload, 44, 3)
    if two is not None and not same(two, stored_two):
        raise ValueError("Rectangular stored second direction disagrees with explicit selector")
    if two_id is None and not same(stored_two, [0, 0, 0]):
        raise ValueError("Unexpected cached vector for an inactive second direction")
    _, collection = typed(collection_id, "8DB90DAE-3FF5-4E01-BACC-00AAA3EBB3EF")
    count = struct.unpack_from("<I", collection, 6)[0]
    if collection[:6] != b"\0"*6 or not 1 <= count <= 1024 or len(collection) != 74+26*count:
        raise ValueError("Unsupported rectangular input entity collection")
    body_map = {item["object_id"]: item for item in (body_selections or decode_body_selections(data, records))["body_descriptors"]} if entity_type == 2 else {}
    named = {item["object_id"]: item for item in (features or [])}
    inputs = []
    for index in range(count):
        offset = 10+26*index
        descriptor_id, association_id = reference(collection, offset), reference(collection, offset+15)
        if struct.unpack_from("<I", collection, offset+11)[0] != 1:
            raise ValueError("Unsupported rectangular input association count")
        typed(association_id, "C46D3EEB-40E1-43FA-83DC-9CB204335417")
        descriptor = primary.get(descriptor_id)
        if descriptor is None:
            raise ValueError("Rectangular input descriptor missing")
        definition = data[descriptor.body:descriptor.end]
        if reference(definition, len(definition)-11) != feature["object_id"]:
            raise ValueError("Rectangular input descriptor owner disagrees")
        item = {"descriptor_object_id": descriptor_id, "association_record_object_id": association_id}
        if entity_type == 2:
            if descriptor.class_guid != "9716F783-676D-42E0-93F9-EBF273E7C035" or descriptor_id not in body_map:
                raise ValueError("Rectangular body input identity unresolved")
            item.update(native_body_object_id=body_map[descriptor_id]["native_body_object_id"],
                        body_anchor_object_id=body_map[descriptor_id]["body_anchor_object_id"])
        else:
            if (descriptor.class_guid != "5A1BF548-241F-46FD-9FB5-E4B05126EB9D" or len(definition) != 263
                    or definition[:2] != b"\0\0" or struct.unpack_from("<I", definition, 13)[0] != 1):
                raise ValueError("Unsupported rectangular feature-input descriptor")
            namespace, pos = read_string(definition, 17)
            identity_text, pos = read_string(definition, pos)
            if len(namespace) != 36 or len(identity_text) != 36:
                raise ValueError("Unsupported rectangular feature-input UUID field")
            uuid.UUID(namespace)
            uuid.UUID(identity_text)
            leaf_id = reference(definition, 2)
            _, leaf = typed(leaf_id, "90055C05-546C-4EE7-B3C9-3DD922AD0C9C")
            if len(leaf) != 10 or leaf[:2] != b"\0\0":
                raise ValueError("Unsupported rectangular feature-input identity leaf")
            source_id = struct.unpack_from("<Q", leaf, 2)[0]
            source = named.get(source_id)
            if source is None or source_id == feature["object_id"] or primary.get(source_id) is None or primary[source_id].class_guid != source["class_guid"]:
                raise ValueError("Rectangular input source feature identity unresolved")
            item.update(source_feature_object_id=source_id, source_feature_kind=source["kind"],
                        source_feature_name=source.get("name"), terminal_object_id=leaf_id)
        inputs.append(item)
    if (reference(collection, 10+26*count) != feature["object_id"]
            or reference(collection, len(collection)-11) != feature["object_id"]
            or proxy_descriptors != [item["descriptor_object_id"] for item in inputs]):
        raise ValueError("Rectangular input collection/proxy descriptor copies or owners disagree")
    if body[feature_header_end:feature_header_end+4] != b"\0"*4:
        raise ValueError("Unsupported rectangular result-reference prefix")
    result_count = struct.unpack_from("<I", body, feature_header_end+4)[0]
    if result_count > 100000:
        raise ValueError("Unsupported rectangular result-reference count")
    results = [reference(body, feature_header_end+8+11*i) for i in range(result_count)]
    for identity in results:
        _, result = typed(identity, "D26351F0-5940-4D23-AA20-2C35475A6D9E")
        if len(result) != 102 or reference(result, 91) != feature["object_id"]:
            raise ValueError("Rectangular result anchor owner disagrees")
    if entity_type == 2 and not suppressed and result_count != (total-1)*count:
        raise ValueError("Rectangular body pattern result count disagrees with observed unsuppressed copies")
    return {"quantity_one": quantity_one, "quantity_two": quantity_two,
            "distance_one_cm": parameter(reference(payload, 68), "uSpaceDistance"),
            "distance_two_cm": parameter(reference(payload, 79), "vSpaceDistance"),
            "distance_type": "Extent" if extent else "Spacing", "stored_extent_flag": int(extent),
            "symmetric_one": bool(payload[90]), "symmetric_two": bool(payload[91]),
            "direction_one": one, "direction_two": two,
            "direction_one_selection": one_selection, "direction_two_selection": two_selection,
            "direction_one_selection_record_object_id": one_id, "direction_two_selection_record_object_id": two_id,
            "stored_direction_two_vector": stored_two,
            "direction_scope": "Observed explicit native axes/sketch-line vectors; inactive second/API default and occurrence contexts unresolved",
            "control_record_object_id": control_id,
            "pattern_entity_type": "Bodies" if entity_type == 2 else "Features", "pattern_entity_type_code": entity_type,
            "pattern_compute_option": {0: "Optimized", 1: "Identical", 2: "Adjust"}[compute], "pattern_compute_option_code": compute,
            "compute_applies_to_feature_inputs": entity_type == 1,
            "input_entity_collection_object_id": collection_id, "input_selection_record_object_id": input_proxy_id,
            "input_count": count, "input_body_count": count if entity_type == 2 else None,
            "input_descriptors": inputs,
            "native_input_body_object_ids": [item["native_body_object_id"] for item in inputs] if entity_type == 2 else [],
            "source_feature_object_ids": [item["source_feature_object_id"] for item in inputs] if entity_type == 1 else [],
            "stored_instance_key_pairs": pairs, "element_record_object_ids": element_ids,
            "stored_element_keys": keys, "stored_suppressed_element_keys": suppressed,
            "suppressed_element_ids": [] if not suppressed else None,
            "suppression_status": "Empty suppression lists observed; nonempty native-key/API-ID mapping remains unverified",
            "grid_key_scope": "Native key sets match observed one-based Cantor pairing; no semantic API ID, symmetric order, or transform mapping asserted",
            "result_record_object_ids": results, "generated_result_reference_count": result_count,
            "input_selection_status": "Owned input proxy/collection copies agree; explicit native body or source feature identities recovered",
            "geometry_status": "Controls, references and cached directions only; no pattern geometry regeneration"}
