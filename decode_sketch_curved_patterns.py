"""Observed curved sketch-pattern memberships and missing owned geometry.

Uses the standard native controller/binding/order reader. Curves are resolved by
explicit IDs; geometric consistency checks never assign pattern identities.
"""

import math
import struct

from decode_nurbs import decode_spline
from decode_sketch import attributes, constraint_prefix, numbers, reference, same
from decode_sketch_pattern_modes import CIRCULAR, RECTANGULAR, decode_sketch_pattern


ARC = "F0130424-8B7E-4092-93C9-1CA807482534"
ELLIPSE = "FF23079A-D99C-47AB-940E-2F4E18F022AB"
FITTED = "D82E012F-6DDD-4AED-BDE1-C0F7F9100B9B"


def decode_sketch_curved_patterns(data, records, features):
    """Return patterns/additional_geometry/unresolved without mutating features.

    Additional geometry is published only after its owning pattern passes common
    framing and the curved validation below. Already decoded geometry stays in
    the caller's output; only missing geometry is returned for merging.
    """
    primary = {r.object_id: r for r in records if r.is_primary}
    sketches = {f["sketch_object_id"]: f for f in features if f["kind"] == "Sketch"}
    entities = {g["object_id"]: g for s in sketches.values() for g in s.get("geometry", [])}
    patterns, additional, unresolved = [], {}, []

    def ellipse(record, props, cursor):
        body = data[record.body:record.end]
        if len(body)-cursor not in (172, 192):
            raise ValueError("Unsupported patterned ellipse layout")
        owner = reference(body, len(body)-11)
        if owner not in sketches:
            raise ValueError("Patterned ellipse owner unresolved")
        values = numbers(body, cursor, 13)
        center_id = reference(body, cursor+104)
        center = entities.get(center_id)
        if (center is None or center["kind"] != "Point" or center["sketch_object_id"] != owner
                or not same(center["position_cm"], values[:3])):
            raise ValueError("Patterned ellipse center ownership or coordinates disagree")
        major, minor = values[3:6], values[6:9]
        if (not 0 < values[10] <= values[9]
                or not same([sum(x*x for x in major),sum(x*x for x in minor),sum(a*b for a,b in zip(major,minor))],[1,1,0])
                or not same(values[11:], [0,2*math.pi]) or body[cursor+115] != 0):
            raise ValueError("Unsupported patterned ellipse axes/radii/interval")
        position, axes = cursor+116, []
        for _ in range(2):
            if body[position] == 0:
                axes.append(None)
                position += 1
            else:
                identity = reference(body, position)
                axis = entities.get(identity)
                if axis is None or axis["kind"] != "Line" or axis["sketch_object_id"] != owner:
                    raise ValueError("Patterned ellipse axis-line owner unresolved")
                axes.append(identity)
                position += 11
        if len(body)-position != 54 or ((len(body)-cursor == 172) != (axes == [None,None])):
            raise ValueError("Unobserved optional ellipse axis-line framing")
        return {"kind": "Ellipse", "object_id": record.object_id, "entity_tag": props["crv_primary_id"],
                "entity_genesis": props["EntityGenesis"], "sketch_object_id": owner,
                "record_offset": record.start, "center_point_id": center_id, "center_cm": values[:3],
                "major_radius_cm": values[9], "minor_radius_cm": values[10],
                "stored_major_axis": major, "stored_minor_axis": minor,
                "major_axis_entity_id": axes[0], "minor_axis_entity_id": axes[1],
                "axis_line_status": "Explicit optional native references; generated copies have both absent",
                "uninterpreted_style_hex": body[position:-11].hex()}

    for record in records:
        if not record.is_primary or record.class_guid not in (CIRCULAR,RECTANGULAR):
            continue
        try:
            body = data[record.body:record.end]
            dependencies, _, _ = constraint_prefix(body)
            # Circle and Arc share a native class. Only the already validated
            # Arc kind selects that class for this curved-pattern extension.
            curved = [primary[i] for i in dependencies if i in primary and (
                primary[i].class_guid in (ELLIPSE,FITTED)
                or (primary[i].class_guid == ARC and entities.get(i,{}).get("kind") == "Arc"))]
            if not curved:
                continue
            local, new, extras = dict(entities), {}, {}
            for curve in curved:
                payload = data[curve.body:curve.end]
                props, cursor = attributes(payload, 2)
                if payload[:2] != b"\0\x01" or props.get("crv_secondary_id") != 0:
                    raise ValueError("Unsupported patterned curve attributes")
                genesis = props.get("EntityGenesis")
                if genesis not in ((258,256) if record.class_guid == CIRCULAR else (130,128)):
                    raise ValueError("Patterned curve genesis does not match controller family")
                if curve.class_guid == ARC:
                    item = local.get(curve.object_id)
                    if item is None or item["kind"] != "Arc" or item["entity_tag"] != props["crv_primary_id"]:
                        raise ValueError("Patterned Arc has no validated primitive geometry")
                elif curve.class_guid == ELLIPSE:
                    item = ellipse(curve,props,cursor)
                    if genesis in (258,130):
                        extras[curve.object_id] = 4
                else:
                    if record.class_guid != RECTANGULAR or payload[cursor:] != b"\xff"*8:
                        raise ValueError("Only observed rectangular split fitted-spline layout supported")
                    continuation = [r for r in records if r.object_id == curve.object_id and r.start != curve.start]
                    item = decode_spline(data,records,curve,props,continuation,sketches,local)
                    if item["kind"] != "FittedSpline":
                        raise ValueError("Unobserved patterned spline source kind")
                    item["entity_genesis"] = genesis
                local[curve.object_id] = item
                if curve.object_id not in entities:
                    new[curve.object_id] = item
            pattern, owner = decode_sketch_pattern(data,record,sketches,local,
                member_kinds=("Arc","Ellipse","FittedSpline"),dependency_extras=extras)
            if pattern["seed_entity_count"] != 1 or pattern["suppressed_instance_ordinals"] or pattern.get("direction_selections"):
                raise ValueError("Only observed single curved seed/default direction/unsuppressed patterns supported")
            seed = local[pattern["entity_ids"][0]]
            members = pattern["entity_ids"] + pattern["created_entity_ids"]
            validation = []
            for identity in members:
                member = local[identity]
                if member["kind"] == "Arc":
                    if not same([member["radius_cm"],member["end_angle_radians"]-member["start_angle_radians"]],
                                [seed["radius_cm"],seed["end_angle_radians"]-seed["start_angle_radians"]]):
                        raise ValueError("Explicit Arc member radius/sweep differs from seed")
                    support = {"center_point_id":member["center_point_id"],"start_point_id":member["start_point_id"],"end_point_id":member["end_point_id"]}
                elif member["kind"] == "Ellipse":
                    if not same([member["major_radius_cm"],member["minor_radius_cm"]],[seed["major_radius_cm"],seed["minor_radius_cm"]]):
                        raise ValueError("Explicit Ellipse member radii differ from seed")
                    support = {"center_point_id":member["center_point_id"],"major_axis_entity_id":member.get("major_axis_entity_id"),"minor_axis_entity_id":member.get("minor_axis_entity_id")}
                else:
                    a,b = member["nurbs"],seed["nurbs"]
                    if a["degree"] != b["degree"] or not same(a["knots"],b["knots"]) or not same(a["weights"],b["weights"]) or len(a["control_points_cm"]) != len(b["control_points_cm"]):
                        raise ValueError("Explicit spline member NURBS schema differs from seed")
                    delta = [x-y for x,y in zip(member["start_cm"],seed["start_cm"])]
                    if not all(same(p,[x+y for x,y in zip(q,delta)]) for p,q in zip(a["control_points_cm"],b["control_points_cm"])):
                        raise ValueError("Explicit rectangular spline control points are not consistent translations")
                    support = {"fit_point_ids":member["fit_point_ids"],"geometry_record_offset":member["geometry_record_offset"]}
                validation.append({"entity_object_id":identity,"class_guid":primary[identity].class_guid,
                                   "kind":member["kind"],"entity_tag":member["entity_tag"],"support":support})
            pattern["sketch_object_id"] = owner
            pattern["curved_member_provenance"] = validation
            pattern["dependency_extra_status"] = "Seed Ellipse observed extra4 accepted by typed native ID; raw tag meaning unresolved; other slots zero"
            pattern["curved_geometry_status"] = "Native ordered IDs assign roles; owned primitive/NURBS shape checks independently validate explicit members"
            patterns.append(pattern)
            additional.update(new)
        except (ValueError,KeyError,IndexError,UnicodeError,struct.error) as error:
            unresolved.append({"object_id":record.object_id,"class_guid":record.class_guid,"reason":str(error)})
    return {"patterns":patterns,"additional_geometry":list(additional.values()),"unresolved":unresolved,
            "scope":"Observed single Arc/Ellipse circular/rectangular and rectangular FittedSpline patterns; native membership only, no geometric identity inference"}
