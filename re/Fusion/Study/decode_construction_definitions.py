"""Observed axis/point parametric definitions and explicit support references.

Coverage is limited to two-plane axes, three-plane points and points explicitly
linked to sketch points. Methods are grounded in controlled generator calls and
their exported API geometry; other construction layouts are rejected.
"""

import math
import struct
import uuid

from decode_parameters import read_string
from decode_placement import cross
from decode_selection import known_construction_entities
from decode_sketch import numbers, reference, same


def decode_construction_definitions(data, records, features):
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: values[0] for identity, values in grouped.items() if len(values) == 1}
    known = known_construction_entities(data, records, features)
    decoded, unresolved = [], []

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError("Construction-definition typed reference unresolved: "+guid)
        return record, data[record.body:record.end]

    def descriptor(identity, role, owner_id, expected_kind):
        _, payload = typed(identity, "5A1BF548-241F-46FD-9FB5-E4B05126EB9D")
        if (len(payload) != 263 or payload[:2] != b"\0\0"
                or reference(payload, len(payload)-11) != owner_id
                or struct.unpack_from("<I", payload, 13)[0] != 1):
            raise ValueError("Unsupported construction support descriptor layout/owner")
        namespace, cursor = read_string(payload, 17)
        entity_uuid, _ = read_string(payload, cursor)
        if len(namespace) != 36 or len(entity_uuid) != 36:
            raise ValueError("Unsupported construction support UUID lengths")
        uuid.UUID(namespace)
        uuid.UUID(entity_uuid)
        terminal_id = reference(payload, 2)
        terminal = primary.get(terminal_id)
        if terminal is None:
            raise ValueError("Construction support terminal missing or ambiguous")
        leaf = data[terminal.body:terminal.end]
        if expected_kind == "ConstructionPlane":
            if (terminal.class_guid != "90055C05-546C-4EE7-B3C9-3DD922AD0C9C"
                    or len(leaf) != 10 or leaf[:2] != b"\0\0"):
                raise ValueError("Unobserved construction plane terminal layout")
            native_id = struct.unpack_from("<Q", leaf, 2)[0]
            if native_id not in known or known[native_id]["kind"] != "ConstructionPlane":
                raise ValueError("Construction support does not resolve to known native plane")
            typed(native_id, "8D424E29-DE23-4B1F-A3AD-84C52A497D1A")
            entity = known[native_id]
        else:
            if (terminal.class_guid != "D95DBAC0-238B-4429-A0AD-4AE5BEE79ADF"
                    or len(leaf) != 18 or leaf[:2] != b"\0\0"):
                raise ValueError("Only observed sketch-point construction supports are decoded")
            sketch_id, tag = struct.unpack_from("<QQ", leaf, 2)
            candidates = [(f, point) for f in features if f["kind"] == "Sketch" and f["sketch_object_id"] == sketch_id
                          for point in f.get("geometry", []) if point["kind"] == "Point" and point["entity_tag"] == tag]
            if len(candidates) != 1 or "component_position_cm" not in candidates[0][1]:
                raise ValueError("Construction sketch-point support/tag/placement unresolved")
            sketch, point = candidates[0]
            entity = {"kind": "SketchPoint", "sketch_object_id": sketch_id, "sketch_name": sketch["name"],
                      "point_object_id": point["object_id"], "point_entity_tag": tag,
                      "component_position_cm": point["component_position_cm"]}
        return {"role": role, "descriptor_object_id": identity, "terminal_object_id": terminal_id,
                "namespace_text": namespace, "entity_guid_text": entity_uuid, "entity": entity,
                "association": "Explicit owned descriptor -> typed terminal -> native plane or sketch/tag reference"}

    def consistency(feature, supports, method):
        if method == "ByPoint":
            position = feature["position_cm"]
            point = supports[0]["entity"]["component_position_cm"]
            if not same(position, point):
                raise ValueError("Construction point cache disagrees with explicit sketch point")
            return {"matches": True, "coordinate_scope": "Native component", "point_component_position_cm": point,
                    "scope": "Independently decoded sketch placement agrees with the native construction point cache"}
        position = feature["origin_cm"] if method == "TwoPlanes" else feature["position_cm"]
        planes = [support["entity"] for support in supports]
        residuals = [sum(n*(p-o) for n, p, o in zip(plane["normal"], position, plane["origin_cm"])) for plane in planes]
        if any(not math.isclose(value, 0., abs_tol=1e-8) for value in residuals):
            raise ValueError("Construction cached point is outside its explicit support planes")
        if method == "TwoPlanes":
            direction = feature["direction"]
            dots = [sum(a*b for a, b in zip(plane["normal"], direction)) for plane in planes]
            perpendicular = cross(planes[0]["normal"], planes[1]["normal"])
            if (sum(v*v for v in perpendicular) < 1e-16
                    or any(not math.isclose(value, 0., abs_tol=1e-8) for value in dots)):
                raise ValueError("Construction cached axis/support planes disagree or are parallel")
            return {"matches": True, "origin_plane_residuals_cm": residuals, "direction_dot_support_normals": dots,
                    "scope": "Cached line lies on both explicit planes; axis anchor point and direction sign are retained from the native geometry"}
        determinant = sum(a*b for a, b in zip(planes[0]["normal"], cross(planes[1]["normal"], planes[2]["normal"])))
        if abs(determinant) < 1e-8:
            raise ValueError("Construction three-plane point is not a unique intersection")
        return {"matches": True, "plane_residuals_cm": residuals, "normal_matrix_determinant": determinant,
                "scope": "Cached point satisfies three independent explicit support-plane equations"}

    for feature in features:
        if feature["kind"] not in ("ConstructionAxis", "ConstructionPoint"):
            continue
        try:
            is_axis = feature["kind"] == "ConstructionAxis"
            source_class = "803DEC43-AEA6-42CC-B8D0-F593B5124BDD" if is_axis else "5F40832C-61AA-4A05-95B1-EFA0BA483138"
            source, payload = typed(feature["object_id"], source_class)
            if source.start != feature["record_offset"] or feature["parameters"]:
                raise ValueError("Unobserved construction definition source/parameters")
            if is_axis:
                if payload[:6] != bytes.fromhex("000002000000"):
                    raise ValueError("Only observed two-plane axis feature variant is decoded")
                native_id, backend_id = reference(payload, 6), reference(payload, 17)
                if native_id != feature.get("axis_object_id"):
                    raise ValueError("Construction axis cached geometry ownership unresolved")
                typed(native_id, "19031004-3AB6-4D13-ABBF-C51EE214688D")
                _, backend = typed(backend_id, "F2A7590D-6654-4674-B393-A2AEF4FEC48A")
                if backend[:6] != bytes.fromhex("000008000000") or not same(numbers(backend, 6, 3), feature["origin_cm"]):
                    raise ValueError("Unobserved construction axis backend header/cache")
                method, method_code, variant, roles = "TwoPlanes", 8, 2, ("planarEntityOne", "planarEntityTwo")
                list_offset, api_class = 99, "ConstructionAxisTwoPlaneDefinition"
                cache = {"origin_cm": feature["origin_cm"], "direction": feature["direction"]}
                prefix = backend[6:list_offset]
            else:
                if payload[:3] != b"\0\0\1" or payload[7:11] != b"\0"*4:
                    raise ValueError("Unsupported construction point feature prefix")
                variant = struct.unpack_from("<I", payload, 3)[0]
                native_id, backend_id = reference(payload, 11), reference(payload, 22)
                if native_id != feature.get("point_object_id"):
                    raise ValueError("Construction point cached geometry ownership unresolved")
                typed(native_id, "0E18EEF2-0D6F-480C-997E-5EBC7369AE5F")
                _, backend = typed(backend_id, "69EE2FA7-BCC7-449E-9CA9-976CEFDFED44")
                if backend[:23] != b"\0"*23 or not same(numbers(backend, 23, 3), feature["position_cm"]):
                    raise ValueError("Unobserved construction point backend prefix/cache")
                method_code = struct.unpack_from("<I", backend, 47)[0]
                if (variant, method_code) == (2, 8):
                    method, roles, api_class = "ThreePlanes", ("planeOne", "planeTwo", "planeThree"), "ConstructionPointThreePlanesDefinition"
                elif (variant, method_code) == (0, 10):
                    method, roles, api_class = "ByPoint", ("pointEntity",), "ConstructionPointPointDefinition"
                else:
                    raise ValueError("Unsupported construction point feature/backend method combination")
                list_offset, cache, prefix = 75, {"position_cm": feature["position_cm"]}, backend[51:75]
            count = struct.unpack_from("<I", backend, list_offset)[0]
            end = list_offset+4+11*count
            if count != len(roles) or len(backend)-end != 88 or reference(backend, len(backend)-11) != feature["object_id"]:
                raise ValueError("Construction backend support count/trailer/owner disagreement")
            support_ids = [reference(backend, list_offset+4+11*i) for i in range(count)]
            if len(set(support_ids)) != len(support_ids):
                raise ValueError("Duplicate construction support descriptor identities")
            supports = [descriptor(identity, role, feature["object_id"], "SketchPoint" if method == "ByPoint" else "ConstructionPlane")
                        for identity, role in zip(support_ids, roles)]
            result = {"feature_object_id": feature["object_id"], "kind": feature["kind"], "name": feature["name"],
                      "native_geometry_object_id": native_id, "backend_object_id": backend_id,
                      "definition_kind": method, "api_definition_class": api_class,
                      "stored_feature_variant_code": variant, "stored_backend_method_code": method_code,
                      "support_inputs": supports, "cached_geometry": cache,
                      "support_consistency": consistency(feature, supports, method),
                      "backend_geometry_prefix_hex": prefix.hex(),
                      "backend_prefix_scope": "Stored geometry/auxiliary fields retained; general field meanings are not interpreted",
                      "definition_evidence_scope": "Observed native layout matched to controlled generator invocation and exported API geometry; API definition getters were not captured",
                      "coordinate_scope": "Native component coordinates; occurrence transforms are not inferred",
                      "geometry_status": "Cached native geometry and explicit defining supports decoded; general construction regeneration is not implemented"}
            feature["construction_definition"] = result
            feature["decode_level"] = "Observed cached geometry, parametric definition method and explicit defining supports"
            feature["selection_status"] = "Owned native plane or sketch/tag support references decoded"
            feature["unresolved_inputs"] = [item for item in feature.get("unresolved_inputs", [])
                                            if item != "Parametric construction input geometry references"]
            decoded.append(result)
        except (ValueError, UnicodeError, IndexError, KeyError, struct.error) as error:
            unresolved.append({"feature_object_id": feature["object_id"], "kind": feature["kind"], "reason": str(error)})
    return {"definitions": decoded, "unresolved": unresolved,
            "scope": "Observed two-plane axes, three-plane points and sketch-point reference points; other construction methods remain unsupported"}
