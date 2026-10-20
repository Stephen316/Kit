"""Observed local point-origin assembly joints and explicit motion limits.

Stored occurrence placements/context matrices are not a solved assembly state.
No kinematic solver, arbitrary joint geometry, or as-built joints are provided.
"""

from collections import Counter
import math
import struct
import uuid

from decode_parameters import read_string
from decode_placement import IDENTITY, rigid_matrix
from decode_selection import native_origin_entities, resolve_native_selection
from decode_sketch import numbers, reference, same


JOINT = "7F5A0426-1D2A-4DC4-9F06-58631F69D2F5"
DEFINITION = "8DFDD543-F823-43AA-BDAF-C638E023F0A0"
COLLECTION = "596C8B98-D176-4E40-B294-6404BAD566BC"
ORIGIN = "02E8AA49-08B8-439C-A8C7-221BE20143D8"
ORIGIN_GEOMETRY = "7B6C3C2D-4096-4E6D-B225-699E8C2D9355"
FRAME = "2E3AC990-483D-4A55-8662-C064B976A957"
ROUTE_WRAPPER = "FF415D89-A1DB-44AC-B824-E9A772B86ED4"
ROUTE = "96CBEA21-17E0-4BCB-BA77-04EA87B47934"
MOTION_TYPES = {0: (0, "Rigid"), 1: (1, "Revolute"), 2: (2, "Slider"),
                4: (3, "Cylindrical"), 6: (4, "PinSlot"), 7: (5, "Planar"), 8: (6, "Ball")}


def decode_joints(data, records, assembly, features=None):
    primary_groups = {}
    for record in records:
        if record.is_primary:
            primary_groups.setdefault(record.object_id, []).append(record)
    primary = {identity: values[0] for identity, values in primary_groups.items() if len(values) == 1}
    occurrences = {item["object_id"]: item for item in assembly["native_occurrences"]}
    components = {item["object_id"]: item for item in assembly["components"]}
    feature_map = {item["object_id"]: item for item in (features or [])}
    known_points = native_origin_entities(data, records)
    decoded, unresolved, collections = [], [], []

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError("Joint typed reference missing, ambiguous or wrong class: "+str(identity))
        return record, data[record.body:record.end]

    def uuid_text(payload, cursor):
        text, cursor = read_string(payload, cursor)
        if len(text) != 36:
            raise ValueError("Unsupported joint UUID field")
        uuid.UUID(text)
        return text, cursor

    def point_origin(identity):
        _, payload = typed(identity, ORIGIN)
        if len(payload) != 239 or payload[:4] != b"\0"*4:
            raise ValueError("Only observed native point JointOrigin records supported")
        geometry_id = reference(payload, 4)
        if reference(payload, 98) != geometry_id:
            raise ValueError("JointOrigin repeated geometry reference disagrees")
        _, geometry = typed(geometry_id, ORIGIN_GEOMETRY)
        if (len(geometry) != 204 or geometry[:36] != b"\0"*36
                or reference(geometry, 193) != identity):
            raise ValueError("JointOrigin geometry/owner layout unsupported")
        point_id, descriptor_id = reference(payload, 109), reference(payload, 120)
        if reference(geometry, 105) != point_id:
            raise ValueError("JointOrigin point reference copies disagree")
        _, point = typed(point_id, "69EE2FA7-BCC7-449E-9CA9-976CEFDFED44")
        if len(point) != 178 or reference(point, 167) != identity or reference(point, 79) != descriptor_id:
            raise ValueError("JointOrigin point descriptor/owner mismatch")
        _, descriptor = typed(descriptor_id, "5A1BF548-241F-46FD-9FB5-E4B05126EB9D")
        if reference(descriptor, len(descriptor)-11) != identity:
            raise ValueError("JointOrigin descriptor owner mismatch")
        selected = resolve_native_selection(data, records, point_id, known_points)
        if selected is None or selected["entity"]["kind"] != "ConstructionPoint":
            raise ValueError("Joint origin native construction point remains unresolved")
        entity = selected["entity"]
        container_id = entity["origin_container_object_id"]
        _, container = typed(container_id, "2972A3B8-3627-49BC-8C3D-18707605EC44")
        count = struct.unpack_from("<I", container, 4)[0]
        if container[:4] != b"\0"*4 or count > 32 or len(container) != 19+11*count:
            raise ValueError("Unsupported native origin container")
        members = [reference(container, 8+11*i) for i in range(count)]
        component_id = reference(container, 8+11*count)
        if entity["object_id"] not in members or component_id not in components:
            raise ValueError("Native joint point component membership unresolved")
        return {"joint_origin_object_id": identity, "geometry_object_id": geometry_id,
                "point_selection_object_id": point_id, "selection": selected,
                "component_object_id": component_id, "origin_container_object_id": container_id,
                "geometry_scope": "Explicit native component-origin point; arbitrary joint geometry/frames unsupported"}

    def context_frame(identity, owner_id, origin):
        _, payload = typed(identity, FRAME)
        if (len(payload) not in (78, 206) or payload[:20] != b"\0"*20
                or struct.unpack_from("<I", payload, 20)[0] != 3 or payload[24:37] != b"\0"*13):
            raise ValueError("Unsupported joint context frame")
        frame_link_id = reference(payload, 37)
        typed(frame_link_id, "549FBB80-B890-473E-A5C0-415D3D9BF4E6")
        if payload[48] == 0 and len(payload) == 206:
            matrix, cursor = rigid_matrix(numbers(payload, 49, 16)), 177
        elif payload[48] == 1 and len(payload) == 78:
            matrix, cursor = list(IDENTITY), 49
        else:
            raise ValueError("Unsupported joint context matrix encoding")
        if (payload[cursor] != 0 or reference(payload, cursor+1) != owner_id
                or payload[cursor+23:] != struct.pack("<I", 2)+b"\0\0"):
            raise ValueError("Joint context frame owner/footer mismatch")
        wrapper_id = reference(payload, cursor+12)
        _, wrapper = typed(wrapper_id, ROUTE_WRAPPER)
        if len(wrapper) != 18 or wrapper[:7] != bytes.fromhex("00000101000000"):
            raise ValueError("Unsupported joint context route wrapper")
        route_id = reference(wrapper, 7)
        _, route = typed(route_id, ROUTE)
        if len(route) != 406 or route[:6] != bytes.fromhex("000001000000"):
            raise ValueError("Only observed single-occurrence joint context routes supported")
        occurrence_uuid, cursor = uuid_text(route, 6)
        namespace, cursor = uuid_text(route, cursor)
        entity_uuid, cursor = uuid_text(route, cursor)
        if (namespace != origin["selection"]["namespace_text"]
                or entity_uuid != origin["selection"]["entity_guid_text"]
                or route[cursor:cursor+8] != struct.pack("<Q", 2)):
            raise ValueError("Joint context route disagrees with native origin point")
        namespace_two, cursor = uuid_text(route, cursor+8)
        endpoint_uuid, cursor = uuid_text(route, cursor)
        if namespace_two != namespace or route[cursor:] != struct.pack("<QI", 2, 0):
            raise ValueError("Unsupported joint route endpoint")
        matches = [item for item in occurrences.values() if item["instance_guid_text"] == occurrence_uuid]
        if len(matches) != 1 or matches[0]["component_object_id"] != origin["component_object_id"]:
            raise ValueError("Joint context occurrence and point component disagree")
        occurrence = matches[0]
        return {"object_id": identity, "frame_link_object_id": frame_link_id,
                "route_wrapper_object_id": wrapper_id, "route_object_id": route_id,
                "native_occurrence_object_id": occurrence["object_id"],
                "component_object_id": occurrence["component_object_id"],
                "component_name": components[occurrence["component_object_id"]]["name"],
                "instance_number": occurrence["instance_number"], "instance_guid_text": occurrence_uuid,
                "endpoint_uuid_text": endpoint_uuid, "stored_context_matrix": matrix,
                "matrix_scope": "Stored context matrix; not a solved occurrence placement or API Joint.geometry transform"}

    for record in primary.values():
        if record.class_guid != COLLECTION:
            continue
        payload = data[record.body:record.end]
        try:
            count = struct.unpack_from("<I", payload, 12)[0]
            if (payload[:6] != b"\0"*6 or payload[10:12] != b"\x01\0"
                    or count > 1024 or len(payload) != 27+11*count):
                raise ValueError("Unsupported native joint collection")
            identities = [reference(payload, 16+11*i) for i in range(count)]
            component_id = reference(payload, len(payload)-11)
            if component_id not in components or len(set(identities)) != count:
                raise ValueError("Joint collection component/membership unresolved")
            for identity in identities:
                _, joint = typed(identity, JOINT)
                if reference(joint, len(joint)-11) != record.object_id:
                    raise ValueError("Joint/collection ownership is not reciprocal")
            collections.append({"object_id": record.object_id, "joint_object_ids": identities,
                                "component_object_id": component_id,
                                "stored_header_field": struct.unpack_from("<I", payload, 6)[0]})
        except (ValueError, IndexError, struct.error) as error:
            unresolved.append({"object_id": record.object_id, "kind": "JointCollection", "reason": str(error)})
    collection_by_joint = {identity: item for item in collections for identity in item["joint_object_ids"]}

    for record in primary.values():
        if record.class_guid != DEFINITION:
            continue
        payload = data[record.body:record.end]
        try:
            if len(payload) < 534 or payload[:2] != b"\0\0" or payload[2] not in (0, 1) or payload[3:14] != b"\0"*11:
                raise ValueError("Unsupported Assemble joint definition prefix")
            origin_ids = [reference(payload, offset) for offset in (14, 108)]
            for offset in (25, 119):
                if payload[offset:offset+7] != b"\0"*6+b"\x01":
                    raise ValueError("Unsupported Assemble joint-origin reference layout")
                uuid_text(payload, offset+7)
            if payload[202:206] != b"\0"*4 or payload[217:219] != b"\0\0" or payload[252:254] != b"\0\0":
                raise ValueError("Unsupported Assemble alignment parameter separators")
            alignment_ids = [reference(payload, offset) for offset in (206, 230, 241, 219)]
            limit_count = struct.unpack_from("<I", payload, 254)[0]
            if limit_count > 18:
                raise ValueError("Unsupported enabled joint-limit parameter count")
            limit_ids = [reference(payload, 258+11*i) for i in range(limit_count)]
            cursor = 258+11*limit_count
            if struct.unpack_from("<I", payload, cursor)[0] != 2:
                raise ValueError("Expected two ordered joint context frames")
            context_ids = [reference(payload, cursor+4+11*i) for i in range(2)]
            joint_id = reference(payload, cursor+26)
            _, joint = typed(joint_id, JOINT)
            collection = collection_by_joint.get(joint_id)
            if collection is None or joint[:5] != bytes.fromhex("0102000000") or joint[35] != 0:
                raise ValueError("Native joint collection/prefix unresolved")
            definition_component = feature_map.get(record.object_id, {}).get("component_object_id")
            if definition_component is not None and definition_component != collection["component_object_id"]:
                raise ValueError("Assemble feature and native joint collection component owners disagree")
            member_ids = [reference(joint, 5), reference(joint, 20)]
            member_fields = [struct.unpack_from("<I", joint, offset)[0] for offset in (16, 31)]
            if any(identity not in occurrences for identity in member_ids):
                raise ValueError("Native joint references an unresolved occurrence")
            motion, cursor = [], 36
            for slot in range(6):
                count = struct.unpack_from("<I", joint, cursor)[0]
                cursor += 4
                if count not in (0, 1):
                    raise ValueError("Unsupported joint motion slot membership count")
                if not count:
                    continue
                if reference(joint, cursor) != joint_id:
                    raise ValueError("Joint motion entry self-owner mismatch")
                flags = joint[cursor+11:cursor+14]
                if any(flag not in (0, 1) for flag in flags) or joint[cursor+14] != 0:
                    raise ValueError("Unsupported joint motion limit flags")
                current, maximum, minimum, rest = numbers(joint, cursor+15, 4)
                motion.append({"slot_index": slot, "stored_axis_tag": struct.unpack_from("<I", joint, cursor+47)[0],
                               "current_value": current, "maximum_value": maximum, "minimum_value": minimum,
                               "rest_value": rest, "maximum_enabled": bool(flags[0]),
                               "minimum_enabled": bool(flags[1]), "rest_enabled": bool(flags[2])})
                cursor += 51
            native_code = struct.unpack_from("<I", joint, cursor)[0]
            if native_code not in MOTION_TYPES or joint[cursor+4:cursor+15] != bytes.fromhex("0001000000000200000000"):
                raise ValueError("Unobserved native joint motion type/trailer")
            api_code, kind = MOTION_TYPES[native_code]
            stored_matrix = rigid_matrix(numbers(joint, cursor+15, 16))
            tail = cursor+143
            name, end = read_string(joint, tail+79)
            if end+12 != len(joint) or joint[end] != 0 or reference(joint, end+1) != collection["object_id"]:
                raise ValueError("Native joint name/collection footer disagrees")
            slots = [item["slot_index"] for item in motion]
            expected_counts = {"Rigid": 0, "Revolute": 1, "Slider": 1, "Cylindrical": 2,
                               "PinSlot": 2, "Planar": 3, "Ball": 3}
            if len(motion) != expected_counts[kind]:
                raise ValueError("Native joint motion type/degree count disagree")
            labels, directions = [], {}
            if kind == "Rigid":
                pass
            elif kind == "Ball":
                if slots != [0, 1, 2] or [item["stored_axis_tag"] for item in motion] != [3, 4, 5]:
                    raise ValueError("Unsupported ball joint motion layout")
                labels = ["pitchLimits", "yawLimits", "rollLimits"]
            else:
                angular = [item for item in motion if item["slot_index"] < 3]
                linear = [item for item in motion if item["slot_index"] >= 3]
                required = {"Revolute": (1, 0), "Slider": (0, 1), "Cylindrical": (1, 1),
                            "PinSlot": (1, 1), "Planar": (1, 2)}[kind]
                if (len(angular), len(linear)) != required:
                    raise ValueError("Joint angular/linear degree partition disagrees")
                if any(item["stored_axis_tag"] != item["slot_index"]+(3 if item["slot_index"] >= 3 else 0) for item in motion):
                    raise ValueError("Unobserved native joint axis tags")
                if kind == "Planar":
                    labels = ["rotationLimits", "primarySlideLimits", "secondarySlideLimits"]
                    directions = {"normalDirection": angular[0]["slot_index"], "primarySlideDirection": linear[0]["slot_index"]-3}
                else:
                    labels = (["rotationLimits"] if angular else [])+(["slideLimits"] if linear else [])
                    if angular:
                        directions["rotationAxis"] = angular[0]["slot_index"]
                    if kind in ("Slider", "PinSlot"):
                        directions["slideDirection"] = linear[0]["slot_index"]-3
            for item, label in zip(motion, labels):
                item.update(limit_kind=label, units="cm" if item["slot_index"] >= 3 else "rad")
            origins = [point_origin(identity) for identity in origin_ids]
            contexts = [context_frame(identity, record.object_id, origin) for identity, origin in zip(context_ids, origins)]
            if set(member_ids) != {item["native_occurrence_object_id"] for item in contexts}:
                raise ValueError("Native joint occurrence members disagree with ordered Assemble contexts")
            if not same(contexts[0]["stored_context_matrix"], stored_matrix) or not same(contexts[1]["stored_context_matrix"], IDENTITY):
                raise ValueError("Observed stored joint/context matrix copies disagree")
            parameters = {item["binding_object_id"]: item for item in feature_map.get(record.object_id, {}).get("parameters", [])}

            def binding(identity):
                _, parameter_record = typed(identity, "D91D429C-1BB5-4640-B49F-69AF14F463E9")
                parameter = parameters.get(identity)
                if (parameter is None or len(parameter_record) != 85 or reference(parameter_record, 5) != record.object_id
                        or not math.isclose(numbers(parameter_record, 21, 1)[0], parameter["raw_float64"], abs_tol=1e-12)):
                    raise ValueError("Joint parameter explicit owner/value association unresolved")
                return parameter

            alignment = []
            for identity, role in zip(alignment_ids, ("alignAngle", "alignOffsetX", "alignOffsetY", "alignOffsetZ")):
                parameter = binding(identity)
                if parameter["role"] != role:
                    raise ValueError("Joint alignment parameter role disagrees")
                alignment.append({"binding_object_id": identity, "role": role, "value": parameter["raw_float64"]})
            limits = [binding(identity) for identity in limit_ids]
            expected = []
            for item in motion:
                prefix = {"rotationLimits": "Rotate", "slideLimits": "Slide", "primarySlideLimits": "Slide",
                          "secondarySlideLimits": "Slide", "pitchLimits": "Pitch", "yawLimits": "Yaw", "rollLimits": "Roll"}[item["limit_kind"]]
                for field, suffix in (("minimum", "Minimum"), ("maximum", "Maximum"), ("rest", "Rest")):
                    if item[field+"_enabled"]:
                        expected.append((prefix+suffix, item[field+"_value"]))
            if Counter((item["role"], item["raw_float64"]) for item in limits) != Counter(expected):
                raise ValueError("Enabled joint-limit parameters disagree with cached native motion values/flags")
            decoded.append({"object_id": joint_id, "name": name, "definition_object_id": record.object_id,
                            "collection_object_id": collection["object_id"], "component_object_id": collection["component_object_id"],
                            "joint_type": kind, "api_joint_type_code": api_code, "stored_joint_type_code": native_code,
                            "is_flipped": bool(payload[2]), "alignment_parameters": alignment,
                            "motion_limits": motion, "direction_codes": directions,
                            "direction_scope": "Observed principal-axis motion slot mapping; custom direction and ball frame axes unresolved",
                            "origin_one": origins[0], "origin_two": origins[1], "context_one": contexts[0], "context_two": contexts[1],
                            "stored_occurrence_member_object_ids": member_ids, "stored_occurrence_member_fields": member_fields,
                            "stored_context_matrix": stored_matrix, "uninterpreted_joint_footer_hex": joint[tail:tail+79].hex(),
                            "enabled_limit_binding_object_ids": limit_ids,
                            "state_scope": "Locked/suppressed state semantics unverified; no kinematic solve or solved assembly/world placement"})
        except (ValueError, UnicodeError, IndexError, KeyError, struct.error) as error:
            unresolved.append({"object_id": record.object_id, "kind": "JointDefinition", "reason": str(error)})
    resolved_ids = {item["object_id"] for item in decoded}
    for record in primary.values():
        if record.class_guid == JOINT and record.object_id not in resolved_ids:
            unresolved.append({"object_id": record.object_id, "kind": "NativeJoint", "reason": "Native joint not resolved through a supported Assemble definition"})
    return {"decoded": decoded, "collections": collections, "unresolved": unresolved,
            "scope": "Observed local point-origin rigid/revolute/slider/cylindrical/pin-slot/planar/ball definitions and cached motion limits",
            "placement_limitation": "Native occurrence/context caches do not establish joint-solved placement; joint kinematics are not applied"}
