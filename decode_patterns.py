"""Observed rectangular pattern control references and distance conventions."""

import struct

from decode_extrude import optional_reference
from decode_selection import resolve_native_selection
from decode_sketch import attributes, numbers, reference, same


def decode_rectangular_pattern(data, records, body, feature, known):
    if body[0] != 0 or body[1] not in (0, 1):
        raise ValueError("Unsupported rectangular pattern feature prefix")
    cursor = attributes(body, 2)[1] if body[1] else 2
    control_id = reference(body, cursor)
    bindings = {p["binding_object_id"]: p for p in feature["parameters"]}

    def parameter(identity, role, integer=False):
        result = bindings.get(identity)
        if result is None or result["role"] != role:
            raise ValueError("Pattern binding does not resolve: "+role)
        value = result["raw_float64"]
        if integer:
            if value < 1 or not value.is_integer():
                raise ValueError("Invalid pattern quantity")
            return int(value)
        return value

    choices = []
    for record in records:
        if record.object_id != control_id or record.class_guid != "EA0E146E-3126-42F0-9280-0DE74AB17D78":
            continue
        chunk = data[record.body:record.end]
        if len(chunk) < 180 or chunk[:5] != bytes.fromhex("0102000000"):
            continue
        if reference(chunk, len(chunk)-26) != feature["object_id"]:
            continue
        if chunk[16:20] != b"\0"*4 or chunk[31:44] != b"\0"*9+b"\xff"*4:
            continue
        if chunk[90] not in (0, 1) or chunk[91] not in (0, 1):
            continue
        quantity_one, quantity_two = reference(chunk, 5), reference(chunk, 20)
        if reference(chunk, 92) != quantity_two or reference(chunk, len(chunk)-37) != quantity_one:
            raise ValueError("Repeated pattern quantity references disagree")
        one_axis = reference(chunk, 103)
        two_axis, cursor = optional_reference(chunk, 114)
        if chunk[cursor:cursor+24] != b"\0"*12+struct.pack("<II", 2, 2)+b"\xff"*4:
            raise ValueError("Unsupported pattern distance-mode prefix")
        flag = chunk[cursor+24]
        if flag not in (0, 1):
            raise ValueError("Unsupported pattern distance convention")
        selections = [resolve_native_selection(data, records, identity, known) if identity is not None else None
                      for identity in (one_axis, two_axis)]
        stored_two = numbers(chunk, 44, 3)
        if two_axis is None and not same(stored_two, [0, 0, 0]):
            raise ValueError("Unexpected stored vector in inactive second pattern direction")
        directions = []
        for selection in selections:
            entity = selection["entity"] if selection else None
            directions.append(entity.get("direction") if entity and entity["kind"] == "ConstructionAxis" else None)
        if directions[1] is not None and not same(directions[1], stored_two):
            raise ValueError("Pattern axis selection disagrees with stored direction")
        choices.append({
            "quantity_one": parameter(quantity_one, "countU", True),
            "quantity_two": parameter(quantity_two, "CountV", True),
            "distance_one_cm": parameter(reference(chunk, 68), "uSpaceDistance"),
            "distance_two_cm": parameter(reference(chunk, 79), "vSpaceDistance"),
            "distance_type": "Extent" if flag else "Spacing", "stored_extent_flag": flag,
            "symmetric_one": bool(chunk[90]), "symmetric_two": bool(chunk[91]),
            "direction_one": directions[0], "direction_two": directions[1],
            "direction_one_selection": selections[0], "direction_two_selection": selections[1],
            "direction_one_selection_record_object_id": one_axis,
            "direction_two_selection_record_object_id": two_axis,
            "stored_direction_two_vector": stored_two,
            "direction_scope": "Observed native construction axes; inactive API default direction not inferred",
            "control_record_object_id": control_id,
            "input_selection_status": "Selected bodies/features, suppressed elements and compute option unresolved",
        })
    if len(choices) != 1:
        raise ValueError("Rectangular pattern control record unresolved or ambiguous")
    return choices[0]
