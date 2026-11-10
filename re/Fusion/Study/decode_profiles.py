"""Observed selected-profile loop membership, with explicit sketch curve tags.

This resolves boundary membership and outer/inner loops. Stored curve order is
not assumed to be traversal order; trimmed/intersection contours remain partial.
"""

import struct

from decode_sketch import reference


PROFILE_DESCRIPTOR_GUID = "4BD53E5A-0B3E-45E5-AE8B-02044306485A"
PROFILE_LOOP_GUID = "0D57BD2F-D09B-43FC-AD57-1E89A118C453"


def read_loops(body, descriptor_id, sketch, *, curve_reference_details=None):
    if body[:2] != b"\0\0" or reference(body, 2) != descriptor_id:
        raise ValueError("Profile loop ownership does not match its descriptor")
    if struct.unpack_from("<I", body, 13)[0] != 1:
        raise ValueError("Unsupported profile set prefix")
    count = struct.unpack_from("<I", body, 17)[0]
    if not 1 <= count <= 1024:
        raise ValueError("Unsupported profile loop count")
    by_tag = {}
    for geometry in sketch["geometry"]:
        if geometry["kind"] != "Point":
            by_tag.setdefault(geometry["entity_tag"], []).append(geometry)
    cursor, loops = 21, []
    for _ in range(count):
        size = struct.unpack_from("<I", body, cursor)[0]
        cursor += 4
        if not 1 <= size <= 100000 or cursor+size*40+1 > len(body):
            raise ValueError("Unsupported profile curve count or truncated loop")
        curves = []
        for _ in range(size):
            code, tag, secondary, direction, flag_one, flag_two, opaque = struct.unpack_from("<IQQIIIQ", body, cursor)
            cursor += 40
            if (code != 3 or secondary or direction not in (0, 1) or opaque
                    or curve_reference_details is None and (flag_one, flag_two) != (1, 1)):
                raise ValueError("Unsupported profile curve or trim-reference layout")
            candidates = by_tag.get(tag, [])
            if len(candidates) != 1:
                raise ValueError("Profile curve tag is unresolved or ambiguous")
            curve = {"entity_id": candidates[0]["object_id"], "entity_kind": candidates[0]["kind"],
                     "entity_tag": tag, "secondary_tag": secondary, "stored_direction_flag": direction}
            if curve_reference_details is not None:
                extra = curve_reference_details((code, tag, secondary, direction, flag_one, flag_two, opaque), candidates[0])
                if not isinstance(extra, dict) or curve.keys() & extra.keys():
                    raise ValueError('Profile curve detail callback would replace native identity fields')
                curve.update(extra)
            curves.append(curve)
        outer = body[cursor]
        cursor += 1
        if outer not in (0, 1):
            raise ValueError("Unsupported profile outer-loop flag")
        loops.append({"is_outer": bool(outer), "curve_references": curves,
                      "order_status": "Stored membership order; traversal ordering not decoded"})
    if body[cursor:] != b"\0\0\0\0" or not any(loop["is_outer"] for loop in loops):
        raise ValueError("Unsupported profile loop suffix or missing outer loop")
    return loops


def decode_profiles(data, records, features):
    sketches = {f["sketch_object_id"]: f for f in features if f["kind"] == "Sketch"}
    by_offset = {r.start: r for r in records}
    decoded, unresolved = [], []
    for feature in features:
        if feature["kind"] not in ("Extrude", "Revolve", "SurfacePatch"):
            continue
        sources = feature.get("sketch_reference_candidates", [])
        if not sources:
            unresolved.append({"feature_object_id": feature["object_id"], "reason": "Profile source reference is unresolved"})
        for source in sources:
            try:
                descriptor = by_offset[source["reference_record_offset"]]
                if descriptor.class_guid != PROFILE_DESCRIPTOR_GUID:
                    raise ValueError("Unsupported profile descriptor class")
                sketch = sketches[source["sketch_object_id"]]
                definition_id = reference(data[descriptor.body:descriptor.end], 2)
                choices = []
                for definition in records:
                    if definition.object_id != definition_id or definition.class_guid != PROFILE_LOOP_GUID:
                        continue
                    loops = read_loops(data[definition.body:definition.end], descriptor.object_id, sketch)
                    choices.append({"sketch_object_id": sketch["sketch_object_id"], "sketch_name": sketch["name"],
                                    "descriptor_object_id": descriptor.object_id,
                                    "loop_definition_object_id": definition_id, "loops": loops,
                                    "selection_level": "Observed curve membership and outer/inner loops",
                                    "limitations": "No general trim reconstruction or traversal ordering"})
                if len(choices) != 1:
                    raise ValueError("Profile loop definition is unresolved or ambiguous")
                feature.setdefault("profile_selection", []).append(choices[0])
                source["scope"] = "Explicit sketch reference with profile loop membership resolved separately"
                decoded.append({"feature_object_id": feature["object_id"], "descriptor_object_id": descriptor.object_id,
                                "loop_count": len(choices[0]["loops"])})
            except (ValueError, KeyError, IndexError, struct.error) as error:
                unresolved.append({"feature_object_id": feature["object_id"], "reason": str(error)})
    return {"decoded": decoded, "unresolved": unresolved,
            "scope": "Observed selected loop/curve membership only; no general trimmed-profile reconstruction"}
