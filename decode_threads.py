"""Observed straight metric-thread metadata, controls and owned selections."""

import struct

from decode_parameters import read_string
from decode_selection import native_proxy_references
from decode_sketch import numbers, reference
from decode_extrude import optional_reference


def thread_parent_hole(body):
    count = struct.unpack_from("<I", body, 11)[0]
    if count not in (0, 1):
        raise ValueError("Unsupported thread parent header")
    cursor = 15+16*count
    for _ in range(5):
        _, cursor = read_string(body, cursor)
    return optional_reference(body, cursor+38)[0]


def decode_thread(data, records, body, feature, *, selection_resolver=None):
    if feature["class_guid"] != "584D9526-EF22-4F6F-9FE1-5FCF1F3CE575" or body[:2] != b"\0\0" or body[10] not in (0, 1):
        raise ValueError("Unsupported thread prefix/class")
    table_count = struct.unpack_from("<I", body, 11)[0]
    if table_count not in (0, 1):
        raise ValueError("Unsupported modeled-thread table size")
    table = [list(struct.unpack_from("<QQ", body, 15+16*i)) for i in range(table_count)]
    cursor, strings = 15+16*table_count, []
    for _ in range(5):
        text, cursor = read_string(body, cursor)
        strings.append(text)
    thread_class, designation, designation_copy, size, family = strings
    if designation != designation_copy or family != "ISO Metric profile":
        raise ValueError("Only observed matching straight metric thread definitions supported")
    parent_hole, binding_cursor = optional_reference(body, cursor+38)
    hand_cursor = binding_cursor+22
    full, modeled, handed = body[cursor], body[cursor+21], body[hand_cursor]
    location = struct.unpack_from("<I", body, cursor+1)[0]
    if (any(v not in (0, 1) for v in (full, modeled, handed)) or location not in (1, 2)
            or body[hand_cursor+1:hand_cursor+41] != b"\0"*40
            or bool(table_count) != bool(modeled)):
        raise ValueError("Unsupported thread flags/location/table combination")
    angle = numbers(body, 2, 1)[0]
    major, minor = numbers(body, cursor+5, 2)
    pitch, pitch_diameter = numbers(body, cursor+22, 2)
    if not (0 < angle < 180 and 0 < minor < pitch_diameter < major and pitch > 0):
        raise ValueError("Unsupported thread physical dimensions")
    bindings = {p["binding_object_id"]: p for p in feature["parameters"]}

    def parameter(offset, role):
        identity = reference(body, offset)
        parameter = bindings.get(identity)
        if parameter is None or parameter["role"] != role:
            raise ValueError("Thread parameter binding unresolved: "+role)
        return parameter["raw_float64"], identity

    if parent_hole is not None:
        parents = [r for r in records if r.is_primary and r.object_id == parent_hole
                   and r.class_guid == "1C037A07-4A15-43F6-ABFC-BBF61B9038D4"]
        if len(parents) != 1:
            raise ValueError("Attached thread parent hole is unresolved")
    length_role = "ThreadDepth" if parent_hole is not None else "ThreadLength"
    length, length_binding = parameter(binding_cursor, length_role)
    offset, offset_binding = parameter(binding_cursor+11, "ThreadOffset")
    selection_cursor = hand_cursor+41
    selection_count = struct.unpack_from("<I", body, selection_cursor)[0]
    if length <= 0 or offset < 0 or (selection_resolver is None and selection_count != 1):
        raise ValueError("Unsupported thread length/offset/selection count")
    selection_evidence = None
    if selection_resolver is None:
        selection_id = reference(body, hand_cursor+45)
        proxies = [r for r in records if r.is_primary and r.object_id == selection_id
                   and r.class_guid == "2CA5A1CD-C99B-4C9B-91AF-57989148E841"]
        if len(proxies) != 1:
            raise ValueError("Thread input selection unresolved")
        proxy = proxies[0]
        payload = data[proxy.body:proxy.end]
        if reference(payload, len(payload)-11) != feature["object_id"]:
            raise ValueError("Thread selection owner disagrees with feature")
        descriptors, _ = native_proxy_references(data, proxy)
        if len(descriptors) != 1:
            raise ValueError("Only observed single cylindrical thread face supported")
        descriptor = [r for r in records if r.is_primary and r.object_id == descriptors[0]
                      and r.class_guid == "5662F619-2281-4AD9-93DC-1FCFDA1062E7"]
        if len(descriptor) != 1:
            raise ValueError("Unsupported thread cylindrical-face descriptor")
        payload = data[descriptor[0].body:descriptor[0].end]
        if reference(payload, len(payload)-11) != feature["object_id"]:
            raise ValueError("Thread face descriptor owner disagrees with feature")
    else:
        selection_evidence = selection_resolver(data, records, body, feature, selection_cursor)
        if not isinstance(selection_evidence,dict):
            raise ValueError("Thread plural selection resolver did not return bounded evidence")
        selection_ids = selection_evidence.get('selection_record_object_ids')
        descriptors = selection_evidence.get('descriptor_object_ids')
        selection_end = selection_evidence.get('selection_end_offset')
        if (selection_count != 2 or not isinstance(selection_ids,list) or not isinstance(descriptors,list)
                or len(selection_ids) != selection_count or len(descriptors) != selection_count
                or any(type(i) is not int for i in selection_ids+descriptors)
                or len(set(selection_ids)) != selection_count or len(set(descriptors)) != selection_count
                or type(selection_end) is not int or selection_end != selection_cursor+4+11*selection_count
                or selection_end > len(body)
                or [reference(body,selection_cursor+4+11*i) for i in range(selection_count)] != selection_ids):
            raise ValueError("Thread plural selection count/extent/identity copies disagree")
    return {"thread_type": family, "thread_size": size, "thread_designation": designation, "thread_class": thread_class,
            "thread_angle_degrees": angle, "is_internal": not bool(body[10]), "is_modeled": bool(modeled),
            "is_right_handed": bool(handed), "is_full_length": bool(full), "pitch_cm": pitch,
            "major_diameter_cm": major, "minor_diameter_cm": minor, "pitch_diameter_cm": pitch_diameter,
            "active_length_cm": None if full else length, "active_offset_cm": None if full else offset,
            "stored_length_cm": length, "stored_offset_cm": offset,
            "stored_location_code": location, "active_location": None if full else {1: "HighEnd", 2: "LowEnd"}[location],
            "parameter_bindings": {length_role: length_binding, "ThreadOffset": offset_binding},
            "attached_hole_object_id": parent_hole,
            "stored_modeled_table_pairs": table, "modeled_table_scope": "Opaque integer pairs; not interpreted as ASM record indices",
            **({"selection_record_object_id": selection_id, "descriptor_object_ids": descriptors} if selection_evidence is None else
               {"selection_record_object_ids": selection_ids, "descriptor_object_ids": descriptors, "selection_evidence": selection_evidence}),
            "input_selection_status": (("Owned cylindrical-face descriptor and attached parent-hole link retained" if parent_hole is not None else
                                       "Owned cylindrical-face descriptor retained; persistent face-to-ASM mapping unresolved") if selection_evidence is None else
                                       "Owned plural cylindrical-face descriptors and native source recipes retained; API handle and persistent face-to-ASM correspondence unresolved"),
            "length_scope": "Full-length mode has inactive native length/offset bindings even when API getters return null",
            "geometry_status": "Thread metadata/settings decoded; helical thread geometry is not regenerated"}
