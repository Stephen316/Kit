"""Observed planar split-body input lists and extension flags."""

import struct

from decode_selection import native_proxy_references, resolve_native_selection
from decode_sketch import reference


def decode_split(data, records, body, feature, known, *, tool_resolver=None):
    if body[:6] != bytes.fromhex("000100000000") or body[6] not in (0, 1):
        raise ValueError("Unsupported split-body prefix")
    if struct.unpack_from("<I", body, 7)[0] != 1 or body[20] != 0:
        raise ValueError("Unsupported split-body tool layout")
    operation_flag = struct.unpack_from("<Q", body, 22)[0]
    if struct.unpack_from("<I", body, 30)[0] != 1:
        raise ValueError("Unsupported split-body tool count")
    tool_id = reference(body, 34)
    definition_id = reference(body, 11)
    if body[45:49] != b"\0"*4:
        raise ValueError("Unsupported split-body target header")
    count = struct.unpack_from("<I", body, 49)[0]
    if not 1 <= count <= 1024:
        raise ValueError("Unsupported split target count")
    result_ids = [reference(body, 53+11*i) for i in range(count)]
    cursor = 53+11*count
    if body[cursor:cursor+8] != bytes.fromhex("0000000001000000"):
        raise ValueError("Unsupported split target selection prefix")
    targets_id = reference(body, cursor+8)

    def proxy(identity):
        matches = [r for r in records if r.object_id == identity and r.is_primary
                   and r.class_guid == "2CA5A1CD-C99B-4C9B-91AF-57989148E841"]
        if len(matches) != 1:
            raise ValueError("Split input proxy unresolved or ambiguous")
        record = matches[0]
        chunk = data[record.body:record.end]
        if reference(chunk, len(chunk)-11) != feature["object_id"]:
            raise ValueError("Split input owner disagrees with feature")
        return native_proxy_references(data, record)

    tool_descriptors, props = proxy(tool_id)
    target_descriptors, _ = proxy(targets_id)
    if len(tool_descriptors) != 1 or props.get("DcFeatureOperationIdFlag") != operation_flag:
        raise ValueError("Split tool operation flag disagrees with feature")
    if len(target_descriptors) != count:
        raise ValueError("Split target and per-target record counts disagree")
    tool = (resolve_native_selection(data, records, tool_id, known) if tool_resolver is None else
            tool_resolver(data, records, tool_id, feature, known))
    if tool_resolver is not None and (not isinstance(tool, dict)
            or tool.get("entity", {}).get("kind") not in ("BRepFace", "BRepBody")
            or not isinstance(tool.get("native_evidence"), dict)):
        raise ValueError("Split tool resolver did not qualify an observed BRep tool")
    settings = {"is_tool_extended": bool(body[6]), "input_body_count": count,
                "split_definition_record_object_id": definition_id,
                "tool_selection_record_object_id": tool_id, "tool": tool,
                "tool_descriptor_object_id": tool_descriptors[0],
                "target_selection_record_object_id": targets_id, "target_descriptor_object_ids": target_descriptors,
                "per_target_record_object_ids": result_ids, "stored_operation_flag": operation_flag,
                "target_selection_status": "Explicit target descriptors retained; body topology unresolved"}
    if tool is None:
        settings["tool_selection_status"] = "Split tool reference unresolved"
    elif tool_resolver is None and tool["entity"]["kind"] != "ConstructionPlane":
        raise ValueError("Split tool resolved outside observed planar layout")
    return settings
