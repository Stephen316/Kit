"""Explicit sketch-pattern member/center ownership and reciprocal point helpers.

This augments existing single-circle pattern decoding. It does not infer a
suppression bit, multi-entity seed grouping, or lattice indices from geometry.
"""

from collections import Counter
import struct

from decode_sketch import attributes, constraint_prefix, reference
from decode_sketch_tools import CIRCULAR, RECTANGULAR


POINT_GUID = "C2CEDAE7-1716-47C1-B7B1-07B70081D0FB"
CIRCLE_GUID = "F0130424-8B7E-4092-93C9-1CA807482534"
POINT_HELPER_GUID = "362B7EC3-0F09-47C8-A3BE-DC066715CDAE"


def decode_sketch_pattern_details(data, records, features):
    decoded, unresolved, skipped = [], [], []

    def primary(identity, guid):
        matches = [r for r in records if r.is_primary and r.object_id == identity and r.class_guid == guid]
        if len(matches) != 1:
            raise ValueError("Sketch pattern detail typed reference missing or ambiguous")
        record = matches[0]
        return record, data[record.body:record.end]

    for sketch in features:
        if sketch["kind"] != "Sketch":
            continue
        owner = sketch["sketch_object_id"]
        geometry = {g["object_id"]: g for g in sketch.get("geometry", [])}
        for pattern in sketch.get("constraints", []):
            if pattern["kind"] not in ("SketchCircularPattern", "SketchRectangularPattern"):
                continue
            members = pattern["entity_ids"]+pattern["created_entity_ids"]
            if (pattern.get("seed_entity_count", 1) != 1
                    or pattern.get("suppressed_instance_ordinals") or pattern.get("direction_selections")
                    or any(geometry.get(identity, {}).get("kind") != "Circle" for identity in members)):
                skipped.append({"object_id": pattern["object_id"],
                                "reason": "Expanded pattern shape; optional legacy center-helper reader not applied"})
                continue
            try:
                guid = CIRCULAR if pattern["kind"] == "SketchCircularPattern" else RECTANGULAR
                controller, body = primary(pattern["object_id"], guid)
                dependencies, props, cursor = constraint_prefix(body)
                if props != {"EntityGenesis": 2}:
                    raise ValueError("Unsupported sketch pattern detail attributes")
                slots = [{"entity_object_id": reference(body, 5+15*i),
                          "stored_extra_u32": struct.unpack_from("<I", body, 16+15*i)[0]}
                         for i in range(len(dependencies))]
                # Only zero extras are observed. Their meaning, including any
                # relationship to suppression, is deliberately left unknown.
                if any(slot["stored_extra_u32"] != 0 for slot in slots):
                    raise ValueError("Unobserved sketch pattern dependency extra field")
                head = body[cursor:]
                list_offset, owner_offset = (66, 43) if guid == CIRCULAR else (154, 131)
                if reference(head, owner_offset) != owner:
                    raise ValueError("Sketch pattern detail owner disagrees")
                count = struct.unpack_from("<I", head, list_offset-4)[0]
                if not 2 <= count <= 1024 or len(head) != list_offset+11*count+1 or head[-1] != 0:
                    raise ValueError("Unsupported sketch pattern detail membership list")
                roles = [reference(head, list_offset+11*i) for i in range(count)]
                if len(set(roles)) != count or Counter(roles) != Counter(dependencies):
                    raise ValueError("Sketch pattern detail dependency/role lists disagree")
                members = pattern["entity_ids"]+pattern["created_entity_ids"]
                expected = members+[pattern["center_entity_id"]] if guid == CIRCULAR else members
                if roles != expected or len(pattern["entity_ids"]) != 1:
                    raise ValueError("Sketch pattern detail seed/created order disagrees with decoded roles")
                items = []
                for index, identity in enumerate(members):
                    curve = geometry.get(identity)
                    if curve is None or curve["kind"] != "Circle" or curve["sketch_object_id"] != owner:
                        raise ValueError("Only observed same-sketch circle pattern members supported")
                    _, payload = primary(identity, CIRCLE_GUID)
                    curve_props, start = attributes(payload, 2)
                    if (payload[:2] != b"\0\1" or len(payload)-start != 162
                            or curve_props.get("crv_primary_id") != curve["entity_tag"]
                            or curve_props.get("crv_secondary_id") != 0
                            or reference(payload, len(payload)-11) != owner):
                        raise ValueError("Unsupported sketch pattern circle native layout/owner")
                    center_id = reference(payload, start+96)
                    center = geometry.get(center_id)
                    if (center is None or center["kind"] != "Point" or center["sketch_object_id"] != owner
                            or center_id != curve["center_point_id"]):
                        raise ValueError("Sketch pattern circle center identity disagrees")
                    _, point = primary(center_id, POINT_GUID)
                    point_props, point_start = attributes(point, 2)
                    if (point[:2] != b"\0\1" or len(point)-point_start != 99
                            or point_props.get("pt_tag") != center["entity_tag"]
                            or reference(point, point_start+88) != owner):
                        raise ValueError("Unsupported sketch pattern center point layout/owner")
                    helper_id = reference(point, point_start)
                    if reference(point, point_start+77) != helper_id:
                        raise ValueError("Sketch pattern center helper references disagree")
                    _, helper = primary(helper_id, POINT_HELPER_GUID)
                    if (len(helper) != 29 or helper[:6] != bytes.fromhex("000001000000") or helper[17] != 0
                            or reference(helper, 6) != identity or reference(helper, 18) != center_id):
                        raise ValueError("Sketch pattern circle/point/helper references are not reciprocal")
                    items.append({"membership_index": index, "role": "Seed" if index == 0 else "Created",
                                  "created_order_index": index-1 if index else None,
                                  "entity_object_id": identity, "entity_tag": curve["entity_tag"],
                                  "dependency_order_index": dependencies.index(identity),
                                  "center_point_object_id": center_id, "center_point_tag": center["entity_tag"],
                                  "center_helper_object_id": helper_id,
                                  "stored_curve_entity_genesis": curve_props.get("EntityGenesis"),
                                  "stored_point_entity_genesis": point_props.get("EntityGenesis"),
                                  "center_cm": curve["center_cm"], "radius_cm": curve["radius_cm"],
                                  "suppression_state": None,
                                  "suppression_status": "Native suppression field unresolved; geometry presence does not establish suppression state"})
                decoded.append({"object_id": controller.object_id, "kind": pattern["kind"],
                                "sketch_object_id": owner, "sketch_name": sketch["name"],
                                "members": items, "dependency_slots": slots, "ordered_role_entity_ids": roles,
                                "center_entity_id": pattern.get("center_entity_id"),
                                "scope": "Existing ordered single-circle member roles enriched with explicit reciprocal center-point/helper provenance; no inferred lattice positions"})
            except (ValueError, KeyError, IndexError, struct.error) as error:
                unresolved.append({"object_id": pattern["object_id"], "reason": str(error)})
    return {"patterns": decoded, "unresolved": unresolved, "skipped": skipped,
            "scope": "Observed single-circle pattern member ownership and reciprocal native center helpers",
            "limitations": "Multi-entity seeds, non-circle pattern members, suppression states and selected nondefault directions remain unresolved"}
