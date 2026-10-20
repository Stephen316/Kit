"""Observed offset, plane replacement and delete-face controls/selections."""

import struct

from decode_selection import native_proxy_references, resolve_native_selection
from decode_sketch import reference


def decode_face_tool(data, records, body, feature, known):
    expected_guid = {"OffsetFaces": "D087EFE5-2D28-42e6-BB45-61739E7D0204",
                     "ReplaceFace": "8BD31492-18F4-45C9-8512-D720CCFC2450",
                     "DeleteFace": "29EF07D3-7BAF-4FA1-A28A-43A36279EA6D"}[feature["kind"]]
    if feature["class_guid"] != expected_guid:
        raise ValueError("Unrecognized face-edit feature class")

    def selection(identity, descriptor_guid):
        matches = [r for r in records if r.object_id == identity and r.is_primary
                   and r.class_guid == "2CA5A1CD-C99B-4C9B-91AF-57989148E841"]
        if len(matches) != 1:
            raise ValueError("Face-edit proxy missing or ambiguous")
        record = matches[0]
        chunk = data[record.body:record.end]
        if reference(chunk, len(chunk)-11) != feature["object_id"]:
            raise ValueError("Face-edit proxy owner disagrees with feature")
        descriptors, _ = native_proxy_references(data, record)
        for identity in descriptors:
            targets = [r for r in records if r.object_id == identity and r.is_primary
                       and r.class_guid == descriptor_guid]
            if len(targets) != 1:
                raise ValueError("Unsupported face-edit selection descriptor class")
            descriptor = data[targets[0].body:targets[0].end]
            if reference(descriptor, len(descriptor)-11) != feature["object_id"]:
                raise ValueError("Face-edit descriptor owner disagrees with feature")
        return descriptors

    topology_guid = "5662F619-2281-4AD9-93DC-1FCFDA1062E7"
    result = {"input_selection_status": "Observed descriptor lists and owners; persistent face-to-ASM topology mapping unresolved"}
    if feature["kind"] == "OffsetFaces":
        if body[:2] != b"\0\0" or struct.unpack_from("<I", body, 13)[0] != 1:
            raise ValueError("Unsupported offset-face selection groups")
        binding_id, selected_id = reference(body, 2), reference(body, 17)
        parameters = [p for p in feature["parameters"] if p["binding_object_id"] == binding_id and p["role"] == "distance"]
        if len(parameters) != 1:
            raise ValueError("Offset-face distance binding unresolved")
        descriptors = selection(selected_id, topology_guid)
        result.update(distance_cm=parameters[0]["raw_float64"], distance_binding_object_id=binding_id,
                      selection_record_object_id=selected_id, selection_descriptor_object_ids=descriptors,
                      selected_descriptor_count=len(descriptors))
    elif feature["kind"] == "ReplaceFace":
        if (body[:2] != b"\0\0" or body[2] not in (0, 1)
                or struct.unpack_from("<I", body, 3)[0] != 1
                or struct.unpack_from("<I", body, 18)[0] != 1):
            raise ValueError("Unsupported replacement-face selection groups")
        target_id, source_id = reference(body, 7), reference(body, 22)
        targets = selection(target_id, "5A1BF548-241F-46FD-9FB5-E4B05126EB9D")
        sources = selection(source_id, topology_guid)
        target = resolve_native_selection(data, records, target_id, known)
        if len(targets) != 1 or target is None or target["entity"]["kind"] != "ConstructionPlane":
            raise ValueError("Only observed replacement construction-plane targets supported")
        result.update(is_tangent_chain=bool(body[2]), source_selection_record_object_id=source_id,
                      source_descriptor_object_ids=sources, selected_descriptor_count=len(sources),
                      target_selection_record_object_id=target_id, target_descriptor_object_ids=targets,
                      replacement_target=target)
    else:
        if body[:14] != b"\0"*14 or struct.unpack_from("<I", body, 14)[0] != 1:
            raise ValueError("Unsupported delete-face prefix or selection groups")
        selected_id = reference(body, 18)
        descriptors = selection(selected_id, topology_guid)
        result.update(selection_record_object_id=selected_id, selection_descriptor_object_ids=descriptors,
                      selected_descriptor_count=len(descriptors),
                      mode_status="Observed delete-face feature; no general healing-mode field decoded")
    return result
