"""Resolve observed native-entity selection chains, without inferring topology."""

import struct
import uuid

from decode_parameters import read_string
from decode_sketch import attributes, numbers, reference, same


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


def resolve_native_selection(data, records, selection_id, known_entities):
    candidates = []
    for proxy in records:
        if proxy.object_id != selection_id:
            continue
        body = data[proxy.body:proxy.end]
        try:
            if len(body) == 105 and body[:6] == b"\0\0\x01\0\0\0":
                descriptor_id = reference(body, 6)
            elif (len(body) == 202 and body[:6] == b"\0\0\x08\0\0\0"
                  and struct.unpack_from("<I", body, 99)[0] == 1):
                descriptor_id = reference(body, 103)
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


def decode_selections(data, records, features):
    known = native_origin_axes(data, records)
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
            record = next(r for r in records if r.start == feature["record_offset"])
            body = data[record.body:record.end]
            try:
                angle_binding = reference(body, 20)
                angle_parameters = [p for p in feature["parameters"] if p["role"] == "AlongAngle"
                                    and p["binding_object_id"] == angle_binding]
                if len(angle_parameters) != 1:
                    continue
                identity = reference(body, 31)
                feature["revolve"]["axis_selection_record_object_id"] = identity
                selection = resolve_native_selection(data, records, identity, known)
                if selection and selection["entity"]["kind"] == "ConstructionAxis":
                    feature["revolve"].update(axis_selection="Observed native construction axis reference decoded",
                                               axis=selection)
                    resolved.append({"feature_object_id": feature["object_id"], "selection_object_id": identity})
                else:
                    unresolved.append({"feature_object_id": feature["object_id"], "selection_object_id": identity})
            except (ValueError, KeyError, struct.error):
                continue
    return {"resolved": resolved, "unresolved": unresolved,
            "scope": "Observed native construction-plane and origin-axis selection chains; no face/edge topology"}
