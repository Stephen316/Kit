"""Resolve observed native-entity selection chains, without inferring topology."""

import struct
import uuid

from decode_parameters import read_string
from decode_sketch import attributes, numbers, reference, same
from decode_placement import cross


def native_origin_axes(data, records):
    axes = {}
    for record in records:
        body = data[record.body:record.end]
        try:
            if len(body) != 186 or body[:2] != b"\0\x01":
                continue
            props, cursor = attributes(body, 2)
            if props != {"EntityGenesis": 0}:
                continue
            origin, direction = numbers(body, cursor, 3), numbers(body, cursor+24, 3)
            name, _ = read_string(body, cursor+74)
            if name not in ("X", "Y", "Z"):
                continue
            expected = [float(i == "XYZ".index(name)) for i in range(3)]
            if not same(origin, [0, 0, 0]) or not same(direction, expected):
                continue
            axes[record.object_id] = {"kind": "ConstructionAxis", "name": name,
                                      "object_id": record.object_id, "origin_cm": origin,
                                      "direction": direction, "origin_container_object_id": reference(body, len(body)-11),
                                      "scope": "Native component origin axis; occurrence transforms unresolved"}
        except (ValueError, UnicodeError, struct.error):
            continue
    return axes


def native_origin_entities(data, records):
    known = native_origin_axes(data, records)
    expected = {"XY": [0., 0., 1.], "XZ": [0., 1., 0.], "YZ": [1., 0., 0.]}
    for record in records:
        body = data[record.body:record.end]
        try:
            if body[:2] != b"\0\x01":
                continue
            props, cursor = attributes(body, 2)
            if props != {"EntityGenesis": 0}:
                continue
            if record.class_guid == "8D424E29-DE23-4B1F-A3AD-84C52A497D1A" and len(body) == 233:
                coordinates = numbers(body, cursor+21, 9)
                origin, x_axis, y_axis = coordinates[:3], coordinates[3:6], coordinates[6:]
                normal = cross(x_axis, y_axis)
                name, _ = read_string(body, cursor+119)
                if name not in expected or not same(origin, [0, 0, 0]) or not same(normal, expected[name]):
                    continue
                entity = {"kind": "ConstructionPlane", "name": name, "origin_cm": origin,
                          "x_axis": x_axis, "y_axis": y_axis, "normal": normal}
            elif record.class_guid == "0E18EEF2-0D6F-480C-997E-5EBC7369AE5F" and len(body) == 146:
                position = numbers(body, cursor, 3)
                name, _ = read_string(body, cursor+34)
                if name != "O" or not same(position, [0, 0, 0]):
                    continue
                entity = {"kind": "ConstructionPoint", "name": name, "position_cm": position}
            else:
                continue
            entity.update(object_id=record.object_id,
                          origin_container_object_id=reference(body, len(body)-11),
                          scope="Native component origin entity; occurrence context unresolved")
            known[record.object_id] = entity
        except (ValueError, UnicodeError, struct.error):
            continue
    return known


def native_proxy_references(data, record):
    """Observed counted proxy list, including its optional numeric attributes."""
    body = data[record.body:record.end]
    if (record.class_guid != "2CA5A1CD-C99B-4C9B-91AF-57989148E841" or len(body) < 6
            or body[0] != 0 or body[1] not in (0, 1)):
        raise ValueError("Not an observed native selection proxy")
    props, cursor = attributes(body, 2) if body[1] else ({}, 2)
    count = struct.unpack_from("<I", body, cursor)[0]
    if not 1 <= count <= 1024 or len(body) != cursor+92+11*count:
        raise ValueError("Unsupported native proxy list layout")
    return [reference(body, cursor+4+11*i) for i in range(count)], props


def resolve_native_selection(data, records, selection_id, known_entities):
    candidates = []
    for proxy in records:
        if proxy.object_id != selection_id:
            continue
        body = data[proxy.body:proxy.end]
        try:
            if proxy.class_guid == "2CA5A1CD-C99B-4C9B-91AF-57989148E841":
                descriptors, _ = native_proxy_references(data, proxy)
                if len(descriptors) != 1:
                    continue
                descriptor_id = descriptors[0]
            elif (len(body) == 202 and body[:6] == b"\0\0\x08\0\0\0"
                  and struct.unpack_from("<I", body, 99)[0] == 1):
                descriptor_id = reference(body, 103)
            elif (len(body) == 178 and proxy.class_guid == "69EE2FA7-BCC7-449E-9CA9-976CEFDFED44"
                  and struct.unpack_from("<I", body, 75)[0] == 1):
                descriptor_id = reference(body, 79)
            else:
                continue
            for descriptor in records:
                if descriptor.object_id != descriptor_id:
                    continue
                chunk = data[descriptor.body:descriptor.end]
                if len(chunk) != 263 or chunk[:2] != b"\0\0":
                    continue
                leaf_id = reference(chunk, 2)
                if struct.unpack_from("<I", chunk, 13)[0] != 1:
                    continue
                namespace, cursor = read_string(chunk, 17)
                entity_guid, cursor = read_string(chunk, cursor)
                uuid.UUID(namespace)
                uuid.UUID(entity_guid)
                if len(namespace) != 36 or len(entity_guid) != 36:
                    continue
                for leaf in records:
                    if leaf.object_id != leaf_id:
                        continue
                    terminal = data[leaf.body:leaf.end]
                    if len(terminal) != 10 or terminal[:2] != b"\0\0":
                        continue
                    entity_id = struct.unpack_from("<Q", terminal, 2)[0]
                    if entity_id not in known_entities:
                        continue
                    candidates.append({
                        "entity": known_entities[entity_id],
                        "selection_object_id": selection_id, "descriptor_object_id": descriptor_id,
                        "terminal_object_id": leaf_id, "namespace_text": namespace,
                        "entity_guid_text": entity_guid,
                        "association": "Explicit selection -> descriptor -> native object reference chain",
                    })
        except (ValueError, UnicodeError, struct.error):
            continue
    return candidates[0] if len(candidates) == 1 else None


def known_construction_entities(data, records, features):
    known = native_origin_entities(data, records)
    for feature in features:
        if feature["kind"] == "ConstructionPlane" and "plane_object_id" in feature:
            known[feature["plane_object_id"]] = {
                "kind": "ConstructionPlane", "name": feature["name"],
                "object_id": feature["plane_object_id"], "feature_object_id": feature["object_id"],
                "origin_cm": feature["origin_cm"], "normal": feature["normal"],
            }
        elif feature["kind"] == "ConstructionAxis" and "axis_object_id" in feature:
            known[feature["axis_object_id"]] = {
                "kind": "ConstructionAxis", "name": feature["name"],
                "object_id": feature["axis_object_id"], "feature_object_id": feature["object_id"],
                "origin_cm": feature["origin_cm"], "direction": feature["direction"],
            }
        elif feature["kind"] == "ConstructionPoint" and "point_object_id" in feature:
            known[feature["point_object_id"]] = {
                "kind": "ConstructionPoint", "name": feature["name"],
                "object_id": feature["point_object_id"], "feature_object_id": feature["object_id"],
                "position_cm": feature["position_cm"],
            }
    return known


def decode_selections(data, records, features):
    known = known_construction_entities(data, records, features)
    resolved, unresolved = [], []
    for feature in features:
        if feature["kind"] == "Extrude":
            scopes = [feature.get("start", {}), feature.get("extent", {}).get("side_one", {}),
                      feature.get("extent", {}).get("side_two", {})]
            for scope in scopes:
                if scope.get("kind") != "FromEntity" and scope.get("condition") != "ToEntity":
                    continue
                identity = scope.get("selection_record_object_id")
                selection = resolve_native_selection(data, records, identity, known)
                if selection:
                    scope["selection"] = selection
                    scope["selection_status"] = "Observed native entity reference decoded"
                    resolved.append({"feature_object_id": feature["object_id"], "selection_object_id": identity})
                else:
                    unresolved.append({"feature_object_id": feature["object_id"], "selection_object_id": identity})
        elif feature["kind"] == "Revolve":
            try:
                identity = feature["revolve"]["axis_selection_record_object_id"]
                selection = resolve_native_selection(data, records, identity, known)
                if selection and selection["entity"]["kind"] == "ConstructionAxis":
                    feature["revolve"].update(axis_selection="Observed native construction axis reference decoded",
                                               axis=selection)
                    resolved.append({"feature_object_id": feature["object_id"], "selection_object_id": identity})
                else:
                    unresolved.append({"feature_object_id": feature["object_id"], "selection_object_id": identity})
                for side in ("side_one", "side_two"):
                    scope = feature["revolve"].get(side)
                    if not scope or scope.get("condition") != "ToEntity":
                        continue
                    identity = scope["selection_record_object_id"]
                    selection = resolve_native_selection(data, records, identity, known)
                    if selection and selection["entity"]["kind"] == "ConstructionPlane":
                        scope.update(selection=selection, selection_status="Observed construction-plane reference decoded")
                        resolved.append({"feature_object_id": feature["object_id"], "selection_object_id": identity})
                    else:
                        unresolved.append({"feature_object_id": feature["object_id"], "selection_object_id": identity})
            except (ValueError, KeyError, struct.error):
                continue
    return {"resolved": resolved, "unresolved": unresolved,
            "scope": "Observed native construction-plane and origin-axis selection chains; no face/edge topology"}
