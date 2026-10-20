"""Captured Point patterns, single selected direction and symmetric suppression.

Membership and normalized groups use the common native framing reader. Only the
two captured symmetric suppression combinations are accepted by this extension.
"""

import math
import struct

from decode_sketch import attributes, constraint_prefix
from decode_sketch_pattern_modes import CIRCULAR, RECTANGULAR, decode_sketch_pattern


POINT = "C2CEDAE7-1716-47C1-B7B1-07B70081D0FB"


def captured_symmetric_suppression(indices, settings, total):
    """Normalize only the independently observed symmetric API masks."""
    if (settings["kind"] == "SketchCircularPattern" and total == 4
            and settings["is_symmetric"] and settings["quantity"] == 4
            and math.isclose(settings["total_angle_radians"], math.pi, abs_tol=1e-9)
            and indices == [1]):
        return [2]
    if (settings["kind"] == "SketchRectangularPattern" and total == 6
            and settings["quantity_one"] == 3 and settings["quantity_two"] == 2
            and settings["symmetric_one"] and not settings["symmetric_two"]
            and settings["distance_type"] == "Spacing" and indices == [2]):
        return [2]
    raise ValueError("Uncaptured symmetric quantity/symmetry/native suppression-index combination")


def decode_sketch_pattern_coverage(data, records, features):
    """Return new patterns/unresolved; no feature mutation or geometry additions."""
    sketches = {f["sketch_object_id"]:f for f in features if f["kind"] == "Sketch"}
    geometry = {g["object_id"]:g for s in sketches.values() for g in s.get("geometry",[])}
    primary = {r.object_id:r for r in records if r.is_primary}
    patterns, unresolved = [], []
    for record in records:
        if not record.is_primary or record.class_guid not in (CIRCULAR,RECTANGULAR):
            continue
        try:
            body = data[record.body:record.end]
            dependencies, _, cursor = constraint_prefix(body)
            head = body[cursor:]
            point_members = dependencies and all(geometry.get(i,{}).get("kind") == "Point" for i in dependencies)
            if record.class_guid == CIRCULAR:
                direction_count = 0
                suppression_count = struct.unpack_from("<I",head,38)[0]
                symmetric = bool(head[42+4*suppression_count])
            else:
                direction_count = struct.unpack_from("<I",head,3)[0]
                suppression_count = struct.unpack_from("<I",head,11+11*direction_count)[0]
                symmetric = bool(head[1] or head[2])
            symmetric_suppressed = symmetric and suppression_count > 0
            if not point_members and direction_count != 1 and not symmetric_suppressed:
                continue
            pattern, owner = decode_sketch_pattern(data,record,sketches,geometry,
                member_kinds=("Line","Circle","Point"), allow_single_direction=True,
                symmetric_suppression_mapper=captured_symmetric_suppression)
            if pattern["seed_entity_count"] != 1:
                raise ValueError("Only captured single-seed sketch-pattern coverage variants supported")
            seed = geometry[pattern["entity_ids"][0]]
            variants = []
            if point_members:
                if pattern["suppressed_instance_ordinals"] or direction_count or symmetric:
                    raise ValueError("Point suppression/symmetry/selected-direction combinations remain uncaptured")
                for identity in pattern["entity_ids"]+pattern["created_entity_ids"]:
                    typed = primary.get(identity)
                    if typed is None or typed.class_guid != POINT:
                        raise ValueError("Pattern Point member has no typed native point record")
                    props,_ = attributes(data[typed.body:typed.end],2)
                    item = geometry[identity]
                    if props.get("pt_tag") != item["entity_tag"] or props.get("EntityGenesis") != item["entity_genesis"]:
                        raise ValueError("Pattern Point native tag/genesis disagrees with validated primitive")
                variants.append("PointSeed")
            if direction_count == 1:
                if seed["kind"] != "Line" or pattern["suppressed_instance_ordinals"] or symmetric:
                    raise ValueError("Only captured single-Line unsuppressed/non-symmetric one-direction pattern supported")
                variants.append("OneExplicitDirection")
            if symmetric_suppressed:
                if seed["kind"] != "Circle" or direction_count:
                    raise ValueError("Only captured default-direction single-Circle symmetric suppression supported")
                variants.append("CapturedSymmetricSuppression")
            pattern["sketch_object_id"] = owner
            pattern["captured_coverage_variants"] = variants
            patterns.append(pattern)
        except (ValueError,KeyError,IndexError,UnicodeError,struct.error) as error:
            unresolved.append({"object_id":record.object_id,"class_guid":record.class_guid,"reason":str(error)})
    return {"patterns":patterns,"additional_geometry":[],"unresolved":unresolved,
            "scope":"Captured Point seeds, one explicit planar rectangular direction and two strictly bounded symmetric suppression masks; no general symmetric ordinal formula"}
