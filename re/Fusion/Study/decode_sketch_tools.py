"""Observed offset relationships and bounded Line/Circle sketch patterns."""

from collections import Counter
import math
import struct

from decode_sketch import constraint_prefix, numbers, reference
from decode_sketch_pattern_modes import decode_sketch_pattern

OFFSET = "afc07c10-99ac-5304-ae1b-dbee335b0e43"
CIRCULAR = "8269E861-0BB7-47E0-9911-5AE3EC475058"
RECTANGULAR = "40800FB9-C2BE-494E-A047-7D76E82B9F6C"


def decode_sketch_tools(data, records, sketches, entities):
    decoded, unresolved = [], []

    def typed(identity, guid):
        matches = [r for r in records if r.object_id == identity and r.class_guid == guid and r.is_primary]
        if len(matches) != 1:
            raise ValueError("Sketch tool reference unresolved or ambiguous")
        r = matches[0]
        return data[r.body:r.end]

    def parameter(sketch, identity, suffix):
        choices = [p for p in sketch["parameters"] if p["binding_object_id"] == identity and p["role"].endswith(suffix)]
        if len(choices) != 1:
            raise ValueError("Sketch tool parameter binding does not resolve: "+suffix)
        return choices[0]

    def scoped(identity, owner):
        item = entities.get(identity)
        if item is None or item["sketch_object_id"] != owner:
            raise ValueError("Sketch tool entity reference does not resolve in its owner")
        return item

    def offset_side(identity, expected_kind):
        body = typed(identity, "04e598ff-2979-5e41-8bc0-5c435c810909")
        count = struct.unpack_from("<I", body, 1)[0]
        cursor = 5+15*count
        if body[0] != 1 or not 1 <= count <= 1024 or len(body) != cursor+16 or body[cursor] != 0:
            raise ValueError("Unsupported offset side list")
        if struct.unpack_from("<I", body, cursor+12)[0] != expected_kind:
            raise ValueError("Offset parent/child side kind disagrees")
        return [reference(body, 5+15*i) for i in range(count)], reference(body, cursor+1)

    for record in records:
        if not record.is_primary or record.class_guid not in (OFFSET, CIRCULAR, RECTANGULAR):
            continue
        body = data[record.body:record.end]
        try:
            if record.class_guid == OFFSET:
                if len(body) != 176 or body[:5] != bytes.fromhex("0105000000"):
                    raise ValueError("Unsupported offset controller layout")
                owner = reference(body, 135)
                sketch = sketches[owner]
                parent_id, child_id = reference(body, 146), reference(body, 102)
                parents, parent_opposite = offset_side(parent_id, 1)
                children, child_opposite = offset_side(child_id, 2)
                if parent_opposite != child_id or child_opposite != parent_id:
                    raise ValueError("Offset side references are not reciprocal")
                if len(parents) != len(children):
                    raise ValueError("Only observed matching offset topology is supported")
                for identity in parents+children:
                    entity = scoped(identity, owner)
                    side = parent_id if identity in parents else child_id
                    if entity.get("offset_side_record_object_id") != side:
                        raise ValueError("Offset geometry does not refer back to its side list")
                association_id, dimension_id = reference(body, 113), reference(body, 124)
                assoc = typed(association_id, "D3BD153B-EB8A-405E-9D29-69EE0C3D227C")
                dependencies, props, cursor = constraint_prefix(assoc)
                if props != {"EntityGenesis": 32} or reference(assoc, cursor) != owner:
                    raise ValueError("Unsupported offset relationship header")
                code = struct.unpack_from("<Q", assoc, cursor+11)[0]
                count = struct.unpack_from("<I", assoc, cursor+19)[0]
                if code != 0x2000000000 or count != 2*len(parents) or len(assoc) != cursor+24+11*count or assoc[-1] != 0:
                    raise ValueError("Unsupported offset relationship count or trailer")
                pairs = [reference(assoc, cursor+23+11*i) for i in range(count)]
                if Counter(pairs) != Counter(dependencies):
                    raise ValueError("Offset relationship entity copies disagree")
                if Counter(pairs[::2]) != Counter(parents) or Counter(pairs[1::2]) != Counter(children):
                    raise ValueError("Offset relationship parent/child roles disagree")
                dimension = typed(dimension_id, "8C780195-72C0-4a56-A911-E43AB14357F2")
                if struct.unpack_from("<Q", dimension, len(dimension)-35)[0] != 0x1000000000:
                    raise ValueError("Unsupported offset dimension kind")
                binding_id = reference(dimension, len(dimension)-27)
                param = parameter(sketch, binding_id, " Dimension-2")
                distance = numbers(body, 168, 1)[0]
                if not math.isclose(distance, param["raw_float64"], abs_tol=1e-9):
                    raise ValueError("Offset cached distance disagrees with parameter")
                seed_id = reference(body, 157)
                if seed_id not in parents or reference(dimension, len(dimension)-12) != seed_id:
                    raise ValueError("Offset dimension seed is not a parent curve")
                expected = [seed_id, parent_id, child_id, dimension_id, association_id]
                dependencies = [reference(body, 5+15*i) for i in range(5)]
                if Counter(expected) != Counter(dependencies):
                    raise ValueError("Offset controller dependency list disagrees")
                result = {"kind": "OffsetCurves", "object_id": record.object_id,
                          "parent_entity_ids": parents, "child_entity_ids": children,
                          "stored_pairs": list(zip(pairs[::2], pairs[1::2])), "distance_cm": distance,
                          "binding_object_id": binding_id, "parameter_name": param["parameter_name"],
                          "dimension_object_id": dimension_id, "relationship_object_id": association_id,
                          "topology_match_status": "Observed one-to-one stored pairs; general topology-match flag unresolved"}
            else:
                result, owner = decode_sketch_pattern(data, record, sketches, entities)
            result["record_offset"] = record.start
            result["class_guid"] = record.class_guid
            sketches[owner]["constraints"].append(result)
            decoded.append({"object_id": record.object_id, "kind": result["kind"], "sketch_object_id": owner})
        except (ValueError, KeyError, IndexError, struct.error) as error:
            unresolved.append({"object_id": record.object_id, "class_guid": record.class_guid, "reason": str(error)})
    return {"decoded": decoded, "unresolved": unresolved,
            "scope": "Observed offset pairs and Line/Circle patterns with explicit directions and non-symmetric suppression; no solver"}
