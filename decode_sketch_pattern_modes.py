"""Observed multi-entity sketch patterns, explicit directions and suppression.

Native role lists contain the seed prefix followed by active instance-major
member groups. Suppressed non-seed ordinals are explicitly counted in each
controller; omitted cached geometry is not itself used to infer suppression.
The shared constraint reader limits this path to16 dependency arguments.
"""

from collections import Counter
import math
import struct

from decode_sketch import constraint_prefix, numbers, reference, same


CIRCULAR = "8269E861-0BB7-47E0-9911-5AE3EC475058"
RECTANGULAR = "40800FB9-C2BE-494E-A047-7D76E82B9F6C"


def decode_sketch_pattern(data, record, sketches, entities):
    """Return (constraint, owner_sketch_id) for one observed pattern record."""
    if not record.is_primary or record.class_guid not in (CIRCULAR, RECTANGULAR):
        raise ValueError("Unsupported sketch pattern class")
    body = data[record.body:record.end]
    dependencies, props, offset = constraint_prefix(body)
    if props != {"EntityGenesis": 2}:
        raise ValueError("Unsupported sketch pattern attributes")
    if any(struct.unpack_from("<I", body, 16+15*i)[0] != 0 for i in range(len(dependencies))):
        raise ValueError("Unobserved sketch pattern dependency extra field")
    head = body[offset:]

    def u32(cursor):
        return struct.unpack_from("<I", head, cursor)[0]

    def suppression(cursor):
        count = u32(cursor)
        cursor += 4
        if count > 1023 or cursor+4*count > len(head):
            raise ValueError("Unsupported sketch pattern suppression list count")
        ordinals = [u32(cursor+4*i) for i in range(count)]
        if len(set(ordinals)) != count:
            raise ValueError("Duplicate sketch pattern suppressed ordinals")
        return ordinals, cursor+4*count

    def scoped(identity, owner, allowed=None):
        item = entities.get(identity)
        if item is None or item["sketch_object_id"] != owner or (allowed and item["kind"] not in allowed):
            raise ValueError("Sketch pattern entity does not resolve in its owner/kind")
        return item

    def parameter(owner, identity, suffix):
        sketch = sketches[owner]
        matches = [p for p in sketch["parameters"] if p["binding_object_id"] == identity and p["role"].endswith(suffix)]
        if len(matches) != 1 or not math.isfinite(matches[0]["raw_float64"]):
            raise ValueError("Sketch pattern parameter binding unresolved: "+suffix)
        return matches[0]

    direction_ids, direction_selections = [], []
    if record.class_guid == CIRCULAR:
        quantity = struct.unpack_from("<Q", head, 30)[0]
        if not 2 <= quantity <= 1024:
            raise ValueError("Unsupported sketch circular pattern quantity")
        suppressed, cursor = suppression(38)
        if head[cursor] not in (0, 1):
            raise ValueError("Unsupported sketch circular symmetry flag")
        symmetric = bool(head[cursor])
        owner = reference(head, cursor+1)
        angle = parameter(owner, reference(head, 0), "-Angle")
        count = parameter(owner, reference(head, 11), "-Count")
        if count["raw_float64"] != quantity or not math.isclose(numbers(head, 22, 1)[0], angle["raw_float64"], abs_tol=1e-9):
            raise ValueError("Circular sketch pattern cached parameters disagree")
        code_offset, list_offset = cursor+12, cursor+24
        expected_code, total = 0x10000000, quantity
        result = {"kind": "SketchCircularPattern", "quantity": quantity,
                  "total_angle_radians": angle["raw_float64"], "is_symmetric": symmetric}
        seed_genesis, created_genesis = 258, 256
    else:
        if any(v not in (0, 1) for v in head[:3]):
            raise ValueError("Unsupported sketch rectangular flags")
        direction_count = u32(3)
        if direction_count not in (0, 2):
            raise ValueError("Only observed default axes or two explicit sketch directions supported")
        direction_ids = [reference(head, 7+11*i) for i in range(direction_count)]
        if len(set(direction_ids)) != direction_count:
            raise ValueError("Duplicate rectangular sketch direction selections")
        cursor = 7+11*direction_count
        if head[cursor:cursor+4] != b"\0"*4:
            raise ValueError("Unobserved rectangular sketch direction reserved field")
        suppressed, cursor = suppression(cursor+4)
        owner = reference(head, cursor+116)
        result = {"kind": "SketchRectangularPattern", "distance_type": "Extent" if head[0] else "Spacing",
                  "symmetric_one": bool(head[1]), "symmetric_two": bool(head[2])}
        for side, shift, letter in (("one", 0, "u"), ("two", 58, "v")):
            position = cursor+shift
            quantity = u32(position)
            count = parameter(owner, reference(head, position+4), "-"+letter+"Count")
            distance = parameter(owner, reference(head, position+47), "-"+letter+"Distance")
            if (not 1 <= quantity <= 1024 or count["raw_float64"] != quantity
                    or not math.isclose(numbers(head, position+39, 1)[0], distance["raw_float64"], abs_tol=1e-9)):
                raise ValueError("Rectangular sketch pattern cached parameters disagree")
            result["quantity_"+side] = quantity
            result["distance_"+side+"_cm"] = distance["raw_float64"]
            result["direction_"+side] = numbers(head, position+15, 3)
        total = result["quantity_one"]*result["quantity_two"]
        if not 2 <= total <= 1024:
            raise ValueError("Unsupported rectangular sketch total instance count")
        for index, side in enumerate(("one", "two")):
            if direction_ids:
                line = scoped(direction_ids[index], owner, ("Line",))
                vector = [b-a for a, b in zip(line["start_cm"], line["end_cm"])]
                magnitude = math.sqrt(sum(v*v for v in vector))
                if magnitude <= 0 or not same(result["direction_"+side], [v/magnitude for v in vector]):
                    raise ValueError("Rectangular sketch selected direction and stored vector disagree")
                direction_selections.append({"direction": side, "entity_object_id": line["object_id"],
                                             "entity_tag": line["entity_tag"], "kind": "Line"})
            elif not same(result["direction_"+side], [1, 0, 0] if index == 0 else [0, 1, 0]):
                raise ValueError("Unobserved rectangular sketch implicit direction")
        code_offset, list_offset = cursor+127, cursor+139
        expected_code = 0x20000000
        seed_genesis, created_genesis = 130, 128
        result["direction_selections"] = direction_selections
    if suppressed and (result.get("is_symmetric") or result.get("symmetric_one") or result.get("symmetric_two")):
        raise ValueError("Symmetric sketch pattern suppression ordinal mapping remains unverified")
    if any(not 1 <= ordinal < total for ordinal in suppressed):
        raise ValueError("Sketch pattern suppression ordinal outside non-seed domain")
    if struct.unpack_from("<Q", head, code_offset)[0] != expected_code:
        raise ValueError("Unsupported sketch pattern kind code")
    member_count = u32(list_offset-4)
    if not 2 <= member_count <= 1024 or len(head) != list_offset+11*member_count+1 or head[-1] != 0:
        raise ValueError("Unsupported sketch pattern role-list framing")
    roles = [reference(head, list_offset+11*i) for i in range(member_count)]
    if len(set(roles)) != member_count or set(roles)&set(direction_ids):
        raise ValueError("Duplicate or overlapping sketch pattern member/direction roles")
    if Counter(roles+direction_ids) != Counter(dependencies):
        raise ValueError("Sketch pattern dependency and member/direction lists disagree")
    copied = roles
    if record.class_guid == CIRCULAR:
        center = scoped(roles[-1], owner, ("Point",))
        result.update(center_entity_id=roles[-1], center_cm=center["position_cm"])
        copied = roles[:-1]
    active_instances = total-len(suppressed)
    if len(copied)%active_instances or not copied:
        raise ValueError("Sketch pattern member count does not divide active instances")
    seed_count = len(copied)//active_instances
    seeds, created = copied[:seed_count], copied[seed_count:]
    seed_geometry = [scoped(identity, owner, ("Line", "Circle")) for identity in seeds]
    if any(g.get("entity_genesis") != seed_genesis for g in seed_geometry):
        raise ValueError("Sketch pattern seed-prefix genesis flags disagree")
    for identity in created:
        if scoped(identity, owner, ("Line", "Circle")).get("entity_genesis") != created_genesis:
            raise ValueError("Sketch pattern created-member genesis flags disagree")
    groups, position = [], 0
    suppressed_set = set(suppressed)
    for ordinal in range(total):
        is_suppressed = ordinal in suppressed_set
        identities = [] if is_suppressed else copied[position:position+seed_count]
        if not is_suppressed:
            position += seed_count
        associations = []
        for column, identity in enumerate(identities):
            geometry = scoped(identity, owner, ("Line", "Circle"))
            source = seed_geometry[column]
            if geometry["kind"] != source["kind"]:
                raise ValueError("Sketch pattern grouped member kind disagrees with seed")
            if geometry["kind"] == "Circle" and not math.isclose(geometry["radius_cm"], source["radius_cm"], abs_tol=1e-9):
                raise ValueError("Sketch pattern grouped circle radius disagrees with seed")
            associations.append({"seed_entity_id": seeds[column], "entity_id": identity, "kind": geometry["kind"]})
        groups.append({"instance_ordinal": ordinal, "is_seed_instance": ordinal == 0,
                       "is_suppressed": is_suppressed, "entity_ids": identities, "seed_associations": associations})
    result.update(object_id=record.object_id, entity_ids=seeds, created_entity_ids=created,
                  seed_entity_count=seed_count,
                  instance_count=total, instance_groups=groups,
                  suppressed_instance_ordinals=suppressed,
                  is_suppressed=[ordinal in suppressed_set for ordinal in range(1, total)],
                  suppression_status="Explicit native non-seed ordinal list decoded; suppressed members are absent from the active role list",
                  membership_status="Observed seed prefix and active instance-major role groups; associations follow stored positions, not geometric matching",
                  record_offset=record.start, class_guid=record.class_guid)
    return result, owner
