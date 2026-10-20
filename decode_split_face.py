"""Observed SplitFace controls, owned tools, target recipes and projection axis."""

import struct
import uuid

from decode_extrude import optional_reference
from decode_face_selections import resolve_native_faces
from decode_parameters import read_string
from decode_selection import native_proxy_references, resolve_native_selection
from decode_sketch import reference

FEATURE = "7C5886AE-A774-4848-A89C-C3A578A9763A"
PROXY = "2CA5A1CD-C99B-4C9B-91AF-57989148E841"


def decode_split_face(data, records, body, feature, known, features):
    if feature["class_guid"] != FEATURE or body[:2] != bytes(2):
        raise ValueError("Unsupported SplitFace class/prefix")
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: values[0] for identity, values in grouped.items() if len(values) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError("SplitFace typed reference missing, ambiguous or wrong class")
        return record, data[record.body:record.end]

    def proxy(identity):
        record, payload = typed(identity, PROXY)
        if reference(payload, len(payload)-11) != feature["object_id"]:
            raise ValueError("SplitFace selection proxy owner disagrees")
        return native_proxy_references(data, record)

    def native_descriptor(identity):
        _, payload = typed(identity, "5A1BF548-241F-46FD-9FB5-E4B05126EB9D")
        if (len(payload) != 263 or payload[:2] != bytes(2)
                or struct.unpack_from("<I", payload, 13)[0] != 1
                or reference(payload, 252) != feature["object_id"]):
            raise ValueError("Unsupported SplitFace native descriptor/owner")
        namespace, position = read_string(payload, 17)
        entity_uuid, _ = read_string(payload, position)
        if len(namespace) != 36 or len(entity_uuid) != 36:
            raise ValueError("Unsupported SplitFace descriptor UUID lengths")
        uuid.UUID(namespace)
        uuid.UUID(entity_uuid)
        return payload

    direction_id, cursor = optional_reference(body, 2)
    family = struct.unpack_from("<I", body, cursor)[0]
    projection, extension = body[cursor+4:cursor+6]
    split_type = {(1, 0, False): "SurfaceIntersection", (1, 1, False): "ClosestPoint",
                  (0, 1, True): "AlongVector"}.get((family, projection, direction_id is not None))
    if split_type is None or extension not in (0, 1) or (split_type != "SurfaceIntersection" and extension):
        raise ValueError("Unobserved SplitFace mode/direction/extension combination")
    if struct.unpack_from("<I", body, cursor+6)[0] != 1:
        raise ValueError("Unsupported SplitFace frame count")
    frame_id = reference(body, cursor+10)
    _, frame = typed(frame_id, "2E3AC990-483D-4A55-8662-C064B976A957")
    if len(frame) != 58 or reference(frame, 40) != feature["object_id"]:
        raise ValueError("Unsupported SplitFace frame layout/owner")
    operation_flag = struct.unpack_from("<Q", body, cursor+21)[0]
    if (struct.unpack_from("<I", body, cursor+29)[0] != 1
            or body[cursor+44:cursor+56] != bytes(12)
            or struct.unpack_from("<I", body, cursor+56)[0] != 1):
        raise ValueError("Unsupported SplitFace tool/target selection framing")
    tool_id, face_id = reference(body, cursor+33), reference(body, cursor+60)
    tool_descriptors, properties = proxy(tool_id)
    face_descriptors, _ = proxy(face_id)
    if len(tool_descriptors) != 1 or properties.get("DcFeatureOperationIdFlag") != operation_flag:
        raise ValueError("SplitFace tool count or copied operation flag disagrees")
    target = resolve_native_faces(data, records, face_id, feature["object_id"])
    if not target["faces"] or [f["descriptor_object_id"] for f in target["faces"]] != face_descriptors:
        raise ValueError("SplitFace target face list disagrees with its owned descriptor list")
    descriptor = native_descriptor(tool_descriptors[0])
    tool = resolve_native_selection(data, records, tool_id, known)
    if tool is not None:
        if tool["entity"]["kind"] != "ConstructionPlane":
            raise ValueError("Unobserved SplitFace native splitting tool kind")
    else:
        terminal_id = reference(descriptor, 2)
        _, leaf = typed(terminal_id, "E2CEFD18-D755-4E09-8E7F-953A2F6D43F8")
        if len(leaf) != 26 or leaf[:10] != bytes(10):
            raise ValueError("Unsupported SplitFace sketch curve terminal")
        sketch_id, tag = struct.unpack_from("<QQ", leaf, 10)
        matches = [(f, g) for f in features if f["kind"] == "Sketch" and f["sketch_object_id"] == sketch_id
                   for g in f["geometry"] if g.get("entity_tag") == tag and g["kind"] == "Line"]
        if len(matches) != 1:
            raise ValueError("SplitFace tool sketch/tag identity unresolved or ambiguous")
        sketch, line = matches[0]
        tool = {"selection_object_id": tool_id, "descriptor_object_id": tool_descriptors[0],
                "terminal_object_id": terminal_id, "entity": {"kind": "SketchLine", "sketch_object_id": sketch_id,
                    "sketch_name": sketch["name"], "object_id": line["object_id"], "entity_tag": tag,
                    "component_start_cm": line.get("component_start_cm"), "component_end_cm": line.get("component_end_cm")},
                "association": "Owned tool proxy/descriptor -> explicit sketch ID and curve tag"}
    direction, direction_descriptors = None, []
    if direction_id is not None:
        _, payload = typed(direction_id, "F2A7590D-6654-4674-B393-A2AEF4FEC48A")
        if (len(payload) != 202 or payload[:6] != bytes.fromhex("000008000000")
                or struct.unpack_from("<I", payload, 99)[0] != 1
                or reference(payload, 191) != feature["object_id"]):
            raise ValueError("Unsupported SplitFace direction selection/owner")
        direction_descriptors = [reference(payload, 103)]
        native_descriptor(direction_descriptors[0])
        direction = resolve_native_selection(data, records, direction_id, known)
        if direction is None or direction["entity"]["kind"] != "ConstructionAxis":
            raise ValueError("Only observed native-axis SplitFace projection directions are decoded")
    sentinel, end = read_string(body, cursor+71)
    if sentinel != "00000000-0000-0000-0000-000000000000" or body[end:end+3] != bytes(3):
        raise ValueError("Unsupported SplitFace reference-table sentinel")
    count = struct.unpack_from("<I", body, end+3)[0]
    expected = [tool_id]+tool_descriptors+[face_id]+face_descriptors
    if direction_id is not None:
        expected += [direction_id]+direction_descriptors
    if count != len(expected) or [reference(body, end+7+11*i) for i in range(count)] != expected:
        raise ValueError("SplitFace feature table does not repeat its ordered selections/descriptors")
    end += 7+11*count
    label, _ = read_string(body, end+4)
    if struct.unpack_from("<I", body, end)[0] != 4 or label != "SplitFace":
        raise ValueError("Unsupported SplitFace table metadata or kind label")
    return {"split_type": split_type, "is_tool_extended": bool(extension) if split_type == "SurfaceIntersection" else None,
            "stored_extension_flag": extension, "stored_mode_fields": [family, projection],
            "tool_selection_record_object_id": tool_id, "tool": tool, "target_selection_record_object_id": face_id,
            "target_faces": target["faces"], "target_face_count": len(target["faces"]),
            "projection_direction": direction, "frame_record_object_id": frame_id,
            "stored_operation_flag": operation_flag, "ordered_selection_reference_ids": expected,
            "scope": "Observed surface/closest-point/axis-projection controls, a plane or sketch-line tool and owned target face recipes",
            "geometry_status": "Explicit historical body/face recipes; exact selected/result faces and split geometry regeneration unresolved"}
