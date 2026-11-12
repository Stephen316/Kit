"""Observed Sweep Boolean inputs, two-sided fractions and rail active branch."""

import struct

from decode_assembly import COMPONENT_GUID, SKETCH_BASE_GUID, SKETCH_COLLECTION_GUID
from decode_body_selections import decode_body_selections
from decode_placement import rigid_matrix, transform_point
from decode_sketch import attributes, reference
from decode_sweep_modes import decode_sweep_modes


def decode_sweep_operations(data, records, body, feature, features):
    result = decode_sweep_modes(data, records, body, feature, features,
                                allowed_operation_codes=(1, 2, 3, 4), allow_two_sided=True)
    cursor = result["result_anchor_list_end_relative_offset"]
    if body[cursor:cursor+4] != b"\0"*4:
        raise ValueError("Unsupported Sweep post-anchor reserved field")
    count = struct.unpack_from("<I", body, cursor+4)[0]
    if count != (0 if result["stored_operation_code"] == 4 else 1):
        raise ValueError("Unobserved Sweep operation/input-body count")
    identities = [reference(body, cursor+8+11*i) for i in range(count)]
    if struct.unpack_from("<I", body, cursor+8+11*count)[0] != 36:
        raise ValueError("Unsupported Sweep post-input-list framing")
    selected = []
    if identities:
        summary = decode_body_selections(data, records)
        for identity in identities:
            proxies = [s for s in summary["selection_proxies"] if s["selection_record_object_id"] == identity
                       and s["owner_object_id"] == feature["object_id"]]
            if len(proxies) != 1 or len(proxies[0]["descriptor_object_ids"]) != 1:
                raise ValueError("Sweep input-body proxy/owner unresolved")
            descriptors = [d for d in summary["body_descriptors"] if d["object_id"] == proxies[0]["descriptor_object_ids"][0]
                           and d["owner_object_id"] == feature["object_id"]]
            if len(descriptors) != 1:
                raise ValueError("Sweep input-body descriptor/owner unresolved")
            descriptor = descriptors[0]
            selected.append({"selection_record_object_id": identity, "descriptor_object_id": descriptor["object_id"],
                             "native_body_object_id": descriptor["native_body_object_id"],
                             "body_anchor_object_id": descriptor["body_anchor_object_id"],
                             "source_owner_object_id": descriptor["source_owner_object_id"],
                             "association": "Counted Sweep input proxy with matching owner, descriptor and typed native body anchor"})
    result.update(input_body_selection_record_object_ids=identities, input_bodies=selected,
                  input_body_status="Observed one historical input body for Join/Cut/Intersect; exact result lifecycle and general participant lists unresolved")

    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: values[0] for identity, values in grouped.items() if len(values) == 1}

    def typed(identity, guid):
        if guid in (SKETCH_BASE_GUID, COMPONENT_GUID):
            matches = [r for r in records if r.object_id == identity and r.class_guid == guid]
            if len(matches) != 1 or identity not in primary:
                raise ValueError("Sweep inherited sketch/component fragment unresolved")
            record = matches[0]
            return data[record.body:record.end]
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError("Sweep context typed reference unresolved")
        return data[record.body:record.end]

    def sketch_context(identity):
        sketches = [f for f in features if f["kind"] == "Sketch" and f["sketch_object_id"] == identity]
        if len(sketches) != 1:
            raise ValueError("Sweep path/profile sketch context ambiguous")
        sketch = sketches[0]
        source = typed(identity, SKETCH_BASE_GUID)
        collection_id = reference(source, len(source)-11)
        collection = typed(collection_id, SKETCH_COLLECTION_GUID)
        if collection[:2] != b"\0\1":
            raise ValueError("Unobserved Sweep sketch collection prefix")
        props, start = attributes(collection, 2)
        count = struct.unpack_from("<I", collection, start)[0]
        if "crv_tag_id_idx" not in props or count > 100000 or start+4+11*count > len(collection)-11:
            raise ValueError("Unsupported Sweep component sketch collection")
        members = [reference(collection, start+4+11*i) for i in range(count)]
        if members.count(identity) != 1:
            raise ValueError("Sweep sketch/component reciprocal membership disagrees")
        component_id = reference(collection, len(collection)-11)
        typed(component_id, COMPONENT_GUID)
        matrix = rigid_matrix(sketch["placement"]["sketch_to_component_matrix"])
        return sketch, component_id, matrix

    source = result["path"]
    # Other previously observed shapes still retain the strict source reader's
    # results. Branch activity is added only for straight sketch lines here.
    if source["count"] != 1 or source["segments"][0]["kind"] != "Line":
        against = result["stored_parameter_values"]["AgainstDistance"]
        if against != 0 and not (source["is_closed"] and against == 1):
            raise ValueError("Unobserved non-Line Sweep two-sided context")
        return result
    profile_sketch, component_id, profile_matrix = sketch_context(result["profile"]["sketch_object_id"])
    origin = [profile_matrix[i] for i in (3, 7, 11)]
    normal = [profile_matrix[i] for i in (2, 6, 10)]

    def line_context(path):
        if path["count"] != 1 or path["segments"][0]["kind"] != "Line":
            raise ValueError("Unobserved Sweep two-sided non-Line path")
        segment = path["segments"][0]
        sketch, line_component, matrix = sketch_context(segment["sketch_object_id"])
        if line_component != component_id:
            raise ValueError("Sweep line/profile native components disagree")
        curves = [g for g in sketch["geometry"] if g["object_id"] == segment["curve_object_id"] and g["kind"] == "Line"]
        if len(curves) != 1:
            raise ValueError("Sweep source Line geometry unresolved")
        points = [transform_point(matrix, curves[0][key]) for key in ("start_cm", "end_cm")]
        signed = [sum((v-o)*n for v, o, n in zip(point, origin, normal)) for point in points]
        if abs(signed[1]-signed[0]) < 1e-9:
            raise ValueError("Unobserved Sweep path parallel to profile plane")
        fraction = -signed[0]/(signed[1]-signed[0])
        if not -1e-9 <= fraction <= 1+1e-9:
            raise ValueError("Sweep source Line misses profile plane")
        return {"sketch_object_id": sketch["sketch_object_id"], "curve_object_id": curves[0]["object_id"],
                "start_component_cm": points[0], "end_component_cm": points[1],
                "signed_endpoint_distances_to_profile_plane_cm": signed,
                "profile_plane_intersection_line_fraction": fraction,
                "extends_both_sides_of_profile_plane": signed[0]*signed[1] < -1e-18,
                "source_direction_matches_observed_branch_order": signed[0] < -1e-9 and signed[1] > 1e-9,
                "context_scope": "Same native component through reciprocal sketch collection; plane crossing does not reconstruct profile interiors"}

    context = line_context(source)
    along, against = (result["stored_parameter_values"][key] for key in ("AlongDistance", "AgainstDistance"))
    if (context["extends_both_sides_of_profile_plane"]
            and (not context["source_direction_matches_observed_branch_order"] or result["stored_mode_code"] not in (2, 3))):
        raise ValueError("Unobserved Sweep two-sided source direction/mode")
    if not context["extends_both_sides_of_profile_plane"] and against != 0:
        raise ValueError("Sweep against branch outside observed two-sided context")
    result["path_profile_context"] = {"component_object_id": component_id,
                                      "profile_sketch_object_id": profile_sketch["sketch_object_id"],
                                      "profile_origin_component_cm": origin, "profile_normal_component": normal,
                                      "path": context}
    if result["stored_mode_code"] == 2:
        result["distance_two_fraction"] = against if context["extends_both_sides_of_profile_plane"] else None
        result["distance_branch_status"] = "AlongDistance and AgainstDistance match API distanceOne/Two on captured normal-oriented straight two-sided path" if context["extends_both_sides_of_profile_plane"] else "Captured one-sided normal-oriented straight path"
    elif result["stored_mode_code"] == 3 and context["extends_both_sides_of_profile_plane"]:
        rail_context = line_context(result["stored_guide_rail"])
        if not rail_context["extends_both_sides_of_profile_plane"] or not rail_context["source_direction_matches_observed_branch_order"]:
            raise ValueError("Unobserved two-sided path with one-sided rail")
        if along > 0 and against == 0:
            flipped, active, fraction = True, "AlongDistance", along
        elif against > 0 and along == 0:
            flipped, active, fraction = False, "AgainstDistance", against
        else:
            raise ValueError("Unobserved two-sided rail active distance branches")
        result.update(is_direction_flipped=flipped, path_fraction=fraction, distance_two_fraction=None,
                      direction_flip_status="Observed API false/true contrast encoded by exclusive AgainstDistance/AlongDistance activation; no dedicated native flag claimed",
                      direction_branch={"active_parameter_role": active, "stored_along_fraction": along,
                                        "stored_against_fraction": against,
                                        "activity_scope": "Observed normal-oriented straight path and rail both cross profile plane in one native component"})
        result["path_profile_context"]["rail"] = rail_context
    return result
