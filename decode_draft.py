"""Observed fixed-plane Draft modes, flags, bindings and owned input references."""

import struct
import uuid

from decode_body_selections import decode_body_selections
from decode_brep_recipes import decode_recipe
from decode_parameters import read_string
from decode_selection import native_proxy_references, resolve_native_selection
from decode_sketch import numbers, reference


def decode_draft(data, records, body, feature, known=None):
    if (feature["class_guid"] != "F4163A07-9E71-4C46-BD92-ACE5B5B40BED"
            or body[:2] != b"\0\0" or struct.unpack_from("<II", body, 2) != (3, 1)):
        raise ValueError("Unsupported observed fixed-plane Draft class/header")
    flipped, chain = body[10], body[11]
    mode = struct.unpack_from("<I", body, 12)[0]
    if flipped not in (0, 1) or chain not in (0, 1) or mode not in (1, 2, 3) or body[54:56] != b"\0\0" or body[67] != 0:
        raise ValueError("Unsupported Draft flags/mode/input prefix")
    bindings = [reference(body, 16), reference(body, 27)]
    angles = []
    for binding, role in zip(bindings, ("Angle1", "Angle2")):
        parameters = [p for p in feature["parameters"] if p["binding_object_id"] == binding and p["role"] == role]
        if len(parameters) != 1:
            raise ValueError("Draft explicit angle binding unresolved: "+role)
        angles.append(parameters[0]["raw_float64"])

    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: values[0] for identity, values in grouped.items() if len(values) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError("Draft typed reference unresolved: "+guid)
        return record, data[record.body:record.end]

    def counted(payload, offset):
        count = struct.unpack_from("<I", payload, offset)[0]
        if count > 1024 or offset+4+11*count > len(payload):
            raise ValueError("Unsupported Draft reference count")
        identities = [reference(payload, offset+4+11*i) for i in range(count)]
        if len(set(identities)) != len(identities):
            raise ValueError("Duplicate Draft list references")
        return identities, offset+4+11*count

    anchors = {a["object_id"]: a for a in decode_body_selections(data, records)["body_anchors"]}

    def face_descriptor(identity):
        record, descriptor = typed(identity, "5662F619-2281-4AD9-93DC-1FCFDA1062E7")
        if descriptor[:4] != b"\0"*4 or reference(descriptor, len(descriptor)-11) != feature["object_id"]:
            raise ValueError("Unsupported Draft face descriptor prefix/owner")
        recipe_id = reference(descriptor, 4)
        if struct.unpack_from("<I", descriptor, 15)[0] != 1:
            raise ValueError("Unsupported Draft face namespace count")
        namespace, cursor = read_string(descriptor, 19)
        entity_uuid, cursor = read_string(descriptor, cursor)
        if len(namespace) != 36 or len(entity_uuid) != 36:
            raise ValueError("Unsupported Draft face UUID lengths")
        uuid.UUID(namespace)
        uuid.UUID(entity_uuid)
        if struct.unpack_from("<Q", descriptor, cursor)[0] != 2:
            raise ValueError("Unsupported Draft face association header")
        context_ids, cursor = counted(descriptor, cursor+8)
        if len(context_ids) > 1:
            raise ValueError("Unsupported Draft face context count")
        for context_id in context_ids:
            typed(context_id, "C46D3EEB-40E1-43FA-83DC-9CB204335417")
        anchor_ids, cursor = counted(descriptor, cursor)
        if len(anchor_ids) != 1 or len(descriptor)-cursor != 67 or anchor_ids[0] not in anchors:
            raise ValueError("Draft face native body anchor/trailer unresolved")
        recipe_record, _ = typed(recipe_id, "7ACC2A03-0261-4879-A14A-A93D661A5BDC")
        recipe = decode_recipe(data, recipe_record, primary)
        if recipe["payload_kind"] not in ("face_recipe_data", "bounded_face_recipe_data"):
            raise ValueError("Unsupported Draft face recipe kind")
        anchor = anchors[anchor_ids[0]]
        return {"object_id": identity, "kind": "Face", "recipe": recipe,
                "body_anchor_object_id": anchor_ids[0], "native_body_object_id": anchor["native_body_object_id"],
                "source_owner_object_id": anchor["source_owner_object_id"],
                "namespace_text": namespace, "entity_guid_text": entity_uuid,
                "context_record_object_ids": context_ids,
                "selection_scope": "Explicit native historical body and persistent face recipe; exact ASM face unresolved",
                "context_scope": "Context references retained; occurrence transforms are not inferred"}

    def selection(identity, allow_native=False):
        proxy, payload = typed(identity, "2CA5A1CD-C99B-4C9B-91AF-57989148E841")
        if reference(payload, len(payload)-11) != feature["object_id"]:
            raise ValueError("Draft input proxy owner disagrees")
        descriptor_ids, props = native_proxy_references(data, proxy)
        if not descriptor_ids:
            raise ValueError("Empty Draft input selection")
        descriptors = []
        native_selection = None
        for descriptor_id in descriptor_ids:
            record = primary.get(descriptor_id)
            if allow_native and record and record.class_guid == "5A1BF548-241F-46FD-9FB5-E4B05126EB9D":
                payload = data[record.body:record.end]
                if len(descriptor_ids) != 1 or reference(payload, len(payload)-11) != feature["object_id"]:
                    raise ValueError("Unsupported Draft native-plane descriptor count/owner")
                native_selection = resolve_native_selection(data, records, identity, known or {})
                if native_selection is not None and native_selection["entity"]["kind"] != "ConstructionPlane":
                    raise ValueError("Draft pull geometry resolves outside observed construction-plane layout")
                descriptors.append({"object_id": descriptor_id, "kind": "NativeEntityDescriptor"})
            else:
                descriptors.append(face_descriptor(descriptor_id))
        return {"selection_record_object_id": identity, "descriptor_count": len(descriptors),
                "attributes": props, "descriptors": descriptors, "native_selection": native_selection}

    plane_id = reference(body, 56)
    plane = selection(plane_id, True)
    if plane["native_selection"] is not None:
        plane["geometry_status"] = "Explicit reference to independently decoded native construction-plane geometry"
    else:
        plane["geometry_status"] = "Owned descriptor retained; exact pull-plane geometry is unresolved"
    input_ids, _ = counted(body, 68)
    if len(input_ids) != 1:
        raise ValueError("Only observed single Draft input selection group supported")
    inputs = [selection(identity) for identity in input_ids]
    return {"draft_type": "FixedPlane", "stored_header_fields": [3, 1],
            "header_scope": "Observed fixed-plane header combination; general field meanings not established",
            "angle_mode": "TwoAngles" if mode == 2 else "SingleAngle", "stored_angle_mode_code": mode,
            "is_symmetric": mode == 3, "is_direction_flipped": bool(flipped), "is_tangent_chain": bool(chain),
            "angle_one_radians": angles[0], "angle_two_radians": angles[1] if mode == 2 else None,
            "stored_angle_one_radians": angles[0], "stored_angle_two_radians": angles[1],
            "angle_binding_object_ids": {"Angle1": bindings[0], "Angle2": bindings[1]},
            "angle_activity_scope": "Single-angle mode retains an inactive Angle2 binding; symmetric mode uses Angle1",
            "stored_reference_pair": numbers(body, 38, 2),
            "reference_pair_scope": "Two stored finite doubles retained; their coordinate system/meaning is unresolved",
            "pull_geometry": plane, "input_selections": inputs,
            "input_descriptor_count": sum(s["descriptor_count"] for s in inputs),
            "geometry_status": "Observed Draft controls and owned selections decoded; drafted geometry is not regenerated",
            "unsupported_scope": "Parting-line draft modes and exact persistent face-to-ASM mapping remain unsupported"}
