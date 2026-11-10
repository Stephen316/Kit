"""Additional observed construction-axis/point modes and actual support roles."""

import math
import struct
import uuid

from decode_body_selections import decode_body_selections
from decode_brep_recipes import decode_recipe
from decode_parameters import read_string
from decode_placement import cross
from decode_selection import known_construction_entities
from decode_sketch import attributes, numbers, reference, same


# (family, feature variant, backend method): method, API definition class, stored support roles.
SCHEMAS = {
    ("ConstructionAxis", 0, 6): ("CircularFace", "ConstructionAxisCircularFaceDefinition", ("circularFace",)),
    ("ConstructionAxis", 1, 18): ("NormalToFaceAtPoint", "ConstructionAxisNormalToFaceAtPointDefinition", ("face", "pointEntity")),
    ("ConstructionAxis", 3, 12): ("TwoPoints", "ConstructionAxisTwoPointDefinition", ("pointEntityOne", "pointEntityTwo")),
    ("ConstructionAxis", 4, 10): ("Edge", "ConstructionAxisEdgeDefinition", ("edgeEntity",)),
    ("ConstructionAxis", 6, 19): ("PerpendicularAtPoint", "ConstructionAxisPerpendicularAtPointDefinition", ("face",)),
    ("ConstructionPoint", 1, 7): ("TwoEdges", "ConstructionPointTwoEdgesDefinition", ("edgeOne", "edgeTwo")),
    ("ConstructionPoint", 3, 15): ("Center", "ConstructionPointCenterDefinition", ("circularEntity",)),
    ("ConstructionPoint", 4, 14): ("EdgePlane", "ConstructionPointEdgePlaneDefinition", ("edge", "plane")),
}


def decode_construction_modes(data, records, features):
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: values[0] for identity, values in grouped.items() if len(values) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError("Construction-mode typed reference unresolved: "+guid)
        return record, data[record.body:record.end]

    def counted(payload, cursor):
        count = struct.unpack_from("<I", payload, cursor)[0]
        if count > 1024 or cursor+4+11*count > len(payload):
            raise ValueError("Unsupported construction-mode reference count")
        identities = [reference(payload, cursor+4+11*i) for i in range(count)]
        if len(set(identities)) != len(identities):
            raise ValueError("Duplicate construction-mode reference list")
        return identities, cursor+4+11*count

    def cache(feature, native_id, is_axis):
        _, payload = typed(native_id, "19031004-3AB6-4D13-ABBF-C51EE214688D" if is_axis else "0E18EEF2-0D6F-480C-997E-5EBC7369AE5F")
        if payload[:2] != b"\0\1":
            raise ValueError("Unsupported construction-mode geometry prefix")
        props, cursor = attributes(payload, 2)
        if props != {"EntityGenesis": 0}:
            raise ValueError("Unsupported construction-mode geometry attributes")
        position = numbers(payload, cursor, 3)
        label_offset = cursor+(64 if is_axis else 24)
        _, end = read_string(payload, label_offset)
        reference(payload, end)
        if (struct.unpack_from("<Q", payload, end+11)[0] != feature["stored_index"]
                or reference(payload, end+20) != feature["object_id"] or payload[end+19] != 0
                or payload[end+31:end+33] != b"\0\1"):
            raise ValueError("Construction-mode geometry/feature ownership disagrees")
        name, _ = read_string(payload, end+33)
        geometry = {"name": name or None, "coordinate_units": "cm",
                    "coordinate_scope": "Native component; occurrence transforms are not inferred"}
        if is_axis:
            raw = numbers(payload, cursor+24, 3)
            length = math.sqrt(sum(v*v for v in raw))
            if length < 1e-12:
                raise ValueError("Degenerate cached construction axis direction")
            geometry.update(axis_object_id=native_id, origin_cm=position, direction=[v/length for v in raw],
                            stored_raw_direction=raw,
                            direction_encoding="Native direction vector normalized to API unit direction; original vector retained")
        else:
            geometry.update(point_object_id=native_id, position_cm=position)
        return geometry

    pending, decoded, unresolved, skipped = [], [], [], []
    for feature in features:
        family = feature["kind"]
        if family not in ("ConstructionAxis", "ConstructionPoint"):
            continue
        if feature.get("construction_definition", {}).get("definition_kind") in ("TwoPlanes", "ThreePlanes", "ByPoint"):
            skipped.append(feature["object_id"])
            continue
        try:
            is_axis = family == "ConstructionAxis"
            record, payload = typed(feature["object_id"], "803DEC43-AEA6-42CC-B8D0-F593B5124BDD" if is_axis else "5F40832C-61AA-4A05-95B1-EFA0BA483138")
            if record.start != feature["record_offset"] or feature["parameters"]:
                raise ValueError("Unobserved construction-mode source/parameters")
            if is_axis:
                if payload[:2] != b"\0\0":
                    raise ValueError("Unsupported construction-axis feature prefix")
                variant = struct.unpack_from("<I", payload, 2)[0]
                native_id, backend_id = reference(payload, 6), reference(payload, 17)
                _, backend = typed(backend_id, "F2A7590D-6654-4674-B393-A2AEF4FEC48A")
                if backend[:6] != bytes.fromhex("000008000000") or backend[74] != 0:
                    raise ValueError("Unsupported construction-axis backend prefix/marker")
                method, list_offset = struct.unpack_from("<I", backend, 70)[0], 99
            else:
                if payload[:3] != b"\0\0\1" or payload[7:11] != b"\0"*4:
                    raise ValueError("Unsupported construction-point feature prefix")
                variant = struct.unpack_from("<I", payload, 3)[0]
                native_id, backend_id = reference(payload, 11), reference(payload, 22)
                _, backend = typed(backend_id, "69EE2FA7-BCC7-449E-9CA9-976CEFDFED44")
                if backend[:23] != b"\0"*23:
                    raise ValueError("Unsupported construction-point backend prefix")
                method, list_offset = struct.unpack_from("<I", backend, 47)[0], 75
            schema = SCHEMAS.get((family, variant, method))
            if schema is None:
                raise ValueError("Unobserved construction feature/backend mode combination")
            support_ids, end = counted(backend, list_offset)
            if (len(support_ids) != len(schema[2]) or len(backend)-end != 88
                    or reference(backend, len(backend)-11) != feature["object_id"]):
                raise ValueError("Construction-mode backend support count/trailer/owner disagrees")
            geometry = cache(feature, native_id, is_axis)
            feature.update(geometry)
            pending.append({"feature": feature, "backend_id": backend_id, "backend": backend, "variant": variant,
                            "method": method, "schema": schema, "support_ids": support_ids, "geometry": geometry})
        except (ValueError, UnicodeError, KeyError, IndexError, struct.error) as error:
            unresolved.append({"feature_object_id": feature["object_id"], "kind": family, "reason": str(error)})
    known = known_construction_entities(data, records, features)
    anchors = {a["object_id"]: a for a in decode_body_selections(data, records)["body_anchors"]}

    def support(identity, role, owner_id):
        record = primary.get(identity)
        if record is None:
            raise ValueError("Construction-mode support missing or ambiguous")
        provider_id = None
        provider_position = None
        if record.class_guid == "69EE2FA7-BCC7-449E-9CA9-976CEFDFED44":
            payload = data[record.body:record.end]
            if (len(payload) != 178 or payload[:23] != b"\0"*23 or struct.unpack_from("<I", payload, 47)[0] != 10
                    or reference(payload, len(payload)-11) != owner_id):
                raise ValueError("Unsupported construction-mode point provider")
            ids, _ = counted(payload, 75)
            if len(ids) != 1:
                raise ValueError("Unsupported construction point-provider support count")
            provider_id, provider_position, identity = identity, numbers(payload, 23, 3), ids[0]
            record = primary.get(identity)
        if record is None:
            raise ValueError("Construction support descriptor missing or ambiguous")
        payload = data[record.body:record.end]
        if reference(payload, len(payload)-11) != owner_id:
            raise ValueError("Construction-mode support descriptor owner disagrees")
        if record.class_guid == "5662F619-2281-4AD9-93DC-1FCFDA1062E7":
            if payload[:4] != b"\0"*4 or struct.unpack_from("<I", payload, 15)[0] != 1:
                raise ValueError("Unsupported construction-mode face descriptor prefix")
            recipe_id = reference(payload, 4)
            namespace, cursor = read_string(payload, 19)
            entity_uuid, cursor = read_string(payload, cursor)
            if struct.unpack_from("<Q", payload, cursor)[0] != 2:
                raise ValueError("Unsupported construction face association header")
            context_ids, cursor = counted(payload, cursor+8)
            if len(context_ids) > 1:
                raise ValueError("Unsupported construction face context count")
            for context_id in context_ids:
                typed(context_id, "C46D3EEB-40E1-43FA-83DC-9CB204335417")
            anchor_ids, cursor = counted(payload, cursor)
            if len(anchor_ids) != 1 or len(payload)-cursor != 67 or anchor_ids[0] not in anchors:
                raise ValueError("Construction face body anchor unresolved")
            recipe_record, _ = typed(recipe_id, "7ACC2A03-0261-4879-A14A-A93D661A5BDC")
            recipe = decode_recipe(data, recipe_record, primary)
            if recipe["payload_kind"] not in ("face_recipe_data", "bounded_face_recipe_data"):
                raise ValueError("Unsupported construction face recipe kind")
            anchor = anchors[anchor_ids[0]]
            entity = {"kind": "Face", "body_anchor_object_id": anchor_ids[0],
                      "native_body_object_id": anchor["native_body_object_id"], "source_owner_object_id": anchor["source_owner_object_id"],
                      "recipe": recipe, "context_record_object_ids": context_ids,
                      "geometry_status": "Explicit native body and persistent face recipe; exact face geometry unresolved"}
            terminal_id = None
        else:
            if (record.class_guid != "5A1BF548-241F-46FD-9FB5-E4B05126EB9D" or len(payload) != 263
                    or payload[:2] != b"\0\0" or struct.unpack_from("<I", payload, 13)[0] != 1):
                raise ValueError("Unsupported construction-mode native descriptor")
            namespace, cursor = read_string(payload, 17)
            entity_uuid, _ = read_string(payload, cursor)
            terminal_id = reference(payload, 2)
            terminal = primary.get(terminal_id)
            if terminal is None:
                raise ValueError("Construction-mode support terminal unresolved")
            leaf = data[terminal.body:terminal.end]
            if terminal.class_guid == "90055C05-546C-4EE7-B3C9-3DD922AD0C9C" and len(leaf) == 10 and leaf[:2] == b"\0\0":
                native_id = struct.unpack_from("<Q", leaf, 2)[0]
                if native_id not in known:
                    raise ValueError("Construction-mode native entity geometry unresolved")
                entity = dict(known[native_id])
            elif ((terminal.class_guid == "D95DBAC0-238B-4429-A0AD-4AE5BEE79ADF" and len(leaf) == 18 and leaf[:2] == b"\0\0")
                  or (terminal.class_guid == "E2CEFD18-D755-4E09-8E7F-953A2F6D43F8" and len(leaf) == 26 and leaf[:10] == b"\0"*10)):
                point_terminal = terminal.class_guid == "D95DBAC0-238B-4429-A0AD-4AE5BEE79ADF"
                sketch_id, tag = struct.unpack_from("<QQ", leaf, 2 if point_terminal else 10)
                candidates = [(f, g) for f in features if f["kind"] == "Sketch" and f["sketch_object_id"] == sketch_id
                              for g in f.get("geometry", []) if g.get("entity_tag") == tag]
                if len(candidates) != 1:
                    raise ValueError("Construction-mode sketch/tag association unresolved")
                sketch, g = candidates[0]
                if (point_terminal and g["kind"] != "Point") or (not point_terminal and g["kind"] not in ("Line", "Circle")):
                    raise ValueError("Construction-mode sketch terminal/geometry kind disagrees")
                entity = {"kind": {"Point": "SketchPoint", "Line": "SketchLine", "Circle": "SketchCircle"}.get(g["kind"]),
                          "sketch_object_id": sketch_id, "sketch_name": sketch["name"], "geometry_object_id": g["object_id"], "entity_tag": tag}
                if g["kind"] == "Point" and "component_position_cm" in g:
                    entity["component_position_cm"] = g["component_position_cm"]
                elif g["kind"] == "Line" and "component_start_cm" in g and "component_end_cm" in g:
                    entity.update(component_start_cm=g["component_start_cm"], component_end_cm=g["component_end_cm"])
                elif g["kind"] == "Circle" and "component_center_cm" in g:
                    entity.update(component_center_cm=g["component_center_cm"], radius_cm=g["radius_cm"])
                else:
                    raise ValueError("Unobserved construction-mode sketch geometry or unavailable component placement")
            else:
                raise ValueError("Unobserved construction-mode support terminal layout")
        if len(namespace) != 36 or len(entity_uuid) != 36:
            raise ValueError("Unsupported construction-mode support UUID lengths")
        uuid.UUID(namespace)
        uuid.UUID(entity_uuid)
        allowed = {"circularFace": "Face", "face": "Face", "pointEntity": "SketchPoint", "pointEntityOne": "SketchPoint",
                   "pointEntityTwo": "SketchPoint", "edgeEntity": "SketchLine", "edgeOne": "SketchLine", "edgeTwo": "SketchLine",
                   "circularEntity": "SketchCircle", "edge": "ConstructionAxis", "plane": "ConstructionPlane"}
        if entity["kind"] != allowed[role]:
            raise ValueError("Construction-mode support role/entity type disagrees: "+role)
        if provider_position is not None and (entity["kind"] != "SketchPoint" or not same(provider_position, entity["component_position_cm"])):
            raise ValueError("Construction point-provider cache disagrees with explicit sketch point")
        return {"role": role, "descriptor_object_id": identity, "terminal_object_id": terminal_id,
                "point_provider_object_id": provider_id, "namespace_text": namespace, "entity_guid_text": entity_uuid,
                "entity": entity, "coordinate_scope": "Native component support geometry; occurrence context remains unverified"}

    def point_on_line(point, origin, vector):
        length = math.sqrt(sum(v*v for v in vector))
        if length < 1e-12:
            raise ValueError("Degenerate construction support line")
        distance = math.sqrt(sum(v*v for v in cross([p-o for p, o in zip(point, origin)], vector)))/length
        if distance > 1e-8:
            raise ValueError("Construction result/support point is outside its defining line")
        return distance

    for candidate in pending:
        feature, backend, schema = candidate["feature"], candidate["backend"], candidate["schema"]
        try:
            supports = [support(identity, role, feature["object_id"]) for identity, role in zip(candidate["support_ids"], schema[2])]
            method, geometry = schema[0], candidate["geometry"]
            if method == "PerpendicularAtPoint":
                point = numbers(backend, 6, 3)
                point_on_line(point, geometry["origin_cm"], geometry["direction"])
                supports.append({"role": "point", "entity": {"kind": "Point3D", "position_cm": point},
                                 "association": "Inline native backend position agrees with actual API Point3D getter",
                                 "reference_scope": "Stored point value; no sketch-point dependency is inferred"})
            consistency = {"matches": None, "scope": "Owned face recipe/body links retained; face normal/axis geometry is not independently reconstructed"}
            if method == "TwoPoints":
                points = [s["entity"]["component_position_cm"] for s in supports]
                delta = [a-b for a, b in zip(points[1], points[0])]
                if sum(v*v for v in delta) < 1e-20:
                    raise ValueError("Coincident defining points for construction axis")
                residuals = [point_on_line(p, geometry["origin_cm"], geometry["direction"]) for p in points]
                consistency = {"matches": True, "point_to_cached_axis_distances_cm": residuals,
                               "scope": "Cached axis contains both explicit noncoincident defining points"}
            elif method == "Edge":
                line = supports[0]["entity"]
                if sum((a-b)**2 for a, b in zip(line["component_start_cm"], line["component_end_cm"])) < 1e-20:
                    raise ValueError("Degenerate defining sketch line for construction axis")
                residuals = [point_on_line(line[k], geometry["origin_cm"], geometry["direction"]) for k in ("component_start_cm", "component_end_cm")]
                consistency = {"matches": True, "support_endpoint_to_axis_distances_cm": residuals}
            elif method == "NormalToFaceAtPoint":
                residual = point_on_line(supports[1]["entity"]["component_position_cm"], geometry["origin_cm"], geometry["direction"])
                consistency = {"matches": None, "point_to_axis_distance_cm": residual,
                               "scope": "Axis contains its explicit point; face-normal constraint remains unresolved"}
            elif method == "PerpendicularAtPoint":
                consistency = {"matches": None, "inline_point_lies_on_cached_axis": True,
                               "scope": "Inline point value lies on the cached axis; perpendicular face geometry remains unresolved"}
            elif method == "TwoEdges":
                residuals, directions = [], []
                for selected in supports:
                    line = selected["entity"]
                    direction = [a-b for a, b in zip(line["component_end_cm"], line["component_start_cm"])]
                    directions.append(direction)
                    residuals.append(point_on_line(geometry["position_cm"], line["component_start_cm"], direction))
                if sum(v*v for v in cross(*directions)) < 1e-20:
                    raise ValueError("Construction two-edge point has parallel or coincident defining lines")
                consistency = {"matches": True, "point_to_support_line_distances_cm": residuals}
            elif method == "Center":
                if not same(geometry["position_cm"], supports[0]["entity"]["component_center_cm"]):
                    raise ValueError("Construction point cache differs from explicit sketch-circle center")
                consistency = {"matches": True, "scope": "Cached point matches the explicit sketch-circle center"}
            elif method == "EdgePlane":
                axis, plane = [s["entity"] for s in supports]
                line_distance = point_on_line(geometry["position_cm"], axis["origin_cm"], axis["direction"])
                residual = sum(n*(p-o) for n, p, o in zip(plane["normal"], geometry["position_cm"], plane["origin_cm"]))
                denominator = sum(a*b for a, b in zip(plane["normal"], axis["direction"]))
                if abs(residual) > 1e-8 or abs(denominator) < 1e-8:
                    raise ValueError("Construction edge-plane point has inconsistent or nonunique supports")
                consistency = {"matches": True, "point_to_axis_distance_cm": line_distance, "plane_residual_cm": residual}
            result = {"feature_object_id": feature["object_id"], "kind": feature["kind"], "name": feature["name"],
                      "definition_kind": method, "api_definition_class": schema[1], "backend_object_id": candidate["backend_id"],
                      "stored_feature_variant_code": candidate["variant"], "stored_backend_method_code": candidate["method"],
                      "support_inputs": supports, "cached_geometry": geometry, "support_consistency": consistency,
                      "backend_geometry_values": numbers(backend, 6, 8) if feature["kind"] == "ConstructionAxis" else numbers(backend, 23, 3),
                      "backend_geometry_scope": "Stored values retained; API normalized axis direction and anchor point may differ",
                      "geometry_status": "Observed cached geometry and explicit defining supports decoded; exact face topology and general regeneration remain unsupported"}
            feature["construction_definition"] = result
            feature["decode_level"] = "Observed construction definition mode, cached geometry and explicit support roles"
            feature["selection_status"] = "Owned typed construction supports decoded; face geometry remains partial"
            feature["unresolved_inputs"] = (["Exact persistent face geometry"] if any(s["entity"]["kind"] == "Face" for s in supports) else [])
            decoded.append(result)
        except (ValueError, UnicodeError, KeyError, IndexError, struct.error) as error:
            unresolved.append({"feature_object_id": feature["object_id"], "kind": feature["kind"], "reason": str(error)})
    return {"definitions": decoded, "unresolved": unresolved, "skipped_prior_definition_feature_ids": skipped,
            "scope": "Eight observed additional construction modes; native component support geometry, actual API definition roles and explicit unsupported face constraints"}
