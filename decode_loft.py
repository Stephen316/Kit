"""Observed sketch-profile loft sections, flags and Free/Direction end controls."""

import math
import struct

from decode_profile_selections import resolve_sketch_profiles
from decode_selection import resolve_single_sketch_curve
from decode_sketch import attributes, reference


LOFT_GUID = "B6678572-C095-4DD1-9348-614677DD0B4A"
SECTION_GUID = "2F3200BA-FDFB-48C6-97D4-71A4A0D86190"


def decode_loft(data, records, body, feature, features):
    if (feature["class_guid"] != LOFT_GUID or len(body) < 110
            or body[0] != 0 or body[1] not in (0, 1)):
        raise ValueError("Unsupported Loft class/prefix")
    props, base = attributes(body, 2) if body[1] else ({}, 2)
    if props or body[base:base+3] != b"\1\1\1" or body[base+3] not in (0, 1):
        raise ValueError("Unsupported observed Loft control prefix")
    operation = struct.unpack_from("<I", body, base+4)[0]
    if operation != 4:
        raise ValueError("Only observed NewBody loft operation supported")

    def primary(identity, guid):
        matches = [r for r in records if r.is_primary and r.object_id == identity and r.class_guid == guid]
        if len(matches) != 1:
            raise ValueError("Loft typed reference missing or ambiguous")
        record = matches[0]
        return record, data[record.body:record.end]

    bindings = {p["binding_object_id"]: p for p in feature["parameters"]}

    def optional_ref(cursor):
        if cursor >= len(body):
            raise ValueError("Truncated Loft optional reference")
        if body[cursor] == 0:
            return None, cursor+1
        return reference(body, cursor), cursor+11

    def parameter(identity, role):
        binding = bindings.get(identity)
        if binding is None or binding["role"] != role or not math.isfinite(binding["raw_float64"]):
            raise ValueError("Loft binding role disagrees with end control: "+role)
        return binding["raw_float64"]

    def end_condition(cursor, side):
        start = cursor
        if body[cursor:cursor+12] != b"\xff"*4+b"\0"*8:
            raise ValueError("Unsupported Loft end-condition prefix")
        angle_id, cursor = optional_ref(cursor+12)
        code = struct.unpack_from("<I", body, cursor)[0]
        weight_id, cursor = optional_ref(cursor+4)
        stored_edge_field = struct.unpack_from("<I", body, cursor)[0]
        cursor += 4
        if stored_edge_field != 0:
            raise ValueError("Unobserved Loft edge-alignment field")
        result = {"type": {0: "Free", 3: "Direction"}.get(code), "stored_condition_code": code,
                  "stored_edge_field": stored_edge_field, "byte_length": cursor-start}
        if code == 0 and angle_id is None and weight_id is None:
            return result, cursor
        if code != 3 or angle_id is None or weight_id is None:
            raise ValueError("Unsupported Loft end-condition type/bindings")
        angle = parameter(angle_id, side+" TakeOff Angle")
        weight = parameter(weight_id, side+" Weight")
        if weight <= 0:
            raise ValueError("Loft end weight must be positive")
        result.update(angle_radians=angle, weight=weight,
                      angle_binding_object_id=angle_id, weight_binding_object_id=weight_id)
        return result, cursor

    centerline_id, cursor = optional_ref(base+8)
    centerline = (resolve_single_sketch_curve(data, records, centerline_id, feature["object_id"], features, ("Line",))
                  if centerline_id is not None else None)
    end, cursor = end_condition(cursor, "End")
    if body[cursor] != 0 or body[cursor+1] not in (0, 1):
        raise ValueError("Unsupported Loft guide/solid flags")
    is_solid = bool(body[cursor+1])
    rail_count = struct.unpack_from("<I", body, cursor+2)[0]
    if rail_count != 0:
        raise ValueError("Loft rail variants remain unsupported")
    result_control_id = reference(body, cursor+6)
    _, control = primary(result_control_id, "B0387387-0FAA-4928-B189-FEB34071D524")
    if len(control) != 81 or reference(control, 2) != feature["object_id"] or reference(control, 70) != feature["object_id"]:
        raise ValueError("Loft result control owner disagrees")
    cursor += 17
    count = struct.unpack_from("<I", body, cursor)[0]
    cursor += 4
    if not 2 <= count <= 1024:
        raise ValueError("Unsupported Loft section count")
    section_ids = [reference(body, cursor+11*i) for i in range(count)]
    if len(set(section_ids)) != count:
        raise ValueError("Duplicate Loft section references")
    cursor += 11*count
    start, cursor = end_condition(cursor, "Start")
    sections = []
    for index, section_id in enumerate(section_ids):
        _, section = primary(section_id, SECTION_GUID)
        if (len(section) != 36 or section[:10] != b"\0"*10
                or reference(section, 10) != feature["object_id"]
                or struct.unpack_from("<I", section, 32)[0] != 2):
            raise ValueError("Unsupported Loft profile section layout/owner")
        profile_id = reference(section, 21)
        profiles = resolve_sketch_profiles(data, records, profile_id, feature["object_id"], features)
        if len(profiles) != 1:
            raise ValueError("Only observed single-profile Loft sections supported")
        sections.append({"index": index, "section_record_object_id": section_id,
                         "profile": profiles[0],
                         "end_condition": start if index == 0 else end if index == count-1 else None})
    body_count = struct.unpack_from("<I", body, cursor)[0]
    if body_count != 1:
        raise ValueError("Unsupported Loft result body-anchor count")
    anchor_id = reference(body, cursor+4)
    primary(anchor_id, "D26351F0-5940-4D23-AA20-2C35475A6D9E")
    return {"operation": "NewBody", "stored_operation_code": operation, "is_solid": is_solid,
            "is_closed": None,
            "closure_status": "Captured API examples are open; native closure encoding unresolved",
            "is_tangent_edges_merged": bool(body[base+3]),
            "section_count": count, "section_input_record_object_ids": section_ids, "sections": sections,
            "start_condition": start, "end_condition": end,
            "result_control_record_object_id": result_control_id, "result_body_anchor_object_ids": [anchor_id],
            "guide_count": int(centerline is not None), "is_centerline": centerline is not None,
            "centerline": centerline, "stored_rail_count": rail_count,
            "guide_status": "Observed absent guide or single straight sketch centerline; rails and composite centerlines unsupported",
            "section_selection_status": "Explicit ordered section list with sketch profile membership; contour traversal and general trim reconstruction unresolved"}
