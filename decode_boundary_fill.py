"""Observed Boundary Fill controls and typed selected-cell definitions.

Tool membership groups and face recipes are retained without resolving persistent
faces to ASM topology or treating native cell keys as API array indices.
"""

import struct

from decode_selection import native_proxy_references, resolve_native_selection
from decode_boundary_planes import resolve_boundary_plane_selection
from decode_sketch import attributes, reference


BOUNDARY_FILL_GUID = "49004167-470D-4892-B50E-5C589B1486D2"
CELL_GUID = "233D4E1B-1C2F-4622-96A0-0027622078CB"
PROXY_GUID = "2CA5A1CD-C99B-4C9B-91AF-57989148E841"
FACE_RECIPE_GUID = "7ACC2A03-0261-4879-A14A-A93D661A5BDC"
PLANE_RECIPE_GUID = "772DE81C-5009-4BB7-9D8C-54DBAF536216"


def counted_references(body, cursor):
    count = struct.unpack_from("<I", body, cursor)[0]
    if count > 1024 or cursor+4+11*count > len(body):
        raise ValueError("Unsupported Boundary Fill reference count")
    identities = [reference(body, cursor+4+11*i) for i in range(count)]
    if len(set(identities)) != count:
        raise ValueError("Duplicate Boundary Fill references")
    return identities, cursor+4+11*count


def decode_boundary_fill(data, records, body, feature, known=None):
    if (feature["class_guid"] != BOUNDARY_FILL_GUID or len(body) < 20
            or body[0] != 0 or body[1] not in (0, 1)):
        raise ValueError("Unsupported Boundary Fill class/prefix")
    props, cursor = attributes(body, 2) if body[1] else ({}, 2)
    if props:
        raise ValueError("Unobserved Boundary Fill attributes")
    operation = struct.unpack_from("<I", body, cursor)[0]
    if operation not in (1, 2, 3, 4) or body[cursor+4:cursor+8] != b"\0"*4:
        raise ValueError("Unsupported Boundary Fill operation/header")
    removal_ids, cursor = counted_references(body, cursor+8)
    remove = body[cursor]
    if remove not in (0, 1) or bool(remove) != bool(removal_ids):
        raise ValueError("Boundary Fill removal flag/list disagree")
    body_tools, cursor = counted_references(body, cursor+1)
    plane_tools, cursor = counted_references(body, cursor)
    if not body_tools or set(body_tools) & set(plane_tools):
        raise ValueError("Unsupported Boundary Fill tool partition")
    result_id = reference(body, cursor)
    selected_ids, cursor = counted_references(body, cursor+11)
    if not selected_ids:
        raise ValueError("Boundary Fill has no stored selected cells")
    selected_end = cursor

    def primary(identity, guid):
        candidates = [r for r in records if r.is_primary and r.object_id == identity and r.class_guid == guid]
        if len(candidates) != 1:
            raise ValueError("Boundary Fill typed reference unresolved: "+guid)
        record = candidates[0]
        return record, data[record.body:record.end]

    tool_inputs = []
    for identity in body_tools+plane_tools:
        record, payload = primary(identity, PROXY_GUID)
        if reference(payload, len(payload)-11) != feature["object_id"]:
            raise ValueError("Boundary Fill tool proxy owner disagrees with feature")
        try:
            descriptors, _ = native_proxy_references(data, record)
            context_status, context_bytes = "Observed shared proxy layout", None
        except ValueError:
            # NewComponent creates a different occurrence-context middle section.
            # Decode only the primary counted list; keep the rest explicitly opaque.
            if payload[:2] != b"\0\0" or len(payload) != 125:
                raise
            descriptors, after_primary = counted_references(payload, 2)
            if len(descriptors) != 1 or payload[after_primary:after_primary+1] != b"\1":
                raise ValueError("Unsupported Boundary Fill occurrence proxy prefix")
            context_status = "Primary descriptor retained; occurrence-context bytes unresolved"
            context_bytes = payload[after_primary:len(payload)-11].hex()
        if len(descriptors) != 1:
            raise ValueError("Only observed single-object Boundary Fill tools supported")
        descriptor_class = ("9716F783-676D-42E0-93F9-EBF273E7C035" if identity in body_tools
                            else "5A1BF548-241F-46FD-9FB5-E4B05126EB9D")
        _, descriptor = primary(descriptors[0], descriptor_class)
        if reference(descriptor, len(descriptor)-11) != feature["object_id"]:
            raise ValueError("Boundary Fill tool descriptor owner disagrees with feature")
        selection = resolve_native_selection(data, records, identity, known or {}) if identity in plane_tools else None
        plane_error = None
        if identity in plane_tools and selection is None:
            try:
                selection = resolve_boundary_plane_selection(data, records, identity, known or {}, feature["object_id"])
            except (ValueError, UnicodeError, IndexError, struct.error) as error:
                plane_error = str(error)
        item = {"selection_record_object_id": identity, "kind": "Body" if identity in body_tools else "ConstructionPlane",
                "descriptor_object_id": descriptors[0], "descriptor_class_guid": descriptor_class,
                "selection": selection, "proxy_status": context_status}
        if plane_error is not None:
            item["unresolved_plane_selection_reason"] = plane_error
        if context_bytes is not None:
            item["unresolved_proxy_context_hex"] = context_bytes
        tool_inputs.append(item)

    for identity in removal_ids:
        _, payload = primary(identity, "4A782808-FBDD-4351-A10A-F7AE5693D330")
        if reference(payload, len(payload)-12) != feature["object_id"] or payload[-1] != 0:
            raise ValueError("Boundary Fill RemoveBody parent link disagrees")
    _, result = primary(result_id, "5AC5B5CD-44C7-45B7-9CDC-F79B215A825D")
    if len(result) != 81 or reference(result, 2) != feature["object_id"] or reference(result, 70) != feature["object_id"]:
        raise ValueError("Boundary Fill result controller owner disagrees with feature")

    selected = []
    for identity in selected_ids:
        _, cell = primary(identity, CELL_GUID)
        if cell[:2] != b"\0\0" or cell[6:10] != b"\0"*4:
            raise ValueError("Unsupported Boundary Fill cell header")
        groups, position = [], 10
        for _ in range(5):
            group, position = counted_references(cell, position)
            groups.append(group)
        if position != len(cell):
            raise ValueError("Unconsumed Boundary Fill cell data")
        bodies_one, bodies_two, planes, faces, plane_recipes = groups
        if (set(bodies_one) & set(bodies_two) or set(bodies_one+bodies_two) != set(body_tools)
                or set(planes) != set(plane_tools) or len(plane_recipes) != len(planes) or not faces):
            raise ValueError("Boundary Fill cell/tool membership disagreement")
        recipes = []
        for recipe_id in faces:
            _, payload = primary(recipe_id, FACE_RECIPE_GUID)
            if b"face_recipe_data" not in payload:
                raise ValueError("Unobserved Boundary Fill face recipe payload")
            recipes.append({"object_id": recipe_id, "class_guid": FACE_RECIPE_GUID, "payload_hex": payload.hex()})
        plane_definitions = []
        for recipe_id in plane_recipes:
            _, payload = primary(recipe_id, PLANE_RECIPE_GUID)
            if len(payload) != 14 or payload[:2] != b"\0\0" or payload[2] not in (0, 1):
                raise ValueError("Unsupported Boundary Fill plane recipe")
            plane_id = reference(payload, 3)
            if plane_id not in planes:
                raise ValueError("Boundary Fill plane recipe/tool disagreement")
            plane_definitions.append({"object_id": recipe_id, "plane_selection_record_object_id": plane_id,
                                      "stored_side_flag": payload[2], "side_semantics": "Unresolved"})
        selected.append({"object_id": identity, "stored_cell_key": struct.unpack_from("<I", cell, 2)[0],
                         "body_tool_group_one_object_ids": bodies_one, "body_tool_group_two_object_ids": bodies_two,
                         "plane_tool_object_ids": planes, "face_recipes": recipes, "plane_recipes": plane_definitions,
                         "membership_scope": "Group one matches inside and group two outside for the observed closed boxes only",
                         "cell_key_scope": "Native key retained; not an API bRepCells array index",
                         "geometry_status": "Explicit selected-cell definition retained; boundaries are not rebuilt"})
    if len({c["stored_cell_key"] for c in selected}) != len(selected):
        raise ValueError("Duplicate Boundary Fill selected-cell keys")
    return {"operation": {1: "Join", 2: "Cut", 3: "Intersect", 4: "NewBody"}[operation],
            "stored_operation_code": operation, "is_remove_tools": bool(remove),
            "remove_body_feature_object_ids": removal_ids, "body_tool_count": len(body_tools),
            "plane_tool_count": len(plane_tools), "tools": tool_inputs,
            "selected_cell_count": len(selected), "selected_cells": selected,
            "result_controller_object_id": result_id,
            "selected_definition_end_offset": selected_end,
            "remaining_feature_bytes_scope": "Later shared feature metadata/auxiliary fields are not interpreted here",
            "selection_status": "Owned typed tool descriptors and chosen-cell memberships retained; face-to-ASM mapping unresolved",
            "operation_scope": "NewComponent creation normalizes this feature to NewBody and uses separate component wrappers",
            "geometry_status": "Controls/cell references decoded; Boolean cell generation is not implemented"}
