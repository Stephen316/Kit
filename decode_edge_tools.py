"""Observed fillet/chamfer edge-set definitions, without edge topology recovery."""

import struct

from decode_extrude import optional_reference
from decode_sketch import reference


def decode_edge_tool(data, records, body, feature):
    bindings = {p["binding_object_id"]: p for p in feature["parameters"]}

    def value(identity, role):
        parameter = bindings.get(identity)
        if parameter is None or parameter["role"] != role:
            raise ValueError("Edge-set binding does not resolve: "+role)
        return {"value": parameter["raw_float64"], "role": role,
                "name": parameter["parameter_name"], "binding_object_id": identity}

    def record_body(identity, guid):
        matches = [r for r in records if r.object_id == identity and r.class_guid == guid and r.is_primary]
        if len(matches) != 1:
            raise ValueError("Typed edge-set reference unresolved or ambiguous")
        record = matches[0]
        return data[record.body:record.end]

    def selection_owner(identity):
        selection = record_body(identity, "2CA5A1CD-C99B-4C9B-91AF-57989148E841")
        if len(selection) != 105 or reference(selection, 94) != feature["object_id"]:
            raise ValueError("Edge-set selection owner disagrees with feature")

    if feature["kind"] == "Chamfer":
        if body[:8] != bytes.fromhex("0000010000000001"):
            raise ValueError("Unsupported chamfer feature prefix")
        count = struct.unpack_from("<I", body, 8)[0]
        if not 1 <= count <= 1024:
            raise ValueError("Unsupported chamfer set count")
        for index in range(count):
            ordinal, reserved, repeated = struct.unpack_from("<IIH", body, 12+10*index)
            if (ordinal, reserved, repeated) != (index+1, 0, index+1):
                raise ValueError("Unsupported chamfer set ordinal table")
        cursor = 12+10*count
        if struct.unpack_from("<I", body, cursor)[0] != count:
            raise ValueError("Chamfer edge-set counts disagree")
        identities = [reference(body, cursor+4+11*i) for i in range(count)]
        sets = []
        for identity in identities:
            chunk = record_body(identity, "0D383DB2-A6E5-48C7-82D5-ED3DD0C275C5")
            if chunk[:2] != b"\0\0" or chunk[2] not in (0, 1) or chunk[3] not in (0, 1):
                raise ValueError("Unsupported chamfer set flags")
            if reference(chunk, len(chunk)-11) != feature["object_id"]:
                raise ValueError("Chamfer set owner disagrees with feature")
            cursor, refs = 4, []
            for _ in range(3):
                item, cursor = optional_reference(chunk, cursor)
                refs.append(item)
            mode = struct.unpack_from("<I", chunk, cursor)[0]
            selection_id = reference(chunk, cursor+4)
            selection_owner(selection_id)
            item = {"tangent_chain": bool(chunk[2]), "definition_record_object_id": identity,
                    "selection_record_object_id": selection_id}
            if mode == 1 and refs[0] is None and refs[2] is None and chunk[3] == 0:
                item.update(kind="EqualDistanceChamferEdgeSet", distance=value(refs[1], "Distance"))
            elif mode == 2 and refs[0] is None:
                item.update(kind="TwoDistancesChamferEdgeSet", distanceOne=value(refs[1], "Distance 1"),
                            distanceTwo=value(refs[2], "Distance 2"), isFlipped=bool(chunk[3]))
            elif mode == 3 and refs[2] is None:
                item.update(kind="DistanceAndAngleChamferEdgeSet", angle=value(refs[0], "Rotate Angle"),
                            distance=value(refs[1], "Distance"), isFlipped=bool(chunk[3]))
            else:
                raise ValueError("Unsupported chamfer mode/reference combination")
            item["stored_mode"] = mode
            sets.append(item)
        return {"edge_sets": sets, "input_selection_status": "Actual chamfer edge/face topology unresolved"}

    if body[:2] != b"\0\0":
        raise ValueError("Unsupported fillet feature prefix")
    count = struct.unpack_from("<I", body, 2)[0]
    if not 1 <= count <= 1024:
        raise ValueError("Unsupported fillet edge-set count")
    identities = [reference(body, 6+11*i) for i in range(count)]
    cursor = 6+11*count
    if body[cursor:cursor+4] != b"\0"*4 or body[cursor+4] not in (0, 1):
        raise ValueError("Unsupported fillet corner-mode layout")
    settings = {"rolling_ball_corner": bool(body[cursor+4]), "edge_sets": [],
                "input_selection_status": "Actual fillet edge/face topology unresolved"}
    for set_index, identity in enumerate(identities):
        chunk = record_body(identity, "4A557CE2-375C-4F69-AA76-2403109F1493")
        if chunk[:2] != b"\0\0" or chunk[6] not in (0, 1) or chunk[7] not in (0, 1) or chunk[8] != 0:
            raise ValueError("Unsupported fillet edge-set flags")
        item = {"definition_record_object_id": identity, "tangent_chain": bool(chunk[7]),
                "continuity": 2 if chunk[6] else 1}
        mode = chunk[2:6]
        if mode == bytes.fromhex("00000100") and len(chunk) == 78:
            if chunk[9] or chunk[21:44] != b"\0"*23 or chunk[55:59] != b"\0"*4:
                raise ValueError("Unsupported constant fillet fields")
            item.update(kind="ConstantRadiusFilletEdgeSet", radius=value(reference(chunk, 44), "Radius"))
            selection_id, weight_offset = reference(chunk, 10), 63
        elif mode == bytes.fromhex("00010000") and len(chunk) == 78:
            if chunk[31:59] != b"\0"*28:
                raise ValueError("Unsupported chord fillet fields")
            item.update(kind="ChordLengthFilletEdgeSet", chordLength=value(reference(chunk, 9), "ChordLen"))
            selection_id, weight_offset = reference(chunk, 20), 63
        elif mode == bytes.fromhex("01000000") and len(chunk) == 88:
            if chunk[9] or chunk[21] or chunk[44:69] != b"\0"*25:
                raise ValueError("Unsupported asymmetric fillet fields")
            item.update(kind="AsymmetricFilletEdgeSet", offsetOne=value(reference(chunk, 22), "EdgeOffset1"),
                        offsetTwo=value(reference(chunk, 33), "EdgeOffset2"),
                        flip_status="Asymmetric fillet flip state unresolved")
            selection_id, weight_offset = reference(chunk, 10), 73
        elif mode == b"\0"*4 and len(chunk) == 90:
            if chunk[9] or chunk[21:36] != b"\0"*15 or struct.unpack_from("<I", chunk, 36)[0] != 2:
                raise ValueError("Unsupported variable fillet radius list")
            if chunk[62:71] != b"\0"*9:
                raise ValueError("Unsupported variable fillet intermediate radii")
            item.update(kind="VariableRadiusFilletEdgeSet", startRadius=value(reference(chunk, 40), "StartRadius"),
                        endRadius=value(reference(chunk, 51), "EndRadius"),
                        radius_scope="Observed endpoint-only variable radius; intermediate radii unsupported")
            selection_id, weight_offset = reference(chunk, 10), 75
        else:
            raise ValueError("Unsupported fillet edge-set mode or layout")
        if chunk[weight_offset+11:] != b"\0"*4:
            raise ValueError("Unsupported fillet edge-set trailer")
        if struct.unpack_from("<I", chunk, weight_offset-4)[0] != set_index:
            raise ValueError("Fillet edge-set index disagrees with feature list order")
        selection_owner(selection_id)
        item.update(tangencyWeight=value(reference(chunk, weight_offset), "TangencyWeight"),
                    selection_record_object_id=selection_id)
        settings["edge_sets"].append(item)
    return settings
