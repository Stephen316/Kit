"""Observed Thicken controls and owned face/body input references."""

import struct
import uuid

from decode_body_selections import decode_body_selections
from decode_brep_recipes import decode_recipe
from decode_parameters import read_string
from decode_selection import native_proxy_references
from decode_sketch import attributes, reference


def decode_thicken(data, records, body, feature):
    if (feature["class_guid"] != "BCE0AD0E-377B-4A37-9F4F-112D0DAFEAA1"
            or body[0] != 0 or body[1] not in (0, 1)):
        raise ValueError("Unsupported Thicken class/prefix")
    props, cursor = attributes(body, 2) if body[1] else ({}, 2)
    if props:
        raise ValueError("Unobserved Thicken attributes")
    mode = body[cursor]
    operation = struct.unpack_from("<I", body, cursor+1)[0]
    if mode not in (0, 1) or operation not in (1, 2, 3, 4):
        raise ValueError("Unsupported Thicken mode/operation")

    def counted(payload, offset):
        count = struct.unpack_from("<I", payload, offset)[0]
        if count > 1024 or offset+4+11*count > len(payload):
            raise ValueError("Unsupported Thicken reference count")
        identities = [reference(payload, offset+4+11*i) for i in range(count)]
        if len(set(identities)) != len(identities):
            raise ValueError("Duplicate Thicken list references")
        return identities, offset+4+11*count

    proxy_ids, cursor = counted(body, cursor+5)
    if not proxy_ids or body[cursor] not in (0, 1) or body[cursor+1] not in (0, 1):
        raise ValueError("Unsupported Thicken input/side flags")
    symmetric, chain = bool(body[cursor]), bool(body[cursor+1])
    binding_id = reference(body, cursor+2)
    parameters = [p for p in feature["parameters"] if p["role"] == "Thickness" and p["binding_object_id"] == binding_id]
    if len(parameters) != 1 or parameters[0]["raw_float64"] == 0:
        raise ValueError("Thicken thickness binding unresolved or zero")
    thickness = parameters[0]["raw_float64"]
    cursor += 13
    if body[cursor:cursor+4] != b"\0"*4:
        raise ValueError("Unsupported Thicken output list prefix")
    result_ids, _ = counted(body, cursor+4)

    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary_records = {identity: values[0] for identity, values in grouped.items() if len(values) == 1}

    def typed(identity, guid):
        record = primary_records.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError("Thicken typed reference unresolved: "+guid)
        return record, data[record.body:record.end]

    bodies = decode_body_selections(data, records)
    anchors = {a["object_id"]: a for a in bodies["body_anchors"]}
    body_descriptors = {d["object_id"]: d for d in bodies["body_descriptors"]}
    inputs = []
    for identity in proxy_ids:
        proxy, payload = typed(identity, "2CA5A1CD-C99B-4C9B-91AF-57989148E841")
        if reference(payload, len(payload)-11) != feature["object_id"]:
            raise ValueError("Thicken input proxy owner disagrees")
        descriptor_ids, selection_props = native_proxy_references(data, proxy)
        selected = []
        for descriptor_id in descriptor_ids:
            record = primary_records.get(descriptor_id)
            if record is None:
                raise ValueError("Thicken descriptor missing or ambiguous")
            descriptor = data[record.body:record.end]
            if reference(descriptor, len(descriptor)-11) != feature["object_id"]:
                raise ValueError("Thicken input descriptor owner disagrees")
            if record.class_guid == "9716F783-676D-42E0-93F9-EBF273E7C035":
                resolved = body_descriptors.get(descriptor_id)
                if resolved is None or resolved["owner_object_id"] != feature["object_id"]:
                    raise ValueError("Thicken whole-body descriptor unresolved")
                selected.append({"object_id": descriptor_id, "kind": "Body", "body_selection": resolved})
                continue
            if record.class_guid != "5662F619-2281-4AD9-93DC-1FCFDA1062E7" or descriptor[:4] != b"\0"*4:
                raise ValueError("Unsupported Thicken face/body descriptor")
            recipe_id = reference(descriptor, 4)
            if struct.unpack_from("<I", descriptor, 15)[0] != 1:
                raise ValueError("Unsupported Thicken face descriptor namespace count")
            namespace, pos = read_string(descriptor, 19)
            entity_uuid, pos = read_string(descriptor, pos)
            if len(namespace) != 36 or len(entity_uuid) != 36:
                raise ValueError("Unsupported Thicken face descriptor UUID length")
            uuid.UUID(namespace)
            uuid.UUID(entity_uuid)
            if struct.unpack_from("<Q", descriptor, pos)[0] != 2:
                raise ValueError("Unsupported Thicken face association prefix")
            context_ids, pos = counted(descriptor, pos+8)
            if len(context_ids) > 1:
                raise ValueError("Unsupported Thicken face context count")
            for context_id in context_ids:
                typed(context_id, "C46D3EEB-40E1-43FA-83DC-9CB204335417")
            anchor_ids, pos = counted(descriptor, pos)
            if len(anchor_ids) != 1 or len(descriptor)-pos != 67:
                raise ValueError("Unsupported Thicken face body-anchor/trailer layout")
            anchor_id = anchor_ids[0]
            if anchor_id not in anchors:
                raise ValueError("Thicken face native body anchor unresolved")
            recipe_record, _ = typed(recipe_id, "7ACC2A03-0261-4879-A14A-A93D661A5BDC")
            recipe = decode_recipe(data, recipe_record, primary_records)
            if recipe["payload_kind"] not in ("face_recipe_data", "bounded_face_recipe_data"):
                raise ValueError("Unsupported Thicken face recipe kind")
            selected.append({"object_id": descriptor_id, "kind": "Face", "recipe": recipe,
                             "body_anchor_object_id": anchor_id,
                             "native_body_object_id": anchors[anchor_id]["native_body_object_id"],
                             "source_owner_object_id": anchors[anchor_id]["source_owner_object_id"],
                             "namespace_text": namespace, "entity_guid_text": entity_uuid,
                             "context_record_object_ids": context_ids,
                             "context_scope": "Explicit context record identities retained; occurrence transforms not inferred",
                             "face_identity_scope": "Owning native body and persistent face recipe retained; exact ASM face unresolved"})
        inputs.append({"selection_record_object_id": identity, "descriptor_count": len(selected),
                       "attributes": selection_props, "descriptors": selected})
    results = []
    for identity in result_ids:
        anchor = anchors.get(identity)
        if anchor is None or anchor["source_owner_object_id"] != feature["object_id"]:
            raise ValueError("Thicken resulting native-body anchor owner disagrees")
        results.append(anchor)
    return {"thickness_cm": thickness, "thickness_binding_object_id": binding_id,
            "is_symmetric": symmetric, "is_chain_selection": chain,
            "thicken_type": {0: "Sharp", 1: "Rounded"}[mode], "stored_thicken_type_code": mode,
            "operation": {1: "Join", 2: "Cut", 3: "Intersect", 4: "NewBody"}[operation],
            "stored_operation_code": operation, "input_selections": inputs,
            "result_body_anchors": results,
            "thickness_scope": "Signed stored parameter retained; exact side offsets/regeneration are not inferred",
            "input_count_scope": "Only one API input entity is sampled; counted native selection lists are retained",
            "participant_scope": "Thickened sheet inputs resolved; Boolean participant body roles are not classified here",
            "input_selection_status": "Owned typed descriptors and native-body anchors; exact persistent face-to-ASM mapping unresolved",
            "geometry_status": "Observed controls and native input/result body identities decoded; thickened geometry is not regenerated"}
