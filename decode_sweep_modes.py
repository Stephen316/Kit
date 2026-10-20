"""Observed Sweep rail/surface controls, composite paths and closed Circles."""

import math
import struct
import uuid

from decode_body_selections import decode_body_selections
from decode_brep_recipes import decode_recipe
from decode_parameters import read_string
from decode_profile_selections import resolve_sketch_profiles
from decode_selection import native_proxy_references
from decode_sketch import attributes, numbers, reference, same


SWEEP = "FCBB1707-4450-46B3-9E65-0F61682EA8CA"
PROXY = "2CA5A1CD-C99B-4C9B-91AF-57989148E841"
CURVE_DESCRIPTOR = "5A1BF548-241F-46FD-9FB5-E4B05126EB9D"
CURVE_LEAF = "E2CEFD18-D755-4E09-8E7F-953A2F6D43F8"


def decode_sweep_modes(data, records, body, feature, features, *, allowed_operation_codes=(4,), allow_two_sided=False,
                       profile_resolver=None, allowed_header_vectors=((1., 0., 0.),),
                       allowed_new_body_anchor_counts=(1,)):
    """Strict defaults; optional observed operations/branches serve the wrapper."""
    allowed_operation_codes = tuple(allowed_operation_codes)
    allowed_header_vectors = tuple(tuple(v) for v in allowed_header_vectors)
    allowed_new_body_anchor_counts = tuple(allowed_new_body_anchor_counts)
    if (not allowed_header_vectors or any(len(v) != 3 or not all(math.isfinite(x) for x in v) for v in allowed_header_vectors)
            or not allowed_new_body_anchor_counts or len(set(allowed_new_body_anchor_counts)) != len(allowed_new_body_anchor_counts)
            or any(type(count) is not int or count not in (1, 2) for count in allowed_new_body_anchor_counts)
            or (profile_resolver is not None and not callable(profile_resolver))):
        raise ValueError("Unsupported Sweep profile reader options")
    if (not allowed_operation_codes or len(set(allowed_operation_codes)) != len(allowed_operation_codes)
            or any(code not in (1, 2, 3, 4) for code in allowed_operation_codes)
            or type(allow_two_sided) is not bool):
        raise ValueError("Unsupported Sweep reader operation/branch options")
    if (feature["class_guid"] != SWEEP or len(body) < 170
            or body[0] != 0 or body[1] not in (0, 1)):
        raise ValueError("Unsupported Sweep mode class/prefix")
    props, base = attributes(body, 2) if body[1] else ({}, 2)
    operation = struct.unpack_from("<I", body, base)[0]
    if (props or operation not in allowed_operation_codes or body[base+4] not in (0, 1)
            or body[base+5:base+11] != struct.pack("<I", 3)+b"\0\0"
            or body[base+11] not in (0, 1)
            or tuple(numbers(body, base+14, 3)) not in allowed_header_vectors):
        raise ValueError("Unsupported observed Sweep mode control header")
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {i: values[0] for i, values in grouped.items() if len(values) == 1}
    owner = feature["object_id"]

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError("Sweep mode typed reference unresolved: "+guid)
        return record, data[record.body:record.end]

    def owned(identity, guid):
        record, payload = typed(identity, guid)
        if reference(payload, len(payload)-11) != owner:
            raise ValueError("Sweep mode selection owner disagrees")
        return record, payload

    def optional(cursor):
        if cursor >= len(body):
            raise ValueError("Truncated Sweep optional selection")
        return (None, cursor+1) if body[cursor] == 0 else (reference(body, cursor), cursor+11)

    bindings = {p["binding_object_id"]: p for p in feature["parameters"]}
    values, binding_ids = {}, {}

    def parameter(offset, role):
        identity = reference(body, offset)
        parameter = bindings.get(identity)
        if parameter is None or parameter["role"] != role or not math.isfinite(parameter["raw_float64"]):
            raise ValueError("Sweep mode parameter binding/role disagrees: "+role)
        values[role], binding_ids[role] = parameter["raw_float64"], identity

    for offset, role in ((38, "AgainstDistance"), (49, "AgainstRailDistance"),
                         (60, "AlongDistance"), (71, "AlongRailDistance")):
        parameter(base+offset, role)
    surface_id, cursor = optional(base+82)
    path_id, cursor = reference(body, cursor), cursor+11
    rail_id, cursor = optional(cursor)
    control_id, cursor = reference(body, cursor), cursor+11
    _, control = typed(control_id, "B3E4AB56-412B-45EA-85E5-79BE88865B41")
    control_count = struct.unpack_from("<I", control, 17)[0]
    if (control_count not in allowed_new_body_anchor_counts or len(control) != 74+11*control_count
            or reference(control, 6) != owner or reference(control, len(control)-11) != owner):
        raise ValueError("Sweep mode result control owner/layout disagrees")
    control_context_ids = [reference(control, 21+11*i) for i in range(control_count)]
    if len(set(control_context_ids)) != control_count:
        raise ValueError("Duplicate Sweep result control context references")
    parameter(cursor, "TaperAngle")
    parameter(cursor+11, "TwistAngle")
    mode = struct.unpack_from("<I", body, cursor+22)[0]
    count = struct.unpack_from("<I", body, cursor+26)[0]
    if mode not in (1, 2, 3, 4, 5) or count != 1:
        raise ValueError("Unsupported Sweep mode/profile count")
    profile_id = reference(body, cursor+30)
    resolver = resolve_sketch_profiles if profile_resolver is None else profile_resolver
    profiles = resolver(data, records, profile_id, owner, features)
    if (profile_resolver is None and len(profiles) != 1) or (profile_resolver is not None and len(profiles) not in (1, 2)):
        raise ValueError("Unsupported Sweep resolved profile count")
    after_profile = cursor+41
    anchor_count = struct.unpack_from("<I", body, after_profile+4)[0]
    if (body[after_profile:after_profile+4] != b"\0"*4
            or anchor_count not in (allowed_new_body_anchor_counts if operation == 4 else (0,))):
        raise ValueError("Unsupported Sweep mode result-anchor list")
    anchor_ids = [reference(body, after_profile+8+11*i) for i in range(anchor_count)]
    anchor_map = {a["object_id"]: a for a in decode_body_selections(data, records)["body_anchors"]}
    if any(i not in anchor_map or anchor_map[i]["source_owner_object_id"] != owner for i in anchor_ids):
        raise ValueError("Sweep result native body anchor unresolved or owner disagrees")
    if profile_resolver is not None:
        if operation == 4 and control_count != anchor_count:
            raise ValueError("Sweep result control/context count disagrees with observed result-anchor count")
        for context_id in control_context_ids:
            _, context_payload = typed(context_id, "C46D3EEB-40E1-43FA-83DC-9CB204335417")
            if len(context_payload) != 171:
                raise ValueError("Unsupported Sweep result control context payload")

    def path(identity):
        record, _ = owned(identity, PROXY)
        descriptors, selection_props = native_proxy_references(data, record)
        if selection_props or len(set(descriptors)) != len(descriptors):
            raise ValueError("Unsupported Sweep path proxy attributes/duplicates")
        segments, geometries = [], []
        for index, descriptor_id in enumerate(descriptors):
            _, payload = owned(descriptor_id, CURVE_DESCRIPTOR)
            if len(payload) != 263 or payload[:2] != b"\0\0":
                raise ValueError("Unsupported Sweep path descriptor layout")
            leaf_id = reference(payload, 2)
            _, leaf = typed(leaf_id, CURVE_LEAF)
            if len(leaf) != 26 or leaf[:10] != b"\0"*10:
                raise ValueError("Unsupported Sweep path sketch-curve leaf")
            sketch_id, tag = struct.unpack_from("<QQ", leaf, 10)
            sketches = [f for f in features if f["kind"] == "Sketch" and f["sketch_object_id"] == sketch_id]
            curves = [g for f in sketches for g in f["geometry"] if g.get("entity_tag") == tag and g["kind"] in ("Line", "Arc", "Circle")]
            if len(sketches) != 1 or len(curves) != 1:
                raise ValueError("Sweep path sketch/curve tag unresolved or ambiguous")
            curve = curves[0]
            segments.append({"index": index, "descriptor_object_id": descriptor_id, "terminal_object_id": leaf_id,
                             "sketch_object_id": sketch_id, "sketch_name": sketches[0]["name"],
                             "curve_object_id": curve["object_id"], "curve_entity_tag": tag, "kind": curve["kind"]})
            geometries.append(curve)
        kinds = [s["kind"] for s in segments]
        if len(kinds) == 1:
            closed = kinds == ["Circle"]
            if not closed and same(geometries[0]["start_cm"], geometries[0]["end_cm"]):
                raise ValueError("Unobserved Sweep closed Line/Arc source")
        elif (kinds == ["Line", "Arc"] and same(geometries[0]["end_cm"], geometries[1]["start_cm"])
                and not same(geometries[1]["end_cm"], geometries[0]["start_cm"])):
            closed = False
        else:
            raise ValueError("Unobserved Sweep composite source sequence/endpoint copies")
        return {"selection_record_object_id": identity, "count": len(segments), "segments": segments,
                "is_closed": closed,
                "order_scope": "Explicit descriptor list order; API traversal reversal flags and general trim reconstruction unresolved",
                "closure_scope": "Observed single Circle is closed; single Line/Arc or joined Line-Arc samples are open; no general native closure flag claimed"}

    source_path = path(path_id)
    is_rail, is_surface = mode in (3, 4), mode == 5
    if ((is_rail and (rail_id is None or surface_id is not None))
            or (is_surface and (surface_id is None or rail_id is not None))
            or (mode in (1, 2) and (rail_id is not None or surface_id is not None))):
        raise ValueError("Sweep mode disagrees with explicit guide selections")
    if (any(not 0 <= values[r] <= 1 for r in ("AlongDistance", "AgainstDistance", "AlongRailDistance", "AgainstRailDistance"))
            or (not allow_two_sided and values["AgainstDistance"] != 0
                and not (source_path["is_closed"] and values["AgainstDistance"] == 1))):
        raise ValueError("Unobserved Sweep mode distance fractions")
    stored_rail = path(rail_id) if rail_id is not None else None
    scaling_bits = tuple(body[base+12:base+14])
    scaling = {(1, 1): "Scale", (1, 0): "Stretch", (0, 0): "NoScaling"}.get(scaling_bits)
    if scaling is None or (not is_rail and scaling_bits != (1, 1)):
        raise ValueError("Unobserved Sweep profile scaling bits")

    surfaces = []
    if is_surface:
        record, _ = owned(surface_id, PROXY)
        descriptor_ids, attrs = native_proxy_references(data, record)
        if attrs or len(descriptor_ids) != 1:
            raise ValueError("Only observed one-face guide surface supported")
        for identity in descriptor_ids:
            _, payload = owned(identity, "5662F619-2281-4AD9-93DC-1FCFDA1062E7")
            if payload[:4] != b"\0"*4 or struct.unpack_from("<I", payload, 15)[0] != 1:
                raise ValueError("Unsupported Sweep guide face descriptor")
            recipe_id = reference(payload, 4)
            namespace, pos = read_string(payload, 19)
            entity_uuid, pos = read_string(payload, pos)
            if len(namespace) != 36 or len(entity_uuid) != 36:
                raise ValueError("Unsupported Sweep guide face namespace lengths")
            uuid.UUID(namespace)
            uuid.UUID(entity_uuid)
            context_count = struct.unpack_from("<I", payload, pos+8)[0]
            if struct.unpack_from("<Q", payload, pos)[0] != 2 or context_count not in (0, 1):
                raise ValueError("Unobserved Sweep guide face association/context")
            context_ids = [reference(payload, pos+12+11*i) for i in range(context_count)]
            for context_id in context_ids:
                typed(context_id, "C46D3EEB-40E1-43FA-83DC-9CB204335417")
            pos += 12+11*context_count
            if struct.unpack_from("<I", payload, pos)[0] != 1 or len(payload)-(pos+15) != 67:
                raise ValueError("Unsupported Sweep guide face anchor/trailer")
            source_anchor_id = reference(payload, pos+4)
            anchor = anchor_map.get(source_anchor_id)
            if anchor is None:
                raise ValueError("Sweep guide face native body unresolved")
            recipe_record, _ = typed(recipe_id, "7ACC2A03-0261-4879-A14A-A93D661A5BDC")
            recipe = decode_recipe(data, recipe_record, primary)
            if recipe["payload_kind"] != "bounded_face_recipe_data":
                raise ValueError("Unobserved Sweep guide face recipe kind")
            surfaces.append({"selection_record_object_id": surface_id, "descriptor_object_id": identity,
                             "recipe": recipe, "body_anchor_object_id": source_anchor_id,
                             "native_body_object_id": anchor["native_body_object_id"],
                             "source_owner_object_id": anchor["source_owner_object_id"],
                             "context_record_object_ids": context_ids,
                             "context_scope": "Explicit native context identities retained; occurrence transforms unresolved",
                             "namespace_text": namespace, "entity_uuid_text": entity_uuid,
                             "face_identity_scope": "Explicit historical native body and persistent face recipe; exact ASM face identity unresolved"})
    guided = is_rail or is_surface
    result = {"operation": {1: "Join", 2: "Cut", 3: "Intersect", 4: "NewBody"}[operation],
            "stored_operation_code": operation, "is_solid": bool(body[base+11]),
            "sweep_mode": {1: "SinglePathParallel", 2: "SinglePathPerpendicular", 3: "GuideRailPerpendicularExtent", 4: "GuideRailFullExtents", 5: "GuideSurface"}[mode],
            "stored_mode_code": mode,
            "orientation": None if guided else {1: "Parallel", 2: "Perpendicular"}[mode],
            "orientation_status": "Inactive guide mode; actual API getter raises InternalValidationError" if guided else "Observed single-path enum",
            "path_fraction": values["AlongDistance"], "stored_against_path_fraction": values["AgainstDistance"],
            "distance_two_fraction": values["AgainstDistance"] if source_path["is_closed"] else None,
            "stored_parameter_values": values, "parameter_bindings": binding_ids,
            "taper_angle_radians": None if guided or mode == 1 else values["TaperAngle"],
            "twist_angle_radians": None if guided or mode == 1 else values["TwistAngle"],
            "angle_control_status": "SDK ignores taper/twist in guide modes; native bindings retained" if guided else "Single-path orientation controls activity",
            "path": source_path, "profile": profiles[0] if len(profiles) == 1 else None,
            "profile_scaling": scaling if is_rail else None, "stored_scaling_bits": list(scaling_bits),
            "extent": {3: "PerpendicularToPath", 4: "FullExtents"}.get(mode),
            "guide_rail": stored_rail if mode == 3 else None, "stored_guide_rail": stored_rail,
            "guide_rail_status": "FullExtents retains a native rail selection although actual API guideRail getter returned None in captured case" if mode == 4 else "Explicit native rail selection" if mode == 3 else "No rail selection",
            "guide_surfaces": surfaces, "is_chain_selection": bool(body[base+4]) if is_surface else None,
            "stored_chain_selection_flag": body[base+4],
            "is_direction_flipped": None,
            "direction_flip_status": "Native flag unverified; API returned true for one-sided rails where SDK says it is inapplicable",
            "result_control_record_object_id": control_id, "uninterpreted_result_control_prefix_hex": control[:6].hex(),
            "result_body_anchors": [anchor_map[i] for i in anchor_ids],
            "input_selection_status": "Explicit sketch profile/path/rail membership and guide-face historical body references; general path traversal, trims and persistent face mapping unresolved"}
    if profile_resolver is not None:
        result["profiles"] = profiles
        result["stored_header_vector"] = numbers(body, base+14, 3)
        result["result_control_context_record_object_ids"] = control_context_ids
    if allowed_operation_codes != (4,) or allow_two_sided or profile_resolver is not None:
        result["result_anchor_list_end_relative_offset"] = after_profile+8+11*anchor_count
    return result
